"""
Skill Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SkillMasterResponse(BaseModel):
    """Schema for skill master response."""
    id: UUID
    skill_name: str
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    difficulty_level: int
    market_demand_score: float
    related_skills: Optional[List[str]]
    
    class Config:
        from_attributes = True


class UserSkillResponse(BaseModel):
    """Schema for user skill response."""
    id: UUID
    skill_id: UUID
    skill_name: str
    category: str
    proficiency_level: int
    target_proficiency: int
    practice_hours: float
    confidence_rating: int
    last_practiced: Optional[datetime]
    
    class Config:
        from_attributes = True


class SkillGapAnalysisRequest(BaseModel):
    """Schema for skill gap analysis request."""
    target_role: str


class SkillGap(BaseModel):
    """Schema for individual skill gap."""
    skill_name: str
    skill_id: Optional[UUID]
    category: str
    required_proficiency: int
    current_proficiency: int = 0
    gap_severity: str  # critical, high, medium, low
    estimated_learning_weeks: float
    importance: str  # required, preferred


class SkillGapAnalysisResponse(BaseModel):
    """Schema for skill gap analysis response."""
    target_role: str
    required_skills: List[SkillGap]
    current_skills: List[UserSkillResponse]
    missing_skills: List[SkillGap]
    skills_to_improve: List[SkillGap]
    strength_areas: List[str]
    overall_readiness: float  # 0-100
    estimated_time_to_ready: int  # weeks
    ai_insights: Dict[str, Any]
