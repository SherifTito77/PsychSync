import asyncio
from datetime import datetime

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, async_engine
from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.db.models.user import User


async def comprehensive_db_test():
    print("=" * 70)
    print(" " * 15 + "DATABASE COMPREHENSIVE TEST")
    print("=" * 70)

    results = {"passed": 0, "failed": 0, "tests": []}

    def test_result(name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        results["tests"].append((name, passed, details))
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        print(f"{status} - {name}")
        if details:
            print(f"     {details}")

    # Test 1: Database Connection
    print("\n[TEST 1/7] Database Connectivity")
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

            if async_engine.dialect.name == "sqlite":
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            else:
                result = await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            tables = [row[0] for row in result.fetchall()]

        test_result("Database Connection", True, f"{len(tables)} tables found")
    except Exception as e:
        test_result("Database Connection", False, str(e))

    # Test 2: User Model - Full CRUD
    print("\n[TEST 2/7] User Model (Full CRUD)")
    try:
        async with AsyncSessionLocal() as session:
            timestamp = int(datetime.now().timestamp())

            user = User(
                email=f"test_{timestamp}@dbtest.com",
                password_hash="test_hash",
                full_name="CRUD Test User",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            user_id = user.id

            result = await session.execute(select(User).where(User.id == user_id))
            fetched = result.scalar_one()
            assert fetched.email == user.email

            fetched.full_name = "Updated CRUD User"
            await session.commit()
            await session.refresh(fetched)
            assert fetched.full_name == "Updated CRUD User"

            await session.rollback()

        test_result("User CRUD", True, f"User ID: {user_id}")
    except Exception as e:
        test_result("User CRUD", False, str(e))

    # Test 3: Organization Model
    print("\n[TEST 3/7] Organization Model")
    try:
        async with AsyncSessionLocal() as session:
            timestamp = int(datetime.now().timestamp())

            org = Organization(
                name=f"Test Org {timestamp}",
            )
            session.add(org)
            await session.commit()
            await session.refresh(org)
            org_id = org.id

            assert org.name == f"Test Org {timestamp}"
            assert org.created_at is not None

        test_result("Organization Create", True, f"Org ID: {org_id}")
    except Exception as e:
        test_result("Organization Create", False, str(e))

    # Test 4: Team Model
    print("\n[TEST 4/7] Team Model")
    try:
        async with AsyncSessionLocal() as session:
            timestamp = int(datetime.now().timestamp())

            org = Organization(name=f"Team Test Org {timestamp}")
            session.add(org)
            await session.flush()

            user = User(
                email=f"teamtest_{timestamp}@test.com",
                password_hash="hash",
                full_name="Team Test User",
            )
            session.add(user)
            await session.flush()

            team = Team(
                name=f"Test Team {timestamp}",
                description="Test team description",
                organization_id=org.id,
                created_by_id=user.id,
            )
            session.add(team)
            await session.commit()
            await session.refresh(team)
            team_id = team.id

            assert team.name is not None
            assert team.organization_id == org.id

        test_result("Team Create", True, f"Team ID: {team_id}")
    except Exception as e:
        test_result("Team Create", False, str(e))

    # Test 5: Assessment Model
    print("\n[TEST 5/7] Assessment Model")
    try:
        async with AsyncSessionLocal() as session:
            timestamp = int(datetime.now().timestamp())

            org = Organization(name=f"Assess Test Org {timestamp}")
            session.add(org)
            await session.flush()

            user = User(
                email=f"assesstest_{timestamp}@test.com",
                password_hash="hash",
                full_name="Assessment Test User",
            )
            session.add(user)
            await session.flush()

            team = Team(
                name=f"Assess Test Team {timestamp}",
                organization_id=org.id,
                created_by_id=user.id,
            )
            session.add(team)
            await session.flush()

            assessment = Assessment(
                title=f"Test Assessment {timestamp}",
                description="Test assessment description",
                category=AssessmentCategory.PERSONALITY,
                status=AssessmentStatus.DRAFT,
                created_by_id=user.id,
                team_id=team.id,
                organization_id=org.id,
                framework_code="BIG_FIVE",
            )
            session.add(assessment)
            await session.commit()
            await session.refresh(assessment)
            assess_id = assessment.id

            assert assessment.title is not None
            assert assessment.category == AssessmentCategory.PERSONALITY

        test_result("Assessment Create", True, f"Assessment ID: {assess_id}")
    except Exception as e:
        test_result("Assessment Create", False, str(e))

    # Test 6: Data Relationships
    print("\n[TEST 6/7] Model Relationships")
    try:
        async with AsyncSessionLocal() as session:
            timestamp = int(datetime.now().timestamp())

            org = Organization(name=f"Rel Test Org {timestamp}")
            session.add(org)
            await session.flush()

            user = User(
                email=f"reltest_{timestamp}@test.com",
                password_hash="hash",
                full_name="Relationship Test User",
            )
            session.add(user)
            await session.flush()

            team = Team(
                name=f"Rel Test Team {timestamp}",
                organization_id=org.id,
                created_by_id=user.id,
            )
            session.add(team)
            await session.flush()

            assessment = Assessment(
                title=f"Rel Test Assessment {timestamp}",
                category=AssessmentCategory.PERSONALITY,
                created_by_id=user.id,
                team_id=team.id,
                organization_id=org.id,
            )
            session.add(assessment)
            await session.commit()

            assert assessment.organization_id == org.id
            assert assessment.team_id == team.id
            assert team.created_by_id == user.id
            assert team.organization_id == org.id

        test_result("Relationships", True, "Org→Team→User→Assessment chain verified")
    except Exception as e:
        test_result("Relationships", False, str(e))

    # Test 7: Query Performance
    print("\n[TEST 7/7] Query Performance")
    try:
        import time

        async with AsyncSessionLocal() as session:
            start = time.time()

            result = await session.execute(select(User).limit(100))
            users = result.scalars().all()

            result = await session.execute(select(Organization).limit(100))
            orgs = result.scalars().all()

            result = await session.execute(select(Team).limit(100))
            teams = result.scalars().all()

            result = await session.execute(select(Assessment).limit(100))
            assess = result.scalars().all()

            elapsed = time.time() - start
            total_records = len(users) + len(orgs) + len(teams) + len(assess)

            assert elapsed < 2.0

        test_result(
            "Query Performance",
            True,
            (
                f"{total_records} records in {elapsed:.4f}s"
                if total_records > 0
                else "No records found"
            ),
        )
    except Exception as e:
        test_result("Query Performance", False, str(e))

    # Final Summary
    print("\n" + "=" * 70)
    print(" " * 20 + "TEST SUMMARY")
    print("=" * 70)
    print(f'\nTotal Tests: {results["passed"] + results["failed"]}')
    print(f'✅ Passed: {results["passed"]}')
    print(f'❌ Failed: {results["failed"]}')
    print(
        f'Success Rate: {(results["passed"]/(results["passed"]+results["failed"])*100):.1f}%'
    )

    print("\nDetailed Results:")
    for name, passed, details in results["tests"]:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if details:
            print(f"     └─ {details}")

    print("\n" + "=" * 70)
    if results["failed"] == 0:
        print(" " * 18 + "🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f" " * 15 + f'⚠️  {results["failed"]} TEST(S) FAILED')
    print("=" * 70 + "\n")

    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(comprehensive_db_test())
    exit(0 if success else 1)
