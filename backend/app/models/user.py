"""
User Model - Core user table
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database.postgres import Base


class User(Base):
    """User model for authentication and core user data."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    skills = relationship("UserSkill", back_populates="user")
    roadmaps = relationship("Roadmap", back_populates="user")
    progress_logs = relationship("ProgressLog", back_populates="user")
    resumes = relationship("Resume", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
