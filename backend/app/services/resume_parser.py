"""
Resume parser — stateless PDF/DOCX-free text extraction + LLM profile extraction.

Pipeline:
    bytes -> extract_text_from_pdf(bytes) -> str
    str   -> parse_profile_from_text(text, llm) -> dict (matches ProfileUpdate fields)

No DB writes. Caller receives a suggestion payload and decides what to persist.
"""

from __future__ import annotations

import io
import json
import logging
from typing import Any, Dict

from pypdf import PdfReader

from .ai.llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


# Fields the LLM should try to populate. Keys MUST match the ProfileUpdate
# schema and the profile-page React state exactly — anything off-schema gets
# dropped in _sanitize.
PROFILE_FIELDS_SCHEMA = """{
  "goal_role": "string | null (target career role, e.g. 'Data Scientist')",
  "experience_level": "one of: beginner | intermediate | advanced | null",
  "current_education": "string | null (most recent degree + institution, one line)",
  "graduation_year": "integer | null (4-digit year)",
  "bio": "string | null (2-3 sentence professional summary)",
  "linkedin_url": "string | null",
  "github_url": "string | null",
  "portfolio_url": "string | null",
  "phone": "string | null",
  "location": "string | null (city, country)",
  "website_url": "string | null",
  "education_data": "array of { institution, degree, field_of_study, start_year, end_year, cgpa, location } | null",
  "experience_data": "array of { company, role, location, start_date, end_date, bullet_points (array of strings) } | null",
  "projects_data": "array of { title, description, technologies (array of strings), github_url, demo_url, highlights (array of strings) } | null",
  "certifications_data": "array of { name, issuer, date_obtained, credential_url } | null",
  "extracurricular_data": "array of { organization, role, achievements (array of strings) } | null",
  "technical_skills_data": "object with keys: languages, frameworks_and_tools, databases, cloud_platforms, other — each value is an array of strings | null"
}"""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF byte stream. Returns empty string on failure."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        logger.warning("pypdf failed to open PDF: %s", exc)
        return ""

    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as exc:
            logger.warning("pypdf page extract failed: %s", exc)
    return "\n".join(p for p in parts if p).strip()


async def parse_profile_from_text(
    text: str,
    llm: LLMClient | None = None,
) -> Dict[str, Any]:
    """
    Ask the LLM to structure resume text into profile-shaped JSON.
    Returns {} if the text is empty or parsing fails. Caller decides what to do.
    """
    if not text or not text.strip():
        return {}

    llm = llm or get_llm_client()

    system_prompt = (
        "You extract structured profile data from resumes. Return ONLY JSON. "
        "Use the EXACT keys from the user's schema — do not rename, abbreviate, or "
        "add new keys. Every array-typed field must be a JSON array, never a "
        "comma-separated string. If a field is not present, omit it or use null — "
        "never invent. Dates: YYYY-MM or YYYY. Years: 4-digit integers. "
        "For experience_level, infer from years of experience: <1 year = beginner, "
        "1-4 = intermediate, 5+ = advanced. "
        "Extract EVERY project, experience entry, certification, and activity you "
        "find — do not summarize or skip entries."
    )

    user_prompt = (
        f"Extract into this exact JSON shape. Keys and nesting must match exactly; "
        f"arrays must be arrays (not strings):\n{PROFILE_FIELDS_SCHEMA}\n\n"
        f"Resume text:\n---\n{text[:15000]}\n---\n\n"
        "Respond with a single JSON object matching the shape above. "
        "Include every resume entry — be exhaustive, not selective."
    )

    try:
        payload = await llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
        )
    except Exception as exc:
        logger.warning("LLM profile extraction failed: %s", exc)
        return {}

    if not isinstance(payload, dict):
        logger.warning("LLM returned non-dict payload: %r", type(payload))
        return {}

    return _sanitize(payload)


_ALLOWED_KEYS = {
    "goal_role", "experience_level", "current_education", "graduation_year",
    "bio", "linkedin_url", "github_url", "portfolio_url", "phone", "location",
    "website_url", "education_data", "experience_data", "projects_data",
    "certifications_data", "extracurricular_data", "technical_skills_data",
}

