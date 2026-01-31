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
from app.schemas.resume import (
    ResumeUpdateRequest,
    ATSOptimizationRequest,
    ATSOptimizationResponse,
    MissingSection,
    ResumeValidationResponse
)
from app.services.ai.llm_client import LLMClient


class ResumeService:
    """Service for resume operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_client = LLMClient()
    
    async def _generate_summary(self, user: User, skills_section: dict, resume: Resume = None) -> str:
        """Generate AI-powered professional summary."""
        try:
            # Collect context about the user
            context_parts = [f"Target Role: {user.profile.goal_role}"]
            context_parts.append(f"Experience Level: {user.profile.experience_level}")
            
            # Add skills context
            if skills_section:
                all_skills = []
                for category, skills in skills_section.items():
                    all_skills.extend([s["name"] for s in skills])
                if all_skills:
                    context_parts.append(f"Skills: {', '.join(all_skills[:10])}")
            
            # Add resume context if available
            if resume:
                if resume.projects_section:
                    context_parts.append(f"Projects: {len(resume.projects_section)} completed")
                if resume.experience_section:
                    context_parts.append(f"Experience: {len(resume.experience_section)} positions")
                if resume.certifications_section:
                    context_parts.append(f"Certifications: {len(resume.certifications_section)} earned")
            
            context = "\\n".join(context_parts)
            
            prompt = f"""You are an expert resume writer. Create a compelling professional summary (2-3 sentences) for a resume.

Context:
{context}

Requirements:
1. Highlight key strengths and career goals
2. Include quantifiable achievements if available
3. Use strong action words
4. Be ATS-friendly with relevant keywords
5. Keep it concise (2-3 sentences, max 100 words)
6. Make it impactful and professional

