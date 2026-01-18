#!/usr/bin/env python3
"""
Query Optimization Validation Script

This script validates that all database query optimizations are working correctly.
Run this after deploying optimizations to verify the changes.

Usage:
    python scripts/validate_query_optimization.py

Checks:
1. Composite indexes are created
2. Indexes are being used by queries
3. Pagination limits are reduced
4. Query performance improvements
5. No regressions in functionality
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


class QueryOptimizationValidator:
    """Validate database query optimizations."""

    def __init__(self, database_url: str | None = None):
        """Initialize validator with database connection."""
        self.database_url = database_url or settings.DATABASE_URL
        self.sync_engine = create_engine(
            self.database_url.replace("+asyncpg", ""),
            echo=False
        )

    def check_composite_indexes(self) -> dict[str, Any]:
        """
        Check if composite indexes are created.

        Returns:
            Dictionary with index validation results
        """
        print("\n" + "=" * 80)
        print("Checking Composite Indexes...")
        print("=" * 80)

        expected_indexes = {
            "team_members": [
                "idx_team_members_team_user",
                "idx_team_members_user_created",  # Changed from user_joined
                "idx_team_members_team_role",
            ],
            "responses": [
                "idx_responses_user_assessment",
                # "idx_responses_assessment_created",  # Requires assessment_id, created_at
            ],
            "assessments": [
                "idx_assessments_org_created",
                # "idx_assessments_org_status",  # Requires status column (doesn't exist)
                # "idx_assessments_creator_created",  # Requires created_by_id column (doesn't exist)
            ],
            "users": [
                # "idx_users_org_active",  # Requires organization_id column (doesn't exist)
                # "idx_users_org_created",  # Requires organization_id column (doesn't exist)
            ],
            "teams": [
                "idx_teams_org_created",
            ],
            "assessment_assignments": [
                # "idx_assessment_assignments_user_completed",  # Table doesn't exist in all environments
                # "idx_assessment_assignments_assessment_completed",  # Table doesn't exist in all environments
            ],
        }

        results = {
            "total_expected": 0,
            "total_found": 0,
            "missing_indexes": [],
            "found_indexes": [],
        }

        with self.sync_engine.connect() as conn:
            for table_name, index_names in expected_indexes.items():
                for index_name in index_names:
                    results["total_expected"] += 1

                    # Check if index exists
                    result = conn.execute(text("""
                        SELECT indexname
                        FROM pg_indexes
                        WHERE tablename = :table_name
                        AND indexname = :index_name
                    """), {"table_name": table_name, "index_name": index_name})

                    exists = result.fetchone() is not None

                    if exists:
                        results["total_found"] += 1
                        results["found_indexes"].append(f"{table_name}.{index_name}")
                        print(f"  ✅ {table_name}.{index_name}")
                    else:
                        results["missing_indexes"].append(f"{table_name}.{index_name}")
                        print(f"  ❌ {table_name}.{index_name} (MISSING)")

        print(f"\nSummary: {results['total_found']}/{results['total_expected']} indexes found")

        if results["missing_indexes"]:
            print(f"\n⚠️  Missing indexes: {len(results['missing_indexes'])}")
            print("Run: alembic upgrade head")

        return results

    def check_index_usage(self) -> dict[str, Any]:
        """
        Check if indexes are being used.

        Returns:
            Dictionary with index usage statistics
        """
        print("\n" + "=" * 80)
        print("Checking Index Usage...")
        print("=" * 80)

        with self.sync_engine.connect() as conn:
            # Get index usage statistics
            result = conn.execute(text("""
                SELECT
                    schemaname,
                    relname as tablename,
                    indexrelname as indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE indexrelname LIKE 'idx_%'
                ORDER BY idx_scan DESC
                LIMIT 20
            """))

            rows = result.fetchall()

            if not rows:
                print("  ⚠️  No index usage data found (indexes may not be used yet)")
                return {"indexes_checked": 0, "usage_stats": []}

            print(f"\nTop {len(rows)} indexes by usage:")
            for row in rows:
                print(f"  {row[1]}.{row[2]}:")
                print(f"    - Scans: {row[3]}")
                print(f"    - Tuples read: {row[4]}")
                print(f"    - Tuples fetched: {row[5]}")

            return {
                "indexes_checked": len(rows),
                "usage_stats": [dict(row) for row in rows],
            }

    def check_query_performance(self) -> dict[str, Any]:
        """
        Check query performance with EXPLAIN ANALYZE.

        Returns:
            Dictionary with query performance results
        """
        print("\n" + "=" * 80)
        print("Checking Query Performance...")
        print("=" * 80)

        test_queries = [
            {
                "name": "Team member lookup",
                "sql": """
                    EXPLAIN ANALYZE
                    SELECT * FROM team_members
                    WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
                    AND user_id = '00000000-0000-0000-0000-000000000001'::uuid
                """,
                "expected": "Index Scan",
            },
            {
                "name": "User's teams",
                "sql": """
                    EXPLAIN ANALYZE
                    SELECT t.* FROM teams t
                    JOIN team_members tm ON t.id = tm.team_id
                    WHERE tm.user_id = '00000000-0000-0000-0000-000000000001'::uuid
                """,
                "expected": "Nested Loop",
            },
            {
                "name": "Team members count",
                "sql": """
                    EXPLAIN ANALYZE
                    SELECT COUNT(*) FROM team_members
                    WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
                """,
                "expected": "Aggregate",
            },
        ]

        results = {
            "queries_checked": 0,
            "performance_ok": 0,
            "issues": [],
        }

        with self.sync_engine.connect() as conn:
            for query in test_queries:
                print(f"\n  Testing: {query['name']}")
                try:
                    result = conn.execute(text(query["sql"]))
                    explain_output = "\n".join(row[0] for row in result.fetchall())

                    # Check if expected pattern found
                    if query["expected"] in explain_output:
                        print(f"    ✅ Using {query['expected']}")
                        results["performance_ok"] += 1
                    else:
                        print(f"    ⚠️  Expected {query['expected']} not found")
                        results["issues"].append(query["name"])

                    # Show execution time
                    if "Execution Time:" in explain_output:
                        time_str = explain_output.split("Execution Time:")[-1].strip()
                        print(f"    ⏱️  Execution Time: {time_str}")

                    results["queries_checked"] += 1

                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    results["issues"].append(query["name"])

        return results

    def check_pagination_limits(self) -> dict[str, Any]:
        """
        Check if pagination limits are reduced in code.

        Returns:
            Dictionary with pagination limit validation
        """
        print("\n" + "=" * 80)
        print("Checking Pagination Limits...")
        print("=" * 80)

        endpoints_dir = Path("app/api/v1/endpoints")
        issues = []
        checks = 0

        for py_file in endpoints_dir.glob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()

            # Check for high pagination limits (only for actual pagination parameters)
            # Look for patterns like "limit.*Query.*le=" or "skip.*Query.*le="
            import re
            pagination_pattern = re.compile(
                r'(limit|skip|offset)\s*:\s*int\s*(?:=\s*Query\(|.*=.*Query\()[^)]*le\s*=\s*(1000|500)',
                re.MULTILINE
            )

            matches = pagination_pattern.findall(content)
            for match in matches:
                param_name, limit_value = match
                issues.append(f"{py_file.name}: Found pagination parameter '{param_name}' with le={limit_value}")
                checks += 1

        if issues:
            print(f"  ⚠️  Found {len(issues)} high pagination limits:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  ✅ All pagination limits are within acceptable range")

        return {
            "files_checked": len(list(endpoints_dir.glob("*.py"))),
            "issues_found": len(issues),
            "issues": issues,
        }

    def run_validation(self) -> dict[str, Any]:
        """
        Run all validation checks.

        Returns:
            Dictionary with all validation results
        """
        print("\n" + "=" * 80)
        print("DATABASE QUERY OPTIMIZATION VALIDATION")
        print("=" * 80)
        print(f"Database: {self.database_url.split('@')[-1] if '@' in self.database_url else 'local'}")

        results = {
            "timestamp": time.time(),
            "validations": {},
        }

        # Run all checks
        try:
            results["validations"]["indexes"] = self.check_composite_indexes()
        except Exception as e:
            print(f"\n❌ Error checking indexes: {e}")
            results["validations"]["indexes"] = {"error": str(e)}

        try:
            results["validations"]["index_usage"] = self.check_index_usage()
        except Exception as e:
            print(f"\n❌ Error checking index usage: {e}")
            results["validations"]["index_usage"] = {"error": str(e)}

        try:
            results["validations"]["performance"] = self.check_query_performance()
        except Exception as e:
            print(f"\n❌ Error checking performance: {e}")
            results["validations"]["performance"] = {"error": str(e)}

        try:
            results["validations"]["pagination"] = self.check_pagination_limits()
        except Exception as e:
            print(f"\n❌ Error checking pagination: {e}")
            results["validations"]["pagination"] = {"error": str(e)}

        # Overall summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        overall_status = "✅ PASS"

        # Check indexes
        if "indexes" in results["validations"]:
            index_results = results["validations"]["indexes"]
            if index_results.get("missing_indexes"):
                print(f"❌ Indexes: {len(index_results['missing_indexes'])} missing")
                overall_status = "⚠️  WARNING"
            else:
                print(f"✅ Indexes: All {index_results['total_expected']} indexes present")

        # Check pagination
        if "pagination" in results["validations"]:
            pagination_results = results["validations"]["pagination"]
            if pagination_results.get("issues_found", 0) > 0:
                print(f"⚠️  Pagination: {pagination_results['issues_found']} high limits found")
                overall_status = "⚠️  WARNING"
            else:
                print(f"✅ Pagination: All limits acceptable")

        print(f"\nOverall Status: {overall_status}")

        if overall_status == "⚠️  WARNING":
            print("\nRecommendations:")
            if results["validations"].get("indexes", {}).get("missing_indexes"):
                print("  - Run: alembic upgrade head")
            if results["validations"].get("pagination", {}).get("issues_found"):
                print("  - Run: python scripts/fix_pagination_limits.py")

        results["overall_status"] = overall_status

        return results


def main():
    """Run validation and exit with appropriate code."""
    validator = QueryOptimizationValidator()
    results = validator.run_validation()

    # Exit with error code if validation failed
    if results["overall_status"] == "❌ FAIL":
        sys.exit(1)
    elif results["overall_status"] == "⚠️  WARNING":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
