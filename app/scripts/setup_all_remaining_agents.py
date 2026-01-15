#!/usr/bin/env python3
"""
Combined setup script for all remaining AI agent tables:
- Build Failure Analysis
- Caching Configuration
- Breaking Changes Detection
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def create_all_tables():
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
    """Create all remaining agent tables"""
    from app.core.database import AsyncSessionLocal

    print("🚀 Creating all remaining AI agent tables...\n")

    async with AsyncSessionLocal() as session:
        # ========================================
        # BUILD FAILURE ANALYSIS TABLES
        # ========================================
        print("🔨 Build Failure Analysis...")

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

        # Create indexes
        for index in [
            "CREATE INDEX IF NOT EXISTS idx_build_failures_build_id ON build_failures(build_id);",
            "CREATE INDEX IF NOT EXISTS idx_build_failures_branch ON build_failures(branch_name);",
            "CREATE INDEX IF NOT EXISTS idx_build_failures_type ON build_failures(failure_type);",
            "CREATE INDEX IF NOT EXISTS idx_build_failures_priority ON build_failures(priority);",
            "CREATE INDEX IF NOT EXISTS idx_build_failures_resolved ON build_failures(is_resolved);",
            "CREATE INDEX IF NOT EXISTS idx_build_patterns_type ON build_patterns(pattern_type);",
            "CREATE INDEX IF NOT EXISTS idx_build_reports_date ON build_analysis_reports(report_date DESC);",
        ]:
            await session.execute(text(index))

        print("  ✅ Build Failure Analysis tables created")

        # ========================================
        # CACHING CONFIGURATION TABLES
        # ========================================
        print("💾 Caching Configuration...")

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cache_key VARCHAR(500) NOT NULL UNIQUE,
                cache_type VARCHAR(100) NOT NULL,
                endpoint_path VARCHAR(500) NOT NULL,
                data_size_bytes INTEGER NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                hit_count INTEGER NOT NULL DEFAULT 0,
                miss_count INTEGER NOT NULL DEFAULT 0,
                hit_rate FLOAT NOT NULL DEFAULT 0.0,
                miss_rate FLOAT NOT NULL DEFAULT 0.0,
                last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS cache_performance (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cache_type VARCHAR(100) NOT NULL,
                measurement_period VARCHAR(50) NOT NULL,
                total_requests INTEGER NOT NULL,
                cache_hits INTEGER NOT NULL,
                cache_misses INTEGER NOT NULL,
                hit_rate FLOAT NOT NULL,
                miss_rate FLOAT NOT NULL,
                avg_response_time_ms FLOAT NOT NULL,
                memory_usage_mb FLOAT NOT NULL,
                eviction_count INTEGER NOT NULL,
                measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS cache_optimizations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cache_key VARCHAR(500) NOT NULL,
                optimization_type VARCHAR(100) NOT NULL,
                current_hit_rate FLOAT NOT NULL,
                expected_hit_rate FLOAT NOT NULL,
                estimated_improvement_mb FLOAT NOT NULL,
                implementation_effort VARCHAR(50) NOT NULL,
                ai_recommendation TEXT,
                is_applied FLOAT NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS cache_configuration_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_date TIMESTAMP WITH TIME ZONE NOT NULL,
                period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                total_cache_entries INTEGER NOT NULL,
                active_cache_types TEXT[] NOT NULL,
                overall_hit_rate FLOAT NOT NULL,
                total_memory_usage_mb FLOAT NOT NULL,
                avg_response_time_ms FLOAT NOT NULL,
                optimization_opportunities INTEGER NOT NULL,
                potential_improvement_mb FLOAT NOT NULL,
                top_slow_cache_keys TEXT[],
                configuration_grade VARCHAR(5) NOT NULL,
                ai_summary TEXT,
                ai_insights JSONB,
                recommendations TEXT[]
            );
        """))

        # Create indexes
        for index in [
            "CREATE INDEX IF NOT EXISTS idx_cache_entries_key ON cache_entries(cache_key);",
            "CREATE INDEX IF NOT EXISTS idx_cache_entries_type ON cache_entries(cache_type);",
            "CREATE INDEX IF NOT EXISTS idx_cache_entries_hit_rate ON cache_entries(hit_rate);",
            "CREATE INDEX IF NOT EXISTS idx_cache_perf_type ON cache_performance(cache_type);",
            "CREATE INDEX IF NOT EXISTS idx_cache_opt_applied ON cache_optimizations(is_applied);",
            "CREATE INDEX IF NOT EXISTS idx_cache_config_reports_date ON cache_configuration_reports(report_date DESC);",
        ]:
            await session.execute(text(index))

        print("  ✅ Caching Configuration tables created")

        # ========================================
        # BREAKING CHANGES DETECTION TABLES
        # ========================================
        print("🚨 Breaking Changes Detection...")

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS breaking_changes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                change_type VARCHAR(100) NOT NULL,
                affected_component VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                severity VARCHAR(50) NOT NULL,
                source_branch VARCHAR(255) NOT NULL,
                commit_hash VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                line_number INTEGER NOT NULL,
                backwards_compatible FLOAT NOT NULL DEFAULT 0.0,
                migration_required FLOAT NOT NULL DEFAULT 0.0,
                affected_endpoints TEXT[],
                affected_models TEXT[],
                ai_risk_assessment TEXT,
                ai_mitigation_suggestion TEXT,
                is_approved FLOAT NOT NULL DEFAULT 0.0,
                approved_by VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS migration_guides (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                breaking_change_id UUID NOT NULL REFERENCES breaking_changes(id) ON DELETE CASCADE,
                guide_type VARCHAR(100) NOT NULL,
                steps TEXT[] NOT NULL,
                estimated_effort_hours FLOAT NOT NULL,
                required_downtime_minutes INTEGER NOT NULL DEFAULT 0,
                is_automated FLOAT NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS breaking_change_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_date TIMESTAMP WITH TIME ZONE NOT NULL,
                period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                total_changes_detected INTEGER NOT NULL,
                critical_changes INTEGER NOT NULL,
                high_priority_changes INTEGER NOT NULL,
                medium_priority_changes INTEGER NOT NULL,
                low_priority_changes INTEGER NOT NULL,
                backwards_compatible_changes INTEGER NOT NULL,
                breaking_changes INTEGER NOT NULL,
                changes_by_type JSONB,
                most_affected_components JSONB,
                risk_score FLOAT NOT NULL,
                ai_summary TEXT,
                ai_insights JSONB,
                recommendations TEXT[]
            );
        """))

        # Create indexes
        for index in [
            "CREATE INDEX IF NOT EXISTS idx_breaking_changes_type ON breaking_changes(change_type);",
            "CREATE INDEX IF NOT EXISTS idx_breaking_changes_severity ON breaking_changes(severity);",
            "CREATE INDEX IF NOT EXISTS idx_breaking_changes_approved ON breaking_changes(is_approved);",
            "CREATE INDEX IF NOT EXISTS idx_breaking_changes_component ON breaking_changes(affected_component);",
            "CREATE INDEX IF NOT EXISTS idx_migration_guides_change_id ON migration_guides(breaking_change_id);",
            "CREATE INDEX IF NOT EXISTS idx_breaking_reports_date ON breaking_change_reports(report_date DESC);",
        ]:
            await session.execute(text(index))

        print("  ✅ Breaking Changes Detection tables created")

        await session.commit()

    print("\n✅ All remaining AI agent tables created successfully!")
    print("\n📊 Tables created:")
    print("   Build Failure Analysis:")
    print("     - build_failures")
    print("     - root_cause_analyses")
    print("     - build_patterns")
    print("     - build_analysis_reports")
    print("   Caching Configuration:")
    print("     - cache_entries")
    print("     - cache_performance")
    print("     - cache_optimizations")
    print("     - cache_configuration_reports")
    print("   Breaking Changes Detection:")
    print("     - breaking_changes")
    print("     - migration_guides")
    print("     - breaking_change_reports")


if __name__ == "__main__":
    asyncio.run(create_all_tables())
