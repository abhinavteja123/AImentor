"""Experiment 4 — End-to-end synthetic-persona journey simulator.

For each of the 5 personas in ``personas.yaml`` we run a 5-step journey:

    profile -> skill_gap -> roadmap -> chat_turns -> resume_tailor

The DB and LLM are mocked with deterministic stubs so the simulation is
offline and reproducible. We record per-step latency, success, and a rough
token count (whitespace-split length of the generated response) and then
aggregate into a single table for the paper.

The purpose is *not* to evaluate content quality — it is to demonstrate that
the hybrid intent + multi-provider + semantic pipeline completes realistic
journeys under injected faults without stalling.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False

from backend.research.baselines import keyword_matcher
from backend.research.config import (
    DATASETS_DIR,
    GLOBAL_SEED,
    ensure_dirs,
)
from backend.research.experiments.fault_scheduler import build_scenarios
from backend.research.experiments.shared import (
    append_manifest,
    timer,
    write_table,
)
from backend.research.models import intent_rule, semantic_ats


PERSONAS_PATH = DATASETS_DIR / "personas.yaml"


# ---------------------------------------------------------------------------
# Minimal YAML fallback (only what personas.yaml needs)
# ---------------------------------------------------------------------------

def _naive_yaml_load(text: str) -> List[dict]:
    """Very small subset of YAML — lists of mappings with scalar/list values.

    This is only used if pyyaml is not installed; ``personas.yaml`` is the
    only file that flows through here and its shape is known.
    """
    records: List[dict] = []
    current: Optional[dict] = None
    key_stack: List[str] = []

    def _coerce(v: str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            return [x.strip() for x in inner.split(",")]
        if s.isdigit():
            return int(s)
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        return s

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("- "):
            if current is not None:
                records.append(current)
            current = {}
            rest = line[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                current[k.strip()] = _coerce(v)
            key_stack = []
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            # nested list item
            if key_stack:
                parent = key_stack[-1]
                current.setdefault(parent, []).append(_coerce(stripped[2:]))
            continue
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            if v.strip() == "":
                # nested key — list follows
                current[k.strip()] = []
                key_stack = [k.strip()]
            else:
                current[k.strip()] = _coerce(v)
                key_stack = []
    if current is not None:
        records.append(current)
    return records


def _load_personas() -> List[dict]:
    text = PERSONAS_PATH.read_text(encoding="utf-8")
    if _HAS_YAML:
        return yaml.safe_load(text)  # type: ignore[return-value]
    return _naive_yaml_load(text)


# ---------------------------------------------------------------------------
# Deterministic LLM + provider stubs
# ---------------------------------------------------------------------------

@dataclass
class _StubLLM:
    """Deterministic LLM stub driven by a seeded RNG + provider chain.

    Every ``generate(prompt)`` call simulates the multi-provider failover
    path from Exp.1, so the simulator exercises the real reliability path
    without hitting the network.
    """

    request_counter: int = 0
    chain: object = None  # ProviderChain

    def generate(self, prompt: str) -> Tuple[bool, str, float, int]:
        """Return (success, text, latency_ms, fallback_depth)."""
        self.request_counter += 1
        ok, latency, depth = self.chain.run(self.request_counter)  # type: ignore[attr-defined]
        if not ok:
            return False, "", latency, depth
        # Deterministic canned response whose content depends on the prompt.
        body = f"[stub] processed {len(prompt)} chars: " + prompt[:60]
        return True, body, latency, depth


# ---------------------------------------------------------------------------
# Journey steps
# ---------------------------------------------------------------------------

def _skill_gap(persona: dict) -> Dict[str, object]:
    """Approximate the real skill-gap analysis on persona skills vs. role."""
    required = _REQUIRED_FOR_ROLE.get(persona.get("goal_role", ""), [])
    have = {s.lower() for s in persona.get("current_skills", [])}
    missing = [s for s in required if s.lower() not in have]
    return {
        "target_role": persona.get("goal_role"),
        "missing_skills": missing,
        "severity": "high" if len(missing) >= 5 else ("medium" if len(missing) >= 2 else "low"),
    }


def _roadmap(persona: dict, gap: Dict[str, object]) -> List[dict]:
    """Fabricate a 4-week roadmap proportional to the gap size."""
    missing = list(gap.get("missing_skills", []))  # type: ignore[arg-type]
    weeks = max(4, min(12, len(missing)))
    return [
        {"week": i + 1, "focus": missing[i % max(1, len(missing))] if missing else "portfolio"}
        for i in range(weeks)
    ]


def _resume_score(persona: dict) -> Tuple[float, float]:
    """Score persona skills vs. role JD using keyword + semantic matchers."""
    required = _REQUIRED_FOR_ROLE.get(persona.get("goal_role", ""), [])
    resume_text = ", ".join(persona.get("current_skills", []))
    jd_text = ", ".join(required) or persona.get("goal_role", "")
    kw = keyword_matcher.score(resume_text, jd_text)
    sem = semantic_ats.score(resume_text, jd_text)
    return float(kw), float(sem)


# Hand-authored required-skill lists per goal role used in the personas file.
_REQUIRED_FOR_ROLE: Dict[str, List[str]] = {
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "TypeScript", "Testing", "Git"],
    "Data Scientist": ["Python", "Pandas", "NumPy", "SQL", "scikit-learn", "Statistics", "Matplotlib"],
    "Full Stack Developer": ["JavaScript", "React", "Node.js", "Express", "PostgreSQL", "Docker", "Git"],
    "Staff Engineer": ["System Design", "Distributed Systems", "Leadership", "Kubernetes", "Observability"],
    "Machine Learning Engineer": ["Python", "PyTorch", "TensorFlow", "Docker", "MLOps", "Kubernetes", "SQL"],
}


# ---------------------------------------------------------------------------
# One persona journey
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    name: str
    ok: bool
    latency_ms: float
    tokens: int
    depth: int = 0
    extra: Dict[str, object] = field(default_factory=dict)


def _run_persona(persona: dict, llm: _StubLLM) -> Tuple[bool, List[StepResult]]:
    steps: List[StepResult] = []

    # 1) profile creation — no LLM, local latency only
    with timer() as t:
        profile = {
            "name": persona.get("full_name"),
            "role": persona.get("goal_role"),
            "skills": persona.get("current_skills", []),
        }
    steps.append(StepResult("profile", True, t.elapsed_ms, tokens=len(json.dumps(profile).split())))

    # 2) skill-gap analysis + LLM rationale
    with timer() as t:
        gap = _skill_gap(persona)
        ok, text, lat, depth = llm.generate(
            f"Explain gap for {persona.get('goal_role')}: {gap['missing_skills']}"
        )
    steps.append(StepResult(
        "skill_gap", ok, t.elapsed_ms + lat,
        tokens=len(text.split()) if text else 0, depth=depth,
        extra={"missing": gap["missing_skills"], "severity": gap["severity"]},
    ))

    # 3) roadmap
    with timer() as t:
        plan = _roadmap(persona, gap)
        ok, text, lat, depth = llm.generate(
            f"Build a {len(plan)}-week roadmap for {persona.get('full_name')}."
        )
    steps.append(StepResult(
        "roadmap", ok, t.elapsed_ms + lat,
        tokens=len(text.split()) if text else 0, depth=depth,
        extra={"weeks": len(plan)},
    ))

    # 4) chat turns — each gated by rule-based intent classifier
    chat_ok = True
    turns = persona.get("chat_turns", []) or []
    intents: List[str] = []
    chat_latency = 0.0
    chat_tokens = 0
    max_depth = 0
    for turn in turns:
        intents.append(intent_rule.predict(turn))
        ok, text, lat, depth = llm.generate(turn)
        chat_latency += lat
        chat_tokens += len(text.split()) if text else 0
        max_depth = max(max_depth, depth)
        if not ok:
            chat_ok = False
            break
    steps.append(StepResult(
        "chat", chat_ok, chat_latency, tokens=chat_tokens, depth=max_depth,
        extra={"intents": intents, "n_turns": len(turns)},
    ))

    # 5) resume tailoring — keyword + semantic score + LLM narrative
    with timer() as t:
        kw_score, sem_score = _resume_score(persona)
        ok, text, lat, depth = llm.generate(
            f"Tailor resume for {persona.get('goal_role')} (kw={kw_score:.0f}, sem={sem_score:.0f})"
        )
    steps.append(StepResult(
        "resume_tailor", ok, t.elapsed_ms + lat,
        tokens=len(text.split()) if text else 0, depth=depth,
        extra={"kw_score": round(kw_score, 2), "semantic_score": round(sem_score, 2)},
    ))

    journey_ok = all(s.ok for s in steps)
    return journey_ok, steps


# ---------------------------------------------------------------------------
# Experiment driver
# ---------------------------------------------------------------------------

def run() -> Path:
    ensure_dirs()
    personas = _load_personas()

    chain = build_scenarios()["chain_proposed"]

    rows_out: List[List[object]] = []
    per_persona_dump: List[dict] = []
    total_success = 0

    for persona in personas:
        llm = _StubLLM(chain=chain)
        journey_ok, steps = _run_persona(persona, llm)
        total_success += int(journey_ok)

        total_latency = sum(s.latency_ms for s in steps)
        total_tokens = sum(s.tokens for s in steps)
        max_depth = max((s.depth for s in steps), default=0)

        rows_out.append([
            persona.get("id"),
            persona.get("goal_role"),
            "yes" if journey_ok else "no",
            round(total_latency, 1),
            total_tokens,
            max_depth,
        ])
        per_persona_dump.append({
            "persona_id": persona.get("id"),
            "journey_ok": journey_ok,
            "steps": [
                {
                    "name": s.name,
                    "ok": s.ok,
                    "latency_ms": round(s.latency_ms, 2),
                    "tokens": s.tokens,
                    "depth": s.depth,
                    "extra": s.extra,
                }
                for s in steps
            ],
        })

    headers = ["Persona", "Goal role", "End-to-end OK", "Total latency (ms)", "Total tokens", "Max depth"]
    csv_p, tex_p = write_table(
        name="exp4_simulator",
        headers=headers,
        rows=rows_out,
        caption=(
            "End-to-end synthetic persona journeys (profile $\\to$ skill-gap $\\to$ "
            "roadmap $\\to$ chat $\\to$ resume) through the proposed three-provider chain."
        ),
        label="tab:simulator",
    )

    # Side artefact: full per-step trace for appendix / reproducibility.
    trace_path = Path(csv_p).parent / "exp4_journey_trace.json"
    trace_path.write_text(json.dumps(per_persona_dump, indent=2), encoding="utf-8")

    append_manifest({
        "experiment": "exp4_simulator",
        "n_personas": len(personas),
        "success_rate": total_success / len(personas) if personas else 0.0,
        "csv": str(csv_p),
        "tex": str(tex_p),
        "trace": str(trace_path),
    })
    return csv_p


if __name__ == "__main__":
    p = run()
    print(f"Exp.4 complete -> {p}")
