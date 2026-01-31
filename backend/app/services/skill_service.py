"""
Skill Service - Complete skill management
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.skill import SkillMaster, UserSkill


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
        categories = [row[0] for row in result.all() if row[0]]
        
        # Add default categories if none exist
        default_categories = [
            "frontend", "backend", "database", "devops", "mobile",
            "ai_ml", "data_science", "soft_skills", "tools", "other"
        ]
        all_categories = list(set(categories + default_categories))
        return sorted(all_categories)
    
    async def get_user_skills(self, user_id: UUID) -> List[dict]:
        """Get user's skills with proficiency and progress."""
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.proficiency_level.desc())
        )
        user_skills = result.scalars().all()
        
        return [
            {
                "id": str(us.id),
                "skill_id": str(us.skill_id),
                "skill_name": us.skill.skill_name if us.skill else "Unknown",
                "category": us.skill.category if us.skill else "other",
                "proficiency_level": us.proficiency_level,
                "target_proficiency": us.target_proficiency,
                "practice_hours": us.practice_hours or 0,
                "confidence_rating": us.confidence_rating or 1,
                "last_practiced": us.last_practiced.isoformat() if us.last_practiced else None,
                "notes": us.notes,
                "progress_percentage": min(100, (us.proficiency_level / us.target_proficiency * 100)) if us.target_proficiency else 100
            }
            for us in user_skills
        ]
    
    async def get_user_skill_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's skill statistics."""
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = result.scalars().all()
        
        if not user_skills:
            return {
                "total_skills": 0,
                "skills_by_category": {},
                "average_proficiency": 0,
                "skills_at_target": 0,
                "total_practice_hours": 0,
                "strongest_category": None,
                "weakest_category": None
            }
        
        # Calculate stats
        total_skills = len(user_skills)
        total_proficiency = sum(us.proficiency_level for us in user_skills)
        skills_at_target = sum(1 for us in user_skills if us.proficiency_level >= us.target_proficiency)
        total_practice = sum(us.practice_hours or 0 for us in user_skills)
        
        # Group by category
        skills_by_category = {}
        category_proficiency = {}
        for us in user_skills:
            cat = us.skill.category if us.skill else "other"
            if cat not in skills_by_category:
                skills_by_category[cat] = 0
                category_proficiency[cat] = []
            skills_by_category[cat] += 1
            category_proficiency[cat].append(us.proficiency_level)
        
        # Find strongest/weakest categories
        category_averages = {
            cat: sum(profs) / len(profs) 
            for cat, profs in category_proficiency.items()
        }
        strongest = max(category_averages, key=category_averages.get) if category_averages else None
        weakest = min(category_averages, key=category_averages.get) if category_averages else None
        
        return {
            "total_skills": total_skills,
            "skills_by_category": skills_by_category,
            "average_proficiency": round(total_proficiency / total_skills, 1),
            "skills_at_target": skills_at_target,
            "total_practice_hours": round(total_practice, 1),
            "strongest_category": strongest,
            "weakest_category": weakest,
            "category_averages": category_averages
        }
    
    async def add_user_skill(
        self,
        user_id: UUID,
        skill_id: Optional[UUID] = None,
        skill_name: Optional[str] = None,
        category: Optional[str] = "other",
        proficiency_level: int = 1,
        target_proficiency: int = 3,
        confidence_rating: int = 1,
        notes: Optional[str] = None
    ) -> dict:
        """Add a skill to user's profile."""
        
        # Get or create skill
        if skill_id:
            # Use existing skill
            skill = await self.get_skill_by_id(skill_id)
            if not skill:
                raise ValueError("Skill not found")
        elif skill_name:
            # Find or create skill
            skill = await self.get_skill_by_name(skill_name)
            if not skill:
                # Create new skill in master
                skill = SkillMaster(
                    skill_name=skill_name.strip(),
                    category=category or "other",
                    difficulty_level=3,
                    market_demand_score=0.5
                )
                self.db.add(skill)
                await self.db.flush()
        else:
            raise ValueError("Either skill_id or skill_name must be provided")
        
        # Check if user already has this skill
        existing = await self.db.execute(
            select(UserSkill).where(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill.id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Skill already added to your profile")
        
        # Create user skill
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=skill.id,
            proficiency_level=proficiency_level,
            target_proficiency=target_proficiency,
            confidence_rating=confidence_rating,
            notes=notes,
            acquired_date=datetime.utcnow().date()
        )
        self.db.add(user_skill)
        await self.db.commit()
        await self.db.refresh(user_skill)
        
        return {
            "id": str(user_skill.id),
            "skill_id": str(skill.id),
            "skill_name": skill.skill_name,
            "category": skill.category,
            "proficiency_level": user_skill.proficiency_level,
            "target_proficiency": user_skill.target_proficiency,
            "practice_hours": user_skill.practice_hours or 0,
            "confidence_rating": user_skill.confidence_rating,
            "last_practiced": None,
            "notes": user_skill.notes,
            "progress_percentage": min(100, (user_skill.proficiency_level / user_skill.target_proficiency * 100))
        }
    
    async def bulk_add_skills(
        self,
        user_id: UUID,
        skills: List[dict]
    ) -> Dict[str, Any]:
        """Bulk add skills to user's profile."""
        added = []
        skipped = []
        
        for skill_input in skills:
            try:
                result = await self.add_user_skill(
                    user_id=user_id,
                    skill_name=skill_input.skill_name,
                    category=skill_input.category,
                    proficiency_level=skill_input.proficiency_level
                )
                added.append(result)
            except ValueError as e:
                skipped.append({
                    "skill_name": skill_input.skill_name,
                    "reason": str(e)
                })
        
        return {
            "added": added,
            "skipped": skipped,
            "total_added": len(added),
            "total_skipped": len(skipped)
        }
    
    async def update_user_skill(
        self,
        user_id: UUID,
        user_skill_id: UUID,
        proficiency_level: Optional[int] = None,
        target_proficiency: Optional[int] = None,
        confidence_rating: Optional[int] = None,
        notes: Optional[str] = None,
        practice_hours: Optional[float] = None
    ) -> Optional[dict]:
        """Update a user's skill."""
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(
                UserSkill.id == user_skill_id,
                UserSkill.user_id == user_id
            )
        )
        user_skill = result.scalar_one_or_none()
        
        if not user_skill:
            return None
        
        # Update fields
        if proficiency_level is not None:
            user_skill.proficiency_level = proficiency_level
        if target_proficiency is not None:
            user_skill.target_proficiency = target_proficiency
        if confidence_rating is not None:
            user_skill.confidence_rating = confidence_rating
        if notes is not None:
            user_skill.notes = notes
        if practice_hours is not None:
            user_skill.practice_hours = (user_skill.practice_hours or 0) + practice_hours
            user_skill.last_practiced = datetime.utcnow()
        
        user_skill.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user_skill)
        
        return {
            "id": str(user_skill.id),
            "skill_id": str(user_skill.skill_id),
            "skill_name": user_skill.skill.skill_name if user_skill.skill else "Unknown",
            "category": user_skill.skill.category if user_skill.skill else "other",
            "proficiency_level": user_skill.proficiency_level,
            "target_proficiency": user_skill.target_proficiency,
            "practice_hours": user_skill.practice_hours or 0,
            "confidence_rating": user_skill.confidence_rating,
            "last_practiced": user_skill.last_practiced.isoformat() if user_skill.last_practiced else None,
            "notes": user_skill.notes,
            "progress_percentage": min(100, (user_skill.proficiency_level / user_skill.target_proficiency * 100))
        }
    
    async def remove_user_skill(self, user_id: UUID, user_skill_id: UUID) -> bool:
        """Remove a skill from user's profile."""
        result = await self.db.execute(
            delete(UserSkill).where(
                UserSkill.id == user_skill_id,
                UserSkill.user_id == user_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def log_practice(
        self,
        user_id: UUID,
        user_skill_id: UUID,
        hours: float
    ) -> Optional[dict]:
        """Log practice hours for a skill."""
        return await self.update_user_skill(
            user_id=user_id,
            user_skill_id=user_skill_id,
            practice_hours=hours
        )
    
    async def get_skill_by_name(self, skill_name: str) -> Optional[SkillMaster]:
        """Get skill by name."""
        result = await self.db.execute(
            select(SkillMaster).where(
                SkillMaster.skill_name.ilike(skill_name.strip())
            )
        )
        return result.scalar_one_or_none()
    
    async def get_skill_by_id(self, skill_id: UUID) -> Optional[SkillMaster]:
        """Get skill by ID."""
        result = await self.db.execute(
            select(SkillMaster).where(SkillMaster.id == skill_id)
        )
        return result.scalar_one_or_none()
    
    async def get_trending_skills(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """Get trending skills by market demand."""
        query = select(SkillMaster).order_by(SkillMaster.market_demand_score.desc())
        
        if category:
            query = query.where(SkillMaster.category == category)
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        skills = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "skill_name": s.skill_name,
                "category": s.category,
                "market_demand_score": s.market_demand_score,
                "difficulty_level": s.difficulty_level,
                "description": s.description
            }
            for s in skills
        ]
