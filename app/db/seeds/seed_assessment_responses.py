"""
Create assessment response data directly in database for ML training
Simplest version - bypasses complex schema issues.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def create_ml_training_data():
    """Create minimal assessment data for ML training"""
    db = AsyncSessionLocal()
    try:
        print("=" * 60)
        print("Creating ML training data...")
        print("=" * 60)

        # Get assessment
        result = await db.execute(
            text(
                "SELECT id, created_by_id FROM assessments WHERE title = 'ML Training Assessment' LIMIT 1"
            )
        )
        assessment = result.fetchone()

        if not assessment:
            print("❌ Assessment 'ML Training Assessment' not found!")
            return

        assessment_id, user_id = assessment
        print(f"✅ Using existing assessment: {assessment_id}, user: {user_id}")

        # Get users to create responses for
        users_result = await db.execute(
            text("SELECT id FROM users WHERE email LIKE 'test_user_%' LIMIT 10")
        )
        user_ids = [row[0] for row in users_result]

        if not user_ids:
            print("❌ No test users found!")
            return

        # Create responses directly (bypass assessment_sections schema)
        print("Creating responses...")
        responses_created = 0

        for i, uid in enumerate(user_ids):
            # Varied responses (1-5 scale)
            answer_value = (i % 5) + 1
            score = float(answer_value * 20)
            confidence = 70 + (i * 3)

            await db.execute(
                text(
                    """
                INSERT INTO responses (id, user_id, assessment_id, question_id, answer_value, score, confidence_rating, created_at, updated_at)
                VALUES (:id, :uid, :aid, NULL, :value, :score, :conf, NOW(), NOW())
                """
                ),
                {
                    "id": uuid4(),
                    "uid": uid,
                    "aid": assessment_id,
                    "value": answer_value,
                    "score": score,
                    "conf": confidence,
                },
            )
            responses_created += 1

        await db.commit()

        print("\n" + "=" * 60)
        print("ML Training Data Summary:")
        print("=" * 60)
        print(f"  Assessment ID: {assessment_id}")
        print(f"  Users with responses: {len(user_ids)}")
        print(f"  Total responses: {responses_created}")
        print("\n✅ ML training data created successfully!")
        print("   You can now test predictive analytics at:")
        print("   http://localhost:5173/predictive-analytics")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        await db.rollback()
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(create_ml_training_data())
