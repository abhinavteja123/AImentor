"""PII redaction for resume / chat text.

Applied to any user-submitted string before it is logged or written to the
evaluation artifacts. Regexes are intentionally conservative; false positives
(over-redaction) are preferred to leaks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Pattern, Tuple

EMAIL_RE: Pattern[str] = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
)

# E.164, US, and common IN patterns.
PHONE_RE: Pattern[str] = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}",
)

URL_RE: Pattern[str] = re.compile(r"https?://\S+|www\.\S+")

# Quick-and-dirty name heuristic — two consecutive capitalized tokens at start
# of a resume line. Used for logs only, not for real anonymization.
NAME_RE: Pattern[str] = re.compile(
    r"(?m)^([A-Z][a-z]+\s+[A-Z][a-z]+)(?=\s|$|,)",
)

SSN_RE: Pattern[str] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Indian Aadhaar (12 digits, often grouped 4-4-4).
AADHAAR_RE: Pattern[str] = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


@dataclass(frozen=True)
class RedactionReport:
    redacted: str
    counts: Dict[str, int]


def redact(text: str) -> RedactionReport:
    """Redact PII and return the masked string + per-type counts."""
    if not text:
        return RedactionReport(redacted=text or "", counts={})

    counts: Dict[str, int] = {}

    def _apply(pattern: Pattern[str], label: str, token: str, s: str) -> str:
        hits = pattern.findall(s)
        if hits:
            counts[label] = counts.get(label, 0) + len(hits)
        return pattern.sub(token, s)

    # Order matters: URLs before emails (some URLs contain @).
    s = text
    s = _apply(URL_RE, "url", "[URL]", s)
    s = _apply(EMAIL_RE, "email", "[EMAIL]", s)
    s = _apply(SSN_RE, "ssn", "[SSN]", s)
    s = _apply(AADHAAR_RE, "aadhaar", "[AADHAAR]", s)
    # Phones last among numerics — loose pattern catches the rest.
    s = _apply(PHONE_RE, "phone", "[PHONE]", s)
    s = _apply(NAME_RE, "name", "[NAME]", s)

    return RedactionReport(redacted=s, counts=counts)


def redact_string(text: str) -> str:
    """Convenience wrapper returning only the redacted text."""
    return redact(text).redacted


__all__ = ["RedactionReport", "redact", "redact_string"]
