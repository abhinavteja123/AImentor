"""Keyword / ontology baseline that mirrors the production tech_keywords_map logic.

We import the ontology from the committed CSV rather than ``ResumeService`` so
the scorer works offline without importing SQLAlchemy models.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from backend.research.config import DATASETS_DIR

_ONTOLOGY: Dict[str, List[str]] | None = None


def _load() -> Dict[str, List[str]]:
    global _ONTOLOGY
    if _ONTOLOGY is not None:
        return _ONTOLOGY
    by_cat: Dict[str, List[str]] = {}
    path = DATASETS_DIR / "tech_skills_ontology.csv"
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            aliases = [a.strip().lower() for a in (row.get("aliases") or "").split(";") if a.strip()]
            names = [row["skill"].lower(), *aliases]
            by_cat.setdefault(row["category"], []).extend(names)
    _ONTOLOGY = by_cat
    return by_cat


_CATEGORY_WEIGHTS: Dict[str, float] = {
    "languages": 1.0,
    "frameworks": 1.0,
    "databases": 0.9,
    "cloud": 0.9,
    "devops": 0.8,
    "tools": 0.6,
    "ai_ml": 1.0,
    "data": 0.9,
    "backend": 0.9,
    "security": 0.7,
    "mobile": 0.8,
    "testing": 0.7,
    "soft_skills": 0.5,
}


def score(resume_text: str, jd_text: str) -> float:
    ontology = _load()
    r = (resume_text or "").lower()
    j = (jd_text or "").lower()

    total = 0.0
    matched = 0.0
    for cat, names in ontology.items():
        w = _CATEGORY_WEIGHTS.get(cat, 0.5)
        present_in_jd = [n for n in names if n in j]
        if not present_in_jd:
            continue
        total += w * len(present_in_jd)
        hit_in_resume = [n for n in present_in_jd if n in r]
        # Diminishing returns: sqrt for per-category hits.
        matched += w * (len(hit_in_resume) ** 0.5) * (len(present_in_jd) ** 0.5)

    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, matched / total * 100.0))
