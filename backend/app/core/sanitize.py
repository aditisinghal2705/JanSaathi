"""
Privacy guard. Citizens sometimes paste Aadhaar numbers, phone numbers or OTPs
into a chat box. None of that is needed to answer a scheme question, and none
of it should ever be sent to a model or written to a log, so we strip it here
before the text goes anywhere else.
"""
import re

REDACTED = "[removed]"

# 12-digit Aadhaar, optionally written as 4-4-4 with spaces or hyphens.
_AADHAAR = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
# 16-digit card numbers, optionally grouped.
_CARD = re.compile(r"(?<!\d)(?:\d{4}[\s-]?){3}\d{4}(?!\d)")
# Indian mobile numbers, with or without +91 / 0.
# Also matches the common grouping 98765 43210.
_MOBILE = re.compile(r"(?<!\d)(?:\+?91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
# "OTP is 123456", "otp: 4821", "OTP 998877"
_OTP = re.compile(r"(?i)\b(?:otp|one[\s-]?time[\s-]?password)\b[^\d]{0,12}\d{4,8}")


def redact_sensitive(text: str) -> tuple[str, bool]:
    """Return (clean_text, was_anything_removed)."""
    original = text
    # Order matters: card (16) before Aadhaar (12) before mobile (10).
    text = _OTP.sub(REDACTED, text)
    text = _CARD.sub(REDACTED, text)
    text = _AADHAAR.sub(REDACTED, text)
    text = _MOBILE.sub(REDACTED, text)
    return text, text != original


def clean_history(history: list, limit: int) -> list[dict]:
    """
    Keep the most recent `limit` turns, redact each, and return plain dicts.
    Accepts pydantic ChatMessage objects or dicts.
    """
    recent = history[-limit:] if limit > 0 else []
    cleaned = []
    for item in recent:
        role = item["role"] if isinstance(item, dict) else item.role
        content = item["content"] if isinstance(item, dict) else item.content
        content, _ = redact_sensitive(content)
        cleaned.append({"role": role, "content": content})
    return cleaned
