"""
Mentor Chat API Endpoints
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.schemas.mentor import (
    ChatMessage,
    ChatResponse,
    ChatSessionResponse,
    ChatSessionListResponse
)
from app.services.ai.chat_engine import MentorChatEngine
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to AI mentor.
    
    Returns:
    - AI response
    - Suggested actions
    - Context used
    """
    chat_engine = MentorChatEngine(db)
    response = await chat_engine.chat(
        user_id=current_user.id,
        message=message.content,
        session_id=message.session_id
    )
    return response


@router.get("/sessions", response_model=List[ChatSessionListResponse])
async def get_chat_sessions(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of chat sessions.
    """
    chat_engine = MentorChatEngine(db)
    sessions = await chat_engine.get_sessions(
        user_id=current_user.id,
        limit=limit
    )
    return sessions


@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full conversation history for a session.
    """
    chat_engine = MentorChatEngine(db)
    session = await chat_engine.get_session(
        session_id=session_id,
        user_id=current_user.id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat session.
    """
    chat_engine = MentorChatEngine(db)
    await chat_engine.delete_session(
        session_id=session_id,
        user_id=current_user.id
    )
    return {"message": "Session deleted"}
