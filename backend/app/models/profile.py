"""
User Profile Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.postgres import Base


class UserProfile(Base):
    """User profile with onboarding data and preferences."""
    
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Career Goals
    goal_role = Column(String(255), nullable=True)
    experience_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    
    # Education
    current_education = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    
    # Learning Preferences
    time_per_day = Column(Integer, default=60)  # minutes
    preferred_learning_style = Column(String(50), nullable=True)  # visual, reading, hands-on, mixed
    
    # Profile Completion
    onboarding_completed = Column(DateTime, nullable=True)
    profile_completion_percentage = Column(Integer, default=0)
    
    # Bio
    bio = Column(Text, nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile {self.user_id}>"
