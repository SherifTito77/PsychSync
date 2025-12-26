#!/usr/bin/env python3
"""
Quick database initialization for production optimization testing
Creates basic tables needed for the tools to function properly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from app.core.database import async_engine

async def initialize_database():
    """Initialize basic database schema"""

    # Basic schema statements
    schema_statements = [
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100),
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            hashed_password VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS teams (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            organization_id UUID REFERENCES organizations(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS team_members (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            team_id UUID REFERENCES teams(id),
            user_id UUID REFERENCES users(id),
            role VARCHAR(50) DEFAULT 'member',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            assessment_type VARCHAR(100),
            organization_id UUID REFERENCES organizations(id),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_responses (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id),
            assessment_id UUID REFERENCES assessments(id),
            response_data JSONB,
            total_score DECIMAL(5,2),
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_teams_org ON teams(organization_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_assessments_org ON assessments(organization_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_assessment_responses_user ON assessment_responses(user_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_assessment_responses_assessment ON assessment_responses(assessment_id)
        """
    ]

    async with async_engine.begin() as conn:
        try:
            # Execute each schema statement separately
            for i, statement in enumerate(schema_statements):
                await conn.execute(text(statement))
                print(f"✅ Schema statement {i+1}/{len(schema_statements)} executed")

            print("✅ Database schema initialized successfully")

            # Insert some test data
            test_data_statements = [
                """
                INSERT INTO organizations (id, name, description) VALUES
                ('550e8400-e29b-41d4-a716-446655440001', 'Test Organization', 'Test organization for optimization'),
                ('550e8400-e29b-41d4-a716-446655440002', 'Demo Organization', 'Demo organization')
                ON CONFLICT (id) DO NOTHING
                """,
                """
                INSERT INTO users (id, email, username, full_name, is_active) VALUES
                ('550e8400-e29b-41d4-a716-446655440003', 'admin@example.com', 'admin', 'Admin User', true),
                ('550e8400-e29b-41d4-a716-446655440004', 'test@example.com', 'test', 'Test User', true)
                ON CONFLICT (email) DO NOTHING
                """,
                """
                INSERT INTO teams (id, name, organization_id) VALUES
                ('550e8400-e29b-41d4-a716-446655440005', 'Test Team', '550e8400-e29b-41d4-a716-446655440001'),
                ('550e8400-e29b-41d4-a716-446655440006', 'Demo Team', '550e8400-e29b-41d4-a716-446655440002')
                ON CONFLICT (id) DO NOTHING
                """,
                """
                INSERT INTO team_members (team_id, user_id, role) VALUES
                ('550e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440003', 'admin'),
                ('550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440004', 'member')
                ON CONFLICT DO NOTHING
                """,
                """
                INSERT INTO assessments (id, title, description, assessment_type, organization_id) VALUES
                ('550e8400-e29b-41d4-a716-446655440007', 'Test Assessment', 'Test assessment for optimization', 'BIG_FIVE', '550e8400-e29b-41d4-a716-446655440001'),
                ('550e8400-e29b-41d4-a716-446655440008', 'Demo Assessment', 'Demo assessment', 'MBTI', '550e8400-e29b-41d4-a716-446655440002')
                ON CONFLICT (id) DO NOTHING
                """
            ]

            # Execute each test data statement separately
            for i, statement in enumerate(test_data_statements):
                await conn.execute(text(statement))
                print(f"✅ Test data statement {i+1}/{len(test_data_statements)} executed")

            print("✅ Test data inserted successfully")

            return True

        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(initialize_database())
    if result:
        print("🎉 Database initialization complete!")
    else:
        print("💥 Database initialization failed!")
        sys.exit(1)