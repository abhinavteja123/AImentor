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
    proficiency: Optional[int] = 3
    category: Optional[str] = "General"


class ProjectItem(BaseModel):
    """Project for resume."""
    title: Optional[str] = None
    name: Optional[str] = None  # Alias for title
    description: Optional[str] = None
    technologies: Optional[List[str]] = []
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: Optional[List[str]] = []  # Bullet points of achievements


class ExperienceItem(BaseModel):
    """Work experience/internship for resume."""
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = False
    bullet_points: Optional[List[str]] = []
    company_url: Optional[str] = None


class EducationItem(BaseModel):
    """Education for resume."""
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[str] = None  # Format: "2023"
    end_year: Optional[str] = None    # Format: "2027"
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    cgpa: Optional[float] = None
    percentage: Optional[float] = None
    location: Optional[str] = None


class CertificationItem(BaseModel):
    """Certification for resume."""
    name: Optional[str] = None
    issuer: Optional[str] = None
    date_obtained: Optional[str] = None
    credential_url: Optional[str] = None


class ExtracurricularItem(BaseModel):
    """Extracurricular activity for resume."""
    organization: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    achievements: Optional[List[str]] = []


class CourseworkItem(BaseModel):
    """Coursework/skill item for resume."""
    name: str
    category: Optional[str] = None


class ContactInfo(BaseModel):
    """Contact information."""
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website: Optional[str] = None


class TechnicalSkillsSection(BaseModel):
    """Technical skills grouped by type."""
    languages: Optional[List[str]] = []
    frameworks_and_tools: Optional[List[str]] = []
    databases: Optional[List[str]] = []
    cloud_platforms: Optional[List[str]] = []
    other: Optional[List[str]] = []


class ResumeResponse(BaseModel):
    """Schema for resume response."""
    id: UUID
    user_id: UUID
    version: int
    is_active: bool
    draft_name: Optional[str] = None
    is_base_version: bool = True
    parent_version_id: Optional[UUID] = None
    job_description: Optional[str] = None
    summary: Optional[str]
    skills_section: Optional[Dict[str, List[SkillItem]]]  # Grouped by category
    coursework_section: Optional[List[CourseworkItem]]
    projects_section: Optional[List[ProjectItem]]
    experience_section: Optional[List[ExperienceItem]]
    education_section: Optional[List[EducationItem]]
    certifications_section: Optional[List[CertificationItem]]
    extracurricular_section: Optional[List[ExtracurricularItem]]
    technical_skills_section: Optional[TechnicalSkillsSection]
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
    coursework_section: Optional[List[CourseworkItem]] = None
    projects_section: Optional[List[ProjectItem]] = None
    experience_section: Optional[List[ExperienceItem]] = None
    education_section: Optional[List[EducationItem]] = None
    certifications_section: Optional[List[CertificationItem]] = None
    extracurricular_section: Optional[List[ExtracurricularItem]] = None
    technical_skills_section: Optional[TechnicalSkillsSection] = None
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


class MissingSection(BaseModel):
    """Schema for missing resume section."""
    section_name: str
    is_required: bool
    prompt: str
    fields: List[str]


class ResumeValidationResponse(BaseModel):
    """Schema for resume validation response."""
    is_complete: bool
    missing_sections: List[MissingSection]
    completion_percentage: int


class ATSOptimizationRequest(BaseModel):
    """Schema for ATS optimization request."""
    section_type: str  # 'summary', 'experience', 'project', etc.
    content: Dict[str, Any]
    target_role: Optional[str] = None


class ATSOptimizationResponse(BaseModel):
    """Schema for ATS optimization response."""
    optimized_content: Dict[str, Any]
    improvements: List[str]
    ats_score: int  # 0-100
    keywords_added: List[str]

# Version Management Schemas
class ResumeVersionInfo(BaseModel):
    """Schema for resume version info."""
    id: UUID
    version: int
    draft_name: Optional[str] = None
    is_active: bool
    is_base_version: bool
    tailored_for: Optional[str] = None
    match_score: Optional[int] = None
    job_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CreateDraftRequest(BaseModel):
    """Schema for creating a new draft/version."""
    draft_name: str  # Name for this draft (e.g., "Google SWE Application")
    job_description: Optional[str] = None  # Optional JD to tailor for
    base_version_id: Optional[UUID] = None  # Clone from this version (or use active if not specified)


class CreateDraftResponse(BaseModel):
    """Schema for create draft response."""
    id: UUID
    version: int
    draft_name: str
    is_active: bool
    message: str


class CloneVersionRequest(BaseModel):
    """Schema for cloning a version."""
    source_version_id: UUID
    new_draft_name: str


class SetActiveVersionRequest(BaseModel):
    """Schema for setting active version."""
    version_id: UUID


class RegenerateResumeRequest(BaseModel):
    """Schema for regenerating resume."""
    version_id: Optional[UUID] = None  # If specified, regenerate specific version
    regenerate_summary: bool = True
    regenerate_from_profile: bool = False  # Pull fresh data from profile


class DeleteVersionRequest(BaseModel):
    """Schema for deleting a version."""
    version_id: UUID


class UpdateDraftRequest(BaseModel):
    """Schema for updating draft metadata."""
    draft_name: Optional[str] = None
    job_description: Optional[str] = None


# Export Schemas
class ExportPDFRequest(BaseModel):
    """Schema for PDF export request."""
    version_id: Optional[UUID] = None
    template: str = "modern"  # modern, classic, minimal


class ExportPDFResponse(BaseModel):
    """Schema for PDF export response."""
    pdf_data: str  # Base64 encoded PDF
    filename: str
    format: str = "pdf"
    template: str
    version_id: str
    generated_at: str


class ExportLaTeXResponse(BaseModel):
    """Schema for LaTeX export response."""
    latex_source: str
    template: str
    version_id: str
    generated_at: str


class LaTeXValidationRequest(BaseModel):
    """Schema for LaTeX validation request."""
    latex_content: str


class LaTeXValidationResponse(BaseModel):
    """Schema for LaTeX validation response."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    latex_length: int


class ExportPreviewResponse(BaseModel):
    """Schema for export preview response."""
    id: str
    version: int
    summary: Optional[str]
    skills_section: Optional[Dict[str, Any]]
    education_section: Optional[List[Dict[str, Any]]]
    experience_section: Optional[List[Dict[str, Any]]]
    projects_section: Optional[List[Dict[str, Any]]]
    certifications_section: Optional[List[Dict[str, Any]]]
    contact_info: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    available_formats: List[str]
    available_templates: List[str]