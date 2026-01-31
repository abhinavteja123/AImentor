"""
Seed Database Script
Populates the database with initial skills and role templates
"""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import AsyncSessionLocal, init_db
from app.models.skill import SkillMaster, RoleTemplate


# Skills data organized by category
SKILLS_DATA = [
    # Frontend
    {"skill_name": "HTML", "category": "frontend", "difficulty_level": 1, "market_demand_score": 0.9},
    {"skill_name": "CSS", "category": "frontend", "difficulty_level": 2, "market_demand_score": 0.9},
    {"skill_name": "JavaScript", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.95},
    {"skill_name": "TypeScript", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "React", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.95},
    {"skill_name": "Vue.js", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.8},
    {"skill_name": "Angular", "category": "frontend", "difficulty_level": 4, "market_demand_score": 0.75},
    {"skill_name": "Next.js", "category": "frontend", "difficulty_level": 4, "market_demand_score": 0.85},
    {"skill_name": "Tailwind CSS", "category": "frontend", "difficulty_level": 2, "market_demand_score": 0.85},
    {"skill_name": "SASS/SCSS", "category": "frontend", "difficulty_level": 2, "market_demand_score": 0.7},
    {"skill_name": "Redux", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.75},
    {"skill_name": "Webpack", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.6},
    {"skill_name": "Responsive Design", "category": "frontend", "difficulty_level": 2, "market_demand_score": 0.9},
    {"skill_name": "Web Accessibility", "category": "frontend", "difficulty_level": 3, "market_demand_score": 0.7},
    
    # Backend
    {"skill_name": "Python", "category": "backend", "difficulty_level": 2, "market_demand_score": 0.95},
    {"skill_name": "Node.js", "category": "backend", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "FastAPI", "category": "backend", "difficulty_level": 3, "market_demand_score": 0.8},
    {"skill_name": "Django", "category": "backend", "difficulty_level": 3, "market_demand_score": 0.75},
    {"skill_name": "Flask", "category": "backend", "difficulty_level": 2, "market_demand_score": 0.7},
    {"skill_name": "Express.js", "category": "backend", "difficulty_level": 3, "market_demand_score": 0.85},
    {"skill_name": "Java", "category": "backend", "difficulty_level": 4, "market_demand_score": 0.85},
    {"skill_name": "Spring Boot", "category": "backend", "difficulty_level": 4, "market_demand_score": 0.8},
    {"skill_name": "Go", "category": "backend", "difficulty_level": 4, "market_demand_score": 0.75},
    {"skill_name": "Ruby on Rails", "category": "backend", "difficulty_level": 3, "market_demand_score": 0.6},
    {"skill_name": "REST API Design", "category": "backend", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "GraphQL", "category": "backend", "difficulty_level": 4, "market_demand_score": 0.7},
    {"skill_name": "Microservices", "category": "backend", "difficulty_level": 4, "market_demand_score": 0.8},
    
    # Database
    {"skill_name": "PostgreSQL", "category": "database", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "MySQL", "category": "database", "difficulty_level": 2, "market_demand_score": 0.85},
    {"skill_name": "MongoDB", "category": "database", "difficulty_level": 3, "market_demand_score": 0.85},
    {"skill_name": "Redis", "category": "database", "difficulty_level": 3, "market_demand_score": 0.8},
    {"skill_name": "SQL", "category": "database", "difficulty_level": 2, "market_demand_score": 0.95},
    {"skill_name": "Database Design", "category": "database", "difficulty_level": 3, "market_demand_score": 0.85},
    {"skill_name": "ORM (SQLAlchemy/Prisma)", "category": "database", "difficulty_level": 3, "market_demand_score": 0.8},
    {"skill_name": "Elasticsearch", "category": "database", "difficulty_level": 4, "market_demand_score": 0.7},
    
    # DevOps
    {"skill_name": "Git", "category": "devops", "difficulty_level": 2, "market_demand_score": 0.95},
    {"skill_name": "Docker", "category": "devops", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "Kubernetes", "category": "devops", "difficulty_level": 5, "market_demand_score": 0.85},
    {"skill_name": "CI/CD", "category": "devops", "difficulty_level": 3, "market_demand_score": 0.85},
    {"skill_name": "AWS", "category": "devops", "difficulty_level": 4, "market_demand_score": 0.9},
    {"skill_name": "Azure", "category": "devops", "difficulty_level": 4, "market_demand_score": 0.8},
    {"skill_name": "GCP", "category": "devops", "difficulty_level": 4, "market_demand_score": 0.75},
    {"skill_name": "Linux", "category": "devops", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "Terraform", "category": "devops", "difficulty_level": 4, "market_demand_score": 0.75},
    {"skill_name": "Nginx", "category": "devops", "difficulty_level": 3, "market_demand_score": 0.7},
    
    # Data Science / ML
    {"skill_name": "Machine Learning", "category": "data_science", "difficulty_level": 4, "market_demand_score": 0.9},
    {"skill_name": "Deep Learning", "category": "data_science", "difficulty_level": 5, "market_demand_score": 0.85},
    {"skill_name": "TensorFlow", "category": "data_science", "difficulty_level": 4, "market_demand_score": 0.8},
    {"skill_name": "PyTorch", "category": "data_science", "difficulty_level": 4, "market_demand_score": 0.85},
    {"skill_name": "Pandas", "category": "data_science", "difficulty_level": 2, "market_demand_score": 0.9},
    {"skill_name": "NumPy", "category": "data_science", "difficulty_level": 2, "market_demand_score": 0.85},
    {"skill_name": "Data Visualization", "category": "data_science", "difficulty_level": 3, "market_demand_score": 0.8},
    {"skill_name": "NLP", "category": "data_science", "difficulty_level": 4, "market_demand_score": 0.85},
    {"skill_name": "Computer Vision", "category": "data_science", "difficulty_level": 5, "market_demand_score": 0.75},
    {"skill_name": "LangChain", "category": "data_science", "difficulty_level": 3, "market_demand_score": 0.8},
    
    # Soft Skills
    {"skill_name": "Problem Solving", "category": "soft_skills", "difficulty_level": 3, "market_demand_score": 0.95},
    {"skill_name": "Communication", "category": "soft_skills", "difficulty_level": 2, "market_demand_score": 0.95},
    {"skill_name": "Team Collaboration", "category": "soft_skills", "difficulty_level": 2, "market_demand_score": 0.9},
    {"skill_name": "Time Management", "category": "soft_skills", "difficulty_level": 2, "market_demand_score": 0.85},
    {"skill_name": "Critical Thinking", "category": "soft_skills", "difficulty_level": 3, "market_demand_score": 0.9},
    {"skill_name": "Agile/Scrum", "category": "soft_skills", "difficulty_level": 2, "market_demand_score": 0.85},
    {"skill_name": "Technical Writing", "category": "soft_skills", "difficulty_level": 3, "market_demand_score": 0.7},
    
    # Testing
    {"skill_name": "Unit Testing", "category": "testing", "difficulty_level": 2, "market_demand_score": 0.85},
    {"skill_name": "Integration Testing", "category": "testing", "difficulty_level": 3, "market_demand_score": 0.8},
    {"skill_name": "Jest", "category": "testing", "difficulty_level": 2, "market_demand_score": 0.8},
    {"skill_name": "Pytest", "category": "testing", "difficulty_level": 2, "market_demand_score": 0.8},
    {"skill_name": "Cypress", "category": "testing", "difficulty_level": 3, "market_demand_score": 0.75},
    {"skill_name": "Selenium", "category": "testing", "difficulty_level": 3, "market_demand_score": 0.7},
]


