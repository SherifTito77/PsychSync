"""
Create a simple test user for assessment taking
"""

import asyncio
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash


async def create_simple_user():
    """Create a simple test user"""
    db = AsyncSessionLocal()
    try:
        user_id = uuid4()
        hashed_password = get_password_hash("XyZ$7pQwErt9!mN")

        # Get default organization
        result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
        org_row = result.fetchone()
        org_id = org_row[0] if org_row else None

        await db.execute(
            text(
                """
            INSERT INTO users (
                id, email, full_name, password_hash, is_active, organization_id,
                created_at, updated_at
            ) VALUES (
                :id, :email, :full_name, :password_hash, :is_active, :org_id,
                NOW(), NOW()
            ) ON CONFLICT (email) DO UPDATE SET is_active = true
            """
            ),
            {
                "id": user_id,
                "email": "test_assessment@example.com",
                "full_name": "Test Assessment User",
                "password_hash": hashed_password,
                "is_active": True,
                "org_id": org_id,
            },
        )

        await db.commit()

        print("✅ Created test user:")
        print("   Email: test_assessment@example.com")
        print("   Password: XyZ$7pQwErt9!mN")

    except Exception as e:
        print(f"❌ Error: {e}")
        await db.rollback()
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(create_simple_user())
