"""
Progress Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class TaskCompleteRequest(BaseModel):
    """Schema for completing a task."""
    task_id: UUID
    time_spent: int = Field(ge=1, description="Time spent in minutes")
    difficulty_rating: Optional[int] = Field(ge=1, le=5, default=None)
    confidence_rating: Optional[int] = Field(ge=1, le=5, default=None)
    notes: Optional[str] = None


class TaskSkipRequest(BaseModel):
    """Schema for skipping a task."""
    task_id: UUID
    reason: str


class ProgressLogResponse(BaseModel):
    """Schema for progress log response."""
    id: UUID
    user_id: UUID
    task_id: Optional[UUID]
    time_spent: int
    difficulty_rating: Optional[int]
    confidence_rating: Optional[int]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class StreakInfo(BaseModel):
    """Streak information."""
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[datetime]


class WeeklyStats(BaseModel):
    """Weekly statistics."""
    tasks_completed: int
    time_spent: int
    skills_practiced: int
    average_difficulty: float
    average_confidence: float


class AchievementResponse(BaseModel):
    """Achievement response."""
    id: UUID
    achievement_type: str
    achievement_name: str
    description: Optional[str]
    icon: Optional[str]
    earned_at: datetime
    
    class Config:
        from_attributes = True


class ProgressStatsResponse(BaseModel):
    """Schema for progress statistics."""
    total_learning_time: int  # minutes
    total_tasks_completed: int
    total_tasks: int
    skills_acquired: int
    current_roadmap_progress: float
    streak: StreakInfo
    weekly_stats: WeeklyStats
    recent_achievements: List[AchievementResponse]
    skill_growth: List[Dict[str, Any]]


class ActivityDay(BaseModel):
    """Activity for a single day."""
    date: str
    tasks_completed: int
    time_spent: int
    activity_level: int  # 0-4 for heatmap
