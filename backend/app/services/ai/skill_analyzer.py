"""
Skill Analyzer - AI-powered skill gap analysis
"""

import logging
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.skill import SkillMaster, UserSkill, RoleTemplate
from app.models.profile import UserProfile
from app.services.ai.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class SkillAnalyzer:
    """AI-powered skill gap analyzer."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
    
    async def analyze_skill_gap(
        self,
        user_id: UUID,
        target_role: str
    ) -> Dict[str, Any]:
        """
        Analyze skill gap between user's current skills and target role.
        """
        # Get user's current skills
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = result.scalars().all()
        
        current_skills = [
            {
                "id": str(us.id),
                "skill_id": str(us.skill_id),
                "skill_name": us.skill.skill_name,
                "category": us.skill.category,
                "proficiency_level": us.proficiency_level,
                "target_proficiency": us.target_proficiency,
                "practice_hours": us.practice_hours,
                "confidence_rating": us.confidence_rating
            }
            for us in user_skills
        ]
        
        # Get user profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        # Try to get role template
        result = await self.db.execute(
            select(RoleTemplate).where(
                RoleTemplate.role_name.ilike(f"%{target_role}%")
            )
        )
        role_template = result.scalar_one_or_none()
        
        # Get required skills for role (from template or generate)
        if role_template and role_template.required_skills:
            required_skills = role_template.required_skills
        else:
            required_skills = await self._generate_required_skills(target_role)
        
        # Compare skills
        missing_skills = []
        skills_to_improve = []
        strength_areas = []
        
        current_skill_names = {s["skill_name"].lower() for s in current_skills}
        current_skill_map = {s["skill_name"].lower(): s for s in current_skills}
        
        for req_skill in required_skills:
            skill_name = req_skill.get("skill_name", "").lower()
            min_prof = req_skill.get("min_proficiency", 3)
            importance = req_skill.get("importance", "required")
            
            if skill_name not in current_skill_names:
                missing_skills.append({
                    "skill_name": req_skill.get("skill_name"),
                    "skill_id": None,
                    "category": req_skill.get("category", "other"),
                    "required_proficiency": min_prof,
                    "current_proficiency": 0,
                    "gap_severity": "critical" if importance == "required" else "medium",
                    "estimated_learning_weeks": self._estimate_learning_time(0, min_prof),
                    "importance": importance
                })
            else:
                user_skill = current_skill_map[skill_name]
                if user_skill["proficiency_level"] < min_prof:
                    skills_to_improve.append({
                        "skill_name": req_skill.get("skill_name"),
                        "skill_id": user_skill["skill_id"],
                        "category": req_skill.get("category", user_skill["category"]),
                        "required_proficiency": min_prof,
                        "current_proficiency": user_skill["proficiency_level"],
                        "gap_severity": self._calculate_severity(
                            user_skill["proficiency_level"], 
                            min_prof
                        ),
                        "estimated_learning_weeks": self._estimate_learning_time(
                            user_skill["proficiency_level"], 
                            min_prof
                        ),
                        "importance": importance
                    })
                else:
                    strength_areas.append(user_skill["skill_name"])
        
        # Calculate overall readiness
        total_required = len(required_skills)
        met_requirements = len(strength_areas)
        overall_readiness = (met_requirements / total_required * 100) if total_required > 0 else 0
        
        # Estimate time to ready
        total_weeks = sum(s["estimated_learning_weeks"] for s in missing_skills)
        total_weeks += sum(s["estimated_learning_weeks"] for s in skills_to_improve)
        
        # Generate AI insights
        ai_insights = await self._generate_ai_insights(
            target_role=target_role,
            current_skills=current_skills,
            missing_skills=missing_skills,
            skills_to_improve=skills_to_improve,
            strength_areas=strength_areas,
            overall_readiness=overall_readiness,
            experience_level=profile.experience_level if profile else "beginner"
        )
        
        return {
            "target_role": target_role,
            "required_skills": required_skills,
            "current_skills": current_skills,
            "missing_skills": missing_skills,
            "skills_to_improve": skills_to_improve,
            "strength_areas": strength_areas,
            "overall_readiness": round(overall_readiness, 1),
            "estimated_time_to_ready": int(total_weeks),
            "ai_insights": ai_insights
        }
    
    async def _generate_required_skills(self, target_role: str) -> List[Dict]:
        """Generate required skills for a role using AI."""
        system_prompt = """You are a career advisor. Generate the required skills for a job role.
Return a JSON array with skill objects."""
        
        user_prompt = f"""Generate the required skills for the role: {target_role}

Return JSON array with format:
[
  {{
    "skill_name": "Skill Name",
    "category": "frontend|backend|database|devops|soft_skills|other",
    "min_proficiency": 3,
    "importance": "required|preferred"
  }}
]

Include 8-12 skills covering technical and soft skills."""
        
        try:
            result = await self.llm.generate_json(system_prompt, user_prompt)
            return result if isinstance(result, list) else result.get("skills", [])
        except Exception as e:
            logger.error(f"Error generating skills: {e}")
            # Return default skills
            return [
                {"skill_name": "Problem Solving", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Communication", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Python", "category": "backend", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "JavaScript", "category": "frontend", "min_proficiency": 3, "importance": "required"},
            ]
    
    async def _generate_ai_insights(
        self,
        target_role: str,
        current_skills: List[Dict],
        missing_skills: List[Dict],
        skills_to_improve: List[Dict],
        strength_areas: List[str],
        overall_readiness: float,
        experience_level: str
    ) -> Dict[str, Any]:
        """Generate AI insights about the skill gap."""
        system_prompt = """You are an encouraging career mentor. 
Analyze the skill gap and provide actionable insights.
Be positive but realistic. Return JSON format."""
        
        user_prompt = f"""Analyze this skill gap for a {experience_level} aiming for {target_role}:

Current Skills: {len(current_skills)}
Missing Skills: {[s.get("skill_name") for s in missing_skills]}
Skills to Improve: {[s.get("skill_name") for s in skills_to_improve]}
Strengths: {strength_areas}
Overall Readiness: {overall_readiness}%

Return JSON with:
{{
  "encouraging_observations": ["observation1", "observation2"],
  "top_priority_skills": [
    {{"skill": "name", "reason": "why important"}}
  ],
  "learning_strategy": "recommended approach",
  "timeline_assessment": "realistic timeline message",
  "quick_wins": ["easy wins to build momentum"]
}}"""
        
        try:
            return await self.llm.generate_json(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "encouraging_observations": [
                    f"You've already made progress with {len(current_skills)} skills!",
                    "Every expert was once a beginner."
                ],
                "top_priority_skills": [
                    {"skill": missing_skills[0]["skill_name"], "reason": "Core requirement"} 
                ] if missing_skills else [],
                "learning_strategy": "Focus on fundamentals first, then specialize.",
                "timeline_assessment": f"With consistent effort, you can be job-ready in {int(len(missing_skills) * 2)} weeks.",
                "quick_wins": ["Complete one small project to build confidence"]
            }
    
    def _calculate_severity(self, current: int, required: int) -> str:
        """Calculate gap severity."""
        gap = required - current
        if gap >= 3:
            return "critical"
        elif gap == 2:
            return "high"
        elif gap == 1:
            return "medium"
        return "low"
    
    def _estimate_learning_time(self, current: int, target: int) -> float:
        """Estimate learning time in weeks."""
        gap = target - current
        if gap <= 0:
            return 0
        # Rough estimate: 2 weeks per proficiency level
        return gap * 2.0