Return ONLY the professional summary text, no additional formatting or explanation."""
            
            summary = await self.llm_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=150
            )
            
            # Clean up the response
            summary = summary.strip().strip('"').strip("'")
            return summary
            
        except Exception as e:
            # Fallback to simple summary
            return f"Aspiring {user.profile.goal_role} with a passion for learning and technology."
    
    async def get_current_resume(self, user_id: UUID) -> Optional[Resume]:
        """Get current active resume."""
        result = await self.db.execute(
            select(Resume)
            .where(
                Resume.user_id == user_id,
                Resume.is_active == True
            )
            .order_by(Resume.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def generate_initial_resume(self, user_id: UUID) -> Resume:
        """Generate initial resume from profile and skills, or return existing one with data."""
        # Check if resume already exists with data
        existing_resume = await self.get_current_resume(user_id)
        if existing_resume:
            # If resume has substantial data (projects, experience, etc), return it
            has_data = (
                (existing_resume.projects_section and len(existing_resume.projects_section) > 0) or
                (existing_resume.experience_section and len(existing_resume.experience_section) > 0) or
                (existing_resume.technical_skills_section is not None) or
                (existing_resume.certifications_section and len(existing_resume.certifications_section) > 0)
            )
            if has_data:
                return existing_resume
        
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
        
        # If existing resume exists, update it instead of creating new
        if existing_resume:
            existing_resume.summary = await self._generate_summary(user, skills_section, existing_resume)
            existing_resume.skills_section = skills_section
            if not existing_resume.education_section or len(existing_resume.education_section) == 0:
                existing_resume.education_section = [{
                    "institution": user.profile.current_education or "University",
                    "degree": "Bachelor's",
                    "graduation_year": user.profile.graduation_year
                }] if user.profile.current_education else []
            if not existing_resume.contact_info:
                existing_resume.contact_info = {
                    "email": user.email,
                    "linkedin_url": user.profile.linkedin_url,
                    "github_url": user.profile.github_url,
                    "portfolio_url": user.profile.portfolio_url
                }
            existing_resume.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing_resume)
            return existing_resume
        
        # Create new resume with AI-generated summary
        summary = await self._generate_summary(user, skills_section)
        
        resume = Resume(
            user_id=user_id,
            version=1,
            is_active=True,
            summary=summary,
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
        """Update resume sections, create if doesn't exist."""
        resume = await self.get_current_resume(user_id)
        
        # If no resume exists, create a basic one first
        if not resume:
            # Get user info for basic resume creation
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
            
            resume = Resume(
                user_id=user_id,
                version=1,
                is_active=True,
                summary="",
                contact_info={"email": user.email}
            )
            self.db.add(resume)
            await self.db.flush()
        
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
    
    async def validate_resume_data(self, user_id: UUID) -> ResumeValidationResponse:
        """Validate if user has all necessary data for a complete resume."""
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
        
        missing_sections = []
        
        # Check Education
        if not user.profile.current_education:
            missing_sections.append(MissingSection(
                section_name="education",
                is_required=True,
                prompt="Please provide your education details including institution name, degree, field of study, CGPA/percentage, and years attended.",
                fields=["institution", "degree", "field_of_study", "start_year", "end_year", "cgpa", "location"]
            ))
        
        # Check Experience/Internships
        resume = await self.get_current_resume(user_id)
        if not resume or not resume.experience_section or len(resume.experience_section) == 0:
            missing_sections.append(MissingSection(
                section_name="experience",
                is_required=False,
                prompt="Add your work experience or internships including company name, role, location, dates, and key achievements (bullet points).",
                fields=["company", "role", "location", "start_date", "end_date", "bullet_points", "company_url"]
            ))
        
        # Check Projects
        if not resume or not resume.projects_section or len(resume.projects_section) == 0:
            missing_sections.append(MissingSection(
                section_name="projects",
                is_required=True,
                prompt="Add your projects including project name, description, technologies used, dates, and key highlights/achievements (bullet points).",
                fields=["title", "description", "technologies", "start_date", "end_date", "highlights", "github_url", "demo_url"]
            ))
        
        # Check Technical Skills
        if not resume or not resume.technical_skills_section:
            missing_sections.append(MissingSection(
                section_name="technical_skills",
                is_required=True,
                prompt="List your technical skills grouped by: Languages (Python, Java, etc.), Frameworks & Tools (React, Docker, etc.), Databases, Cloud Platforms, and Other.",
                fields=["languages", "frameworks_and_tools", "databases", "cloud_platforms", "other"]
            ))
        
        # Check Certifications
        if not resume or not resume.certifications_section or len(resume.certifications_section) == 0:
            missing_sections.append(MissingSection(
                section_name="certifications",
                is_required=False,
                prompt="Add your certifications including name, issuer, date obtained, and credential URL if available.",
                fields=["name", "issuer", "date_obtained", "credential_url"]
            ))
        
        # Check Contact Information
        if not user.email:
            missing_sections.append(MissingSection(
                section_name="contact",
                is_required=True,
                prompt="Provide your contact information: email, phone number, location, and professional links (LinkedIn, GitHub, Portfolio).",
                fields=["email", "phone", "location", "linkedin_url", "github_url", "portfolio_url", "website"]
            ))
        
        # Check Extracurricular Activities
        if not resume or not resume.extracurricular_section or len(resume.extracurricular_section) == 0:
            missing_sections.append(MissingSection(
                section_name="extracurricular",
                is_required=False,
                prompt="Add extracurricular activities including organization name, your role, dates, location, and key achievements.",
                fields=["organization", "role", "start_date", "end_date", "location", "achievements"]
            ))
        
        total_sections = 7
        completed_sections = total_sections - len(missing_sections)
        completion_percentage = int((completed_sections / total_sections) * 100)
        
        return ResumeValidationResponse(
            is_complete=len(missing_sections) == 0,
            missing_sections=missing_sections,
            completion_percentage=completion_percentage
        )
    
    async def optimize_section_for_ats(
        self, 
        user_id: UUID,
        request: ATSOptimizationRequest
    ) -> ATSOptimizationResponse:
        """Optimize a resume section for ATS using AI."""
        # Get user profile for context
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
        
        target_role = request.target_role or user.profile.goal_role or "Software Developer"
        
        # Create ATS optimization prompt
        prompt = f"""You are an expert ATS (Applicant Tracking System) resume optimizer and career coach.

Target Role: {target_role}
Section Type: {request.section_type}

Original Content:
{request.content}

Task: Optimize this resume section to be ATS-friendly and impactful. Follow these guidelines:
1. Use strong action verbs (Developed, Implemented, Led, Achieved, etc.)
2. Include quantifiable metrics and achievements
3. Add relevant keywords for {target_role} role
4. Keep bullet points concise (1-2 lines each)
5. Use industry-standard terminology
6. Ensure proper formatting for ATS parsing

Return a JSON object with:
{{
    "optimized_content": {{the optimized version maintaining the same structure}},
    "improvements": [list of 3-5 specific improvements made],
    "ats_score": score from 0-100,
    "keywords_added": [list of relevant keywords added]
}}"""
        
        try:
            response = await self.llm_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse response (assuming JSON format)
            import json
            result_data = json.loads(response)
            
            return ATSOptimizationResponse(
                optimized_content=result_data.get("optimized_content", request.content),
                improvements=result_data.get("improvements", []),
                ats_score=result_data.get("ats_score", 75),
                keywords_added=result_data.get("keywords_added", [])
            )
        except Exception as e:
            # Fallback if AI fails
            return ATSOptimizationResponse(
                optimized_content=request.content,
                improvements=["Use more action verbs", "Add quantifiable metrics", "Include relevant keywords"],
                ats_score=60,
                keywords_added=[]
            )
    # ==================== VERSION MANAGEMENT ====================
    
    async def get_version_by_id(self, user_id: UUID, version_id: UUID) -> Optional[Resume]:
        """Get a specific version of a resume by ID."""
        result = await self.db.execute(
            select(Resume)
            .where(
                Resume.user_id == user_id,
                Resume.id == version_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_versions(self, user_id: UUID) -> List[dict]:
        """Get all resume versions for a user with metadata."""
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )
        resumes = result.scalars().all()
        
        return [
            {
                "id": str(r.id),
                "version": r.version,
                "draft_name": r.draft_name or f"Version {r.version}",
                "is_active": r.is_active,
                "is_base_version": r.is_base_version if hasattr(r, 'is_base_version') else True,
                "tailored_for": r.tailored_for,
                "match_score": r.match_score,
                "job_description": r.job_description if hasattr(r, 'job_description') else None,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat()
            }
            for r in resumes
        ]
    
    async def create_draft(
        self, 
        user_id: UUID, 
        draft_name: str,
        job_description: Optional[str] = None,
        base_version_id: Optional[UUID] = None
    ) -> Resume:
        """Create a new draft by cloning an existing version or active resume."""
        # Get the base version to clone
        if base_version_id:
            base_resume = await self.get_version_by_id(user_id, base_version_id)
        else:
            base_resume = await self.get_current_resume(user_id)
        
        if not base_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found to create draft from"
            )
        
        # Get the next version number
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.version.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        next_version = (latest.version if latest else 0) + 1
        
        # Create new draft (clone the base resume)
        new_draft = Resume(
            user_id=user_id,
            version=next_version,
            is_active=False,  # New drafts are not active by default
            draft_name=draft_name,
            is_base_version=False,
            parent_version_id=base_resume.id,
            job_description=job_description,
            summary=base_resume.summary,
            skills_section=base_resume.skills_section,
            coursework_section=base_resume.coursework_section,
            projects_section=base_resume.projects_section,
            experience_section=base_resume.experience_section,
            education_section=base_resume.education_section,
            certifications_section=base_resume.certifications_section,
            extracurricular_section=base_resume.extracurricular_section,
            technical_skills_section=base_resume.technical_skills_section,
            contact_info=base_resume.contact_info,
            tailored_for=None,
            match_score=None
        )
        
        self.db.add(new_draft)
        await self.db.commit()
        await self.db.refresh(new_draft)
        
        # If job description provided, tailor the summary
        if job_description:
            await self._tailor_draft_for_job(new_draft, job_description)
        
        return new_draft
    
    async def _tailor_draft_for_job(self, draft: Resume, job_description: str) -> None:
        """Tailor a draft's summary for a specific job description."""
        try:
            prompt = f"""You are an expert resume writer. Rewrite this professional summary to be tailored for the following job description.

Current Summary:
{draft.summary}

Job Description:
{job_description}

Requirements:
1. Highlight skills and experiences that match the job requirements
2. Use keywords from the job description
3. Keep it concise (2-3 sentences)
4. Be ATS-friendly

Return ONLY the tailored summary text, no additional formatting."""

            tailored_summary = await self.llm_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=200
            )
            
            draft.summary = tailored_summary.strip().strip('"').strip("'")
            draft.tailored_for = job_description[:100] + "..." if len(job_description) > 100 else job_description
            draft.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(draft)
        except Exception as e:
            # If AI fails, keep original summary
            pass
    
    async def set_active_version(self, user_id: UUID, version_id: UUID) -> Resume:
        """Set a specific version as the active resume."""
        # First, check if the version exists and belongs to user
        version = await self.get_version_by_id(user_id, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Deactivate all other versions
        await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
        )
        result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        all_resumes = result.scalars().all()
        for r in all_resumes:
            r.is_active = False
        
        # Activate the selected version
        version.is_active = True
        version.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(version)
        
        return version
    
    async def delete_version(self, user_id: UUID, version_id: UUID) -> bool:
        """Delete a specific version. Cannot delete the only/active version."""
        version = await self.get_version_by_id(user_id, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Check if this is the only version
        result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        all_versions = result.scalars().all()
        
        if len(all_versions) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only resume version"
            )
        
        # If deleting active version, make another version active
        if version.is_active:
            for v in all_versions:
                if v.id != version_id:
                    v.is_active = True
                    break
        
        await self.db.delete(version)
        await self.db.commit()
        
        return True
    
    async def update_draft_metadata(
        self,
        user_id: UUID,
        version_id: UUID,
        draft_name: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> Resume:
        """Update draft name and/or job description."""
        version = await self.get_version_by_id(user_id, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        if draft_name:
            version.draft_name = draft_name
        if job_description:
            version.job_description = job_description
            # Optionally re-tailor for the new JD
            await self._tailor_draft_for_job(version, job_description)
        
        version.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(version)
        
        return version
    
    async def regenerate_resume(
        self,
        user_id: UUID,
        version_id: Optional[UUID] = None,
        regenerate_summary: bool = True,
        regenerate_from_profile: bool = False
    ) -> Resume:
        """Regenerate resume content, optionally from profile data."""
        # Get the version to regenerate
        if version_id:
            resume = await self.get_version_by_id(user_id, version_id)
        else:
            resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found"
            )
        
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
        
        if regenerate_from_profile:
            # Pull fresh data from user skills
            result = await self.db.execute(
                select(UserSkill)
                .options(selectinload(UserSkill.skill))
                .where(UserSkill.user_id == user_id)
            )
            user_skills = result.scalars().all()
            
            # Rebuild skills section
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
            
            resume.skills_section = skills_section
            
            # Update contact info
            resume.contact_info = {
                "email": user.email,
                "linkedin_url": user.profile.linkedin_url,
                "github_url": user.profile.github_url,
                "portfolio_url": user.profile.portfolio_url
            }
        
        if regenerate_summary:
            # Regenerate summary using AI
            resume.summary = await self._generate_summary(user, resume.skills_section, resume)
        
        resume.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(resume)
        
        return resume
    
    async def update_version_sections(
        self,
        user_id: UUID,
        version_id: UUID,
        updates: ResumeUpdateRequest
    ) -> Resume:
        """Update specific sections of a version."""
        version = await self.get_version_by_id(user_id, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(version, field, value)
        
        version.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(version)
        
        return version