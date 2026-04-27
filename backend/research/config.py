"""Global configuration + reproducibility pins for the research workspace.

Every experiment imports ``GLOBAL_SEED`` and model identifiers from here so
each run is deterministic. Altering anything in this module invalidates the
published numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

GLOBAL_SEED: int = 20260421  # YYYYMMDD of the plan; any run past this uses it.

# Multi-seed sweep for variance estimates. Any reported number uses these five.
SEEDS: List[int] = [13, 42, 123, 2024, 7]

# Pinned model identifiers — change invalidates reported numbers.
MODEL_BI_ENCODER: str = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_CROSS_ENCODER: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MODEL_DISTILBERT: str = "distilbert-base-uncased"

# Eval-time LLM temperature is clamped to zero for determinism.
EVAL_LLM_TEMPERATURE: float = 0.0


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RESEARCH_ROOT: Path = Path(__file__).resolve().parent
DATASETS_DIR: Path = RESEARCH_ROOT / "datasets"
RESULTS_DIR: Path = RESEARCH_ROOT / "results"
TABLES_DIR: Path = RESULTS_DIR / "tables"
FIGURES_DIR: Path = RESULTS_DIR / "figures"
PAPER_DIR: Path = RESEARCH_ROOT / "paper"


def ensure_dirs() -> None:
    """Create all output directories idempotently."""
    for d in (DATASETS_DIR, RESULTS_DIR, TABLES_DIR, FIGURES_DIR, PAPER_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Experiment registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExperimentSpec:
    key: str
    module: str
    title: str
    n_samples: int
    out_prefix: str


EXPERIMENTS: Dict[str, ExperimentSpec] = {
    "exp1": ExperimentSpec(
        key="exp1",
        module="backend.research.experiments.exp1_llm_reliability",
        title="Multi-provider failover reliability",
        n_samples=10_000,
        out_prefix="exp1",
    ),
    "exp2": ExperimentSpec(
        key="exp2",
        module="backend.research.experiments.exp2_intent_eval",
        title="Rule vs. learned intent classification",
        n_samples=500,
        out_prefix="exp2",
    ),
    "exp3": ExperimentSpec(
        key="exp3",
        module="backend.research.experiments.exp3_ats_eval",
        title="ATS scoring: keyword, BM25, TF-IDF, Jaccard, semantic, cross-encoder",
        n_samples=200,
        out_prefix="exp3",
    ),
    "exp4": ExperimentSpec(
        key="exp4",
        module="backend.research.experiments.exp4_user_simulator",
        title="End-to-end persona journey simulator",
        n_samples=5,
        out_prefix="exp4",
    ),
    "exp5": ExperimentSpec(
        key="exp5",
        module="backend.research.experiments.exp5_ablations",
        title="Component ablations",
        n_samples=0,
        out_prefix="exp5",
    ),
}


# ---------------------------------------------------------------------------
# Intent taxonomy — kept aligned with chat_engine._analyze_intent
# ---------------------------------------------------------------------------

INTENT_LABELS: List[str] = [
    "asking_for_help",
    "requesting_explanation",
    "seeking_motivation",
    "reporting_struggle",
    "asking_next_steps",
    "requesting_resources",
    "asking_progress",
    "general_chat",
]


@dataclass(frozen=True)
class FaultProfile:
    """Parameters for the deterministic httpx fault injector used in Exp.1."""

    p_429: float = 0.12
    p_5xx: float = 0.05
    p_network: float = 0.02
    latency_lognorm_mean: float = -0.6  # exp(-0.6)=0.55s median
    latency_lognorm_sigma: float = 0.6


DEFAULT_FAULT_PROFILE = FaultProfile()
