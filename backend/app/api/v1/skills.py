"""
Skills API Endpoints - Full Skills Management & AI Gap Analysis
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.postgres import get_db
from ...schemas.skill import (
    SkillMasterResponse,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
    AddUserSkillRequest,
    UpdateUserSkillRequest,
    UserSkillResponse,
    SkillRecommendationsResponse,
    BulkAddSkillsRequest
)
from ...services.skill_service import SkillService
from ...services.ai.skill_analyzer import SkillAnalyzer
from ...utils.security import get_current_user
from ...models.user import User

router = APIRouter()


# ============== Master Skills Database ==============

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


# ============== User Skills Management ==============

@router.get("/user-skills", response_model=dict)
async def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's skills with proficiency and statistics.
    """
    skill_service = SkillService(db)
    skills = await skill_service.get_user_skills(current_user.id)
    stats = await skill_service.get_user_skill_stats(current_user.id)
    return {"skills": skills, "stats": stats}


@router.post("/user-skills", response_model=UserSkillResponse)
async def add_user_skill(
    request: AddUserSkillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a skill to user's profile.
    Can specify skill_id (from master DB) or skill_name (will create/find).
    """
    skill_service = SkillService(db)
    try:
        skill = await skill_service.add_user_skill(
            user_id=current_user.id,
            skill_id=request.skill_id,
            skill_name=request.skill_name,
            category=request.category,
            proficiency_level=request.proficiency_level,
            target_proficiency=request.target_proficiency,
            confidence_rating=request.confidence_rating,
            notes=request.notes
        )
        return skill
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/user-skills/bulk", response_model=dict)
async def bulk_add_skills(
    request: BulkAddSkillsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk add multiple skills to user's profile.
    """
    skill_service = SkillService(db)
    results = await skill_service.bulk_add_skills(
        user_id=current_user.id,
        skills=request.skills
    )
    return results


@router.put("/user-skills/{skill_id}", response_model=UserSkillResponse)
async def update_user_skill(
    skill_id: UUID,
    request: UpdateUserSkillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's skill (proficiency, target, notes).
    """
    skill_service = SkillService(db)
    skill = await skill_service.update_user_skill(
        user_id=current_user.id,
        user_skill_id=skill_id,
        proficiency_level=request.proficiency_level,
        target_proficiency=request.target_proficiency,
        confidence_rating=request.confidence_rating,
        notes=request.notes,
        practice_hours=request.practice_hours
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/user-skills/{skill_id}")
async def remove_user_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a skill from user's profile.
    """
    skill_service = SkillService(db)
    success = await skill_service.remove_user_skill(
        user_id=current_user.id,
        user_skill_id=skill_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill removed successfully"}


@router.post("/user-skills/{skill_id}/practice")
async def log_skill_practice(
    skill_id: UUID,
    hours: float = Query(..., gt=0, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Log practice hours for a skill.
    """
    skill_service = SkillService(db)
    skill = await skill_service.log_practice(
        user_id=current_user.id,
        user_skill_id=skill_id,
        hours=hours
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


# ============== AI-Powered Analysis ==============

@router.post("/analyze-gap", response_model=SkillGapAnalysisResponse)
async def analyze_skill_gap(
    request: SkillGapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI-powered skill gap analysis for target role.
    
    Returns:
    - Required skills for role
    - Current user skills
    - Missing skills
    - Skills to improve
    - Overall readiness percentage
    - AI insights and recommendations
    - Learning roadmap suggestions
    """
    skill_analyzer = SkillAnalyzer(db)
    analysis = await skill_analyzer.analyze_skill_gap(
        user_id=current_user.id,
        target_role=request.target_role
    )
    return analysis


@router.get("/recommendations", response_model=SkillRecommendationsResponse)
async def get_skill_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered skill recommendations based on:
    - User's current skills
    - Career goals
    - Market trends
    - Learning patterns
    """
    skill_analyzer = SkillAnalyzer(db)
    recommendations = await skill_analyzer.get_skill_recommendations(
        user_id=current_user.id
    )
    return recommendations


@router.get("/trending")
async def get_trending_skills(
    category: Optional[str] = None,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trending skills by market demand.
    """
    skill_service = SkillService(db)
    trending = await skill_service.get_trending_skills(
        category=category,
        limit=limit
    )
    return {"trending_skills": trending}


@router.post("/assess-proficiency")
async def assess_skill_proficiency(
    skill_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI-powered skill proficiency assessment.
    Returns questions and evaluates skill level.
    """
    skill_analyzer = SkillAnalyzer(db)
    assessment = await skill_analyzer.generate_skill_assessment(
        skill_name=skill_name
    )
    return assessment


@router.post("/compare-roles")
async def compare_role_requirements(
    role1: str,
    role2: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare skill requirements between two roles.
    """
    skill_analyzer = SkillAnalyzer(db)
    comparison = await skill_analyzer.compare_roles(role1, role2)
    return comparison
