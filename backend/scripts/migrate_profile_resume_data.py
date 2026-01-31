"""
Database migration script to add resume data columns to user_profiles table.
"""

import asyncio
import asyncpg
import os


async def migrate():
    """Add resume data columns to user_profiles table."""
    
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres123'),
        database=os.getenv('POSTGRES_DB', 'ai_mentor')
    )
    
    try:
        # Check which columns need to be added
        result = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' 
            AND column_name IN (
                'phone', 'location', 'website_url',
                'education_data', 'experience_data', 'projects_data',
                'certifications_data', 'extracurricular_data', 'technical_skills_data'
            )
        """)
        existing_columns = {row['column_name'] for row in result}
        
        columns_to_add = []
        
        if 'phone' not in existing_columns:
            columns_to_add.append("ADD COLUMN phone VARCHAR(50)")
            print("Will add: phone")
        
        if 'location' not in existing_columns:
            columns_to_add.append("ADD COLUMN location VARCHAR(255)")
            print("Will add: location")
        
        if 'website_url' not in existing_columns:
            columns_to_add.append("ADD COLUMN website_url VARCHAR(255)")
            print("Will add: website_url")
        
        if 'education_data' not in existing_columns:
            columns_to_add.append("ADD COLUMN education_data JSONB")
            print("Will add: education_data")
        
        if 'experience_data' not in existing_columns:
            columns_to_add.append("ADD COLUMN experience_data JSONB")
            print("Will add: experience_data")
        
        if 'projects_data' not in existing_columns:
            columns_to_add.append("ADD COLUMN projects_data JSONB")
            print("Will add: projects_data")
        
        if 'certifications_data' not in existing_columns:
            columns_to_add.append("ADD COLUMN certifications_data JSONB")
            print("Will add: certifications_data")
        
        if 'extracurricular_data' not in existing_columns:
            columns_to_add.append("ADD COLUMN extracurricular_data JSONB")
            print("Will add: extracurricular_data")
        
        if 'technical_skills_data' not in existing_columns:
            columns_to_add.append("ADD COLUMN technical_skills_data JSONB")
            print("Will add: technical_skills_data")
        
        if not columns_to_add:
            print("All columns already exist. No migration needed.")
            return
        
        # Build and execute ALTER TABLE statement
        alter_sql = "ALTER TABLE user_profiles " + ", ".join(columns_to_add)
        print(f"\nExecuting: {alter_sql}")
        
        await conn.execute(alter_sql)
        print("\n✅ Migration completed successfully!")
        
        # Verify the changes
        result = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' 
            AND column_name IN (
                'phone', 'location', 'website_url',
                'education_data', 'experience_data', 'projects_data',
                'certifications_data', 'extracurricular_data', 'technical_skills_data'
            )
            ORDER BY column_name
        """)
        
        print("\n📋 New columns in user_profiles table:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    print("🚀 Starting database migration for profile resume data...")
    print("=" * 60)
    asyncio.run(migrate())
    print("=" * 60)
    print("Migration complete!")
