#!/usr/bin/env python3
"""Create sql_audit and query_performance tables directly"""

import asyncio
from uuid import uuid4

from sqlalchemy import text

from app.db.database import engine


async def create_tables():
    """Create the required tables"""
    async with engine.begin() as conn:
        # Create SQL Audit Tables
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sql_queries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_hash VARCHAR(64) UNIQUE NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                line_number INTEGER NOT NULL,
                query_text TEXT NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                risk_score FLOAT NOT NULL DEFAULT 0.0,
                vulnerability_type VARCHAR(100),
                is_parameterized FLOAT NOT NULL DEFAULT 0.0,
                uses_orm FLOAT NOT NULL DEFAULT 0.0,
                has_user_input FLOAT NOT NULL DEFAULT 0.0,
                complexity_score FLOAT,
                ai_suggestion TEXT,
                safe_example TEXT,
                reference_url VARCHAR(500),
                is_fixed FLOAT NOT NULL DEFAULT 0.0,
                fix_priority VARCHAR(20),
                scanned_at TIMESTAMP NOT NULL DEFAULT NOW(),
                last_scanned TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS ix_sql_queries_query_hash ON sql_queries(query_hash)
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sql_vulnerabilities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_id UUID NOT NULL REFERENCES sql_queries(id) ON DELETE CASCADE,
                vulnerability_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                injection_point VARCHAR(200),
                exploit_example TEXT,
                impact_description TEXT,
                remediation_steps TEXT,
                code_fix TEXT,
                verified_safe FLOAT NOT NULL DEFAULT 0.0,
                discovered_at TIMESTAMP NOT NULL DEFAULT NOW(),
                resolved_at TIMESTAMP
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sql_scan_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                scan_date TIMESTAMP NOT NULL DEFAULT NOW(),
                total_queries_scanned INTEGER NOT NULL,
                total_vulnerabilities INTEGER NOT NULL,
                critical_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                high_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                medium_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                low_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                safe_queries INTEGER NOT NULL DEFAULT 0,
                parameterized_queries INTEGER NOT NULL DEFAULT 0,
                orm_queries INTEGER NOT NULL DEFAULT 0,
                vulnerability_breakdown JSONB,
                ai_summary TEXT,
                ai_insights JSONB,
                overall_risk_score FLOAT NOT NULL DEFAULT 0.0,
                risk_trend VARCHAR(20),
                vulnerabilities_trend VARCHAR(20),
                top_risk_files JSONB,
                top_vulnerability_types JSONB
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS ix_sql_scan_reports_scan_date ON sql_scan_reports(scan_date)
        """
            )
        )

        # Create Query Performance Tables
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS slow_queries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_hash VARCHAR(64) UNIQUE NOT NULL,
                query_text TEXT NOT NULL,
                query_signature VARCHAR(200) NOT NULL,
                file_path VARCHAR(500),
                line_number INTEGER,
                execution_count INTEGER NOT NULL DEFAULT 1,
                total_time_ms FLOAT NOT NULL,
                avg_time_ms FLOAT NOT NULL,
                max_time_ms FLOAT NOT NULL,
                min_time_ms FLOAT NOT NULL,
                performance_tier VARCHAR(20) NOT NULL,
                impact_score FLOAT NOT NULL DEFAULT 0.0,
                rows_examined INTEGER,
                rows_returned INTEGER,
                selectivity FLOAT,
                bottleneck_type VARCHAR(100),
                optimization_potential VARCHAR(20),
                ai_suggestion TEXT,
                suggested_index TEXT,
                rewritten_query TEXT,
                estimated_improvement FLOAT,
                is_optimized FLOAT NOT NULL DEFAULT 0.0,
                optimization_applied_at TIMESTAMP,
                first_detected TIMESTAMP NOT NULL DEFAULT NOW(),
                last_detected TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS ix_slow_queries_query_hash ON slow_queries(query_hash)
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS index_recommendations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_id UUID NOT NULL REFERENCES slow_queries(id) ON DELETE CASCADE,
                table_name VARCHAR(100) NOT NULL,
                index_name VARCHAR(100) NOT NULL,
                columns JSONB NOT NULL,
                index_type VARCHAR(50) NOT NULL,
                estimated_benefit VARCHAR(20) NOT NULL,
                estimated_speedup FLOAT,
                affected_queries INTEGER NOT NULL DEFAULT 1,
                create_statement TEXT NOT NULL,
                size_estimate_mb FLOAT,
                write_overhead VARCHAR(20),
                storage_overhead_mb FLOAT,
                is_created FLOAT NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP,
                created_by VARCHAR(100),
                priority VARCHAR(20) NOT NULL
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS query_performance_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_id UUID NOT NULL REFERENCES slow_queries(id) ON DELETE CASCADE,
                execution_time_ms FLOAT NOT NULL,
                rows_examined INTEGER,
                rows_returned INTEGER,
                recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
                context JSONB
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS query_optimization_reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_date TIMESTAMP NOT NULL DEFAULT NOW(),
                total_queries_analyzed INTEGER NOT NULL,
                slow_queries_count INTEGER NOT NULL,
                critical_queries_count INTEGER NOT NULL DEFAULT 0,
                avg_query_time_ms FLOAT NOT NULL,
                p95_query_time_ms FLOAT NOT NULL,
                p99_query_time_ms FLOAT NOT NULL,
                total_optimization_potential_ms FLOAT NOT NULL,
                estimated_speedup_percentage FLOAT NOT NULL,
                missing_indexes_count INTEGER NOT NULL DEFAULT 0,
                n_plus_1_count INTEGER NOT NULL DEFAULT 0,
                full_table_scans INTEGER NOT NULL DEFAULT 0,
                inefficient_joins INTEGER NOT NULL DEFAULT 0,
                ai_summary TEXT,
                ai_insights JSONB,
                top_slow_queries JSONB,
                performance_trend VARCHAR(20),
                optimization_progress FLOAT
            )
        """
            )
        )

        await conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS ix_query_optimization_reports_report_date
            ON query_optimization_reports(report_date)
        """
            )
        )

        print("✅ All tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
