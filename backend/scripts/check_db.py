"""Check and seed Supabase tables."""
import asyncio
import asyncpg

DB_URL = "postgresql://postgres.imrilpldnvfbsobtxyzo:DadMomand1432@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

async def check_tables():
    conn = await asyncpg.connect(DB_URL, ssl=False)
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    print("Tables in Supabase:")
    for r in rows:
        try:
            count = await conn.fetchval(f"SELECT count(*) FROM \"{r['tablename']}\"")
            print(f"  {r['tablename']}: {count} rows")
        except Exception as e:
            print(f"  {r['tablename']}: ERROR - {e}")
    await conn.close()

asyncio.run(check_tables())
