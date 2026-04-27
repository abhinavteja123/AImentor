"""
RL Adaptive Difficulty Controller — Multi-Armed Bandit (MAB).

Each "arm" is a (difficulty_level, question_type) pair.
Reward = improvement in BKT mastery × difficulty bonus − time penalty.
Uses epsilon-greedy exploration with decay.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.tutor import RLPolicyState
from .ppo_agent import get_ppo_agent

logger = logging.getLogger(__name__)

DIFFICULTY_LEVELS = [1, 2, 3, 4, 5]
QUESTION_TYPES = ["multiple_choice", "short_answer", "code_exercise", "open_ended"]
ARMS = [(d, t) for d in DIFFICULTY_LEVELS for t in QUESTION_TYPES]


def _arm_key(difficulty: int, q_type: str) -> str:
    return f"{difficulty}_{q_type}"


# Difficulty-conditioned distribution over question types.
# Higher difficulty → more open-ended / code questions; easy levels → MCQ.
_QTYPE_WEIGHTS_BY_DIFFICULTY: Dict[int, Dict[str, float]] = {
    1: {"multiple_choice": 0.55, "short_answer": 0.30, "code_exercise": 0.05, "open_ended": 0.10},
    2: {"multiple_choice": 0.40, "short_answer": 0.35, "code_exercise": 0.10, "open_ended": 0.15},
    3: {"multiple_choice": 0.25, "short_answer": 0.35, "code_exercise": 0.20, "open_ended": 0.20},
    4: {"multiple_choice": 0.10, "short_answer": 0.30, "code_exercise": 0.30, "open_ended": 0.30},
    5: {"multiple_choice": 0.05, "short_answer": 0.20, "code_exercise": 0.35, "open_ended": 0.40},
}


def _pick_question_type(difficulty: int) -> str:
    weights = _QTYPE_WEIGHTS_BY_DIFFICULTY.get(
        difficulty, _QTYPE_WEIGHTS_BY_DIFFICULTY[3])
    types = list(weights.keys())
    probs = list(weights.values())
    return random.choices(types, weights=probs, k=1)[0]


class DifficultyController:
    """Epsilon-greedy Multi-Armed Bandit for selecting question difficulty and type."""

    EPSILON_MIN = 0.05
    EPSILON_DECAY = 0.995

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_policy(self, user_id: UUID) -> RLPolicyState:
        result = await self.db.execute(
            select(RLPolicyState).where(RLPolicyState.user_id == user_id))
        policy = result.scalar_one_or_none()
        if policy is None:
            initial_state = {_arm_key(d, t): {"count": 0, "total_reward": 0.0, "avg_reward": 0.0}
                            for d, t in ARMS}
            policy = RLPolicyState(user_id=user_id, bandit_state=initial_state, epsilon=0.3, total_interactions=0)
            self.db.add(policy)
            await self.db.flush()
        return policy

    async def select_action(self, user_id: UUID, current_mastery: float = 0.5) -> Dict[str, Any]:
        """Select the next (difficulty, question_type) using epsilon-greedy."""
        policy = await self._get_or_create_policy(user_id)
        bandit = policy.bandit_state or {}
        epsilon = policy.epsilon

        # Mastery-aware difficulty range: don't give difficulty 5 to a 0.1 mastery student
        min_diff = max(1, int(current_mastery * 5))
        max_diff = min(5, min_diff + 2)
        valid_arms = [(d, t) for d, t in ARMS if min_diff <= d <= max_diff]
        if not valid_arms:
            valid_arms = ARMS[:4]  # fallback to easiest

        if random.random() < epsilon:
            # Explore: random arm
            difficulty, q_type = random.choice(valid_arms)
        else:
            # Exploit: best average reward
            best_key, best_reward = None, -float("inf")
            for d, t in valid_arms:
                key = _arm_key(d, t)
                arm_data = bandit.get(key, {"avg_reward": 0.0, "count": 0})
                # UCB1 bonus for under-explored arms
                total = policy.total_interactions or 1
                count = arm_data.get("count", 0)
                ucb = arm_data.get("avg_reward", 0.0)
                if count > 0:
                    import math
                    ucb += math.sqrt(2 * math.log(total) / count)
                else:
                    ucb = float("inf")  # always try unexplored
                if ucb > best_reward:
                    best_reward = ucb
                    best_key = (d, t)
            difficulty, q_type = best_key or random.choice(valid_arms)

        return {"difficulty": difficulty, "question_type": q_type,
                "epsilon": round(epsilon, 4), "exploration": random.random() < epsilon,
                "selector": "mab"}

    async def select_action_with_ppo(self, user_id: UUID,
                                      mastery_vector: List[float],
                                      session_step: int = 0,
                                      max_steps: int = 20) -> Dict[str, Any]:
        """
        Paper Section 5.3 inference path.

        Uses the trained PPO policy with the 5-KC mastery vector + step ratio
        as state. Question type is sampled from a difficulty-conditioned
        distribution since the paper MDP defines a difficulty-only action.
        Falls back to ``select_action`` (MAB) when no PPO checkpoint loaded.
        """
        agent = get_ppo_agent()
        if not agent.is_ppo_active:
            avg = sum(mastery_vector) / max(len(mastery_vector), 1)
            return await self.select_action(user_id, current_mastery=avg)

        difficulty = agent.select_difficulty(
            mastery_vector=list(mastery_vector),
            session_step=session_step,
            max_steps=max_steps,
        )
        q_type = _pick_question_type(difficulty)
        # Update epsilon counter for analytics parity with MAB path.
        policy = await self._get_or_create_policy(user_id)
        return {"difficulty": int(difficulty), "question_type": q_type,
                "epsilon": round(policy.epsilon, 4), "exploration": False,
                "selector": "ppo"}

    async def update_reward(self, user_id: UUID, difficulty: int, question_type: str,
                            mastery_before: float, mastery_after: float,
                            is_correct: bool, response_time_seconds: int = 0) -> Dict[str, Any]:
        """Update the bandit arm after observing a response."""
        policy = await self._get_or_create_policy(user_id)

        # Reward = mastery improvement × difficulty bonus - time penalty
        mastery_delta = mastery_after - mastery_before
        difficulty_bonus = 1.0 + (difficulty - 1) * 0.2
        time_penalty = min(0.3, max(0, (response_time_seconds - 120) / 600)) if response_time_seconds > 0 else 0
        correctness_bonus = 0.2 if is_correct else -0.1
        reward = mastery_delta * difficulty_bonus + correctness_bonus - time_penalty

        key = _arm_key(difficulty, question_type)
        bandit = dict(policy.bandit_state or {})
        arm = bandit.get(key, {"count": 0, "total_reward": 0.0, "avg_reward": 0.0})
        arm["count"] = arm.get("count", 0) + 1
        arm["total_reward"] = arm.get("total_reward", 0.0) + reward
        arm["avg_reward"] = arm["total_reward"] / arm["count"]
        bandit[key] = arm
        policy.bandit_state = bandit

        # Decay epsilon
        policy.epsilon = max(self.EPSILON_MIN, policy.epsilon * self.EPSILON_DECAY)
        policy.total_interactions += 1
        policy.last_updated = datetime.utcnow()

        await self.db.flush()

        logger.info("RL update: user=%s arm=%s reward=%.4f epsilon=%.4f",
                     user_id, key, reward, policy.epsilon)

        return {"arm": key, "reward": round(reward, 4), "epsilon": round(policy.epsilon, 4),
                "arm_avg_reward": round(arm["avg_reward"], 4), "total_interactions": policy.total_interactions}
