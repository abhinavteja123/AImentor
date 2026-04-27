"""
Multi-KC Bayesian Knowledge Tracing — Paper Section 5.2.

Maintains 5 independent BKT models (one per Knowledge Component)
matching the AIFund-5 dataset units. Provides the mastery vector
[P(L₁), P(L₂), ..., P(L₅)] used as PPO state input.

Parameters calibrated from literature defaults (Table 2 in paper).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Paper Table: BKT parameters per Knowledge Component (Section 5.2.2) ──
#
# Authoritative parameter source is now ``kc_mapping.COURSE_REGISTRY``.
# ``BKT_PARAMS`` below is a backwards-compat shim populated from the
# AI Fundamentals slice — used by the offline simulator (TutoringEnv) and
# any legacy callers. Multi-course logic in ``BKTService`` resolves params
# directly via ``get_bkt_params(course_key, kc_id)``.

from .kc_mapping import COURSE_REGISTRY  # noqa: E402  (avoid circular at top)

_AI_COURSE = COURSE_REGISTRY["ai_fundamentals"]
BKT_PARAMS = {
    kc_id: {
        "name": spec.name,
        "p_l0": spec.p_l0,
        "p_t": spec.p_t,
        "p_g": spec.p_g,
        "p_s": spec.p_s,
    }
    for kc_id, spec in _AI_COURSE.kcs.items()
}

MASTERY_THRESHOLD = 0.95  # Paper Section 5.2.3


# ── Single-skill BKT Model (Corbett & Anderson, 1994) ────────

@dataclass
class BKTModel:
    """
    4-parameter Hidden Markov Model for one knowledge component.
    Implements exact Bayesian update equations from paper Section 5.2.1.
    """
    name: str
    p_l0: float         # P(L₀) — prior mastery
    p_t: float          # P(T)  — learn rate
    p_g: float          # P(G)  — guess rate
    p_s: float          # P(S)  — slip rate
    p_l: float = 0.0    # P(L_t) — current mastery (set in __post_init__)
    history: List[float] = field(default_factory=list)

    def __post_init__(self):
        self.p_l = self.p_l0
        self.history = [self.p_l0]

    def update(self, correct: bool) -> float:
        """
        Bayes update + learning transition.

        P(L_t | correct) = P(L)·(1-S) / [P(L)·(1-S) + (1-P(L))·G]
        P(L_t | wrong)   = P(L)·S     / [P(L)·S     + (1-P(L))·(1-G)]
        P(L_{t+1})       = P(L_t|obs) + (1 - P(L_t|obs)) · P(T)
        """
        if correct:
            numerator = self.p_l * (1 - self.p_s)
            denominator = self.p_l * (1 - self.p_s) + (1 - self.p_l) * self.p_g
        else:
            numerator = self.p_l * self.p_s
            denominator = self.p_l * self.p_s + (1 - self.p_l) * (1 - self.p_g)

        p_l_given_obs = numerator / max(denominator, 1e-9)

        # Learning transition
        self.p_l = p_l_given_obs + (1 - p_l_given_obs) * self.p_t
        self.history.append(self.p_l)
        return self.p_l

    def predict_correct(self) -> float:
        """P(correct on next question) — equation from paper."""
        return self.p_l * (1 - self.p_s) + (1 - self.p_l) * self.p_g

    def is_mastered(self) -> bool:
        return self.p_l >= MASTERY_THRESHOLD

    def reset(self):
        self.p_l = self.p_l0
        self.history = [self.p_l0]


# ── Multi-KC Tracker (Paper Section 5.2) ─────────────────────

class BKTTracker:
    """
    Tracks BKT mastery across 5 knowledge components for one student.
    Provides the mastery vector used as PPO state input.
    """

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.models: Dict[int, BKTModel] = {}

        for kc_id, params in BKT_PARAMS.items():
            self.models[kc_id] = BKTModel(
                name=params["name"],
                p_l0=params["p_l0"],
                p_t=params["p_t"],
                p_g=params["p_g"],
                p_s=params["p_s"],
            )

    def update(self, kc: int, correct: bool) -> float:
        """Update mastery for a single KC. Returns new P(L)."""
        if kc not in self.models:
            logger.warning("Unknown KC %d, ignoring", kc)
            return 0.0
        new_mastery = self.models[kc].update(correct)
        logger.debug("BKT update: student=%s kc=%d correct=%s → P(L)=%.4f",
                      self.student_id, kc, correct, new_mastery)
        return new_mastery

    def get_mastery_vector(self) -> List[float]:
        """Returns [P(L₁), P(L₂), P(L₃), P(L₄), P(L₅)] for PPO state."""
        return [self.models[kc].p_l for kc in sorted(self.models.keys())]

    def get_mastery_dict(self) -> Dict[str, float]:
        """Returns {name: mastery} for dashboard display."""
        return {m.name: round(m.p_l, 4) for m in self.models.values()}

    def get_weakest_kc(self) -> int:
        """Returns KC with lowest mastery — focus next session here."""
        return min(self.models, key=lambda k: self.models[k].p_l)

    def get_strongest_kc(self) -> int:
        return max(self.models, key=lambda k: self.models[k].p_l)

    def all_mastered(self) -> bool:
        return all(m.is_mastered() for m in self.models.values())

    def get_history(self) -> Dict[int, List[float]]:
        """Returns mastery history per KC for plotting."""
        return {kc: m.history for kc, m in self.models.items()}

    def predict_next_correct(self, kc: int) -> float:
        if kc in self.models:
            return self.models[kc].predict_correct()
        return 0.5

    def format_mastery_summary(self) -> str:
        """Human-readable summary for LLM prompts."""
        return ", ".join(
            f"{m.name}:{m.p_l:.0%}" for m in self.models.values()
        )
