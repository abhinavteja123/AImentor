"""
Database migration script to add version management columns to resumes table.
Run this script to add draft_name, parent_version_id, is_base_version, and job_description columns.
"""

import asyncio
import asyncpg
import os


async def migrate():
    """Add version management columns to resumes table."""
    
    # Connect to PostgreSQL using environment variables
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres123'),
        database=os.getenv('POSTGRES_DB', 'ai_mentor')
    )
    
    try:
        # Check if columns already exist
        columns_to_add = []
        
        result = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'resumes' 
            AND column_name IN ('draft_name', 'parent_version_id', 'is_base_version', 'job_description')
        """)
        existing_columns = {row['column_name'] for row in result}
        
        if 'draft_name' not in existing_columns:
            columns_to_add.append("ADD COLUMN draft_name VARCHAR(255)")
            print("Will add: draft_name")
        
        if 'parent_version_id' not in existing_columns:
            columns_to_add.append("ADD COLUMN parent_version_id UUID")
            print("Will add: parent_version_id")
        
        if 'is_base_version' not in existing_columns:
            columns_to_add.append("ADD COLUMN is_base_version BOOLEAN DEFAULT TRUE")
            print("Will add: is_base_version")
        
        if 'job_description' not in existing_columns:
            columns_to_add.append("ADD COLUMN job_description TEXT")
            print("Will add: job_description")
        
        if not columns_to_add:
            print("All columns already exist. No migration needed.")
            return
        
        # Build and execute ALTER TABLE statement
        alter_sql = "ALTER TABLE resumes " + ", ".join(columns_to_add)
        print(f"\nExecuting: {alter_sql}")
        
        await conn.execute(alter_sql)
        print("\n✅ Migration completed successfully!")
        
        # Update existing resumes to set is_base_version and draft_name
        await conn.execute("""
            UPDATE resumes 
            SET 
                is_base_version = TRUE,
                draft_name = CONCAT('Version ', version::text)
            WHERE is_base_version IS NULL OR draft_name IS NULL
        """)
        print("✅ Updated existing resumes with default values")
        
        # Verify the changes
        result = await conn.fetch("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'resumes' 
            AND column_name IN ('draft_name', 'parent_version_id', 'is_base_version', 'job_description')
            ORDER BY column_name
        """)
        
        print("\n📋 New columns in resumes table:")
        for row in result:
            print(f"  - {row['column_name']}: {row['data_type']} (default: {row['column_default']})")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    print("🚀 Starting database migration for resume version management...")
    print("=" * 60)
    asyncio.run(migrate())
    print("=" * 60)
    print("Migration complete!")
