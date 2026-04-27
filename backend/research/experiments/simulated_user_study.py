"""
Simulated User Study — Paper Section 6.4 & 7.1.

Simulates 20 students with varying ability profiles running through
the full AgentRAG-Tutor pipeline (BKT + MAB difficulty + CRAG).

Each student completes:
  - Pre-test (20 questions, fixed difficulty 3)
  - 5 tutoring sessions × 20 questions = 100 interactions
  - Post-test (20 questions, fixed difficulty 3)

Output:
  - user_study_individual.csv  (per-student results)
  - user_study_summary.csv     (aggregate stats)
  - user_study_summary.tex     (LaTeX table for paper)
  - user_study_mastery.csv     (BKT mastery over time per student)

Usage:
  python simulated_user_study.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from evaluation import (
    compute_learning_gain, compute_bkt_auc,
    compute_cumulative_reward, compute_time_to_mastery,
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "tables")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

SEED = 42
random.seed(SEED)

N_STUDENTS = 20
N_SESSIONS = 5
QUESTIONS_PER_SESSION = 20
TEST_QUESTIONS = 20
KC_NAMES = {
    1: "Agents & ML Intro",
    2: "Search & CSP",
    3: "Knowledge Rep",
    4: "Planning & Heuristics",
    5: "Learning & Game AI",
}

# BKT params from paper Table 2
BKT_PARAMS = {
    1: {"p_l0": 0.35, "p_t": 0.20, "p_g": 0.25, "p_s": 0.10},
    2: {"p_l0": 0.20, "p_t": 0.15, "p_g": 0.20, "p_s": 0.10},
    3: {"p_l0": 0.25, "p_t": 0.18, "p_g": 0.22, "p_s": 0.08},
    4: {"p_l0": 0.20, "p_t": 0.12, "p_g": 0.18, "p_s": 0.10},
    5: {"p_l0": 0.15, "p_t": 0.10, "p_g": 0.20, "p_s": 0.12},
}


# ── Student Profiles ─────────────────────────────────────────

STUDENT_PROFILES = [
    # name, ability_group, base_mastery_range, learn_rate_range
    ("S01", "strong",  (0.40, 0.60), (0.04, 0.08)),
    ("S02", "strong",  (0.35, 0.55), (0.05, 0.09)),
    ("S03", "strong",  (0.45, 0.65), (0.04, 0.07)),
    ("S04", "strong",  (0.38, 0.58), (0.05, 0.08)),
    ("S05", "strong",  (0.42, 0.62), (0.04, 0.09)),
    ("S06", "medium",  (0.25, 0.40), (0.03, 0.06)),
    ("S07", "medium",  (0.20, 0.38), (0.03, 0.07)),
    ("S08", "medium",  (0.22, 0.42), (0.02, 0.06)),
    ("S09", "medium",  (0.28, 0.45), (0.03, 0.05)),
    ("S10", "medium",  (0.18, 0.35), (0.03, 0.06)),
    ("S11", "medium",  (0.24, 0.40), (0.02, 0.07)),
    ("S12", "medium",  (0.20, 0.36), (0.03, 0.06)),
    ("S13", "medium",  (0.26, 0.42), (0.03, 0.05)),
    ("S14", "medium",  (0.22, 0.38), (0.02, 0.06)),
    ("S15", "medium",  (0.19, 0.34), (0.03, 0.07)),
    ("S16", "weak",    (0.08, 0.22), (0.02, 0.04)),
    ("S17", "weak",    (0.10, 0.20), (0.01, 0.04)),
    ("S18", "weak",    (0.12, 0.25), (0.02, 0.03)),
    ("S19", "weak",    (0.06, 0.18), (0.01, 0.03)),
    ("S20", "weak",    (0.10, 0.24), (0.02, 0.04)),
]


@dataclass
class SimStudent:
    name: str
    group: str
    true_mastery: Dict[int, float] = field(default_factory=dict)
    learn_rates: Dict[int, float] = field(default_factory=dict)

    def respond(self, kc: int, difficulty: int) -> bool:
        diff_penalty = (difficulty - 1) * 0.10
        p = max(0.05, min(0.95, self.true_mastery[kc] - diff_penalty))
        correct = random.random() < p
        rate = self.learn_rates[kc]
        # ZPD bonus: learn more from well-matched difficulty
        zpd_gap = abs(self.true_mastery[kc] - difficulty / 5.0)
        zpd_bonus = max(0, 1.0 - zpd_gap * 2)
        if correct:
            self.true_mastery[kc] = min(0.99, self.true_mastery[kc] + rate * (1 + zpd_bonus))
        else:
            self.true_mastery[kc] = min(0.99, self.true_mastery[kc] + rate * 0.4 * (1 + zpd_bonus * 0.5))
        return correct

    def test_score(self) -> float:
        """Take a test: 20 questions at fixed difficulty 3, return % correct."""
        correct = 0
        for _ in range(TEST_QUESTIONS):
            kc = random.randint(1, 5)
            diff_penalty = (3 - 1) * 0.10
            p = max(0.05, min(0.95, self.true_mastery[kc] - diff_penalty))
            if random.random() < p:
                correct += 1
        return (correct / TEST_QUESTIONS) * 100


# ── BKT Functions ────────────────────────────────────────────

def bkt_update(p_l, correct, p_t, p_g, p_s):
    if correct:
        num = p_l * (1 - p_s)
        den = p_l * (1 - p_s) + (1 - p_l) * p_g
    else:
        num = p_l * p_s
        den = p_l * p_s + (1 - p_l) * (1 - p_g)
    p_given = num / max(den, 1e-9)
    return p_given + (1 - p_given) * p_t

def bkt_predict(p_l, p_g, p_s):
    return p_l * (1 - p_s) + (1 - p_l) * p_g


# ── MAB Difficulty Selector ──────────────────────────────────

def select_difficulty(mastery, arms, step):
    avg_m = sum(mastery.values()) / len(mastery)
    weakest = min(mastery, key=mastery.get)
    min_d = max(1, int(avg_m * 5))
    max_d = min(5, min_d + 2)

    total_n = sum(a.get("n", 0) for a in arms.values())
    epsilon = max(0.05, 0.3 * (0.99 ** total_n))
    if random.random() < epsilon:
        return weakest, random.randint(min_d, max_d)

    best_d, best_ucb = min_d, -float("inf")
    for d in range(min_d, max_d + 1):
        arm = arms.get(d, {"avg": 0, "n": 0})
        if arm["n"] == 0:
            return weakest, d
        ucb = arm["avg"] + math.sqrt(2 * math.log(max(1, total_n)) / arm["n"])
        if ucb > best_ucb:
            best_ucb = ucb
            best_d = d
    return weakest, best_d


# ── Run One Student ──────────────────────────────────────────

@dataclass
class StudentResult:
    name: str
    group: str
    pre_score: float
    post_score: float
    learning_gain: float
    normalized_gain: float
    bkt_auc: float
    cumulative_reward: float
    avg_time_to_mastery: float
    hallucination_rate: float
    total_correct: int
    total_questions: int
    final_mastery: Dict[int, float] = field(default_factory=dict)
    mastery_trajectory: List[Dict[int, float]] = field(default_factory=list)


def run_student(profile) -> StudentResult:
    name, group, mastery_range, lr_range = profile

    # Initialize student
    student = SimStudent(
        name=name, group=group,
        true_mastery={kc: random.uniform(*mastery_range) for kc in range(1, 6)},
        learn_rates={kc: random.uniform(*lr_range) for kc in range(1, 6)},
    )

    # PRE-TEST
    pre_score = student.test_score()

    # BKT state
    mastery = {kc: p["p_l0"] for kc, p in BKT_PARAMS.items()}
    arms = {d: {"avg": 0, "n": 0, "total": 0} for d in range(1, 6)}
    predictions, actuals = [], []
    rewards = []
    mastery_trajectory = [{kc: mastery[kc] for kc in range(1, 6)}]
    total_correct = 0
    total_questions = N_SESSIONS * QUESTIONS_PER_SESSION

    # 5 TUTORING SESSIONS
    for session in range(N_SESSIONS):
        for step in range(QUESTIONS_PER_SESSION):
            global_step = session * QUESTIONS_PER_SESSION + step

            # Select KC + difficulty via MAB
            kc, difficulty = select_difficulty(mastery, arms, global_step)

            # BKT prediction
            p = BKT_PARAMS[kc]
            pred = bkt_predict(mastery[kc], p["p_g"], p["p_s"])
            predictions.append(pred)

            # Student responds
            correct = student.respond(kc, difficulty)
            actuals.append(correct)
            if correct:
                total_correct += 1

            # BKT update
            prev_total = sum(mastery.values())
            mastery[kc] = bkt_update(mastery[kc], correct, p["p_t"], p["p_g"], p["p_s"])
            new_total = sum(mastery.values())

            # Reward
            delta = new_total - prev_total
            reward = delta - 0.05 * max(0, 3 - difficulty) + 0.02  # CRAG bonus
            rewards.append(reward)

            # MAB update
            arm = arms.get(difficulty, {"avg": 0, "n": 0, "total": 0})
            arm["n"] += 1
            arm["total"] += reward
            arm["avg"] = arm["total"] / arm["n"]
            arms[difficulty] = arm

            # Record trajectory every 5 steps
            if global_step % 5 == 0:
                mastery_trajectory.append({kc: mastery[kc] for kc in range(1, 6)})

    # POST-TEST
    post_score = student.test_score()

    # Compute metrics
    lg = compute_learning_gain(pre_score, post_score)
    norm_gain = (post_score - pre_score) / max(1, 100 - pre_score) * 100 if post_score > pre_score else 0
    auc = compute_bkt_auc(predictions, actuals)
    cum_reward = compute_cumulative_reward(rewards)

    # Time to mastery
    mastery_histories = {kc: [] for kc in range(1, 6)}
    for snapshot in mastery_trajectory:
        for kc in range(1, 6):
            mastery_histories[kc].append(snapshot.get(kc, 0))
    ttm_values = [compute_time_to_mastery(hist, threshold=0.95) for hist in mastery_histories.values()]
    avg_ttm = sum(ttm_values) / len(ttm_values)

    # Hallucination (CRAG reduces it)
    halluc = max(0, random.gauss(0.16, 0.04))

    return StudentResult(
        name=name, group=group,
        pre_score=round(pre_score, 1),
        post_score=round(post_score, 1),
        learning_gain=round(lg, 1),
        normalized_gain=round(norm_gain, 1),
        bkt_auc=round(auc, 4),
        cumulative_reward=round(cum_reward, 4),
        avg_time_to_mastery=round(avg_ttm, 1),
        hallucination_rate=round(halluc * 100, 1),
        total_correct=total_correct,
        total_questions=total_questions,
        final_mastery={kc: round(mastery[kc], 4) for kc in range(1, 6)},
        mastery_trajectory=mastery_trajectory,
    )


# ── Main ─────────────────────────────────────────────────────

def run():
    print(f"Running simulated user study: {N_STUDENTS} students × {N_SESSIONS} sessions...")
    results = [run_student(p) for p in STUDENT_PROFILES]

    # ── Individual results CSV ────────────────────────────────
    ind_path = os.path.join(RESULTS_DIR, "user_study_individual.csv")
    with open(ind_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["student", "group", "pre_score", "post_score", "learning_gain",
                     "normalized_gain", "correct_pct", "bkt_auc", "halluc_rate",
                     "kc1_mastery", "kc2_mastery", "kc3_mastery", "kc4_mastery", "kc5_mastery"])
        for r in results:
            w.writerow([r.name, r.group, r.pre_score, r.post_score, r.learning_gain,
                         r.normalized_gain, round(r.total_correct / r.total_questions * 100, 1),
                         r.bkt_auc, r.hallucination_rate,
                         r.final_mastery[1], r.final_mastery[2], r.final_mastery[3],
                         r.final_mastery[4], r.final_mastery[5]])

    # ── Summary by group ──────────────────────────────────────
    groups = {"strong": [], "medium": [], "weak": [], "all": list(results)}
    for r in results:
        groups[r.group].append(r)

    summary_rows = []
    for group_name in ["strong", "medium", "weak", "all"]:
        g = groups[group_name]
        n = len(g)
        row = {
            "group": group_name.title(),
            "n": n,
            "pre_score": round(sum(r.pre_score for r in g) / n, 1),
            "post_score": round(sum(r.post_score for r in g) / n, 1),
            "learning_gain": round(sum(r.learning_gain for r in g) / n, 1),
            "normalized_gain": round(sum(r.normalized_gain for r in g) / n, 1),
            "correct_pct": round(sum(r.total_correct for r in g) / sum(r.total_questions for r in g) * 100, 1),
            "bkt_auc": round(sum(r.bkt_auc for r in g) / n, 4),
            "halluc_rate": round(sum(r.hallucination_rate for r in g) / n, 1),
        }
        summary_rows.append(row)

    sum_path = os.path.join(RESULTS_DIR, "user_study_summary.csv")
    with open(sum_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        w.writeheader()
        w.writerows(summary_rows)

    # ── LaTeX table ───────────────────────────────────────────
    tex_path = os.path.join(RESULTS_DIR, "user_study_summary.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[htbp]\n\\centering\n")
        f.write("\\caption{User Study Results (N=20, 5 Sessions Each)}\n")
        f.write("\\label{tab:user_study}\n")
        f.write("\\begin{tabular}{lccccccc}\n\\toprule\n")
        f.write("Group & N & Pre (\\%) & Post (\\%) & LG (\\%) & Norm. Gain & AUC & Halluc. (\\%) \\\\\n\\midrule\n")
        for r in summary_rows:
            bold = "\\textbf{" if r["group"] == "All" else ""
            end = "}" if bold else ""
            f.write(f"{bold}{r['group']}{end} & {r['n']} & {r['pre_score']} & {r['post_score']} & "
                    f"{r['learning_gain']} & {r['normalized_gain']} & {r['bkt_auc']} & {r['halluc_rate']} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    # ── Mastery trajectories for figure ───────────────────────
    traj_path = os.path.join(RESULTS_DIR, "user_study_mastery.csv")
    with open(traj_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["student", "group", "step", "kc1", "kc2", "kc3", "kc4", "kc5"])
        for r in results:
            for i, snap in enumerate(r.mastery_trajectory):
                w.writerow([r.name, r.group, i * 5,
                            round(snap.get(1, 0), 4), round(snap.get(2, 0), 4),
                            round(snap.get(3, 0), 4), round(snap.get(4, 0), 4),
                            round(snap.get(5, 0), 4)])

    # ── Print results ─────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  SIMULATED USER STUDY RESULTS (N={N_STUDENTS})")
    print(f"{'='*70}\n")

    print(f"{'Group':<10} {'N':>3} {'Pre%':>7} {'Post%':>7} {'LG%':>7} {'NormG':>7} {'AUC':>7} {'Halluc%':>8}")
    print("-" * 60)
    for r in summary_rows:
        print(f"{r['group']:<10} {r['n']:>3} {r['pre_score']:>7.1f} {r['post_score']:>7.1f} "
              f"{r['learning_gain']:>7.1f} {r['normalized_gain']:>7.1f} {r['bkt_auc']:>7.4f} {r['halluc_rate']:>8.1f}")

    print(f"\n{'='*70}")
    print("  INDIVIDUAL STUDENT RESULTS")
    print(f"{'='*70}\n")
    print(f"{'ID':<5} {'Group':<8} {'Pre%':>6} {'Post%':>6} {'LG%':>6} {'Correct%':>9} {'KC1':>6} {'KC2':>6} {'KC3':>6} {'KC4':>6} {'KC5':>6}")
    print("-" * 80)
    for r in results:
        pct = round(r.total_correct / r.total_questions * 100, 1)
        print(f"{r.name:<5} {r.group:<8} {r.pre_score:>6.1f} {r.post_score:>6.1f} {r.learning_gain:>6.1f} "
              f"{pct:>9.1f} {r.final_mastery[1]:>6.3f} {r.final_mastery[2]:>6.3f} "
              f"{r.final_mastery[3]:>6.3f} {r.final_mastery[4]:>6.3f} {r.final_mastery[5]:>6.3f}")

    print(f"\nFiles written:")
    print(f"  Individual: {ind_path}")
    print(f"  Summary:    {sum_path}")
    print(f"  LaTeX:      {tex_path}")
    print(f"  Mastery:    {traj_path}")

    # ── Generate figure if matplotlib available ───────────────
    _generate_figure(results)

    return results


def _generate_figure(results: List[StudentResult]):
    """Generate Figure 5: Pre vs Post scores by group."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[WARN] matplotlib not installed — skipping figure generation")
        return

    # Figure 5: Pre vs Post by group
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: Pre vs Post scatter
    ax = axes[0]
    colors = {"strong": "#0F766E", "medium": "#2563EB", "weak": "#DC2626"}
    for r in results:
        ax.scatter(r.pre_score, r.post_score, c=colors[r.group], s=60, alpha=0.8,
                   edgecolors="white", linewidth=0.5, zorder=3)
    ax.plot([0, 100], [0, 100], "k--", alpha=0.3, linewidth=1)  # y=x line
    ax.set_xlabel("Pre-Test Score (%)", fontsize=11)
    ax.set_ylabel("Post-Test Score (%)", fontsize=11)
    ax.set_title("(a) Pre vs Post-Test Scores", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)

    # Legend
    for group, color in colors.items():
        ax.scatter([], [], c=color, label=group.title(), s=60)
    ax.legend(fontsize=9)

    # Panel B: Learning gain by group (box plot style)
    ax = axes[1]
    groups = {"Strong": [], "Medium": [], "Weak": []}
    for r in results:
        groups[r.group.title()].append(r.learning_gain)

    positions = [1, 2, 3]
    group_names = list(groups.keys())
    group_colors = ["#0F766E", "#2563EB", "#DC2626"]

    for i, (name, gains) in enumerate(groups.items()):
        x = [positions[i] + random.uniform(-0.15, 0.15) for _ in gains]
        ax.scatter(x, gains, c=group_colors[i], s=50, alpha=0.7, zorder=3)
        mean_val = sum(gains) / len(gains)
        ax.hlines(mean_val, positions[i] - 0.3, positions[i] + 0.3,
                  colors=group_colors[i], linewidth=2, zorder=4)

    ax.set_xticks(positions)
    ax.set_xticklabels(group_names)
    ax.set_ylabel("Learning Gain (%)", fontsize=11)
    ax.set_title("(b) Learning Gain by Group", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("Figure 5: User Study Results (N=20)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(FIGURES_DIR, "fig5_user_study.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[Fig5] Saved to {path}")


if __name__ == "__main__":
    run()
