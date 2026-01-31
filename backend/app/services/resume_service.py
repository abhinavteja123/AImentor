"""
Resume Service
"""

from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
import io

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume
from app.models.user import User
from app.models.profile import UserProfile
from app.models.skill import UserSkill, SkillMaster
from app.schemas.resume import ResumeUpdateRequest


class ResumeService:
    """Service for resume operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_current_resume(self, user_id: UUID) -> Optional[Resume]:
        """Get current active resume."""
        result = await self.db.execute(
            select(Resume)
            .where(
                Resume.user_id == user_id,
                Resume.is_active == True
            )
            .order_by(Resume.version.desc())
        )
        return result.scalar_one_or_none()
    
    async def generate_initial_resume(self, user_id: UUID) -> Resume:
        """Generate initial resume from profile and skills."""
        # Get user with profile
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complete onboarding first"
            )
        
        # Get user skills
        result = await self.db.execute(
            select(UserSkill)
            .options(selectinload(UserSkill.skill))
            .where(UserSkill.user_id == user_id)
        )
        user_skills = result.scalars().all()
        
        # Group skills by category
        skills_section = {}
        for us in user_skills:
            category = us.skill.category
            if category not in skills_section:
                skills_section[category] = []
            skills_section[category].append({
                "name": us.skill.skill_name,
                "proficiency": us.proficiency_level,
                "category": category
            })
        
        # Create resume
        resume = Resume(
            user_id=user_id,
            version=1,
            is_active=True,
            summary=f"Aspiring {user.profile.goal_role} with a passion for learning and technology.",
            skills_section=skills_section,
            education_section=[{
                "institution": user.profile.current_education or "University",
                "degree": "Bachelor's",
                "graduation_year": user.profile.graduation_year
            }] if user.profile.current_education else [],
            contact_info={
                "email": user.email,
                "linkedin_url": user.profile.linkedin_url,
                "github_url": user.profile.github_url,
                "portfolio_url": user.profile.portfolio_url
            }
        )
        
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        
        return resume
    
    async def update_resume(
        self, 
        user_id: UUID, 
        updates: ResumeUpdateRequest
    ) -> Resume:
        """Update resume sections."""
        resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found"
            )
        
        # Update fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(resume, field, value)
        
        resume.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(resume)
        
        return resume
    
    async def tailor_resume_to_job(
        self, 
        user_id: UUID, 
        job_description: str
    ) -> dict:
        """Tailor resume to job description."""
        resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found"
            )
        
        # Extract keywords from job description (simplified)
        keywords = set(job_description.lower().split())
        
        # Match skills
        matched_skills = []
        if resume.skills_section:
            for category, skills in resume.skills_section.items():
                for skill in skills:
                    if skill["name"].lower() in job_description.lower():
                        matched_skills.append(skill["name"])
        
        # Calculate match score
        match_score = min(100, len(matched_skills) * 10)
        
        return {
            "tailored_summary": f"Experienced professional with skills in {', '.join(matched_skills[:5])}.",
            "matched_skills": matched_skills,
            "relevant_projects": [],
            "match_score": match_score,
            "missing_skills": [],
            "suggestions": [
                "Add more projects showcasing your skills",
                "Include quantifiable achievements"
            ]
        }
    
    async def export_resume(
        self, 
        user_id: UUID, 
        format: str = "pdf"
    ) -> Tuple[io.BytesIO, str, str]:
        """Export resume as PDF or DOCX."""
        resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found"
            )
        
        # For now, return a simple text representation
        # In production, use libraries like reportlab for PDF
        content = io.BytesIO()
        content.write(f"Resume\n{resume.summary}\n".encode())
        content.seek(0)
        
        if format == "pdf":
            return content, "resume.pdf", "application/pdf"
        else:
            return content, "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    async def get_versions(self, user_id: UUID) -> List[dict]:
        """Get all resume versions."""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.version.desc())
        )
        resumes = result.scalars().all()
        
        return [
            {
                "id": str(r.id),
                "version": r.version,
                "is_active": r.is_active,
                "tailored_for": r.tailored_for,
                "created_at": r.created_at
            }
            for r in resumes
        ]
