"""
Roadmap Service
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.roadmap import Roadmap, RoadmapTask


class RoadmapService:
    """Service for roadmap operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_current_roadmap(self, user_id: UUID) -> Optional[Roadmap]:
        """Get user's current active roadmap."""
        result = await self.db.execute(
            select(Roadmap)
            .options(selectinload(Roadmap.tasks))
            .where(
                Roadmap.user_id == user_id,
                Roadmap.status == "active"
            )
            .order_by(Roadmap.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_roadmap(
        self, 
        roadmap_id: UUID, 
        user_id: UUID
    ) -> Optional[Roadmap]:
        """Get specific roadmap."""
        result = await self.db.execute(
            select(Roadmap)
            .options(selectinload(Roadmap.tasks))
            .where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_roadmaps(self, user_id: UUID) -> List[Roadmap]:
        """Get all user's roadmaps."""
        result = await self.db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .order_by(Roadmap.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_week_tasks(
        self, 
        roadmap_id: UUID, 
        week_number: int,
        user_id: UUID
    ) -> dict:
        """Get tasks for a specific week."""
        # Verify roadmap belongs to user
        roadmap = await self.get_roadmap(roadmap_id, user_id)
        if not roadmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap not found"
            )
        
        # Get week tasks
        result = await self.db.execute(
            select(RoadmapTask)
            .where(
                RoadmapTask.roadmap_id == roadmap_id,
                RoadmapTask.week_number == week_number
            )
            .order_by(RoadmapTask.day_number, RoadmapTask.order_in_day)
        )
        tasks = result.scalars().all()
        
        # Group by day
        days = {}
        for task in tasks:
            if task.day_number not in days:
                days[task.day_number] = []
            days[task.day_number].append(task)
        
        day_list = []
        for day_number in sorted(days.keys()):
            day_tasks = days[day_number]
            day_list.append({
                "day_number": day_number,
                "tasks": day_tasks,
                "total_duration": sum(t.estimated_duration for t in day_tasks),
                "completed_count": sum(1 for t in day_tasks if t.status == "completed")
            })
        
        # Calculate stats
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        
        return {
            "week_number": week_number,
            "focus_area": roadmap.milestones[week_number - 1]["title"] if roadmap.milestones and len(roadmap.milestones) >= week_number else f"Week {week_number}",
            "learning_objectives": [],
            "days": day_list,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    async def update_roadmap_progress(self, roadmap_id: UUID):
        """Recalculate and update roadmap progress."""
        result = await self.db.execute(
            select(RoadmapTask).where(RoadmapTask.roadmap_id == roadmap_id)
        )
        tasks = result.scalars().all()
        
        if not tasks:
            return
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        
        result = await self.db.execute(
            select(Roadmap).where(Roadmap.id == roadmap_id)
        )
        roadmap = result.scalar_one_or_none()
        
        if roadmap:
            roadmap.completion_percentage = (completed / total * 100)
            roadmap.updated_at = datetime.utcnow()
            
            if roadmap.completion_percentage >= 100:
                roadmap.status = "completed"
            
            await self.db.commit()
