"""
Resume API Endpoints
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.schemas.resume import (
    ResumeResponse,
    ResumeTailorRequest,
    ResumeTailorResponse,
    ResumeUpdateRequest
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
    Get all resume versions.
    """
    resume_service = ResumeService(db)
    versions = await resume_service.get_versions(current_user.id)
    return {"versions": versions}
