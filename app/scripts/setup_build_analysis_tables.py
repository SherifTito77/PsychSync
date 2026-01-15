#!/usr/bin/env python3
"""
Setup script for Build Failure Analysis tables
Creates database tables for tracking build failures, patterns, and reports
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


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
    """Create all build analysis tables"""
    from app.core.database import async_session_maker

    print("🔨 Creating Build Failure Analysis tables...")

    async with async_session_maker() as session:
        # Create build_failures table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS build_failures (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                build_id VARCHAR(255) NOT NULL,
                project_name VARCHAR(255) NOT NULL,
                branch_name VARCHAR(255) NOT NULL,
                commit_hash VARCHAR(255) NOT NULL,
                failure_type VARCHAR(100) NOT NULL,
                failure_stage VARCHAR(100) NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                failed_tests TEXT[],
                changed_files TEXT[],
                developer_name VARCHAR(255) NOT NULL,
                root_cause_category VARCHAR(100) NOT NULL,
                suspected_culprit_file VARCHAR(500),
                ai_suggested_fix TEXT,
                priority VARCHAR(50) NOT NULL DEFAULT 'medium',
                is_resolved FLOAT NOT NULL DEFAULT 0.0,
                resolution_notes TEXT,
                actual_root_cause VARCHAR(255),
                fix_commit_hash VARCHAR(255),
                resolution_time_minutes INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP WITH TIME ZONE
            );
        """))

        # Create indexes for build_failures
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_build_id ON build_failures(build_id);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_branch ON build_failures(branch_name);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_type ON build_failures(failure_type);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_priority ON build_failures(priority);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_resolved ON build_failures(is_resolved);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_developer ON build_failures(developer_name);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_failures_created_at ON build_failures(created_at DESC);
        """))

        print("  ✅ build_failures table created")

        # Create root_cause_analyses table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS root_cause_analyses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                failure_id UUID NOT NULL REFERENCES build_failures(id) ON DELETE CASCADE,
                analysis_depth VARCHAR(50) NOT NULL,
                contributing_factors TEXT[] NOT NULL,
                affected_components TEXT[],
                similar_failures UUID[],
                confidence_score FLOAT NOT NULL,
                analysis_result TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_root_cause_failure_id ON root_cause_analyses(failure_id);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_root_cause_created_at ON root_cause_analyses(created_at DESC);
        """))

        print("  ✅ root_cause_analyses table created")

        # Create build_patterns table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS build_patterns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pattern_type VARCHAR(100) NOT NULL,
                pattern_name VARCHAR(255) NOT NULL,
                occurrence_count INTEGER NOT NULL,
                affected_branches TEXT[] NOT NULL,
                affected_developers TEXT[],
                remediation_priority VARCHAR(50) NOT NULL DEFAULT 'medium',
                ai_remediation_suggestion TEXT,
                last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_resolved FLOAT NOT NULL DEFAULT 0.0
            );
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_patterns_type ON build_patterns(pattern_type);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_patterns_resolved ON build_patterns(is_resolved);
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_patterns_occurrence ON build_patterns(occurrence_count DESC);
        """))

        print("  ✅ build_patterns table created")

        # Create build_analysis_reports table
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS build_analysis_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_date TIMESTAMP WITH TIME ZONE NOT NULL,
                period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                total_builds INTEGER NOT NULL,
                successful_builds INTEGER NOT NULL,
                failed_builds INTEGER NOT NULL,
                flaky_builds INTEGER NOT NULL,
                average_build_time_minutes FLOAT NOT NULL,
                average_recovery_time_minutes FLOAT NOT NULL,
                success_rate FLOAT NOT NULL,
                top_failure_types JSONB,
                top_failing_branches JSONB,
                top_failing_developers JSONB,
                ai_summary TEXT,
                ai_insights JSONB,
                recommendations TEXT[]
            );
        """))

        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_build_reports_date ON build_analysis_reports(report_date DESC);
        """))

        print("  ✅ build_analysis_reports table created")

        await session.commit()

    print("\n✅ All Build Failure Analysis tables created successfully!")
    print("\n📊 Tables created:")
    print("   - build_failures")
    print("   - root_cause_analyses")
    print("   - build_patterns")
    print("   - build_analysis_reports")


if __name__ == "__main__":
    asyncio.run(create_tables())
