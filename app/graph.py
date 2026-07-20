# from typing import Optional, TypedDict


# from langgraph.graph import StateGraph, END


# from app.memory.session_memory import ClientProfile
# from app.agents.supervisor import route_request, extract_profile_fields
# from app.agents.sales_agent import run_sales_agent
# from app.agents.technical_agent import run_technical_agent
# from app.agents.documentation_agent import run_documentation_agent
# from app.agents.meeting_agent import run_meeting_agent, is_meeting_info_complete
# from app.evaluation import evaluate_response
# from app.logging_config import logger


# CANCEL_KEYWORDS = ["cancel", "never mind", "nevermind", "stop the meeting"]




# class AgentState(TypedDict):
#     session_id: str
#     message: str
#     profile: dict
#     # Snapshot of `profile` taken once per user turn, BEFORE any agent node
#     # mutates it. Agent nodes always read from this (not `profile`) so that
#     # every pass — first attempt or retry — evaluates the same user message
#     # against the same starting profile.
#     turn_profile: dict
#     agent: str
#     active_agent: Optional[str]
#     response: str
#     confidence: float
#     retry_count: int
#     retry_reason: str




# AGENT_FUNCS = {
#     "sales": run_sales_agent,
#     "technical": run_technical_agent,
#     "documentation": run_documentation_agent,
#     "meeting": run_meeting_agent,
# }


# def _merge_extracted_fields(profile: dict, extracted: dict) -> None:
#     """Merge newly-extracted fields into the in-progress profile dict.
#     Every field is a plain overwrite (last mention wins), EXCEPT
#     preferred_technology, which accumulates across turns (e.g. "Python" on
#     one turn plus "FastAPI" on a later turn becomes "python, fastapi")
#     instead of the later mention erasing the earlier one."""
#     for key, value in extracted.items():
#         if not value:
#             continue
#         if key == "preferred_technology":
#             existing = profile.get("preferred_technology")
#             if existing:
#                 existing_terms = [t.strip() for t in existing.split(",") if t.strip()]
#                 new_terms = [t.strip() for t in value.split(",") if t.strip()]
#                 combined = existing_terms + [t for t in new_terms if t not in existing_terms]
#                 profile[key] = ", ".join(combined)
#             else:
#                 profile[key] = value
#         else:
#             profile[key] = value




# def supervisor_node(state: AgentState) -> AgentState:
#     text = state["message"].lower()
#     in_meeting_flow = state.get("active_agent") == "meeting" and not any(
#         k in text for k in CANCEL_KEYWORDS
#     )

#     # The Meeting Agent collects fields strictly one at a time. Running the
#     # generic, model-based field extractor on top of that and merging
#     # whatever it guesses would race with that logic, so we skip it while a
#     # meeting flow is in progress.
#     if not in_meeting_flow:
#         extracted = extract_profile_fields(state["message"])
#         _merge_extracted_fields(state["profile"], extracted)

#     if in_meeting_flow:
#         state["agent"] = "meeting"
#     else:
#         state["agent"] = route_request(state["message"])

#     # Stable per-turn baseline. supervisor_node runs once per user message
#     # (retries loop directly back into the agent node, not through here).
#     state["turn_profile"] = dict(state["profile"])

#     logger.info("Session %s routed to '%s' agent", state["session_id"], state["agent"])
#     return state




# def make_agent_node(name: str):
#     def node(state: AgentState) -> AgentState:
#         # retry_count is 0 on the first pass through this node for a given
#         # user message, and is set to 1 by evaluation_node BEFORE routing
#         # back here for a retry. So this flag reliably tells us which pass
#         # we're on.
#         is_retry_pass = state.get("retry_count", 0) > 0

#         # Always build the working profile from the turn's snapshot, never
#         # from `state["profile"]` — this keeps every pass (first or retry)
#         # asking for/consuming the same field, instead of the retry seeing
#         # an already-advanced profile and consuming the message again into
#         # the next field.
#         profile = ClientProfile(**state["turn_profile"])
#         func = AGENT_FUNCS[name]
#         try:
#             # Re-run to regenerate the response text (this is what a retry
#             # is for). Any mutation `func` makes to `profile` here is on a
#             # disposable local object — see below, it's only persisted on
#             # the first pass.
#             state["response"] = func(state["message"], profile)
#         except Exception as exc:
#             logger.error("Agent '%s' failed: %s", name, exc)
#             state["response"] = "I'm having trouble processing that right now. Could you rephrase your request?"

