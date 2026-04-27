"""One-shot connectivity check against the configured DATABASE_URL."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Windows 3.12+ proactor loop + asyncpg TLS upgrade is buggy; force selector loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

# Load .env BEFORE importing app modules so settings pick up the new values.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from sqlalchemy import text  # noqa: E402

from app.database.postgres import engine  # noqa: E402


async def main() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 AS ok"))
        row = result.one()
        print("DB OK:", dict(row._mapping))
        tables = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        )
        names = [r.tablename for r in tables]
        print(f"Tables ({len(names)}):", names)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
