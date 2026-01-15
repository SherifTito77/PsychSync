#!/usr/bin/env python3
"""Create Query Performance tables"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import get_async_db


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
    async for db in get_async_db():
        try:
            await db.execute(text("""
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
                    first_detected TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_detected TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))

            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS index_recommendations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    query_id UUID NOT NULL REFERENCES slow_queries(id) ON DELETE CASCADE,
                    table_name VARCHAR(100) NOT NULL,
                    index_name VARCHAR(100) NOT NULL,
                    columns JSON NOT NULL,
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
                );
            """))

            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS query_performance_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    query_id UUID NOT NULL REFERENCES slow_queries(id) ON DELETE CASCADE,
                    execution_time_ms FLOAT NOT NULL,
                    rows_examined INTEGER,
                    rows_returned INTEGER,
                    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    context JSON
                );
            """))

            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS query_optimization_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
                    ai_insights JSON,
                    top_slow_queries JSON,
                    performance_trend VARCHAR(20),
                    optimization_progress FLOAT
                );
            """))

            # Indexes
            await db.execute(text('CREATE INDEX IF NOT EXISTS idx_slow_queries_hash ON slow_queries(query_hash);'))
            await db.execute(text('CREATE INDEX IF NOT EXISTS idx_slow_queries_tier ON slow_queries(performance_tier);'))
            await db.execute(text('CREATE INDEX IF NOT EXISTS idx_slow_queries_optimized ON slow_queries(is_optimized);'))
            await db.execute(text('CREATE INDEX IF NOT EXISTS idx_index_recommendations_query ON index_recommendations(query_id);'))
            await db.execute(text('CREATE INDEX IF NOT EXISTS idx_index_recommendations_table ON index_recommendations(table_name);'))
            await db.execute(text('CREATE INDEX IF NOT EXISTS idx_optimization_reports_date ON query_optimization_reports(report_date);'))

            await db.commit()
            print("✓ Query Performance tables created successfully")
            print("  - slow_queries")
            print("  - index_recommendations")
            print("  - query_performance_history")
            print("  - query_optimization_reports")

        except Exception as e:
            await db.rollback()
            print(f"✗ Error: {e}")
            raise
        finally:
            await db.close()
        break


if __name__ == "__main__":
    print("Creating Query Performance tables...")
    asyncio.run(create_tables())
    print("\nDone!")
