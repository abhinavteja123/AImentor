"""Jaccard similarity baseline for resume/JD scoring (Exp.3).

Score = |candidate ∩ required| / |candidate ∪ required| × 100.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/_-]{1,}")


def _tokens(s: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(s or "")]


def score(resume_text: str, jd_text: str) -> float:
    a = set(_tokens(resume_text))
    b = set(_tokens(jd_text))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b) * 100.0


def score_sets(cand_skills: Sequence[str], required: Sequence[str]) -> float:
    a = {s.lower() for s in cand_skills}
    b = {s.lower() for s in required}
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b) * 100.0
