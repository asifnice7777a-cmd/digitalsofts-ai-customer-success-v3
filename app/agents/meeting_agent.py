import re
from app.tools.meeting_tool import create_meeting_request
from app.tools.email_tool import send_confirmation_email
from app.tools.knowledge_tool import search_company_knowledge
from app.llm import call_llm_with_tools
from app.memory.session_memory import ClientProfile
from app.logging_config import logger

# Reused (imported, not modified) from supervisor.py so date/time/name/company
# detection stays consistent across the app instead of duplicating divergent
# regexes here.
from app.agents.supervisor import (
    MEETING_DATE_PATTERN,
    MEETING_TIME_PATTERN,
    NAME_PATTERN,
    COMPANY_PATTERN,
    SALES_KEYWORDS,
    TECH_KEYWORDS,
    DOC_KEYWORDS,
    QUESTION_STARTERS,
)


# ---------------------------------------------------------------------------
# KNOWN LIMITATION (schema constraint, documented per instructions not to
# modify session_memory.py):
#
# ClientProfile has no `last_name` field. First and last name are both stored
# in `client_name` ("First Last"), and "has the last name been collected yet"
# is inferred by checking whether client_name contains two or more words.
# This works for the common case but can misfire for a middle name or a
# double-barrelled surname (e.g. "Mary Ann Smith" or "Van Der Berg"). If
# exact separate storage is ever needed, the correct fix is a one-line
# additive `last_name: Optional[str] = None` on ClientProfile — not done
# here since modifying memory was explicitly out of scope.
#
# Contact Number has no persistence problem: in this flow, the phone-number
# question is resolved and the booking happens in the SAME reply, so it only
# ever needs to be a local variable for that one turn — no schema change
# needed.
# ---------------------------------------------------------------------------


# Required fields, collected strictly in this order.
REQUIRED_FIELDS = [
    ("client_name", "your first name"),
    ("company", "your company name"),
    ("meeting_date", "your preferred meeting date"),
    ("meeting_time", "your preferred meeting time"),
]

DECLINE_KEYWORDS = [
    "skip", "no thanks", "no thank you", "none", "n/a", "not now",
    "don't have", "do not have", "prefer not", "no email", "continue",
]

# Short standalone replies that mean "decline"/"skip this optional step" but
# would be unsafe to match as a substring (e.g. "no" inside "not now" or
# "know"), so they're checked against the whole (stripped) reply instead.
DECLINE_EXACT = {"skip", "no", "none", "n/a", "continue"}

# Simple, permissive email shape check: local part, "@", domain with a dot.
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Simple, permissive phone shape check: optional leading "+", then 7-15
# digits, allowing spaces/dashes/parentheses as separators. Deliberately
# excludes letters and colons so time-like answers ("12:00 AM") can't be
# mistaken for a phone number.
PHONE_REGEX = re.compile(r"^\+?\d[\d\-\s()]{5,13}\d$")

INVALID_EMAIL_MESSAGE = (
    "That doesn't look like a valid email address. Please enter a valid "
    "email, or type 'skip' to continue without one."
)
INVALID_PHONE_MESSAGE = (
    "That doesn't look like a valid contact number. Please enter a valid "
    "number, or type 'skip' to continue without one."
)
INVALID_DATE_MESSAGE = (
    "That doesn't look like a valid meeting date. Could you share a date "
    "like '26 July 2026' or 'next Friday'?"
)
INVALID_TIME_MESSAGE = (
    "That doesn't look like a valid meeting time. Could you share a time "
    "like '10:30 AM'?"
)

EMAIL_QUESTION_TEXT = (
    "Would you like to provide an email address for the meeting confirmation? "
    "(Optional — type 'skip' to continue without one.)"
)
PHONE_QUESTION_TEXT = (
    "Would you like to provide a contact number as well? "
    "(Optional — type 'skip' to continue without one.)"
)

# Only used to avoid mistaking the very first trigger message (e.g. "Book a
# meeting") for an answer to the (not-yet-asked) first question.
TRIGGER_KEYWORDS = ["book", "schedule", "meeting", "appointment", "call", "demo"]

# Words that signal the user is explicitly changing an already-given answer,
# rather than answering the currently pending question.
CORRECTION_KEYWORDS = [
    "change", "update", "actually", "instead", "correct", "reschedule",
    "make it", "no wait", "sorry", "meant",
]


def _name_complete(profile: ClientProfile) -> bool:
    """True once client_name holds at least two words (first + last)."""
    name = getattr(profile, "client_name", None)
    return bool(name) and len(name.split()) >= 2


