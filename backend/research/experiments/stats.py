"""Statistical significance helpers for paired-system comparisons.

Every function here is numpy-only with a scipy fast path. Used by Exp.2
(McNemar on intent), Exp.3 (paired bootstrap + Wilcoxon on ranking quality),
and Exp.5 (bootstrap CIs on ablation deltas).
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Sequence, Tuple

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:
    from scipy.stats import wilcoxon as _sp_wilcoxon  # type: ignore
    _HAS_WILCOXON = True
except Exception:
    _HAS_WILCOXON = False

try:
    from statsmodels.stats.contingency_tables import mcnemar as _sm_mcnemar  # type: ignore
    _HAS_SM_MCNEMAR = True
except Exception:
    _HAS_SM_MCNEMAR = False


# ---------------------------------------------------------------------------
# McNemar's test (paired classification systems)
# ---------------------------------------------------------------------------

def mcnemar(
    y_true: Sequence[str],
    y_pred_a: Sequence[str],
    y_pred_b: Sequence[str],
) -> Dict[str, float]:
    """Exact-binomial McNemar's test on the disagreement table of A vs B.

    Returns ``{"b": count_a_right_b_wrong, "c": count_a_wrong_b_right,
               "stat": X², "p": p-value}``.
    """
    if len(y_true) != len(y_pred_a) or len(y_true) != len(y_pred_b):
        return {"b": 0.0, "c": 0.0, "stat": 0.0, "p": 1.0}

    b = sum(1 for t, a, bb in zip(y_true, y_pred_a, y_pred_b) if a == t and bb != t)
    c = sum(1 for t, a, bb in zip(y_true, y_pred_a, y_pred_b) if a != t and bb == t)

    if _HAS_SM_MCNEMAR:
        res = _sm_mcnemar([[0, b], [c, 0]], exact=True)
        return {"b": float(b), "c": float(c),
                "stat": float(res.statistic) if res.statistic is not None else 0.0,
                "p": float(res.pvalue)}

    # Fallback: continuity-corrected chi² approximation.
    n = b + c
    if n == 0:
        return {"b": 0.0, "c": 0.0, "stat": 0.0, "p": 1.0}
    stat = (abs(b - c) - 1) ** 2 / n if n > 0 else 0.0
    # Convert χ²(df=1) to p via survival-of-normal approximation.
    p = math.erfc(math.sqrt(stat / 2))
    return {"b": float(b), "c": float(c), "stat": float(stat), "p": float(p)}


# ---------------------------------------------------------------------------
# Paired bootstrap on any scalar metric
# ---------------------------------------------------------------------------

def paired_bootstrap(
    metric_fn: Callable[[Sequence[float], Sequence[float]], float],
    preds_a: Sequence[float],
    preds_b: Sequence[float],
    gold: Sequence[float],
    n_resamples: int = 10000,
    seed: int = 1234,
) -> Dict[str, float]:
    """Paired bootstrap for Δ = metric(A, gold) − metric(B, gold).

    Returns ``{"delta": point estimate, "ci_low", "ci_high", "p"}`` where
    ``p`` is a two-sided approximation: 2 × min(P(Δ≤0), P(Δ≥0)).
    """
    n = len(gold)
    assert len(preds_a) == n and len(preds_b) == n, "all lengths must match"
    rng = random.Random(seed)

    point = metric_fn(preds_a, gold) - metric_fn(preds_b, gold)
    if n == 0:
        return {"delta": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p": 1.0}

    deltas: List[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        ra = [preds_a[i] for i in idx]
        rb = [preds_b[i] for i in idx]
        rg = [gold[i] for i in idx]
        try:
            d = metric_fn(ra, rg) - metric_fn(rb, rg)
        except Exception:
            d = 0.0
        deltas.append(d)

    deltas.sort()
    ci_low = deltas[int(0.025 * n_resamples)]
    ci_high = deltas[int(0.975 * n_resamples) - 1]
    n_le0 = sum(1 for d in deltas if d <= 0)
    p = 2.0 * min(n_le0, n_resamples - n_le0) / n_resamples
    return {"delta": point, "ci_low": ci_low, "ci_high": ci_high, "p": p}


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank (paired 1:1 samples)
# ---------------------------------------------------------------------------

def wilcoxon_signed_rank(
    xs: Sequence[float],
    ys: Sequence[float],
) -> Dict[str, float]:
    """Two-sided Wilcoxon signed-rank on ``xs − ys``."""
    if len(xs) != len(ys) or not xs:
        return {"stat": 0.0, "p": 1.0}
    if _HAS_WILCOXON:
        try:
            res = _sp_wilcoxon(xs, ys, zero_method="wilcox", alternative="two-sided")
            return {"stat": float(res.statistic), "p": float(res.pvalue)}
        except Exception:
            pass

    # Manual fallback.
    diffs = [float(a) - float(b) for a, b in zip(xs, ys) if a != b]
    if not diffs:
        return {"stat": 0.0, "p": 1.0}
    abs_diffs = sorted(diffs, key=abs)
    ranks = list(range(1, len(abs_diffs) + 1))
    w_pos = sum(r for r, d in zip(ranks, abs_diffs) if d > 0)
    w_neg = sum(r for r, d in zip(ranks, abs_diffs) if d < 0)
    stat = min(w_pos, w_neg)
    n = len(abs_diffs)
    mean = n * (n + 1) / 4.0
    var = n * (n + 1) * (2 * n + 1) / 24.0
    if var <= 0:
        return {"stat": float(stat), "p": 1.0}
    z = (stat - mean) / math.sqrt(var)
    p = 2.0 * (0.5 * math.erfc(abs(z) / math.sqrt(2)))
    return {"stat": float(stat), "p": float(p)}


# ---------------------------------------------------------------------------
# Multi-comparison correction
# ---------------------------------------------------------------------------

def bonferroni(ps: Sequence[float]) -> List[float]:
    k = max(1, len(ps))
    return [min(1.0, p * k) for p in ps]


__all__ = ["mcnemar", "paired_bootstrap", "wilcoxon_signed_rank", "bonferroni"]