# For each array-of-objects section, the nested fields that MUST be arrays of
# strings. Anything the LLM returns as a comma-joined string gets split.
_STRING_ARRAY_SUBFIELDS = {
    "experience_data": {"bullet_points"},
    "projects_data": {"technologies", "highlights"},
    "extracurricular_data": {"achievements"},
}

# Common LLM field-name drift -> the canonical name the frontend expects.
_SUBFIELD_ALIASES = {
    "education_data": {"field": "field_of_study", "gpa": "cgpa"},
    "experience_data": {"title": "role", "highlights": "bullet_points", "description": "bullet_points"},
    "projects_data": {"name": "title", "url": "github_url"},
    "certifications_data": {"date": "date_obtained", "url": "credential_url"},
    "extracurricular_data": {"title": "organization", "description": "achievements"},
}


def _as_string_array(val: Any) -> list[str]:
    """Coerce strings / comma-joined / nested lists into a clean list[str]."""
    if val is None or val == "":
        return []
    if isinstance(val, list):
        return [str(item).strip() for item in val if str(item).strip()]
    if isinstance(val, str):
        # Split on newlines first (bullet points), then commas as fallback
        if "\n" in val:
            parts = [p.strip(" -•*\t") for p in val.split("\n")]
        else:
            parts = [p.strip() for p in val.split(",")]
        return [p for p in parts if p]
    return [str(val).strip()]


def _normalize_section(section_key: str, items: Any) -> list[dict]:
    """Rename aliased keys, coerce string_array fields, drop empty items."""
    if not isinstance(items, list):
        return []
    aliases = _SUBFIELD_ALIASES.get(section_key, {})
    array_fields = _STRING_ARRAY_SUBFIELDS.get(section_key, set())
    out: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        renamed: dict = {}
        for k, v in item.items():
            # Merge aliased keys into canonical (don't overwrite if canonical already present)
            canon = aliases.get(k, k)
            if canon in array_fields:
                existing = renamed.get(canon)
                new_vals = _as_string_array(v)
                if existing:
                    renamed[canon] = list(dict.fromkeys([*existing, *new_vals]))
                else:
                    renamed[canon] = new_vals
            else:
                if canon not in renamed and v not in (None, "", [], {}):
                    renamed[canon] = v
        # Drop rows that are empty after cleanup
        if any(v not in (None, "", [], {}) for v in renamed.values()):
            out.append(renamed)
    return out


def _normalize_technical_skills(val: Any) -> dict:
    """Ensure each category is a list[str]. Unknown categories are kept under 'other'."""
    if not isinstance(val, dict):
        return {}
    canonical_keys = {"languages", "frameworks_and_tools", "databases", "cloud_platforms", "other"}
    out: dict[str, list[str]] = {k: [] for k in canonical_keys}
    for k, v in val.items():
        key = k.strip().lower().replace(" ", "_").replace("&", "and")
        # Common aliases
        if key in {"frameworks", "tools", "frameworks_tools"}:
            key = "frameworks_and_tools"
        if key in {"languages_and_frameworks", "programming_languages"}:
            key = "languages"
        target = key if key in canonical_keys else "other"
        out[target].extend(_as_string_array(v))
    # Drop categories that ended up empty, dedupe preserving order
    return {k: list(dict.fromkeys(vs)) for k, vs in out.items() if vs}


def _sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drop unknown top-level keys; deep-normalize nested arrays and object maps
    so downstream consumers never see a string where they expect an array.
    """
    out: Dict[str, Any] = {}
    for key, val in payload.items():
        if key not in _ALLOWED_KEYS:
            continue
        if val is None or val == "" or val == [] or val == {}:
            continue
        if key == "graduation_year":
            try:
                out[key] = int(val)
            except (TypeError, ValueError):
                continue
        elif key == "experience_level":
            norm = str(val).strip().lower()
            if norm in {"beginner", "intermediate", "advanced"}:
                out[key] = norm
        elif key in _SUBFIELD_ALIASES:
            normalized = _normalize_section(key, val)
            if normalized:
                out[key] = normalized
        elif key == "technical_skills_data":
            normalized = _normalize_technical_skills(val)
            if normalized:
                out[key] = normalized
        else:
            out[key] = val
    return out