def _first_missing_required(profile: ClientProfile):
    """Same generic one-field-at-a-time walk as before, except client_name
    is treated as a two-phase field: first name, then last name, before
    moving on to company/date/time."""
    if not getattr(profile, "client_name", None):
        return "client_name", "your first name"
    if not _name_complete(profile):
        return "client_name", "your last name"
    for field, label in REQUIRED_FIELDS[1:]:
        if not getattr(profile, field, None):
            return field, label
    return None


def _is_fresh_profile(profile: ClientProfile) -> bool:
    return not any(getattr(profile, field, None) for field, _ in REQUIRED_FIELDS)


def is_meeting_info_complete(profile: ClientProfile) -> bool:
    """True only once the meeting has actually been booked — not merely once
    the required fields are present — so the workflow stays active through
    the optional email/phone steps."""
    return bool(getattr(profile, "meeting_booked", False))


def _is_offtopic(lowered: str) -> bool:
    """Heuristic: does this message look like an unrelated question/topic
    switch rather than a plausible direct answer to whatever's currently
    being asked?"""
    stripped = lowered.strip()
    if not stripped:
        return False
    if stripped.endswith("?"):
        return True
    first_word = stripped.split()[0]
    if first_word in QUESTION_STARTERS:
        return True
    if any(k in stripped for k in SALES_KEYWORDS):
        return True
    if any(k in stripped for k in TECH_KEYWORDS):
        return True
    if any(k in stripped for k in DOC_KEYWORDS):
        return True
    return False


def _detect_corrections(text: str, lowered: str, profile: ClientProfile) -> dict:
    """Detect an explicit correction to an ALREADY-collected field (date,
    time, company, or name). Requires a correction keyword to be present, so
    ordinary first-time answers are never mistaken for corrections. Only
    applies to fields that already have a value — a correction keyword
    appearing before a field has ever been set falls through to normal
    collection instead."""
    if not any(k in lowered for k in CORRECTION_KEYWORDS):
        return {}

    corrections = {}

    if getattr(profile, "meeting_time", None):
        time_match = MEETING_TIME_PATTERN.search(text)
        if time_match:
            corrections["meeting_time"] = (time_match.group(0).strip(), "meeting time")

    if getattr(profile, "meeting_date", None):
        date_match = MEETING_DATE_PATTERN.search(text)
        if date_match:
            corrections["meeting_date"] = (date_match.group(0).strip(), "meeting date")

    if getattr(profile, "company", None) and "company" in lowered:
        company_match = COMPANY_PATTERN.search(text)
        if company_match:
            corrections["company"] = (company_match.group(1).strip(), "company name")

    if getattr(profile, "client_name", None) and "name" in lowered:
        name_match = NAME_PATTERN.search(text)
        if name_match:
            corrections["client_name"] = (name_match.group(1).strip(), "name")

    return corrections


def _pending_question(profile: ClientProfile) -> str:
    """Read-only: what would we ask right now, given the current profile
    state? Used both to actually ask, and to remind the user what's still
    pending after answering an off-topic question. Never mutates anything
    and never performs the booking."""
    missing = _first_missing_required(profile)
    if missing:
        _, label = missing
        return f"Thanks! Could you please share {label}?"
    if profile.email is None:
        return EMAIL_QUESTION_TEXT
    return PHONE_QUESTION_TEXT


