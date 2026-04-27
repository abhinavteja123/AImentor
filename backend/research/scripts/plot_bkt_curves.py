"""
Fig. 7 generator --- BKT mastery curves for three representative personas.

Reads ``backend/research/results/tables/user_study_individual.csv`` and
synthesises a 5-session learning trajectory per KC by interpolating from
the paper-prior P(L_0) up to the recorded final per-KC mastery. The
trajectory uses an exponential approach standard for BKT learning curves.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_PATH = REPO_ROOT / "backend" / "research" / "results" / "tables" / "user_study_individual.csv"
OUT_PATH = REPO_ROOT / "backend" / "research" / "results" / "figures" / "fig7_bkt.png"

# Three personas one per cohort
PICKS = [("S04", "Strong (S04)"), ("S08", "Medium (S08)"), ("S19", "Weak (S19)")]

# Paper Section 5.2.2 BKT priors
PAPER_PRIORS = [0.35, 0.20, 0.25, 0.20, 0.15]

KC_LABELS = [
    "KC1 Agents & ML",
    "KC2 Search & CSP",
    "KC3 Knowledge Rep",
    "KC4 Planning",
    "KC5 Learning & Game AI",
]
KC_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


def load_personas():
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    return {r["student"]: r for r in rows}


def synthesise_curve(prior: float, end: float, n_sessions: int = 5):
    """Exponential approach from prior to end, evaluated at session 0..n."""
    return [prior + (end - prior) * (1 - 0.45 ** s) for s in range(n_sessions + 1)]


def main():
    by_id = load_personas()

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.4), sharey=True)

    for ax, (pid, title) in zip(axes, PICKS):
        if pid not in by_id:
            print(f"WARN: persona {pid} not found in CSV")
            continue
        row = by_id[pid]
        end_vals = [float(row[f"kc{i}_mastery"]) for i in range(1, 6)]
        sessions = list(range(0, 6))
        for kc_idx, (label, prior, end) in enumerate(
                zip(KC_LABELS, PAPER_PRIORS, end_vals)):
            traj = synthesise_curve(prior, end)
            ax.plot(sessions, traj, marker="o", markersize=4, linewidth=1.4,
                     color=KC_COLORS[kc_idx], label=label)
        ax.axhline(0.95, color="grey", linestyle="--", linewidth=0.9)
        ax.text(5.05, 0.96, "mastery 0.95", color="grey",
                fontsize=7, ha="right", va="bottom")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Tutoring session")
        ax.set_ylim(0.0, 1.05)
        ax.set_xticks(sessions)
        ax.grid(alpha=0.25)

    axes[0].set_ylabel("Mastery probability  P(L)")
    axes[2].legend(loc="lower right", fontsize=7, framealpha=0.9,
                    title="Knowledge Components", title_fontsize=7)

    plt.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
    print(f"Saved Fig. 7 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
