from app.tools.proposal_tool import generate_proposal_summary
from app.llm import call_llm_with_tools
from app.memory.session_memory import ClientProfile


def run_documentation_agent(message: str, profile: ClientProfile) -> str:
    known_fields = {
        "Client name": profile.client_name,
        "Company": profile.company,
        "Project type": profile.project_type,
        "Preferred technology": profile.preferred_technology,
        "Budget": profile.budget,
        "Timeline": profile.timeline,
    }
    missing_fields = [label for label, value in known_fields.items() if not value]
    missing_note = ", ".join(missing_fields) if missing_fields else "None"

    # Generate the document directly rather than relying on the LLM to decide
    # to call the tool — this guarantees the document body always exists,
    # regardless of whether the underlying model supports/executes tool calls.
    tool_result = generate_proposal_summary.invoke({
        "client_name": profile.client_name or "",
        "company": profile.company or "",
        "project_type": profile.project_type or "",
        "budget": profile.budget or "TBD",
        "timeline": profile.timeline or "TBD",
    })

    # generate_proposal_summary's signature has no preferred_technology parameter,
    # so it's appended here to guarantee it appears in the document.
    tech_line = f"Preferred Technology: {profile.preferred_technology or 'Not specified'}"
    document_text = f"{tool_result}\n{tech_line}"

    system_prompt = (
        "You are the Documentation Agent for DigitalSofts. The document below has ALREADY been "
        "generated from the client's known details. Present it to the client as your answer, in a "
        "friendly, professional tone, including a short one-sentence project summary. You MUST "
        "include every detail from the document below (client name, company, project type, "
        "preferred technology, budget, timeline) — do not omit any of them.\n"
        "AFTER presenting the full document, add a final section titled 'Missing Information:' "
        "listing any fields that are not specified, or 'None' if all are present. "
        "Do NOT reply with only the missing-information line — the full document must always come first.\n\n"
        f"Generated document:\n{document_text}\n\n"
        f"Missing Information: {missing_note}"
    )

    fallback = f"{document_text}\n\nMissing Information: {missing_note}"

    return call_llm_with_tools(system_prompt, message, [], fallback)