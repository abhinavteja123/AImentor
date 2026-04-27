"""Build a real (resume, JD, gold) evaluation set.

Joins three public sources::

    - Livecareer resumes (Kaggle)       -> candidate text
    - LinkedIn 2023 JDs (Kaggle)        -> job text
    - O*NET 28.2 Skills.txt (DoL)       -> independent importance-weighted gold

Output schema is identical to the synthetic ``resume_jd_200.jsonl`` so the
experiment runners are source-agnostic::

    {"resume": str, "jd": str, "role": str,
     "required": [str], "preferred": [str],
     "candidate_skills": [str], "gold_score": float,
     "soc": str, "source": "real"}

Title → SOC resolution uses a deterministic substring match on O*NET's
occupation titles. Callers wanting higher-recall resolution should plug in
the O*NET Sample Titles table and match on that; the fixture set of 5 tech
and adjacent occupations was chosen because their titles match 1:1.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.research.config import DATASETS_DIR
from backend.research.data_adapters import jobs as jobs_adapter
from backend.research.data_adapters import resumes as resumes_adapter
from backend.research.data_adapters.onet import (
    gold_match,
    load_skill_ratings,
    occupation_skill_map,
)


def _occupation_titles(skills: List) -> Dict[str, str]:
    return {s.soc: s.title for s in skills if s.title}


def _resolve_soc(title: str, soc_titles: Dict[str, str]) -> Optional[str]:
    t = title.lower()
    best: Tuple[int, Optional[str]] = (0, None)
    for soc, oc_title in soc_titles.items():
        if not oc_title:
            continue
        ot = oc_title.lower().rstrip("s")
        if ot in t or t in ot:
            score = len(ot)
            if score > best[0]:
                best = (score, soc)
    return best[1]


_SKILL_TOKEN = re.compile(r"[A-Za-z][A-Za-z +\-\.]{2,}")


def _extract_skills(text: str, vocabulary: List[str]) -> List[str]:
    lc = text.lower()
    hits: List[str] = []
    for skill in vocabulary:
        if skill.lower() in lc:
            hits.append(skill)
    return hits


def generate(
    *,
    seed: int = 13,
    max_pairs: int = 200,
    out_path: Optional[Path] = None,
) -> Path:
    rnd = random.Random(seed)
    ratings = load_skill_ratings()
    smap = occupation_skill_map(ratings)
    soc_titles = _occupation_titles(ratings)
    vocabulary = sorted({s for skills in smap.values() for s, _ in skills})

    jd_rows = jobs_adapter.load()
    resume_rows = resumes_adapter.load()
    if not jd_rows or not resume_rows:
        raise RuntimeError("no resumes or jobs available; check fixtures or real files")

    out = out_path or (DATASETS_DIR / "resume_jd_real.jsonl")
    written = 0
    with out.open("w", encoding="utf-8") as f:
        for jd in jd_rows:
            soc = _resolve_soc(jd.title, soc_titles)
            if soc is None:
                continue
            required = [s for s, _ in smap.get(soc, [])][:5]
            preferred = [s for s, _ in smap.get(soc, [])][5:10]

            for res in rnd.sample(resume_rows, k=min(len(resume_rows), max_pairs // max(1, len(jd_rows)) + 1)):
                candidate_skills = _extract_skills(res.text, vocabulary)
                gold_unit = gold_match(candidate_skills, soc, smap)
                gold_score = round(100.0 * gold_unit, 2)

                row = {
                    "resume": res.text,
                    "jd": jd.description,
                    "role": jd.title,
                    "required": required,
                    "preferred": preferred,
                    "candidate_skills": candidate_skills,
                    "gold_score": gold_score,
                    "soc": soc,
                    "source": "real",
                }
                f.write(json.dumps(row) + "\n")
                written += 1
                if written >= max_pairs:
                    break
            if written >= max_pairs:
                break
    return out


if __name__ == "__main__":  # pragma: no cover
    p = generate()
    print(f"wrote {p}")
