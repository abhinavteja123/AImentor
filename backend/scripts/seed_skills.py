"""
Seed Skills Master Database
Run this script to populate the skills_master table with common tech skills
"""

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.postgres import AsyncSessionLocal
from ..models.skill import SkillMaster


# Skills data organized by category
SKILLS_DATA = {
    "frontend": [
        {"name": "JavaScript", "difficulty": 3, "demand": 0.95, "description": "Core web programming language"},
        {"name": "TypeScript", "difficulty": 3, "demand": 0.90, "description": "Typed superset of JavaScript"},
        {"name": "React", "difficulty": 3, "demand": 0.92, "description": "Popular UI library by Meta"},
        {"name": "Vue.js", "difficulty": 3, "demand": 0.75, "description": "Progressive JavaScript framework"},
        {"name": "Angular", "difficulty": 4, "demand": 0.70, "description": "Full-featured framework by Google"},
        {"name": "Next.js", "difficulty": 3, "demand": 0.85, "description": "React framework for production"},
        {"name": "HTML", "difficulty": 1, "demand": 0.98, "description": "Markup language for web pages"},
        {"name": "CSS", "difficulty": 2, "demand": 0.95, "description": "Styling language for web"},
        {"name": "Tailwind CSS", "difficulty": 2, "demand": 0.85, "description": "Utility-first CSS framework"},
        {"name": "SASS/SCSS", "difficulty": 2, "demand": 0.70, "description": "CSS preprocessor"},
        {"name": "Redux", "difficulty": 3, "demand": 0.75, "description": "State management for React"},
        {"name": "Webpack", "difficulty": 3, "demand": 0.65, "description": "Module bundler"},
        {"name": "Vite", "difficulty": 2, "demand": 0.80, "description": "Fast build tool"},
        {"name": "Responsive Design", "difficulty": 2, "demand": 0.90, "description": "Mobile-first design approach"},
        {"name": "Web Accessibility", "difficulty": 2, "demand": 0.75, "description": "WCAG accessibility standards"},
        {"name": "Svelte", "difficulty": 2, "demand": 0.60, "description": "Compile-time framework"},
    ],
    "backend": [
        {"name": "Python", "difficulty": 2, "demand": 0.95, "description": "Versatile programming language"},
        {"name": "Node.js", "difficulty": 3, "demand": 0.90, "description": "JavaScript runtime"},
        {"name": "Java", "difficulty": 3, "demand": 0.85, "description": "Enterprise programming language"},
        {"name": "Go", "difficulty": 3, "demand": 0.80, "description": "Fast, compiled language by Google"},
        {"name": "Rust", "difficulty": 4, "demand": 0.70, "description": "Systems programming language"},
        {"name": "C#", "difficulty": 3, "demand": 0.75, "description": ".NET programming language"},
        {"name": "PHP", "difficulty": 2, "demand": 0.60, "description": "Server-side scripting"},
        {"name": "Ruby", "difficulty": 2, "demand": 0.50, "description": "Dynamic programming language"},
        {"name": "FastAPI", "difficulty": 2, "demand": 0.80, "description": "Modern Python web framework"},
        {"name": "Django", "difficulty": 3, "demand": 0.75, "description": "Python web framework"},
        {"name": "Flask", "difficulty": 2, "demand": 0.70, "description": "Lightweight Python framework"},
        {"name": "Express.js", "difficulty": 2, "demand": 0.85, "description": "Node.js web framework"},
        {"name": "Spring Boot", "difficulty": 4, "demand": 0.80, "description": "Java application framework"},
        {"name": "REST APIs", "difficulty": 2, "demand": 0.95, "description": "API design and development"},
        {"name": "GraphQL", "difficulty": 3, "demand": 0.75, "description": "Query language for APIs"},
        {"name": "gRPC", "difficulty": 3, "demand": 0.60, "description": "High-performance RPC framework"},
    ],
    "database": [
        {"name": "SQL", "difficulty": 2, "demand": 0.95, "description": "Structured query language"},
        {"name": "PostgreSQL", "difficulty": 3, "demand": 0.90, "description": "Advanced open-source database"},
        {"name": "MySQL", "difficulty": 2, "demand": 0.85, "description": "Popular relational database"},
        {"name": "MongoDB", "difficulty": 2, "demand": 0.80, "description": "NoSQL document database"},
        {"name": "Redis", "difficulty": 2, "demand": 0.85, "description": "In-memory data store"},
        {"name": "Elasticsearch", "difficulty": 3, "demand": 0.70, "description": "Search and analytics engine"},
        {"name": "SQLite", "difficulty": 1, "demand": 0.60, "description": "Lightweight database"},
        {"name": "DynamoDB", "difficulty": 3, "demand": 0.65, "description": "AWS NoSQL database"},
        {"name": "Cassandra", "difficulty": 4, "demand": 0.55, "description": "Distributed database"},
        {"name": "Database Design", "difficulty": 3, "demand": 0.85, "description": "Schema design and normalization"},
    ],
    "devops": [
        {"name": "Docker", "difficulty": 2, "demand": 0.92, "description": "Container platform"},
        {"name": "Kubernetes", "difficulty": 4, "demand": 0.85, "description": "Container orchestration"},
        {"name": "AWS", "difficulty": 3, "demand": 0.90, "description": "Amazon cloud services"},
        {"name": "Azure", "difficulty": 3, "demand": 0.80, "description": "Microsoft cloud platform"},
        {"name": "GCP", "difficulty": 3, "demand": 0.75, "description": "Google Cloud Platform"},
        {"name": "CI/CD", "difficulty": 3, "demand": 0.90, "description": "Continuous integration/deployment"},
        {"name": "GitHub Actions", "difficulty": 2, "demand": 0.85, "description": "GitHub CI/CD"},
        {"name": "Jenkins", "difficulty": 3, "demand": 0.70, "description": "Automation server"},
        {"name": "Terraform", "difficulty": 3, "demand": 0.80, "description": "Infrastructure as Code"},
        {"name": "Ansible", "difficulty": 3, "demand": 0.65, "description": "Configuration management"},
        {"name": "Linux", "difficulty": 2, "demand": 0.90, "description": "Server administration"},
        {"name": "Nginx", "difficulty": 2, "demand": 0.75, "description": "Web server/reverse proxy"},
        {"name": "Monitoring", "difficulty": 3, "demand": 0.80, "description": "System monitoring tools"},
    ],
    "mobile": [
        {"name": "React Native", "difficulty": 3, "demand": 0.85, "description": "Cross-platform mobile framework"},
        {"name": "Flutter", "difficulty": 3, "demand": 0.80, "description": "Google's UI toolkit"},
        {"name": "Swift", "difficulty": 3, "demand": 0.75, "description": "iOS development language"},
        {"name": "Kotlin", "difficulty": 3, "demand": 0.80, "description": "Android development language"},
        {"name": "iOS Development", "difficulty": 3, "demand": 0.75, "description": "Apple mobile development"},
        {"name": "Android Development", "difficulty": 3, "demand": 0.80, "description": "Android app development"},
        {"name": "Mobile UI/UX", "difficulty": 2, "demand": 0.75, "description": "Mobile design principles"},
    ],
    "ai_ml": [
        {"name": "Machine Learning", "difficulty": 4, "demand": 0.90, "description": "ML algorithms and models"},
        {"name": "Deep Learning", "difficulty": 5, "demand": 0.85, "description": "Neural networks"},
        {"name": "TensorFlow", "difficulty": 4, "demand": 0.80, "description": "ML framework by Google"},
        {"name": "PyTorch", "difficulty": 4, "demand": 0.85, "description": "ML framework by Meta"},
        {"name": "NLP", "difficulty": 4, "demand": 0.80, "description": "Natural language processing"},
        {"name": "Computer Vision", "difficulty": 4, "demand": 0.75, "description": "Image processing and analysis"},
        {"name": "LLMs", "difficulty": 4, "demand": 0.90, "description": "Large Language Models"},
        {"name": "Scikit-learn", "difficulty": 3, "demand": 0.80, "description": "ML library for Python"},
        {"name": "OpenAI API", "difficulty": 2, "demand": 0.85, "description": "GPT and AI integration"},
        {"name": "Hugging Face", "difficulty": 3, "demand": 0.80, "description": "ML model hub"},
    ],
    "data_science": [
        {"name": "Data Analysis", "difficulty": 3, "demand": 0.90, "description": "Data exploration and insights"},
        {"name": "Pandas", "difficulty": 2, "demand": 0.90, "description": "Python data manipulation"},
        {"name": "NumPy", "difficulty": 2, "demand": 0.85, "description": "Numerical computing"},
        {"name": "Data Visualization", "difficulty": 2, "demand": 0.85, "description": "Charts and dashboards"},
        {"name": "Statistics", "difficulty": 3, "demand": 0.80, "description": "Statistical analysis"},
        {"name": "SQL Analytics", "difficulty": 3, "demand": 0.85, "description": "Data querying and analysis"},
        {"name": "Power BI", "difficulty": 2, "demand": 0.70, "description": "Microsoft BI tool"},
        {"name": "Tableau", "difficulty": 2, "demand": 0.70, "description": "Data visualization platform"},
        {"name": "Apache Spark", "difficulty": 4, "demand": 0.70, "description": "Big data processing"},
        {"name": "ETL", "difficulty": 3, "demand": 0.75, "description": "Data pipeline design"},
    ],
    "tools": [
        {"name": "Git", "difficulty": 2, "demand": 0.98, "description": "Version control system"},
        {"name": "GitHub", "difficulty": 1, "demand": 0.95, "description": "Code hosting platform"},
        {"name": "VS Code", "difficulty": 1, "demand": 0.90, "description": "Code editor"},
        {"name": "Postman", "difficulty": 1, "demand": 0.85, "description": "API testing tool"},
        {"name": "Jira", "difficulty": 1, "demand": 0.75, "description": "Project management"},
        {"name": "Figma", "difficulty": 2, "demand": 0.80, "description": "Design tool"},
        {"name": "Unit Testing", "difficulty": 2, "demand": 0.90, "description": "Test-driven development"},
        {"name": "Jest", "difficulty": 2, "demand": 0.80, "description": "JavaScript testing"},
        {"name": "Pytest", "difficulty": 2, "demand": 0.80, "description": "Python testing"},
        {"name": "Agile/Scrum", "difficulty": 1, "demand": 0.85, "description": "Agile methodology"},
    ],
    "soft_skills": [
        {"name": "Problem Solving", "difficulty": 3, "demand": 0.95, "description": "Analytical thinking"},
        {"name": "Communication", "difficulty": 2, "demand": 0.95, "description": "Clear technical communication"},
        {"name": "Teamwork", "difficulty": 2, "demand": 0.90, "description": "Collaboration skills"},
        {"name": "Time Management", "difficulty": 2, "demand": 0.85, "description": "Prioritization and planning"},
        {"name": "Leadership", "difficulty": 3, "demand": 0.80, "description": "Team leadership skills"},
        {"name": "Critical Thinking", "difficulty": 3, "demand": 0.90, "description": "Logical analysis"},
        {"name": "Adaptability", "difficulty": 2, "demand": 0.90, "description": "Learning new technologies"},
        {"name": "Documentation", "difficulty": 2, "demand": 0.80, "description": "Technical writing"},
        {"name": "Presentation Skills", "difficulty": 2, "demand": 0.75, "description": "Public speaking"},
        {"name": "Mentoring", "difficulty": 3, "demand": 0.70, "description": "Teaching and guidance"},
    ],
}


