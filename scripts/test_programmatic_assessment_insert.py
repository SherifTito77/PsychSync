#!/usr/bin/env python
"""
Test Programmatic Assessment Data Insertion

This script validates that the schema fixes enable direct data insertion
without foreign key relationship issues or multiple answer column confusion.

Usage:
    python scripts/test_programmatic_assessment_insert.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.db.models.assessment import Assessment, AssessmentQuestion, AssessmentSection
from app.db.models.response import Response
from app.db.models.user import User


async def create_test_assessment_flow():
    """
    Test complete assessment data flow from creation to response insertion.

    This validates:
    1. Assessment creation
    2. Section creation
    3. Question creation
    4. Direct response insertion (programmatic)
    5. Query verification
    """
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        # Create tables if they don't exist
        # This ensures we can test even on fresh database
        from app.db.base_class import Base

        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        print("Testing Programmatic Assessment Data Insertion")
        print("=" * 60)

        # Step 1: Create test user
        print("\n1. Creating test user...")
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
        )
        session.add(user)
        await session.flush()
        print(f"   ✓ User created: {user.id}")

        # Step 2: Create assessment
        print("\n2. Creating assessment...")
        assessment = Assessment(
            title="Test Assessment",
            description="A test assessment for schema validation",
            category="personality",
            status="published",
            created_by_id=user.id,
        )
        session.add(assessment)
        await session.flush()
        print(f"   ✓ Assessment created: {assessment.id}")

        # Step 3: Create section
        print("\n3. Creating assessment section...")
        section = AssessmentSection(
            assessment_id=assessment.id,
            title="Section 1",
            description="First section",
            order=0,
        )
        session.add(section)
        await session.flush()
        print(f"   ✓ Section created: {section.id}")

        # Step 4: Create multiple question types
        print("\n4. Creating assessment questions...")
        questions = []

        # Text question
        text_question = AssessmentQuestion(
            section_id=section.id,
            question_type="text",
            question_text="What motivates you?",
            order=1,
            is_required=True,
        )
        session.add(text_question)
        await session.flush()
        questions.append(("text", text_question))
        print(f"   ✓ Text question created: {text_question.id}")

        # Scale question (1-5)
        scale_question = AssessmentQuestion(
            section_id=section.id,
            question_type="scale",
            question_text="How satisfied are you?",
            order=2,
            is_required=True,
            config={
                "min": 1,
                "max": 5,
                "labels": ["Very Dissatisfied", "Very Satisfied"],
            },
        )
        session.add(scale_question)
        await session.flush()
        questions.append(("scale", scale_question))
        print(f"   ✓ Scale question created: {scale_question.id}")

        # Multiple choice question
        mc_question = AssessmentQuestion(
            section_id=section.id,
            question_type="multiple_choice",
            question_text="Which activities do you enjoy?",
            order=3,
            is_required=True,
            config={
                "options": ["Reading", "Sports", "Music", "Travel"],
                "allow_multiple": True,
            },
        )
        session.add(mc_question)
        await session.flush()
        questions.append(("multiple_choice", mc_question))
        print(f"   ✓ Multiple choice question created: {mc_question.id}")

        # Commit all changes before inserting responses
        await session.commit()

        # Step 5: Test programmatic response insertion
        print("\n5. Testing programmatic response insertion...")

        # Insert text response using answer_text
        text_response = Response(
            assessment_id=assessment.id,
            user_id=user.id,
            question_id=text_question.id,
            answer_text="I am motivated by learning new things and helping others.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(text_response)
        await session.flush()
        print(f"   ✓ Text response inserted (answer_text)")

        # Insert scale response using answer_value
        scale_response = Response(
            assessment_id=assessment.id,
            user_id=user.id,
            question_id=scale_question.id,
            answer_value=4,
            score=0.8,  # Normalized: 4/5 = 0.8
            response_time_ms=2500,  # 2.5 seconds
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(scale_response)
        await session.flush()
        print(f"   ✓ Scale response inserted (answer_value)")

        # Insert multiple choice response using answer_data
        mc_response = Response(
            assessment_id=assessment.id,
            user_id=user.id,
            question_id=mc_question.id,
            answer_data={"choices": ["Reading", "Music"]},
            confidence_rating=5,  # Very confident
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(mc_response)
        await session.flush()
        print(f"   ✓ Multiple choice response inserted (answer_data)")

        await session.commit()

        # Step 6: Verify data retrieval
        print("\n6. Verifying data retrieval...")

        # Query all responses for the assessment
        result = await session.execute(
            select(Response)
            .where(Response.assessment_id == assessment.id)
            .where(Response.user_id == user.id)
        )
        responses = result.scalars().all()

        print(f"   ✓ Retrieved {len(responses)} responses")

        # Verify each response type
        for resp in responses:
            if resp.answer_text:
                print(f"      - Text answer: '{resp.answer_text[:30]}...'")
            elif resp.answer_value:
                print(
                    f"      - Scale answer: {resp.answer_value} (normalized: {resp.normalized_score or 'N/A'})"
                )
            elif resp.answer_data:
                print(f"      - Data answer: {resp.answer_data}")

        # Step 7: Test complex query with joins
        print("\n7. Testing complex query with joins...")

        # Query responses with question details
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(Response)
            .select_from(Response)
            .join(AssessmentQuestion, Response.question_id == AssessmentQuestion.id)
            .where(Response.assessment_id == assessment.id)
            .order_by(AssessmentQuestion.order)
        )
        responses_with_questions = result.scalars().all()

        print(
            f"   ✓ Retrieved {len(responses_with_questions)} responses with question details"
        )

        for i, resp in enumerate(responses_with_questions, 1):
            # Get question text by querying
            q_result = await session.execute(
                select(AssessmentQuestion.question_text).where(
                    AssessmentQuestion.id == resp.question_id
                )
            )
            question_text = q_result.scalar_one()
            print(f"      {i}. Q: {question_text[:40]}...")
            if resp.answer_text:
                print(f"         A: {resp.answer_text[:40]}...")
            elif resp.answer_value:
                print(f"         A: {resp.answer_value}")
            elif resp.answer_data:
                print(f"         A: {resp.answer_data}")

        # Step 8: Test bulk insert
        print("\n8. Testing bulk insert for multiple users...")

        # Create second user
        user2 = User(
            email="test2@example.com",
            password_hash="hashed_password",
            full_name="Test User 2",
        )
        session.add(user2)
        await session.flush()

        # Bulk insert responses for user2
        bulk_responses = [
            Response(
                assessment_id=assessment.id,
                user_id=user2.id,
                question_id=q.id,
                answer_text=f"User 2 answer for question {i}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i, (_, q) in enumerate(questions, 1)
        ]

        session.add_all(bulk_responses)
        await session.commit()
        print(f"   ✓ Bulk inserted {len(bulk_responses)} responses for user2")

        # Verify both users' responses
        result = await session.execute(
            select(Response).where(Response.assessment_id == assessment.id)
        )
        all_responses = result.scalars().all()
        print(f"   ✓ Total responses for assessment: {len(all_responses)}")

        await session.close()

    await engine.dispose()

    print("\n" + "=" * 60)
    print("✓ All tests passed! Schema is working correctly.")
    print("=" * 60)


async def check_schema_health():
    """Check if required tables and columns exist."""
    engine = create_async_engine(settings.database_url)

    async with AsyncSession(engine) as session:
        print("\nChecking Schema Health")
        print("=" * 60)

        # Check if assessment_questions table exists
        try:
            await session.execute(select(AssessmentQuestion).limit(1))
            print("✓ assessment_questions table exists")
        except Exception as e:
            print(f"✗ assessment_questions table error: {e}")
            return False

        # Check if responses table exists
        try:
            await session.execute(select(Response).limit(1))
            print("✓ responses table exists")
        except Exception as e:
            print(f"✗ responses table error: {e}")
            return False

        # Check required columns in responses
        try:
            await session.execute(
                select(
                    Response.answer_text, Response.answer_value, Response.answer_data
                ).limit(1)
            )
            print("✓ responses table has all answer columns")
        except Exception as e:
            print(f"✗ responses columns error: {e}")
            return False

        await session.close()

    await engine.dispose()
    print("=" * 60)
    return True


async def main():
    """Run all tests."""
    try:
        # First check schema health
        schema_ok = await check_schema_health()
        if not schema_ok:
            print("\nERROR: Schema health check failed. Please run migrations first:")
            print("  alembic upgrade head")
            sys.exit(1)

        # Run full test
        await create_test_assessment_flow()

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
