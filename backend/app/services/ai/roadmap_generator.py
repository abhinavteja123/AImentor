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

from ...models.roadmap import Roadmap, RoadmapTask
from ...models.profile import UserProfile
from .llm_client import get_llm_client
from .skill_analyzer import SkillAnalyzer

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
        logger.info(f"Starting roadmap generation for user {user_id}")
        logger.info(f"Input target_role: '{target_role}', duration: {duration_weeks} weeks, intensity: {intensity}")
        
        # Get user profile first
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            logger.info(f"Found user profile - goal_role: '{profile.goal_role}', experience: '{profile.experience_level}'")
        else:
            logger.warning(f"No user profile found for user {user_id}")
        
        # Validate and resolve target_role
        if not target_role or target_role.strip() == "" or target_role.lower() == "none":
            logger.info("Target role not provided in request, checking profile...")
            if profile and profile.goal_role and profile.goal_role.lower() != "none":
                target_role = profile.goal_role
                logger.info(f"Using goal_role from profile: '{target_role}'")
            else:
                raise ValueError(
                    "Target role is required. Please complete your profile with your career goal first."
                )
        
        logger.info(f"Final target_role for roadmap: '{target_role}'")
        
        # Get skill gap analysis
        skill_analysis = await self.skill_analyzer.analyze_skill_gap(
            user_id, target_role
        )
        logger.info(f"Skill analysis: missing={len(skill_analysis.get('missing_skills', []))}, "
                   f"to_improve={len(skill_analysis.get('skills_to_improve', []))}")
        
        # Determine daily time based on intensity
        daily_minutes = self._get_daily_minutes(intensity, profile)
        logger.info(f"Daily learning time: {daily_minutes} minutes")
        
        # Generate roadmap structure using AI
        roadmap_data = await self._generate_roadmap_structure(
            target_role=target_role,
            duration_weeks=duration_weeks,
            daily_minutes=daily_minutes,
            skill_analysis=skill_analysis,
            experience_level=profile.experience_level if profile else "beginner",
            learning_style=profile.preferred_learning_style if profile else "mixed"
        )
        
        logger.info(f"Generated roadmap data with title: {roadmap_data.get('roadmap_title', 'N/A')}")
        
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
        
        logger.info(f"Generating roadmap for target_role: {target_role}")
        logger.info(f"Parameters: duration={duration_weeks} weeks, daily_minutes={daily_minutes}, experience={experience_level}")
        
        # Get skills to learn based on target role
        missing_skills = [s["skill_name"] for s in skill_analysis.get("missing_skills", [])]
        skills_to_improve = [s["skill_name"] for s in skill_analysis.get("skills_to_improve", [])]
        
        # If no skills analysis available, generate role-specific skills
        if not missing_skills:
            missing_skills = self._get_default_skills_for_role(target_role)
            logger.info(f"Using default skills for {target_role}: {missing_skills}")
        
        system_prompt = f"""You are an expert career mentor and technical educator. 
Your task is to create a detailed, practical learning roadmap for someone aspiring to become a {target_role}.
You must return ONLY valid JSON - no explanations, no markdown, just the JSON object."""
        
        user_prompt = f"""Create a comprehensive {duration_weeks}-week learning roadmap for becoming a **{target_role}**.

## User Profile:
- **Target Career Goal**: {target_role}
- **Experience Level**: {experience_level}
- **Daily Learning Time**: {daily_minutes} minutes
- **Preferred Learning Style**: {learning_style}

## Skills to Master:
{', '.join(missing_skills[:8]) if missing_skills else 'Core skills for ' + target_role}

## Skills to Improve:
{', '.join(skills_to_improve[:4]) if skills_to_improve else 'Foundational skills'}

## Current Readiness: {skill_analysis.get("overall_readiness", 0)}%

## Requirements for the Roadmap:
1. **Week 1**: Foundation - Basic concepts, environment setup, first small exercises
2. **Week 2**: Core Skills - Dive deeper into fundamental technologies
3. **Week 3**: Intermediate - More complex topics, small projects
4. **Week 4**: Applied Learning - Larger project, real-world applications

Each week should have 5-6 days with 2-3 tasks per day.
Each task should fit within {daily_minutes // 2} to {daily_minutes} minutes.

Include actual learning resources with real URLs from:
- Official documentation (docs.python.org, developer.mozilla.org, etc.)
- FreeCodeCamp, Codecademy, W3Schools
- YouTube tutorials (specific channel recommendations)
- GitHub repositories for practice

Return this exact JSON structure:
{{
  "roadmap_title": "Your Journey to Becoming a {target_role}",
  "description": "A personalized {duration_weeks}-week learning path tailored for {experience_level} level learners",
  "weekly_breakdown": [
    {{
      "week_number": 1,
      "focus_area": "Foundations & Setup",
      "learning_objectives": ["Set up development environment", "Understand basic concepts"],
      "days": [
        {{
          "day_number": 1,
          "tasks": [
            {{
              "title": "Specific task title",
              "description": "Detailed description of what to learn and why it matters for a {target_role}",
              "task_type": "reading",
              "estimated_duration": {daily_minutes // 2},
              "difficulty": 2,
              "learning_objectives": ["objective1", "objective2"],
              "success_criteria": "You can explain X and do Y",
              "prerequisites": [],
              "resources": [
                {{"title": "Resource Name", "url": "https://actual-url.com", "type": "documentation"}}
              ]
            }}
          ]
        }}
      ]
    }}
  ],
  "milestones": [
    {{
      "week_number": 2,
      "title": "First Mini Project",
      "description": "Build something practical",
      "skills_demonstrated": ["skill1", "skill2"],
      "deliverable": "Working code/project"
    }}
  ]
}}

Generate exactly 4 weeks with detailed, actionable content specific to becoming a {target_role}."""

        try:
            logger.info("Calling LLM for roadmap generation...")
            result = await self.llm.generate_json(system_prompt, user_prompt)
            
            # Validate the response has required structure
            if "weekly_breakdown" not in result or not result["weekly_breakdown"]:
                logger.warning("LLM response missing weekly_breakdown, using default")
                return self._generate_default_roadmap(target_role, duration_weeks, daily_minutes)
            
            logger.info(f"Successfully generated roadmap with {len(result.get('weekly_breakdown', []))} weeks")
            return result
            
        except Exception as e:
            logger.error(f"Error generating roadmap with AI: {str(e)}", exc_info=True)
            logger.info("Falling back to default roadmap generation")
            return self._generate_default_roadmap(target_role, duration_weeks, daily_minutes)
    
    def _get_default_skills_for_role(self, target_role: str) -> List[str]:
        """Get default skills based on target role."""
        role_lower = target_role.lower()
        
        skill_mappings = {
            "frontend": ["HTML", "CSS", "JavaScript", "React", "TypeScript", "Responsive Design", "Git"],
            "backend": ["Python", "Node.js", "Databases", "REST APIs", "SQL", "Authentication", "Git"],
            "fullstack": ["HTML/CSS", "JavaScript", "React", "Node.js", "Databases", "REST APIs", "Git", "Deployment"],
            "data scientist": ["Python", "Pandas", "NumPy", "Machine Learning", "SQL", "Data Visualization", "Statistics"],
            "data analyst": ["SQL", "Excel", "Python", "Data Visualization", "Statistics", "Tableau/PowerBI"],
            "devops": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS/Azure", "Terraform", "Scripting"],
            "machine learning": ["Python", "TensorFlow/PyTorch", "Mathematics", "Statistics", "Deep Learning", "Data Processing"],
            "mobile": ["React Native", "Flutter", "iOS/Android", "Mobile UI/UX", "APIs", "App Store Deployment"],
            "cloud": ["AWS", "Azure", "GCP", "Networking", "Security", "IaC", "Serverless"],
            "cybersecurity": ["Network Security", "Ethical Hacking", "Cryptography", "Security Tools", "Compliance", "Incident Response"],
        }
        
        # Try to match the role
        for key, skills in skill_mappings.items():
            if key in role_lower:
                return skills
        
        # Default generic tech skills
        return ["Programming Fundamentals", "Problem Solving", "Git Version Control", "Documentation", "Best Practices", "Testing"]
    
    def _generate_default_roadmap(
        self, 
        target_role: str, 
        duration_weeks: int,
        daily_minutes: int
    ) -> Dict[str, Any]:
        """Generate a default roadmap structure when AI fails."""
        logger.info(f"Generating default roadmap for: {target_role}")
        
        # Get skills for the role
        skills = self._get_default_skills_for_role(target_role)
        
        weekly_breakdown = []
        week_focus = [
            ("Foundation & Setup", "Set up your development environment and learn the basics"),
            ("Core Concepts", "Deep dive into fundamental concepts and patterns"),
            ("Intermediate Skills", "Build on foundations with more complex topics"),
            ("Applied Learning", "Apply your skills in a practical project")
        ]
        
        for week in range(1, min(duration_weeks + 1, 5)):
            days = []
            focus_title, focus_desc = week_focus[week - 1] if week <= 4 else (f"Week {week} Focus", "Continue building skills")
            
            # Get skills for this week
            week_skills = skills[(week-1)*2:week*2] if len(skills) >= week*2 else skills[:2]
            
            for day in range(1, 6):  # 5 days per week
                task_types = ["reading", "reading", "coding", "coding", "project"]
                task_type = task_types[day - 1]
                
                tasks = []
                
                # First task - learning
                skill_focus = week_skills[0] if week_skills else "Core Skills"
                tasks.append({
                    "title": f"Learn {skill_focus}" if day <= 2 else f"Practice {skill_focus}",
                    "description": f"{'Study the fundamentals of' if day <= 2 else 'Apply your knowledge of'} {skill_focus} for {target_role} development",
                    "task_type": task_type,
                    "estimated_duration": daily_minutes // 2,
                    "difficulty": 1 + week,
                    "learning_objectives": [f"Understand {skill_focus} basics", f"Apply {skill_focus} concepts"],
                    "success_criteria": f"Complete the {skill_focus} exercises and understand the core concepts",
                    "prerequisites": [] if week == 1 else [f"Week {week-1} completed"],
                    "resources": [
                        {
                            "title": f"{skill_focus} Documentation",
                            "url": "https://developer.mozilla.org/en-US/docs/Learn",
                            "type": "documentation"
                        }
                    ]
                })
                
                # Second task for some days
                if day in [3, 4, 5] and len(week_skills) > 1:
                    skill_focus2 = week_skills[1] if len(week_skills) > 1 else skill_focus
                    tasks.append({
                        "title": f"{'Hands-on' if day <= 4 else 'Mini Project:'} {skill_focus2}",
                        "description": f"Build practical experience with {skill_focus2}",
                        "task_type": "coding" if day <= 4 else "project",
                        "estimated_duration": daily_minutes // 2,
                        "difficulty": 2 + week // 2,
                        "learning_objectives": [f"Practice {skill_focus2}", "Build something useful"],
                        "success_criteria": f"Complete a working example using {skill_focus2}",
                        "prerequisites": [tasks[0]["title"]],
                        "resources": [
                            {
                                "title": f"{skill_focus2} Tutorial",
                                "url": "https://www.freecodecamp.org/learn",
                                "type": "tutorial"
                            }
                        ]
                    })
                
                days.append({
                    "day_number": day,
                    "tasks": tasks
                })
            
            weekly_breakdown.append({
                "week_number": week,
                "focus_area": f"{focus_title}: {', '.join(week_skills)}" if week_skills else focus_title,
                "learning_objectives": [
                    f"Master {week_skills[0]}" if week_skills else "Learn fundamentals",
                    focus_desc
                ],
                "days": days
            })
        
        return {
            "roadmap_title": f"Your Path to Becoming a {target_role}",
            "description": f"A personalized {duration_weeks}-week learning journey to help you become a {target_role}. "
                          f"This roadmap covers: {', '.join(skills[:4])}",
            "weekly_breakdown": weekly_breakdown,
            "milestones": [
                {
                    "week_number": 2,
                    "title": "First Working Project",
                    "description": f"Build your first mini-project as a {target_role}",
                    "skills_demonstrated": skills[:2],
                    "deliverable": "A small working project demonstrating basic skills"
                },
                {
                    "week_number": 4,
                    "title": "Portfolio Project",
                    "description": "Complete a project you can show to employers",
                    "skills_demonstrated": skills[:4],
                    "deliverable": "A complete project for your portfolio"
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
        logger.info(f"Regenerating roadmap {roadmap_id} for user {user_id}")
        
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
        
        logger.info(f"Old roadmap target_role: '{old_roadmap.target_role}'")
        
        # ALWAYS get the current target_role from profile (user may have changed their goal)
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        # Use profile's goal_role if available, otherwise fall back to old roadmap's target_role
        if profile and profile.goal_role and profile.goal_role.lower() != "none":
            target_role = profile.goal_role
            logger.info(f"Using profile's goal_role: '{target_role}'")
        elif old_roadmap.target_role and old_roadmap.target_role.lower() != "none":
            target_role = old_roadmap.target_role
            logger.info(f"Falling back to old roadmap's target_role: '{target_role}'")
        else:
            raise ValueError(
                "Cannot regenerate roadmap: No valid career goal found. Please update your profile first."
            )
        
        # Mark old as abandoned
        old_roadmap.status = "abandoned"
        
        # Generate new with adjustments
        params = old_roadmap.generation_params or {}
        if adjustments:
            params.update(adjustments)
        
        logger.info(f"Generating new roadmap with target_role: '{target_role}'")
        
        new_roadmap = await self.generate_roadmap(
            user_id=user_id,
            target_role=target_role,
            duration_weeks=old_roadmap.total_weeks,
            intensity=params.get("intensity", "medium")
        )
        
        await self.db.commit()
        
        return new_roadmap
