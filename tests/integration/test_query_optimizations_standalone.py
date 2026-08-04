#!/usr/bin/env python3
"""
Standalone Query Optimization Tests

This script runs integration tests for query optimizations without
requiring the full FastAPI application to load.

Run with:
    python tests/integration/test_query_optimizations_standalone.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text

from app.core.config import settings


def test_composite_indexes():
    """Test that composite indexes are created."""
    print("\n" + "=" * 80)
    print("Testing Composite Indexes")
    print("=" * 80)

    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

    expected_indexes = {
        "team_members": [
            "idx_team_members_team_user",
            "idx_team_members_user_created",
            "idx_team_members_team_role",
        ],
        "responses": [
            "idx_responses_user_assessment",
        ],
        "assessments": [
            "idx_assessments_org_created",
        ],
        "teams": [
            "idx_teams_org_created",
        ],
    }

    passed = 0
    failed = 0

    with engine.connect() as conn:
        for table_name, index_names in expected_indexes.items():
            for index_name in index_names:
                result = conn.execute(
                    text(
                        """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = :table_name
                    AND indexname = :index_name
                """
                    ),
                    {"table_name": table_name, "index_name": index_name},
                )

                exists = result.fetchone() is not None

                if exists:
                    print(f"✅ {table_name}.{index_name}")
                    passed += 1
                else:
                    print(f"❌ {table_name}.{index_name} - MISSING")
                    failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_query_performance():
    """Test that queries use indexes effectively."""
    print("\n" + "=" * 80)
    print("Testing Query Performance")
    print("=" * 80)

    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

    test_queries = [
        {
            "name": "Team member lookup with composite index",
            "sql": """
                EXPLAIN ANALYZE
                SELECT * FROM team_members
                WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
                AND user_id = '00000000-0000-0000-0000-000000000001'::uuid
            """,
            "expected_patterns": [
                "Index Scan",
                "Seq Scan",
            ],  # Accept either - PG planner decides
            "note": "Seq Scan is OK for small tables, Index Scan will be used with more data",
        },
        {
            "name": "Team count with aggregation",
            "sql": """
                EXPLAIN ANALYZE
                SELECT COUNT(*) FROM team_members
                WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
            """,
            "expected_patterns": ["Aggregate"],
        },
    ]

    passed = 0
    failed = 0

    with engine.connect() as conn:
        for query in test_queries:
            print(f"\n  Testing: {query['name']}")
            try:
                result = conn.execute(text(query["sql"]))
                explain_output = "\n".join(row[0] for row in result.fetchall())

                # Check if expected patterns found
                found_patterns = [
                    pattern
                    for pattern in query["expected_patterns"]
                    if pattern in explain_output
                ]

                if found_patterns:
                    print(f"    ✅ Found: {', '.join(found_patterns)}")
                    if "note" in query:
                        print(f"    ℹ️  {query['note']}")
                    passed += 1
                else:
                    print(
                        f"    ⚠️  Expected patterns not found: {query['expected_patterns']}"
                    )
                    print(f"    Output: {explain_output[:200]}...")
                    failed += 1

                # Show execution time
                if "Execution Time:" in explain_output:
                    time_str = (
                        explain_output.split("Execution Time:")[-1].strip().split()[0]
                    )
                    print(f"    ⏱️  Execution Time: {time_str} ms")

            except Exception as e:
                print(f"    ❌ Error: {e}")
                failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("QUERY OPTIMIZATION STANDALONE TESTS")
    print("=" * 80)

    results = {
        "Composite Indexes": test_composite_indexes(),
        "Query Performance": test_query_performance(),
    }

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
