"""
Profile Schemas for Onboarding
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    """Skill input for onboarding."""
    skill_name: str
    proficiency: int = Field(ge=1, le=5, default=1)


class OnboardingData(BaseModel):
    """Schema for onboarding data."""
    # Step 1: Goal Setting
    goal_role: str = Field(..., min_length=2, max_length=255, description="Target career role (required)")
    
    # Step 2: Experience Level
    experience_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$", description="Experience level (required)")
    
    # Step 3: Education
    current_education: Optional[str] = None
    graduation_year: Optional[int] = None
    
    # Step 4: Time Commitment
    time_per_day: int = Field(..., ge=15, le=480, description="Daily time commitment in minutes (required)")  # 15 min to 8 hours
    
    # Step 5: Current Skills
    current_skills: Optional[List[SkillInput]] = []
    
    # Step 6: Learning Style
    preferred_learning_style: str = Field(
        ...,
        pattern="^(visual|reading|hands-on|mixed)$",
        description="Preferred learning style (required)"
    )


class ProfileCreate(BaseModel):
    """Schema for creating profile."""
    goal_role: Optional[str] = None
    experience_level: Optional[str] = None
    current_education: Optional[str] = None
    graduation_year: Optional[int] = None
    time_per_day: int = 60
    preferred_learning_style: Optional[str] = "mixed"
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Schema for updating profile."""
    goal_role: Optional[str] = None
    experience_level: Optional[str] = None
    current_education: Optional[str] = None
    graduation_year: Optional[int] = None
    time_per_day: Optional[int] = None
    preferred_learning_style: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    # Contact Info
    phone: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    # Resume Data
    education_data: Optional[List[Dict[str, Any]]] = None
    experience_data: Optional[List[Dict[str, Any]]] = None
    projects_data: Optional[List[Dict[str, Any]]] = None
    certifications_data: Optional[List[Dict[str, Any]]] = None
    extracurricular_data: Optional[List[Dict[str, Any]]] = None
    technical_skills_data: Optional[Dict[str, List[str]]] = None


class ProfileResponse(BaseModel):
    """Schema for profile response."""
    id: UUID
    user_id: UUID
    goal_role: Optional[str]
    experience_level: Optional[str]
    current_education: Optional[str]
    graduation_year: Optional[int]
    time_per_day: int
    preferred_learning_style: Optional[str]
    bio: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    phone: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    education_data: Optional[List[Dict[str, Any]]] = None
    experience_data: Optional[List[Dict[str, Any]]] = None
    projects_data: Optional[List[Dict[str, Any]]] = None
    certifications_data: Optional[List[Dict[str, Any]]] = None
    extracurricular_data: Optional[List[Dict[str, Any]]] = None
    technical_skills_data: Optional[Dict[str, List[str]]] = None
    profile_completion_percentage: int
    onboarding_completed: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
