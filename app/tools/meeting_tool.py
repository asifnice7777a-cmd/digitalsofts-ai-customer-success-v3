import uuid
from datetime import datetime, timezone
from langchain_core.tools import tool


@tool
def create_meeting_request(
    client_name: str, preferred_date: str = "next available slot", purpose: str = "project discussion"
) -> str:
    """Create a mocked meeting request/booking for the client with DigitalSofts' team."""
    meeting_id = str(uuid.uuid4())[:8]
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"Meeting request created (ID: {meeting_id}) for {client_name or 'the client'}. "
        f"Purpose: {purpose}. Preferred time: {preferred_date}. "
        f"Created at {created_at}. Our team will confirm via email shortly."
    )
