"""Fix demo user password and create real user."""
import asyncio
import asyncpg
import bcrypt

DB_URL = "postgresql://postgres.imrilpldnvfbsobtxyzo:DadMomand1432@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

async def fix():
    conn = await asyncpg.connect(DB_URL, ssl=False, statement_cache_size=0)

    # Fix demo user password hash
    proper_hash = bcrypt.hashpw(b"demo123", bcrypt.gensalt(12)).decode()
    result = await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE email = 'demo@aimentor.com'",
        proper_hash
    )
    print(f"Updated demo user password: {result}")

    # Create your real account: abhinavteja_mariyala@srmap.edu.in / Admin@123
    email = "abhinavteja_mariyala@srmap.edu.in"
    existing = await conn.fetchval("SELECT count(*) FROM users WHERE email = $1", email)
    if existing == 0:
        import uuid
        user_id = str(uuid.uuid4())
        pwd_hash = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt(12)).decode()
        await conn.execute(
            """INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, created_at)
               VALUES ($1::uuid, $2, $3, $4, TRUE, TRUE, NOW())""",
            user_id, email, pwd_hash, "Abhinav Teja"
        )
        await conn.execute(
            """INSERT INTO user_profiles (id, user_id, bio, goal_role, experience_level, created_at, updated_at)
               VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, NOW(), NOW())""",
            user_id,
            "CS student at SRM AP, exploring AI and full-stack development.",
            "ML Engineer",
            "intermediate"
        )
        print(f"Created user: {email} / Admin@123")
    else:
        # Update existing password
        pwd_hash = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt(12)).decode()
        await conn.execute("UPDATE users SET password_hash = $1 WHERE email = $2", pwd_hash, email)
        print(f"Updated password for: {email}")

    # Show all users
    users = await conn.fetch("SELECT email, full_name FROM users")
    print("\nAll users:")
    for u in users:
        print(f"  {u['email']} - {u['full_name']}")

    await conn.close()

asyncio.run(fix())
