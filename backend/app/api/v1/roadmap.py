"""
Roadmap API Endpoints
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.schemas.roadmap import (
    RoadmapGenerateRequest,
    RoadmapResponse,
    RoadmapWeekResponse,
    RoadmapRegenerateRequest
)
from app.services.roadmap_service import RoadmapService
from app.services.ai.roadmap_generator import RoadmapGenerator
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(
    request: RoadmapGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate personalized learning roadmap.
    
    - **target_role**: Target career role
    - **duration_weeks**: Duration in weeks (4-24)
    - **intensity**: low, medium, high
    """
    roadmap_generator = RoadmapGenerator(db)
    roadmap = await roadmap_generator.generate_roadmap(
        user_id=current_user.id,
        target_role=request.target_role,
        duration_weeks=request.duration_weeks,
        intensity=request.intensity
    )
    return roadmap


@router.get("/current", response_model=RoadmapResponse)
async def get_current_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's current active roadmap.
    """
    roadmap_service = RoadmapService(db)
    roadmap = await roadmap_service.get_current_roadmap(current_user.id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active roadmap found. Generate one first."
        )
    return roadmap


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific roadmap by ID.
    """
    roadmap_service = RoadmapService(db)
    roadmap = await roadmap_service.get_roadmap(roadmap_id, current_user.id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found"
        )
    return roadmap


@router.get("/{roadmap_id}/week/{week_number}", response_model=RoadmapWeekResponse)
async def get_roadmap_week(
    roadmap_id: UUID,
    week_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific week's tasks from roadmap.
    """
    roadmap_service = RoadmapService(db)
    week_data = await roadmap_service.get_week_tasks(
        roadmap_id, 
        week_number, 
        current_user.id
    )
    return week_data


@router.put("/regenerate", response_model=RoadmapResponse)
async def regenerate_roadmap(
    request: RoadmapRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate roadmap with feedback.
    """
    roadmap_generator = RoadmapGenerator(db)
    roadmap = await roadmap_generator.regenerate_roadmap(
        user_id=current_user.id,
        roadmap_id=request.roadmap_id,
        feedback=request.feedback,
        adjustments=request.adjustments
    )
    return roadmap


@router.get("/all", response_model=list)
async def get_all_roadmaps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all user's roadmaps.
    """
    roadmap_service = RoadmapService(db)
    roadmaps = await roadmap_service.get_all_roadmaps(current_user.id)
    return roadmaps
