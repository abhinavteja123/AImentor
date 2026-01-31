"""
Cleanup Script: Fix Multiple Active Resumes Issue
Ensures only the latest version of each user's resume is marked as active
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select, func
from app.database.postgres import engine
from app.models.resume import Resume


async def cleanup_active_resumes():
    """Ensure only the latest resume version is active for each user."""
    print("Starting cleanup of active resumes...")
    
    try:
        async with engine.begin() as conn:
            # Find users with multiple active resumes
            result = await conn.execute(text("""
                SELECT user_id, COUNT(*) as count
                FROM resumes
                WHERE is_active = true
                GROUP BY user_id
                HAVING COUNT(*) > 1
            """))
            
            duplicate_users = result.fetchall()
            
            if not duplicate_users:
                print("✅ No duplicate active resumes found. Database is clean.")
                return
            
            print(f"Found {len(duplicate_users)} users with multiple active resumes")
            
            # For each user with duplicates, keep only the latest version active
            for user_row in duplicate_users:
                user_id = user_row[0]
                count = user_row[1]
                
                print(f"\nProcessing user {user_id} ({count} active resumes)...")
                
                # Set all resumes to inactive first
                await conn.execute(text("""
                    UPDATE resumes
                    SET is_active = false
                    WHERE user_id = :user_id
                """), {"user_id": user_id})
                
                # Set only the latest version to active
                await conn.execute(text("""
                    UPDATE resumes
                    SET is_active = true
                    WHERE id = (
                        SELECT id
                        FROM resumes
                        WHERE user_id = :user_id
                        ORDER BY version DESC, created_at DESC
                        LIMIT 1
                    )
                """), {"user_id": user_id})
                
                print(f"  ✅ Fixed: Only latest version is now active")
            
            print("\n" + "="*60)
            print("✅ Cleanup completed successfully!")
            print(f"   - Fixed {len(duplicate_users)} users")
            print(f"   - Each user now has only 1 active resume (latest version)")
            print("="*60)
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        raise
    finally:
        await engine.dispose()


async def verify_cleanup():
    """Verify that cleanup was successful."""
    print("\nVerifying cleanup...")
    
    try:
        async with engine.begin() as conn:
            # Check for any remaining duplicates
            result = await conn.execute(text("""
                SELECT user_id, COUNT(*) as count
                FROM resumes
                WHERE is_active = true
                GROUP BY user_id
                HAVING COUNT(*) > 1
            """))
            
            duplicates = result.fetchall()
            
            if duplicates:
                print(f"⚠️  Still found {len(duplicates)} users with multiple active resumes")
                return False
            
            # Show summary
            result = await conn.execute(text("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(*) as total_resumes,
                    SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_resumes
                FROM resumes
            """))
            
            stats = result.fetchone()
            print("\nDatabase Summary:")
            print(f"  - Total users with resumes: {stats[0]}")
            print(f"  - Total resume records: {stats[1]}")
            print(f"  - Active resumes: {stats[2]}")
            print("  ✅ Each user has exactly 1 active resume")
            
            return True
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Resume Database Cleanup")
    print("=" * 60)
    print()
    
    asyncio.run(cleanup_active_resumes())
    asyncio.run(verify_cleanup())
