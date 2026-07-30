from langchain_core.tools import tool

RATE_CARD = {
    "web development": (5000, 15000),
    "mobile app": (8000, 25000),
    "erp": (20000, 60000),
    "ai solution": (10000, 40000),
    "cloud migration": (7000, 30000),
    "custom software": (10000, 50000),
}


@tool
def estimate_project_cost(project_type: str, complexity: str = "medium") -> str:
    """Estimate the project cost range in USD given a project type and complexity (low/medium/high)."""
    key = project_type.lower().strip()
    base_low, base_high = (10000, 30000)
    for name, (low, high) in RATE_CARD.items():
        if name in key or key in name:
            base_low, base_high = low, high
            break
    multiplier = {"low": 0.7, "medium": 1.0, "high": 1.6}.get(complexity.lower(), 1.0)
    low = int(base_low * multiplier)
    high = int(base_high * multiplier)
    return f"Estimated cost for {project_type} ({complexity} complexity): ${low:,} - ${high:,} USD"


# --- Negotiation business rules ---------------------------------------
# Discount bands the Sales Agent applies when a client counters on price.
# Kept as plain module-level constants (not env-configurable) since this
# mirrors the existing style of RATE_CARD — simple, readable, easy to tune.
AUTO_APPROVE_DISCOUNT = 0.10   # up to 10% off list price: accept, no approval needed
REDUCED_SCOPE_DISCOUNT = 0.23  # 10-23% off: counter with a reduced-scope offer
# beyond 23% off list price: exceeds the agent's approval limit -> escalate


@tool
def evaluate_price_offer(offered_price: float, list_price: float) -> str:
    """Evaluate a client's price offer against the list price using DigitalSofts'
    standard discount approval rules. Returns a structured decision: ACCEPT,
    COUNTER_OFFER (with a suggested reduced-scope counter amount), or ESCALATE
    (exceeds the agent's approval limit and requires a sales manager)."""
    if list_price <= 0:
        return "DECISION: ESCALATE. Reason: no valid list price available to evaluate the offer."

    if offered_price >= list_price:
        return f"DECISION: ACCEPT. Offer ${offered_price:,.0f} meets or exceeds list price ${list_price:,.0f}."

    discount = (list_price - offered_price) / list_price

    if discount <= AUTO_APPROVE_DISCOUNT:
        return (
            f"DECISION: ACCEPT. Offer ${offered_price:,.0f} is a {discount * 100:.1f}% discount off "
            f"list price ${list_price:,.0f}, within the {AUTO_APPROVE_DISCOUNT * 100:.0f}% standard approval limit."
        )

    if discount <= REDUCED_SCOPE_DISCOUNT:
        counter = round(list_price * (1 - REDUCED_SCOPE_DISCOUNT), -2)
        return (
            f"DECISION: COUNTER_OFFER. Offer ${offered_price:,.0f} is a {discount * 100:.1f}% discount, "
            f"below the {AUTO_APPROVE_DISCOUNT * 100:.0f}% standard limit but within the reduced-scope band. "
            f"Suggested counter: ${counter:,.0f} with a reduced feature set."
        )

    return (
        f"DECISION: ESCALATE. Offer ${offered_price:,.0f} is a {discount * 100:.1f}% discount off "
        f"list price ${list_price:,.0f}, exceeding the {REDUCED_SCOPE_DISCOUNT * 100:.0f}% approval limit. "
        f"Requires sales manager approval."
    )


# --- Structured, deterministic pricing (for direct Python use, not an LLM tool) --
# Unlike estimate_project_cost (a range, meant to be read aloud by the LLM) and
# evaluate_price_offer (an LLM tool, invoked mid-conversation), this is a plain
# function the Sales Agent calls DIRECTLY in Python, before generating any
# response. It returns a single deterministic list_price plus the internal
# minimum_price/approval_limit floors, computed from the exact same RATE_CARD
# and discount bands above — so the "quoted price" the client sees is never
# something the LLM invented or that got parsed back out of its own text; it's
# a plain number set in profile.list_price ahead of time, and the LLM only
# ever narrates it.
def get_pricing_data(project_type: str, complexity: str = "medium") -> dict:
    """Deterministically compute list_price, minimum_price, and approval_limit
    for a project. Not exposed to the LLM as a tool — called directly by agent
    code so pricing is established before the LLM generates any text."""
    key = project_type.lower().strip()
    base_low, base_high = (10000, 30000)
    for name, (low, high) in RATE_CARD.items():
        if name in key or key in name:
            base_low, base_high = low, high
            break
    multiplier = {"low": 0.7, "medium": 1.0, "high": 1.6}.get(complexity.lower(), 1.0)

    list_price = round(((base_low + base_high) / 2) * multiplier, -2)
    approval_limit = round(list_price * (1 - AUTO_APPROVE_DISCOUNT), -2)
    minimum_price = round(list_price * (1 - REDUCED_SCOPE_DISCOUNT), -2)

    return {
        "list_price": list_price,
        "minimum_price": minimum_price,
        "approval_limit": approval_limit,
    }


# @tool
# def evaluate_price_offer(offered_price: float, list_price: float) -> str:
#     """Evaluate a client's price offer against the list price using DigitalSofts'
#     standard discount approval rules. Returns a structured decision: ACCEPT,
#     COUNTER_OFFER (with a suggested reduced-scope counter amount), or ESCALATE
#     (exceeds the agent's approval limit and requires a sales manager)."""
#     if list_price <= 0:
#         return "DECISION: ESCALATE. Reason: no valid list price available to evaluate the offer."

#     if offered_price >= list_price:
#         return f"DECISION: ACCEPT. Offer ${offered_price:,.0f} meets or exceeds list price ${list_price:,.0f}."

#     discount = (list_price - offered_price) / list_price

#     if discount <= AUTO_APPROVE_DISCOUNT:
#         return (
#             f"DECISION: ACCEPT. Offer ${offered_price:,.0f} is a {discount * 100:.1f}% discount off "
#             f"list price ${list_price:,.0f}, within the {AUTO_APPROVE_DISCOUNT * 100:.0f}% standard approval limit."
#         )

#     if discount <= REDUCED_SCOPE_DISCOUNT:
#         counter = round(list_price * (1 - REDUCED_SCOPE_DISCOUNT), -2)
#         return (
#             f"DECISION: COUNTER_OFFER. Offer ${offered_price:,.0f} is a {discount * 100:.1f}% discount, "
#             f"below the {AUTO_APPROVE_DISCOUNT * 100:.0f}% standard limit but within the reduced-scope band. "
#             f"Suggested counter: ${counter:,.0f} with a reduced feature set."
#         )

#     return (
#         f"DECISION: ESCALATE. Offer ${offered_price:,.0f} is a {discount * 100:.1f}% discount off "
#         f"list price ${list_price:,.0f}, exceeding the {REDUCED_SCOPE_DISCOUNT * 100:.0f}% approval limit. "
#         f"Requires sales manager approval."
#     )