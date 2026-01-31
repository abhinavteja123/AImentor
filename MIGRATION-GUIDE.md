# Database Migration Guide

## Problem
The application is trying to query columns that don't exist in the database:
- `coursework_section`
- `extracurricular_section`
- `technical_skills_section`

## Solution
Run the migration to add these columns to the `resumes` table.

## Option 1: Automated Script (Recommended)

### Windows:
```bash
run-migration.bat
```

### Linux/Mac:
```bash
chmod +x run-migration.sh
./run-migration.sh
```

## Option 2: Using Docker Compose

```bash
docker compose exec backend python scripts/migrate_resume_table.py
```

## Option 3: Direct PostgreSQL Connection

1. **Connect to the database:**
```bash
docker compose exec postgres psql -U aimentor -d aimentor
```

2. **Run the SQL commands:**
```sql
-- Add coursework_section column
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS coursework_section JSONB;

-- Add extracurricular_section column
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS extracurricular_section JSONB;

-- Add technical_skills_section column
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS technical_skills_section JSONB;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_resumes_coursework_section ON resumes USING gin(coursework_section);
CREATE INDEX IF NOT EXISTS idx_resumes_extracurricular_section ON resumes USING gin(extracurricular_section);
CREATE INDEX IF NOT EXISTS idx_resumes_technical_skills_section ON resumes USING gin(technical_skills_section);
```

3. **Verify the changes:**
```sql
\d resumes
```

You should see the new columns listed.

4. **Exit psql:**
```sql
\q
```

## Option 4: Using SQL File Directly

```bash
docker compose exec -T postgres psql -U aimentor -d aimentor < backend/scripts/add_resume_columns.sql
```

## Verification

After running the migration, restart the backend service:

```bash
docker compose restart backend
```

Then test the application. The error should be resolved.

## Troubleshooting

### If migration fails:

1. **Check if containers are running:**
```bash
docker compose ps
```

2. **Check database connection:**
```bash
docker compose exec backend python -c "from app.database.postgres import engine; import asyncio; asyncio.run(engine.connect())"
```

3. **View backend logs:**
```bash
docker compose logs backend
```

4. **View database logs:**
```bash
docker compose logs postgres
```

### If columns already exist:

The migration scripts use `IF NOT EXISTS` checks, so running them multiple times is safe.

### If you want to start fresh:

```bash
# WARNING: This will delete all data!
docker compose down -v
docker compose up -d
```

Then run the initialization script:
```bash
docker compose exec backend python scripts/seed_database.py
```

## What Changed

The migration adds three new JSONB columns to the `resumes` table to support the LaTeX template:

1. **coursework_section** - Stores coursework/skills list
2. **extracurricular_section** - Stores extracurricular activities
3. **technical_skills_section** - Stores technical skills grouped by category

These columns are required for the new ATS-optimized resume generation feature.
