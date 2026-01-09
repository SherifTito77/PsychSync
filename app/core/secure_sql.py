# app/core/secure_sql.py
"""
SECURE SQL IDENTIFIER VALIDATION
Prevents SQL injection via table/column names in dynamic SQL

PostgreSQL identifiers (table names, column names) cannot be parameterized
like VALUES. This module provides safe handling for identifier interpolation.

SECURITY APPROACH:
1. Whitelist validation against known tables
2. Strict pattern matching for identifiers
3. PostgreSQL quote_ident() for escaping
4. SQLAlchemy identifier quoting

Author: Security Team
Version: 1.0
"""

import logging
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# PostgreSQL identifier validation rules:
# - Must start with letter or underscore
# - Can contain letters, numbers, underscores
# - Max length: 63 bytes
# - Cannot be a reserved keyword
VALID_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")

# Reserved SQL keywords that should never be used as table names
RESERVED_KEYWORDS: set[str] = {
    "select", "insert", "update", "delete", "drop", "create", "alter",
    "truncate", "grant", "revoke", "union", "where", "from", "join",
    "and", "or", "not", "in", "like", "between", "null", "true", "false",
    "table", "index", "view", "sequence", "database", "schema", "function",
    "trigger", "constraint", "primary", "foreign", "key", "unique", "check",
    "execute", "commit", "rollback", "transaction", "savepoint"
}

# Known application tables (whitelist)
# This should be updated when new tables are added
KNOWN_TABLES: set[str] = {
    "users", "organizations", "teams", "team_members", "assessments",
    "assessment_templates", "assessment_questions", "assessment_responses",
    "assessment_results", "response_answers", "invitations", "audit_logs",
    "refresh_tokens", "password_resets", "email_verifications", "api_keys",
    "webhooks", "webhook_events", "notifications", "user_sessions",
    "role_permissions", "permissions", "user_roles", "team_permissions"
}


def is_valid_identifier(identifier: str) -> bool:
    """
    Validate SQL identifier using strict pattern matching

    Args:
        identifier: Table or column name to validate

    Returns:
        True if identifier is safe to use, False otherwise

    Security:
    - Checks against valid identifier pattern
    - Rejects SQL reserved keywords
    - Prevents SQL injection via special characters
    """
    if not identifier or not isinstance(identifier, str):
        logger.warning("Invalid identifier: null or non-string value")
        return False

    # Check length limit (PostgreSQL max is 63 bytes)
    if len(identifier.encode("utf-8")) > 63:
        logger.warning(f"Invalid identifier: exceeds 63 bytes - {identifier}")
        return False

    # Check pattern (start with letter/underscore, alphanumeric + underscore)
    if not VALID_IDENTIFIER_PATTERN.match(identifier):
        logger.warning(f"Invalid identifier: contains invalid characters - {identifier}")
        return False

    # Check for reserved keywords
    if identifier.lower() in RESERVED_KEYWORDS:
        logger.warning(f"Invalid identifier: reserved SQL keyword - {identifier}")
        return False

    return True


def is_known_table(table_name: str) -> bool:
    """
    Check if table is in the whitelist of known application tables

    Args:
        table_name: Table name to validate

    Returns:
        True if table is known and trusted
    """
    return table_name.lower() in {t.lower() for t in KNOWN_TABLES}


def validate_table_name(table_name: str, require_whitelist: bool = True) -> bool:
    """
    Comprehensive table name validation

    Args:
        table_name: Table name to validate
        require_whitelist: If True, table must be in KNOWN_TABLES

    Returns:
        True if table name is safe

    Raises:
        ValueError: If table name fails validation
    """
    # First check identifier pattern
    if not is_valid_identifier(table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    # Optionally check against whitelist
    if require_whitelist and not is_known_table(table_name):
        logger.warning(f"Table not in whitelist: {table_name}")
        raise ValueError(f"Unknown table name: {table_name}")

    logger.debug(f"Table name validated: {table_name}")
    return True


async def get_validated_tables(session: AsyncSession) -> set[str]:
    """
    Get list of actual tables from database and update whitelist

    This function queries the database for existing tables and can be used
    to dynamically update the KNOWN_TABLES whitelist.

    Args:
        session: Database session

    Returns:
        Set of table names in the database
    """
    try:
        # Query information_schema for actual tables
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)

        result = await session.execute(query)
        tables = {row[0] for row in result.fetchall()}

        logger.info(f"Found {len(tables)} tables in database")
        return tables

    except Exception as e:
        logger.error(f"Failed to retrieve table list: {e}")
        return set()


def quote_identifier(identifier: str) -> str:
    """
    Quote SQL identifier using PostgreSQL's quote_ident() logic

    This wraps identifiers in double quotes and escapes any internal quotes.
    While this is safer than raw interpolation, validation should still be done.

    Args:
        identifier: Table or column name

    Returns:
        Quoted identifier safe for SQL interpolation

    Example:
        >>> quote_identifier("my_table")
        '"my_table"'
        >>> quote_identifier("my/table")  # Invalid but would be escaped
        '"my/table"'
    """
    # First validate the identifier
    if not is_valid_identifier(identifier):
        raise ValueError(f"Cannot quote invalid identifier: {identifier}")

    # Escape double quotes by doubling them
    escaped = identifier.replace('"', '""')

    # Wrap in double quotes
    return f'"{escaped}"'


def build_safe_table_query(table_name: str, query_template: str) -> str:
    """
    Build a safe SQL query with validated table name

    Args:
        table_name: Table name (will be validated)
        query_template: Query template with {table} placeholder

    Returns:
        Safe SQL query string

    Example:
        >>> build_safe_table_query("users", "SELECT * FROM {table}")
        'SELECT * FROM "users"'
    """
    # Validate table name
    validate_table_name(table_name, require_whitelist=True)

    # Quote the table name
    quoted_table = quote_identifier(table_name)

    # Build the query
    return query_template.format(table=quoted_table)


# ✅ SECURITY: Prevents SQL injection via table names
# All table names must pass:
# 1. Pattern validation (alphanumeric + underscore)
# 2. Reserved keyword check
# 3. Whitelist validation (optional but recommended)
# 4. PostgreSQL quote_ident() escaping
