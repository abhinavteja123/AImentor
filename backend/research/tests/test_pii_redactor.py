"""Unit tests for ethics.pii_redactor.

Covers each regex category, composite redaction (several PII types in one
string), idempotence (redacting twice yields the same output), and count
bookkeeping.
"""

from __future__ import annotations

from backend.research.ethics.pii_redactor import redact, redact_string


def test_email_redacted():
    r = redact("Contact me at jane.doe@example.co.uk for the role.")
    assert "[EMAIL]" in r.redacted
    assert "jane.doe@example.co.uk" not in r.redacted
    assert r.counts.get("email") == 1


def test_phone_redacted():
    r = redact("Call +1 415-555-0123 or 9876543210 any time.")
    assert "[PHONE]" in r.redacted
    assert r.counts.get("phone", 0) >= 1


def test_url_redacted_before_email():
    # URL with an @ must be redacted as URL, not as email.
    r = redact("See https://foo.bar/path?x=1 for details.")
    assert "[URL]" in r.redacted
    assert "foo.bar" not in r.redacted
    assert r.counts.get("url") == 1


def test_ssn_redacted():
    r = redact("SSN: 123-45-6789 on file.")
    assert "[SSN]" in r.redacted
    assert "123-45-6789" not in r.redacted
    assert r.counts.get("ssn") == 1


def test_aadhaar_redacted():
    r = redact("Aadhaar 1234 5678 9012 is confidential.")
    assert "[AADHAAR]" in r.redacted
    assert "1234 5678 9012" not in r.redacted
    assert r.counts.get("aadhaar") == 1


def test_name_heuristic_at_line_start():
    r = redact("John Smith\nSoftware engineer")
    assert "[NAME]" in r.redacted
    assert r.counts.get("name", 0) >= 1


def test_composite_redaction():
    text = (
        "Jane Doe\n"
        "Email: jane@foo.com\n"
        "Phone: +91 9876543210\n"
        "Portfolio: https://jane.dev"
    )
    r = redact(text)
    for tok in ("[EMAIL]", "[PHONE]", "[URL]"):
        assert tok in r.redacted, f"missing {tok}"
    assert "jane@foo.com" not in r.redacted
    assert "jane.dev" not in r.redacted


def test_idempotent():
    text = "Email: x@y.com Phone: 555-1234"
    once = redact_string(text)
    twice = redact_string(once)
    assert once == twice


def test_empty_input():
    r = redact("")
    assert r.redacted == ""
    assert r.counts == {}


def test_no_pii_passes_through():
    text = "This is a perfectly innocuous sentence."
    r = redact(text)
    assert r.redacted == text
    assert r.counts == {}
