"""
One-shot: dump PostgreSQL DDL for all SQLAlchemy models to supabase_schema.sql.

Run from backend/:  python scripts/dump_supabase_schema.py
Output goes to repo root so the user can paste it into Supabase SQL editor.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Use sqlite driver for the import-time engine so this script works without asyncpg.
# We compile DDL against the postgresql dialect below, so the engine URL doesn't affect output.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database.postgres import Base
from app import models  # noqa: F401  (registers all tables on Base.metadata)


HEADER = """-- AImentor — Supabase schema
-- Paste this into the Supabase SQL editor and run.
-- Generated from SQLAlchemy models; do not hand-edit. Regenerate with:
--   cd backend && python scripts/dump_supabase_schema.py

-- Required extension for gen_random_uuid() if you ever switch server-side UUID defaults.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

"""

FOOTER = """
-- Optional: Row-Level Security examples (uncomment once Supabase Auth is wired).
-- ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "own_resumes" ON resumes FOR ALL USING (user_id = auth.uid());
"""


def main() -> None:
    dialect = postgresql.dialect()
    out_lines: list[str] = [HEADER]

    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).strip()
        out_lines.append(f"-- Table: {table.name}")
        out_lines.append(ddl + ";\n")
        for idx in table.indexes:
            idx_ddl = str(CreateIndex(idx).compile(dialect=dialect)).strip()
            out_lines.append(idx_ddl + ";")
        out_lines.append("")

    out_lines.append(FOOTER)

    repo_root = Path(__file__).resolve().parents[2]
    out_path = repo_root / "supabase_schema.sql"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
