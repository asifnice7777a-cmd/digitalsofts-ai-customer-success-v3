from typing import Tuple


def evaluate_response(user_message: str, response: str) -> Tuple[bool, float, str]:
    """Returns (is_complete, confidence_score, retry_reason)."""
    if not response or len(response.strip()) < 20:
        return False, 0.4, "Response too short or empty"

    completeness = True
    confidence = 0.9
    reason = ""
    word_count = len(response.split())

    if word_count < 15:
        confidence = 0.6
        reason = "Response lacks sufficient detail"
        completeness = False

    lowered = response.lower()
    if "error" in lowered or "sorry, i cannot" in lowered:
        confidence = min(confidence, 0.5)
        reason = "Response indicates an error or refusal"
        completeness = False

    if user_message.strip().endswith("?") and "?" not in response and word_count < 25:
        confidence = min(confidence, 0.65)
        reason = reason or "Question may not be fully addressed"
        completeness = False

    return completeness, round(confidence, 2), reason
