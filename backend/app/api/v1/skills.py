"""
Skills API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.schemas.skill import (
    SkillMasterResponse,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse
)
from app.services.skill_service import SkillService
from app.services.ai.skill_analyzer import SkillAnalyzer
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/master", response_model=List[SkillMasterResponse])
async def get_skills_database(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search skills"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get skills from master database.
    
    - **category**: Filter by category (frontend, backend, database, devops, etc.)
    - **search**: Search by skill name
    - **limit**: Maximum results (default 50)
    """
    skill_service = SkillService(db)
    skills = await skill_service.get_skills(
        category=category,
        search=search,
        limit=limit,
        offset=offset
    )
    return skills


@router.get("/categories")
async def get_skill_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all skill categories.
    """
    skill_service = SkillService(db)
    categories = await skill_service.get_categories()
    return {"categories": categories}


@router.post("/analyze-gap", response_model=SkillGapAnalysisResponse)
async def analyze_skill_gap(
    request: SkillGapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze skill gap for target role.
    
    Returns:
    - Required skills for role
    - Current user skills
    - Missing skills
    - Skills to improve
    - Overall readiness percentage
    - AI insights and recommendations
    """
    skill_analyzer = SkillAnalyzer(db)
    analysis = await skill_analyzer.analyze_skill_gap(
        user_id=current_user.id,
        target_role=request.target_role
    )
    return analysis


@router.get("/user-skills")
async def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's skills with proficiency.
    """
    skill_service = SkillService(db)
    skills = await skill_service.get_user_skills(current_user.id)
    return {"skills": skills}
