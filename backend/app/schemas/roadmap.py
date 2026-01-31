"""
Roadmap Schemas
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class RoadmapGenerateRequest(BaseModel):
    """Schema for roadmap generation request."""
    target_role: str
    duration_weeks: int = Field(ge=4, le=24, default=12)
    intensity: str = Field(pattern="^(low|medium|high)$", default="medium")


class RoadmapRegenerateRequest(BaseModel):
    """Schema for roadmap regeneration."""
    roadmap_id: UUID
    feedback: Optional[str] = None
    adjustments: Optional[Dict[str, Any]] = None


class ResourceItem(BaseModel):
    """Schema for learning resource."""
    title: str
    url: str
    type: str  # documentation, tutorial, video, practice, article


class RoadmapTaskResponse(BaseModel):
    """Schema for roadmap task response."""
    id: UUID
    week_number: int
    day_number: int
    order_in_day: int
    task_title: str
    task_description: Optional[str]
    task_type: str
    estimated_duration: int
    difficulty: int
    learning_objectives: Optional[List[str]]
    success_criteria: Optional[str]
    prerequisites: Optional[List[str]]
    resources: Optional[List[ResourceItem]]
    status: str
    completed_at: Optional[datetime]
    notes: Optional[str]
    is_favorite: bool
    
    class Config:
        from_attributes = True


class MilestoneItem(BaseModel):
    """Schema for milestone."""
    week_number: int
    title: str
    description: str
    skills_demonstrated: List[str]
    deliverable: str
    completed: bool = False


class RoadmapResponse(BaseModel):
    """Schema for roadmap response."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    target_role: Optional[str]
    total_weeks: int
    start_date: Optional[date]
    end_date: Optional[date]
    completion_percentage: float
    status: str
    milestones: Optional[List[MilestoneItem]]
    tasks: Optional[List[RoadmapTaskResponse]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DayTasks(BaseModel):
    """Tasks for a specific day."""
    day_number: int
    tasks: List[RoadmapTaskResponse]
    total_duration: int
    completed_count: int


class RoadmapWeekResponse(BaseModel):
    """Schema for week view."""
    week_number: int
    focus_area: str
    learning_objectives: List[str]
    days: List[DayTasks]
    total_tasks: int
    completed_tasks: int
    completion_percentage: float
