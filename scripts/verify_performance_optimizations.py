#!/usr/bin/env python3
"""
Performance Optimizations Verification Script

This script verifies that all performance optimizations are in place:
- Database indexes
- Async file I/O fixes
- Query optimization helpers available

Usage:
    python scripts/verify_performance_optimizations.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("Installing psycopg2...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Colors:
    """Terminal colors"""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.NC}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓{Colors.NC} {text}")


def print_error(text: str):
    print(f"{Colors.RED}✗{Colors.NC} {text}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {text}")


def verify_database_indexes():
    """Verify that performance indexes exist in the database"""
    print_header("Database Performance Indexes")

    # Get database connection info from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Try default PostgreSQL connection
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_pass = os.getenv("POSTGRES_PASSWORD", "")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "psychsync")

        try:
            conn = psycopg2.connect(
                user=db_user,
                password=db_pass,
                host=db_host,
                port=db_port,
                database=db_name,
            )
        except Exception as e:
            print_warning(f"Cannot connect to database: {e}")
            print_warning("Skipping database index verification")
            return
    else:
        conn = psycopg2.connect(db_url)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Expected indexes
    expected_indexes = {
        "assessments": [
            "idx_assessments_created_at",
            "idx_assessments_user_id",
            "idx_assessments_status",
            "idx_assessments_user_status",
            "idx_assessments_org_created",
        ],
        "responses": [
            "idx_responses_assessment_id",
            "idx_responses_user_id",
            "idx_responses_created_at",
            "idx_responses_assessment_user",
        ],
        "teams": [
            "idx_teams_organization_id",
            "idx_teams_created_at",
        ],
        "team_members": [
            "idx_team_members_team_user",
            "idx_team_members_role",
        ],
        "users": [
            "idx_users_created_at",
            "idx_users_is_active",
            "idx_users_email",
        ],
    }

    total_expected = sum(len(indexes) for indexes in expected_indexes.values())
    total_found = 0

    for table, indexes in expected_indexes.items():
        print(f"\n{Colors.BOLD}Table: {table}{Colors.NC}")

        # Check which indexes exist
        cursor.execute(
            f"""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = '{table}'
        """
        )

        existing_indexes = {row[0] for row in cursor.fetchall()}

        for index_name in indexes:
            if index_name in existing_indexes:
                print_success(f"  {index_name}")
                total_found += 1
            else:
                print_error(f"  {index_name} (missing)")

    cursor.close()
    conn.close()

    print(f"\n{Colors.BOLD}Summary:{Colors.NC}")
    print(f"  Indexes found: {total_found}/{total_expected}")

    if total_found == total_expected:
        print_success("All performance indexes are in place!")
        return True
    else:
        print_warning(f"{total_expected - total_found} indexes missing")
        return False


def verify_async_file_io():
    """Verify that async file I/O is being used"""
    print_header("Async File I/O Fix")

    file_path = project_root / "app/services/data_export_service.py"

    if not file_path.exists():
        print_error("data_export_service.py not found")
        return False

    content = file_path.read_text()

    # Check for async file operations
    has_aiofiles = "import aiofiles" in content
    has_async_with = "async with aiofiles.open" in content
    no_sync_open = "with open(" not in content or content.count(
        "with open("
    ) < content.count("async with aiofiles.open(")

    print("Checking file I/O implementation...")

    if has_aiofiles:
        print_success("aiofiles imported")
    else:
        print_error("aiofiles not imported")

    if has_async_with:
        print_success("Using async file operations")
    else:
        print_warning("No async file operations found")

    if has_aiofiles and has_async_with:
        print_success("Async file I/O fix is in place!")
        return True
    else:
        print_error("Async file I/O fix not fully implemented")
        return False


def verify_query_helpers():
    """Verify that query optimization helpers exist"""
    print_header("Query Optimization Helpers")

    helper_file = project_root / "app/services/query_optimizer_helper.py"

    if not helper_file.exists():
        print_error("query_optimizer_helper.py not found")
        return False

    content = helper_file.read_text()

    # Check for key functions
    functions = [
        "get_assessment_with_responses_and_users",
        "get_user_assessments_with_responses",
        "get_team_members_with_users",
        "get_organization_analytics_optimized",
    ]

    all_present = True
    for func in functions:
        if f"async def {func}" in content:
            print_success(f"{func}")
        else:
            print_error(f"{func} (missing)")
            all_present = False

    if all_present:
        print_success("All query optimization helpers are implemented!")
        return True
    else:
        print_error("Some query optimization helpers missing")
        return False


def verify_profiling_tool():
    """Verify that profiling tool exists and is executable"""
    print_header("Performance Profiling Tool")

    profiler_path = project_root / "scripts/profile_api_endpoints.py"

    if not profiler_path.exists():
        print_error("Profiling tool not found")
        return False

    # Check if executable
    if os.access(profiler_path, os.X_OK):
        print_success("Profiling tool is executable")
    else:
        print_warning(
            "Profiling tool not executable (run: chmod +x scripts/profile_api_endpoints.py)"
        )

    # Check file content
    content = profiler_path.read_text()

    has_profiling = "ProfilerMetrics" in content
    has_concurrent = "concurrent" in content.lower()

    if has_profiling:
        print_success("Profiling logic implemented")

    if has_concurrent:
        print_success("Concurrent load testing implemented")

    if has_profiling and has_concurrent:
        print_success("Profiling tool is ready!")
        return True
    else:
        print_warning("Profiling tool may be incomplete")
        return False


def main():
    """Run all verifications"""
    print_header("Performance Optimizations Verification")

    results = {
        "Database Indexes": verify_database_indexes(),
        "Async File I/O": verify_async_file_io(),
        "Query Helpers": verify_query_helpers(),
        "Profiling Tool": verify_profiling_tool(),
    }

    print_header("Verification Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        if result:
            print_success(f"{check}")
        else:
            print_warning(f"{check}")

    print(f"\n{Colors.BOLD}Result: {passed}/{total} checks passed{Colors.NC}")

    if passed == total:
        print_success("\n✓ All performance optimizations are in place!")
        print(f"\n{Colors.BOLD}Next steps:{Colors.NC}")
        print("  1. Run profiling: python scripts/profile_api_endpoints.py")
        print("  2. Use query helpers in your endpoints")
        print("  3. Monitor performance improvements")
    else:
        print_warning(f"\n{total - passed} optimization(s) need attention")
        print(f"\n{Colors.BOLD}To apply missing optimizations:{Colors.NC}")
        print("  1. Review PERFORMANCE_COMPLETE_SUMMARY.md")
        print("  2. Check migration status: alembic current")
        print("  3. Apply migration if needed: alembic upgrade head")

    print()


if __name__ == "__main__":
    main()
