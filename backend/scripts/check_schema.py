"""Check column names of all tables."""
import asyncio, asyncpg

DB_URL = "postgresql://postgres.imrilpldnvfbsobtxyzo:DadMomand1432@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

async def check():
    conn = await asyncpg.connect(DB_URL, ssl=False, statement_cache_size=0)
    for table in ['skills_master', 'role_templates', 'users', 'user_profiles']:
        cols = await conn.fetch(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1 ORDER BY ordinal_position",
            table
        )
        print(f"\n{table}:")
        for c in cols:
            print(f"  {c['column_name']}: {c['data_type']}")
    await conn.close()

asyncio.run(check())
