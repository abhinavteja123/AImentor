"""
Bayesian Knowledge Tracing (BKT) — core algorithm + service layer.

Per-skill rows live in ``knowledge_states``. When the calling layer can map a
skill to one of the paper-aligned KCs (any course in ``COURSE_REGISTRY``), the
row is initialised with that course/KC's paper parameters from
``kc_mapping.get_bkt_params``. Otherwise the generic defaults from the model
definition are used.

BKT parameters per skill row:
  p_init  — prior probability the student already knows the skill
  p_learn — probability of learning on each attempt
  p_guess — probability of correct guess without knowing
  p_slip  — probability of error despite knowing
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....models.tutor import KnowledgeState
from ....models.skill import SkillMaster, UserSkill
from .bkt_tracker import MASTERY_THRESHOLD as PAPER_MASTERY_THRESHOLD
from .kc_mapping import (
    COURSE_REGISTRY,
    CourseSpec,
    get_anchor_skill_id,
    get_bkt_params,
    get_course,
)

logger = logging.getLogger(__name__)


def bkt_update(p_mastery: float, is_correct: bool,
               p_learn: float = 0.3, p_guess: float = 0.25, p_slip: float = 0.1) -> float:
    """Single BKT update step. Returns new P(mastery)."""
    if is_correct:
        num = p_mastery * (1.0 - p_slip)
        den = num + (1.0 - p_mastery) * p_guess
    else:
        num = p_mastery * p_slip
        den = num + (1.0 - p_mastery) * (1.0 - p_guess)
    p_k = num / den if den > 0 else p_mastery
    return max(0.001, min(0.999, p_k + (1.0 - p_k) * p_learn))


def predict_correct(p_mastery: float, p_guess: float = 0.25, p_slip: float = 0.1) -> float:
    return p_mastery * (1.0 - p_slip) + (1.0 - p_mastery) * p_guess


class BKTService:
    # Paper Section 5.2.3.
    MASTERY_THRESHOLD = PAPER_MASTERY_THRESHOLD  # 0.95

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_state(self, user_id: UUID, skill_id: UUID,
                                   kc_id: Optional[int] = None,
                                   course_key: Optional[str] = None) -> KnowledgeState:
        """
        Fetch or create a BKT state row.

        When both ``course_key`` and ``kc_id`` are supplied, the per-KC
        parameters from that course's ``BKT_PARAMS`` are written to the row
        on first creation. Existing rows are not retro-mutated.

        Backwards-compat: if only ``kc_id`` is given, defaults to AI
        Fundamentals to keep older callers working.
        """
        result = await self.db.execute(
            select(KnowledgeState).where(
                KnowledgeState.user_id == user_id, KnowledgeState.skill_id == skill_id))
        state = result.scalar_one_or_none()
        if state is None:
            params = None
            if kc_id is not None:
                resolved_course = course_key or "ai_fundamentals"
                params = get_bkt_params(resolved_course, kc_id)

            if params:
                p_init = float(params["p_l0"])
                p_learn = float(params["p_t"])
                p_guess = float(params["p_g"])
                p_slip = float(params["p_s"])
            else:
                # Off-curriculum row: keep prior tied to user's self-rated proficiency.
                p_init = 0.1
                us = (await self.db.execute(
                    select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
                )).scalar_one_or_none()
                if us and us.proficiency_level:
                    p_init = 0.1 + (us.proficiency_level - 1) * 0.15
                p_learn, p_guess, p_slip = 0.3, 0.25, 0.1

            state = KnowledgeState(
                user_id=user_id, skill_id=skill_id,
                p_mastery=p_init, p_init=p_init,
                p_learn=p_learn, p_guess=p_guess, p_slip=p_slip,
            )
            self.db.add(state)
            await self.db.flush()
        return state

    async def update_mastery(self, user_id: UUID, skill_id: UUID, is_correct: bool,
                              kc_id: Optional[int] = None,
                              course_key: Optional[str] = None) -> KnowledgeState:
        state = await self.get_or_create_state(user_id, skill_id,
                                                kc_id=kc_id, course_key=course_key)
        old = state.p_mastery
        state.p_mastery = bkt_update(state.p_mastery, is_correct, state.p_learn, state.p_guess, state.p_slip)
        state.attempts += 1
        if is_correct:
            state.correct_count += 1
            state.consecutive_correct += 1
            state.consecutive_incorrect = 0
        else:
            state.consecutive_incorrect += 1
            state.consecutive_correct = 0
        state.last_updated = datetime.utcnow()
        logger.info("BKT: user=%s skill=%s correct=%s mastery=%.3f->%.3f", user_id, skill_id, is_correct, old, state.p_mastery)
        await self.db.flush()
        return state

    async def get_all_states(self, user_id: UUID) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(KnowledgeState, SkillMaster.skill_name, SkillMaster.category)
            .join(SkillMaster, KnowledgeState.skill_id == SkillMaster.id)
            .where(KnowledgeState.user_id == user_id)
            .order_by(KnowledgeState.p_mastery.desc()))
        return [
            {"skill_id": str(s.skill_id), "skill_name": n, "category": c,
             "p_mastery": round(s.p_mastery, 4), "is_mastered": s.p_mastery >= self.MASTERY_THRESHOLD,
             "attempts": s.attempts, "correct_count": s.correct_count,
             "accuracy": round(s.correct_count / s.attempts, 3) if s.attempts else 0,
             "consecutive_correct": s.consecutive_correct,
             "last_updated": s.last_updated.isoformat() if s.last_updated else None}
            for s, n, c in result.all()]

    async def get_weakest_skills(self, user_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(KnowledgeState, SkillMaster.skill_name, SkillMaster.category)
            .join(SkillMaster, KnowledgeState.skill_id == SkillMaster.id)
            .where(KnowledgeState.user_id == user_id, KnowledgeState.p_mastery < self.MASTERY_THRESHOLD)
            .order_by(KnowledgeState.p_mastery.asc()).limit(limit))
        return [
            {"skill_id": str(s.skill_id), "skill_name": n, "category": c,
             "p_mastery": round(s.p_mastery, 4), "attempts": s.attempts,
             "predicted_correct": round(predict_correct(s.p_mastery, s.p_guess, s.p_slip), 3)}
            for s, n, c in result.all()]

    async def get_mastery_summary(self, user_id: UUID) -> Dict[str, Any]:
        states = await self.get_all_states(user_id)
        if not states:
            return {"total_skills_tracked": 0, "mastered_count": 0, "in_progress_count": 0,
                    "average_mastery": 0.0, "overall_readiness": 0.0}
        mastered = sum(1 for s in states if s["is_mastered"])
        avg = sum(s["p_mastery"] for s in states) / len(states)
        return {"total_skills_tracked": len(states), "mastered_count": mastered,
                "in_progress_count": len(states) - mastered, "average_mastery": round(avg, 4),
                "overall_readiness": round(mastered / len(states), 3)}

    # ── Multi-course KC layer (paper alignment) ────────────────

    async def get_kc_mastery_vector(self, user_id: UUID,
                                     course_key: str = "ai_fundamentals") -> List[float]:
        """
        Return the 5-KC mastery vector ``[P(L_1), …, P(L_5)]`` for one course.

        Used as PPO state input. Missing rows fall back to the KC's paper
        prior ``p_l0`` so cold-start users get a sensible vector. Rows are
        not auto-created — creation is deferred to ``update_mastery`` on
        first answer.
        """
        course = get_course(course_key)
        if course is None:
            # Unknown course — return the AI Fundamentals prior vector.
            course = get_course("ai_fundamentals")
            if course is None:
                return [0.0] * 5

        anchor_ids: Dict[int, UUID] = {}
        for kc_id in sorted(course.kcs.keys()):
            sid = await get_anchor_skill_id(self.db, course.course_key, kc_id)
            if sid is not None:
                anchor_ids[kc_id] = sid

        result = await self.db.execute(
            select(KnowledgeState.skill_id, KnowledgeState.p_mastery)
            .where(KnowledgeState.user_id == user_id,
                   KnowledgeState.skill_id.in_(list(anchor_ids.values()))))
        by_skill = {row[0]: float(row[1]) for row in result.all()}

        vector: List[float] = []
        for kc_id in sorted(course.kcs.keys()):
            sid = anchor_ids.get(kc_id)
            if sid is not None and sid in by_skill:
                vector.append(by_skill[sid])
            else:
                vector.append(float(course.kcs[kc_id].p_l0))
        return vector

    async def get_kc_mastery_breakdown(self, user_id: UUID,
                                        course_key: str = "ai_fundamentals") -> List[Dict[str, Any]]:
        """Per-KC mastery rows for one course's radar."""
        course = get_course(course_key)
        if course is None:
            return []
        return await self._breakdown_for_course(user_id, course)

    async def get_all_courses_mastery_breakdown(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Concatenate per-course breakdowns for every registered course.

        Each row carries ``course_key`` + ``course_name`` so the frontend can
        group by course and render one radar per course.
        """
        out: List[Dict[str, Any]] = []
        for course in COURSE_REGISTRY.values():
            out.extend(await self._breakdown_for_course(user_id, course))
        return out

    async def _breakdown_for_course(self, user_id: UUID,
                                     course: CourseSpec) -> List[Dict[str, Any]]:
        anchor_ids: Dict[int, UUID] = {}
        for kc_id in sorted(course.kcs.keys()):
            sid = await get_anchor_skill_id(self.db, course.course_key, kc_id)
            if sid is not None:
                anchor_ids[kc_id] = sid

        result = await self.db.execute(
            select(KnowledgeState)
            .where(KnowledgeState.user_id == user_id,
                   KnowledgeState.skill_id.in_(list(anchor_ids.values()))))
        by_skill = {s.skill_id: s for s in result.scalars().all()}

        out: List[Dict[str, Any]] = []
        for kc_id in sorted(course.kcs.keys()):
            spec = course.kcs[kc_id]
            sid = anchor_ids.get(kc_id)
            row = by_skill.get(sid) if sid is not None else None
            if row is not None:
                out.append({
                    "kc_id": kc_id, "kc_name": spec.name,
                    "course_key": course.course_key,
                    "course_name": course.display_name,
                    "p_mastery": round(float(row.p_mastery), 4),
                    "is_mastered": float(row.p_mastery) >= self.MASTERY_THRESHOLD,
                    "attempts": int(row.attempts or 0),
                })
            else:
                out.append({
                    "kc_id": kc_id, "kc_name": spec.name,
                    "course_key": course.course_key,
                    "course_name": course.display_name,
                    "p_mastery": float(spec.p_l0),
                    "is_mastered": False, "attempts": 0,
                })
        return out
