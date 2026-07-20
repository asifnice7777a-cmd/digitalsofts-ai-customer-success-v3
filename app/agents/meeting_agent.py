from app.tools.meeting_tool import create_meeting_request
from app.tools.email_tool import send_confirmation_email
from app.llm import call_llm_with_tools
from app.memory.session_memory import ClientProfile
from app.logging_config import logger
from app.agents.supervisor import QUESTION_STARTERS
import re


# Required fields, collected strictly in this order — one at a time.
REQUIRED_FIELDS = [
    ("client_name", "your first name"),
    ("company", "your company name"),
    ("meeting_date", "your preferred meeting date"),
    ("meeting_time", "your preferred meeting time"),
]

DECLINE_KEYWORDS = [
    "skip", "no thanks", "no thank you", "none", "n/a", "not now",
    "don't have", "do not have", "prefer not", "no email",
]

# Only used to avoid mistaking the very first trigger message (e.g. "Book a
# meeting") for an answer to the (not-yet-asked) first question.
TRIGGER_KEYWORDS = ["book", "schedule", "meeting", "appointment", "call", "demo"]

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")


def _first_missing_required(profile: ClientProfile):
    for field, label in REQUIRED_FIELDS:
        if not getattr(profile, field, None):
            return field, label
    return None


def _is_fresh_profile(profile: ClientProfile) -> bool:
    return not any(getattr(profile, field, None) for field, _ in REQUIRED_FIELDS)


def _looks_like_unrelated_question(message: str) -> bool:
    """Detects whether a message looks like an unrelated question rather than
    an answer to the booking field currently being requested."""
    stripped = message.strip()
    if not stripped:
        return False
    if stripped.endswith("?"):
        return True
    first_word = stripped.split()[0].lower()
    return first_word in QUESTION_STARTERS


def is_meeting_info_complete(profile: ClientProfile) -> bool:
    """True once the meeting has actually been booked, OR the workflow was
    paused/cancelled due to an unrelated message — either way, this signals
    graph.py to release the active_agent lock so routing resumes normally."""
    return bool(getattr(profile, "meeting_booked", False))


def run_meeting_agent(message: str, profile: ClientProfile) -> str:
    text = message.strip()
    is_trigger_message = _is_fresh_profile(profile) and any(
        k in text.lower() for k in TRIGGER_KEYWORDS
    )

    # Auto-save plain-text answers into the profile, one field at a time,
    # like a form. Skip this only for the very first message that kicks off
    # the workflow (e.g. "Book a meeting"), so it isn't mistaken for a name.
    consumed_by_required = False
    if not is_trigger_message:
        missing_before = _first_missing_required(profile)
        if missing_before:
            field, label = missing_before

            if _looks_like_unrelated_question(text):
                # This message doesn't look like an answer to the pending
                # field — it looks like an unrelated question. Pause the
                # booking flow and release the active_agent lock so the
                # Supervisor can route the client's real question correctly
                # on their next message.
                profile.meeting_booked = True
                system_prompt = (
                    "You are the Meeting Coordinator Agent for DigitalSofts. The client asked "
                    "something unrelated to the meeting booking while you were collecting their "
                    "details. Briefly let them know you've paused the meeting booking for now, "
                    "and ask them to resend their question so it can be answered properly. "
                    "Do not attempt to answer their question yourself."
                )
                fallback = (
                    "No problem — I've paused the meeting booking for now. Could you resend your "
                    "question so I can make sure it gets answered correctly?"
                )
                return call_llm_with_tools(system_prompt, message, [], fallback)

            if text:
                setattr(profile, field, text)
                consumed_by_required = True

    missing = _first_missing_required(profile)

    if missing:
        field, label = missing
        system_prompt = (
            "You are the Meeting Coordinator Agent for DigitalSofts. "
            "You are collecting details to book a meeting, ONE piece of information at a time. "
            f"Ask the client ONLY for {label}. "
            "Do not ask for any other detail, and do not list multiple questions at once. "
            "Keep it brief and friendly."
        )
        fallback = f"Thanks! Could you please share {label}?"
        return call_llm_with_tools(system_prompt, message, [], fallback)

    # All required fields are present. Handle the optional email step.
    lowered = text.lower()
    is_decline = any(k in lowered for k in DECLINE_KEYWORDS)
    off_topic_email_exit = False

    if not profile.email:
        if consumed_by_required or is_trigger_message:
            system_prompt = (
                "You are the Meeting Coordinator Agent for DigitalSofts. All required meeting "
                "details are known. Ask the client, briefly and warmly, whether they'd like to "
                "provide an email address for the meeting confirmation, and make clear this is "
                "optional."
            )
            fallback = "Would you like to provide an email address for the meeting confirmation? (Optional)"
            return call_llm_with_tools(system_prompt, message, [], fallback)

        email_match = EMAIL_PATTERN.search(text)
        if email_match:
            profile.email = email_match.group(0)
        elif is_decline:
            pass  # leave email empty and proceed to booking
        else:
            off_topic_email_exit = True

    # Required fields present, and the email question has been resolved
    # (email given, declined, or exited due to an unrelated message). Book.
    preferred_date_and_time = f"{profile.meeting_date} at {profile.meeting_time}"
    tool_result = create_meeting_request.invoke({
        "client_name": profile.client_name,
        "preferred_date": preferred_date_and_time,
        "purpose": profile.project_type or "General discussion",
    })
    profile.meeting_booked = True

    email_status_note = ""
    if profile.email:
        try:
            send_confirmation_email.invoke({
                "to_email": profile.email,
                "client_name": profile.client_name,
                "meeting_details": tool_result,
            })
            email_status_note = f" A confirmation email was sent to {profile.email}."
        except Exception as exc:
            logger.error("Confirmation email failed for %s: %s", profile.email, exc)
            email_status_note = (
                " The meeting was booked, but the confirmation email could not be delivered."
            )

    handoff_note = ""
    if off_topic_email_exit:
        handoff_note = (
            " I noticed your last message wasn't an email address, so I went ahead and booked "
            "the meeting without one. Feel free to ask your other question now and I'll make "
            "sure it's handled."
        )

    system_prompt = (
        "You are the Meeting Coordinator Agent for DigitalSofts. The meeting has ALREADY been "
        "booked successfully using the details below. Present a clear confirmation summary to the "
        "client, starting with a checkmark, including their name, company, date, time, and email "
        "(only if one was provided). Do not say you will book it — it is already booked. "
        "Include this note verbatim if present: "
        f"'{email_status_note.strip()}'\n"
        "Include this note verbatim if present, after the confirmation: "
        f"'{handoff_note.strip()}'\n"
        f"Booking details: {tool_result}"
    )
    fallback = (
        "✅ Meeting booked successfully.\n"
        f"Name: {profile.client_name}\n"
        f"Company: {profile.company}\n"
        f"Date: {profile.meeting_date}\n"
        f"Time: {profile.meeting_time}\n"
        + (f"Email: {profile.email}\n" if profile.email else "")
        + email_status_note
        + handoff_note
    )
    return call_llm_with_tools(system_prompt, message, [], fallback)