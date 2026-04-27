"""
PPO Adaptive Difficulty Agent — Paper Section 5.3.

Custom Gymnasium environment + stable-baselines3 PPO wrapper.

MDP Formulation (Table 3):
  State:   s_t = [P(L₁), P(L₂), P(L₃), P(L₄), P(L₅), session_step_norm] ∈ ℝ⁶
  Action:  a_t ∈ {0,1,2,3,4} → difficulty ∈ {1,2,3,4,5}
  Reward:  r_t = Σ_k ΔP(L_t^k) − λ·max(0, 3−a_t)    [penalize too-easy]
  Horizon: T = 20 questions per session

Falls back to the existing MAB controller if stable-baselines3
is not installed, keeping the system functional without GPU deps.
"""

from __future__ import annotations

import logging
import os
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Check for optional GPU dependencies ──────────────────────

_HAS_SB3 = False
_HAS_GYM = False

try:
    import gymnasium as gym
    _HAS_GYM = True
except ImportError:
    logger.info("gymnasium not installed. PPO env unavailable, using MAB fallback.")

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.callbacks import EvalCallback
    _HAS_SB3 = True
except ImportError:
    logger.info("stable-baselines3 not installed. Using MAB fallback for difficulty control.")


# ── Gymnasium Environment ─────────────────────────────────────

if _HAS_GYM:

    class TutoringEnv(gym.Env):
        """
        Custom Gym environment for PPO-based adaptive difficulty.

        State (6-dim):  [P(L₁..L₅), session_step / max_steps]
        Action (5):     difficulty level 1-5
        Reward:         mastery gain − easy-question penalty
        """
        metadata = {"render_modes": []}

        def __init__(self, qa_bank: Optional[List[Dict]] = None,
                     max_steps: int = 20, lambda_pen: float = 0.05):
            super().__init__()
            self.qa_bank = qa_bank or []
            self.max_steps = max_steps
            self.lambda_pen = lambda_pen

            self.observation_space = gym.spaces.Box(
                low=0.0, high=1.0, shape=(6,), dtype=np.float32
            )
            self.action_space = gym.spaces.Discrete(5)

            self.tracker = None
            self.step_count = 0

        def reset(self, seed=None, options=None):
            super().reset(seed=seed)
            from ..bkt.bkt_tracker import BKTTracker
            student_id = f"sim_{np.random.randint(0, 10000)}"
            self.tracker = BKTTracker(student_id)
            self.step_count = 0
            return self._get_obs(), {}

        def step(self, action: int):
            difficulty = int(action) + 1
            prev_mastery = sum(self.tracker.get_mastery_vector())

            # Pick weakest KC to focus
            kc = self.tracker.get_weakest_kc()

            # Simulate student answer (BKT-predicted probability modulated by difficulty)
            p_correct = self.tracker.predict_next_correct(kc)
            difficulty_factor = {1: 0.85, 2: 0.75, 3: 0.60, 4: 0.45, 5: 0.30}
            p_answer = p_correct * difficulty_factor.get(difficulty, 0.5)
            correct = np.random.random() < p_answer

            # Update BKT
            self.tracker.update(kc, correct)
            new_mastery = sum(self.tracker.get_mastery_vector())

            # Reward = learning gain − penalty for too-easy questions
            reward = (new_mastery - prev_mastery) - self.lambda_pen * max(0, 3 - difficulty)

            self.step_count += 1
            terminated = self.tracker.all_mastered() or self.step_count >= self.max_steps
            truncated = False

            return self._get_obs(), reward, terminated, truncated, {
                "difficulty": difficulty,
                "kc": kc,
                "correct": correct,
                "mastery_vector": self.tracker.get_mastery_vector(),
            }

        def _get_obs(self) -> np.ndarray:
            mastery = self.tracker.get_mastery_vector() if self.tracker else [0.2] * 5
            step_norm = self.step_count / self.max_steps
            return np.array(mastery + [step_norm], dtype=np.float32)


# ── PPO Agent Wrapper ─────────────────────────────────────────

