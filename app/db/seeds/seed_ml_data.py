"""
Seed script to create ML training data (users and teams)
Simple seed to enable team management and assessment taking.

File path: app/db/seeds/seed_ml_data.py
"""

import asyncio
import random
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.db.models.team import TeamMember, TeamRole


async def create_test_users(db: AsyncSession, count: int = 10) -> list[UUID]:
    """Create test users for ML training"""
    user_ids = []

    for i in range(count):
        user_id = uuid4()
        user_ids.append(user_id)

        # Create secure password
        hashed_password = get_password_hash(f"SecureP@ss{i}7sQw3rT{10-i}!")

        await db.execute(
            text(
                """
            INSERT INTO users (
                id, email, full_name, password_hash, is_active,
                created_at, updated_at
            ) VALUES (
                :id, :email, :full_name, :password_hash, :is_active,
                NOW(), NOW()
            ) ON CONFLICT (email) DO NOTHING
            """
            ),
            {
                "id": user_id,
                "email": f"test_user_{i+1}@example.com",
                "full_name": f"Test User {i+1}",
                "password_hash": hashed_password,
                "is_active": True,
            },
        )

    await db.commit()
    print(f"✅ Created {len(user_ids)} test users")
    return user_ids


async def create_test_teams(db: AsyncSession, user_ids: list[UUID]) -> None:
    """Create test teams and assign users"""
    # Get default organization
    result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
    org_row = result.fetchone()
    org_id = org_row[0] if org_row else None

    # Create 3 test teams
    team_configs = [
        {"name": "Engineering Team", "description": "Software development team"},
        {"name": "Product Team", "description": "Product management team"},
        {"name": "Design Team", "description": "UX/UI design team"},
    ]

    team_ids = []
    for config in team_configs:
        result = await db.execute(
            text(
                """
            INSERT INTO teams (
                id, name, description, organization_id,
                created_at, updated_at, created_by_id
            ) VALUES (
                :id, :name, :description, :org_id,
                NOW(), NOW(), :created_by_id
            ) RETURNING id
            """
            ),
            {
                "id": uuid4(),
                "name": config["name"],
                "description": config["description"],
                "org_id": org_id,
                "created_by_id": user_ids[0] if user_ids else None,
            },
        )
        team_id = result.scalar()
        if team_id:
            team_ids.append(team_id)

    # Assign users to teams (3-5 members per team)
    users_per_team = max(3, len(user_ids) // len(team_ids))
    for i, team_id in enumerate(team_ids):
        start_idx = i * users_per_team
        end_idx = min(start_idx + users_per_team, len(user_ids))

        for user_idx in range(start_idx, end_idx):
            # First user is always owner for testing
            role = (
                TeamRole.OWNER.value if user_idx == start_idx else TeamRole.MEMBER.value
            )

            await db.execute(
                text(
                    """
                INSERT INTO team_members (
                    id, team_id, user_id, role
                ) VALUES (
                    :id, :team_id, :user_id, :role
                )
                """
                ),
                {
                    "id": uuid4(),
                    "team_id": team_id,
                    "user_id": user_ids[user_idx],
                    "role": role,
                },
            )

    await db.commit()
    print(f"✅ Created {len(team_ids)} teams with members")


async def verify_data(db: AsyncSession) -> None:
    """Verify seeded data"""
    # Count users
    result = await db.execute(text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()

    # Count teams
    result = await db.execute(text("SELECT COUNT(*) FROM teams"))
    team_count = result.scalar()

    # Count team members
    result = await db.execute(text("SELECT COUNT(*) FROM team_members"))
    member_count = result.scalar()

    # Show sample users
    result = await db.execute(text("SELECT email FROM users LIMIT 3"))
    sample_users = [row[0] for row in result]

    print("\n" + "=" * 60)
    print("📊 Test Data Summary")
    print("=" * 60)
    print(f"  Total Users: {user_count}")
    print(f"  Total Teams: {team_count}")
    print(f"  Total Team Members: {member_count}")
    print("\n  Sample users:")
    for i, email in enumerate(sample_users, 1):
        print(
            f"    {i}. {email} (password: SecureP@ss{len(sample_users)-i}7sQw3rT{10-len(sample_users)+i}!)"
        )
    print("=" * 60)


async def run_seed():
    """Main function to run ML data seeding"""
    db = AsyncSessionLocal()
    try:
        print("=" * 60)
        print("Starting test data seed...")
        print("=" * 60)

        # Create test users
        user_ids = await create_test_users(db, count=10)

        # Create test teams
        result = await db.execute(text("SELECT id FROM teams"))
        existing_teams = [row[0] for row in result]

        if not existing_teams:
            await create_test_teams(db, user_ids)
        else:
            print("ℹ️  Teams already exist, skipping team creation")

        # Verify data
        await verify_data(db)

        print("\n✅ Test data seed completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        await db.rollback()
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(run_seed())
