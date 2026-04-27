"""
Mentor Chat Engine — Context-aware AI chat.

History is stored in the Postgres `chat_sessions` table (one row per session,
messages in a JSONB column). Previously this lived in MongoDB.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.chat_session import ChatSession
from ...models.profile import UserProfile
from ...models.progress import UserStreak
from ...models.roadmap import Roadmap
from ...models.skill import UserSkill
from ...models.user import User
from .llm_client import get_llm_client

logger = logging.getLogger(__name__)


def _parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


class MentorChatEngine:
    """Context-aware AI mentor chat engine backed by Postgres."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()

    async def chat(
        self,
        user_id: UUID,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a chat message and generate a response."""
        if not session_id:
            session_id = str(uuid4())

        context = await self._gather_user_context(user_id)
        history = await self._get_chat_history(session_id, limit=10)
        intent = await self._analyze_intent(message, context)
        response = await self._generate_response(
            message=message, history=history, context=context, intent=intent
        )
        suggestions = await self._generate_suggestions(context, intent)

        await self._save_conversation(
            session_id=session_id,
            user_id=user_id,
            user_message=message,
            assistant_message=response,
            context_used={"intent": intent},
        )

        return {
            "session_id": session_id,
            "response": {
                "message": response,
                "suggestions": suggestions,
                "context_used": {
                    "user_name": context.get("full_name", ""),
                    "intent": intent,
                },
            },
        }

    # ------------------------------------------------------------------
    # Context gathering (unchanged from previous Mongo-backed version)
    # ------------------------------------------------------------------

    async def _gather_user_context(self, user_id: UUID) -> Dict[str, Any]:
        context: Dict[str, Any] = {}

        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user:
            context["full_name"] = user.full_name
            context["email"] = user.email

        profile = (
            await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        ).scalar_one_or_none()
        if profile:
            context["goal_role"] = profile.goal_role
            context["experience_level"] = profile.experience_level
            context["learning_style"] = profile.preferred_learning_style
            context["daily_time"] = profile.time_per_day

        roadmap = (
            await self.db.execute(
                select(Roadmap)
                .where(Roadmap.user_id == user_id, Roadmap.status == "active")
                .order_by(Roadmap.created_at.desc())
            )
        ).scalar_one_or_none()
        if roadmap:
            context["roadmap_title"] = roadmap.title
            context["roadmap_progress"] = roadmap.completion_percentage
            context["roadmap_weeks"] = roadmap.total_weeks

        streak = (
            await self.db.execute(select(UserStreak).where(UserStreak.user_id == user_id))
        ).scalar_one_or_none()
        if streak:
            context["current_streak"] = streak.current_streak
            context["tasks_this_week"] = streak.tasks_this_week

        skills = (
            await self.db.execute(select(UserSkill).where(UserSkill.user_id == user_id))
        ).scalars().all()
        context["skills_count"] = len(skills)

        return context

    async def _analyze_intent(self, message: str, context: Dict[str, Any]) -> str:
        m = message.lower()
        if any(w in m for w in ("help", "stuck", "don't understand", "confused")):
            return "asking_for_help"
        if any(w in m for w in ("explain", "what is", "how does", "why")):
            return "requesting_explanation"
        if any(w in m for w in ("motivation", "tired", "giving up", "hard")):
            return "seeking_motivation"
        if any(w in m for w in ("struggling", "difficult", "can't")):
            return "reporting_struggle"
        if any(w in m for w in ("next", "should i", "what now", "today")):
            return "asking_next_steps"
        if any(w in m for w in ("resource", "learn", "tutorial", "course")):
            return "requesting_resources"
        if any(w in m for w in ("progress", "how am i", "doing")):
            return "asking_progress"
        return "general_chat"

    async def _generate_response(
        self,
        message: str,
        history: List[Dict],
        context: Dict[str, Any],
        intent: str,
    ) -> str:
        name = context.get("full_name", "").split()[0] if context.get("full_name") else "there"
        goal = context.get("goal_role", "your career goals")
        progress = context.get("roadmap_progress", 0) or 0
        streak = context.get("current_streak", 0) or 0

        system_prompt = f"""You are {name}'s personal AI career mentor.

About your mentee:
- Goal: Become a {goal}
- Experience: {context.get("experience_level", "beginner")}
- Progress: {progress:.0f}% through their roadmap
- Streak: {streak} days
- Tasks this week: {context.get("tasks_this_week", 0)}

Your role:
- Supportive, knowledgeable advisor
- Know their entire journey
- Give specific, actionable guidance
- Balance encouragement with honesty
- Celebrate progress, empathize with struggles

Communication style:
- Warm and approachable
- Use their name: {name}
- Reference their specific journey
- Conversational, not robotic
- Be enthusiastic but genuine

Current intent: {intent}"""

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for h in history[-5:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        try:
            return await self.llm.chat_completion(messages, temperature=0.8)
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return (
                f"Hi {name}! I'm here to help you on your journey to becoming a {goal}. "
                "What would you like to discuss?"
            )

    async def _generate_suggestions(
        self, context: Dict[str, Any], intent: str
    ) -> List[Dict[str, Any]]:
        suggestions: List[Dict[str, Any]] = []
        if intent in ("asking_next_steps", "general_chat"):
            suggestions.append(
                {
                    "icon": "▶️",
                    "title": "Start Next Task",
                    "description": "Continue your learning journey",
                    "action": "start_task",
                    "action_data": None,
                }
            )
        if intent == "requesting_resources":
            suggestions.append(
                {
                    "icon": "📚",
                    "title": "View Resources",
                    "description": "Browse learning materials",
                    "action": "view_resources",
                    "action_data": None,
                }
            )
        if intent == "asking_progress":
            suggestions.append(
                {
                    "icon": "📊",
                    "title": "View Progress",
                    "description": "Check your detailed stats",
                    "action": "view_progress",
                    "action_data": None,
                }
            )
        suggestions.append(
            {
                "icon": "🎯",
                "title": "View Roadmap",
                "description": "See your learning path",
                "action": "view_roadmap",
                "action_data": None,
            }
        )
        return suggestions[:3]

    # ------------------------------------------------------------------
    # Persistence — Postgres via ChatSession (was MongoDB)
    # ------------------------------------------------------------------

    async def _get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        sid = _parse_uuid(session_id)
        if sid is None:
            return []
        session = await self.db.get(ChatSession, sid)
        if not session or not session.messages:
            return []
        return list(session.messages[-limit:])

    async def _save_conversation(
        self,
        session_id: str,
        user_id: UUID,
        user_message: str,
        assistant_message: str,
        context_used: Dict,
    ) -> None:
        sid = _parse_uuid(session_id)
        if sid is None:
            logger.warning("save: invalid session_id %r, skipping", session_id)
            return

        now = datetime.utcnow()
        new_msgs = [
            {
                "role": "user",
                "content": user_message,
                "timestamp": now.isoformat(),
            },
            {
                "role": "assistant",
                "content": assistant_message,
                "timestamp": now.isoformat(),
                "context_used": context_used,
            },
        ]

        try:
            session = await self.db.get(ChatSession, sid)
            if session is None:
                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                session = ChatSession(
                    id=sid,
                    user_id=user_id,
                    title=title,
                    messages=new_msgs,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(session)
            else:
                session.messages = list(session.messages or []) + new_msgs
                session.updated_at = now
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            await self.db.rollback()

    async def get_sessions(self, user_id: UUID, limit: int = 20) -> List[Dict]:
        try:
            result = await self.db.execute(
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
            )
            sessions = result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return []

        out: List[Dict] = []
        for s in sessions:
            messages = s.messages or []
            last_content = messages[-1].get("content", "") if messages else ""
            out.append(
                {
                    "session_id": str(s.id),
                    "title": s.title or "Chat",
                    "last_message_preview": last_content[:100],
                    "message_count": len(messages),
                    "updated_at": s.updated_at,
                }
            )
        return out

    async def get_session(self, session_id: str, user_id: UUID) -> Optional[Dict]:
        sid = _parse_uuid(session_id)
        if sid is None:
            return None
        try:
            session = await self.db.get(ChatSession, sid)
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
        if session is None or session.user_id != user_id:
            return None
        return {
            "session_id": str(session.id),
            "user_id": str(session.user_id),
            "title": session.title or "Chat",
            "messages": session.messages or [],
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    async def delete_session(self, session_id: str, user_id: UUID) -> None:
        sid = _parse_uuid(session_id)
        if sid is None:
            return
        try:
            session = await self.db.get(ChatSession, sid)
            if session is not None and session.user_id == user_id:
                await self.db.delete(session)
                await self.db.commit()
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            await self.db.rollback()
