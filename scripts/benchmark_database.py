#!/usr/bin/env python3
"""
Database Benchmarking Script

Captures baseline performance metrics before and after migrations.
Run this before starting migrations to establish a baseline.

Usage:
    python scripts/benchmark_database.py --capture-baseline
    python scripts/benchmark_database.py --compare-baseline baseline_2026_01_04.json
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

import uvloop
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import pg_table_size

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal, async_engine
from app.db.models import (
    Analytics,
    Assessment,
    AssessmentResponse,
    AuditLog,
    Response,
    User,
)


async def get_database_size() -> Dict[str, int]:
    """Get database and table sizes"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                """
            SELECT
                pg_database_size('psychsync') as db_size,
                pg_total_relation_size('responses') as responses_size,
                pg_total_relation_size('assessment_responses') as ar_size,
                pg_total_relation_size('analytics') as analytics_size,
                pg_total_relation_size('audit_logs') as audit_logs_size,
                pg_total_relation_size('users') as users_size,
                pg_total_relation_size('assessments') as assessments_size
        """
            )
        )

        row = result.fetchone()
        return {
            "database_size_gb": round(row[0] / (1024**3), 2),
            "responses_size_gb": round(row[1] / (1024**3), 2),
            "assessment_responses_size_gb": round(row[2] / (1024**3), 2),
            "analytics_size_gb": round(row[3] / (1024**3), 2),
            "audit_logs_size_gb": round(row[4] / (1024**3), 2),
            "users_size_gb": round(row[5] / (1024**3), 2),
            "assessments_size_gb": round(row[6] / (1024**3), 2),
        }


async def benchmark_response_queries() -> Dict[str, float]:
    """Benchmark response loading queries"""
    async with AsyncSessionLocal() as session:
        # Get a sample assessment_id
        result = await session.execute(select(Assessment.id).limit(1))
        assessment_id = result.scalar()

        if not assessment_id:
            return {"error": "No assessments found"}

        # Benchmark 1: Load all responses for assessment
        start = time.time()
        await session.execute(
            select(Response).where(Response.assessment_id == assessment_id).limit(1000)
        )
        load_all_time = time.time() - start

        # Benchmark 2: Load responses with user and question
        start = time.time()
        await session.execute(
            text(
                """
            SELECT
                r.id, r.assessment_id, r.user_id, r.score,
                u.email, u.full_name,
                q.question_text
            FROM responses r
            JOIN users u ON u.id = r.user_id
            JOIN assessment_questions q ON q.id = r.question_id
            WHERE r.assessment_id = :assessment_id
            LIMIT 1000
        """
            ),
            {"assessment_id": assessment_id},
        )
        load_with_joins_time = time.time() - start

        # Benchmark 3: Count responses
        start = time.time()
        await session.execute(
            select(func.count(Response.id)).where(
                Response.assessment_id == assessment_id
            )
        )
        count_time = time.time() - start

        return {
            "load_all_responses_ms": round(load_all_time * 1000, 2),
            "load_with_joins_ms": round(load_with_joins_time * 1000, 2),
            "count_responses_ms": round(count_time * 1000, 2),
        }


async def benchmark_analytics_queries() -> Dict[str, float]:
    """Benchmark analytics queries"""
    async with AsyncSessionLocal() as session:
        # Get a sample organization_id
        result = await session.execute(select(Assessment.organization_id).limit(1))
        org_id = result.scalar()

        if not org_id:
            return {"error": "No organizations found"}

        # Benchmark 1: Organization analytics summary
        start = time.time()
        await session.execute(
            text(
                """
            SELECT
                entity_type,
                COUNT(*) as record_count,
                AVG(overall_score) as avg_score,
                AVG(confidence_level) as avg_confidence
            FROM analytics
            WHERE organization_id = :org_id
            AND period_start >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY entity_type
        """
            ),
            {"org_id": org_id},
        )
        org_analytics_time = time.time() - start

        # Benchmark 2: User analytics with JOINs
        start = time.time()
        await session.execute(
            text(
                """
            SELECT
                u.id,
                u.email,
                a.overall_score,
                a.period_start,
                a.period_end
            FROM analytics a
            JOIN users u ON u.id = a.entity_id
            WHERE a.organization_id = :org_id
            AND a.entity_type = 'user'
            AND a.status = 'completed'
            ORDER BY a.period_start DESC
            LIMIT 100
        """
            ),
            {"org_id": org_id},
        )
        user_analytics_time = time.time() - start

        return {
            "org_analytics_ms": round(org_analytics_time * 1000, 2),
            "user_analytics_ms": round(user_analytics_time * 1000, 2),
        }


async def benchmark_dashboard_queries() -> Dict[str, float]:
    """Benchmark dashboard loading queries"""
    async with AsyncSessionLocal() as session:
        # Get a sample user_id
        result = await session.execute(select(User.id).limit(1))
        user_id = result.scalar()

        if not user_id:
            return {"error": "No users found"}

        # Benchmark 1: Load user's teams
        start = time.time()
        await session.execute(
            text(
                """
            SELECT
                t.id, t.name, t.description,
                tm.role,
                COUNT(DISTINCT tm2.user_id) as member_count
            FROM teams t
            JOIN team_members tm ON tm.team_id = t.id
            LEFT JOIN team_members tm2 ON tm2.team_id = t.id
            WHERE tm.user_id = :user_id
            GROUP BY t.id, t.name, t.description, tm.role
        """
            ),
            {"user_id": user_id},
        )
        teams_time = time.time() - start

        # Benchmark 2: Load user's assessments
        start = time.time()
        await session.execute(
            text(
                """
            SELECT
                a.id, a.title, a.status, a.category,
                COUNT(DISTINCT ar.respondent_id) as response_count
            FROM assessments a
            LEFT JOIN assessment_responses ar ON ar.assessment_id = a.id
            WHERE a.created_by_id = :user_id
            OR a.team_id IN (
                SELECT team_id FROM team_members WHERE user_id = :user_id
            )
            GROUP BY a.id, a.title, a.status, a.category
            ORDER BY a.created_at DESC
            LIMIT 20
        """
            ),
            {"user_id": user_id},
        )
        assessments_time = time.time() - start

        # Benchmark 3: Load user's recent activity
        start = time.time()
        await session.execute(
            text(
                """
            SELECT
                a.id as assessment_id,
                a.title as assessment_title,
                ar.status,
                ar.started_at,
                ar.completed_at
            FROM assessment_responses ar
            JOIN assessments a ON a.id = ar.assessment_id
            WHERE ar.respondent_id = :user_id
            ORDER BY ar.started_at DESC
            LIMIT 10
        """
            ),
            {"user_id": user_id},
        )
        activity_time = time.time() - start

        return {
            "load_teams_ms": round(teams_time * 1000, 2),
            "load_assessments_ms": round(assessments_time * 1000, 2),
            "load_activity_ms": round(activity_time * 1000, 2),
            "total_dashboard_load_ms": round(
                (teams_time + assessments_time + activity_time) * 1000, 2
            ),
        }


async def get_index_usage_stats() -> Dict[str, Any]:
    """Get index usage statistics"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                """
            SELECT
                COUNT(*) as total_indexes,
                COUNT(*) FILTER (WHERE idx_scan > 0) as used_indexes,
                COUNT(*) FILTER (WHERE idx_scan = 0) as unused_indexes,
                SUM(idx_scan) as total_index_scans,
                AVG(idx_scan) as avg_scans_per_index
            FROM pg_stat_user_indexes
        """
            )
        )

        row = result.fetchone()
        return {
            "total_indexes": row[0],
            "used_indexes": row[1],
            "unused_indexes": row[2],
            "total_index_scans": row[3],
            "avg_scans_per_index": round(row[4], 2) if row[4] else 0,
        }


async def get_slow_query_count() -> int:
    """Get count of slow queries (> 1 second) from pg_stat_statements"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM pg_stat_statements
                WHERE mean_exec_time > 1000
                AND calls > 10
            """
                )
            )
            return result.scalar() or 0
        except Exception:
            # pg_stat_statements might not be enabled
            return 0


async def get_table_row_counts() -> Dict[str, int]:
    """Get row counts for major tables"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                """
            SELECT
                (SELECT COUNT(*) FROM users) as users,
                (SELECT COUNT(*) FROM organizations) as organizations,
                (SELECT COUNT(*) FROM teams) as teams,
                (SELECT COUNT(*) FROM assessments) as assessments,
                (SELECT COUNT(*) FROM responses) as responses,
                (SELECT COUNT(*) FROM assessment_responses) as assessment_responses,
                (SELECT COUNT(*) FROM analytics) as analytics,
                (SELECT COUNT(*) FROM audit_logs) as audit_logs
        """
            )
        )

        row = result.fetchone()
        return {
            "users": row[0],
            "organizations": row[1],
            "teams": row[2],
            "assessments": row[3],
            "responses": row[4],
            "assessment_responses": row[5],
            "analytics": row[6],
            "audit_logs": row[7],
        }


async def capture_baseline(output_file: str):
    """Capture complete baseline metrics"""
    print(f"🔍 Capturing baseline metrics...")

    baseline = {
        "timestamp": datetime.now().isoformat(),
        "date": str(date.today()),
    }

    # Database size
    print("  📊 Measuring database sizes...")
    baseline["database_sizes"] = await get_database_size()

    # Row counts
    print("  📈 Counting table rows...")
    baseline["row_counts"] = await get_table_row_counts()

    # Query benchmarks
    print("  ⚡ Benchmarking response queries...")
    baseline["response_queries"] = await benchmark_response_queries()

    print("  ⚡ Benchmarking analytics queries...")
    baseline["analytics_queries"] = await benchmark_analytics_queries()

    print("  ⚡ Benchmarking dashboard queries...")
    baseline["dashboard_queries"] = await benchmark_dashboard_queries()

    # Index stats
    print("  📚 Analyzing index usage...")
    baseline["index_stats"] = await get_index_usage_stats()

    # Slow queries
    print("  🐌 Checking slow queries...")
    baseline["slow_query_count"] = await get_slow_query_count()

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\n✅ Baseline saved to {output_file}")
    print("\n📊 Baseline Summary:")
    print(f"  Database Size: {baseline['database_sizes']['database_size_gb']} GB")
    print(f"  Responses: {baseline['row_counts']['responses']:,} rows")
    print(
        f"  Dashboard Load: {baseline['dashboard_queries']['total_dashboard_load_ms']} ms"
    )
    print(f"  Total Indexes: {baseline['index_stats']['total_indexes']}")


async def compare_baseline(baseline_file: str):
    """Compare current performance with baseline"""
    print(f"📊 Comparing with baseline from {baseline_file}")

    # Load baseline
    with open(baseline_file, "r") as f:
        baseline = json.load(f)

    # Capture current metrics
    current = {
        "timestamp": datetime.now().isoformat(),
    }

    print("  📊 Measuring current database sizes...")
    current["database_sizes"] = await get_database_size()

    print("  📈 Counting current table rows...")
    current["row_counts"] = await get_table_row_counts()

    print("  ⚡ Benchmarking response queries...")
    current["response_queries"] = await benchmark_response_queries()

    print("  ⚡ Benchmarking analytics queries...")
    current["analytics_queries"] = await benchmark_analytics_queries()

    print("  ⚡ Benchmarking dashboard queries...")
    current["dashboard_queries"] = await benchmark_dashboard_queries()

    print("  📚 Analyzing index usage...")
    current["index_stats"] = await get_index_usage_stats()

    # Compare and calculate improvements
    print("\n📈 Performance Comparison:")
    print("=" * 60)

    # Response queries
    if "load_all_responses_ms" in baseline["response_queries"]:
        old_time = baseline["response_queries"]["load_all_responses_ms"]
        new_time = current["response_queries"]["load_all_responses_ms"]
        improvement = ((old_time - new_time) / old_time) * 100
        print(f"  Response Load Time:")
        print(f"    Before: {old_time:.2f} ms")
        print(f"    After:  {new_time:.2f} ms")
        print(f"    Change: {improvement:+.1f}% {'✅' if improvement > 0 else '❌'}")

    # Analytics queries
    if "org_analytics_ms" in baseline["analytics_queries"]:
        old_time = baseline["analytics_queries"]["org_analytics_ms"]
        new_time = current["analytics_queries"]["org_analytics_ms"]
        improvement = ((old_time - new_time) / old_time) * 100
        print(f"\n  Analytics Query Time:")
        print(f"    Before: {old_time:.2f} ms")
        print(f"    After:  {new_time:.2f} ms")
        print(f"    Change: {improvement:+.1f}% {'✅' if improvement > 0 else '❌'}")

    # Dashboard queries
    if "total_dashboard_load_ms" in baseline["dashboard_queries"]:
        old_time = baseline["dashboard_queries"]["total_dashboard_load_ms"]
        new_time = current["dashboard_queries"]["total_dashboard_load_ms"]
        improvement = ((old_time - new_time) / old_time) * 100
        print(f"\n  Dashboard Load Time:")
        print(f"    Before: {old_time:.2f} ms")
        print(f"    After:  {new_time:.2f} ms")
        print(f"    Change: {improvement:+.1f}% {'✅' if improvement > 0 else '❌'}")

    # Index stats
    print(f"\n  Index Statistics:")
    print(f"    Before: {baseline['index_stats']['total_indexes']} indexes")
    print(f"    After:  {current['index_stats']['total_indexes']} indexes")
    print(
        f"    Change: +{current['index_stats']['total_indexes'] - baseline['index_stats']['total_indexes']} indexes"
    )

    # Database size
    print(f"\n  Database Size:")
    print(f"    Before: {baseline['database_sizes']['database_size_gb']} GB")
    print(f"    After:  {current['database_sizes']['database_size_gb']} GB")
    print(
        f"    Change: +{current['database_sizes']['database_size_gb'] - baseline['database_sizes']['database_size_gb']:.2f} GB"
    )


async def main():
    parser = argparse.ArgumentParser(description="Database benchmarking tool")
    parser.add_argument(
        "--capture-baseline", action="store_true", help="Capture baseline metrics"
    )
    parser.add_argument(
        "--compare-baseline", type=str, help="Compare with baseline file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="baseline_metrics.json",
        help="Output file for baseline",
    )

    args = parser.parse_args()

    if args.capture_baseline:
        await capture_baseline(args.output)
    elif args.compare_baseline:
        await compare_baseline(args.compare_baseline)
    else:
        parser.print_help()


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
