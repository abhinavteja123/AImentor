"""
Resume API Endpoints
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.resume import (
    ResumeResponse,
    ResumeTailorRequest,
    ResumeTailorResponse,
    ResumeUpdateRequest,
    ResumeValidationResponse,
    ATSOptimizationRequest,
    ATSOptimizationResponse,
    ResumeVersionInfo,
    CreateDraftRequest,
    CreateDraftResponse,
    SetActiveVersionRequest,
    RegenerateResumeRequest,
    UpdateDraftRequest
)
from app.services.resume_service import ResumeService
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/current", response_model=ResumeResponse)
async def get_current_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current active resume.
    """
    resume_service = ResumeService(db)
    resume = await resume_service.get_current_resume(current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Generate one first."
        )
    return resume


@router.post("/generate", response_model=ResumeResponse)
async def generate_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate initial resume from profile and skills.
    """
    resume_service = ResumeService(db)
    resume = await resume_service.generate_initial_resume(current_user.id)
    return resume


@router.post("/sync-from-profile", response_model=ResumeResponse)
async def sync_from_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync resume data from user profile.
    This pulls education, experience, projects, etc. from the profile
    and updates the resume accordingly.
    """
    resume_service = ResumeService(db)
    resume = await resume_service.sync_from_profile(current_user.id)
    return resume


@router.put("/update", response_model=ResumeResponse)
async def update_resume(
    updates: ResumeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update resume sections.
    """
    resume_service = ResumeService(db)
    resume = await resume_service.update_resume(
        current_user.id,
        updates
    )
    return resume


@router.post("/tailor", response_model=ResumeTailorResponse)
async def tailor_resume(
    request: ResumeTailorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Tailor resume to job description.
    
    Returns:
    - Tailored summary
    - Matched skills
    - Match score
    - Improvement suggestions
    """
    resume_service = ResumeService(db)
    result = await resume_service.tailor_resume_to_job(
        current_user.id,
        request.job_description
    )
    return result


@router.get("/export")
async def export_resume(
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export resume as PDF or DOCX.
    
    - **format**: pdf or docx
    """
    resume_service = ResumeService(db)
    file_content, filename, content_type = await resume_service.export_resume(
        current_user.id,
        format=format
    )
    
    return StreamingResponse(
        file_content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/versions")
async def get_resume_versions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all resume versions with metadata.
    """
    resume_service = ResumeService(db)
    versions = await resume_service.get_all_versions(current_user.id)
    return {"versions": versions}


@router.get("/versions/{version_id}", response_model=ResumeResponse)
async def get_specific_version(
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific version of the resume by ID.
    """
    resume_service = ResumeService(db)
    version = await resume_service.get_version_by_id(current_user.id, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    return version


@router.post("/versions/create", response_model=ResumeResponse)
async def create_draft(
    request: CreateDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new draft/version by cloning an existing resume.
    Can optionally tailor for a specific job description.
    """
    resume_service = ResumeService(db)
    draft = await resume_service.create_draft(
        user_id=current_user.id,
        draft_name=request.draft_name,
        job_description=request.job_description,
        base_version_id=request.base_version_id
    )
    return draft


@router.post("/versions/{version_id}/activate", response_model=ResumeResponse)
async def set_active_version(
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set a specific version as the active resume.
    """
    resume_service = ResumeService(db)
    version = await resume_service.set_active_version(current_user.id, version_id)
    return version


@router.put("/versions/{version_id}", response_model=ResumeResponse)
async def update_version_sections(
    version_id: UUID,
    updates: ResumeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update specific sections of a version.
    """
    resume_service = ResumeService(db)
    version = await resume_service.update_version_sections(
        current_user.id,
        version_id,
        updates
    )
    return version


@router.patch("/versions/{version_id}/metadata", response_model=ResumeResponse)
async def update_draft_metadata(
    version_id: UUID,
    request: UpdateDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update draft name and/or job description.
    """
    resume_service = ResumeService(db)
    version = await resume_service.update_draft_metadata(
        current_user.id,
        version_id,
        draft_name=request.draft_name,
        job_description=request.job_description
    )
    return version


@router.delete("/versions/{version_id}")
async def delete_version(
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific version. Cannot delete the only version.
    """
    resume_service = ResumeService(db)
    await resume_service.delete_version(current_user.id, version_id)
    return {"message": "Version deleted successfully"}


@router.post("/regenerate", response_model=ResumeResponse)
async def regenerate_resume(
    request: RegenerateResumeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate resume content with AI.
    Optionally pull fresh data from profile.
    """
    resume_service = ResumeService(db)
    resume = await resume_service.regenerate_resume(
        user_id=current_user.id,
        version_id=request.version_id,
        regenerate_summary=request.regenerate_summary,
        regenerate_from_profile=request.regenerate_from_profile
    )
    return resume


@router.get("/validate", response_model=ResumeValidationResponse)
async def validate_resume_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate resume data and identify missing sections.
    Returns prompts for user to fill in missing information.
    """
    resume_service = ResumeService(db)
    validation_result = await resume_service.validate_resume_data(current_user.id)
    return validation_result


@router.post("/optimize-section", response_model=ATSOptimizationResponse)
async def optimize_section_for_ats(
    request: ATSOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize a resume section for ATS compatibility.
    Uses AI to enhance content with relevant keywords and formatting.
    """
    resume_service = ResumeService(db)
    result = await resume_service.optimize_section_for_ats(
        current_user.id,
        request
    )
    return result
