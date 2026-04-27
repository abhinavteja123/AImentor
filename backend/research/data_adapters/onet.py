"""O*NET 28.2 Skills taxonomy adapter.

Why
---
Exp.3 evaluates ATS scorers against a synthetic gold score. Reviewers will
flag that as circular — the same keyword overlap that scorers use is also
what generates the gold. O*NET provides an *independent*, government-
maintained occupation×skill importance matrix (US Department of Labor).
We derive a gold per (resume, JD) pair from::

    gold(R, J) = sum_s { IM(s, soc(J)) · 1[s in R] } / sum_s { IM(s, soc(J)) }

clipped to [0, 1], where ``IM`` is O*NET's 1-5 Importance rating.

Data files
----------
Users drop the O*NET 28.2 release (from https://www.onetcenter.org/database.html)
into ``datasets/external/onet/`` as::

    Skills.txt                (tab-separated; IM + LV scores per SOC×skill)
    Occupation Data.txt       (tab-separated; SOC → title, description)

Files are *not* auto-downloaded to respect the O*NET data-use agreement.
A minimal 5-occupation fixture is checked in at ``datasets/external/onet_fixture/``
so tests can run without the full dump.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from backend.research.config import DATASETS_DIR

ONET_DIR = DATASETS_DIR / "external" / "onet"
FIXTURE_DIR = DATASETS_DIR / "external" / "onet_fixture"


@dataclass(frozen=True)
class SkillRating:
    soc: str
    title: str
    skill: str
    importance: float  # 1.0-5.0 (IM scale)
    level: Optional[float] = None  # 0.0-7.0 (LV scale), optional

    @property
    def importance_norm(self) -> float:
        """Rescale IM from [1, 5] → [0, 1]."""
        return max(0.0, (self.importance - 1.0) / 4.0)


def _resolve_source(path: Optional[Path] = None) -> Path:
    if path is not None:
        return path
    if (ONET_DIR / "Skills.txt").exists():
        return ONET_DIR
    if (FIXTURE_DIR / "Skills.txt").exists():
        return FIXTURE_DIR
    raise FileNotFoundError(
        "Neither datasets/external/onet/Skills.txt nor the fixture exists. "
        "Download O*NET 28.2 from https://www.onetcenter.org/database.html or "
        "rely on onet_fixture for testing."
    )


def load_skill_ratings(
    src: Optional[Path] = None,
    *,
    scale: str = "IM",
) -> List[SkillRating]:
    """Return every (SOC, skill, importance) triple on the chosen scale."""
    src = _resolve_source(src)
    skills_path = src / "Skills.txt"
    occ_path = src / "Occupation Data.txt"

    titles: Dict[str, str] = {}
    if occ_path.exists():
        with occ_path.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f, delimiter="\t")
            for row in r:
                code = row.get("O*NET-SOC Code") or row.get("Occupation Code")
                title = row.get("Title") or ""
                if code:
                    titles[code] = title

    out: List[SkillRating] = []
    with skills_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if row.get("Scale ID") != scale:
                continue
            soc = row.get("O*NET-SOC Code") or ""
            skill = (row.get("Element Name") or "").strip()
            try:
                val = float(row.get("Data Value") or 0.0)
            except ValueError:
                continue
            if not soc or not skill:
                continue
            out.append(
                SkillRating(
                    soc=soc,
                    title=titles.get(soc, ""),
                    skill=skill,
                    importance=val,
                )
            )
    return out


def occupation_skill_map(
    ratings: Iterable[SkillRating],
    *,
    min_importance: float = 2.5,
) -> Dict[str, List[Tuple[str, float]]]:
    """Group ratings into ``{soc: [(skill, importance), ...]}`` sorted desc.

    Skills with ``importance < min_importance`` are dropped (O*NET docs
    treat anything below ~2.5 as non-essential to the occupation).
    """
    acc: Dict[str, List[Tuple[str, float]]] = {}
    for r in ratings:
        if r.importance < min_importance:
            continue
        acc.setdefault(r.soc, []).append((r.skill, r.importance))
    for soc in acc:
        acc[soc].sort(key=lambda t: t[1], reverse=True)
    return acc


def gold_match(
    resume_skills: Iterable[str],
    occupation_soc: str,
    skill_map: Dict[str, List[Tuple[str, float]]],
) -> float:
    """Importance-weighted skill coverage ∈ [0, 1].

    Case-insensitive substring/contains matching on skill names — lightweight
    but defensible (O*NET skills are short phrases like "Active Listening"
    or "Critical Thinking").
    """
    required = skill_map.get(occupation_soc, [])
    if not required:
        return 0.0
    resume_lower = " \n ".join(s.lower() for s in resume_skills)
    matched = 0.0
    total = 0.0
    for skill, imp in required:
        total += imp
        if skill.lower() in resume_lower:
            matched += imp
    if total == 0:
        return 0.0
    return min(1.0, matched / total)
