"""
PPO trainer CLI — Paper Section 5.3.

Trains the difficulty-control PPO policy on a BKT-driven tutoring simulator
(``backend/app/services/ai/adaptive/ppo_agent.TutoringEnv``) and saves the
resulting checkpoint to ``backend/models/ppo_agent/final_model.zip``. The
backend lazy-loads that path at startup via ``get_ppo_agent``.

Usage
-----
Smoke run (~5 min on CPU; useful for sanity checking install + env):
    python -m backend.research.training.train_ppo_tutor --smoke

Full paper-spec run (500K timesteps, ~30–45 min on CPU):
    python -m backend.research.training.train_ppo_tutor

Custom output directory or step count:
    python -m backend.research.training.train_ppo_tutor \
        --timesteps 250000 \
        --output backend/models/ppo_agent

Requirements
------------
``stable-baselines3`` and ``gymnasium`` (declared in
``backend/app/requirements-research.txt``). The runtime backend remains
functional without these packages — it falls back to MAB.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Configure logging early so the trainer's stdout is informative.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("train_ppo_tutor")


def _default_output_dir() -> Path:
    """``<repo>/backend/models/ppo_agent``."""
    here = Path(__file__).resolve()
    repo_root = here.parents[3]  # …/AImentor
    return repo_root / "backend" / "models" / "ppo_agent"


def main() -> int:
    parser = argparse.ArgumentParser(description="Train PPO difficulty controller.")
    parser.add_argument("--timesteps", type=int, default=500_000,
                        help="Total environment timesteps (paper default: 500_000).")
    parser.add_argument("--smoke", action="store_true",
                        help="Quick sanity-check run (50K timesteps).")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: backend/models/ppo_agent).")
    args = parser.parse_args()

    timesteps = 50_000 if args.smoke else int(args.timesteps)
    output_dir = Path(args.output) if args.output else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Import lazily so the CLI can fail fast with a useful error if SB3
    # is not installed.
    try:
        from backend.app.services.ai.adaptive.ppo_agent import (
            PPODifficultyAgent, _HAS_SB3, _HAS_GYM,
        )
    except ImportError as e:
        logger.error("Failed to import PPO agent module: %s", e)
        return 2

    if not (_HAS_SB3 and _HAS_GYM):
        logger.error(
            "stable-baselines3 and gymnasium are required for training. "
            "Install with: pip install -r backend/app/requirements-research.txt"
        )
        return 2

    logger.info("Output directory: %s", output_dir)
    logger.info("Total timesteps:  %s%s",
                f"{timesteps:,}", " (SMOKE)" if args.smoke else "")

    agent = PPODifficultyAgent.train(
        qa_bank_path=None,
        output_path=str(output_dir),
        total_timesteps=timesteps,
    )
    if agent is None:
        logger.error("Training failed (see SB3 logs above).")
        return 1

    final_path = output_dir / "final_model.zip"
    if not final_path.exists():
        # SB3's `model.save("…/final_model")` adds .zip automatically.
        alt = output_dir / "final_model"
        if alt.exists():
            final_path = alt
    logger.info("✅ PPO checkpoint written: %s", final_path)
    logger.info(
        "Backend will auto-load this checkpoint on next start "
        "(set $PPO_MODEL_PATH to override)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
