"""
Skill Models - Skills Master and User Skills
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Float, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..database.postgres import Base


class SkillMaster(Base):
    """Master skills database - all available skills."""
    
    __tablename__ = "skills_master"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # frontend, backend, database, devops, etc.
    subcategory = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    difficulty_level = Column(Integer, default=1)  # 1-5
    market_demand_score = Column(Float, default=0.5)  # 0-1
    related_skills = Column(ARRAY(String), nullable=True)
    learning_resources = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill")
    
    def __repr__(self):
        return f"<SkillMaster {self.skill_name}>"


class UserSkill(Base):
    """User's skills with proficiency levels."""
    
    __tablename__ = "user_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills_master.id"), nullable=False)
    
    proficiency_level = Column(Integer, default=1)  # 1-5
    target_proficiency = Column(Integer, default=3)
    acquired_date = Column(Date, nullable=True)
    last_practiced = Column(DateTime, nullable=True)
    practice_hours = Column(Float, default=0)
    confidence_rating = Column(Integer, default=1)  # 1-5
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="skills")
    skill = relationship("SkillMaster", back_populates="user_skills")
    
    def __repr__(self):
        return f"<UserSkill {self.user_id} - {self.skill_id}>"


class RoleTemplate(Base):
    """Role templates with required skills for different career paths."""
    
    __tablename__ = "role_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(255), unique=True, nullable=False, index=True)
    level = Column(String(50), nullable=True)  # junior, mid, senior
    description = Column(Text, nullable=True)
    
    # Required skills with minimum proficiency
    required_skills = Column(JSONB, nullable=False)  # [{"skill_id": ..., "min_proficiency": 3}]
    preferred_skills = Column(JSONB, nullable=True)
    responsibilities = Column(ARRAY(String), nullable=True)
    
    # Market data
    average_salary_range = Column(String(100), nullable=True)
    demand_score = Column(Float, default=0.5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RoleTemplate {self.role_name}>"