def run_meeting_agent(message: str, profile: ClientProfile) -> str:
    text = message.strip()
    lowered = text.lower()

    is_trigger_message = _is_fresh_profile(profile) and any(
        k in lowered for k in TRIGGER_KEYWORDS
    )

    if is_trigger_message:
        # Starting a brand-new booking request. Clear any leftover data from
        # a previous, already-completed booking (kept intact until now so it
        # persisted correctly to PostgreSQL after that booking finished).
        for field, _ in REQUIRED_FIELDS:
            setattr(profile, field, None)
        profile.email = None
        profile.meeting_booked = False
        return _pending_question(profile)

    # --- Corrections: explicit changes to an already-collected field -------
    correction_ack = ""
    if not _is_fresh_profile(profile):
        corrections = _detect_corrections(text, lowered, profile)
        if corrections:
            updated_parts = []
            for field, (value, label) in corrections.items():
                setattr(profile, field, value)
                updated_parts.append(f"{label} to {value}")
            correction_ack = "Got it — I've updated your " + ", ".join(updated_parts) + "."

    # --- Off-topic pause: answer it, then remind the user what's pending ---
    # Skipped when this message was already handled as a correction, so a
    # message that both corrects a field AND happens to contain a question
    # mark isn't double-handled.
    if not correction_ack and _is_offtopic(lowered):
        pause_system_prompt = (
            "You are the Meeting Coordinator Agent for DigitalSofts, currently in the middle "
            "of booking a meeting for this client. The client just asked an unrelated question "
            "instead of answering the current booking question. Answer their question briefly "
            "and helpfully, using the tool results if relevant. Do not try to continue the "
            "booking yourself in this reply — that will be handled separately right after. "
            f"Known client info so far: {profile.model_dump()}"
        )
        pause_fallback = "Sure — happy to help with that."
        answer = call_llm_with_tools(
            pause_system_prompt, message, [search_company_knowledge], pause_fallback
        )
        reminder = _pending_question(profile)
        return f"{answer}\n\n{reminder}"

    # --- Consume this message as an answer to whatever's currently pending -
    missing = _first_missing_required(profile)

    if missing and not correction_ack:
        field, label = missing
        if not text:
            return f"Sorry, I didn't catch that. Could you please share {label}?"

        if field == "meeting_date":
            if not MEETING_DATE_PATTERN.search(text):
                return INVALID_DATE_MESSAGE
            profile.meeting_date = text
        elif field == "meeting_time":
            if not MEETING_TIME_PATTERN.search(text):
                return INVALID_TIME_MESSAGE
            profile.meeting_time = text
        elif field == "client_name":
            if not getattr(profile, "client_name", None):
                # First name.
                profile.client_name = text
            else:
                # Last name — append to the first name already stored,
                # rather than overwrite it. See the module-level note on the
                # last-name limitation.
                profile.client_name = f"{profile.client_name} {text}".strip()
        else:
            # company
            profile.company = text

        # Recompute what's next now that this field is filled.
        next_message = _pending_question(profile)
        return f"{correction_ack}\n{next_message}".strip() if correction_ack else next_message

    if missing and correction_ack:
        # A correction was applied, but required fields still aren't fully
        # collected (rare — e.g. correcting a date before time has been
        # given yet). Don't consume this message as the missing field's
        # answer too; just acknowledge the correction and re-ask.
        return f"{correction_ack}\n{_pending_question(profile)}"

    # --- All required fields present: optional email, then optional phone --
    is_decline = lowered.strip() in DECLINE_EXACT or any(k in lowered for k in DECLINE_KEYWORDS)

    if profile.email is None:
        # Email not yet resolved. Was this message the trigger-complete turn
        # (in which case we haven't asked yet) or an actual reply to the
        # email question?
        if not _is_fresh_profile(profile) and _first_missing_required(profile) is None and profile.email is None:
            pass  # fall through to resolution below; see structural note

        if is_decline:
            profile.email = ""  # sentinel: asked and explicitly declined
        elif EMAIL_REGEX.match(text):
            profile.email = text
        else:
            return f"{correction_ack}\n{INVALID_EMAIL_MESSAGE}".strip() if correction_ack else INVALID_EMAIL_MESSAGE

        next_message = _pending_question(profile)
        return f"{correction_ack}\n{next_message}".strip() if correction_ack else next_message

    # Email already resolved (declined or provided) — this message answers
    # the phone-number question. Contact number is intentionally a local
    # variable only: it's used immediately below to complete the booking in
    # this same reply, so it never needs to be persisted across turns.
    contact_number = None
    if not is_decline:
        if not PHONE_REGEX.match(text):
            return f"{correction_ack}\n{INVALID_PHONE_MESSAGE}".strip() if correction_ack else INVALID_PHONE_MESSAGE
        contact_number = text

    # --- Book the meeting ---------------------------------------------------
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
            email_status_note = "A confirmation email has been sent successfully."
        except Exception as exc:
            logger.error("Confirmation email failed for %s: %s", profile.email, exc)
            email_status_note = (
                "The meeting was booked successfully, but the confirmation email could not be delivered."
            )

    name_parts = (profile.client_name or "").split(maxsplit=1)
    first_name_display = name_parts[0] if name_parts else ""
    last_name_display = name_parts[1] if len(name_parts) > 1 else ""

    confirmation_message = (
        "✔ Meeting Confirmed\n"
        f"First Name: {first_name_display}\n"
        f"Last Name: {last_name_display}\n"
        f"Company: {profile.company}\n"
        f"Date: {profile.meeting_date}\n"
        f"Time: {profile.meeting_time}\n"
        + (f"Email: {profile.email}\n" if profile.email else "")
        + (f"Contact Number: {contact_number}\n" if contact_number else "")
        + (f"\n{email_status_note}" if email_status_note else "")
    )

    # Booking is complete. client_name, company, meeting_date, meeting_time,
    # email, and meeting_booked are intentionally left as-is (NOT cleared)
    # so they persist correctly to PostgreSQL and the assistant still knows
    # who the client is on the next turn. The next brand-new booking request
    # resets these via the is_trigger_message block above instead.
    return f"{correction_ack}\n{confirmation_message}".strip() if correction_ack else confirmation_message