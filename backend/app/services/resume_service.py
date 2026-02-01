"""
Resume Service
"""

from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
import io
import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.resume import Resume
from ..models.user import User
from ..models.profile import UserProfile
from ..models.skill import UserSkill, SkillMaster
from ..schemas.resume import (
    ResumeUpdateRequest,
    ATSOptimizationRequest,
    ATSOptimizationResponse,
    MissingSection,
    ResumeValidationResponse
)
from .ai.llm_client import LLMClient
from .latex.latex_compiler import LaTeXResumeGenerator

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_client = LLMClient()
        self.latex_generator = LaTeXResumeGenerator()
    
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
    
    async def sync_from_profile(self, user_id: UUID) -> Resume:
        """Sync resume data from user profile."""
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
        
        profile = user.profile
        resume = await self.get_current_resume(user_id)
        
        if not resume:
            resume = Resume(
                user_id=user_id,
                version=1,
                is_active=True,
                summary="",
                contact_info={"email": user.email}
            )
            self.db.add(resume)
            await self.db.flush()
        
        # Sync data from profile to resume
        if profile.education_data:
            resume.education_section = profile.education_data
        
        if profile.experience_data:
            resume.experience_section = profile.experience_data
        
        if profile.projects_data:
            resume.projects_section = profile.projects_data
        
        if profile.certifications_data:
            resume.certifications_section = profile.certifications_data
        
        if profile.extracurricular_data:
            resume.extracurricular_section = profile.extracurricular_data
        
        if profile.technical_skills_data:
            resume.technical_skills_section = profile.technical_skills_data
        
        # Sync contact info
        resume.contact_info = {
            "email": user.email,
            "phone": profile.phone,
            "location": profile.location,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "portfolio_url": profile.portfolio_url,
            "website": profile.website_url
        }
        
        resume.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(resume)
        
        return resume
    
    async def tailor_resume_to_job(
        self, 
        user_id: UUID, 
        job_description: str
    ) -> dict:
        """Tailor resume to job description using AI."""
        resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found"
            )
        
        # Get user info
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        # Extract all skills from resume - handle various data formats
        all_skills = []
        
        # From skills_section
        if resume.skills_section:
            logger.info(f"Skills section type: {type(resume.skills_section)}, content: {resume.skills_section}")
            if isinstance(resume.skills_section, dict):
                for category, skills in resume.skills_section.items():
                    if isinstance(skills, list):
                        for skill in skills:
                            if isinstance(skill, dict):
                                all_skills.append(skill.get("name", skill.get("skill", "")))
                            else:
                                all_skills.append(str(skill))
                    elif isinstance(skills, str):
                        all_skills.extend([s.strip() for s in skills.split(',')])
            elif isinstance(resume.skills_section, list):
                for skill in resume.skills_section:
                    if isinstance(skill, dict):
                        all_skills.append(skill.get("name", skill.get("skill", "")))
                    else:
                        all_skills.append(str(skill))
        
        # From technical_skills_section
        if resume.technical_skills_section:
            logger.info(f"Technical skills section type: {type(resume.technical_skills_section)}, content: {resume.technical_skills_section}")
            if isinstance(resume.technical_skills_section, dict):
                for category, skills in resume.technical_skills_section.items():
                    if isinstance(skills, list):
                        all_skills.extend([str(s) for s in skills])
                    elif isinstance(skills, str):
                        all_skills.extend([s.strip() for s in skills.split(',')])
            elif isinstance(resume.technical_skills_section, list):
                all_skills.extend([str(s) for s in resume.technical_skills_section])
        
        # Also get skills from user profile if available
        if user and user.profile and user.profile.technical_skills_data:
            logger.info(f"Profile skills: {user.profile.technical_skills_data}")
            profile_skills = user.profile.technical_skills_data
            if isinstance(profile_skills, dict):
                for category, skills in profile_skills.items():
                    if isinstance(skills, list):
                        all_skills.extend([str(s) for s in skills])
                    elif isinstance(skills, str):
                        all_skills.extend([s.strip() for s in skills.split(',')])
            elif isinstance(profile_skills, list):
                all_skills.extend([str(s) for s in profile_skills])
        
        # Clean up skills list - remove empty strings and duplicates
        all_skills = list(set([s.strip() for s in all_skills if s and s.strip()]))
        logger.info(f"All extracted skills: {all_skills}")
        
        # Normalize job description for matching
        job_desc_lower = job_description.lower()
        job_words = set(job_desc_lower.split())
        
        # Extended tech keywords dictionary with variations
        tech_keywords_map = {
            'iot': ['iot', 'internet of things', 'embedded', 'sensors', 'mqtt', 'raspberry pi', 'arduino'],
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'scipy'],
            'java': ['java', 'spring', 'springboot', 'maven', 'gradle', 'hibernate'],
            'javascript': ['javascript', 'js', 'node', 'nodejs', 'express', 'react', 'vue', 'angular', 'typescript'],
            'machine learning': ['machine learning', 'ml', 'ai', 'aiml', 'artificial intelligence', 'deep learning', 'tensorflow', 'pytorch', 'neural network', 'nlp', 'computer vision', 'data science', 'python', 'scikit'],
            'cloud': ['cloud', 'aws', 'azure', 'gcp', 'google cloud', 'serverless', 'lambda', 'firebase', 's3', 'ec2'],
            'devops': ['devops', 'docker', 'kubernetes', 'k8s', 'ci/cd', 'jenkins', 'github actions', 'terraform'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'database', 'nosql', 'firebase', 'dynamodb'],
            'frontend': ['html', 'css', 'react', 'angular', 'vue', 'frontend', 'ui', 'ux', 'tailwind', 'bootstrap', 'nextjs', 'next.js'],
            'backend': ['backend', 'api', 'rest', 'graphql', 'microservices', 'node', 'express', 'fastapi', 'django', 'flask', 'python'],
            'mobile': ['mobile', 'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
            'data': ['data science', 'data analysis', 'data engineering', 'etl', 'spark', 'hadoop', 'analytics', 'python', 'pandas'],
            'security': ['security', 'cybersecurity', 'penetration testing', 'encryption', 'authentication'],
            'fullstack': ['full stack', 'fullstack', 'full-stack', 'mern', 'mean', 'web development', 'web developer', 'react', 'node', 'python', 'javascript', 'frontend', 'backend'],
            'blockchain': ['blockchain', 'web3', 'smart contracts', 'solidity', 'ethereum'],
        }
        
        # Find which tech categories are mentioned in the job
        job_categories = set()
        for category, keywords in tech_keywords_map.items():
            for keyword in keywords:
                # Check if keyword appears in job description
                if keyword in job_desc_lower or keyword.replace(' ', '') in job_desc_lower.replace(' ', ''):
                    job_categories.add(category)
                    break
            for keyword in keywords:
                if keyword in job_desc_lower:
                    job_categories.add(category)
                    break
        
        logger.info(f"Job description: {job_description}")
        logger.info(f"Job categories detected: {job_categories}")
        
        # Match skills against job description and categories
        matched_skills = []
        
        for skill in all_skills:
            if not skill:
                continue
            skill_lower = skill.lower().strip()
            
            # Direct match - skill name appears in job description
            if skill_lower in job_desc_lower:
                matched_skills.append(skill)
                logger.info(f"Direct match: {skill}")
                continue
            
            # Check if any word of job description matches skill
            for word in job_words:
                if len(word) > 2 and (word in skill_lower or skill_lower in word):
                    matched_skills.append(skill)
                    logger.info(f"Word match: {skill} matched {word}")
                    break
            else:
                # Check if skill matches any keyword in the job's categories
                for category in job_categories:
                    if category in tech_keywords_map:
                        category_keywords = tech_keywords_map[category]
                        if skill_lower in category_keywords or any(skill_lower in kw or kw in skill_lower for kw in category_keywords):
                            matched_skills.append(skill)
                            logger.info(f"Category match: {skill} in {category}")
                            break
        
        # Remove duplicates
        matched_skills = list(dict.fromkeys(matched_skills))
        logger.info(f"Final matched skills: {matched_skills}")
        
        # Find missing skills from job description
        missing_skills = []
        for category in job_categories:
            if category in tech_keywords_map:
                for keyword in tech_keywords_map[category]:
                    # Only suggest specific skills, not generic terms
                    if len(keyword) > 2 and keyword not in ['api', 'sql', 'ai', 'ml', 'ui', 'ux']:
                        has_skill = any(keyword in s.lower() or s.lower() in keyword for s in all_skills if s)
                        if not has_skill:
                            missing_skills.append(keyword.title())
        
        # Remove duplicates while preserving order
        missing_skills = list(dict.fromkeys(missing_skills))[:10]
        
        # Count how many job categories the user's skills cover
        user_categories_covered = set()
        for skill in all_skills:
            if not skill:
                continue
            skill_lower = skill.lower().strip()
            for category, keywords in tech_keywords_map.items():
                if category in job_categories:
                    # Check if user's skill matches any keyword in this category
                    if skill_lower in keywords or any(skill_lower in kw or kw in skill_lower for kw in keywords):
                        user_categories_covered.add(category)
                        logger.info(f"Skill '{skill}' covers category '{category}'")
                        break
        
        logger.info(f"User categories covered: {user_categories_covered}")
        
        # Calculate match score
        if job_categories:
            # Score based on how many required categories user has skills in
            category_match_ratio = len(user_categories_covered) / len(job_categories)
            base_score = int(category_match_ratio * 50)  # Max 50 from categories
            logger.info(f"Category ratio: {category_match_ratio}, base_score: {base_score}")
            
            # Bonus for direct skill matches (max 30)
            skill_bonus = min(30, len(matched_skills) * 8)
            logger.info(f"Skill bonus: {skill_bonus} from {len(matched_skills)} matched skills")
            
            # Bonus for resume completeness (max 20)
            completeness_bonus = 0
            if resume.experience_section and len(resume.experience_section) > 0:
                completeness_bonus += 7
            if resume.projects_section and len(resume.projects_section) > 0:
                completeness_bonus += 7
            if resume.education_section:
                completeness_bonus += 4
            if resume.certifications_section:
                completeness_bonus += 2
            
            match_score = min(100, base_score + skill_bonus + completeness_bonus)
        else:
            # Generic job description - score based on overall profile strength
            if all_skills:
                match_score = min(70, 30 + len(all_skills) * 2 + len(matched_skills) * 5)
            else:
                match_score = 20
        
        # Ensure minimum score if user has relevant skills
        if matched_skills and match_score < 30:
            match_score = 30 + min(40, len(matched_skills) * 10)
        
        # Ensure low score if no matches at all
        if not matched_skills and not user_categories_covered:
            match_score = min(match_score, 15)
        
        logger.info(f"Final match score: {match_score}")
        
        # Generate tailored summary and analysis using AI
        try:
            system_prompt = """You are an expert career coach and resume consultant. 
Analyze the job requirements and candidate's profile to provide personalized resume guidance.
Be specific, actionable, and encouraging in your responses."""

            user_prompt = f"""Analyze this job and candidate profile, then generate a tailored resume summary.

JOB DESCRIPTION/ROLE:
{job_description}

CANDIDATE'S SKILLS:
{', '.join(all_skills[:20]) if all_skills else 'Not specified'}

MATCHED SKILLS FOR THIS JOB:
{', '.join(matched_skills[:10]) if matched_skills else 'None directly matching'}

CANDIDATE'S GOAL ROLE:
{user.profile.goal_role if user and user.profile else 'Software Developer'}

CANDIDATE HAS:
- Experience: {'Yes' if resume.experience_section else 'No'}
- Projects: {len(resume.projects_section) if resume.projects_section else 0} projects
- Education: {'Yes' if resume.education_section else 'No'}
- Certifications: {'Yes' if resume.certifications_section else 'No'}

Please provide:
1. A compelling 2-3 sentence professional summary tailored for this job/role
2. Make sure to mention relevant skills from the candidate's profile
3. Focus on how the candidate can add value to this role

Return ONLY the summary text, no explanations or labels."""

            tailored_summary = await self.llm_client.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            # Clean up any extra formatting
            tailored_summary = tailored_summary.strip().strip('"').strip()
            
        except Exception as e:
            logger.warning(f"AI summary generation failed: {e}")
            # Better fallback summary based on actual matches
            if matched_skills:
                skills_text = ', '.join(matched_skills[:5])
                tailored_summary = f"Motivated professional with demonstrated expertise in {skills_text}. Eager to apply these skills to contribute effectively to {job_description[:50].strip()} roles and drive innovative solutions."
            elif all_skills:
                skills_text = ', '.join(all_skills[:5])
                tailored_summary = f"Versatile developer skilled in {skills_text}. While exploring new domains like {job_description[:30].strip()}, bringing strong problem-solving abilities and a passion for learning."
            else:
                tailored_summary = f"Dedicated professional eager to build expertise in {job_description[:50].strip()}. Committed to continuous learning and delivering quality results."
        
        # Generate dynamic suggestions based on actual analysis
        suggestions = []
        
        if not resume.summary:
            suggestions.append("Add a professional summary to your resume")
        
        if not matched_skills and missing_skills:
            suggestions.append(f"Your resume doesn't show skills for this role. Consider learning: {', '.join(missing_skills[:3])}")
        elif len(matched_skills) < 3 and missing_skills:
            suggestions.append(f"Strengthen your profile by adding: {', '.join(missing_skills[:3])}")
        
        if not resume.projects_section:
            suggestions.append(f"Add projects related to {job_description[:20].strip()} to demonstrate hands-on experience")
        elif len(resume.projects_section) < 2:
            suggestions.append("Add more projects showcasing your relevant skills")
        
        if not resume.experience_section:
            suggestions.append("Include internships, freelance work, or relevant experience")
        
        if match_score < 50:
            suggestions.append(f"Consider taking courses in {', '.join(missing_skills[:2])} to improve your match")
        
        suggestions.append("Include quantifiable achievements (e.g., 'improved performance by 30%')")
        suggestions.append("Use action verbs like 'developed', 'implemented', 'designed'")
        
        # Get relevant projects
        relevant_projects = []
        if resume.projects_section:
            for proj in resume.projects_section:
                proj_name = proj.get('title', '') or proj.get('name', '')
                proj_tech = proj.get('technologies', [])
                proj_desc = proj.get('description', '')
                
                if isinstance(proj_tech, list):
                    tech_str = ' '.join([str(t).lower() for t in proj_tech])
                else:
                    tech_str = str(proj_tech).lower()
                
                # Check if project is relevant to job
                proj_text = f"{proj_name} {tech_str} {proj_desc}".lower()
                if any(word in proj_text for word in job_desc_lower.split() if len(word) > 3):
                    relevant_projects.append(proj_name)
                elif matched_skills and any(skill.lower() in proj_text for skill in matched_skills):
                    relevant_projects.append(proj_name)
        
        return {
            "tailored_summary": tailored_summary.strip(),
            "matched_skills": matched_skills,
            "relevant_projects": relevant_projects[:5],
            "match_score": match_score,
            "missing_skills": missing_skills[:10],
            "suggestions": suggestions[:5]
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

    # ==================== EXPORT METHODS ====================
    
    async def export_resume_pdf(
        self, 
        user_id: UUID, 
        version_id: Optional[UUID] = None,
        template: str = "modern"
    ) -> dict:
        """
        Export resume to PDF using LaTeX compilation.
        
        Args:
            user_id: User ID
            version_id: Optional specific version ID (uses active if not provided)
            template: Template name (modern, classic, minimal)
            
        Returns:
            dict with pdf_data (base64 encoded), filename, and metadata
        """
        # Get the resume to export
        if version_id:
            resume = await self.get_version_by_id(user_id, version_id)
        else:
            resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Get user info for contact details
        result = await self.db.execute(
            select(User).options(
                selectinload(User.profile)
            ).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare resume data for LaTeX generation
        resume_data = self._prepare_resume_data_for_export(user, resume)
        
        try:
            # Generate PDF (sync operation)
            pdf_data, filename = self.latex_generator.generate_pdf(
                resume_data=resume_data,
                filename=f"resume_{resume.version}",
                template=template
            )
            
            import base64
            return {
                "pdf_data": base64.b64encode(pdf_data).decode('utf-8'),
                "filename": filename,
                "format": "pdf",
                "template": template,
                "version_id": str(resume.id),
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF generation failed: {str(e)}"
            )
    
    async def preview_latex(
        self, 
        user_id: UUID, 
        version_id: Optional[UUID] = None,
        template: str = "modern"
    ) -> dict:
        """
        Generate LaTeX source code preview for resume.
        
        Args:
            user_id: User ID
            version_id: Optional specific version ID
            template: Template name
            
        Returns:
            dict with latex_source and metadata
        """
        # Get the resume
        if version_id:
            resume = await self.get_version_by_id(user_id, version_id)
        else:
            resume = await self.get_current_resume(user_id)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Get user info
        result = await self.db.execute(
            select(User).options(
                selectinload(User.profile)
            ).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare resume data
        resume_data = self._prepare_resume_data_for_export(user, resume)
        
        # Generate LaTeX source
        latex_source = self.latex_generator.generate_complete_resume(resume_data)
        
        return {
            "latex_source": latex_source,
            "template": template,
            "version_id": str(resume.id),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def validate_latex(self, latex_content: str) -> dict:
        """
        Validate LaTeX content for syntax errors.
        
        Args:
            latex_content: Raw LaTeX source code
            
        Returns:
            dict with is_valid, errors, and warnings
        """
        errors = []
        warnings = []
        
        # Basic syntax validation
        open_braces = latex_content.count('{')
        close_braces = latex_content.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
        
        # Check for required document structure
        if '\\documentclass' not in latex_content:
            errors.append("Missing \\documentclass declaration")
        
        if '\\begin{document}' not in latex_content:
            errors.append("Missing \\begin{document}")
        
        if '\\end{document}' not in latex_content:
            errors.append("Missing \\end{document}")
        
        # Check for common issues
        import re
        
        # Check for unescaped special characters
        unescaped_patterns = [
            (r'(?<!\\)&(?!amp;)', "Unescaped '&' character found"),
            (r'(?<!\\)%(?!\s*$)', "Unescaped '%' character found"),
            (r'(?<!\\)\$(?!\$)', "Unescaped '$' character found"),
        ]
        
        for pattern, message in unescaped_patterns:
            if re.search(pattern, latex_content):
                warnings.append(message)
        
        # Check for balanced environments
        begin_matches = re.findall(r'\\begin\{(\w+)\}', latex_content)
        end_matches = re.findall(r'\\end\{(\w+)\}', latex_content)
        
        begin_counts = {}
        end_counts = {}
        for env in begin_matches:
            begin_counts[env] = begin_counts.get(env, 0) + 1
        for env in end_matches:
            end_counts[env] = end_counts.get(env, 0) + 1
        
        for env, count in begin_counts.items():
            end_count = end_counts.get(env, 0)
            if count != end_count:
                errors.append(f"Unbalanced environment '{env}': {count} begin, {end_count} end")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "latex_length": len(latex_content)
        }
    
    def _prepare_resume_data_for_export(self, user: User, resume: Resume) -> dict:
        """
        Prepare resume data in the format expected by LaTeX generator.
        
        Args:
            user: User model with profile
            resume: Resume model
            
        Returns:
            dict with all resume sections properly formatted
        """
        profile = user.profile
        
        # Build contact info
        contact_info = {
            "name": user.full_name or f"{user.email.split('@')[0]}",
            "email": user.email,
            "phone": getattr(profile, 'phone', None) or "",
            "location": getattr(profile, 'location', None) or "",
            "linkedin": getattr(profile, 'linkedin_url', None) or "",
            "github": getattr(profile, 'github_url', None) or "",
            "portfolio": getattr(profile, 'portfolio_url', None) or ""
        }
        
        # Process skills
        skills = []
        if resume.skills_section:
            for category, skill_list in resume.skills_section.items():
                if isinstance(skill_list, list):
                    for skill in skill_list:
                        if isinstance(skill, dict):
                            skills.append({
                                "name": skill.get("name", ""),
                                "category": category,
                                "proficiency": skill.get("proficiency", 3)
                            })
                        else:
                            skills.append({
                                "name": str(skill),
                                "category": category,
                                "proficiency": 3
                            })
        
        # Process education - map to LaTeX generator expected fields
        education = []
        if resume.education_section:
            for edu in resume.education_section:
                education.append({
                    "institution": edu.get("institution", ""),
                    "degree": edu.get("degree", ""),
                    "field_of_study": edu.get("field_of_study", "") or edu.get("field", ""),
                    "location": edu.get("location", ""),
                    "start_year": edu.get("start_year", ""),
                    "end_year": edu.get("end_year", "") or edu.get("graduation_year", ""),
                    "cgpa": edu.get("cgpa", "") or edu.get("gpa", ""),
                    "percentage": edu.get("percentage", "")
                })
        
        # Process experience - map to LaTeX generator expected fields
        experience = []
        if resume.experience_section:
            for exp in resume.experience_section:
                experience.append({
                    "company": exp.get("company", ""),
                    "role": exp.get("role", "") or exp.get("title", ""),
                    "location": exp.get("location", ""),
                    "start_date": exp.get("start_date", ""),
                    "end_date": exp.get("end_date", "Present"),
                    "bullet_points": exp.get("bullet_points", []) or exp.get("achievements", []) or exp.get("highlights", []),
                    "company_url": exp.get("company_url", "")
                })
        
        # Process projects - map to LaTeX generator expected fields
        projects = []
        if resume.projects_section:
            for proj in resume.projects_section:
                projects.append({
                    "title": proj.get("title", "") or proj.get("name", ""),
                    "description": proj.get("description", ""),
                    "technologies": proj.get("technologies", []),
                    "github_url": proj.get("github_url", ""),
                    "demo_url": proj.get("demo_url", "") or proj.get("url", ""),
                    "highlights": proj.get("highlights", []) or proj.get("achievements", []),
                    "start_date": proj.get("start_date", ""),
                    "end_date": proj.get("end_date", "")
                })
        
        # Process certifications - map to LaTeX generator expected fields
        certifications = []
        if resume.certifications_section:
            for cert in resume.certifications_section:
                certifications.append({
                    "name": cert.get("name", ""),
                    "issuer": cert.get("issuer", ""),
                    "date_obtained": cert.get("date_obtained", "") or cert.get("date", ""),
                    "credential_url": cert.get("credential_url", "") or cert.get("url", "")
                })
        
        # Process extracurricular - map to LaTeX generator expected fields
        extracurricular = []
        if resume.extracurricular_section:
            for ext in resume.extracurricular_section:
                extracurricular.append({
                    "organization": ext.get("organization", ""),
                    "role": ext.get("role", ""),
                    "location": ext.get("location", ""),
                    "start_date": ext.get("start_date", ""),
                    "end_date": ext.get("end_date", ""),
                    "achievements": ext.get("achievements", [])
                })
        
        return {
            "contact_info": contact_info,
            "summary": resume.summary or "",
            "skills_section": resume.skills_section or {},
            "education_section": education,
            "experience_section": experience,
            "projects_section": projects,
            "certifications_section": certifications,
            "technical_skills_section": resume.technical_skills_section or {},
            "coursework_section": resume.coursework_section or [],
            "extracurricular_section": extracurricular
        }