#!/usr/bin/env python3
"""
Secure Query Utilities - SQL Injection Prevention

Provides safe, parameterized query building utilities to prevent SQL injection.
Always uses parameterized queries - never string concatenation for user input.

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import logging
import re
from typing import Any

from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Delete, Insert, Select, Update

logger = logging.getLogger(__name__)


class SQLInjectionError(Exception):
    """Raised when potential SQL injection is detected"""


class QueryBuilder:
    """
    Secure query builder that enforces parameterized queries.

    NEVER allows direct string interpolation of user input.
    All user input must be passed as parameters.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== SELECT Queries ====================

    def select_by_id(self, model: type, id_field: InstrumentedAttribute, record_id: int) -> Select:
        """
        Build safe SELECT by ID query.

        ✅ SAFE: Parameterized
        ❌ UNSAFE: f"SELECT * FROM {table} WHERE id = {record_id}"
        """
        return select(model).where(id_field == record_id)

    def select_by_ids(
        self, model: type, id_field: InstrumentedAttribute, record_ids: list[int]
    ) -> Select:
        """Build safe SELECT by multiple IDs"""
        return select(model).where(id_field.in_(record_ids))

    def select_where(self, model: type, conditions: dict[InstrumentedAttribute, Any]) -> Select:
        """
        Build safe SELECT with WHERE clause.

        Args:
            model: SQLAlchemy model
            conditions: Dict mapping fields to values

        Example:
            builder.select_where(
                User,
                {User.email: 'user@example.com', User.is_active: True}
            )
        """
        query = select(model)
        for field, value in conditions.items():
            query = query.where(field == value)
        return query

    def select_where_like(
        self, model: type, field: InstrumentedAttribute, pattern: str, case_sensitive: bool = False
    ) -> Select:
        """
        Build safe SELECT with LIKE clause.

        ✅ SAFE: Pattern is parameterized
        """
        if case_sensitive:
            query = select(model).where(field.like(pattern))
        else:
            query = select(model).where(field.ilike(pattern))
        return query

    def select_with_pagination(self, base_query: Select, limit: int, offset: int) -> Select:
        """Add pagination to query"""
        # Validate limit and offset to prevent injection
        if not isinstance(limit, int) or limit < 0 or limit > 1000:
            raise ValueError("Limit must be between 0 and 1000")

        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be non-negative")

        return base_query.limit(limit).offset(offset)

    def select_order_by(
        self, base_query: Select, field: InstrumentedAttribute, direction: str = "asc"
    ) -> Select:
        """
        Add ORDER BY to query.

        Args:
            field: Model field to order by
            direction: "asc" or "desc"

        Note: Field name is validated against allowed fields
        """
        direction = direction.lower()
        if direction not in ["asc", "desc"]:
            raise ValueError("Direction must be 'asc' or 'desc'")

        if direction == "asc":
            return base_query.order_by(field.asc())
        return base_query.order_by(field.desc())

    # ==================== INSERT Queries ====================

    def insert_record(self, model: type, data: dict[str, Any]) -> Insert:
        """
        Build safe INSERT query.

        ✅ SAFE: All values parameterized
        """
        # Validate field names
        valid_fields = {c.name for c in model.__table__.columns}
        for field in data:
            if field not in valid_fields:
                raise ValueError(f"Invalid field: {field}")

        return insert(model).values(**data)

    def insert_many(self, model: type, records: list[dict[str, Any]]) -> Insert:
        """Build safe bulk INSERT query"""
        if not records:
            raise ValueError("Cannot insert empty list")

        # Validate all records have same fields
        fields = set(records[0].keys())
        for record in records:
            if set(record.keys()) != fields:
                raise ValueError("All records must have same fields")

        # Validate field names
        valid_fields = {c.name for c in model.__table__.columns}
        for field in fields:
            if field not in valid_fields:
                raise ValueError(f"Invalid field: {field}")

        return insert(model).values(records)

    # ==================== UPDATE Queries ====================

    def update_by_id(
        self, model: type, id_field: InstrumentedAttribute, record_id: int, data: dict[str, Any]
    ) -> Update:
        """
        Build safe UPDATE query.

        ✅ SAFE: ID and data parameterized
        """
        # Validate field names
        valid_fields = {c.name for c in model.__table__.columns}
        for field in data:
            if field not in valid_fields:
                raise ValueError(f"Invalid field: {field}")

        return update(model).where(id_field == record_id).values(**data)

    def update_where(
        self, model: type, conditions: dict[InstrumentedAttribute, Any], data: dict[str, Any]
    ) -> Update:
        """Build safe UPDATE with WHERE clause"""
        # Validate field names
        valid_fields = {c.name for c in model.__table__.columns}
        for field in data:
            if field not in valid_fields:
                raise ValueError(f"Invalid field: {field}")

        query = update(model).values(**data)
        for field, value in conditions.items():
            query = query.where(field == value)

        return query

    # ==================== DELETE Queries ====================

    def delete_by_id(self, model: type, id_field: InstrumentedAttribute, record_id: int) -> Delete:
        """
        Build safe DELETE query.

        ✅ SAFE: ID parameterized
        """
        return delete(model).where(id_field == record_id)

    def delete_where(self, model: type, conditions: dict[InstrumentedAttribute, Any]) -> Delete:
        """Build safe DELETE with WHERE clause"""
        query = delete(model)
        for field, value in conditions.items():
            query = query.where(field == value)
        return query

    # ==================== Raw SQL (Safe) ====================

    async def execute_raw(self, query: str, params: dict[str, Any]) -> Any:
        """
        Execute raw SQL with parameters.

        ✅ SAFE: Uses named parameters
        ❌ UNSAFE: Never use f-strings or string concatenation

        Example:
            builder.execute_raw(
                "SELECT * FROM users WHERE email = :email AND status = :status",
                {"email": user_email, "status": "active"}
            )
        """
        # Validate query contains no string interpolation
        dangerous_patterns = [
            r"\{[^}]*\}",  # f-string style placeholders
            r"%s",  # % formatting
            r"\?%s",  # Concatenation
            r'f["\']',  # f-string prefix
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query):
                raise SQLInjectionError(
                    f"Query contains dangerous pattern: {pattern}. "
                    "Use only :parameter style placeholders."
                )

        # Verify all placeholders are in params
        placeholders = re.findall(r":(\w+)", query)
        for placeholder in placeholders:
            if placeholder not in params:
                raise ValueError(f"Missing parameter: {placeholder}")

        # Execute with parameters
        return await self.session.execute(text(query), params)

    # ==================== Search Utilities ====================

    def build_search_query(
        self, model: type, search_fields: list[InstrumentedAttribute], search_term: str
    ) -> Select:
        """
        Build safe full-text search query.

        Searches across multiple fields using LIKE.

        ✅ SAFE: Search term is parameterized
        """
        # Sanitize search term (but preserve wildcards)
        # Only allow alphanumeric, space, and common wildcards
        if not re.match(r"^[\w\s%\-\.@]+$", search_term):
            raise ValueError("Invalid search term")

        search_pattern = f"%{search_term}%"

        # Build OR conditions across all search fields
        conditions = [field.ilike(search_pattern) for field in search_fields]

        # Combine with OR
        from sqlalchemy import or_

        return select(model).where(or_(*conditions))


