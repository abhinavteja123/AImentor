"""
Profile API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.postgres import get_db
from ...schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    OnboardingData
)
from ...services.profile_service import ProfileService
from ...utils.security import get_current_user
from ...models.user import User

router = APIRouter()


@router.post("/onboarding", response_model=ProfileResponse)
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete user onboarding with profile data.
    
    Creates user profile with:
    - Goal role
    - Experience level
    - Education
    - Time commitment
    - Learning style
    - Current skills (optional)
    """
    profile_service = ProfileService(db)
    profile = await profile_service.create_profile(current_user.id, onboarding_data)
    return profile


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile.
    """
    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete onboarding."
        )
    return profile


@router.put("/update", response_model=ProfileResponse)
async def update_profile(
    updates: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile.
    """
    profile_service = ProfileService(db)
    profile = await profile_service.update_profile(current_user.id, updates)
    return profile


@router.post("/skills")
async def add_user_skill(
    skill_name: str,
    proficiency: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a skill to user's profile.
    
    - **skill_name**: Name of the skill
    - **proficiency**: Proficiency level (1-5)
    """
    profile_service = ProfileService(db)
    skill = await profile_service.add_user_skill(
        current_user.id, 
        skill_name, 
        proficiency
    )
    return {"message": "Skill added successfully", "skill": skill}