async def seed_skills(db: AsyncSession):
    """Seed skills master database."""
    print("🌱 Seeding skills master database...")
    
    skills_added = 0
    skills_skipped = 0
    
    for category, skills in SKILLS_DATA.items():
        for skill_data in skills:
            # Check if skill already exists
            result = await db.execute(
                select(SkillMaster).where(
                    SkillMaster.skill_name.ilike(skill_data["name"])
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                skills_skipped += 1
                continue
            
            # Create new skill
            skill = SkillMaster(
                id=uuid.uuid4(),
                skill_name=skill_data["name"],
                category=category,
                description=skill_data.get("description"),
                difficulty_level=skill_data.get("difficulty", 3),
                market_demand_score=skill_data.get("demand", 0.5),
                created_at=datetime.utcnow()
            )
            db.add(skill)
            skills_added += 1
    
    await db.commit()
    
    print(f"✅ Skills seeded: {skills_added} added, {skills_skipped} skipped (already exist)")
    return {"added": skills_added, "skipped": skills_skipped}


async def seed_role_templates(db: AsyncSession):
    """Seed role templates with required skills."""
    from app.models.skill import RoleTemplate
    
    print("🎯 Seeding role templates...")
    
    templates = [
        {
            "role_name": "Frontend Developer",
            "level": "mid",
            "description": "Build user interfaces and web applications",
            "required_skills": [
                {"skill_name": "JavaScript", "min_proficiency": 4},
                {"skill_name": "React", "min_proficiency": 3},
                {"skill_name": "HTML", "min_proficiency": 4},
                {"skill_name": "CSS", "min_proficiency": 3},
                {"skill_name": "TypeScript", "min_proficiency": 3},
                {"skill_name": "Git", "min_proficiency": 3},
                {"skill_name": "Problem Solving", "min_proficiency": 3},
            ],
            "preferred_skills": [
                {"skill_name": "Next.js", "min_proficiency": 2},
                {"skill_name": "Tailwind CSS", "min_proficiency": 2},
                {"skill_name": "Unit Testing", "min_proficiency": 2},
            ],
            "average_salary_range": "$70,000 - $120,000",
            "demand_score": 0.90
        },
        {
            "role_name": "Backend Developer",
            "level": "mid",
            "description": "Build server-side applications and APIs",
            "required_skills": [
                {"skill_name": "Python", "min_proficiency": 4},
                {"skill_name": "SQL", "min_proficiency": 3},
                {"skill_name": "REST APIs", "min_proficiency": 4},
                {"skill_name": "Git", "min_proficiency": 3},
                {"skill_name": "PostgreSQL", "min_proficiency": 3},
                {"skill_name": "Problem Solving", "min_proficiency": 3},
            ],
            "preferred_skills": [
                {"skill_name": "Docker", "min_proficiency": 2},
                {"skill_name": "FastAPI", "min_proficiency": 3},
                {"skill_name": "Redis", "min_proficiency": 2},
            ],
            "average_salary_range": "$75,000 - $130,000",
            "demand_score": 0.88
        },
        {
            "role_name": "Full Stack Developer",
            "level": "mid",
            "description": "Build end-to-end web applications",
            "required_skills": [
                {"skill_name": "JavaScript", "min_proficiency": 4},
                {"skill_name": "React", "min_proficiency": 3},
                {"skill_name": "Node.js", "min_proficiency": 3},
                {"skill_name": "SQL", "min_proficiency": 3},
                {"skill_name": "Git", "min_proficiency": 3},
                {"skill_name": "REST APIs", "min_proficiency": 3},
                {"skill_name": "Problem Solving", "min_proficiency": 3},
            ],
            "preferred_skills": [
                {"skill_name": "TypeScript", "min_proficiency": 3},
                {"skill_name": "Docker", "min_proficiency": 2},
                {"skill_name": "AWS", "min_proficiency": 2},
            ],
            "average_salary_range": "$80,000 - $140,000",
            "demand_score": 0.92
        },
        {
            "role_name": "Data Scientist",
            "level": "mid",
            "description": "Analyze data and build ML models",
            "required_skills": [
                {"skill_name": "Python", "min_proficiency": 4},
                {"skill_name": "Machine Learning", "min_proficiency": 3},
                {"skill_name": "SQL", "min_proficiency": 3},
                {"skill_name": "Data Analysis", "min_proficiency": 4},
                {"skill_name": "Statistics", "min_proficiency": 3},
                {"skill_name": "Pandas", "min_proficiency": 4},
            ],
            "preferred_skills": [
                {"skill_name": "Deep Learning", "min_proficiency": 2},
                {"skill_name": "TensorFlow", "min_proficiency": 2},
                {"skill_name": "Data Visualization", "min_proficiency": 3},
            ],
            "average_salary_range": "$90,000 - $150,000",
            "demand_score": 0.88
        },
        {
            "role_name": "DevOps Engineer",
            "level": "mid",
            "description": "Manage infrastructure and deployment pipelines",
            "required_skills": [
                {"skill_name": "Docker", "min_proficiency": 4},
                {"skill_name": "Kubernetes", "min_proficiency": 3},
                {"skill_name": "AWS", "min_proficiency": 3},
                {"skill_name": "CI/CD", "min_proficiency": 4},
                {"skill_name": "Linux", "min_proficiency": 4},
                {"skill_name": "Git", "min_proficiency": 3},
            ],
            "preferred_skills": [
                {"skill_name": "Terraform", "min_proficiency": 3},
                {"skill_name": "Python", "min_proficiency": 2},
                {"skill_name": "Monitoring", "min_proficiency": 3},
            ],
            "average_salary_range": "$85,000 - $145,000",
            "demand_score": 0.90
        },
    ]
    
    templates_added = 0
    templates_skipped = 0
    
    for template_data in templates:
        result = await db.execute(
            select(RoleTemplate).where(
                RoleTemplate.role_name.ilike(template_data["role_name"])
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            templates_skipped += 1
            continue
        
        # Combine required and preferred skills
        all_required = []
        for skill in template_data["required_skills"]:
            all_required.append({
                "skill_name": skill["skill_name"],
                "category": get_skill_category(skill["skill_name"]),
                "min_proficiency": skill["min_proficiency"],
                "importance": "required"
            })
        for skill in template_data.get("preferred_skills", []):
            all_required.append({
                "skill_name": skill["skill_name"],
                "category": get_skill_category(skill["skill_name"]),
                "min_proficiency": skill["min_proficiency"],
                "importance": "preferred"
            })
        
        template = RoleTemplate(
            id=uuid.uuid4(),
            role_name=template_data["role_name"],
            level=template_data.get("level"),
            description=template_data.get("description"),
            required_skills=all_required,
            average_salary_range=template_data.get("average_salary_range"),
            demand_score=template_data.get("demand_score", 0.5),
            created_at=datetime.utcnow()
        )
        db.add(template)
        templates_added += 1
    
    await db.commit()
    
    print(f"✅ Role templates seeded: {templates_added} added, {templates_skipped} skipped")
    return {"added": templates_added, "skipped": templates_skipped}


def get_skill_category(skill_name: str) -> str:
    """Get category for a skill name."""
    for category, skills in SKILLS_DATA.items():
        for skill in skills:
            if skill["name"].lower() == skill_name.lower():
                return category
    return "other"


async def main():
    """Run the seeding script."""
    print("=" * 50)
    print("AI Mentor - Skills Database Seeder")
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        await seed_skills(db)
        await seed_role_templates(db)
    
    print("\n✨ Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
