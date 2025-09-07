from __future__ import annotations

import re


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


# Common phone patterns, permissive but conservative to avoid over-redaction
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s.-]?\d{3,4}[\s.-]?\d{3,4}"
)


URL_RE = re.compile(
    r"\b(?:(?:https?://)|(?:www\.))[-A-Za-z0-9@:%._+~#=]{1,256}"
    r"\.[A-Za-z]{2,63}\b(?:[-A-Za-z0-9()@:%_+.~#?&/=]*)"
)


def redact_pii(text: str) -> str:
    """Mask obvious PII like emails, phone numbers, and links.

    Replaces matches with placeholders: [EMAIL], [PHONE], [LINK].
    """
    if not text:
        return text
    redacted = EMAIL_RE.sub("[EMAIL]", text)
    redacted = PHONE_RE.sub("[PHONE]", redacted)
    redacted = URL_RE.sub("[LINK]", redacted)
    return redacted

