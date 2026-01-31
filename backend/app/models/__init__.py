"""
Models package initialization
Import all models here for easy access
"""

from app.models.user import User
from app.models.profile import UserProfile
from app.models.skill import SkillMaster, UserSkill, RoleTemplate
from app.models.roadmap import Roadmap, RoadmapTask
from app.models.progress import ProgressLog, Achievement, UserStreak
from app.models.resume import Resume

__all__ = [
    "User",
    "UserProfile", 
    "SkillMaster",
    "UserSkill",
    "RoleTemplate",
    "Roadmap",
    "RoadmapTask",
    "ProgressLog",
    "Achievement",
    "UserStreak",
    "Resume"
]
