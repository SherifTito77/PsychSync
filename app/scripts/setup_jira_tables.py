#!/usr/bin/env python3
"""
Setup Jira Integration Tables

This script creates the database tables for Jira integration.

Usage:
    python -m app.scripts.setup_jira_tables
"""

import asyncio
import logging
from pathlib import Path

import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create a new resource.

Args:
    db: Database session
    **kwargs: Resource attributes

Returns:
    Created resource object

Raises:
    ValidationError: If input data is invalid
    """
    """Create a new resource.

Args:
    db: Database session
    **kwargs: Resource attributes

Returns:
    Created resource object

Raises:
    ValidationError: If input data is invalid
    """
    """Create Jira integration tables using raw SQL"""

    # Create async engine
    engine = create_async_engine(settings.get_database_url(async_driver=True))

    async with engine.begin() as conn:
        # Create jira_issues table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jira_issues (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                issue_key VARCHAR(50) UNIQUE NOT NULL,
                issue_type VARCHAR(50) NOT NULL,
                summary VARCHAR(500) NOT NULL,
                description TEXT,
                status VARCHAR(50) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                is_bug FLOAT NOT NULL DEFAULT 0.0,
                severity VARCHAR(20),
                category VARCHAR(100),
                reporter_id VARCHAR(100),
                assignee_id VARCHAR(100),
                assignee_name VARCHAR(255),
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                resolved_at TIMESTAMP,
                due_date TIMESTAMP,
                time_estimate INTEGER,
                time_spent INTEGER,
                time_remaining INTEGER,
                sprint_id VARCHAR(100),
                sprint_name VARCHAR(255),
                project_key VARCHAR(50) NOT NULL,
                project_name VARCHAR(255) NOT NULL,
                labels JSONB,
                components JSONB,
                attachment_count INTEGER NOT NULL DEFAULT 0,
                comment_count INTEGER NOT NULL DEFAULT 0,
                last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create jira_bug_summaries table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jira_bug_summaries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                summary_date TIMESTAMP NOT NULL,
                project_key VARCHAR(50) NOT NULL,
                sprint_id VARCHAR(100),
                total_bugs INTEGER NOT NULL DEFAULT 0,
                new_bugs INTEGER NOT NULL DEFAULT 0,
                resolved_bugs INTEGER NOT NULL DEFAULT 0,
                reopened_bugs INTEGER NOT NULL DEFAULT 0,
                critical_bugs INTEGER NOT NULL DEFAULT 0,
                major_bugs INTEGER NOT NULL DEFAULT 0,
                minor_bugs INTEGER NOT NULL DEFAULT 0,
                avg_bug_age_hours FLOAT,
                oldest_bug_age_hours FLOAT,
                bugs_over_sla INTEGER NOT NULL DEFAULT 0,
                bugs_by_category JSONB,
                top_bugs JSONB,
                ai_summary TEXT,
                ai_insights JSONB,
                ai_recommendations JSONB,
                trend_new_bugs VARCHAR(20),
                trend_resolution_rate VARCHAR(20),
                assignee_workload JSONB,
                resolution_time_avg_hours FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generated_by VARCHAR(100),
                issue_ids JSONB
            );
        """))

        # Create jira_sprint_metrics table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jira_sprint_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                sprint_id VARCHAR(100) UNIQUE NOT NULL,
                sprint_name VARCHAR(255) NOT NULL,
                project_key VARCHAR(50) NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                state VARCHAR(50) NOT NULL,
                committed_points INTEGER,
                completed_points INTEGER,
                completion_rate FLOAT,
                total_issues INTEGER NOT NULL DEFAULT 0,
                completed_issues INTEGER NOT NULL DEFAULT 0,
                in_progress_issues INTEGER NOT NULL DEFAULT 0,
                todo_issues INTEGER NOT NULL DEFAULT 0,
                bugs_found INTEGER NOT NULL DEFAULT 0,
                bugs_fixed INTEGER NOT NULL DEFAULT 0,
                bugs_carried_over INTEGER NOT NULL DEFAULT 0,
                team_velocity INTEGER,
                velocity_change FLOAT,
                ai_retrospective TEXT,
                ai_improvements JSONB,
                sprint_goal TEXT,
                goal_achieved FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_key ON jira_issues (issue_key);",
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_type ON jira_issues (issue_type);",
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_status ON jira_issues (status);",
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_is_bug ON jira_issues (is_bug);",
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_sprint ON jira_issues (sprint_id);",
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_project ON jira_issues (project_key);",
            "CREATE INDEX IF NOT EXISTS ix_jira_issues_created ON jira_issues (created_at);",

            "CREATE INDEX IF NOT EXISTS ix_jira_summary_date ON jira_bug_summaries (summary_date);",
            "CREATE INDEX IF NOT EXISTS ix_jira_summary_project ON jira_bug_summaries (project_key);",
            "CREATE INDEX IF NOT EXISTS ix_jira_summary_sprint ON jira_bug_summaries (sprint_id);",
            "CREATE INDEX IF NOT EXISTS ix_jira_summary_date_project ON jira_bug_summaries (summary_date, project_key);",

            "CREATE INDEX IF NOT EXISTS ix_jira_sprint_id ON jira_sprint_metrics (sprint_id);",
            "CREATE INDEX IF NOT EXISTS ix_jira_sprint_project ON jira_sprint_metrics (project_key);",
            "CREATE INDEX IF NOT EXISTS ix_jira_sprint_start ON jira_sprint_metrics (start_date);",
            "CREATE INDEX IF NOT EXISTS ix_jira_sprint_dates ON jira_sprint_metrics (start_date, end_date);",
        ]

        for index_stmt in indexes:
            await conn.execute(text(index_stmt))

    logger.info("✅ Jira integration tables created successfully")

    # Verify tables were created
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        result = await session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN (
                'jira_issues',
                'jira_bug_summaries',
                'jira_sprint_metrics'
            )
            ORDER BY table_name;
        """))

        tables = [row[0] for row in result.fetchall()]

        logger.info(f"📊 Verified {len(tables)} Jira integration tables:")
        for table in tables:
            logger.info(f"   - {table}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
