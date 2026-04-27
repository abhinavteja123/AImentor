"""
Experiment 6 — BKT Calibration & Adaptive Difficulty Evaluation.

Questions:
  1. How accurately does BKT predict student performance?
  2. Does RL-based difficulty selection outperform random / fixed baselines?

Methodology:
  - Generate synthetic student trajectories with known mastery levels
  - Run BKT updates and compare predicted vs actual performance
  - Compare RL (MAB) difficulty selection vs random, fixed-easy, fixed-hard
  - Report: prediction accuracy, mastery convergence rate, learning efficiency

Output: tables/exp6_bkt_rl.csv and exp6_bkt_rl.tex
"""

from __future__ import annotations

import csv
import math
import os
import random
from dataclasses import dataclass, field
from typing import List, Tuple

# Import from the main codebase
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# BKT functions (standalone, no backend dependency)
P_LEARN = 0.15
P_GUESS = 0.25
P_SLIP = 0.10

def bkt_update(p_l: float, correct: bool) -> float:
    if correct:
        num = p_l * (1 - P_SLIP)
        den = p_l * (1 - P_SLIP) + (1 - p_l) * P_GUESS
    else:
        num = p_l * P_SLIP
        den = p_l * P_SLIP + (1 - p_l) * (1 - P_GUESS)
    p_given = num / max(den, 1e-9)
    return p_given + (1 - p_given) * P_LEARN

def predict_correct(p_l: float) -> float:
    return p_l * (1 - P_SLIP) + (1 - p_l) * P_GUESS

GLOBAL_SEED = 42

random.seed(GLOBAL_SEED)
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "tables")


# ── Synthetic Student Model ──────────────────────────────────

@dataclass
class SyntheticStudent:
    """Simulates a student with known true mastery."""
    true_mastery: float = 0.3
    learning_rate: float = 0.05  # true learning rate per attempt
    name: str = "student"

    def respond(self, difficulty: int) -> bool:
        """Simulate a response. Harder questions reduce P(correct)."""
        diff_penalty = (difficulty - 1) * 0.1
        p_correct = max(0.05, min(0.95, self.true_mastery - diff_penalty))
        correct = random.random() < p_correct
        # Student learns from the attempt
        if correct:
            self.true_mastery = min(0.99, self.true_mastery + self.learning_rate)
        else:
            self.true_mastery = min(0.99, self.true_mastery + self.learning_rate * 0.3)
        return correct


# ── Difficulty Selection Strategies ──────────────────────────

def select_random(mastery: float) -> int:
    return random.randint(1, 5)


def select_fixed_easy(mastery: float) -> int:
    return 1


def select_fixed_hard(mastery: float) -> int:
    return 5


def select_adaptive_rule(mastery: float) -> int:
    """Simple rule: match difficulty to mastery."""
    return max(1, min(5, int(mastery * 5) + 1))


def select_mab(mastery: float, arms: dict, epsilon: float = 0.1) -> int:
    """Epsilon-greedy MAB with mastery-aware filtering."""
    valid = list(range(max(1, int(mastery * 5)), min(6, int(mastery * 5) + 3)))
    if not valid:
        valid = [1, 2]
    if random.random() < epsilon:
        return random.choice(valid)
    best_d, best_r = valid[0], -float("inf")
    for d in valid:
        arm = arms.get(d, {"avg": 0, "n": 0})
        ucb = arm["avg"] + math.sqrt(2 * math.log(max(1, sum(a["n"] for a in arms.values()))) / max(1, arm["n"]))
        if ucb > best_r:
            best_r = ucb
            best_d = d
    return best_d


# ── Run Experiment ───────────────────────────────────────────

@dataclass
class ExperimentResult:
    strategy: str
    final_mastery: float
    bkt_final_mastery: float
    prediction_accuracy: float
    total_correct: int
    total_attempts: int
    mastery_convergence_step: int  # step where BKT mastery > 0.8


