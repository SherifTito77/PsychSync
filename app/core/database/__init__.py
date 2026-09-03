from .config import AsyncSessionLocal, Base, async_engine, get_async_db
from .monitoring import setup_database_monitoring
from .utils import (
    DatabaseSecurityIssue,
    DatabaseSecurityRemediator,
    SecurityVulnerability,
    analyze_query_performance,
    clear_row_level_security_context,
    database_security,
    set_row_level_security_context,
    vacuum_analyze_table,
)

# Aliases for backwards compatibility
SessionLocal = AsyncSessionLocal
get_db = get_async_db
get_sync_db = get_async_db

__all__ = [
    "Base",
    "async_engine",
    "AsyncSessionLocal",
    "SessionLocal",
    "get_db",
    "get_async_db",
    "get_sync_db",
    "DatabaseSecurityIssue",
    "DatabaseSecurityRemediator",
    "SecurityVulnerability",
    "database_security",
    "analyze_query_performance",
    "set_row_level_security_context",
    "clear_row_level_security_context",
    "vacuum_analyze_table",
    "setup_database_monitoring",
]
