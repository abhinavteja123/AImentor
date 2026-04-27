"""Synthesize the 10 000-prompt suite used by Exp.1 (LLM-failover reliability).

Each prompt row has:
    {"id": int, "task": str, "difficulty": str, "system": str, "user": str}

We generate a stratified mix across four task types so the suite exercises
every prompt-shape the production system emits (chat, skill-gap, roadmap,
resume-tailoring). Deterministic given :data:`GLOBAL_SEED`.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Iterator, List

from backend.research.config import DATASETS_DIR, GLOBAL_SEED, ensure_dirs

TASKS: List[str] = ["chat", "skill_gap", "roadmap", "resume_tailor"]
DIFFICULTIES: List[str] = ["easy", "medium", "hard"]

ROLE_POOL: List[str] = [
    "Frontend Developer", "Backend Developer", "Full Stack Developer",
    "Data Scientist", "Machine Learning Engineer", "DevOps Engineer",
    "Mobile Developer", "Site Reliability Engineer", "Data Engineer",
    "Security Engineer", "Cloud Architect", "Platform Engineer",
]

SKILL_POOL: List[str] = [
    "Python", "JavaScript", "TypeScript", "Go", "React", "Node.js",
    "Django", "FastAPI", "PostgreSQL", "MongoDB", "Docker", "Kubernetes",
    "AWS", "GCP", "Git", "SQL", "TensorFlow", "PyTorch", "Pandas",
    "NumPy", "Redis", "GraphQL", "REST API", "CI/CD",
]

CHAT_TEMPLATES = [
    "I'm stuck on {topic}, can you help?",
    "Explain {topic} like I'm new to it.",
    "Why is {topic} important for a {role}?",
    "What's the next step after learning {topic}?",
    "I feel like giving up on {topic}. Any motivation?",
]

SKILL_GAP_TEMPLATES = [
    "Analyze my skill gap for {role}.",
    "What skills am I missing to become a {role}?",
    "Compare my profile to a {role} target.",
]

ROADMAP_TEMPLATES = [
    "Build me a {weeks}-week roadmap to become a {role}.",
    "Create a learning plan for {role} at {intensity} intensity.",
    "Plan my next month toward a {role} role.",
]

RESUME_TEMPLATES = [
    "Tailor my resume for this job: {role} requiring {skill1} and {skill2}.",
    "Optimize my resume summary for a {role} position.",
    "Score my resume against a {role} job description.",
]


def _iter_prompts(rng: random.Random, n: int) -> Iterator[dict]:
    for i in range(n):
        task = rng.choice(TASKS)
        diff = rng.choices(DIFFICULTIES, weights=[0.5, 0.35, 0.15])[0]
        role = rng.choice(ROLE_POOL)
        topic = rng.choice(SKILL_POOL)
        s1, s2 = rng.sample(SKILL_POOL, 2)

        if task == "chat":
            user = rng.choice(CHAT_TEMPLATES).format(topic=topic, role=role)
            system = "You are a warm, knowledgeable AI career mentor."
        elif task == "skill_gap":
            user = rng.choice(SKILL_GAP_TEMPLATES).format(role=role)
            system = "You are a career advisor. Return JSON only."
        elif task == "roadmap":
            user = rng.choice(ROADMAP_TEMPLATES).format(
                weeks=rng.choice([4, 8, 12, 16]),
                role=role,
                intensity=rng.choice(["low", "medium", "high"]),
            )
            system = "You are a curriculum designer. Return JSON only."
        else:  # resume_tailor
            user = rng.choice(RESUME_TEMPLATES).format(role=role, skill1=s1, skill2=s2)
            system = "You tailor resumes. Return JSON only."

        yield {
            "id": i,
            "task": task,
            "difficulty": diff,
            "system": system,
            "user": user,
        }


def generate(n: int = 10_000, seed: int = GLOBAL_SEED) -> Path:
    ensure_dirs()
    rng = random.Random(seed)
    out = DATASETS_DIR / "prompts_10k.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for row in _iter_prompts(rng, n):
            f.write(json.dumps(row) + "\n")
    return out


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