# Role templates
ROLE_TEMPLATES = [
    {
        "role_name": "Full Stack Developer",
        "level": "junior",
        "description": "Build complete web applications from frontend to backend",
        "required_skills": [
            {"skill_name": "HTML", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "CSS", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "JavaScript", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "React", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Node.js", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "SQL", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Git", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "REST API Design", "min_proficiency": 2, "importance": "required"},
        ],
        "preferred_skills": [
            {"skill_name": "TypeScript", "min_proficiency": 2},
            {"skill_name": "Docker", "min_proficiency": 2},
            {"skill_name": "PostgreSQL", "min_proficiency": 2},
        ],
        "responsibilities": [
            "Build responsive web applications",
            "Develop RESTful APIs",
            "Work with databases",
            "Collaborate with team members",
            "Write clean, maintainable code"
        ],
        "average_salary_range": "$60,000 - $90,000",
        "demand_score": 0.9
    },
    {
        "role_name": "Frontend Developer",
        "level": "mid",
        "description": "Create beautiful, responsive user interfaces",
        "required_skills": [
            {"skill_name": "HTML", "min_proficiency": 5, "importance": "required"},
            {"skill_name": "CSS", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "JavaScript", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "React", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "TypeScript", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Responsive Design", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Git", "min_proficiency": 3, "importance": "required"},
        ],
        "preferred_skills": [
            {"skill_name": "Next.js", "min_proficiency": 3},
            {"skill_name": "Tailwind CSS", "min_proficiency": 3},
            {"skill_name": "Web Accessibility", "min_proficiency": 3},
        ],
        "responsibilities": [
            "Build pixel-perfect UIs",
            "Optimize web performance",
            "Implement responsive designs",
            "Collaborate with designers"
        ],
        "average_salary_range": "$70,000 - $100,000",
        "demand_score": 0.85
    },
    {
        "role_name": "Backend Developer",
        "level": "mid",
        "description": "Build robust server-side applications and APIs",
        "required_skills": [
            {"skill_name": "Python", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "FastAPI", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "PostgreSQL", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "REST API Design", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "SQL", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Git", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Docker", "min_proficiency": 3, "importance": "required"},
        ],
        "preferred_skills": [
            {"skill_name": "Redis", "min_proficiency": 2},
            {"skill_name": "Microservices", "min_proficiency": 2},
            {"skill_name": "AWS", "min_proficiency": 2},
        ],
        "responsibilities": [
            "Design and build APIs",
            "Manage databases",
            "Ensure security",
            "Optimize performance"
        ],
        "average_salary_range": "$75,000 - $110,000",
        "demand_score": 0.85
    },
    {
        "role_name": "Data Scientist",
        "level": "junior",
        "description": "Extract insights from data using ML and statistics",
        "required_skills": [
            {"skill_name": "Python", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Pandas", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "NumPy", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Machine Learning", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Data Visualization", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "SQL", "min_proficiency": 3, "importance": "required"},
        ],
        "preferred_skills": [
            {"skill_name": "TensorFlow", "min_proficiency": 2},
            {"skill_name": "PyTorch", "min_proficiency": 2},
            {"skill_name": "Deep Learning", "min_proficiency": 2},
        ],
        "responsibilities": [
            "Analyze large datasets",
            "Build ML models",
            "Create visualizations",
            "Present insights"
        ],
        "average_salary_range": "$80,000 - $120,000",
        "demand_score": 0.88
    },
    {
        "role_name": "DevOps Engineer",
        "level": "mid",
        "description": "Bridge development and operations with automation",
        "required_skills": [
            {"skill_name": "Linux", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Docker", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Kubernetes", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "CI/CD", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "AWS", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Git", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Python", "min_proficiency": 3, "importance": "required"},
        ],
        "preferred_skills": [
            {"skill_name": "Terraform", "min_proficiency": 3},
            {"skill_name": "Nginx", "min_proficiency": 3},
        ],
        "responsibilities": [
            "Automate deployments",
            "Manage cloud infrastructure",
            "Monitor systems",
            "Ensure reliability"
        ],
        "average_salary_range": "$85,000 - $130,000",
        "demand_score": 0.9
    },
    {
        "role_name": "AI/ML Engineer",
        "level": "mid",
        "description": "Build and deploy machine learning systems",
        "required_skills": [
            {"skill_name": "Python", "min_proficiency": 5, "importance": "required"},
            {"skill_name": "Machine Learning", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "Deep Learning", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "PyTorch", "min_proficiency": 4, "importance": "required"},
            {"skill_name": "LangChain", "min_proficiency": 3, "importance": "required"},
            {"skill_name": "Docker", "min_proficiency": 3, "importance": "required"},
        ],
        "preferred_skills": [
            {"skill_name": "NLP", "min_proficiency": 3},
            {"skill_name": "AWS", "min_proficiency": 2},
            {"skill_name": "FastAPI", "min_proficiency": 3},
        ],
        "responsibilities": [
            "Train ML models",
            "Deploy models to production",
            "Optimize model performance",
            "Build AI applications"
        ],
        "average_salary_range": "$100,000 - $150,000",
        "demand_score": 0.92
    },
]


async def seed_skills(db: AsyncSession):
    """Seed skills master data."""
    print("Seeding skills...")
    
    for skill_data in SKILLS_DATA:
        skill = SkillMaster(
            id=uuid.uuid4(),
            skill_name=skill_data["skill_name"],
            category=skill_data["category"],
            difficulty_level=skill_data["difficulty_level"],
            market_demand_score=skill_data["market_demand_score"],
            created_at=datetime.utcnow()
        )
        db.add(skill)
    
    await db.commit()
    print(f"✅ Seeded {len(SKILLS_DATA)} skills")


async def seed_role_templates(db: AsyncSession):
    """Seed role templates."""
    print("Seeding role templates...")
    
    for template_data in ROLE_TEMPLATES:
        template = RoleTemplate(
            id=uuid.uuid4(),
            role_name=template_data["role_name"],
            level=template_data["level"],
            description=template_data["description"],
            required_skills=template_data["required_skills"],
            preferred_skills=template_data.get("preferred_skills"),
            responsibilities=template_data["responsibilities"],
            average_salary_range=template_data["average_salary_range"],
            demand_score=template_data["demand_score"],
            created_at=datetime.utcnow()
        )
        db.add(template)
    
    await db.commit()
    print(f"✅ Seeded {len(ROLE_TEMPLATES)} role templates")


async def main():
    """Main seed function."""
    print("🌱 Starting database seed...")
    
    # Initialize database
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT COUNT(*) FROM skills_master"))
        count = result.scalar()
        
        if count > 0:
            print(f"Database already has {count} skills. Skipping seed.")
            return
        
        await seed_skills(db)
        await seed_role_templates(db)
    
    print("✅ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
