"""Livecareer resume-dataset adapter (Kaggle, ~2.4k rows).

Expected file: ``datasets/external/livecareer_resumes.csv`` with columns::

    Category,Resume_str   (or Category,Resume_text,Resume_html — we read the first text-like column)

Per the Kaggle TOS we do not auto-download this file. The research repo
ships a tiny 6-row fixture under ``datasets/external/livecareer_fixture.csv``
so the adapter and downstream tests run without the user dropping anything.

Every resume passes through :mod:`backend.research.ethics.pii_redactor`
before returning so no PII reaches a model or log line.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from backend.research.config import DATASETS_DIR
from backend.research.ethics.pii_redactor import redact_string

EXTERNAL = DATASETS_DIR / "external"
CANONICAL = EXTERNAL / "livecareer_resumes.csv"
FIXTURE = EXTERNAL / "livecareer_fixture.csv"


@dataclass(frozen=True)
class Resume:
    category: str
    text: str
    source: str


def _resolve_source(path: Optional[Path]) -> Path:
    if path is not None:
        return path
    if CANONICAL.exists():
        return CANONICAL
    if FIXTURE.exists():
        return FIXTURE
    raise FileNotFoundError(
        "No resume CSV found. Place the Kaggle Livecareer dataset at "
        f"{CANONICAL} or rely on the shipped fixture."
    )


def _pick_text_column(fieldnames: Iterable[str]) -> str:
    preferred = ("Resume_str", "Resume", "Resume_text", "resume", "text")
    lc = {f.lower(): f for f in fieldnames}
    for k in preferred:
        if k in fieldnames:
            return k
        if k.lower() in lc:
            return lc[k.lower()]
    raise KeyError(f"no recognisable resume text column in {list(fieldnames)}")


def load(
    path: Optional[Path] = None,
    *,
    redact_pii: bool = True,
    limit: Optional[int] = None,
) -> List[Resume]:
    src = _resolve_source(path)
    rows: List[Resume] = []
    with src.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return rows
        text_col = _pick_text_column(reader.fieldnames)
        for row in reader:
            raw_text = (row.get(text_col) or "").strip()
            if not raw_text:
                continue
            text = redact_string(raw_text) if redact_pii else raw_text
            rows.append(
                Resume(
                    category=(row.get("Category") or row.get("category") or "").strip(),
                    text=text,
                    source=src.name,
                )
            )
            if limit is not None and len(rows) >= limit:
                break
    return rows
