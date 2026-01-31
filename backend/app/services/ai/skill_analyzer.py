"""
Skill Analyzer - AI-powered skill gap analysis with Gemini
"""

import logging
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.skill import SkillMaster, UserSkill, RoleTemplate
from ...models.profile import UserProfile
from .llm_client import get_llm_client

logger = logging.getLogger(__name__)


class SkillAnalyzer:
    """AI-powered skill gap analyzer using Gemini."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
    
    async def analyze_skill_gap(
        self,
        user_id: UUID,
        target_role: str
    ) -> Dict[str, Any]:
        """
        Comprehensive AI-powered skill gap analysis.
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
                "skill_name": us.skill.skill_name if us.skill else "Unknown",
                "category": us.skill.category if us.skill else "other",
                "proficiency_level": us.proficiency_level,
                "target_proficiency": us.target_proficiency,
                "practice_hours": us.practice_hours or 0,
                "confidence_rating": us.confidence_rating or 1
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
        
        # Get required skills for role (from template or generate with AI)
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
                    "importance": importance,
                    "learning_resources": req_skill.get("resources", [])
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
                        "importance": importance,
                        "learning_resources": req_skill.get("resources", [])
                    })
                else:
                    strength_areas.append(user_skill["skill_name"])
        
        # Sort by severity and importance
        missing_skills.sort(key=lambda x: (
            0 if x["importance"] == "required" else 1,
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["gap_severity"], 4)
        ))
        skills_to_improve.sort(key=lambda x: (
            0 if x["importance"] == "required" else 1,
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["gap_severity"], 4)
        ))
        
        # Calculate overall readiness
        total_required = len([s for s in required_skills if s.get("importance") == "required"])
        met_requirements = len([s for s in strength_areas])
        required_met = sum(1 for s in current_skill_names 
                          for r in required_skills 
                          if r.get("skill_name", "").lower() == s 
                          and r.get("importance") == "required"
                          and current_skill_map.get(s, {}).get("proficiency_level", 0) >= r.get("min_proficiency", 3))
        
        overall_readiness = (required_met / total_required * 100) if total_required > 0 else 0
        
        # Estimate time to ready
        total_weeks = sum(s["estimated_learning_weeks"] for s in missing_skills if s["importance"] == "required")
        total_weeks += sum(s["estimated_learning_weeks"] for s in skills_to_improve if s["importance"] == "required")
        
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
        
        # Generate learning path
        learning_path = await self._generate_learning_path(
            missing_skills=missing_skills,
            skills_to_improve=skills_to_improve,
            target_role=target_role
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
            "ai_insights": ai_insights,
            "learning_path": learning_path
        }
    
    async def get_skill_recommendations(self, user_id: UUID) -> Dict[str, Any]:
        """Get AI-powered skill recommendations."""
        # Get user's current skills
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = result.scalars().all()
        current_skill_names = [us.skill.skill_name for us in user_skills if us.skill]
        
        # Get user profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        goal_role = profile.goal_role if profile else None
        
        system_prompt = """You are an expert career advisor and skills strategist. 
Analyze the user's current skills and career goals to recommend the most impactful skills to learn.
Consider market demand, skill synergies, and career progression.
Return JSON format only."""
        
        user_prompt = f"""Based on this profile, recommend 5-8 skills to learn:

Current Skills: {current_skill_names if current_skill_names else "No skills added yet"}
Career Goal: {goal_role or "Not specified"}

Return JSON with format:
{{
  "recommended_skills": [
    {{
      "skill_name": "Skill Name",
      "category": "category_name",
      "reason": "Why this skill is recommended",
      "priority": "high|medium|low",
      "market_demand": 0.85,
      "learning_time_weeks": 4,
      "related_to": ["existing_skill_1"]
    }}
  ],
  "market_insights": {{
    "trending_tech": ["tech1", "tech2"],
    "emerging_roles": ["role1"],
    "industry_shifts": "Brief insight about industry direction"
  }},
  "personalized_message": "Encouraging personalized advice based on their profile"
}}

Focus on practical, in-demand skills that complement their existing skillset."""
        
        try:
            result = await self.llm.generate_json(system_prompt, user_prompt)
            return {
                "recommended_skills": result.get("recommended_skills", []),
                "based_on_goal": goal_role,
                "based_on_current_skills": current_skill_names,
                "market_insights": result.get("market_insights", {}),
                "personalized_message": result.get("personalized_message", "Keep learning and growing!")
            }
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "recommended_skills": [
                    {"skill_name": "Python", "category": "backend", "reason": "Versatile and in-demand", "priority": "high", "market_demand": 0.9, "learning_time_weeks": 6},
                    {"skill_name": "JavaScript", "category": "frontend", "reason": "Essential for web development", "priority": "high", "market_demand": 0.9, "learning_time_weeks": 6},
                    {"skill_name": "Git", "category": "tools", "reason": "Required for all development work", "priority": "high", "market_demand": 0.95, "learning_time_weeks": 2},
                ],
                "based_on_goal": goal_role,
                "based_on_current_skills": current_skill_names,
                "market_insights": {"trending_tech": ["AI/ML", "Cloud", "TypeScript"]},
                "personalized_message": "Start with foundational skills and build from there!"
            }
    
    async def generate_skill_assessment(self, skill_name: str) -> Dict[str, Any]:
        """Generate an AI-powered skill assessment."""
        system_prompt = """You are a technical interviewer and skill assessor.
Generate assessment questions to evaluate proficiency in a specific skill.
Return JSON format only."""
        
        user_prompt = f"""Create a skill assessment for: {skill_name}

Return JSON with format:
{{
  "skill_name": "{skill_name}",
  "assessment_type": "knowledge_check",
  "questions": [
    {{
      "id": 1,
      "question": "Question text",
      "difficulty": "beginner|intermediate|advanced",
      "type": "multiple_choice|open_ended",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Why this is correct"
    }}
  ],
  "proficiency_mapping": {{
    "0-2": "beginner",
    "3-4": "intermediate", 
    "5-6": "advanced",
    "7+": "expert"
  }},
  "recommended_resources": [
    {{"title": "Resource name", "type": "course|book|tutorial", "url": "optional"}}
  ]
}}

Include 5-7 questions of varying difficulty."""
        
        try:
            return await self.llm.generate_json(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error generating assessment: {e}")
            return {
                "skill_name": skill_name,
                "error": "Could not generate assessment",
                "questions": []
            }
    
    async def compare_roles(self, role1: str, role2: str) -> Dict[str, Any]:
        """Compare skill requirements between two roles."""
        system_prompt = """You are a career advisor comparing job roles.
Analyze the skill requirements and differences between two career paths.
Return JSON format only."""
        
        user_prompt = f"""Compare these two roles:
Role 1: {role1}
Role 2: {role2}

Return JSON with format:
{{
  "role1": {{
    "name": "{role1}",
    "core_skills": ["skill1", "skill2"],
    "average_salary_range": "$X - $Y",
    "career_outlook": "description"
  }},
  "role2": {{
    "name": "{role2}",
    "core_skills": ["skill1", "skill2"],
    "average_salary_range": "$X - $Y",
    "career_outlook": "description"
  }},
  "common_skills": ["shared skills"],
  "unique_to_role1": ["skills unique to first role"],
  "unique_to_role2": ["skills unique to second role"],
  "transition_difficulty": "easy|moderate|challenging",
  "transition_path": "How to move from one to the other",
  "recommendation": "Personalized advice on which might be better"
}}"""
        
        try:
            return await self.llm.generate_json(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error comparing roles: {e}")
            return {
                "error": "Could not compare roles",
                "role1": {"name": role1},
                "role2": {"name": role2}
            }
    
    async def _generate_required_skills(self, target_role: str) -> List[Dict]:
        """Generate required skills for a role using AI."""
        system_prompt = """You are a career advisor and industry expert.
Generate comprehensive skill requirements for a job role based on current market demands.
Return a JSON array with skill objects."""
        
        user_prompt = f"""Generate the required skills for the role: {target_role}

Return JSON array with format:
[
  {{
    "skill_name": "Skill Name",
    "category": "frontend|backend|database|devops|mobile|ai_ml|data_science|soft_skills|tools|other",
    "min_proficiency": 3,
    "importance": "required|preferred",
    "resources": [
      {{"title": "Resource name", "type": "course|book|tutorial", "url": "optional"}}
    ]
  }}
]

Include 10-15 skills covering:
- 5-7 core technical skills (required)
- 3-4 additional technical skills (preferred)
- 2-3 soft skills (required)

Be specific and practical based on real job market requirements."""
        
        try:
            result = await self.llm.generate_json(system_prompt, user_prompt)
            return result if isinstance(result, list) else result.get("skills", [])
        except Exception as e:
            logger.error(f"Error generating skills: {e}")
            return self._get_default_skills(target_role)
    
    def _get_default_skills(self, target_role: str) -> List[Dict]:
        """Return default skills based on common role patterns."""
        role_lower = target_role.lower()
        
        if "frontend" in role_lower or "react" in role_lower:
            return [
                {"skill_name": "JavaScript", "category": "frontend", "min_proficiency": 4, "importance": "required"},
                {"skill_name": "React", "category": "frontend", "min_proficiency": 4, "importance": "required"},
                {"skill_name": "TypeScript", "category": "frontend", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "CSS/SCSS", "category": "frontend", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "HTML", "category": "frontend", "min_proficiency": 4, "importance": "required"},
                {"skill_name": "Git", "category": "tools", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Testing", "category": "tools", "min_proficiency": 3, "importance": "preferred"},
                {"skill_name": "Problem Solving", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Communication", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
            ]
        elif "backend" in role_lower or "python" in role_lower:
            return [
                {"skill_name": "Python", "category": "backend", "min_proficiency": 4, "importance": "required"},
                {"skill_name": "SQL", "category": "database", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "REST APIs", "category": "backend", "min_proficiency": 4, "importance": "required"},
                {"skill_name": "Git", "category": "tools", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Docker", "category": "devops", "min_proficiency": 2, "importance": "preferred"},
                {"skill_name": "Problem Solving", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
            ]
        elif "full" in role_lower and "stack" in role_lower:
            return [
                {"skill_name": "JavaScript", "category": "frontend", "min_proficiency": 4, "importance": "required"},
                {"skill_name": "React/Vue/Angular", "category": "frontend", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Node.js", "category": "backend", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "SQL", "category": "database", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Git", "category": "tools", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "REST APIs", "category": "backend", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Problem Solving", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
            ]
        else:
            return [
                {"skill_name": "Programming Fundamentals", "category": "other", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Problem Solving", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Communication", "category": "soft_skills", "min_proficiency": 3, "importance": "required"},
                {"skill_name": "Git", "category": "tools", "min_proficiency": 2, "importance": "preferred"},
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
        system_prompt = """You are an encouraging, knowledgeable career mentor using AI.
Analyze the skill gap and provide actionable, personalized insights.
Be positive but realistic. Use specific numbers and timeframes.
Return JSON format only."""
        
        user_prompt = f"""Analyze this skill gap for a {experience_level} professional aiming for {target_role}:

Current Skills Count: {len(current_skills)}
Current Skills: {[s.get("skill_name") for s in current_skills[:10]]}
Missing Critical Skills: {[s.get("skill_name") for s in missing_skills if s.get("importance") == "required"][:5]}
Skills Needing Improvement: {[s.get("skill_name") for s in skills_to_improve][:5]}
Strengths: {strength_areas[:5]}
Overall Readiness: {overall_readiness:.1f}%

Return JSON with:
{{
  "summary": "One paragraph personalized assessment",
  "encouraging_observations": ["specific positive observation 1", "observation 2", "observation 3"],
  "top_priority_skills": [
    {{"skill": "name", "reason": "why important", "quick_start": "how to begin"}}
  ],
  "learning_strategy": {{
    "approach": "recommended learning approach",
    "daily_commitment": "suggested hours per day",
    "milestones": ["week 1-2 goal", "week 3-4 goal", "month 2 goal"]
  }},
  "timeline_assessment": "realistic timeline message with specific weeks/months",
  "quick_wins": ["easy win 1 with timeframe", "easy win 2"],
  "potential_blockers": ["common challenge 1", "challenge 2"],
  "motivation_boost": "Personalized encouraging message"
}}"""
        
        try:
            return await self.llm.generate_json(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "summary": f"You're making progress toward becoming a {target_role}. With focused effort, you can bridge the skill gaps.",
                "encouraging_observations": [
                    f"You've already built a foundation with {len(current_skills)} skills!",
                    "Every expert was once a beginner - you're on the right path.",
                    f"Your readiness of {overall_readiness:.0f}% shows real progress."
                ],
                "top_priority_skills": [
                    {"skill": missing_skills[0]["skill_name"], "reason": "Core requirement for the role", "quick_start": "Start with official documentation and tutorials"} 
                ] if missing_skills else [],
                "learning_strategy": {
                    "approach": "Focus on one skill at a time, practice daily",
                    "daily_commitment": "1-2 hours",
                    "milestones": ["Complete basics in 2 weeks", "Build a small project by week 4"]
                },
                "timeline_assessment": f"With consistent effort of 1-2 hours daily, you can be job-ready in approximately {max(8, len(missing_skills) * 3)} weeks.",
                "quick_wins": ["Complete one tutorial this week", "Set up your development environment"],
                "potential_blockers": ["Information overload - stay focused", "Imposter syndrome - it's normal!"],
                "motivation_boost": "Remember: every line of code you write brings you closer to your goal. You've got this! 🚀"
            }
    
    async def _generate_learning_path(
        self,
        missing_skills: List[Dict],
        skills_to_improve: List[Dict],
        target_role: str
    ) -> List[Dict]:
        """Generate a structured learning path."""
        all_skills = missing_skills + skills_to_improve
        if not all_skills:
            return []
        
        # Sort by importance and severity
        priority_skills = sorted(
            all_skills,
            key=lambda x: (
                0 if x.get("importance") == "required" else 1,
                {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("gap_severity", "medium"), 2)
            )
        )[:8]  # Top 8 skills
        
        system_prompt = """You are a learning path designer.
Create a structured, week-by-week learning path for the given skills.
Return JSON format only."""
        
        skills_list = [s["skill_name"] for s in priority_skills]
        user_prompt = f"""Create a learning path for these skills for {target_role}:
Skills: {skills_list}

Return JSON array:
[
  {{
    "week": 1,
    "focus_skill": "Primary skill to focus on",
    "secondary_skills": ["skill that can be learned alongside"],
    "goals": ["specific goal 1", "goal 2"],
    "projects": ["mini project idea"],
    "resources": [{{"title": "Resource", "type": "course|tutorial|book"}}],
    "estimated_hours": 10
  }}
]

Create 4-8 weeks of learning path. Be practical and achievable."""
        
        try:
            return await self.llm.generate_json(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Error generating learning path: {e}")
            # Return basic path
            path = []
            for i, skill in enumerate(priority_skills[:6], 1):
                path.append({
                    "week": i,
                    "focus_skill": skill["skill_name"],
                    "goals": [f"Learn fundamentals of {skill['skill_name']}", "Complete practice exercises"],
                    "estimated_hours": skill.get("estimated_learning_weeks", 2) * 5
                })
            return path
    
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
        # More realistic estimate: 2-3 weeks per proficiency level
        return gap * 2.5
