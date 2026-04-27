"""
Idempotent applier for backend/app/migrations/tutor_tables.sql.

Run from the repo root:
    python -m backend.scripts.apply_tutor_migration

Reads ``DATABASE_URL`` from the environment (or ``backend/.env`` via the
existing settings loader). Splits the SQL on top-level semicolons and
executes each statement in a single transaction. Safe to re-run: the
``CREATE TABLE IF NOT EXISTS`` and ``ON CONFLICT DO NOTHING`` clauses
mean repeated runs are no-ops.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("apply_tutor_migration")


def _split_sql(text: str) -> list[str]:
    """
    Split on top-level semicolons. The migration has no functions/$$ blocks,
    so a naive split is sufficient. Comments are preserved per-statement.
    """
    # Strip line comments outside strings
    cleaned = re.sub(r"--[^\n]*", "", text)
    parts = [p.strip() for p in cleaned.split(";")]
    return [p for p in parts if p]


async def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

    # Load .env from backend/.env (the project's convention).
    try:
        from dotenv import load_dotenv  # type: ignore
        env_path = repo_root / "backend" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            log.info("Loaded env from %s", env_path)
    except ImportError:
        pass

    from backend.app.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    sql_path = repo_root / "backend" / "app" / "migrations" / "tutor_tables.sql"
    sql = sql_path.read_text(encoding="utf-8")
    statements = _split_sql(sql)
    log.info("Applying %d statements from %s", len(statements), sql_path)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            for i, stmt in enumerate(statements, 1):
                preview = " ".join(stmt.split())[:80]
                log.info("[%d/%d] %s…", i, len(statements), preview)
                await conn.execute(text(stmt))
        log.info("✅ Migration applied successfully.")
    except Exception as e:
        log.error("Migration failed: %s", e)
        return 1
    finally:
        await engine.dispose()

    # Verify the 5 anchor skills are present.
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text(
                "SELECT skill_name FROM skills_master "
                "WHERE category = 'AI Fundamentals' ORDER BY skill_name"))
            rows = [r[0] for r in res.fetchall()]
            log.info("Anchor skills present (%d): %s", len(rows), rows)
            if len(rows) < 5:
                log.warning("Expected 5 anchor skills, found %d.", len(rows))
                return 2
    finally:
        await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
