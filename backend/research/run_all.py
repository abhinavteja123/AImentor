"""Top-level orchestrator: regenerate datasets, run experiments, emit manifest.

Usage::

    python -m backend.research.run_all --exp all
    python -m backend.research.run_all --exp 1
    python -m backend.research.run_all --exp 2,3

Flags::

    --live       (placeholder) forward to real providers when the experiment
                 supports it; currently only Exp.1 documents this path.
    --real PATH  optional CSV of human-labelled intents/JDs; experiments that
                 understand it will merge with the synthetic set.

Every run refreshes ``results/tables/<exp>.{csv,tex}`` and appends a record to
``results/run_manifest.json`` so reviewers can see exactly what was produced.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from importlib import import_module
from pathlib import Path
from typing import List

from backend.research.config import (
    EXPERIMENTS,
    GLOBAL_SEED,
    RESULTS_DIR,
    TABLES_DIR,
    ensure_dirs,
)
from backend.research.data_gen import (
    gen_intents,
    gen_prompts,
    gen_resume_jd,
    gen_resume_jd_real,
)
from backend.research.experiments.shared import append_manifest


# ---------------------------------------------------------------------------
# Dataset regeneration
# ---------------------------------------------------------------------------

def _regenerate_datasets(dataset: str = "synthetic") -> None:
    ensure_dirs()
    gen_prompts.generate()
    gen_intents.generate()
    gen_resume_jd.generate()
    if dataset in ("real", "both"):
        try:
            gen_resume_jd_real.generate()
        except Exception as e:  # pragma: no cover
            print(f"[warn] real resume/JD generation failed: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Environment fingerprint
# ---------------------------------------------------------------------------

def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).resolve().parents[2],
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def _env_fingerprint() -> dict:
    try:
        import importlib.metadata as im
        pkgs = {}
        for name in ("numpy", "scipy", "scikit-learn", "sentence-transformers",
                     "rank-bm25", "transformers", "torch", "pandas"):
            try:
                pkgs[name] = im.version(name)
            except Exception:
                pkgs[name] = "absent"
    except Exception:
        pkgs = {}
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_sha": _git_sha(),
        "seed": GLOBAL_SEED,
        "packages": pkgs,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# ---------------------------------------------------------------------------
# Experiment dispatch
# ---------------------------------------------------------------------------

def _resolve_exps(arg: str) -> List[str]:
    if arg == "all":
        return list(EXPERIMENTS.keys())
    out: List[str] = []
    for part in arg.split(","):
        part = part.strip().lower()
        if not part:
            continue
        key = part if part.startswith("exp") else f"exp{part}"
        if key in EXPERIMENTS:
            out.append(key)
        else:
            print(f"[warn] unknown experiment: {part}", file=sys.stderr)
    return out


def _run_one(key: str) -> Path:
    spec = EXPERIMENTS[key]
    print(f"[run] {key}: {spec.title}")
    mod = import_module(spec.module)
    path = mod.run()
    print(f"[ok]  {key} -> {path}")
    return path


# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------

def _print_summary() -> None:
    manifest = RESULTS_DIR / "run_manifest.json"
    if not manifest.exists():
        return
    records = json.loads(manifest.read_text(encoding="utf-8"))
    print("\n# Run summary\n")
    for rec in records:
        if "experiment" in rec:
            print(f"- **{rec['experiment']}** -> `{rec.get('csv', '?')}`")
    print("\nTables dir:", TABLES_DIR)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AImentor research harness")
    parser.add_argument("--exp", default="all",
                        help="'all' or comma-separated (e.g. 1,2,3 or exp1,exp3)")
    parser.add_argument("--live", action="store_true",
                        help="Forward supported experiments to real providers/LLMs.")
    parser.add_argument("--real", type=Path, default=None,
                        help="Optional CSV of human-labelled data to merge in.")
    parser.add_argument("--dataset", choices=["synthetic", "real", "both"],
                        default="synthetic",
                        help="Data source for exp2/exp3. 'real' swaps in the "
                             "Kaggle + O*NET corpora; 'both' emits two sections.")
    parser.add_argument("--skip-datagen", action="store_true",
                        help="Skip dataset regeneration if the files already exist.")
    parser.add_argument("--gpu", action="store_true",
                        help="Hint downstream models to prefer CUDA when available.")
    args = parser.parse_args(argv)

    ensure_dirs()

    # Propagate runtime flags to experiment modules via env vars (avoids
    # threading kwargs through every runner signature).
    os.environ["AIMENTOR_DATASET"] = args.dataset
    if args.gpu:
        os.environ["AIMENTOR_PREFER_GPU"] = "1"

    if not args.skip_datagen:
        _regenerate_datasets(dataset=args.dataset)

    append_manifest({"env": _env_fingerprint(), "args": vars(args) | {"real": str(args.real)}})

    for key in _resolve_exps(args.exp):
        try:
            _run_one(key)
        except Exception as e:  # pragma: no cover — surfaced to user
            print(f"[err] {key}: {e}", file=sys.stderr)
            append_manifest({"experiment": key, "error": str(e)})

    _print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
