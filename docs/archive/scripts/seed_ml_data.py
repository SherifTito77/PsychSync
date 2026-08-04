#!/usr/bin/env python
"""Seed sample ML data for Predictive Analytics testing"""
from sqlalchemy import create_engine, text

from app.core.config.settings import settings


def seed_data():
    engine = create_engine(settings.get_database_url().replace("+asyncpg", ""))

    with engine.connect() as conn:
        conn.execute(text("BEGIN"))
        # Check existing data
        result = conn.execute(text("SELECT COUNT(*) FROM organizations"))
        org_count = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM teams"))
        team_count = result.scalar()
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        print(
            f"Existing data: {org_count} orgs, {team_count} teams, {user_count} users"
        )

        # Create organization
        if org_count == 0:
            result = conn.execute(
                text(
                    "INSERT INTO organizations (name, created_at, updated_at) VALUES (:name, NOW(), NOW()) RETURNING id"
                ),
                {"name": "Sample Organization"},
            )
            org_id = result.fetchone()[0]
            print(f"Created organization ID: {org_id}")
        else:
            result = conn.execute(text("SELECT id FROM organizations LIMIT 1"))
            org_id = result.fetchone()[0]

        # Create team
        if team_count == 0:
            result = conn.execute(
                text(
                    "INSERT INTO teams (name, description, organization_id, created_at, updated_at) VALUES (:name, :description, :organization_id, NOW(), NOW()) RETURNING id"
                ),
                {
                    "name": "Sample Team",
                    "description": "A sample team for ML testing",
                    "organization_id": org_id,
                },
            )
            team_id = result.fetchone()[0]
            print(f"Created team ID: {team_id}")
        else:
            result = conn.execute(text("SELECT id FROM teams LIMIT 1"))
            team_id = result.fetchone()[0]

        # Use existing user
        if user_count == 0:
            print("No users found")
            return
        else:
            result = conn.execute(text("SELECT id FROM users LIMIT 1"))
            user_id = result.fetchone()[0]
            print(f"Using user ID: {user_id}")

        # Create assessment
        result = conn.execute(
            text(
                "INSERT INTO assessments (title, category, status, created_by_id, team_id, organization_id, created_at, updated_at) VALUES (:title, :category, :status, :created_by_id, :team_id, :organization_id, NOW(), NOW()) RETURNING id"
            ),
            {
                "title": "Sample Assessment",
                "category": "PERSONALITY",
                "status": "PUBLISHED",
                "created_by_id": user_id,
                "team_id": team_id,
                "organization_id": org_id,
            },
        )
        assessment_id = result.fetchone()[0]
        print(f"Created assessment ID: {assessment_id}")

        # Create assessment section
        result = conn.execute(
            text(
                'INSERT INTO assessment_sections (assessment_id, title, "order") VALUES (:assessment_id, :title, :order) RETURNING id'
            ),
            {"assessment_id": assessment_id, "title": "Sample Section", "order": 1},
        )
        section_id = result.fetchone()[0]
        print(f"Created section ID: {section_id}")

        # Create questions
        question_ids = []
        for i in range(10):
            result = conn.execute(
                text(
                    'INSERT INTO assessment_questions (section_id, question_type, question_text, "order") VALUES (:section_id, :question_type, :question_text, :order) RETURNING id'
                ),
                {
                    "section_id": section_id,
                    "question_type": "RATING",
                    "question_text": f"Question {i+1}: How do you feel about this topic?",
                    "order": i + 1,
                },
            )
            question_ids.append(result.fetchone()[0])

        print(f"Created {len(question_ids)} questions")

        # Create responses
        import random
        import traceback

        response_count = 0
        for i, question_id in enumerate(question_ids):
            try:
                answer_value = random.randint(1, 5)  # Rating scale 1-5
                response_time = random.randint(800, 4000)
                conn.execute(
                    text(
                        "INSERT INTO responses (assessment_id, user_id, question_id, answer_value, response_time_ms, created_at, updated_at) VALUES (:assessment_id, :user_id, :question_id, :answer_value, :response_time_ms, NOW(), NOW())"
                    ),
                    {
                        "assessment_id": assessment_id,
                        "user_id": user_id,
                        "question_id": question_id,
                        "answer_value": answer_value,
                        "response_time_ms": response_time,
                    },
                )
                response_count += 1
                print(f"  Created response {i+1} for question {question_id}")
            except Exception as e:
                print(f"  ERROR creating response {i+1}: {e}")
                traceback.print_exc()

        print(f"Total responses created: {response_count}")

        conn.commit()


if __name__ == "__main__":
    seed_data()
    print("Data seeding complete!")
