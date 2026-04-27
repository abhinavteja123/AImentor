"""Seed Supabase with demo data: skills, role templates, and a test user."""
import asyncio
import asyncpg
import uuid
import json

DB_URL = "postgresql://postgres.imrilpldnvfbsobtxyzo:DadMomand1432@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

# bcrypt hash for "demo123"
DEMO_PASSWORD_HASH = "$2b$12$LJ3m4ys3Lk8sJHqE8qvjYOjQ3qK4L5F6fV7yZ1wX0uN2mR9pS5aGe"

SKILLS = [
    ("Python Programming", "programming", "general", "General-purpose programming language", 2),
    ("JavaScript", "programming", "web", "Web scripting language", 2),
    ("React.js", "frontend", "frameworks", "UI component library", 3),
    ("Node.js", "backend", "runtime", "Server-side JavaScript runtime", 3),
    ("SQL & Databases", "database", "relational", "Structured Query Language", 2),
    ("Git & Version Control", "devops", "tools", "Source code management", 1),
    ("Docker & Containers", "devops", "tools", "Containerization platform", 3),
    ("AWS Cloud", "cloud", "platforms", "Amazon Web Services", 4),
    ("Machine Learning Basics", "ai", "fundamentals", "Fundamentals of ML", 3),
    ("Deep Learning", "ai", "advanced", "Neural networks and DL", 4),
    ("Natural Language Processing", "ai", "advanced", "Text and language AI", 4),
    ("Data Structures", "cs_fundamentals", "core", "Core CS data structures", 2),
    ("Algorithms", "cs_fundamentals", "core", "Algorithm design and analysis", 3),
    ("System Design", "architecture", "design", "Distributed systems design", 5),
    ("API Design", "backend", "design", "RESTful and GraphQL APIs", 3),
    ("TypeScript", "programming", "web", "Typed JavaScript", 3),
    ("FastAPI", "backend", "frameworks", "Python async web framework", 3),
    ("Next.js", "frontend", "frameworks", "React framework for production", 3),
    ("MongoDB", "database", "nosql", "NoSQL document database", 3),
    ("Redis", "database", "cache", "In-memory data store", 3),
]

ROLE_TEMPLATES = [
    ("Full Stack Developer", "mid",
     "Build complete web applications from frontend to backend",
     json.dumps(["Python", "JavaScript", "React.js", "Node.js", "SQL & Databases", "Git & Version Control"]),
     json.dumps(["Docker & Containers", "TypeScript"]),),
    ("ML Engineer", "mid",
     "Design and deploy machine learning models",
     json.dumps(["Python", "Machine Learning Basics", "Deep Learning", "SQL & Databases", "Git & Version Control"]),
     json.dumps(["Docker & Containers", "AWS Cloud"]),),
    ("Data Scientist", "mid",
     "Analyze data and build predictive models",
     json.dumps(["Python", "SQL & Databases", "Machine Learning Basics", "Deep Learning"]),
     json.dumps(["Natural Language Processing", "Git & Version Control"]),),
    ("Backend Developer", "mid",
     "Build server-side applications and APIs",
     json.dumps(["Python", "Node.js", "SQL & Databases", "API Design", "Docker & Containers"]),
     json.dumps(["Redis", "AWS Cloud", "System Design"]),),
    ("Frontend Developer", "mid",
     "Create user interfaces and web experiences",
     json.dumps(["JavaScript", "TypeScript", "React.js", "Next.js", "Git & Version Control"]),
     json.dumps(["API Design"]),),
]


async def seed():
    conn = await asyncpg.connect(DB_URL, ssl=False, statement_cache_size=0)

    # 1. Seed skills_master
    existing = await conn.fetchval("SELECT count(*) FROM skills_master")
    if existing == 0:
        print("Seeding skills_master...")
        for skill_name, category, subcategory, desc, difficulty in SKILLS:
            await conn.execute(
                """INSERT INTO skills_master (id, skill_name, category, subcategory, description, difficulty_level, market_demand_score, created_at)
                   VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, NOW())""",
                skill_name, category, subcategory, desc, difficulty, round(0.5 + difficulty * 0.1, 2)
            )
        print(f"  ✅ Inserted {len(SKILLS)} skills")
    else:
        print(f"  skills_master already has {existing} rows, skipping")

    # 2. Seed role_templates
    existing = await conn.fetchval("SELECT count(*) FROM role_templates")
    if existing == 0:
        print("Seeding role_templates...")
        for role_name, level, desc, req_skills, pref_skills in ROLE_TEMPLATES:
            await conn.execute(
                """INSERT INTO role_templates (id, role_name, level, description, required_skills, preferred_skills, created_at)
                   VALUES (gen_random_uuid(), $1, $2, $3, $4::jsonb, $5::jsonb, NOW())""",
                role_name, level, desc, req_skills, pref_skills
            )
        print(f"  ✅ Inserted {len(ROLE_TEMPLATES)} role templates")
    else:
        print(f"  role_templates already has {existing} rows, skipping")

    # 3. Create demo user
    existing = await conn.fetchval("SELECT count(*) FROM users WHERE email = 'demo@aimentor.com'")
    if existing == 0:
        print("Creating demo user...")
        user_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, created_at)
               VALUES ($1::uuid, $2, $3, $4, TRUE, TRUE, NOW())""",
            user_id, "demo@aimentor.com", DEMO_PASSWORD_HASH, "Demo Student"
        )
        # Create profile
        await conn.execute(
            """INSERT INTO user_profiles (id, user_id, bio, goal_role, experience_level, created_at, updated_at)
               VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, NOW(), NOW())""",
            user_id,
            "A CS student exploring AI and full-stack development.",
            "ML Engineer",
            "beginner"
        )
        print(f"  ✅ Demo user created: demo@aimentor.com / demo123")
    else:
        print("  Demo user already exists, skipping")

    # Final check
    print("\n--- Final Table Status ---")
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    for r in rows:
        count = await conn.fetchval(f'SELECT count(*) FROM "{r["tablename"]}"')
        if count > 0:
            print(f"  ✅ {r['tablename']}: {count} rows")
        else:
            print(f"  ⬜ {r['tablename']}: empty")

    await conn.close()
    print("\n🎯 Done! Login at http://localhost:3000 with: demo@aimentor.com / demo123")


asyncio.run(seed())
