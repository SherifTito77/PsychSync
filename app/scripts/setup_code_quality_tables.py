#!/usr/bin/env python3
"""
Setup Code Quality Monitoring Tables

This script creates the database tables for code quality monitoring.

Usage:
    python -m app.scripts.setup_code_quality_tables
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
from app.db.base_class import Base

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
    """Create code quality monitoring tables using raw SQL"""

    # Create async engine
    engine = create_async_engine(settings.get_database_url(async_driver=True))

    async with engine.begin() as conn:
        # Create code_quality_metrics table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS code_quality_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                scan_date TIMESTAMP NOT NULL,
                module_name VARCHAR(255),
                cyclomatic_complexity FLOAT NOT NULL,
                cognitive_complexity FLOAT NOT NULL,
                maintainability_index FLOAT NOT NULL,
                duplication_percentage FLOAT NOT NULL,
                duplicated_lines INTEGER NOT NULL,
                total_lines INTEGER NOT NULL,
                test_coverage_percentage FLOAT,
                test_count INTEGER,
                code_violations_count INTEGER NOT NULL,
                security_hotspots_count INTEGER NOT NULL,
                bugs_count INTEGER NOT NULL,
                technical_debt_ratio FLOAT NOT NULL,
                estimated_remediation_cost FLOAT,
                file_count INTEGER NOT NULL,
                code_lines INTEGER NOT NULL,
                comment_lines INTEGER NOT NULL,
                blank_lines INTEGER NOT NULL,
                language_metrics JSONB,
                complexity_trend VARCHAR(20),
                coverage_trend VARCHAR(20),
                debt_trend VARCHAR(20),
                quality_score FLOAT NOT NULL,
                quality_grade VARCHAR(2) NOT NULL,
                scan_duration_seconds FLOAT,
                scanner_version VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create code_quality_issues table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS code_quality_issues (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_id UUID NOT NULL REFERENCES code_quality_metrics(id) ON DELETE CASCADE,
                issue_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                category VARCHAR(100),
                file_path VARCHAR(500) NOT NULL,
                line_number INTEGER,
                function_name VARCHAR(255),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                rule_id VARCHAR(100),
                effort VARCHAR(20),
                remediation_cost FLOAT,
                status VARCHAR(20) NOT NULL DEFAULT 'open',
                false_positive FLOAT NOT NULL DEFAULT 0.0,
                ai_suggestion TEXT,
                ai_confidence FLOAT,
                auto_fixable FLOAT NOT NULL DEFAULT 0.0,
                first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER NOT NULL DEFAULT 1
            );
        """))

        # Create pull_request_quality table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pull_request_quality (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pr_number INTEGER NOT NULL,
                pr_title VARCHAR(500) NOT NULL,
                source_branch VARCHAR(255) NOT NULL,
                target_branch VARCHAR(255) NOT NULL,
                author_id UUID REFERENCES users(id),
                author_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL,
                merged_at TIMESTAMP,
                closed_at TIMESTAMP,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                files_changed INTEGER NOT NULL,
                lines_added INTEGER NOT NULL,
                lines_deleted INTEGER NOT NULL,
                commits_count INTEGER NOT NULL,
                overall_score FLOAT NOT NULL,
                code_quality_score FLOAT NOT NULL,
                test_coverage_score FLOAT,
                documentation_score FLOAT NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                risk_factors JSONB,
                complexity_increase FLOAT,
                new_debt_added FLOAT,
                duplication_added INTEGER,
                review_count INTEGER NOT NULL DEFAULT 0,
                review_time_hours FLOAT,
                approval_count INTEGER NOT NULL DEFAULT 0,
                request_changes_count INTEGER NOT NULL DEFAULT 0,
                tests_added INTEGER NOT NULL DEFAULT 0,
                coverage_delta FLOAT,
                critical_issues_count INTEGER NOT NULL DEFAULT 0,
                major_issues_count INTEGER NOT NULL DEFAULT 0,
                minor_issues_count INTEGER NOT NULL DEFAULT 0,
                ai_recommendations JSONB,
                merge_confidence FLOAT,
                repository VARCHAR(100),
                is_merged FLOAT NOT NULL DEFAULT 0.0
            );
        """))

        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_code_quality_scan_date_module
            ON code_quality_metrics (scan_date, module_name);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_code_quality_issue_metric_id
            ON code_quality_issues (metric_id);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_code_quality_issue_type_severity
            ON code_quality_issues (issue_type, severity);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_code_quality_status
            ON code_quality_issues (status);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pull_request_quality_score
            ON pull_request_quality (overall_score);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pull_request_risk_level
            ON pull_request_quality (risk_level);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pull_pr_number
            ON pull_request_quality (pr_number);
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_pull_request_author_id
            ON pull_request_quality (author_id);
        """))

    logger.info("✅ Code quality monitoring tables created successfully")

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
                'code_quality_metrics',
                'code_quality_issues',
                'pull_request_quality'
            )
            ORDER BY table_name;
        """))

        tables = [row[0] for row in result.fetchall()]

        logger.info(f"📊 Verified {len(tables)} code quality tables:")
        for table in tables:
            logger.info(f"   - {table}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
