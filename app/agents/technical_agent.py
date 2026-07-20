from app.tools.knowledge_tool import search_company_knowledge
from app.tools.timeline_tool import estimate_project_timeline
from app.llm import call_llm_with_tools
from app.memory.session_memory import ClientProfile


def run_technical_agent(message: str, profile: ClientProfile) -> str:
    tools = [search_company_knowledge, estimate_project_timeline]

    system_prompt = (
        "You are the Technical Consultant Agent for DigitalSofts. "
        "Provide clear, accurate technical guidance about architecture, technology stack, and integrations. "
        f"Known client details — Client name: {profile.client_name or 'not specified'}, "
        f"Company: {profile.company or 'not specified'}, "
        f"Project type: {profile.project_type or 'not specified'}, "
        f"Preferred technology: {profile.preferred_technology or 'not specified'}, "
        f"Budget: {profile.budget or 'not specified'}, "
        f"Timeline: {profile.timeline or 'not specified'}. "
        "You have access to tools to search the company knowledge base and estimate project timelines. "
        "Use them whenever they would help answer the client's question."
    )

    fallback = "Thanks for your question! Let me look into the technical details and get back to you shortly."

    return call_llm_with_tools(system_prompt, message, tools, fallback)