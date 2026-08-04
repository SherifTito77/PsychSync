import asyncio
import os
import random
import sys
import uuid

# Add project root to path
sys.path.append(os.getcwd())

from datetime import datetime

from sqlalchemy import text

from app.db.session import AsyncSessionLocal


async def main():
    assessment_id = str(uuid.uuid4())
    # Try to find Sherif Tito's ID or any user

    async with AsyncSessionLocal() as db:
        # Get a valid user ID for created_by
        user_res = await db.execute(text("SELECT id FROM users LIMIT 1"))
        user_row = user_res.first()
        if not user_row:
            print("No users found in database. Please add a user first.")
            return
        created_by_id = str(user_row[0])

        # 1. Create Assessment
        print(f"Creating assessment: {assessment_id}")
        await db.execute(
            text(
                """
            INSERT INTO assessments (id, title, category, status, created_by_id, description, created_at, updated_at)
            VALUES (:id, :title, 'PERSONALITY', 'PUBLISHED', :created_by_id, :desc, NOW(), NOW())
        """
            ),
            {
                "id": assessment_id,
                "title": "High-Consistency Psychometric Test",
                "created_by_id": created_by_id,
                "desc": "A test with high internal consistency for demonstration.",
            },
        )

        # 2. Create Section
        section_id = str(uuid.uuid4())
        await db.execute(
            text(
                """
            INSERT INTO assessment_sections (id, assessment_id, title, "order")
            VALUES (:id, :assessment_id, 'Primary Questions', 1)
        """
            ),
            {"id": section_id, "assessment_id": assessment_id},
        )

        # 3. Create 10 Questions
        question_ids = []
        for i in range(1, 11):
            q_id = str(uuid.uuid4())
            question_ids.append(q_id)
            await db.execute(
                text(
                    """
                INSERT INTO assessment_questions (id, section_id, question_type, question_text, "order", is_required)
                VALUES (:id, :section_id, 'scale', :text, :order, true)
            """
                ),
                {
                    "id": q_id,
                    "section_id": section_id,
                    "text": f"Question {i}: How consistent are you?",
                    "order": i,
                },
            )

        # 4. Get 10 Users
        res = await db.execute(text("SELECT id FROM users LIMIT 10"))
        user_ids = [str(r[0]) for r in res.all()]

        # 5. Generate Responses
        print(f"Generating responses for {len(user_ids)} users...")
        for i, u_id in enumerate(user_ids):
            # Assign each user a consistent base level (1 to 5)
            base_score = (i % 5) + 1
            for q_id in question_ids:
                # Add tiny noise (0.2 SD) to base score and clamp 1-5
                val = round(random.gauss(base_score, 0.2))
                val = max(1, min(5, int(val)))

                await db.execute(
                    text(
                        """
                    INSERT INTO responses (id, assessment_id, user_id, question_id, answer_value, response_time_ms, created_at, updated_at)
                    VALUES (:id, :assessment_id, :user_id, :question_id, :val, :time_ms, NOW(), NOW())
                """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "assessment_id": assessment_id,
                        "user_id": u_id,
                        "question_id": q_id,
                        "val": val,
                        "time_ms": random.randint(1000, 5000),  # 1-5 seconds
                    },
                )

        await db.commit()
        print(f"Success! Assessment ID: {assessment_id}")
        print(f"Title: High-Consistency Psychometric Test")
        print(f"Total Users: {len(user_ids)}")
        print(f"Total Questions: {len(question_ids)}")
        print(f"Total Responses: {len(user_ids) * len(question_ids)}")


if __name__ == "__main__":
    asyncio.run(main())
