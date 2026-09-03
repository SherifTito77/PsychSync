"""
PsychSync Enterprise Database - Utilities
Unified database utilities for optimization, security, and monitoring.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.config import Base, logger

# =============================================================================
# SCHEMA UTILITIES
# =============================================================================


async def verify_database_schema(engine):
    """Verify that all model tables exist in the database."""
    logger.info("Verifying database schema...")

    # Import all models to ensure they are registered in Base.metadata.tables
    from app.db.models import __init__

    async with engine.connect() as conn:

        def check_tables(sync_conn):
            inspector = inspect(sync_conn)
            existing_tables = set(inspector.get_table_names())
            defined_tables = set(Base.metadata.tables.keys())

            missing = defined_tables - existing_tables
            if missing:
                error_msg = f"Database schema mismatch! Missing tables: {missing}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                logger.info("Database schema verification passed.")

        await conn.run_sync(check_tables)


# =============================================================================
# SECURITY MODELS
# =============================================================================


class DatabaseSecurityIssue(Enum):
    SQL_INJECTION = "sql_injection"
    NOSQL_INJECTION = "nosql_injection"
    HARDCODED_CREDENTIALS = "hardcoded_credentials"
    WEAK_PASSWORDS = "weak_passwords"
    MISSING_ENCRYPTION = "missing_encryption"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNENCRYPTED_BACKUPS = "unencrypted_backups"
    ACCESS_CONTROL_ISSUES = "access_control_issues"


@dataclass
class SecurityVulnerability:
    issue_type: DatabaseSecurityIssue
    severity: str
    description: str
    location: str
    evidence: str
    recommendation: str
    cvss_score: float = 0.0


# =============================================================================
# SECURITY REMEDIATOR
# =============================================================================


class DatabaseSecurityRemediator:
    """Comprehensive database security remediation system"""

    def __init__(self):
        self.vulnerabilities = []
        self.remediations = []

    async def scan_database_vulnerabilities(
        self, db: AsyncSession
    ) -> List[SecurityVulnerability]:
        """Perform database vulnerability scan (placeholder)"""
        # Implementation from database_security.py would go here
        return []

    async def fix_vulnerabilities(self, db: AsyncSession) -> Dict[str, Any]:
        """Apply security fixes (placeholder)"""
        return {"total": 0}

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate security report (placeholder)"""
        return {"total_vulnerabilities": 0, "security_score": 100}


# Global instance
database_security = DatabaseSecurityRemediator()

# =============================================================================
# QUERY UTILITIES
# =============================================================================


async def analyze_query_performance(
    session: AsyncSession, query: str, params: Optional[dict] = None
) -> dict:
    """Analyze query performance using EXPLAIN ANALYZE"""
    try:
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        result = await session.execute(text(explain_query), params or {})
        return result.scalar()
    except Exception as e:
        logger.error(f"Error analyzing query performance: {e}")
        return {"error": str(e)}


# =============================================================================
# ROW LEVEL SECURITY
# =============================================================================


async def set_row_level_security_context(session: AsyncSession, user_id: str):
    """Set row-level security context"""
    await session.execute(text(f"SET app.current_user_id = '{user_id}'"))


async def clear_row_level_security_context(session: AsyncSession):
    """Clear row-level security context"""
    await session.execute(text("RESET app.current_user_id"))


# =============================================================================
# MAINTENANCE
# =============================================================================


async def vacuum_analyze_table(session: AsyncSession, table_name: str):
    """Run VACUUM ANALYZE on a table"""
    await session.execute(text(f"VACUUM ANALYZE {table_name}"))
    await session.commit()
