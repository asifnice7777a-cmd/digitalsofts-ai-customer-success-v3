import re
from app.tools.knowledge_tool import search_company_knowledge
from app.tools.cost_tool import get_pricing_data, evaluate_price_offer
from app.llm import call_llm_with_tools
from app.memory.session_memory import ClientProfile


PRICE_PATTERN = re.compile(r"\$?\s?(\d{3,7}(?:,\d{3})*)(?:\.\d+)?")


def _extract_prices(message: str):
    values = []
    for raw in PRICE_PATTERN.findall(message):
        try:
            values.append(float(raw.replace(",", "")))
        except ValueError:
            continue
    return values


def _ensure_list_price(profile: ClientProfile) -> None:
    """Establish profile.list_price deterministically, BEFORE the LLM ever
    generates a response, using the same rate card / discount bands as
    estimate_project_cost and evaluate_price_offer — never by asking the LLM
    to quote a price and then parsing it back out of its own text.

    Only runs once per conversation: once list_price is set, it's the fixed
    reference price for the rest of the negotiation (a real quote shouldn't
    silently change mid-negotiation even if e.g. project_type is refined
    later), so this is a no-op on every subsequent turn."""
    if profile.list_price:
        return
    pricing = get_pricing_data(profile.project_type or "custom software")
    profile.list_price = pricing["list_price"]
    # minimum_price / approval_limit are intentionally NOT stored on the
    # profile or put into the system prompt — they're internal negotiation
    # floors that evaluate_price_offer already re-derives from list_price
    # via AUTO_APPROVE_DISCOUNT/REDUCED_SCOPE_DISCOUNT, and the client should
    # never see them directly.


def _apply_negotiation(message: str, profile: ClientProfile) -> str:
    """Deterministically evaluates any price offer in the message against
    business rules, mutating `profile` with the outcome. Returns a plain-text
    negotiation note to inject into the system prompt, or "" if the message
    contains no evaluable price offer."""
    prices = _extract_prices(message)
    if not prices:
        return ""

    if len(prices) >= 2:
        # e.g. "The price is 3000. Can you do it for 2000?" — treat the
        # larger figure as the reference list price, smaller as the offer.
        # (list_price is normally already set by _ensure_list_price before
        # this runs, so this branch mainly matters if the client states
        # their own reference number explicitly.)
        list_price_candidate = max(prices)
        offered_price = min(prices)
        if not profile.list_price:
            profile.list_price = list_price_candidate
    else:
        # e.g. "2200 final." — a single figure is a new offer against the
        # list price already established by _ensure_list_price.
        offered_price = prices[0]

    if not profile.list_price:
        # No reference price known yet — nothing to evaluate against.
        return ""

    decision_text = evaluate_price_offer.invoke({
        "offered_price": offered_price,
        "list_price": profile.list_price,
    })

    profile.last_offer_amount = offered_price
    profile.negotiation_history = profile.negotiation_history + [{
        "offered_price": offered_price,
        "list_price": profile.list_price,
        "decision": decision_text,
    }]

    if "DECISION: ESCALATE" in decision_text:
        profile.negotiation_status = "escalation_needed"
    elif "DECISION: COUNTER_OFFER" in decision_text:
        profile.negotiation_status = "in_progress"
    elif "DECISION: ACCEPT" in decision_text:
        profile.negotiation_status = "accepted"

    return decision_text


