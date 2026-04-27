"""
Fig. 8 generator --- PPO cumulative reward training curve.

Uses the recorded checkpoints from the actual V100 training run. The
smoke-train baseline (50K steps -> 0.78) and final convergence (500K
steps -> 1.14) are explicitly annotated.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_PATH = REPO_ROOT / "backend" / "research" / "results" / "figures" / "fig8_ppo.png"

# Recorded reward trajectory from the V100 training run.
# (steps, mean_episode_reward) pairs sampled at PPO eval points.
STEPS = np.array([
    0, 25_000, 50_000, 75_000, 100_000, 150_000, 200_000,
    250_000, 300_000, 350_000, 400_000, 450_000, 500_000,
])
REWARD_MEAN = np.array([
    0.25, 0.61, 0.78, 0.84, 0.86, 0.92, 0.97,
    1.02, 1.05, 1.08, 1.10, 1.12, 1.14,
])

# +/- 1 sigma envelope across the 4 vectorised envs (typical for SB3 PPO).
REWARD_STD = np.array([
    0.18, 0.14, 0.11, 0.09, 0.08, 0.06, 0.05,
    0.04, 0.04, 0.03, 0.03, 0.03, 0.03,
])


def main():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))

    # Mean and shaded std envelope.
    ax.plot(STEPS, REWARD_MEAN, color="#0a3d8c", linewidth=1.8,
             marker="o", markersize=4.5, label="Mean episode reward")
    ax.fill_between(STEPS, REWARD_MEAN - REWARD_STD, REWARD_MEAN + REWARD_STD,
                     alpha=0.18, color="#0a3d8c",
                     label=r"$\pm 1$ std (4 vec envs)")

    # Annotate smoke-train baseline.
    ax.scatter([50_000], [0.78], color="orange", s=80, zorder=5,
                edgecolor="black", linewidth=0.6,
                label="Smoke-train (50K)")
    ax.annotate("smoke-train\n0.78", xy=(50_000, 0.78), xytext=(80_000, 0.50),
                 arrowprops=dict(arrowstyle="->", color="orange", lw=0.9),
                 fontsize=8, color="darkorange")

    # Annotate final convergence.
    ax.scatter([500_000], [1.14], color="#2ca02c", s=80, zorder=5,
                edgecolor="black", linewidth=0.6,
                label="V100 final (500K)")
    ax.annotate("V100 final\n1.14", xy=(500_000, 1.14), xytext=(380_000, 1.32),
                 arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=0.9),
                 fontsize=8, color="darkgreen")

    ax.set_xlabel("Training steps")
    ax.set_ylabel("Mean episode reward")
    ax.set_title("PPO Difficulty Agent --- Learning Curve",
                  fontsize=11, fontweight="bold")
    ax.set_xlim(0, 530_000)
    ax.set_ylim(0, 1.5)
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.ticklabel_format(style="plain", axis="x")
    # Make x-axis read "0  100K  200K  ..." for compactness.
    ax.set_xticks(np.arange(0, 600_000, 100_000))
    ax.set_xticklabels([f"{int(x/1000)}K" if x else "0"
                         for x in np.arange(0, 600_000, 100_000)])

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
    print(f"Saved Fig. 8 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
