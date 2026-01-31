"""
Roadmap Models - Learning roadmaps and tasks
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database.postgres import Base


class Roadmap(Base):
    """Learning roadmap generated for a user."""
    
    __tablename__ = "roadmaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_role = Column(String(255), nullable=True)
    
    total_weeks = Column(Integer, default=12)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    completion_percentage = Column(Float, default=0)
    status = Column(String(50), default="active")  # active, paused, completed, abandoned
    
    # Milestones
    milestones = Column(JSONB, nullable=True)
    
    # AI generation metadata
    generation_params = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="roadmaps")
    tasks = relationship("RoadmapTask", back_populates="roadmap", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Roadmap {self.title}>"


class RoadmapTask(Base):
    """Individual tasks within a roadmap."""
    
    __tablename__ = "roadmap_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id"), nullable=False)
    
    week_number = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=False)  # 1-7
    order_in_day = Column(Integer, default=1)
    
    task_title = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=True)
    task_type = Column(String(50), default="reading")  # reading, coding, project, video, quiz
    
    estimated_duration = Column(Integer, default=60)  # minutes
    difficulty = Column(Integer, default=1)  # 1-5
    
    # Learning objectives
    learning_objectives = Column(ARRAY(String), nullable=True)
    success_criteria = Column(Text, nullable=True)
    prerequisites = Column(ARRAY(String), nullable=True)
    
    # Resources
    resources = Column(JSONB, nullable=True)  # [{"title": ..., "url": ..., "type": ...}]
    
    # Status
    status = Column(String(50), default="pending")  # pending, in_progress, completed, skipped
    completed_at = Column(DateTime, nullable=True)
    skipped_reason = Column(String(255), nullable=True)
    
    # User notes
    notes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roadmap = relationship("Roadmap", back_populates="tasks")
    progress_logs = relationship("ProgressLog", back_populates="task")
    
    def __repr__(self):
        return f"<RoadmapTask Week{self.week_number} Day{self.day_number}: {self.task_title}>"
