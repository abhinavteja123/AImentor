"""
Database Migration Script for Resume Table
Adds new columns: coursework_section, extracurricular_section, technical_skills_section
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database.postgres import engine, Base
from app.models.resume import Resume
from app.models.user import User
from app.models.profile import UserProfile


async def run_migration():
    """Run database migration to add new resume columns."""
    print("Starting migration...")
    
    try:
        async with engine.begin() as conn:
            # Add coursework_section column
            print("Adding coursework_section column...")
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'resumes' AND column_name = 'coursework_section'
                    ) THEN
                        ALTER TABLE resumes ADD COLUMN coursework_section JSONB;
                    END IF;
                END $$;
            """))
            
            # Add extracurricular_section column
            print("Adding extracurricular_section column...")
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'resumes' AND column_name = 'extracurricular_section'
                    ) THEN
                        ALTER TABLE resumes ADD COLUMN extracurricular_section JSONB;
                    END IF;
                END $$;
            """))
            
            # Add technical_skills_section column
            print("Adding technical_skills_section column...")
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'resumes' AND column_name = 'technical_skills_section'
                    ) THEN
                        ALTER TABLE resumes ADD COLUMN technical_skills_section JSONB;
                    END IF;
                END $$;
            """))
            
            # Create indexes
            print("Creating indexes...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_resumes_coursework_section 
                ON resumes USING gin(coursework_section);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_resumes_extracurricular_section 
                ON resumes USING gin(extracurricular_section);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_resumes_technical_skills_section 
                ON resumes USING gin(technical_skills_section);
            """))
            
            print("✅ Migration completed successfully!")
            print("   - Added coursework_section column")
            print("   - Added extracurricular_section column")
            print("   - Added technical_skills_section column")
            print("   - Created GIN indexes for JSONB columns")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Resume Table Migration")
    print("=" * 60)
    asyncio.run(run_migration())