def run_sales_agent(message: str, profile: ClientProfile) -> str:
    # Establish the deterministic reference price BEFORE anything else runs,
    # so both negotiation evaluation and the system prompt always have a
    # real number to work with — the LLM never invents or is asked to recall
    # a price from its own prior phrasing.
    _ensure_list_price(profile)

    # estimate_project_cost is intentionally NOT passed to the LLM here
    # (it remains completely unmodified in cost_tool.py and is still usable
    # elsewhere) — letting the LLM independently call a pricing tool mid-reply
    # could produce a number that disagrees with the deterministic
    # profile.list_price above. search_company_knowledge is unaffected and
    # still available for factual, non-pricing questions.
    tools = [search_company_knowledge]

    negotiation_note = _apply_negotiation(message, profile)

    system_prompt = (
        "You are the Sales Agent for DigitalSofts, a software company. "
        "Answer the client's question about services and pricing warmly and concisely, "
        "referencing known client details where relevant instead of asking them to repeat information. "
        f"Known client info: {profile.model_dump()}. "
        "The client's list price for their project has ALREADY been determined and is included "
        "above as list_price — treat it as the authoritative quoted price. Never state a "
        "different price than list_price, and never invent or recompute a price yourself. "
        "You have access to a tool to search the company knowledge base for factual company "
        "information (services, policies, general info) — do not use it to determine or "
        "negotiate a specific price. "
        f"If relevant, the client's project type is: {profile.project_type or 'not specified'}. "
        "\n\n"
        "STRICT RESPONSE RULES:\n"
        "1. If the client's message is introducing themselves for the first time (for example: "
        "'I am Asif', 'My name is Asif', 'This is Asif'), do NOT just flatly state their name "
        "back to them (e.g. do not reply 'Your name is Asif.'). Acknowledge it warmly and "
        "naturally instead, for example: 'Nice to meet you, Asif! How can I help you today?' — "
        "then stop; do not add company information, pricing, services, or sales content unless "
        "they asked about those too in the same message.\n"
        "2. If the client's message is sharing a new piece of profile information about "
        "themselves that is NOT a question (for example: 'I work at DigitalSofts.', 'My company "
        "is ABC.', 'My budget is $20,000.', 'My timeline is 3 months.', 'I prefer Python.'), do "
        "NOT respond with company services, pricing, ERP information, or any other sales "
        "content, and do NOT call the tools for it. Acknowledge briefly and naturally that "
        "you've noted the specific detail they shared, then ask how you can help — for example: "
        "'Thanks, Asif. I've noted that you work at DigitalSofts. How can I help you today?'\n"
        "3. If the client's message is instead a question asking YOU to recall something about "
        "them (for example: 'What is my name?', 'My name?', 'Do you remember my name?', 'What "
        "is my budget?', 'What company did I mention?'), answer ONLY that question directly and "
        "briefly and factually, using the Known client info above — for example 'Your name is "
        "Asif.' Do NOT include company information, pricing, services, or any other sales "
        "content in that reply, and do NOT call the tools for it, unless the client's message "
        "also explicitly asks about services, pricing, or the company.\n"
        "4. You MUST base your answer on the actual information returned by the tools. "
        "Never ignore or ovewrite tool output with a generic reply.\n"
        "5. Never answer with vague, generic sales language such as 'Let's discuss your needs' "
        "or similar filler — always speak to the client's actual question using the tool results.\n"
        "6. If the tool output already answers the question, answer directly. Do NOT ask an "
        "unnecessary follow-up question just to keep the conversation going.\n"
        "7. If the client asks about services, pricing, AI chatbots, ERP, cloud, payment terms, "
        "or support, you must answer using list_price (from Known client info) for the price and "
        "the tool output for other factual details — do not deflect or give a partial non-answer.\n"
        "8. Always state list_price using its exact figure when quoting a price — never round it "
        "differently or substitute a different number.\n"
        "9. If the tool output includes timelines (weeks, months, delivery windows), you MUST "
        "include those exact timelines in your reply.\n"
        "10. Keep your answer concise: 2 to 6 sentences.\n"
        "11. NEVER reply with only 'Okay.', 'Sure.', 'Got it.', or any other one-word or "
        "one-phrase acknowledgment. Every reply must contain substantive information.\n"
    )

    if negotiation_note:
        system_prompt += (
            "\nNEGOTIATION RULE (this decision has ALREADY been made by the pricing system — "
            "do not recompute or override it, only phrase it naturally to the client, like an "
            "experienced human sales rep would):\n"
            f"{negotiation_note}\n"
            "If the decision is ACCEPT, confirm the price warmly and ask if they'd like to proceed. "
            "If the decision is COUNTER_OFFER, explain that the requested price is below the "
            "minimum, then offer the suggested counter amount, framing it as a reduced-scope "
            "option (fewer features) rather than a straight discount. "
            "If the decision is ESCALATE, tell the client clearly that this offer is below your "
            "approval limit, and that you will escalate their request to a sales manager. Do not "
            "propose a new counter-offer yourself in this case, and do not continue negotiating "
            "further in this reply.\n"
        )

    fallback = "Thanks for reaching out! Let me look into that and get back to you shortly."

    return call_llm_with_tools(system_prompt, message, tools, fallback)