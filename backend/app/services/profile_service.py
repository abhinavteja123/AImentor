"""
Profile Service
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import UserProfile
from app.models.skill import SkillMaster, UserSkill
from app.schemas.profile import OnboardingData, ProfileUpdate, ProfileResponse


class ProfileService:
    """Service for profile operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_profile(
        self, 
        user_id: UUID, 
        data: OnboardingData
    ) -> ProfileResponse:
        """Create or update profile from onboarding data."""
        # Get existing profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update profile fields
        profile.goal_role = data.goal_role
        profile.experience_level = data.experience_level
        profile.current_education = data.current_education
        profile.graduation_year = data.graduation_year
        profile.time_per_day = data.time_per_day
        profile.preferred_learning_style = data.preferred_learning_style
        profile.onboarding_completed = datetime.utcnow()
        profile.profile_completion_percentage = 100
        
        await self.db.flush()
        
        # Add current skills
        if data.current_skills:
            for skill_input in data.current_skills:
                await self.add_user_skill(
                    user_id, 
                    skill_input.skill_name, 
                    skill_input.proficiency
                )
        
        await self.db.commit()
        await self.db.refresh(profile)
        
        return profile
    
    async def get_profile(self, user_id: UUID) -> Optional[UserProfile]:
        """Get user profile."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_profile(
        self, 
        user_id: UUID, 
        updates: ProfileUpdate
    ) -> ProfileResponse:
        """Update user profile."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Update only provided fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(profile)
        
        return profile
    
    async def add_user_skill(
        self, 
        user_id: UUID, 
        skill_name: str, 
        proficiency: int = 1
    ) -> UserSkill:
        """Add a skill to user's profile."""
        # Find or create skill in master
        result = await self.db.execute(
            select(SkillMaster).where(
                SkillMaster.skill_name.ilike(skill_name)
            )
        )
        skill = result.scalar_one_or_none()
        
        if not skill:
            # Create new skill in master
            skill = SkillMaster(
                skill_name=skill_name,
                category="other",
                difficulty_level=3
            )
            self.db.add(skill)
            await self.db.flush()
        
        # Check if user already has this skill
        result = await self.db.execute(
            select(UserSkill).where(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill.id
            )
        )
        user_skill = result.scalar_one_or_none()
        
        if user_skill:
            # Update proficiency
            user_skill.proficiency_level = proficiency
            user_skill.updated_at = datetime.utcnow()
        else:
            # Create new user skill
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                proficiency_level=proficiency
            )
            self.db.add(user_skill)
        
        await self.db.commit()
        await self.db.refresh(user_skill)
        
        return user_skill
