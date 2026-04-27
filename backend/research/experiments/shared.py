"""Shared utilities for all experiments: metrics, timing, LaTeX export.

Every helper here is intentionally dependency-light — numpy is the only hard
requirement. scipy / sklearn are used when available but every function has a
fallback implementation so the harness runs in a minimal environment.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:  # optional hard-numeric deps
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:
    from scipy.stats import spearmanr, pearsonr  # type: ignore
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

try:
    from sklearn.metrics import f1_score, accuracy_score, confusion_matrix  # type: ignore
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False

from backend.research.config import TABLES_DIR, GLOBAL_SEED, ensure_dirs


# ---------------------------------------------------------------------------
# Seeded RNG
# ---------------------------------------------------------------------------

def seeded_rng(salt: str = "") -> random.Random:
    return random.Random(f"{GLOBAL_SEED}:{salt}")


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

@contextmanager
def timer() -> "TimerHandle":
    h = TimerHandle()
    h._start = time.perf_counter()
    try:
        yield h
    finally:
        h._end = time.perf_counter()


@dataclass
class TimerHandle:
    _start: float = 0.0
    _end: float = 0.0

    @property
    def elapsed_ms(self) -> float:
        return (self._end - self._start) * 1000.0


# ---------------------------------------------------------------------------
# Ranking / correlation helpers (fallback implementations)
# ---------------------------------------------------------------------------

def _rank(xs: Sequence[float]) -> List[float]:
    """Average-rank (deals with ties)."""
    idx = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[idx[j + 1]] == xs[idx[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[idx[k]] = avg
        i = j + 1
    return ranks


def spearman_rho(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    if _HAS_SCIPY:
        r, _ = spearmanr(a, b)
        return float(r) if r == r else 0.0  # guard NaN
    ra, rb = _rank(a), _rank(b)
    return pearson_r(ra, rb)


def pearson_r(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    if _HAS_SCIPY:
        r, _ = pearsonr(a, b)
        return float(r) if r == r else 0.0
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    num = sum((ai - ma) * (bi - mb) for ai, bi in zip(a, b))
    da = math.sqrt(sum((ai - ma) ** 2 for ai in a))
    db = math.sqrt(sum((bi - mb) ** 2 for bi in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def ndcg_at_k(scores: Sequence[float], gold: Sequence[float], k: int = 10) -> float:
    """NDCG@k with raw ``2**gold - 1`` gains — kept for legacy callers / tests.

    Use :func:`ndcg_at_k_normalized` for anything where gold is on a 0-100 or
    other wide scale.
    """
    if not scores or len(scores) != len(gold):
        return 0.0
    order = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
    dcg = 0.0
    for i, idx in enumerate(order):
        dcg += (2 ** gold[idx] - 1) / math.log2(i + 2)
    ideal_order = sorted(range(len(gold)), key=lambda i: -gold[i])[:k]
    idcg = 0.0
    for i, idx in enumerate(ideal_order):
        idcg += (2 ** gold[idx] - 1) / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0


def ndcg_at_k_normalized(
    scores: Sequence[float],
    gold: Sequence[float],
    k: int = 10,
    gold_max: Optional[float] = None,
) -> float:
    """NDCG@k with gold first normalized to [0, 1].

    This avoids the ``2**100 - 1`` overflow and yields numerically meaningful
    gains when gold is on a 0-100 scale (as produced by the synthetic and
    O*NET-derived ATS pairs).
    """
    if not scores or len(scores) != len(gold):
        return 0.0
    gmax = float(gold_max) if gold_max is not None else (max(gold) or 1.0)
    if gmax <= 0:
        return 0.0
    norm = [min(1.0, max(0.0, g / gmax)) for g in gold]

    order = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
    dcg = 0.0
    for i, idx in enumerate(order):
        dcg += (2 ** norm[idx] - 1) / math.log2(i + 2)
    ideal_order = sorted(range(len(norm)), key=lambda i: -norm[i])[:k]
    idcg = 0.0
    for i, idx in enumerate(ideal_order):
        idcg += (2 ** norm[idx] - 1) / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0


def mean_absolute_error(a: Sequence[float], b: Sequence[float]) -> float:
    if not a:
        return 0.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


# ---------------------------------------------------------------------------
# Classification metrics
# ---------------------------------------------------------------------------

def classification_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
) -> Dict[str, float]:
    if _HAS_SKLEARN:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        }
    # Fallback: macro-F1
    labels = sorted(set(list(y_true) + list(y_pred)))
    f1s = []
    for lbl in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lbl and p == lbl)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lbl and p == lbl)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lbl and p != lbl)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) else 0.0)
    acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    return {
        "accuracy": acc,
        "f1_macro": sum(f1s) / len(f1s) if f1s else 0.0,
        "f1_weighted": sum(f1s) / len(f1s) if f1s else 0.0,
    }


# ---------------------------------------------------------------------------
# Reliability
# ---------------------------------------------------------------------------

@dataclass
class ReliabilitySummary:
    n: int
    successes: int
    success_rate: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "n": self.n,
            "successes": self.successes,
            "success_rate": self.success_rate,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "mean_ms": self.mean_ms,
        }


def reliability(results: Sequence[Tuple[bool, float]]) -> ReliabilitySummary:
    """Summarize a list of (success, latency_ms) records."""
    n = len(results)
    if n == 0:
        return ReliabilitySummary(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
    successes = sum(1 for ok, _ in results if ok)
    latencies = [lat for ok, lat in results if ok] or [0.0]
    latencies.sort()

    def _q(q: float) -> float:
        if not latencies:
            return 0.0
        idx = max(0, min(len(latencies) - 1, int(q * len(latencies))))
        return latencies[idx]

    return ReliabilitySummary(
        n=n,
        successes=successes,
        success_rate=successes / n,
        p50_ms=_q(0.50),
        p95_ms=_q(0.95),
        p99_ms=_q(0.99),
        mean_ms=statistics.fmean(latencies),
    )


# ---------------------------------------------------------------------------
# LaTeX helpers
# ---------------------------------------------------------------------------

def to_latex_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[object]],
    caption: str,
    label: str,
) -> str:
    """Emit a minimal IEEE-style tabular; no package dependencies needed."""
    col_spec = "l" + "r" * (len(headers) - 1)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        fr"\caption{{{caption}}}",
        fr"\label{{{label}}}",
        fr"\begin{{tabular}}{{{col_spec}}}",
        r"\hline",
        " & ".join(str(h) for h in headers) + r" \\",
        r"\hline",
    ]
    # Escape the header row too.
    lines[-2] = " & ".join(_fmt_cell_latex(h) for h in headers) + r" \\"
    for r in rows:
        lines.append(" & ".join(_fmt_cell_latex(c) for c in r) + r" \\")
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def _fmt_cell(c: object) -> str:
    if isinstance(c, float):
        return f"{c:.3f}"
    return str(c)


def _fmt_cell_latex(c: object) -> str:
    """Like _fmt_cell but escapes LaTeX-sensitive characters in strings."""
    if isinstance(c, float):
        return f"{c:.3f}"
    s = str(c)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                 ("}", r"\}"), ("~", r"\textasciitilde{}"),
                 ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def write_table(
    name: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[object]],
    caption: str,
    label: str,
) -> Tuple[Path, Path]:
    """Write a CSV + LaTeX fragment side-by-side in TABLES_DIR."""
    ensure_dirs()
    csv_path = TABLES_DIR / f"{name}.csv"
    tex_path = TABLES_DIR / f"{name}.tex"

    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(str(h) for h in headers) + "\n")
        for r in rows:
            f.write(",".join(_fmt_cell(c).replace(",", ";") for c in r) + "\n")

    tex_path.write_text(
        to_latex_table(headers, rows, caption, label),
        encoding="utf-8",
    )
    return csv_path, tex_path


def append_manifest(record: dict) -> None:
    ensure_dirs()
    manifest = TABLES_DIR.parent / "run_manifest.json"
    existing: List[dict] = []
    if manifest.exists():
        try:
            existing = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    existing.append(record)
    manifest.write_text(json.dumps(existing, indent=2), encoding="utf-8")


__all__ = [
    "seeded_rng", "timer", "TimerHandle",
    "spearman_rho", "pearson_r", "ndcg_at_k", "ndcg_at_k_normalized",
    "mean_absolute_error",
    "classification_metrics", "reliability", "ReliabilitySummary",
    "to_latex_table", "write_table", "append_manifest",
    "run_multi_seed", "aggregate_runs",
]


# ---------------------------------------------------------------------------
# Multi-seed aggregator
# ---------------------------------------------------------------------------

def run_multi_seed(
    fn: Callable[[int], Dict[str, float]],
    seeds: Sequence[int],
) -> Dict[str, Tuple[float, float, float, float]]:
    """Run ``fn(seed)`` for each seed and aggregate per-metric stats.

    Returns ``{metric: (mean, std, ci95_low, ci95_high)}``. The CI is computed
    as mean ± 1.96 * std/sqrt(n); for n=5 this is a rough normal approximation
    but suffices for the paper's reported variance.
    """
    runs: List[Dict[str, float]] = [fn(s) for s in seeds]
    return aggregate_runs(runs)


def aggregate_runs(
    runs: Sequence[Dict[str, float]],
) -> Dict[str, Tuple[float, float, float, float]]:
    if not runs:
        return {}
    keys = set()
    for r in runs:
        keys.update(r.keys())
    out: Dict[str, Tuple[float, float, float, float]] = {}
    n = len(runs)
    for k in keys:
        vals = [float(r.get(k, 0.0)) for r in runs]
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / max(1, n - 1) if n > 1 else 0.0
        std = math.sqrt(var)
        se = std / math.sqrt(n) if n > 1 else 0.0
        half = 1.96 * se
        out[k] = (mean, std, mean - half, mean + half)
    return out