#         if is_retry_pass:
#             # Retry: keep the freshly regenerated `state["response"]`, but
#             # do NOT touch `state["profile"]` / `state["active_agent"]`
#             # again. The user's message was already consumed into the
#             # profile on the first pass; a retry must not consume it a
#             # second time. Whatever the first pass persisted stays as-is.
#             return state

#         if name == "meeting":
#             # First pass — this is the one authoritative mutation of the
#             # profile for this user message. Sync it back so it persists to
#             # session memory.
#             state["profile"] = profile.model_dump()
#             state["active_agent"] = None if is_meeting_info_complete(profile) else "meeting"
#         else:
#             state["active_agent"] = None

#         return state


#     return node




# def evaluation_node(state: AgentState) -> AgentState:
#     _, confidence, reason = evaluate_response(state["message"], state["response"])
#     state["confidence"] = confidence
#     if confidence < 0.75 and state["retry_count"] == 0:
#         state["retry_count"] = 1
#         state["retry_reason"] = reason
#         logger.warning("Session %s retry triggered (confidence=%.2f): %s", state["session_id"], confidence, reason)
#     else:
#         state["retry_reason"] = ""
#     return state




# def route_after_supervisor(state: AgentState) -> str:
#     return state["agent"]




# def route_after_evaluation(state: AgentState) -> str:
#     if state["retry_reason"]:
#         return state["agent"]
#     return END




# def build_graph():
#     graph = StateGraph(AgentState)
#     graph.add_node("supervisor", supervisor_node)
#     for name in AGENT_FUNCS:
#         graph.add_node(name, make_agent_node(name))
#     graph.add_node("evaluation", evaluation_node)


#     graph.set_entry_point("supervisor")
#     graph.add_conditional_edges("supervisor", route_after_supervisor, {name: name for name in AGENT_FUNCS})
#     for name in AGENT_FUNCS:
#         graph.add_edge(name, "evaluation")
#     graph.add_conditional_edges(
#         "evaluation",
#         route_after_evaluation,
#         {**{name: name for name in AGENT_FUNCS}, END: END},
#     )
#     return graph.compile()




# compiled_graph = build_graph()



from typing import Optional, TypedDict


from langgraph.graph import StateGraph, END


from app.memory.session_memory import ClientProfile
from app.agents.supervisor import route_request, extract_profile_fields
from app.agents.sales_agent import run_sales_agent
from app.agents.technical_agent import run_technical_agent
from app.agents.documentation_agent import run_documentation_agent
from app.agents.meeting_agent import run_meeting_agent, is_meeting_info_complete
from app.evaluation import evaluate_response
from app.logging_config import logger


CANCEL_KEYWORDS = ["cancel", "never mind", "nevermind", "stop the meeting"]




class AgentState(TypedDict):
    session_id: str
    message: str
    profile: dict
    # Snapshot of `profile` taken once per user turn, BEFORE any agent node
    # mutates it. Agent nodes always read from this (not `profile`) so that
    # every pass — first attempt or retry — evaluates the same user message
    # against the same starting profile.
    turn_profile: dict
    agent: str
    active_agent: Optional[str]
    response: str
    confidence: float
    retry_count: int
    retry_reason: str




def run_human_handoff(message: str, profile: ClientProfile) -> str:
    """Deterministic escalation acknowledgment. No LLM or tool call is used
    here — this node's job is only to confirm the handoff to the client, not
    to attempt to resolve their request itself."""
    name_part = f", {profile.client_name}" if profile.client_name else ""
    return (
        f"Understood{name_part} — I'm connecting you with a member of our team who can help "
        "with this directly. Someone from DigitalSofts will follow up with you shortly."
    )




AGENT_FUNCS = {
    "sales": run_sales_agent,
    "technical": run_technical_agent,
    "documentation": run_documentation_agent,
    "meeting": run_meeting_agent,
    "human_handoff": run_human_handoff,
}


def _merge_extracted_fields(profile: dict, extracted: dict) -> None:
    """Merge newly-extracted fields into the in-progress profile dict.
    Every field is a plain overwrite (last mention wins), EXCEPT
    preferred_technology, which accumulates across turns (e.g. "Python" on
    one turn plus "FastAPI" on a later turn becomes "python, fastapi")
    instead of the later mention erasing the earlier one."""
    for key, value in extracted.items():
        if not value:
            continue
        if key == "preferred_technology":
            existing = profile.get("preferred_technology")
            if existing:
                existing_terms = [t.strip() for t in existing.split(",") if t.strip()]
                new_terms = [t.strip() for t in value.split(",") if t.strip()]
                combined = existing_terms + [t for t in new_terms if t not in existing_terms]
                profile[key] = ", ".join(combined)
            else:
                profile[key] = value
        else:
            profile[key] = value




