"""
Chat Session Model — replaces the MongoDB `chat_sessions` collection.

`messages` stores the full conversation as JSONB; `memory` stores any
mentor-memory/context the engine wants to persist across turns. One row
per session — typical chat threads stay under Postgres TOAST limits easily.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from ..database.postgres import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(255), nullable=True)
    messages = Column(JSONB, nullable=False, default=list)
    memory = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="chat_sessions")

    def __repr__(self):
        return f"<ChatSession {self.id} user={self.user_id}>"