def run_trajectory(strategy_name: str, select_fn, n_steps: int = 50) -> ExperimentResult:
    student = SyntheticStudent(true_mastery=0.2, learning_rate=0.04, name=strategy_name)
    bkt_mastery = 0.1
    arms: dict = {}  # for MAB
    correct_predictions = 0
    total_correct = 0
    convergence_step = n_steps  # default: never converged

    for step in range(n_steps):
        if strategy_name == "mab":
            difficulty = select_mab(bkt_mastery, arms, epsilon=max(0.05, 0.3 * (0.99 ** step)))
        else:
            difficulty = select_fn(bkt_mastery)

        # Predict
        p_correct = predict_correct(bkt_mastery)
        predicted = p_correct >= 0.5

        # Student responds
        actual = student.respond(difficulty)
        if predicted == actual:
            correct_predictions += 1
        if actual:
            total_correct += 1

        # BKT update
        old_mastery = bkt_mastery
        bkt_mastery = bkt_update(bkt_mastery, actual)

        # Track convergence
        if bkt_mastery >= 0.8 and convergence_step == n_steps:
            convergence_step = step

        # MAB reward update
        if strategy_name == "mab":
            reward = (bkt_mastery - old_mastery) * (1 + (difficulty - 1) * 0.2) + (0.2 if actual else -0.1)
            arm = arms.get(difficulty, {"avg": 0, "n": 0, "total": 0})
            arm["n"] += 1
            arm["total"] += reward
            arm["avg"] = arm["total"] / arm["n"]
            arms[difficulty] = arm

    return ExperimentResult(
        strategy=strategy_name,
        final_mastery=round(student.true_mastery, 4),
        bkt_final_mastery=round(bkt_mastery, 4),
        prediction_accuracy=round(correct_predictions / n_steps, 4),
        total_correct=total_correct,
        total_attempts=n_steps,
        mastery_convergence_step=convergence_step,
    )


def run(n_trials: int = 100) -> list:
    strategies = {
        "random": select_random,
        "fixed_easy": select_fixed_easy,
        "fixed_hard": select_fixed_hard,
        "adaptive_rule": select_adaptive_rule,
        "mab": None,  # handled separately
    }

    aggregated = {name: [] for name in strategies}

    for _ in range(n_trials):
        for name, fn in strategies.items():
            result = run_trajectory(name, fn, n_steps=60)
            aggregated[name].append(result)

    # Average results
    rows = []
    for name, results in aggregated.items():
        avg = lambda attr: round(sum(getattr(r, attr) for r in results) / len(results), 4)
        rows.append({
            "strategy": name,
            "avg_final_mastery": avg("final_mastery"),
            "avg_bkt_mastery": avg("bkt_final_mastery"),
            "prediction_accuracy": avg("prediction_accuracy"),
            "avg_correct_pct": round(avg("total_correct") / 60 * 100, 2),
            "avg_convergence_step": round(avg("mastery_convergence_step"), 1),
        })

    # Write CSV
    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_DIR, "exp6_bkt_rl.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Write LaTeX
    tex_path = os.path.join(RESULTS_DIR, "exp6_bkt_rl.tex")
    with open(tex_path, "w") as f:
        f.write("\\begin{table}[htbp]\n\\centering\n")
        f.write("\\caption{BKT Prediction Accuracy \\& RL Difficulty Selection Comparison}\n")
        f.write("\\label{tab:bkt_rl}\n")
        f.write("\\begin{tabular}{lccccr}\n\\toprule\n")
        f.write("Strategy & True Mastery & BKT Mastery & Pred. Acc. & Correct\\% & Conv. Step \\\\\n\\midrule\n")
        for r in rows:
            f.write(f"{r['strategy'].replace('_', ' ').title()} & "
                    f"{r['avg_final_mastery']} & {r['avg_bkt_mastery']} & "
                    f"{r['prediction_accuracy']} & {r['avg_correct_pct']}\\% & "
                    f"{r['avg_convergence_step']} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

    print(f"[Exp6] BKT+RL results written to {csv_path}")
    return rows


if __name__ == "__main__":
    results = run()
    for r in results:
        print(r)
