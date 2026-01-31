"""
Skill Service
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import SkillMaster, UserSkill


class SkillService:
    """Service for skill operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_skills(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SkillMaster]:
        """Get skills from master database."""
        query = select(SkillMaster)
        
        if category:
            query = query.where(SkillMaster.category == category)
        
        if search:
            query = query.where(
                SkillMaster.skill_name.ilike(f"%{search}%")
            )
        
        query = query.order_by(SkillMaster.skill_name)
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_categories(self) -> List[str]:
        """Get all skill categories."""
        result = await self.db.execute(
            select(SkillMaster.category).distinct()
        )
        return [row[0] for row in result.all()]
    
    async def get_user_skills(self, user_id: UUID) -> List[dict]:
        """Get user's skills with proficiency."""
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = result.scalars().all()
        
        return [
            {
                "id": str(us.id),
                "skill_id": str(us.skill_id),
                "skill_name": us.skill.skill_name,
                "category": us.skill.category,
                "proficiency_level": us.proficiency_level,
                "target_proficiency": us.target_proficiency,
                "practice_hours": us.practice_hours,
                "confidence_rating": us.confidence_rating,
                "last_practiced": us.last_practiced
            }
            for us in user_skills
        ]
    
    async def get_skill_by_name(self, skill_name: str) -> Optional[SkillMaster]:
        """Get skill by name."""
        result = await self.db.execute(
            select(SkillMaster).where(
                SkillMaster.skill_name.ilike(skill_name)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_skill_by_id(self, skill_id: UUID) -> Optional[SkillMaster]:
        """Get skill by ID."""
        result = await self.db.execute(
            select(SkillMaster).where(SkillMaster.id == skill_id)
        )
        return result.scalar_one_or_none()
