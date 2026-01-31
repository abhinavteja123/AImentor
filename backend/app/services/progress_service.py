"""
Progress Service
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.progress import ProgressLog, Achievement, UserStreak
from ..models.roadmap import RoadmapTask, Roadmap
from ..models.skill import UserSkill
from .roadmap_service import RoadmapService


class ProgressService:
    """Service for progress tracking."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.roadmap_service = RoadmapService(db)
    
    async def complete_task(
        self,
        user_id: UUID,
        task_id: UUID,
        time_spent: int,
        difficulty_rating: Optional[int] = None,
        confidence_rating: Optional[int] = None,
        notes: Optional[str] = None
    ) -> ProgressLog:
        """Mark a task as complete."""
        # Get task
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update task status
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        
        # Create progress log
        log = ProgressLog(
            user_id=user_id,
            task_id=task_id,
            time_spent=time_spent,
            difficulty_rating=difficulty_rating,
            confidence_rating=confidence_rating,
            notes=notes,
            ended_at=datetime.utcnow()
        )
        self.db.add(log)
        
        # Update streak
        await self._update_streak(user_id, time_spent, 1)
        
        # Update roadmap progress
        await self.roadmap_service.update_roadmap_progress(task.roadmap_id)
        
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    async def skip_task(
        self,
        user_id: UUID,
        task_id: UUID,
        reason: str
    ):
        """Skip a task."""
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task.status = "skipped"
        task.skipped_reason = reason
        
        await self.db.commit()
    
    async def get_stats(self, user_id: UUID) -> dict:
        """Get user's progress statistics."""
        # Total learning time
        result = await self.db.execute(
            select(func.sum(ProgressLog.time_spent))
            .where(ProgressLog.user_id == user_id)
        )
        total_time = result.scalar() or 0
        
        # Tasks completed
        result = await self.db.execute(
            select(func.count(ProgressLog.id))
            .where(ProgressLog.user_id == user_id)
        )
        total_completed = result.scalar() or 0
        
        # Current roadmap progress
        roadmap = await self.roadmap_service.get_current_roadmap(user_id)
        roadmap_progress = roadmap.completion_percentage if roadmap else 0
        total_tasks = len(roadmap.tasks) if roadmap else 0
        
        # Skills acquired
        result = await self.db.execute(
            select(func.count(UserSkill.id))
            .where(UserSkill.user_id == user_id)
        )
        skills_count = result.scalar() or 0
        
        # Streak
        result = await self.db.execute(
            select(UserStreak).where(UserStreak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        
        streak_info = {
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "last_activity_date": streak.last_activity_date if streak else None
        }
        
        # Weekly stats
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(
                func.count(ProgressLog.id),
                func.sum(ProgressLog.time_spent),
                func.avg(ProgressLog.difficulty_rating),
                func.avg(ProgressLog.confidence_rating)
            )
            .where(
                ProgressLog.user_id == user_id,
                ProgressLog.created_at >= week_ago
            )
        )
        weekly = result.one()
        
        weekly_stats = {
            "tasks_completed": weekly[0] or 0,
            "time_spent": weekly[1] or 0,
            "skills_practiced": 0,
            "average_difficulty": float(weekly[2]) if weekly[2] else 0,
            "average_confidence": float(weekly[3]) if weekly[3] else 0
        }
        
        # Recent achievements
        result = await self.db.execute(
            select(Achievement)
            .where(Achievement.user_id == user_id)
            .order_by(Achievement.earned_at.desc())
            .limit(5)
        )
        achievements = result.scalars().all()
        
        # Get skill growth data with skill names
        from ..models.skill import SkillMaster
        result = await self.db.execute(
            select(UserSkill, SkillMaster.skill_name)
            .join(SkillMaster, UserSkill.skill_id == SkillMaster.id)
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.proficiency_level.desc())
        )
        user_skills = result.all()
        
        skill_growth = [
            {
                "skill_name": row[1],  # SkillMaster.skill_name
                "proficiency_level": row[0].proficiency_level or 0,  # UserSkill.proficiency_level
                "last_practiced": row[0].updated_at.isoformat() if row[0].updated_at else None
            }
            for row in user_skills
        ]
        
        return {
            "total_learning_time": total_time,
            "total_tasks_completed": total_completed,
            "total_tasks": total_tasks,
            "skills_acquired": skills_count,
            "current_roadmap_progress": roadmap_progress,
            "streak": streak_info,
            "weekly_stats": weekly_stats,
            "recent_achievements": achievements,
            "skill_growth": skill_growth
        }
    
    async def get_activity_history(
        self, 
        user_id: UUID, 
        days: int = 30
    ) -> List[dict]:
        """Get activity history for heatmap."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                func.date(ProgressLog.created_at).label("date"),
                func.count(ProgressLog.id).label("tasks"),
                func.sum(ProgressLog.time_spent).label("time")
            )
            .where(
                ProgressLog.user_id == user_id,
                ProgressLog.created_at >= start_date
            )
            .group_by(func.date(ProgressLog.created_at))
        )
        
        return [
            {
                "date": str(row.date),
                "tasks_completed": row.tasks,
                "time_spent": row.time or 0,
                "activity_level": min(4, row.tasks)  # 0-4 scale
            }
            for row in result.all()
        ]
    
    async def get_achievements(self, user_id: UUID) -> List[Achievement]:
        """Get user's achievements."""
        result = await self.db.execute(
            select(Achievement)
            .where(Achievement.user_id == user_id)
            .order_by(Achievement.earned_at.desc())
        )
        return result.scalars().all()
    
    async def _update_streak(
        self, 
        user_id: UUID, 
        time_spent: int,
        tasks_completed: int
    ):
        """Update user's streak."""
        result = await self.db.execute(
            select(UserStreak).where(UserStreak.user_id == user_id)
        )
        streak = result.scalar_one_or_none()
        
        today = datetime.utcnow().date()
        
        if not streak:
            streak = UserStreak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=datetime.utcnow(),
                tasks_this_week=tasks_completed,
                time_this_week=time_spent
            )
            self.db.add(streak)
        else:
            last_date = streak.last_activity_date.date() if streak.last_activity_date else None
            
            if last_date == today:
                # Same day, just update counts
                pass
            elif last_date == today - timedelta(days=1):
                # Consecutive day
                streak.current_streak += 1
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
            else:
                # Streak broken
                streak.current_streak = 1
            
            streak.last_activity_date = datetime.utcnow()
            streak.tasks_this_week += tasks_completed
            streak.time_this_week += time_spent
