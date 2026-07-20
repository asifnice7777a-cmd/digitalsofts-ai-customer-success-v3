from langchain_core.tools import tool


@tool
def generate_proposal_summary(
    client_name: str, company: str, project_type: str, budget: str = "TBD", timeline: str = "TBD"
) -> str:
    """Generate a short project proposal summary for a client based on collected details."""
    return (
        "PROPOSAL SUMMARY\n"
        f"Client: {client_name or 'N/A'} ({company or 'N/A'})\n"
        f"Project Type: {project_type or 'N/A'}\n"
        f"Budget: {budget}\n"
        f"Timeline: {timeline}\n"
        f"DigitalSofts proposes a tailored solution leveraging our expertise in "
        f"{project_type or 'software development'}, delivered within the agreed timeline and budget, "
        "with dedicated project management and post-launch support."
    )
