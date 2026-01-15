#!/usr/bin/env python3
"""
app/scripts/setup_sql_audit_tables.py
Create SQL Audit tables in the database
"""

import asyncio
from pathlib import Path

# Add parent directory to path
import sys
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
    """Create SQL Audit tables"""
    async for db in get_async_db():
        try:
            # Create sql_queries table
            await db.execute(text("""
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
                    scanned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_scanned TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # Create indexes for sql_queries
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_queries_query_hash ON sql_queries(query_hash);
            """))
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_queries_risk_level ON sql_queries(risk_level);
            """))
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_queries_file_path ON sql_queries(file_path);
            """))
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_queries_scanned_at ON sql_queries(scanned_at);
            """))

            # Create sql_vulnerabilities table
            await db.execute(text("""
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
                    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                );
            """))

            # Create indexes for sql_vulnerabilities
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_vulnerabilities_query_id ON sql_vulnerabilities(query_id);
            """))
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_vulnerabilities_severity ON sql_vulnerabilities(severity);
            """))
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_vulnerabilities_discovered_at ON sql_vulnerabilities(discovered_at);
            """))

            # Create sql_scan_reports table
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS sql_scan_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    scan_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    total_queries_scanned INTEGER NOT NULL,
                    total_vulnerabilities INTEGER NOT NULL,
                    critical_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                    high_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                    medium_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                    low_vulnerabilities INTEGER NOT NULL DEFAULT 0,
                    safe_queries INTEGER NOT NULL DEFAULT 0,
                    parameterized_queries INTEGER NOT NULL DEFAULT 0,
                    orm_queries INTEGER NOT NULL DEFAULT 0,
                    vulnerability_breakdown JSON,
                    ai_summary TEXT,
                    ai_insights JSON,
                    overall_risk_score FLOAT NOT NULL DEFAULT 0.0,
                    risk_trend VARCHAR(20),
                    vulnerabilities_trend VARCHAR(20),
                    top_risk_files JSON,
                    top_vulnerability_types JSON
                );
            """))

            # Create indexes for sql_scan_reports
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sql_scan_reports_scan_date ON sql_scan_reports(scan_date);
            """))

            await db.commit()
            print("✓ SQL Audit tables created successfully")
            print("  - sql_queries")
            print("  - sql_vulnerabilities")
            print("  - sql_scan_reports")

        except Exception as e:
            await db.rollback()
            print(f"✗ Error creating tables: {e}")
            raise
        finally:
            await db.close()
        break


if __name__ == "__main__":
    print("Creating SQL Audit tables...")
    asyncio.run(create_tables())
    print("\nDone!")
