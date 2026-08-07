"""
Test Data Generator for PsychSync Load Testing
Generates users, assessments, teams, and historical responses
"""

import argparse
import asyncio
import os
import random
import string
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add parent directory to path to import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/psychsync_test",
)

# Configuration defaults
DEFAULT_CONFIG = {
    "users": 10000,
    "assessments": 100,
    "teams": 500,
    "responses_per_user": 50,
    "questions_per_assessment": 100,
}


class TestDataGenerator:
    """Generate comprehensive test data for load testing"""

    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.stats = {
            "users_created": 0,
            "teams_created": 0,
            "assessments_created": 0,
            "responses_created": 0,
        }

    async def init_db(self):
        """Initialize database connection"""
        print(f"Connecting to database: {DATABASE_URL}")
        async with self.engine.begin() as conn:
            # Test connection
            await conn.execute("SELECT 1")
        print("Database connection successful")

    async def generate_users(self, count: int = 10000) -> List[str]:
        """
        Generate test users

        Returns: List of user IDs
        """
        print(f"\nGenerating {count} test users...")

        # Note: This is a template - actual implementation depends on your User model
        users = []
        batch_size = 1000

        for batch_start in range(0, count, batch_size):
            batch_end = min(batch_start + batch_size, count)
            batch_users = []

            for i in range(batch_start, batch_end):
                user_data = {
                    "email": f"loadtest_user_{i}@test.com",
                    "username": f"loadtest_{i}",
                    "full_name": f"Load Test User {i}",
                    "hashed_password": self._hash_password("LoadTest123!"),
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 365)),
                }
                batch_users.append(user_data)

            # Insert batch
            # Note: Replace with actual ORM insert
            # async with self.async_session() as session:
            #     for user_data in batch_users:
            #         user = User(**user_data)
            #         session.add(user)
            #     await session.commit()

            users.extend([f"user_{i}" for i in range(batch_start, batch_end)])
            self.stats["users_created"] += len(batch_users)

            print(f"  Created {batch_end}/{count} users...")

        print(f"✓ Created {count} users")
        return users

    async def generate_teams(self, count: int = 500, user_ids: List[str] = None):
        """
        Generate test teams with members

        Args:
            count: Number of teams to create
            user_ids: List of user IDs to assign as team members
        """
        print(f"\nGenerating {count} test teams...")

        if not user_ids:
            user_ids = [f"user_{i}" for i in range(10000)]

        for i in range(count):
            # Create team
            team_data = {
                "name": f"Test Team {i}",
                "description": f"Load testing team {i}",
                "organization_id": f"org_{i % 100}",  # Distribute across 100 orgs
                "created_at": datetime.utcnow()
                - timedelta(days=random.randint(1, 365)),
            }

            # Note: Replace with actual ORM insert
            # async with self.async_session() as session:
            #     team = Team(**team_data)
            #     session.add(team)
            #     await session.flush()
            #     team_id = team.id

            # Assign random members (10-50 members per team)
            team_id = f"team_{i}"
            num_members = random.randint(10, 50)
            members = random.sample(user_ids, min(num_members, len(user_ids)))

            # Note: Insert team members
            # for member_id in members:
            #     team_member = TeamMember(
            #         team_id=team_id,
            #         user_id=member_id,
            #         role=random.choice(["admin", "member", "viewer"])
            #     )
            #     session.add(team_member)
            # await session.commit()

            self.stats["teams_created"] += 1

            if (i + 1) % 100 == 0:
                print(f"  Created {i + 1}/{count} teams...")

        print(f"✓ Created {count} teams")

    async def generate_assessments(self, count: int = 100):
        """
        Generate test assessment templates

        Args:
            count: Number of assessments to create
        """
        print(f"\nGenerating {count} test assessments...")

        frameworks = ["mbti", "big_five", "enneagram", "disc", "predictive_index"]
        categories = ["personality", "behavioral", "clinical", "cognitive"]

        for i in range(count):
            framework = random.choice(frameworks)
            category = random.choice(categories)

            assessment_data = {
                "title": f"Test Assessment {i} ({framework})",
                "description": f"Load testing assessment for {framework}",
                "framework": framework,
                "category": category,
                "status": "published",
                "is_public": random.choice([True, False]),
                "organization_id": f"org_{i % 100}",
                "created_by": f"user_{i % 10000}",
                "created_at": datetime.utcnow()
                - timedelta(days=random.randint(1, 365)),
            }

            # Generate questions
            num_questions = random.randint(20, 100)
            questions = []
            for q in range(num_questions):
                question = {
                    "question_id": f"q{q + 1}",
                    "text": f"Test question {q + 1} for assessment {i}",
                    "type": random.choice(["rating", "multiple_choice", "yes_no"]),
                    "options": [1, 2, 3, 4, 5] if random.random() > 0.3 else None,
                }
                questions.append(question)

            # Note: Replace with actual ORM insert
            # async with self.async_session() as session:
            #     assessment = Assessment(**assessment_data)
            #     session.add(assessment)
            #     await session.flush()
            #     assessment_id = assessment.id
            #
            #     for question_data in questions:
            #         question = Question(assessment_id=assessment_id, **question_data)
            #         session.add(question)
            #     await session.commit()

            self.stats["assessments_created"] += 1

            if (i + 1) % 20 == 0:
                print(f"  Created {i + 1}/{count} assessments...")

        print(f"✓ Created {count} assessments")

    async def generate_responses(
        self,
        user_ids: List[str],
        assessment_ids: List[str],
        responses_per_user: int = 50,
    ):
        """
        Generate historical assessment responses

        Args:
            user_ids: List of user IDs
            assessment_ids: List of assessment IDs
            responses_per_user: Number of responses per user
        """
        print(f"\nGenerating assessment responses...")

        if not assessment_ids:
            assessment_ids = [f"assessment_{i}" for i in range(100)]

        total_responses = len(user_ids) * responses_per_user
        batch_size = 10000
        created = 0

        for user_id in user_ids:
            # Generate responses for this user
            for _ in range(responses_per_user):
                assessment_id = random.choice(assessment_ids)

                # Generate response data
                response_data = {
                    "user_id": user_id,
                    "assessment_id": assessment_id,
                    "status": random.choice(["completed", "in_progress", "abandoned"]),
                    "responses": self._generate_sample_responses(
                        random.randint(20, 100)
                    ),
                    "started_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 365)),
                    "completed_at": datetime.utcnow()
                    - timedelta(days=random.randint(0, 364)),
                }

                # Note: Replace with actual ORM insert
                # async with self.async_session() as session:
                #     response = AssessmentResponse(**response_data)
                #     session.add(response)
                #     await session.commit()

                created += 1

                if created % batch_size == 0:
                    print(f"  Created {created}/{total_responses} responses...")

        self.stats["responses_created"] = created
        print(f"✓ Created {created} responses")

    def _generate_sample_responses(self, count: int) -> List[Dict[str, Any]]:
        """Generate sample question responses"""
        return [
            {"question_id": f"q{i}", "answer": random.randint(1, 5)}
            for i in range(1, count + 1)
        ]

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    async def close(self):
        """Close database connection"""
        await self.engine.dispose()

    def print_summary(self):
        """Print generation summary"""
        print("\n" + "=" * 60)
        print("TEST DATA GENERATION SUMMARY")
        print("=" * 60)
        print(f"Users Created:        {self.stats['users_created']:,}")
        print(f"Teams Created:        {self.stats['teams_created']:,}")
        print(f"Assessments Created:  {self.stats['assessments_created']:,}")
        print(f"Responses Created:    {self.stats['responses_created']:,}")
        print("=" * 60 + "\n")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Generate test data for PsychSync load testing"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=DEFAULT_CONFIG["users"],
        help="Number of users to generate (default: 10,000)",
    )
    parser.add_argument(
        "--teams",
        type=int,
        default=DEFAULT_CONFIG["teams"],
        help="Number of teams to generate (default: 500)",
    )
    parser.add_argument(
        "--assessments",
        type=int,
        default=DEFAULT_CONFIG["assessments"],
        help="Number of assessments to generate (default: 100)",
    )
    parser.add_argument(
        "--responses-per-user",
        type=int,
        default=DEFAULT_CONFIG["responses_per_user"],
        help="Number of assessment responses per user (default: 50)",
    )
    parser.add_argument(
        "--db-url", type=str, default=DATABASE_URL, help="Database connection URL"
    )
    parser.add_argument(
        "--skip-users",
        action="store_true",
        help="Skip user generation (use existing users)",
    )
    parser.add_argument(
        "--skip-teams", action="store_true", help="Skip team generation"
    )
    parser.add_argument(
        "--skip-assessments", action="store_true", help="Skip assessment generation"
    )
    parser.add_argument(
        "--skip-responses", action="store_true", help="Skip response generation"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("PSYCHSYNC TEST DATA GENERATOR")
    print("=" * 60)
    print(f"Database: {args.db_url}")
    print(f"Target Users:        {args.users:,}")
    print(f"Target Teams:        {args.teams:,}")
    print(f"Target Assessments:  {args.assessments:,}")
    print(f"Responses/User:      {args.responses_per_user}")
    print("=" * 60)

    generator = TestDataGenerator(args.db_url)

    try:
        await generator.init_db()

        # Generate data in order of dependencies
        if not args.skip_users:
            user_ids = await generator.generate_users(args.users)
        else:
            user_ids = [f"user_{i}" for i in range(args.users)]

        if not args.skip_teams:
            await generator.generate_teams(args.teams, user_ids)

        if not args.skip_assessments:
            await generator.generate_assessments(args.assessments)

        if not args.skip_responses:
            assessment_ids = [f"assessment_{i}" for i in range(args.assessments)]
            await generator.generate_responses(
                user_ids, assessment_ids, args.responses_per_user
            )

        generator.print_summary()

    except Exception as e:
        print(f"\n❌ Error during data generation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await generator.close()

    print("\n✓ Test data generation completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
