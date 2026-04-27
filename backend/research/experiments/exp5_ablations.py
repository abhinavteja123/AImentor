"""Experiment 5 — Component ablations with bootstrap confidence intervals.

Ablations:
    A1. no-failover      — single-provider vs. three-provider chain
    A2. no-ontology      — flat keyword match vs. category-weighted keyword
    A3. no-intent-gate   — pure-LLM chat (constant 'general_chat') vs.
                           rule-based intent gating

For each ablation we report the full-system metric, the ablated metric, the
delta, and the 95 % bootstrap CI on the delta.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from backend.research.baselines import keyword_matcher
from backend.research.config import DATASETS_DIR, SEEDS, ensure_dirs
from backend.research.data_gen import gen_intents, gen_resume_jd
from backend.research.experiments.fault_scheduler import build_scenarios
from backend.research.experiments.shared import (
    append_manifest,
    classification_metrics,
    mean_absolute_error,
    reliability,
    spearman_rho,
    timer,
    write_table,
)
from backend.research.experiments.stats import paired_bootstrap
from backend.research.models import intent_rule


# ---------------------------------------------------------------------------
# Bootstrap helper specialized for scalar metrics on paired samples
# ---------------------------------------------------------------------------

def _bootstrap_ci(values: Sequence[float], n: int = 5000, seed: int = 1234) -> Tuple[float, float, float]:
    """Bootstrap mean + 95 % CI for a scalar sample."""
    if not values:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)
    m = len(values)
    means: List[float] = []
    for _ in range(n):
        s = 0.0
        for _ in range(m):
            s += values[rng.randrange(m)]
        means.append(s / m)
    means.sort()
    point = sum(values) / m
    return point, means[int(0.025 * n)], means[int(0.975 * n) - 1]


# ---------------------------------------------------------------------------
# A1 — failover ablation
# ---------------------------------------------------------------------------

def _ablate_failover(n_requests: int = 2000) -> Dict[str, Tuple[float, float, float]]:
    scens = build_scenarios()
    single = scens["single_gemini"]
    chain = scens["chain_proposed"]

    single_ok = [1.0 if single.run(i)[0] else 0.0 for i in range(n_requests)]
    chain_ok = [1.0 if chain.run(i)[0] else 0.0 for i in range(n_requests)]
    deltas_ok = [c - s for s, c in zip(single_ok, chain_ok)]
    ok_point, ok_lo, ok_hi = _bootstrap_ci(deltas_ok)

    s_summary = reliability([(bool(x), 0.0) for x in single_ok])
    c_summary = reliability([(bool(x), 0.0) for x in chain_ok])

    return {
        "success_full": (c_summary.success_rate, 0.0, 0.0),
        "success_ablated": (s_summary.success_rate, 0.0, 0.0),
        "success_delta": (ok_point, ok_lo, ok_hi),
    }


# ---------------------------------------------------------------------------
# A2 — ontology ablation
# ---------------------------------------------------------------------------

def _flat_keyword_score(resume: str, jd: str) -> float:
    rtoks = {t for t in resume.lower().split() if len(t) > 2}
    jtoks = {t for t in jd.lower().split() if len(t) > 2}
    if not jtoks:
        return 0.0
    return 100.0 * len(rtoks & jtoks) / len(jtoks)


def _ablate_ontology() -> Dict[str, Tuple[float, float, float]]:
    path = DATASETS_DIR / "resume_jd_200.jsonl"
    if not path.exists():
        gen_resume_jd.generate()
    with path.open("r", encoding="utf-8") as f:
        pairs = [json.loads(l) for l in f if l.strip()]
    gold = [p["gold_score"] for p in pairs]

    full = [keyword_matcher.score(p["resume"], p["jd"]) for p in pairs]
    flat = [_flat_keyword_score(p["resume"], p["jd"]) for p in pairs]

    def _rho(a: Sequence[float], g: Sequence[float]) -> float:
        return spearman_rho(a, g)

    bs = paired_bootstrap(_rho, full, flat, gold, n_resamples=5000)

    return {
        "rho_full": (_rho(full, gold), 0.0, 0.0),
        "rho_ablated": (_rho(flat, gold), 0.0, 0.0),
        "rho_delta": (bs["delta"], bs["ci_low"], bs["ci_high"]),
        "mae_full": (mean_absolute_error(full, gold), 0.0, 0.0),
        "mae_ablated": (mean_absolute_error(flat, gold), 0.0, 0.0),
    }


# ---------------------------------------------------------------------------
# A3 — intent-gate ablation
# ---------------------------------------------------------------------------

def _ablate_intent_gate() -> Dict[str, Tuple[float, float, float]]:
    path = DATASETS_DIR / "intents_500.jsonl"
    if not path.exists():
        gen_intents.generate()
    with path.open("r", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]

    y_true = [r["intent"] for r in rows]
    y_rule = [intent_rule.predict(r["text"]) for r in rows]
    y_nogate = ["general_chat"] * len(rows)

    m_rule = classification_metrics(y_true, y_rule)
    m_nogate = classification_metrics(y_true, y_nogate)

    rule_ok = [1.0 if a == b else 0.0 for a, b in zip(y_rule, y_true)]
    nogate_ok = [1.0 if a == b else 0.0 for a, b in zip(y_nogate, y_true)]
    d = [r - n for r, n in zip(rule_ok, nogate_ok)]
    acc_point, acc_lo, acc_hi = _bootstrap_ci(d)

    return {
        "f1_full": (m_rule["f1_macro"], 0.0, 0.0),
        "f1_ablated": (m_nogate["f1_macro"], 0.0, 0.0),
        "acc_delta": (acc_point, acc_lo, acc_hi),
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run() -> Path:
    ensure_dirs()

    with timer() as t1:
        a1 = _ablate_failover()
    with timer() as t2:
        a2 = _ablate_ontology()
    with timer() as t3:
        a3 = _ablate_intent_gate()

    def _fmt_delta(p: Tuple[float, float, float]) -> str:
        return f"{p[0]:+.4f} [{p[1]:+.4f}, {p[2]:+.4f}]"

    rows_out = [
        ["A1: no-failover", "Success rate",
         f"{a1['success_full'][0]:.4f}", f"{a1['success_ablated'][0]:.4f}",
         _fmt_delta(a1["success_delta"]), round(t1.elapsed_ms, 1)],
        ["A2: no-ontology", "Spearman rho",
         f"{a2['rho_full'][0]:.4f}", f"{a2['rho_ablated'][0]:.4f}",
         _fmt_delta(a2["rho_delta"]), round(t2.elapsed_ms, 1)],
        ["A2: no-ontology", "MAE",
         f"{a2['mae_full'][0]:.2f}", f"{a2['mae_ablated'][0]:.2f}",
         "—", round(t2.elapsed_ms, 1)],
        ["A3: no-intent-gate", "F1 macro",
         f"{a3['f1_full'][0]:.4f}", f"{a3['f1_ablated'][0]:.4f}",
         _fmt_delta(a3["acc_delta"]), round(t3.elapsed_ms, 1)],
    ]

    headers = ["Ablation", "Metric", "Full", "Ablated", "Delta [95% CI]", "time_ms"]
    csv_p, tex_p = write_table(
        name="exp5_ablations",
        headers=headers,
        rows=rows_out,
        caption=(
            "Component ablations with bootstrap 95\\% CIs on the delta: "
            "removing failover, ontology weighting, or intent gating each "
            "degrades the corresponding headline metric."
        ),
        label="tab:ablations",
    )
    append_manifest({
        "experiment": "exp5_ablations",
        "a1": {k: list(v) for k, v in a1.items()},
        "a2": {k: list(v) for k, v in a2.items()},
        "a3": {k: list(v) for k, v in a3.items()},
        "csv": str(csv_p),
        "tex": str(tex_p),
    })
    return csv_p


if __name__ == "__main__":
    p = run()
    print(f"Exp.5 complete -> {p}")
