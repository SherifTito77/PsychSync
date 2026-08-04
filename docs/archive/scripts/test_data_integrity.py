#!/usr/bin/env python3
"""Data integrity validation for PsychSync"""

import asyncio
import sys

from sqlalchemy import func, select, text

from app.core.database import AsyncSessionLocal
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.db.models.team_member import TeamMember
from app.db.models.user import User


async def check_data_integrity():
    """Check for data inconsistencies"""
    print("🔍 PsychSync Data Integrity Validation")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        try:
            # Check user table
            print("\n1. Users table...")
            user_count = await session.execute(select(func.count(User.id)))
            print(f"   Total users: {user_count.scalar()}")

            # Check for users with valid emails
            valid_emails = await session.execute(
                select(func.count(User.id)).where(User.email.like("%@%"))
            )
            print(f"   Users with valid emails: {valid_emails.scalar()}")

            # Check teams table
            print("\n2. Teams table...")
            team_count = await session.execute(select(func.count(Team.id)))
            print(f"   Total teams: {team_count.scalar()}")

            # Check organizations table
            print("\n3. Organizations table...")
            org_count = await session.execute(select(func.count(Organization.id)))
            print(f"   Total organizations: {org_count.scalar()}")

            # Check team members table
            print("\n4. Team members table...")
            member_count = await session.execute(select(func.count(TeamMember.id)))
            print(f"   Total team members: {member_count.scalar()}")

            # Check for orphaned records (users without organizations)
            print("\n5. Checking for data integrity issues...")

            # Users with invalid organization references
            orphaned_users = await session.execute(
                text(
                    """
                SELECT COUNT(*) FROM users
                WHERE organization_id IS NOT NULL
                AND organization_id NOT IN (SELECT id FROM organizations)
            """
                )
            )
            orphaned_user_count = orphaned_users.scalar()
            print(
                f"   Users with invalid organization references: {orphaned_user_count}"
            )

            # Team members with invalid team references
            orphaned_members = await session.execute(
                text(
                    """
                SELECT COUNT(*) FROM team_members tm
                LEFT JOIN teams t ON tm.team_id = t.id
                WHERE t.id IS NULL
            """
                )
            )
            orphaned_member_count = orphaned_members.scalar()
            print(
                f"   Team members with invalid team references: {orphaned_member_count}"
            )

            # Team members with invalid user references
            invalid_user_members = await session.execute(
                text(
                    """
                SELECT COUNT(*) FROM team_members tm
                LEFT JOIN users u ON tm.user_id = u.id
                WHERE u.id IS NULL
            """
                )
            )
            invalid_user_member_count = invalid_user_members.scalar()
            print(
                f"   Team members with invalid user references: {invalid_user_member_count}"
            )

            # Summary
            print("\n" + "=" * 50)
            print("📊 DATA INTEGRITY SUMMARY")
            print("=" * 50)

            integrity_issues = [
                ("Orphaned Users", orphaned_user_count),
                ("Orphaned Team Members", orphaned_member_count),
                ("Invalid User References", invalid_user_member_count),
            ]

            all_good = True
            for issue_name, count in integrity_issues:
                status = "✅ OK" if count == 0 else f"❌ {count} issues"
                print(f"{issue_name:30} {status}")
                if count > 0:
                    all_good = False

            print("=" * 50)
            if all_good:
                print("✅ Data integrity validation PASSED!")
                return 0
            else:
                print("❌ Data integrity validation FAILED!")
                return 1

        except Exception as e:
            print(f"❌ Data integrity check error: {e}")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(check_data_integrity())
    sys.exit(exit_code)
