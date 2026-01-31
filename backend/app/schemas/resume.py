"""
Resume Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class SkillItem(BaseModel):
    """Skill for resume."""
    name: str
    proficiency: int
    category: str


class ProjectItem(BaseModel):
    """Project for resume."""
    title: str
    description: str
    technologies: List[str]
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ExperienceItem(BaseModel):
    """Work experience for resume."""
    company: str
    role: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    is_current: bool = False
    bullet_points: List[str]


class EducationItem(BaseModel):
    """Education for resume."""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None


class CertificationItem(BaseModel):
    """Certification for resume."""
    name: str
    issuer: str
    date_obtained: Optional[str] = None
    credential_url: Optional[str] = None


class ContactInfo(BaseModel):
    """Contact information."""
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class ResumeResponse(BaseModel):
    """Schema for resume response."""
    id: UUID
    user_id: UUID
    version: int
    is_active: bool
    summary: Optional[str]
    skills_section: Optional[Dict[str, List[SkillItem]]]  # Grouped by category
    projects_section: Optional[List[ProjectItem]]
    experience_section: Optional[List[ExperienceItem]]
    education_section: Optional[List[EducationItem]]
    certifications_section: Optional[List[CertificationItem]]
    contact_info: Optional[ContactInfo]
    tailored_for: Optional[str]
    match_score: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ResumeUpdateRequest(BaseModel):
    """Schema for updating resume."""
    summary: Optional[str] = None
    skills_section: Optional[Dict[str, List[SkillItem]]] = None
    projects_section: Optional[List[ProjectItem]] = None
    experience_section: Optional[List[ExperienceItem]] = None
    education_section: Optional[List[EducationItem]] = None
    certifications_section: Optional[List[CertificationItem]] = None
    contact_info: Optional[ContactInfo] = None


class ResumeTailorRequest(BaseModel):
    """Schema for tailoring resume to job."""
    job_description: str


class ResumeTailorResponse(BaseModel):
    """Schema for tailored resume response."""
    tailored_summary: str
    matched_skills: List[str]
    relevant_projects: List[str]
    match_score: int  # 0-100
    missing_skills: List[str]
    suggestions: List[str]
