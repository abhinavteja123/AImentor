"""Synthesize 200 (resume, job-description) pairs with a gold match score for Exp.3.

Generation strategy:
    * draw required / preferred skills for a target role from the ontology
    * draw the candidate's skills as a noisy subset (coverage in [0, 1])
    * score_gold = coverage * 100 + Gaussian noise to simulate recruiter jitter
    * resume text is a short faux-resume; JD text is a short faux-posting

The 200-pair target matches the IEEE-paper eval budget. A gold score is always
in [0, 100]. Deterministic given :data:`GLOBAL_SEED`.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

from backend.research.config import DATASETS_DIR, GLOBAL_SEED, ensure_dirs

ONTOLOGY_PATH = DATASETS_DIR / "tech_skills_ontology.csv"

ROLE_SKILL_HINTS: Dict[str, List[str]] = {
    "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Git", "Testing"],
    "Backend Developer": ["Python", "PostgreSQL", "REST API", "Docker", "Git", "SQL", "Testing"],
    "Full Stack Developer": ["JavaScript", "React", "Node.js", "PostgreSQL", "Git", "Docker"],
    "Data Scientist": ["Python", "Pandas", "NumPy", "scikit-learn", "SQL", "Matplotlib"],
    "ML Engineer": ["Python", "PyTorch", "TensorFlow", "Docker", "AWS", "SQL", "Hugging Face"],
    "DevOps Engineer": ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD", "Bash", "Prometheus"],
    "Mobile Developer": ["Kotlin", "Swift", "React Native", "Flutter", "Git", "Testing"],
    "Data Engineer": ["Python", "SQL", "Airflow", "Spark", "Kafka", "PostgreSQL", "dbt"],
    "SRE": ["Linux", "Bash", "Kubernetes", "Prometheus", "Grafana", "AWS", "Terraform"],
}


def _load_ontology() -> Dict[str, List[str]]:
    by_cat: Dict[str, List[str]] = {}
    with ONTOLOGY_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_cat.setdefault(row["category"], []).append(row["skill"])
    return by_cat


def _make_resume(candidate_skills: List[str], role_hint: str, rng: random.Random) -> str:
    years = rng.randint(0, 10)
    lines = [
        f"Candidate target: {role_hint}",
        f"Experience: {years} years",
        "Skills: " + ", ".join(candidate_skills),
        "Recent projects: " + ", ".join(
            rng.sample(candidate_skills, min(3, len(candidate_skills)))
        ) + " based system.",
    ]
    return "\n".join(lines)


def _make_jd(
    role: str,
    required: List[str],
    preferred: List[str],
) -> str:
    return (
        f"Job Title: {role}\n"
        f"Required skills: {', '.join(required)}.\n"
        f"Nice to have: {', '.join(preferred)}.\n"
        "We are seeking a mission-driven engineer to ship production systems."
    )


def _pair(rng: random.Random, ontology: Dict[str, List[str]]) -> dict:
    role = rng.choice(list(ROLE_SKILL_HINTS.keys()))
    hint = ROLE_SKILL_HINTS[role]
    required = rng.sample(hint, k=min(len(hint), rng.randint(3, 5)))
    all_skills = [s for skills in ontology.values() for s in skills]
    preferred = rng.sample([s for s in all_skills if s not in required], k=3)

    coverage = rng.betavariate(2.5, 2.0)  # skew toward moderate coverage
    keep = max(1, int(len(required) * coverage))
    candidate = rng.sample(required, k=keep)
    # Add distractors so resumes are not too short.
    distractors = rng.sample(
        [s for s in all_skills if s not in required and s not in preferred],
        k=rng.randint(2, 6),
    )
    candidate_skills = candidate + distractors
    rng.shuffle(candidate_skills)

    gold = coverage * 100 + rng.gauss(0, 5)
    gold = max(0.0, min(100.0, gold))

    return {
        "resume": _make_resume(candidate_skills, role, rng),
        "jd": _make_jd(role, required, preferred),
        "role": role,
        "required": required,
        "preferred": preferred,
        "candidate_skills": candidate_skills,
        "gold_score": round(gold, 2),
    }


def generate(n: int = 200, seed: int = GLOBAL_SEED) -> Path:
    ensure_dirs()
    rng = random.Random(seed)
    ontology = _load_ontology()
    out = DATASETS_DIR / "resume_jd_200.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for _ in range(n):
            f.write(json.dumps(_pair(rng, ontology)) + "\n")
    return out


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
