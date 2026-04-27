"""Experiment 1 — Multi-provider LLM fallback reliability.

Runs the 10 000-prompt suite through every scenario (three single-provider
configurations + the proposed three-provider chain) and reports success rate,
latency percentiles, and fallback-depth distribution.

All calls are offline simulations (see :mod:`fault_scheduler`) so reviewers can
reproduce Table I without live API keys. Pass ``--live`` (wired from the top-
level runner) to attach the experiment to the real `llm_provider.build_default_chain`
instead; skipped by default.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import List, Tuple

from backend.research.config import DATASETS_DIR, ensure_dirs
from backend.research.data_gen import gen_prompts
from backend.research.experiments.fault_scheduler import build_scenarios
from backend.research.experiments.shared import (
    append_manifest,
    reliability,
    write_table,
)


def _load_prompts() -> List[dict]:
    path = DATASETS_DIR / "prompts_10k.jsonl"
    if not path.exists():
        gen_prompts.generate()
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run() -> Path:
    ensure_dirs()
    prompts = _load_prompts()
    scenarios = build_scenarios()

    rows = []
    depth_snapshots = {}
    for label, chain in scenarios.items():
        results: List[Tuple[bool, float]] = []
        depths: List[int] = []
        for p in prompts:
            ok, latency, depth = chain.run(request_id=p["id"])
            results.append((ok, latency))
            depths.append(depth)
        summary = reliability(results)
        hist = Counter(depths)
        depth_snapshots[label] = dict(hist)
        rows.append([
            label,
            summary.success_rate,
            summary.p50_ms,
            summary.p95_ms,
            summary.p99_ms,
            summary.mean_ms,
        ])

    headers = ["Scenario", "Success rate", "p50 (ms)", "p95 (ms)", "p99 (ms)", "Mean (ms)"]
    csv_p, tex_p = write_table(
        name="exp1_reliability",
        headers=headers,
        rows=rows,
        caption="End-to-end LLM-call reliability under injected faults (n=10\\,000).",
        label="tab:reliability",
    )

    # Side artifact: fallback-depth histogram JSON.
    hist_path = Path(csv_p).parent / "exp1_depth_histogram.json"
    hist_path.write_text(json.dumps(depth_snapshots, indent=2), encoding="utf-8")

    append_manifest({
        "experiment": "exp1_reliability",
        "n": len(prompts),
        "csv": str(csv_p),
        "tex": str(tex_p),
        "histogram": str(hist_path),
    })
    return csv_p


if __name__ == "__main__":
    p = run()
    print(f"Exp.1 complete -> {p}")
