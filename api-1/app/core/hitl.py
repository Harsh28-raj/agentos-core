"""Human-in-the-loop helpers: reading a user's approval decision and applying it inside tools.

Approvals are resolved with these rules, in order:
  1. Any negative word ("no", "don't", "stop", "cancel", ...) -> REJECT.
     Negatives win, so "no, don't do it" can never be read as approval.
  2. Any hesitant word ("maybe", "wait", "edit", ...) -> None (ask again).
  3. An explicit approval word or phrase ("yes", "confirm", "go ahead", ...) -> CONFIRM.
  4. Anything else -> None (ask again).
Matching is on whole words, so "eyes" is not "yes" and "know" is not "no".
"""
import re
from typing import Any, Literal

Decision = Literal["CONFIRM", "REJECT"]

_NEGATIVE_WORDS = {
    "no", "nope", "nah", "not", "never", "don't", "dont", "do't", "won't", "wont", "can't", "cant",
    "cancel", "cancelled", "reject", "rejected", "stop", "abort", "deny", "denied", "decline",
    "nahi", "nahin", "mat", "ruko",
}
_HESITANT_WORDS = {
    "maybe", "perhaps", "wait", "later", "hold", "hmm", "unsure", "think", "edit", "change",
    "modify", "but", "shayad", "dekh", "?",
}
_AFFIRMATIVE_WORDS = {
    "yes", "y", "yeah", "yep", "yup", "confirm", "confirmed", "approve", "approved", "proceed",
    "ok", "okay", "sure", "haan", "han", "ji", "absolutely", "definitely",
}
_AFFIRMATIVE_PHRASES = [
    "go ahead", "do it", "send it", "looks good", "bhej do", "kar do", "sounds good", "lgtm",
]

_TOKEN_RE = re.compile(r"[a-z']+|\?")


def classify_approval(message: str) -> Decision | None:
    """Maps a free-text chat reply to CONFIRM / REJECT, or None when it is not explicit."""
    text = (message or "").lower().replace("’", "'")
    words = _TOKEN_RE.findall(text)
    if not words:
        return None
    if any(w in _NEGATIVE_WORDS for w in words):
        return "REJECT"
    if any(w in _HESITANT_WORDS for w in words):
        return None
    joined = " ".join(words)
    if any(w in _AFFIRMATIVE_WORDS for w in words) or any(
        re.search(rf"\b{re.escape(p)}\b", joined) for p in _AFFIRMATIVE_PHRASES
    ):
        return "CONFIRM"
    return None


def resolve_approval(resume_value: Any) -> tuple[bool, dict]:
    """Interprets the value passed to Command(resume=...) inside a tool.

    Accepted values: "CONFIRM" / "REJECT", or {"decision": "CONFIRM"|"REJECT"|"EDIT", "args": {...}}.
    Returns (approved, edited_args).
    """
    if isinstance(resume_value, dict):
        decision = str(resume_value.get("decision", "")).upper()
        args = resume_value.get("args") or {}
        if decision == "EDIT":
            return True, dict(args) if isinstance(args, dict) else {}
        return decision == "CONFIRM", {}
    return str(resume_value).strip().upper() == "CONFIRM", {}
