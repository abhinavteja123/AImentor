"""LinkedIn Job Postings 2023-2024 adapter (Kaggle, ~124k rows).

Expected file: ``datasets/external/linkedin_jobs_2023.csv`` with the columns
shipped by the Kaggle ``arshkon/linkedin-job-postings`` release::

    job_id,company_name,title,description,skills_desc,location,...

We keep ``title``, ``description``, and ``skills_desc`` (when present),
filter to rows tagged with tech/analyst/data job titles by default, and
cap the return to ``limit`` rows so experiments stay in memory.

A small 6-row fixture ships at ``datasets/external/linkedin_fixture.csv``
so tests pass without the 500 MB download.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from backend.research.config import DATASETS_DIR

EXTERNAL = DATASETS_DIR / "external"
CANONICAL = EXTERNAL / "linkedin_jobs_2023.csv"
FIXTURE = EXTERNAL / "linkedin_fixture.csv"

_TECH_TITLE = re.compile(
    r"\b(software|engineer|developer|data|analyst|scientist|ml|ai|devops|"
    r"security|cloud|backend|frontend|full.?stack|mobile|qa|sre|architect)\b",
    re.I,
)


@dataclass(frozen=True)
class JobPosting:
    job_id: str
    title: str
    company: str
    description: str
    skills_desc: str
    source: str


def _resolve_source(path: Optional[Path]) -> Path:
    if path is not None:
        return path
    if CANONICAL.exists():
        return CANONICAL
    if FIXTURE.exists():
        return FIXTURE
    raise FileNotFoundError(
        "No LinkedIn jobs CSV found. Place the Kaggle file at "
        f"{CANONICAL} or rely on the shipped fixture."
    )


def load(
    path: Optional[Path] = None,
    *,
    tech_only: bool = True,
    limit: Optional[int] = None,
) -> List[JobPosting]:
    src = _resolve_source(path)
    rows: List[JobPosting] = []
    with src.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("title") or "").strip()
            desc = (row.get("description") or "").strip()
            if not title or not desc:
                continue
            if tech_only and not _TECH_TITLE.search(title):
                continue
            rows.append(
                JobPosting(
                    job_id=(row.get("job_id") or "").strip(),
                    title=title,
                    company=(row.get("company_name") or "").strip(),
                    description=desc,
                    skills_desc=(row.get("skills_desc") or "").strip(),
                    source=src.name,
                )
            )
            if limit is not None and len(rows) >= limit:
                break
    return rows
