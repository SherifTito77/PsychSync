#!/usr/bin/env python
"""
Data Warehouse ETL Example

Demonstrates how to extract data from operational database
and load it into the team analytics data warehouse.

This ETL process:
1. Extracts: Raw data from operational tables (users, teams, assessments)
2. Transforms: Aggregates and calculates metrics
3. Loads: Populates dimension and fact tables

Usage:
    python -m app.etl.example_etl
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from app.analytics.dimensional_models import (
    DimAssessment,
    DimOrganization,
    DimTeam,
    DimUser,
    FactAssessmentCompletion,
    FactTeamMemberCount,
    FactUserEngagement,
)
from app.core.database import get_async_db
from app.db.models.assessment import Assessment, AssessmentResponse
from app.db.models.team import Team
from app.db.models.user import User


class DataWarehouseETL:
    """ETL process for team analytics data warehouse."""

    def __init__(self, db):
        self.db = db

    async def extract_organizations(self) -> List[dict]:
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Extract organization data."""
        print("📤 Extracting organizations...")

        query = """
            SELECT
                id,
                name,
                created_at,
                updated_at
            FROM organizations
        """
        results = await self.db.execute(query)
        orgs = results.fetchall()

        print(f"   ✅ Extracted {len(orgs)} organizations")
        return [dict(org) for org in orgs]

    async def extract_teams(self) -> List[dict]:
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Extract team data."""
        print("📤 Extracting teams...")

        query = """
            SELECT
                t.id,
                t.name,
                t.organization_id,
                t.created_by,
                t.created_at,
                t.updated_at,
                o.name as organization_name
            FROM teams t
            JOIN organizations o ON t.organization_id = o.id
        """
        results = await self.db.execute(query)
        teams = results.fetchall()

        print(f"   ✅ Extracted {len(teams)} teams")
        return [dict(team) for team in teams]

    async def extract_users(self) -> List[dict]:
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Extract user data with team associations."""
        print("📤 Extracting users...")

        query = """
            SELECT
                u.id,
                u.email,
                u.full_name,
                u.organization_id,
                tm.team_id,
                tm.role as team_role,
                u.created_at,
                u.updated_at
            FROM users u
            LEFT JOIN team_members tm ON u.id = tm.user_id
        """
        results = await self.db.execute(query)
        users = results.fetchall()

        print(f"   ✅ Extracted {len(users)} users")
        return [dict(user) for user in users]

    async def extract_assessments(self) -> List[dict]:
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Extract assessment data."""
        print("📤 Extracting assessments...")

        query = """
            SELECT
                a.id,
                a.title,
                a.framework_code,
                a.organization_id,
                a.team_id,
                a.created_by,
                a.created_at,
                a.updated_at,
                COUNT(ar.id) as response_count
            FROM assessments a
            LEFT JOIN assessment_responses ar ON a.id = ar.assessment_id
            GROUP BY a.id
        """
        results = await self.db.execute(query)
        assessments = results.fetchall()

        print(f"   ✅ Extracted {len(assessments)} assessments")
        return [dict(assessment) for assessment in assessments]

    async def extract_assessment_responses(self) -> List[dict]:
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Extract assessment response data for fact tables."""
        print("📤 Extracting assessment responses...")

        query = """
            SELECT
                ar.id,
                ar.assessment_id,
                ar.user_id,
                ar.team_id,
                ar.score,
                ar.max_score,
                ar.completed_at,
                a.framework_code
            FROM assessment_responses ar
            JOIN assessments a ON ar.assessment_id = a.id
            WHERE ar.completed_at IS NOT NULL
        """
        results = await self.db.execute(query)
        responses = results.fetchall()

        print(f"   ✅ Extracted {len(responses)} assessment responses")
        return [dict(response) for response in responses]

    async def load_dim_organization(self, orgs: List[dict]):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load organization dimension table."""
        print("\n📥 Loading DimOrganization...")

        for org in orgs:
            # Check if already exists
            existing = await self.db.execute(
                "SELECT id FROM dim_organization WHERE id = :org_id",
                {"org_id": org["id"]},
            )
            if existing.first():
                # Update
                await self.db.execute(
                    """
                    UPDATE dim_organization
                    SET name = :name,
                        updated_at = NOW()
                    WHERE id = :id
                    """,
                    org,
                )
            else:
                # Insert
                await self.db.execute(
                    """
                    INSERT INTO dim_organization (id, name, created_at, updated_at)
                    VALUES (:id, :name, :created_at, :updated_at)
                    """,
                    org,
                )

        await self.db.commit()
        print(f"   ✅ Loaded {len(orgs)} organizations")

    async def load_dim_team(self, teams: List[dict]):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load team dimension table."""
        print("\n📥 Loading DimTeam...")

        for team in teams:
            existing = await self.db.execute(
                "SELECT id FROM dim_team WHERE id = :team_id", {"team_id": team["id"]}
            )
            if existing.first():
                await self.db.execute(
                    """
                    UPDATE dim_team
                    SET name = :name,
                        organization_id = :organization_id,
                        updated_at = NOW()
                    WHERE id = :id
                    """,
                    team,
                )
            else:
                await self.db.execute(
                    """
                    INSERT INTO dim_team (id, name, organization_id, created_at, updated_at)
                    VALUES (:id, :name, :organization_id, :created_at, :updated_at)
                    """,
                    team,
                )

        await self.db.commit()
        print(f"   ✅ Loaded {len(teams)} teams")

    async def load_dim_user(self, users: List[dict]):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load user dimension table."""
        print("\n📥 Loading DimUser...")

        for user in users:
            existing = await self.db.execute(
                "SELECT id FROM dim_user WHERE id = :user_id", {"user_id": user["id"]}
            )
            if existing.first():
                await self.db.execute(
                    """
                    UPDATE dim_user
                    SET email = :email,
                        full_name = :full_name,
                        organization_id = :organization_id,
                        current_team_id = :team_id,
                        team_role = :team_role,
                        updated_at = NOW()
                    WHERE id = :id
                    """,
                    user,
                )
            else:
                await self.db.execute(
                    """
                    INSERT INTO dim_user
                    (id, email, full_name, organization_id, current_team_id, team_role, created_at, updated_at)
                    VALUES (:id, :email, :full_name, :organization_id, :team_id, :team_role, :created_at, :updated_at)
                    """,
                    user,
                )

        await self.db.commit()
        print(f"   ✅ Loaded {len(users)} users")

    async def load_dim_assessment(self, assessments: List[dict]):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load assessment dimension table."""
        print("\n📥 Loading DimAssessment...")

        for assessment in assessments:
            existing = await self.db.execute(
                "SELECT id FROM dim_assessment WHERE id = :assessment_id",
                {"assessment_id": assessment["id"]},
            )
            if existing.first():
                await self.db.execute(
                    """
                    UPDATE dim_assessment
                    SET title = :title,
                        framework_code = :framework_code,
                        organization_id = :organization_id,
                        team_id = :team_id,
                        updated_at = NOW()
                    WHERE id = :id
                    """,
                    assessment,
                )
            else:
                await self.db.execute(
                    """
                    INSERT INTO dim_assessment
                    (id, title, framework_code, organization_id, team_id, created_by, created_at, updated_at)
                    VALUES (:id, :title, :framework_code, :organization_id, :team_id, :created_by, :created_at, :updated_at)
                    """,
                    assessment,
                )

        await self.db.commit()
        print(f"   ✅ Loaded {len(assessments)} assessments")

    async def load_fact_team_member_count(self, teams: List[dict]):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load team member count fact table."""
        print("\n📥 Loading FactTeamMemberCount...")

        today = datetime.now().date()

        for team in teams:
            # Count members
            count_query = """
                SELECT COUNT(*) as member_count
                FROM team_members
                WHERE team_id = :team_id
            """
            result = await self.db.execute(count_query, {"team_id": team["id"]})
            member_count = result.first()["member_count"]

            # Insert or update fact
            existing = await self.db.execute(
                """
                SELECT id FROM fact_team_member_count
                WHERE team_id = :team_id AND date = :date
                """,
                {"team_id": team["id"], "date": today},
            )

            if existing.first():
                await self.db.execute(
                    """
                    UPDATE fact_team_member_count
                    SET member_count = :member_count,
                        updated_at = NOW()
                    WHERE team_id = :team_id AND date = :date
                    """,
                    {
                        "team_id": team["id"],
                        "date": today,
                        "member_count": member_count,
                    },
                )
            else:
                await self.db.execute(
                    """
                    INSERT INTO fact_team_member_count (team_id, date, member_count)
                    VALUES (:team_id, :date, :member_count)
                    """,
                    {
                        "team_id": team["id"],
                        "date": today,
                        "member_count": member_count,
                    },
                )

        await self.db.commit()
        print(f"   ✅ Loaded {len(teams)} team member counts")

    async def load_fact_assessment_completion(self, responses: List[dict]):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load assessment completion fact table."""
        print("\n📥 Loading FactAssessmentCompletion...")

        for response in responses:
            completed_date = response["completed_at"].date()

            existing = await self.db.execute(
                """
                SELECT id FROM fact_assessment_completion
                WHERE assessment_id = :assessment_id AND date = :date
                """,
                {"assessment_id": response["assessment_id"], "date": completed_date},
            )

            if existing.first():
                # Update count
                await self.db.execute(
                    """
                    UPDATE fact_assessment_completion
                    SET completion_count = completion_count + 1,
                        updated_at = NOW()
                    WHERE assessment_id = :assessment_id AND date = :date
                    """,
                    {
                        "assessment_id": response["assessment_id"],
                        "date": completed_date,
                    },
                )
            else:
                # Insert new record
                await self.db.execute(
                    """
                    INSERT INTO fact_assessment_completion
                    (assessment_id, date, completion_count)
                    VALUES (:assessment_id, :date, 1)
                    """,
                    {
                        "assessment_id": response["assessment_id"],
                        "date": completed_date,
                    },
                )

        await self.db.commit()
        print(f"   ✅ Loaded assessment completion facts")

    async def load_fact_user_engagement(self):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Load user engagement fact table."""
        print("\n📥 Loading FactUserEngagement...")

        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        # Calculate engagement metrics for each user
        query = """
            SELECT
                u.id as user_id,
                u.organization_id,
                COUNT(DISTINCT ar.assessment_id) as assessments_completed,
                COUNT(DISTINCT ar.id) as total_responses,
                AVG(ar.score) as avg_score
            FROM users u
            LEFT JOIN assessment_responses ar ON u.id = ar.user_id
                AND ar.completed_at >= :week_ago
            GROUP BY u.id, u.organization_id
        """
        results = await self.db.execute(query, {"week_ago": week_ago})
        users = results.fetchall()

        for user in users:
            existing = await self.db.execute(
                """
                SELECT id FROM fact_user_engagement
                WHERE user_id = :user_id AND date = :date
                """,
                {"user_id": user["user_id"], "date": today},
            )

            engagement_data = {
                "user_id": user["user_id"],
                "date": today,
                "assessments_completed": user["assessments_completed"] or 0,
                "total_responses": user["total_responses"] or 0,
                "avg_score": float(user["avg_score"]) if user["avg_score"] else 0.0,
                "last_active_at": datetime.now(),
            }

            if existing.first():
                await self.db.execute(
                    """
                    UPDATE fact_user_engagement
                    SET assessments_completed = :assessments_completed,
                        total_responses = :total_responses,
                        avg_score = :avg_score,
                        last_active_at = :last_active_at,
                        updated_at = NOW()
                    WHERE user_id = :user_id AND date = :date
                    """,
                    engagement_data,
                )
            else:
                await self.db.execute(
                    """
                    INSERT INTO fact_user_engagement
                    (user_id, date, assessments_completed, total_responses, avg_score, last_active_at)
                    VALUES (:user_id, :date, :assessments_completed, :total_responses, :avg_score, :last_active_at)
                    """,
                    engagement_data,
                )

        await self.db.commit()
        print(f"   ✅ Loaded {len(users)} user engagement records")

    async def run_full_etl(self):
        """Perform operation.

        Args:
            **kwargs: Input parameters

        Returns:
            Operation result
        """
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        """Run complete ETL process."""
        print("\n" + "=" * 80)
        print("DATA WAREHOUSE ETL - PsychSync Team Analytics")
        print("=" * 80)

        start_time = datetime.now()

        # Extract
        print("\n🔹 EXTRACT PHASE")
        orgs = await self.extract_organizations()
        teams = await self.extract_teams()
        users = await self.extract_users()
        assessments = await self.extract_assessments()
        responses = await self.extract_assessment_responses()

        # Transform & Load Dimensions
        print("\n🔹 LOAD DIMENSION TABLES")
        await self.load_dim_organization(orgs)
        await self.load_dim_team(teams)
        await self.load_dim_user(users)
        await self.load_dim_assessment(assessments)

        # Transform & Load Facts
        print("\n🔹 LOAD FACT TABLES")
        await self.load_fact_team_member_count(teams)
        await self.load_fact_assessment_completion(responses)
        await self.load_fact_user_engagement()

        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 80)
        print(f"✅ ETL Complete! ({elapsed:.2f}s)")
        print("=" * 80)
        print("\n📊 Data Warehouse Stats:")
        print(f"   Organizations: {len(orgs)}")
        print(f"   Teams: {len(teams)}")
        print(f"   Users: {len(users)}")
        print(f"   Assessments: {len(assessments)}")
        print(f"   Responses: {len(responses)}")
        print("\n💡 Next Steps:")
        print("   - Query fact tables for analytics")
        print("   - Build dashboards with dimensional data")
        print("   - Schedule ETL to run daily/weekly")
        print()


async def main():
    """Perform operation.

    Args:
        **kwargs: Input parameters

    Returns:
        Operation result
    """
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    """Run ETL process."""
    async for db in get_async_db():
        etl = DataWarehouseETL(db)
        await etl.run_full_etl()
        break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ ETL Error: {e}")
        import traceback

        traceback.print_exc()
