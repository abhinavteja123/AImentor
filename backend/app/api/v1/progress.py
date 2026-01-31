"""
Progress API Endpoints
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.postgres import get_db
from ...schemas.progress import (
    TaskCompleteRequest,
    TaskSkipRequest,
    ProgressStatsResponse,
    ProgressLogResponse
)
from ...services.progress_service import ProgressService
from ...utils.security import get_current_user
from ...models.user import User

router = APIRouter()


@router.post("/task/complete", response_model=ProgressLogResponse)
async def complete_task(
    request: TaskCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a task as complete.
    
    - **task_id**: ID of the task
    - **time_spent**: Time spent in minutes
    - **difficulty_rating**: How difficult was it (1-5)
    - **confidence_rating**: How confident are you now (1-5)
    - **notes**: Optional notes
    """
    progress_service = ProgressService(db)
    log = await progress_service.complete_task(
        user_id=current_user.id,
        task_id=request.task_id,
        time_spent=request.time_spent,
        difficulty_rating=request.difficulty_rating,
        confidence_rating=request.confidence_rating,
        notes=request.notes
    )
    return log


@router.post("/task/skip")
async def skip_task(
    request: TaskSkipRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Skip a task with reason.
    """
    progress_service = ProgressService(db)
    await progress_service.skip_task(
        user_id=current_user.id,
        task_id=request.task_id,
        reason=request.reason
    )
    return {"message": "Task skipped"}


@router.get("/stats", response_model=ProgressStatsResponse)
async def get_progress_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's progress statistics.
    
    Returns:
    - Total learning time
    - Tasks completed
    - Current streak
    - Skills acquired
    - Weekly stats
    - Achievements
    """
    progress_service = ProgressService(db)
    stats = await progress_service.get_stats(current_user.id)
    return stats


@router.get("/activity")
async def get_activity_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity history for heatmap/charts.
    """
    progress_service = ProgressService(db)
    activity = await progress_service.get_activity_history(
        current_user.id, 
        days=days
    )
    return {"activity": activity}


@router.get("/achievements")
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's achievements and badges.
    """
    progress_service = ProgressService(db)
    achievements = await progress_service.get_achievements(current_user.id)
    return {"achievements": achievements}
