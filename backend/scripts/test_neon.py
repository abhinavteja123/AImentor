"""Compare: does Neon (user's previous DB) work from this network?"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    import asyncpg
    try:
        conn = await asyncpg.connect(
            host="ep-young-rice-ahtzx5q1-pooler.c-3.us-east-1.aws.neon.tech",
            port=5432,
            user="neondb_owner",
            password="npg_eup6Gk5modZP",
            database="neondb",
            ssl="require",
            statement_cache_size=0,
            timeout=15,
        )
        row = await conn.fetchrow("SELECT current_user, current_database()")
        print("NEON OK:", dict(row))
        await conn.close()
    except Exception as e:
        print("NEON FAIL:", type(e).__name__, repr(e))


asyncio.run(main())
