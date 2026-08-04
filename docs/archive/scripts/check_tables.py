#!/usr/bin/env python3
"""Quick script to check database tables"""

import asyncio

from sqlalchemy import text

from app.db.database import engine


async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "AND (table_name LIKE '%sql%' OR table_name LIKE '%query%')"
            )
        )
        tables = [r[0] for r in result]
        print("Tables found:")
        for table in tables:
            print(f"  - {table}")

        if not tables:
            print("No SQL audit or query performance tables found!")

        # Check specifically for the tables we need
        needed = [
            "sql_queries",
            "sql_vulnerabilities",
            "sql_scan_reports",
            "slow_queries",
            "index_recommendations",
            "query_performance_history",
            "query_optimization_reports",
        ]
        for table in needed:
            result = await conn.execute(
                text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                )
            )
            exists = result.scalar()
            status = "✅" if exists else "❌"
            print(f"{status} {table}")


if __name__ == "__main__":
    asyncio.run(check_tables())