def supervisor_node(state: AgentState) -> AgentState:
    text = state["message"].lower()
    in_meeting_flow = state.get("active_agent") == "meeting" and not any(
        k in text for k in CANCEL_KEYWORDS
    )

    # The Meeting Agent collects fields strictly one at a time. Running the
    # generic, model-based field extractor on top of that and merging
    # whatever it guesses would race with that logic, so we skip it while a
    # meeting flow is in progress.
    if not in_meeting_flow:
        extracted = extract_profile_fields(state["message"])
        _merge_extracted_fields(state["profile"], extracted)

    if in_meeting_flow:
        state["agent"] = "meeting"
    else:
        state["agent"] = route_request(state["message"])

    # Stable per-turn baseline. supervisor_node runs once per user message
    # (retries loop directly back into the agent node, not through here).
    state["turn_profile"] = dict(state["profile"])

    logger.info("Session %s routed to '%s' agent", state["session_id"], state["agent"])
    return state




def make_agent_node(name: str):
    def node(state: AgentState) -> AgentState:
        # retry_count is 0 on the first pass through this node for a given
        # user message, and is set to 1 by evaluation_node BEFORE routing
        # back here for a retry. So this flag reliably tells us which pass
        # we're on.
        is_retry_pass = state.get("retry_count", 0) > 0

        # Always build the working profile from the turn's snapshot, never
        # from `state["profile"]` — this keeps every pass (first or retry)
        # asking for/consuming the same field, instead of the retry seeing
        # an already-advanced profile and consuming the message again into
        # the next field.
        profile = ClientProfile(**state["turn_profile"])
        func = AGENT_FUNCS[name]
        try:
            # Re-run to regenerate the response text (this is what a retry
            # is for). Any mutation `func` makes to `profile` here is on a
            # disposable local object — see below, it's only persisted on
            # the first pass.
            state["response"] = func(state["message"], profile)
        except Exception as exc:
            logger.error("Agent '%s' failed: %s", name, exc)
            state["response"] = "I'm having trouble processing that right now. Could you rephrase your request?"

        if is_retry_pass:
            # Retry: keep the freshly regenerated `state["response"]`, but
            # do NOT touch `state["profile"]` / `state["active_agent"]`
            # again. The user's message was already consumed into the
            # profile on the first pass; a retry must not consume it a
            # second time. Whatever the first pass persisted stays as-is.
            return state

        if name == "meeting":
            # First pass — this is the one authoritative mutation of the
            # profile for this user message. Sync it back so it persists to
            # session memory.
            state["profile"] = profile.model_dump()
            state["active_agent"] = None if is_meeting_info_complete(profile) else "meeting"
        else:
            state["active_agent"] = None

        return state


    return node




def evaluation_node(state: AgentState) -> AgentState:
    _, confidence, reason = evaluate_response(state["message"], state["response"])
    state["confidence"] = confidence
    if confidence < 0.75 and state["retry_count"] == 0:
        state["retry_count"] = 1
        state["retry_reason"] = reason
        logger.warning("Session %s retry triggered (confidence=%.2f): %s", state["session_id"], confidence, reason)
    else:
        state["retry_reason"] = ""
    return state




def route_after_supervisor(state: AgentState) -> str:
    return state["agent"]




def route_after_evaluation(state: AgentState) -> str:
    if state["retry_reason"]:
        return state["agent"]
    return END




def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    for name in AGENT_FUNCS:
        graph.add_node(name, make_agent_node(name))
    graph.add_node("evaluation", evaluation_node)


    graph.set_entry_point("supervisor")
    graph.add_conditional_edges("supervisor", route_after_supervisor, {name: name for name in AGENT_FUNCS})
    for name in AGENT_FUNCS:
        graph.add_edge(name, "evaluation")
    graph.add_conditional_edges(
        "evaluation",
        route_after_evaluation,
        {**{name: name for name in AGENT_FUNCS}, END: END},
    )
    return graph.compile()




compiled_graph = build_graph()