class PPODifficultyAgent:
    """
    PPO-based difficulty controller matching paper Section 5.3.

    Trains on simulated student trajectories using BKT tracker.
    Falls back to a local MAB if stable-baselines3 is not installed
    or no checkpoint is supplied.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self._use_ppo = _HAS_SB3 and _HAS_GYM

        if self._use_ppo and model_path and Path(model_path).exists():
            self.model = PPO.load(model_path)
            logger.info("Loaded PPO model from %s", model_path)
        elif not self._use_ppo:
            logger.info("Using MAB fallback for difficulty selection")

        # MAB fallback state — always initialised so select_difficulty
        # can degrade gracefully when no checkpoint is loaded.
        self._mab_arms: Dict[int, Dict] = {
            d: {"avg": 0.0, "n": 0, "total": 0.0} for d in range(1, 6)
        }

    @property
    def is_ppo_active(self) -> bool:
        """True iff a real PPO checkpoint is loaded and inference uses it."""
        return self._use_ppo and self.model is not None

    def select_difficulty(self, mastery_vector: List[float],
                          session_step: int = 0,
                          max_steps: int = 20) -> int:
        """Select next difficulty level given current mastery state."""
        if self._use_ppo and self.model is not None:
            step_norm = session_step / max_steps
            obs = np.array(mastery_vector + [step_norm], dtype=np.float32)
            action, _ = self.model.predict(obs, deterministic=False)
            return int(action) + 1
        else:
            return self._mab_select(mastery_vector)

    def update_reward(self, difficulty: int, reward: float):
        """Update MAB arm with observed reward."""
        arm = self._mab_arms.get(difficulty, {"avg": 0, "n": 0, "total": 0})
        arm["n"] += 1
        arm["total"] += reward
        arm["avg"] = arm["total"] / arm["n"]
        self._mab_arms[difficulty] = arm

    def _mab_select(self, mastery_vector: List[float]) -> int:
        """UCB1 Multi-Armed Bandit with mastery-aware filtering."""
        avg_mastery = sum(mastery_vector) / len(mastery_vector)

        # Mastery-aware difficulty range
        min_d = max(1, int(avg_mastery * 5))
        max_d = min(5, min_d + 2)
        valid = list(range(min_d, max_d + 1))

        total_n = sum(a["n"] for a in self._mab_arms.values())

        # Epsilon-greedy with decay
        epsilon = max(0.05, 0.3 * (0.99 ** total_n))
        if random.random() < epsilon:
            return random.choice(valid)

        # UCB1
        best_d, best_ucb = valid[0], -float("inf")
        for d in valid:
            arm = self._mab_arms.get(d, {"avg": 0, "n": 0})
            if arm["n"] == 0:
                return d  # explore unvisited
            ucb = arm["avg"] + math.sqrt(2 * math.log(max(1, total_n)) / arm["n"])
            if ucb > best_ucb:
                best_ucb = ucb
                best_d = d
        return best_d

    # ── Training ──────────────────────────────────────────────

    @staticmethod
    def train(qa_bank_path: Optional[str] = None,
              output_path: str = "models/ppo_agent",
              total_timesteps: int = 500_000) -> Optional["PPODifficultyAgent"]:
        """
        Train PPO agent on simulated tutoring environment.
        Paper Section 5.3.2 hyperparameters.
        """
        if not _HAS_SB3 or not _HAS_GYM:
            logger.error("Cannot train PPO: missing stable-baselines3 or gymnasium")
            return None

        qa_bank = []
        if qa_bank_path and Path(qa_bank_path).exists():
            with open(qa_bank_path) as f:
                qa_bank = json.load(f)

        # Vectorized environment (4 parallel)
        env = make_vec_env(
            lambda: TutoringEnv(qa_bank),
            n_envs=4,
        )
        eval_env = make_vec_env(lambda: TutoringEnv(qa_bank), n_envs=1)

        model = PPO(
            policy="MlpPolicy",
            env=env,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            verbose=1,
            tensorboard_log="logs/ppo_tutor/",
            policy_kwargs=dict(net_arch=[64, 64]),
        )

        os.makedirs(output_path, exist_ok=True)
        eval_callback = EvalCallback(
            eval_env,
            best_model_save_path=output_path,
            log_path="logs/eval/",
            eval_freq=10_000,
            n_eval_episodes=20,
            deterministic=True,
        )

        logger.info("Training PPO for %d timesteps...", total_timesteps)
        model.learn(total_timesteps=total_timesteps, callback=eval_callback)
        final_path = os.path.join(output_path, "final_model")
        model.save(final_path)
        logger.info("PPO agent saved to %s", final_path)

        agent = PPODifficultyAgent(final_path)
        agent.model = model
        return agent


# ── Module-level lazy singleton ───────────────────────────────

_AGENT_SINGLETON: Optional[PPODifficultyAgent] = None


def _resolve_default_model_path() -> str:
    """Resolve PPO checkpoint path from env or repo-relative default."""
    env = os.getenv("PPO_MODEL_PATH")
    if env:
        return env
    # Repo-relative default: backend/models/ppo_agent/final_model.zip
    here = Path(__file__).resolve()
    repo_root = here.parents[5]  # …/AImentor (services/ai/adaptive/ppo_agent.py → 5 up)
    return str(repo_root / "backend" / "models" / "ppo_agent" / "final_model.zip")


def get_ppo_agent() -> PPODifficultyAgent:
    """
    Lazy-load the production PPO agent. Idempotent.

    On first call, looks at ``$PPO_MODEL_PATH`` (or the repo-default
    ``backend/models/ppo_agent/final_model.zip``). If the file exists and
    stable-baselines3 is installed, the policy is loaded; otherwise the
    returned agent runs the local MAB fallback.
    """
    global _AGENT_SINGLETON
    if _AGENT_SINGLETON is None:
        path = _resolve_default_model_path()
        # Only pass a path if it exists, so the constructor doesn't log
        # "Using MAB fallback" prematurely.
        _AGENT_SINGLETON = PPODifficultyAgent(path if Path(path).exists() else None)
        if not _AGENT_SINGLETON.is_ppo_active:
            logger.info(
                "PPO checkpoint not found at %s — runtime will use MAB fallback.",
                path,
            )
    return _AGENT_SINGLETON


def reset_ppo_agent() -> None:
    """Test-only helper to drop the cached singleton."""
    global _AGENT_SINGLETON
    _AGENT_SINGLETON = None
