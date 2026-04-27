"""
AgentRAG Tutor Engine — the unified orchestrator.

Flow (Paper Section 4.2 — 3 phases per tutoring turn):
  1. RETRIEVAL PHASE:  CRAG evaluates chunk relevance → CORRECT/AMBIGUOUS/INCORRECT
  2. GENERATION PHASE: Socratic question + explanation grounded in retrieved context
  3. ADAPTATION PHASE: Student answer → 5-KC BKT update → PPO selects next difficulty

Multi-course routing (Path 1 — IEEE paper case studies):
  - The student topic is mapped to one of N courses x 5 KCs via keyword scan.
  - On a course/KC hit: BKT row uses that course's paper params; PPO is
    invoked with the course-local 5-KC mastery vector as state.
  - On a miss: tutoring still runs (CRAG + Socratic), but BKT/PPO are skipped
    so off-curriculum traffic does not pollute mastery data for either course.

Self-evaluation loop (agentic): generate → self-critique → refine if quality < 0.7
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.tutor import StudentResponse
from ...models.skill import SkillMaster
from ...models.user import User
from ...models.profile import UserProfile
from .llm_client import get_llm_client
from .rag.knowledge_base import KnowledgeBase
from .rag.crag_loop import CRAGLoop
from .bkt.bkt_service import BKTService
from .bkt.kc_mapping import (
    COURSE_REGISTRY,
    get_anchor_skill_id,
    get_course,
    kc_name as kc_name_lookup,
    lookup_kc_from_skill_name,
    resolve_kc_from_topic,
)
from .adaptive.difficulty_controller import DifficultyController

logger = logging.getLogger(__name__)


# ── AI-only category synonyms used as a tertiary fallback in _resolve_skill ──
# Maps a single AI-related keyword → (course_key, kc_id). Kept narrow to avoid
# misrouting; OS questions are caught earlier by resolve_kc_from_topic.
_AI_SYNONYM_TABLE: Dict[str, Tuple[str, int]] = {
    "search": ("ai_fundamentals", 2), "algorithm": ("ai_fundamentals", 2),
    "bfs": ("ai_fundamentals", 2), "dfs": ("ai_fundamentals", 2),
    "csp": ("ai_fundamentals", 2), "minimax": ("ai_fundamentals", 2),
    "logic": ("ai_fundamentals", 3), "bayes": ("ai_fundamentals", 3),
    "probability": ("ai_fundamentals", 3), "ontology": ("ai_fundamentals", 3),
    "planning": ("ai_fundamentals", 4), "strips": ("ai_fundamentals", 4), "pddl": ("ai_fundamentals", 4),
    "neural": ("ai_fundamentals", 5), "deep": ("ai_fundamentals", 5),
    "reinforcement": ("ai_fundamentals", 5), "machine": ("ai_fundamentals", 5),
    "learning": ("ai_fundamentals", 5),
    "agent": ("ai_fundamentals", 1), "rational": ("ai_fundamentals", 1), "peas": ("ai_fundamentals", 1),
}


class TutorEngine:
    """Agentic RAG tutor with multi-course 5-KC BKT and PPO/MAB difficulty control."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.kb = KnowledgeBase(db)
        self.crag = CRAGLoop(self.kb)
        self.bkt = BKTService(db)
        self.rl = DifficultyController(db)

    # ── Main tutoring flow ────────────────────────────────────

    async def ask(self, user_id: UUID, question: str,
                  topic: Optional[str] = None,
                  session_id: Optional[str] = None) -> Dict[str, Any]:
        """Student asks a question → agentic RAG response + follow-up."""
        context = await self._gather_context(user_id)

        # ── Phase 1: CRAG Retrieval (Paper Algorithm 1) ──
        crag_result = await self.crag.retrieve_and_correct(question, topic_filter=topic)
        retrieved_context = crag_result["context"]
        crag_action = crag_result["action"]
        crag_confidence = crag_result["confidence"]

        # ── Phase 2: Socratic Generation ──
        response = await self._generate_socratic(question, retrieved_context, context)

        # ── Agentic self-evaluation loop ──
        evaluation = await self._self_evaluate(question, response, [])
        if evaluation.get("quality_score", 1.0) < 0.7:
            response = await self._refine_response(question, response, evaluation.get("feedback", ""))

        # ── Phase 3: Adaptation — KC resolution + BKT vector + difficulty ──
        skill_id, kc_id, course_key = await self._resolve_skill(topic or question)
        course_name = get_course(course_key).display_name if course_key else None
        kc_name = kc_name_lookup(course_key, kc_id) if (course_key and kc_id) else None

        # Course-local mastery vector (defaults to AI Fundamentals when course unset).
        mastery_vector = await self.bkt.get_kc_mastery_vector(
            user_id, course_key=course_key or "ai_fundamentals")

        if kc_id is not None and skill_id is not None and course_key is not None:
            state = await self.bkt.get_or_create_state(
                user_id, skill_id, kc_id=kc_id, course_key=course_key)
            current_mastery = state.p_mastery
            action = await self.rl.select_action_with_ppo(
                user_id=user_id,
                mastery_vector=mastery_vector,
                session_step=0,
            )
        else:
            current_mastery = None
            action = await self.rl.select_action(user_id, current_mastery=0.5)

        follow_up = await self._generate_follow_up(
            topic=topic or question, difficulty=action["difficulty"],
            question_type=action["question_type"], context=context)

        return {
            "response": response,
            "follow_up_question": follow_up,
            "crag": {
                "action": crag_action,
                "confidence": crag_confidence,
                "chunks_used": crag_result["chunks_used"],
            },
            "evaluation": {"quality_score": evaluation.get("quality_score", 1.0),
                           "was_refined": evaluation.get("quality_score", 1.0) < 0.7},
            "difficulty_selection": action,
            "current_mastery": round(current_mastery, 4) if current_mastery is not None else None,
            "kc_id": kc_id,
            "kc_name": kc_name,
            "course_key": course_key,
            "course_name": course_name,
            "mastery_vector": [round(v, 4) for v in mastery_vector],
            "session_id": session_id or str(uuid4()),
        }

    async def answer(self, user_id: UUID, question_text: str, student_answer: str,
                     topic: Optional[str] = None, difficulty: int = 1,
                     question_type: str = "short_answer",
                     response_time_seconds: int = 0) -> Dict[str, Any]:
        """Student answers a follow-up → evaluate, update BKT, select next."""
        evaluation = await self._evaluate_answer(question_text, student_answer, topic)
        is_correct = evaluation.get("is_correct", False)
        partial = evaluation.get("partial_credit", 1.0 if is_correct else 0.0)

        skill_id, kc_id, course_key = await self._resolve_skill(topic or question_text)
        course_name = get_course(course_key).display_name if course_key else None
        kc_name = kc_name_lookup(course_key, kc_id) if (course_key and kc_id) else None

        mastery_before = None
        mastery_after = None
        bkt_data: Optional[Dict[str, Any]] = None

        if skill_id is not None and kc_id is not None and course_key is not None:
            state = await self.bkt.get_or_create_state(
                user_id, skill_id, kc_id=kc_id, course_key=course_key)
            mastery_before = state.p_mastery
            state = await self.bkt.update_mastery(
                user_id, skill_id, is_correct, kc_id=kc_id, course_key=course_key)
            mastery_after = state.p_mastery
            bkt_data = {
                "mastery_before": round(mastery_before, 4),
                "mastery_after": round(mastery_after, 4),
                "is_mastered": mastery_after >= self.bkt.MASTERY_THRESHOLD,
                "kc_id": kc_id,
                "course_key": course_key,
            }

            await self.rl.update_reward(
                user_id, difficulty, question_type,
                mastery_before, mastery_after, is_correct, response_time_seconds)

        # Persist response (skill_id may be NULL for off-curriculum questions).
        sr = StudentResponse(
            user_id=user_id, skill_id=skill_id,
            student_answer=student_answer, is_correct=is_correct,
            response_time_seconds=response_time_seconds,
            difficulty_at_time=difficulty,
            bkt_mastery_before=mastery_before,
            bkt_mastery_after=mastery_after,
            evaluation_feedback=evaluation.get("feedback", ""),
            partial_credit=partial,
        )
        self.db.add(sr)
        await self.db.commit()

        # Next question: PPO when on-curriculum, MAB otherwise.
        mastery_vector = await self.bkt.get_kc_mastery_vector(
            user_id, course_key=course_key or "ai_fundamentals")
        if skill_id is not None and kc_id is not None and course_key is not None:
            action = await self.rl.select_action_with_ppo(
                user_id=user_id, mastery_vector=mastery_vector, session_step=0)
        else:
            action = await self.rl.select_action(user_id, current_mastery=0.5)

        next_question = await self._generate_follow_up(
            topic=topic or question_text, difficulty=action["difficulty"],
            question_type=action["question_type"],
            context={"previous_correct": is_correct,
                     "previous_question": question_text})

        return {
            "evaluation": evaluation,
            "bkt": bkt_data,
            "next_question": next_question,
            "next_difficulty": action,
            "kc_id": kc_id,
            "kc_name": kc_name,
            "course_key": course_key,
            "course_name": course_name,
            "mastery_vector": [round(v, 4) for v in mastery_vector],
            "encouragement": await self._get_encouragement(is_correct, mastery_after or 0.0),
        }

    async def get_knowledge_state(self, user_id: UUID) -> Dict[str, Any]:
        """Full knowledge state — per-skill BKT + multi-course KC layer."""
        summary = await self.bkt.get_mastery_summary(user_id)
        states = await self.bkt.get_all_states(user_id)
        weak = await self.bkt.get_weakest_skills(user_id, limit=5)
        kc_breakdown = await self.bkt.get_all_courses_mastery_breakdown(user_id)
        return {
            "summary": summary,
            "skills": states,
            "weakest_skills": weak,
            "kc_mastery": kc_breakdown,
        }

    async def get_next_question(self, user_id: UUID,
                                topic: Optional[str] = None) -> Dict[str, Any]:
        """RL-selected next question for the student."""
        if topic:
            skill_id, kc_id, course_key = await self._resolve_skill(topic)
        else:
            skill_id, kc_id, course_key = (None, None, None)

        course_name = get_course(course_key).display_name if course_key else None
        kc_name = kc_name_lookup(course_key, kc_id) if (course_key and kc_id) else None
        mastery_vector = await self.bkt.get_kc_mastery_vector(
            user_id, course_key=course_key or "ai_fundamentals")

        current_mastery = None
        if skill_id is not None and kc_id is not None and course_key is not None:
            state = await self.bkt.get_or_create_state(
                user_id, skill_id, kc_id=kc_id, course_key=course_key)
            current_mastery = state.p_mastery
            action = await self.rl.select_action_with_ppo(
                user_id=user_id, mastery_vector=mastery_vector, session_step=0)
        else:
            action = await self.rl.select_action(user_id, current_mastery=0.5)

        question = await self._generate_follow_up(
            topic=topic or "general programming", difficulty=action["difficulty"],
            question_type=action["question_type"], context={})
        return {
            "question": question,
            "difficulty": action,
            "current_mastery": round(current_mastery, 4) if current_mastery is not None else None,
            "kc_id": kc_id,
            "kc_name": kc_name,
            "course_key": course_key,
            "course_name": course_name,
            "mastery_vector": [round(v, 4) for v in mastery_vector],
        }

    # ── Private helpers ───────────────────────────────────────

    async def _gather_context(self, user_id: UUID) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {}
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user:
            ctx["name"] = user.full_name.split()[0] if user.full_name else "there"
        profile = (await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id))).scalar_one_or_none()
        if profile:
            ctx["goal_role"] = profile.goal_role
            ctx["experience_level"] = profile.experience_level
        return ctx

    async def _generate_socratic(self, question: str, retrieved_context: str,
                                   context: Dict) -> str:
        """Socratic generation — Paper Section 5.1.3."""
        name = context.get("name", "there")
        goal = context.get("goal_role", "their career goals")

        system = f"""You are a Socratic AI tutor helping {name} learn skills for becoming a {goal}.
Your teaching style: NEVER give the answer directly. Instead:
1. Acknowledge the student's question
2. Provide a clear, concise explanation grounded in the context below
3. Use real examples and analogies to make concepts concrete
4. Ask ONE guiding follow-up question that helps the student think deeper

CONTEXT (retrieved from knowledge base — use this to ground your response):
{retrieved_context if retrieved_context else 'No specific materials found — use your expertise.'}"""

        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": question}]
        try:
            return await self.llm.chat_completion(messages, temperature=0.6, max_tokens=2000)
        except Exception as e:
            logger.error("Socratic generation error: %s", e)
            return f"Great question! Let me help you think through this: {question}"

    async def _self_evaluate(self, question: str, response: str,
                              docs: List[Dict]) -> Dict[str, Any]:
        prompt = f"""Evaluate this tutoring response for quality.

Student question: {question}
Tutor response: {response[:1000]}

Rate on a scale of 0.0-1.0 for:
1. Accuracy (factually correct?)
2. Clarity (easy to understand?)
3. Completeness (covers the question?)
4. Engagement (encouraging and interactive?)

Return JSON: {{"quality_score": 0.0-1.0, "feedback": "brief improvement suggestion"}}"""

        try:
            result = await self.llm.generate_json(
                "You are a teaching quality evaluator. Return only JSON.", prompt)
            score = float(result.get("quality_score", 0.8))
            return {"quality_score": min(1.0, max(0.0, score)),
                    "feedback": result.get("feedback", "")}
        except Exception:
            return {"quality_score": 0.85, "feedback": ""}

    async def _refine_response(self, question: str, original: str, feedback: str) -> str:
        prompt = f"""Improve this tutoring response based on feedback.

Original question: {question}
Original response: {original[:1000]}
Feedback: {feedback}

Provide an improved response that addresses the feedback."""

        try:
            return await self.llm.generate_completion(
                "You are an expert tutor refining your explanation.", prompt,
                temperature=0.5, max_tokens=2000)
        except Exception:
            return original

    async def _generate_follow_up(self, topic: str, difficulty: int,
                                   question_type: str, context: Dict) -> Dict[str, Any]:
        diff_label = {1: "very easy", 2: "easy", 3: "medium", 4: "hard", 5: "expert"}
        prev_q = context.get("previous_question", "")
        avoid_clause = ""
        if prev_q:
            avoid_clause = f"""\n\nIMPORTANT: Do NOT repeat this previous question: \"{prev_q}\"
Ask about a DIFFERENT aspect or sub-topic. Each question must be unique."""

        prompt = f"""Generate a {diff_label.get(difficulty, 'medium')} {question_type} question about "{topic}".{avoid_clause}

Return JSON:
{{"question": "the question text", "correct_answer": "the answer",
  "hints": ["hint1", "hint2"], "explanation": "why this is correct"}}
{"Include 3 wrong options in a 'distractors' array." if question_type == "multiple_choice" else ""}"""

        try:
            result = await self.llm.generate_json(
                "You are a question generator for adaptive learning. Always generate a NEW, unique question. Return only JSON.", prompt)
            result["difficulty"] = difficulty
            result["question_type"] = question_type
            result["topic"] = topic
            return result
        except Exception as e:
            logger.error("Question generation error: %s", e)
            return {"question": f"Explain the key concept of {topic} in your own words.",
                    "correct_answer": "", "difficulty": difficulty,
                    "question_type": "open_ended", "topic": topic,
                    "hints": [], "explanation": ""}

    async def _evaluate_answer(self, question: str, answer: str,
                                topic: Optional[str]) -> Dict[str, Any]:
        prompt = f"""Evaluate this student's answer.

Question: {question}
Student's answer: {answer}
Topic: {topic or 'general'}

Return JSON:
{{"is_correct": true/false, "partial_credit": 0.0-1.0,
  "feedback": "encouraging explanation of what's right/wrong",
  "correct_answer": "the correct answer if student was wrong"}}"""

        try:
            return await self.llm.generate_json(
                "You are a fair, encouraging tutor evaluating student answers. Return only JSON.", prompt)
        except Exception:
            return {"is_correct": False, "partial_credit": 0.0,
                    "feedback": "I couldn't evaluate that properly. Let's try another question!",
                    "correct_answer": ""}

    async def _resolve_skill(self, topic: Optional[str]) -> Tuple[
            Optional[UUID], Optional[int], Optional[str]]:
        """
        Resolve a topic to ``(skill_id, kc_id, course_key)``.

        Order:
          1. KC keyword scan across all courses — best match wins (returns
             ``(course_key, kc_id)`` or None).
          2. Direct ilike on existing SkillMaster names — preserves short-form
             skill queries; resolves the matched skill back to a course/KC if
             it's an anchor row.
          3. Word-overlap inside any registered course's category.
          4. Narrow AI-only synonym table for legacy terms (search/logic/etc).
          5. ``(None, None, None)`` — off-curriculum. Caller skips BKT/PPO.

        Bug fix (#1): no first-skill-in-DB fallback. Off-curriculum questions
        keep working through CRAG + Socratic but never pollute mastery rows.
        """
        if not topic:
            return None, None, None

        clean = topic.strip()

        # 1. KC keyword scan — multi-course paper-aligned routing.
        kc_hit = resolve_kc_from_topic(clean)
        if kc_hit is not None:
            course_key, kc_id = kc_hit
            anchor = await get_anchor_skill_id(self.db, course_key, kc_id)
            if anchor is not None:
                logger.debug("Skill resolved via KC keyword: course=%s kc=%d", course_key, kc_id)
                return anchor, kc_id, course_key

        # 2. Direct ilike on SkillMaster.
        result = await self.db.execute(
            select(SkillMaster).where(
                SkillMaster.skill_name.ilike(f"%{clean[:40]}%")).limit(1))
        skill = result.scalar_one_or_none()
        if skill:
            kc_match = lookup_kc_from_skill_name(skill.skill_name, category=skill.category)
            if kc_match:
                return skill.id, kc_match[1], kc_match[0]
            return skill.id, None, None

        # 3. Word-overlap restricted to any registered course's anchor pool.
        query_words = {w.lower() for w in clean.split() if len(w) > 2}
        stop_words = {"what", "how", "does", "the", "for", "and", "with", "about",
                      "explain", "describe", "define", "tell", "can", "you", "are",
                      "is", "in", "of", "to", "a", "an", "this", "that", "which"}
        query_words -= stop_words

        if query_words:
            anchor_categories = [c.db_category for c in COURSE_REGISTRY.values()]
            anchor_skills = (await self.db.execute(
                select(SkillMaster).where(SkillMaster.category.in_(anchor_categories))
            )).scalars().all()
            best_skill, best_score = None, 0
            for s in anchor_skills:
                skill_words = {w.lower() for w in s.skill_name.split() if len(w) > 2}
                cat_words: set[str] = set()
                if s.subcategory:
                    cat_words.update(w.lower() for w in s.subcategory.split("_") if len(w) > 2)
                overlap = len(query_words & (skill_words | cat_words))
                if overlap > best_score:
                    best_score = overlap
                    best_skill = s
            if best_skill and best_score > 0:
                kc_match = lookup_kc_from_skill_name(best_skill.skill_name,
                                                     category=best_skill.category)
                if kc_match:
                    course_key, kc_id = kc_match
                    logger.info("Skill resolved by overlap: '%s' -> '%s' (course=%s)",
                                 clean[:50], best_skill.skill_name, course_key)
                    return best_skill.id, kc_id, course_key

        # 4. Narrow AI-only synonym table for legacy keywords.
        for word in query_words:
            hit = _AI_SYNONYM_TABLE.get(word)
            if hit is not None:
                course_key, kc_id = hit
                anchor = await get_anchor_skill_id(self.db, course_key, kc_id)
                if anchor is not None:
                    logger.info("Skill resolved via synonym '%s' -> %s/KC%d", word, course_key, kc_id)
                    return anchor, kc_id, course_key

        # 5. Off-curriculum.
        return None, None, None

    async def _get_encouragement(self, is_correct: bool, mastery: float) -> str:
        if is_correct and mastery >= 0.8:
            return "🌟 Outstanding! You've mastered this concept!"
        elif is_correct and mastery >= 0.5:
            return "✅ Great job! You're making solid progress!"
        elif is_correct:
            return "👍 Correct! Keep practicing to strengthen this skill."
        elif mastery >= 0.5:
            return "💪 Not quite, but you're close! Review the explanation and try again."
        else:
            return "📚 That's okay! Learning takes time. Let's look at this concept together."
