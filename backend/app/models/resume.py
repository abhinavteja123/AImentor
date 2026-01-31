"""
Resume Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.postgres import Base


class Resume(Base):
    """User resume with versions."""
    
    __tablename__ = "resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Resume sections
    summary = Column(Text, nullable=True)
    skills_section = Column(JSONB, nullable=True)  # Grouped skills with proficiency
    projects_section = Column(JSONB, nullable=True)  # List of projects
    experience_section = Column(JSONB, nullable=True)  # Work experience
    education_section = Column(JSONB, nullable=True)  # Education details
    certifications_section = Column(JSONB, nullable=True)  # Certifications
    
    # Contact info
    contact_info = Column(JSONB, nullable=True)
    
    # Tailoring
    tailored_for = Column(String(255), nullable=True)  # Job title if tailored
    match_score = Column(Integer, nullable=True)  # 0-100
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    
    def __repr__(self):
        return f"<Resume {self.user_id} v{self.version}>"
