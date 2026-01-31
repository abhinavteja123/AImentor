"""
Roadmap Generator - AI-powered learning path generation
"""

import logging
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap, RoadmapTask
from app.models.profile import UserProfile
from app.services.ai.llm_client import get_llm_client
from app.services.ai.skill_analyzer import SkillAnalyzer

logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """AI-powered learning roadmap generator."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.skill_analyzer = SkillAnalyzer(db)
    
    async def generate_roadmap(
        self,
        user_id: UUID,
        target_role: str,
        duration_weeks: int = 12,
        intensity: str = "medium"
    ) -> Roadmap:
        """
        Generate a personalized learning roadmap.
        """
        # Validate target_role
        if not target_role or target_role.strip() == "" or target_role.lower() == "none":
            raise ValueError(
                "Target role is required. Please complete your profile with your career goal first."
            )
        
        # Get user profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        # Validate profile has required fields
        if profile:
            if not profile.goal_role or profile.goal_role.lower() == "none":
                raise ValueError(
                    "Your profile doesn't have a career goal set. Please update your profile first."
                )
            # Use profile's goal_role if available
            target_role = profile.goal_role
        
        # Get skill gap analysis
        skill_analysis = await self.skill_analyzer.analyze_skill_gap(
            user_id, target_role
        )
        
        # Determine daily time based on intensity
        daily_minutes = self._get_daily_minutes(intensity, profile)
        
        # Generate roadmap structure using AI
        roadmap_data = await self._generate_roadmap_structure(
            target_role=target_role,
            duration_weeks=duration_weeks,
            daily_minutes=daily_minutes,
            skill_analysis=skill_analysis,
            experience_level=profile.experience_level if profile else "beginner",
            learning_style=profile.preferred_learning_style if profile else "mixed"
        )
        
        # Create roadmap in database
        roadmap = Roadmap(
            user_id=user_id,
            title=roadmap_data.get("roadmap_title", f"{target_role} Learning Path"),
            description=roadmap_data.get("description", ""),
            target_role=target_role,
            total_weeks=duration_weeks,
            start_date=date.today(),
            end_date=date.today() + timedelta(weeks=duration_weeks),
            status="active",
            milestones=roadmap_data.get("milestones", []),
            generation_params={
                "intensity": intensity,
                "daily_minutes": daily_minutes
            }
        )
        
        self.db.add(roadmap)
        await self.db.flush()
        
        # Create tasks
        weekly_breakdown = roadmap_data.get("weekly_breakdown", [])
        for week_data in weekly_breakdown:
            week_num = week_data.get("week_number", 1)
            days = week_data.get("days", [])
            
            for day_data in days:
                day_num = day_data.get("day_number", 1)
                tasks = day_data.get("tasks", [])
                
                for order, task_data in enumerate(tasks, 1):
                    task = RoadmapTask(
                        roadmap_id=roadmap.id,
                        week_number=week_num,
                        day_number=day_num,
                        order_in_day=order,
                        task_title=task_data.get("title", "Learning Task"),
                        task_description=task_data.get("description", ""),
                        task_type=task_data.get("task_type", "reading"),
                        estimated_duration=task_data.get("estimated_duration", 60),
                        difficulty=task_data.get("difficulty", 3),
                        learning_objectives=task_data.get("learning_objectives", []),
                        success_criteria=task_data.get("success_criteria", ""),
                        prerequisites=task_data.get("prerequisites", []),
                        resources=task_data.get("resources", []),
                        status="pending"
                    )
                    self.db.add(task)
        
        await self.db.commit()
        
        # Refresh with tasks
        result = await self.db.execute(
            select(Roadmap)
            .options(selectinload(Roadmap.tasks))
            .where(Roadmap.id == roadmap.id)
        )
        return result.scalar_one()
    
    async def _generate_roadmap_structure(
        self,
        target_role: str,
        duration_weeks: int,
        daily_minutes: int,
        skill_analysis: Dict[str, Any],
        experience_level: str,
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate roadmap structure using AI."""
        
        system_prompt = """You are an expert career mentor creating personalized learning roadmaps.
Generate a detailed, week-by-week learning plan. Return valid JSON only."""
        
        missing_skills = [s["skill_name"] for s in skill_analysis.get("missing_skills", [])]
        skills_to_improve = [s["skill_name"] for s in skill_analysis.get("skills_to_improve", [])]
        
        user_prompt = f"""Create a {duration_weeks}-week learning roadmap for becoming a {target_role}.

User Profile:
- Experience Level: {experience_level}
- Daily Time Available: {daily_minutes} minutes
- Learning Style: {learning_style}

Skills to Learn: {missing_skills[:6]}
Skills to Improve: {skills_to_improve[:4]}
Current Readiness: {skill_analysis.get("overall_readiness", 0)}%

Requirements:
1. Prioritize critical skills first
2. Build foundational before advanced topics
3. Mix: 30% reading/theory, 50% practice/coding, 20% projects
4. Include milestone projects every 2-3 weeks
5. Add review days weekly
6. Realistic pacing for daily time limit

Return JSON:
{{
  "roadmap_title": "Title for this roadmap",
  "description": "Brief description",
  "weekly_breakdown": [
    {{
      "week_number": 1,
      "focus_area": "Focus topic",
      "learning_objectives": ["obj1", "obj2"],
      "days": [
        {{
          "day_number": 1,
          "tasks": [
            {{
              "title": "Task title",
              "description": "What to do and why",
              "task_type": "reading|coding|project|video|quiz",
              "estimated_duration": 60,
              "difficulty": 3,
              "success_criteria": "How to know you're done",
              "resources": [
                {{"title": "Resource", "url": "https://...", "type": "documentation"}}
              ]
            }}
          ]
        }}
      ]
    }}
  ],
  "milestones": [
    {{
      "week_number": 3,
      "title": "Milestone name",
      "description": "What to build/achieve",
      "skills_demonstrated": ["skill1"],
      "deliverable": "What to produce"
    }}
  ]
}}

Generate for first 4 weeks with 5-6 days each, 2-3 tasks per day fitting the {daily_minutes} minute limit."""

        try:
            result = await self.llm.generate_json(system_prompt, user_prompt)
            return result
        except Exception as e:
            logger.error(f"Error generating roadmap: {e}")
            return self._generate_default_roadmap(target_role, duration_weeks, daily_minutes)
    
    def _generate_default_roadmap(
        self, 
        target_role: str, 
        duration_weeks: int,
        daily_minutes: int
    ) -> Dict[str, Any]:
        """Generate a default roadmap structure."""
        weekly_breakdown = []
        
        for week in range(1, min(duration_weeks + 1, 5)):
            days = []
            for day in range(1, 6):  # 5 days per week
                days.append({
                    "day_number": day,
                    "tasks": [
                        {
                            "title": f"Week {week} Day {day} - Learning Task",
                            "description": f"Focus on core skills for {target_role}",
                            "task_type": "reading" if day <= 2 else "coding",
                            "estimated_duration": daily_minutes // 2,
                            "difficulty": 2 + (week // 2),
                            "success_criteria": "Complete the exercises",
                            "resources": []
                        }
                    ]
                })
            
            weekly_breakdown.append({
                "week_number": week,
                "focus_area": f"Week {week} Focus",
                "learning_objectives": ["Learn fundamentals", "Practice basics"],
                "days": days
            })
        
        return {
            "roadmap_title": f"Path to {target_role}",
            "description": f"A {duration_weeks}-week journey to becoming a {target_role}",
            "weekly_breakdown": weekly_breakdown,
            "milestones": [
                {
                    "week_number": 3,
                    "title": "First Project",
                    "description": "Build your first mini-project",
                    "skills_demonstrated": ["Core Skills"],
                    "deliverable": "Working project"
                }
            ]
        }
    
    def _get_daily_minutes(self, intensity: str, profile: Optional[UserProfile]) -> int:
        """Get daily learning minutes based on intensity."""
        if profile and profile.time_per_day:
            return profile.time_per_day
        
        intensity_map = {
            "low": 30,
            "medium": 60,
            "high": 120
        }
        return intensity_map.get(intensity, 60)
    
    async def regenerate_roadmap(
        self,
        user_id: UUID,
        roadmap_id: UUID,
        feedback: Optional[str] = None,
        adjustments: Optional[Dict] = None
    ) -> Roadmap:
        """Regenerate roadmap with user feedback."""
        # Get existing roadmap
        result = await self.db.execute(
            select(Roadmap).where(
                Roadmap.id == roadmap_id,
                Roadmap.user_id == user_id
            )
        )
        old_roadmap = result.scalar_one_or_none()
        
        if not old_roadmap:
            raise ValueError("Roadmap not found")
        
        # Validate target role
        if not old_roadmap.target_role or old_roadmap.target_role.lower() == "none":
            # Try to get from user profile
            profile_result = await self.db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = profile_result.scalar_one_or_none()
            
            if not profile or not profile.goal_role or profile.goal_role.lower() == "none":
                raise ValueError(
                    "Cannot regenerate roadmap: No valid career goal found. Please update your profile first."
                )
            
            old_roadmap.target_role = profile.goal_role
        
        # Mark old as abandoned
        old_roadmap.status = "abandoned"
        
        # Generate new with adjustments
        params = old_roadmap.generation_params or {}
        if adjustments:
            params.update(adjustments)
        
        new_roadmap = await self.generate_roadmap(
            user_id=user_id,
            target_role=old_roadmap.target_role,
            duration_weeks=old_roadmap.total_weeks,
            intensity=params.get("intensity", "medium")
        )
        
        await self.db.commit()
        
        return new_roadmap
