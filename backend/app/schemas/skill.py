"""
Skill Schemas - Complete schemas for skills management
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
    subcategory: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: int = 1
    market_demand_score: float = 0.5
    related_skills: Optional[List[str]] = None
    
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
    practice_hours: float = 0
    confidence_rating: int = 1
    last_practiced: Optional[datetime] = None
    notes: Optional[str] = None
    progress_percentage: float = 0
    
    class Config:
        from_attributes = True


class AddUserSkillRequest(BaseModel):
    """Schema for adding a user skill."""
    skill_id: Optional[UUID] = None
    skill_name: Optional[str] = None
    category: Optional[str] = "other"
    proficiency_level: int = Field(default=1, ge=1, le=5)
    target_proficiency: int = Field(default=3, ge=1, le=5)
    confidence_rating: int = Field(default=1, ge=1, le=5)
    notes: Optional[str] = None


class UpdateUserSkillRequest(BaseModel):
    """Schema for updating a user skill."""
    proficiency_level: Optional[int] = Field(None, ge=1, le=5)
    target_proficiency: Optional[int] = Field(None, ge=1, le=5)
    confidence_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None
    practice_hours: Optional[float] = Field(None, ge=0)


class BulkSkillInput(BaseModel):
    """Schema for bulk skill input."""
    skill_name: str
    category: Optional[str] = "other"
    proficiency_level: int = Field(default=1, ge=1, le=5)


class BulkAddSkillsRequest(BaseModel):
    """Schema for bulk adding skills."""
    skills: List[BulkSkillInput]


class SkillGapAnalysisRequest(BaseModel):
    """Schema for skill gap analysis request."""
    target_role: str


class SkillGap(BaseModel):
    """Schema for individual skill gap."""
    skill_name: str
    skill_id: Optional[UUID] = None
    category: str
    required_proficiency: int
    current_proficiency: int = 0
    gap_severity: str  # critical, high, medium, low
    estimated_learning_weeks: float
    importance: str  # required, preferred
    learning_resources: Optional[List[Dict[str, str]]] = None


class SkillGapAnalysisResponse(BaseModel):
    """Schema for skill gap analysis response."""
    target_role: str
    required_skills: List[Dict[str, Any]]
    current_skills: List[Dict[str, Any]]
    missing_skills: List[SkillGap]
    skills_to_improve: List[SkillGap]
    strength_areas: List[str]
    overall_readiness: float  # 0-100
    estimated_time_to_ready: int  # weeks
    ai_insights: Dict[str, Any]
    learning_path: Optional[List[Dict[str, Any]]] = None


class SkillRecommendation(BaseModel):
    """Schema for a single skill recommendation."""
    skill_name: str
    category: str
    reason: str
    priority: str  # high, medium, low
    market_demand: float
    learning_time_weeks: int
    related_to: Optional[List[str]] = None


class SkillRecommendationsResponse(BaseModel):
    """Schema for skill recommendations response."""
    recommended_skills: List[SkillRecommendation]
    based_on_goal: Optional[str] = None
    based_on_current_skills: List[str]
    market_insights: Dict[str, Any]
    personalized_message: str
