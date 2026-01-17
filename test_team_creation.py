#!/usr/bin/env python3
# test_team_creation.py - Debug team creation

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, '/Users/sheriftito/Downloads/psychsync')

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.team import Team
from app.schemas.team import TeamCreate
import uuid

async def debug_team_creation():
    """Debug the team creation process"""

    print("🔍 Debug Team Creation")
    print("======================")

    try:
        async with AsyncSessionLocal() as db:
            # Step 1: Check organizations
            result = await db.execute(text("SELECT id, name FROM organizations"))
            orgs = result.fetchall()
            print(f"Found {len(orgs)} organizations:")
            for org in orgs:
                print(f"  - {org[0]}: {org[1]}")

            if not orgs:
                print("❌ No organizations found!")
                return False

            # Step 2: Get a test user
            result = await db.execute(text("SELECT id, email FROM users LIMIT 1"))
            user_row = result.fetchone()
            if not user_row:
                print("❌ No users found!")
                return False

            user_id = user_row[0]
            print(f"Using user: {user_row[1]} ({user_id})")

            # Step 3: Try creating team manually
            org_id = orgs[0][0]
            print(f"Using organization: {org_id}")

            try:
                # First test direct SQL insertion
                team_id = str(uuid.uuid4())
                result = await db.execute(text("""
                    INSERT INTO teams (id, name, description, created_by_id, organization_id, created_at, updated_at)
                    VALUES (:team_id, :name, :description, :user_id, :org_id, NOW(), NOW())
                    RETURNING id
                """), {
                    "team_id": team_id,
                    "name": "Test Team SQL",
                    "description": "Direct SQL test",
                    "user_id": user_id,
                    "org_id": org_id
                })

                await db.commit()
                print(f"✅ Direct SQL team creation successful: {team_id}")

            except Exception as e:
                print(f"❌ Direct SQL team creation failed: {e}")
                await db.rollback()

            # Step 4: Try using ORM model
            try:
                team_data = TeamCreate(name="Test Team ORM", description="ORM test")
                new_team = Team(
                    name=team_data.name,
                    description=team_data.description,
                    created_by_id=user_id,
                    organization_id=org_id
                )

                db.add(new_team)
                await db.commit()
                await db.refresh(new_team)

                print(f"✅ ORM team creation successful: {new_team.id}")

            except Exception as e:
                print(f"❌ ORM team creation failed: {e}")
                await db.rollback()

            # Step 5: Check final team count
            result = await db.execute(text("SELECT COUNT(*) FROM teams"))
            team_count = result.scalar()
            print(f"Total teams after tests: {team_count}")

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

    print("\n✅ Team creation debug completed")
    return True

if __name__ == "__main__":
    asyncio.run(debug_team_creation())
