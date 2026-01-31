"""
Mentor Chat Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Schema for chat message input."""
    content: str
    session_id: Optional[str] = None


class SuggestionItem(BaseModel):
    """Suggested action after AI response."""
    icon: str
    title: str
    description: str
    action: str  # start_task, view_resource, update_skill, etc.
    action_data: Optional[Dict[str, Any]] = None


class ChatResponseMessage(BaseModel):
    """AI response message."""
    message: str
    suggestions: List[SuggestionItem]
    context_used: Dict[str, Any]


class ChatResponse(BaseModel):
    """Schema for chat response."""
    session_id: str
    response: ChatResponseMessage


class MessageItem(BaseModel):
    """Individual message in conversation."""
    role: str  # user or assistant
    content: str
    timestamp: datetime
    context_used: Optional[Dict[str, Any]] = None


class ChatSessionListResponse(BaseModel):
    """Schema for session list item."""
    session_id: str
    title: str
    last_message_preview: str
    message_count: int
    updated_at: datetime


class ChatSessionResponse(BaseModel):
    """Schema for full session with messages."""
    session_id: str
    user_id: str
    title: str
    messages: List[MessageItem]
    created_at: datetime
    updated_at: datetime