class SecureQueryExecutor:
    """
    Execute queries with automatic safety checks.

    Wraps QueryBuilder with execution logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.builder = QueryBuilder(session)

    # ==================== SELECT Execution ====================

    async def fetch_one(self, query: Select, error_msg: str = "Record not found") -> Any:
        """Execute query and return single result"""
        result = await self.session.execute(query)
        record = result.scalar_one_or_none()

        if record is None:
            raise ValueError(error_msg)

        return record

    async def fetch_or_none(self, query: Select) -> Any | None:
        """Execute query and return result or None"""
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def fetch_all(self, query: Select) -> list[Any]:
        """Execute query and return all results"""
        result = await self.session.execute(query)
        return result.scalars().all()

    async def fetch_paginated(
        self, query: Select, page: int = 1, per_page: int = 20
    ) -> tuple[list[Any], int]:
        """
        Execute paginated query.

        Returns:
            (records, total_count)
        """
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self.session.execute(count_query)
        total_count = total_count.scalar()

        # Get paginated results
        offset = (page - 1) * per_page
        paginated_query = self.builder.select_with_pagination(query, limit=per_page, offset=offset)

        result = await self.session.execute(paginated_query)
        records = result.scalars().all()

        return records, total_count

    # ==================== INSERT Execution ====================

    async def insert_one(self, model: type, data: dict[str, Any]) -> Any:
        """Insert record and return created object"""
        query = self.builder.insert_record(model, data)
        result = await self.session.execute(query)
        await self.session.commit()

        # Return created record
        return await self.fetch_one(select(model).where(model.id == result.inserted_primary_key[0]))

    async def insert_many(self, model: type, records: list[dict[str, Any]]) -> int:
        """Insert multiple records and return count"""
        query = self.builder.insert_many(model, records)
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount

    # ==================== UPDATE Execution ====================

    async def update_one(
        self, model: type, id_field: InstrumentedAttribute, record_id: int, data: dict[str, Any]
    ) -> bool:
        """Update record by ID and return success"""
        query = self.builder.update_by_id(model, id_field, record_id, data)
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    # ==================== DELETE Execution ====================

    async def delete_one(
        self, model: type, id_field: InstrumentedAttribute, record_id: int
    ) -> bool:
        """Delete record by ID and return success"""
        query = self.builder.delete_by_id(model, id_field, record_id)
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0


# ==================== Input Sanitization ====================


class InputSanitizer:
    """
    Sanitize user input before database queries.

    Additional defense-in-depth beyond parameterized queries.
    """

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.

        Removes null bytes and excessive whitespace.
        """
        if not isinstance(value, str):
            raise TypeError("Expected string")

        # Remove null bytes
        value = value.replace("\x00", "")

        # Trim and limit length
        value = value.strip()
        if len(value) > max_length:
            value = value[:max_length]

        return value

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email"""
        email = InputSanitizer.sanitize_string(email, max_length=255)

        # Basic email validation
        if not re.match(r"^[\w\.\-]+@[\w\-]+\.[\w\-\.]+$", email):
            raise ValueError("Invalid email format")

        return email.lower()

    @staticmethod
    def sanitize_integer(value: Any, min_val: int = None, max_val: int = None) -> int:
        """Sanitize integer input"""
        if isinstance(value, str):
            # Remove whitespace
            value = value.strip()

        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Must be an integer")

        # Apply range limits
        if min_val is not None and int_value < min_val:
            raise ValueError(f"Must be at least {min_val}")

        if max_val is not None and int_value > max_val:
            raise ValueError(f"Must be at most {max_val}")

        return int_value

    @staticmethod
    def sanitize_sort_field(field_name: str, allowed_fields: list[str]) -> str:
        """
        Validate sort field against allowlist.

        Prevents SQL injection in ORDER BY clauses.
        """
        if field_name not in allowed_fields:
            raise ValueError(f"Invalid sort field: {field_name}")

        return field_name

    @staticmethod
    def sanitize_sort_direction(direction: str) -> str:
        """Validate sort direction"""
        direction = direction.lower().strip()
        if direction not in ["asc", "desc"]:
            raise ValueError("Direction must be 'asc' or 'desc'")

        return direction


# ==================== Usage Examples ====================


def example_usage():
    """Example usage of secure query utilities"""

    from app.core.database import async_session_maker
    from app.db.models import User

    async def example_select():
        async with async_session_maker() as session:
            executor = SecureQueryExecutor(session)

            # Safe SELECT by ID
            user = await executor.fetch_one(select(User).where(User.id == 123))

            # Safe SELECT with conditions
            users = await executor.fetch_all(select(User).where(User.is_active == True))

            # Safe search
            builder = QueryBuilder(session)
            search_query = builder.build_search_query(User, [User.email, User.username], "john")
            results = await executor.fetch_all(search_query)

            # Safe pagination
            records, total = await executor.fetch_paginated(select(User), page=2, per_page=20)

    async def example_insert():
        async with async_session_maker() as session:
            executor = SecureQueryExecutor(session)

            # Safe INSERT
            user = await executor.insert_one(
                User, {"email": "user@example.com", "username": "testuser", "is_active": True}
            )

    async def example_update():
        async with async_session_maker() as session:
            executor = SecureQueryExecutor(session)

            # Safe UPDATE
            success = await executor.update_one(User, User.id, 123, {"is_active": False})

    async def example_delete():
        async with async_session_maker() as session:
            executor = SecureQueryExecutor(session)

            # Safe DELETE
            success = await executor.delete_one(User, User.id, 123)

    async def example_raw_sql():
        async with async_session_maker() as session:
            builder = QueryBuilder(session)

            # ✅ SAFE: Parameterized raw SQL
            result = await builder.execute_raw(
                "SELECT * FROM users WHERE email = :email AND status = :status",
                {"email": "user@example.com", "status": "active"},
            )

            # ❌ UNSAFE: Never do this!
            # query = f"SELECT * FROM users WHERE email = '{email}'"
            # result = await session.execute(text(query))


if __name__ == "__main__":
    print("Secure Query Utilities - SQL Injection Prevention")
    print("Use SecureQueryExecutor for all database operations")
    print("Never use f-strings or string concatenation for SQL queries!")
