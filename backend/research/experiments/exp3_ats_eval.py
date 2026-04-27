"""Experiment 3 — ATS resume/JD scoring.

Compares six scoring strategies against 200 synthetic pairs with gold scores.
Headline metric is Spearman ρ; also reports Pearson r, MAE, NDCG@10
(normalized), and wall time. Statistical significance for each non-baseline
scorer vs. BM25 is reported via Wilcoxon signed-rank on per-pair residuals.

Key differences from the Phase-1 version:

* **BM25 corpus-wide** — uses ``bm25_matcher.score_corpus`` (single-doc BM25
  returned constant zeros in Phase 1).
* **Semantic skill-level** — uses ``semantic_ats.score_batch`` on the
  ``required`` / ``candidate_skills`` lists from each pair, not on free
  text. One batched encoder pass instead of 200.
* **NDCG@10 normalized** — gold mapped to [0, 1] before the exponential
  gain, fixing the Phase-1 overflow.
* **Multi-seed** — the generator re-runs under each seed (``config.SEEDS``)
  producing a fresh set of 200 pairs; metrics are aggregated as mean ± std.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from backend.research.baselines import (
    bm25_matcher,
    jaccard_matcher,
    keyword_matcher,
    tfidf_matcher,
)
from backend.research.config import DATASETS_DIR, SEEDS, ensure_dirs
from backend.research.data_gen import gen_resume_jd, gen_resume_jd_real
from backend.research.experiments.shared import (
    aggregate_runs,
    append_manifest,
    mean_absolute_error,
    ndcg_at_k_normalized,
    pearson_r,
    spearman_rho,
    timer,
    write_table,
)
from backend.research.experiments.stats import wilcoxon_signed_rank
from backend.research.models import cross_encoder_ats, semantic_ats


def _regenerate_for_seed(seed: int) -> List[dict]:
    dataset = os.environ.get("AIMENTOR_DATASET", "synthetic")
    if dataset == "real":
        real_path = DATASETS_DIR / f"resume_jd_real_seed{seed}.jsonl"
        if not real_path.exists():
            gen_resume_jd_real.generate(seed=seed, out_path=real_path)
        with real_path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    path = DATASETS_DIR / f"resume_jd_200_seed{seed}.jsonl"
    if not path.exists():
        gen_resume_jd.generate(seed=seed)
        default = DATASETS_DIR / "resume_jd_200.jsonl"
        if default.exists():
            path.write_text(default.read_text(encoding="utf-8"), encoding="utf-8")
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _doc_pair_score(fn: Callable[[str, str], float], pairs: List[dict]) -> List[float]:
    return [fn(p["resume"], p["jd"]) for p in pairs]


def _score_all(pairs: List[dict]) -> Dict[str, List[float]]:
    resumes = [p["resume"] for p in pairs]
    jds = [p["jd"] for p in pairs]
    cand_sets = [p.get("candidate_skills", []) for p in pairs]
    req_sets = [p.get("required", []) for p in pairs]

    out: Dict[str, List[float]] = {}
    out["Jaccard"] = _doc_pair_score(jaccard_matcher.score, pairs)
    out["TF-IDF"] = _doc_pair_score(tfidf_matcher.score, pairs)
    out["BM25"] = bm25_matcher.score_corpus(resumes, jds)
    out["Keyword (ours base)"] = _doc_pair_score(keyword_matcher.score, pairs)
    out["Semantic (ours)"] = semantic_ats.score_batch(cand_sets, req_sets)
    out["Cross-Encoder (ours)"] = _doc_pair_score(cross_encoder_ats.score, pairs)
    return out


def _metrics_for(preds: Sequence[float], gold: Sequence[float]) -> Dict[str, float]:
    return {
        "rho": spearman_rho(preds, gold),
        "pearson": pearson_r(preds, gold),
        "mae": mean_absolute_error(preds, gold),
        "ndcg10": ndcg_at_k_normalized(preds, gold, k=10, gold_max=100.0),
    }


def _per_pair_abs_err(preds: Sequence[float], gold: Sequence[float]) -> List[float]:
    return [abs(p - g) for p, g in zip(preds, gold)]


def _eval_one_seed(seed: int) -> Dict[str, float]:
    pairs = _regenerate_for_seed(seed)
    gold = [p["gold_score"] for p in pairs]
    preds = _score_all(pairs)

    out: Dict[str, float] = {}
    for name, p in preds.items():
        m = _metrics_for(p, gold)
        for k, v in m.items():
            out[f"{name}::{k}"] = v
    # Wilcoxon: each scorer's absolute errors vs. BM25 baseline.
    bm25_errs = _per_pair_abs_err(preds["BM25"], gold)
    for name, p in preds.items():
        if name == "BM25":
            continue
        w = wilcoxon_signed_rank(_per_pair_abs_err(p, gold), bm25_errs)
        out[f"{name}::wilcoxon_p"] = w["p"]
    return out


def run() -> Path:
    ensure_dirs()

    runs: List[Dict[str, float]] = []
    for s in SEEDS:
        with timer() as t:
            m = _eval_one_seed(seed=s)
        m["wall_ms"] = t.elapsed_ms
        runs.append(m)

    agg = aggregate_runs(runs)

    def _cell(name: str, metric: str) -> str:
        k = f"{name}::{metric}"
        if k not in agg:
            return "—"
        mean, std, _, _ = agg[k]
        return f"{mean:.3f} ± {std:.3f}"

    def _p(name: str) -> str:
        k = f"{name}::wilcoxon_p"
        if k not in agg:
            return "—"
        mean, _, _, _ = agg[k]
        return f"p={mean:.2g}"

    scorers = [
        "Jaccard", "TF-IDF", "BM25",
        "Keyword (ours base)", "Semantic (ours)", "Cross-Encoder (ours)",
    ]
    rows_out = []
    for s in scorers:
        rows_out.append([
            s,
            _cell(s, "rho"),
            _cell(s, "pearson"),
            _cell(s, "mae"),
            _cell(s, "ndcg10"),
            _p(s),
        ])

    headers = ["Scorer", "Spearman rho", "Pearson r", "MAE",
               "NDCG@10 (norm.)", "Wilcoxon vs BM25"]
    csv_p, tex_p = write_table(
        name="exp3_ats",
        headers=headers,
        rows=rows_out,
        caption=(
            f"ATS resume-JD scoring quality on {len(SEEDS)} × 200 synthetic "
            "pairs. Mean ± std across seeds; Wilcoxon signed-rank p-value on "
            "per-pair absolute errors vs. BM25."
        ),
        label="tab:ats",
    )
    append_manifest({
        "experiment": "exp3_ats",
        "seeds": list(SEEDS),
        "aggregates": {k: {"mean": v[0], "std": v[1], "ci_low": v[2], "ci_high": v[3]}
                       for k, v in agg.items()},
        "csv": str(csv_p),
        "tex": str(tex_p),
    })
    return csv_p


if __name__ == "__main__":
    p = run()
    print(f"Exp.3 complete -> {p}")
