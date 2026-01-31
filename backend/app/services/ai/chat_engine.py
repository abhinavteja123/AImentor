"""
Mentor Chat Engine - Context-aware AI chat
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.profile import UserProfile
from app.models.roadmap import Roadmap
from app.models.skill import UserSkill
from app.models.progress import UserStreak
from app.database.mongodb import get_chat_sessions_collection
from app.services.ai.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class MentorChatEngine:
    """Context-aware AI mentor chat engine."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
    
    async def chat(
        self,
        user_id: UUID,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate a response.
        """
        # Get or create session
        if not session_id:
            session_id = str(uuid4())
        
        # Gather user context
        context = await self._gather_user_context(user_id)
        
        # Get chat history
        history = await self._get_chat_history(session_id, limit=10)
        
        # Analyze intent
        intent = await self._analyze_intent(message, context)
        
        # Generate response
        response = await self._generate_response(
            message=message,
            history=history,
            context=context,
            intent=intent
        )
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(context, intent)
        
        # Save conversation
        await self._save_conversation(
            session_id=session_id,
            user_id=str(user_id),
            user_message=message,
            assistant_message=response,
            context_used={"intent": intent}
        )
        
        return {
            "session_id": session_id,
            "response": {
                "message": response,
                "suggestions": suggestions,
                "context_used": {
                    "user_name": context.get("full_name", ""),
                    "intent": intent
                }
            }
        }
    
    async def _gather_user_context(self, user_id: UUID) -> Dict[str, Any]:
        """Gather comprehensive user context."""
        context = {}
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            context["full_name"] = user.full_name
            context["email"] = user.email
        
        # Get profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            context["goal_role"] = profile.goal_role
            context["experience_level"] = profile.experience_level
            context["learning_style"] = profile.preferred_learning_style
            context["daily_time"] = profile.time_per_day
        
        # Get current roadmap
        result = await self.db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id, Roadmap.status == "active")
            .order_by(Roadmap.created_at.desc())
        )
        roadmap = result.scalar_one_or_none()
        if roadmap:
            context["roadmap_title"] = roadmap.title
            context["roadmap_progress"] = roadmap.completion_percentage
            context["roadmap_weeks"] = roadmap.total_weeks
        
        # Get streak
        result = await self.db.execute(
            select(UserStreak).where(UserStreak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        if streak:
            context["current_streak"] = streak.current_streak
            context["tasks_this_week"] = streak.tasks_this_week
        
        # Get skill count
        result = await self.db.execute(
            select(UserSkill).where(UserSkill.user_id == user_id)
        )
        skills = result.scalars().all()
        context["skills_count"] = len(skills)
        
        return context
    
    async def _analyze_intent(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> str:
        """Analyze user message intent."""
        message_lower = message.lower()
        
        # Simple keyword-based intent detection
        if any(word in message_lower for word in ["help", "stuck", "don't understand", "confused"]):
            return "asking_for_help"
        elif any(word in message_lower for word in ["explain", "what is", "how does", "why"]):
            return "requesting_explanation"
        elif any(word in message_lower for word in ["motivation", "tired", "giving up", "hard"]):
            return "seeking_motivation"
        elif any(word in message_lower for word in ["struggling", "difficult", "can't"]):
            return "reporting_struggle"
        elif any(word in message_lower for word in ["next", "should i", "what now", "today"]):
            return "asking_next_steps"
        elif any(word in message_lower for word in ["resource", "learn", "tutorial", "course"]):
            return "requesting_resources"
        elif any(word in message_lower for word in ["progress", "how am i", "doing"]):
            return "asking_progress"
        else:
            return "general_chat"
    
    async def _generate_response(
        self,
        message: str,
        history: List[Dict],
        context: Dict[str, Any],
        intent: str
    ) -> str:
        """Generate AI response."""
        name = context.get("full_name", "").split()[0] if context.get("full_name") else "there"
        goal = context.get("goal_role", "your career goals")
        progress = context.get("roadmap_progress", 0)
        streak = context.get("current_streak", 0)
        
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

        # Build messages with history
        messages = [{"role": "system", "content": system_prompt}]
        
        for h in history[-5:]:  # Last 5 messages
            messages.append({
                "role": h["role"],
                "content": h["content"]
            })
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.llm.chat_completion(messages, temperature=0.8)
            return response
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Hi {name}! I'm here to help you on your journey to becoming a {goal}. What would you like to discuss?"
    
    async def _generate_suggestions(
        self, 
        context: Dict[str, Any],
        intent: str
    ) -> List[Dict[str, Any]]:
        """Generate contextual suggestions."""
        suggestions = []
        
        if intent == "asking_next_steps" or intent == "general_chat":
            suggestions.append({
                "icon": "▶️",
                "title": "Start Next Task",
                "description": "Continue your learning journey",
                "action": "start_task",
                "action_data": None
            })
        
        if intent == "requesting_resources":
            suggestions.append({
                "icon": "📚",
                "title": "View Resources",
                "description": "Browse learning materials",
                "action": "view_resources",
                "action_data": None
            })
        
        if intent == "asking_progress":
            suggestions.append({
                "icon": "📊",
                "title": "View Progress",
                "description": "Check your detailed stats",
                "action": "view_progress",
                "action_data": None
            })
        
        suggestions.append({
            "icon": "🎯",
            "title": "View Roadmap",
            "description": "See your learning path",
            "action": "view_roadmap",
            "action_data": None
        })
        
        return suggestions[:3]
    
    async def _get_chat_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Get chat history from MongoDB."""
        try:
            collection = get_chat_sessions_collection()
            session = await collection.find_one({"session_id": session_id})
            
            if session and "messages" in session:
                return session["messages"][-limit:]
            return []
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def _save_conversation(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
        context_used: Dict
    ):
        """Save conversation to MongoDB."""
        try:
            collection = get_chat_sessions_collection()
            
            messages = [
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow()
                },
                {
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": datetime.utcnow(),
                    "context_used": context_used
                }
            ]
            
            await collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "messages": {"$each": messages}
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow(),
                        "title": user_message[:50] + "..." if len(user_message) > 50 else user_message
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    async def get_sessions(
        self, 
        user_id: UUID, 
        limit: int = 20
    ) -> List[Dict]:
        """Get list of chat sessions."""
        try:
            collection = get_chat_sessions_collection()
            
            cursor = collection.find(
                {"user_id": str(user_id)}
            ).sort("updated_at", -1).limit(limit)
            
            sessions = []
            async for session in cursor:
                sessions.append({
                    "session_id": session["session_id"],
                    "title": session.get("title", "Chat"),
                    "last_message_preview": session.get("messages", [{}])[-1].get("content", "")[:100] if session.get("messages") else "",
                    "message_count": len(session.get("messages", [])),
                    "updated_at": session.get("updated_at", datetime.utcnow())
                })
            
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return []
    
    async def get_session(
        self, 
        session_id: str, 
        user_id: UUID
    ) -> Optional[Dict]:
        """Get full session with messages."""
        try:
            collection = get_chat_sessions_collection()
            
            session = await collection.find_one({
                "session_id": session_id,
                "user_id": str(user_id)
            })
            
            if session:
                return {
                    "session_id": session["session_id"],
                    "user_id": session["user_id"],
                    "title": session.get("title", "Chat"),
                    "messages": session.get("messages", []),
                    "created_at": session.get("created_at", datetime.utcnow()),
                    "updated_at": session.get("updated_at", datetime.utcnow())
                }
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def delete_session(self, session_id: str, user_id: UUID):
        """Delete a chat session."""
        try:
            collection = get_chat_sessions_collection()
            await collection.delete_one({
                "session_id": session_id,
                "user_id": str(user_id)
            })
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
