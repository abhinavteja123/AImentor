"""
Progress Models - Progress tracking and achievements
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database.postgres import Base


class ProgressLog(Base):
    """Individual progress log entries for tasks."""
    
    __tablename__ = "progress_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("roadmap_tasks.id"), nullable=True)
    
    # Time tracking
    time_spent = Column(Integer, default=0)  # minutes
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Ratings
    difficulty_rating = Column(Integer, nullable=True)  # 1-5
    confidence_rating = Column(Integer, nullable=True)  # 1-5
    enjoyment_rating = Column(Integer, nullable=True)  # 1-5
    
    # Notes
    notes = Column(Text, nullable=True)
    struggles = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="progress_logs")
    task = relationship("RoadmapTask", back_populates="progress_logs")
    
    def __repr__(self):
        return f"<ProgressLog {self.user_id} - {self.task_id}>"


class Achievement(Base):
    """Achievements and badges earned by users."""
    
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    achievement_type = Column(String(100), nullable=False)  # streak, skill, milestone, etc.
    achievement_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    
    # Achievement data
    achievement_data = Column(JSONB, nullable=True)
    
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Achievement {self.achievement_name}>"


class UserStreak(Base):
    """Track user learning streaks."""
    
    __tablename__ = "user_streaks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    
    # Weekly stats
    tasks_this_week = Column(Integer, default=0)
    time_this_week = Column(Integer, default=0)  # minutes
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserStreak {self.user_id}: {self.current_streak} days>"
