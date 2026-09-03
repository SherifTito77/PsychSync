#!/usr/bin/env python
"""Test SQL audit endpoint"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import func, select

from app.db.database import get_async_db
from app.db.models.sql_audit import SQLQuery, SQLVulnerability


async def test_query():
    """Test database query"""
    async for db in get_async_db():
        # Test simple query
        result = await db.execute(select(func.count(SQLQuery.id)))
        count = result.scalar()
        print(f"Total queries: {count}")

        # Test fetching data
        result = await db.execute(select(SQLQuery).limit(1))
        query = result.scalar_one_or_none()
        if query:
            print(
                f"Sample query: id={query.id}, is_fixed={query.is_fixed} (type: {type(query.is_fixed)})"
            )
            print(f"risk_level: {query.risk_level}")
            print(
                f"is_parameterized: {query.is_parameterized} (type: {type(query.is_parameterized)})"
            )

            # Test Pydantic serialization
            from app.schemas.sql_audit import SQLQuery as SQLQuerySchema

            try:
                schema = SQLQuerySchema.model_validate(query)
                print(f"✅ Pydantic validation passed: {schema}")
            except Exception as e:
                print(f"❌ Pydantic validation failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_query())
