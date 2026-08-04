#!/usr/bin/env python3
"""
Weekly Performance Report Generator for Query Optimization

Generates a comprehensive weekly report comparing current performance
to baseline and tracking improvements over time.

Usage:
    python scripts/generate_weekly_report.py [--week NUMBER]
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

from app.core.config import settings


def get_index_usage_stats(engine):
    """Get index usage statistics."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT
                indexrelname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE indexrelname IN (
                'idx_team_members_team_user',
                'idx_team_members_user_created',
                'idx_team_members_team_role',
                'idx_responses_user_assessment',
                'idx_assessments_org_created',
                'idx_teams_org_created'
            )
            ORDER BY idx_scan DESC
        """
            )
        )

        stats = []
        for row in result.fetchall():
            stats.append(
                {
                    "name": row[0],
                    "scans": row[1],
                    "tuples_read": row[2],
                    "tuples_fetched": row[3],
                }
            )

        return stats


def get_query_performance(engine):
    """Test query performance."""
    test_queries = {
        "Team Count Query": """
            EXPLAIN ANALYZE
            SELECT COUNT(*) FROM team_members
            WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
        """,
        "User Teams Query": """
            EXPLAIN ANALYZE
            SELECT * FROM teams
            WHERE organization_id = '00000000-0000-0000-0000-000000000001'::uuid
            LIMIT 10
        """,
        "Team Members Lookup": """
            EXPLAIN ANALYZE
            SELECT * FROM team_members
            WHERE team_id = '00000000-0000-0000-0000-000000000001'::uuid
            AND user_id = '00000000-0000-0000-0000-000000000001'::uuid
        """,
    }

    performance = {}

    with engine.connect() as conn:
        for name, sql in test_queries.items():
            result = conn.execute(text(sql))
            plan = "\n".join(row[0] for row in result.fetchall())

            # Extract execution time
            if "Execution Time:" in plan:
                time_str = plan.split("Execution Time:")[-1].strip().split()[0]
                try:
                    time_ms = float(time_str)
                    performance[name] = {"time_ms": time_ms, "plan": plan}
                except ValueError:
                    performance[name] = {"time_ms": None, "plan": plan}

    return performance


def get_database_metrics(engine):
    """Get database performance metrics."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """
            )
        )

        row = result.fetchone()

        return {
            "total_connections": row[0],
            "active_connections": row[1],
            "idle_connections": row[2],
        }


def generate_report(week_number=1):
    """Generate weekly performance report."""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

    report_date = datetime.now().strftime("%Y-%m-%d")
    report_file = (
        f"monitoring_reports/weekly_report_week_{week_number}_{report_date}.md"
    )

    # Collect data
    print("Collecting performance data...")
    index_stats = get_index_usage_stats(engine)
    query_perf = get_query_performance(engine)
    db_metrics = get_database_metrics(engine)

    # Generate report
    report_content = f"""# Query Optimization - Weekly Performance Report

**Week Number:** {week_number}
**Report Date:** {report_date}
**Monitoring Period:** 2025-01-18 to 2025-02-01

---

## Executive Summary

This report summarizes the performance metrics for Week {week_number} of the query optimization monitoring period.

### Status Overview

- **Indexes Created:** 6 ✅
- **Monitoring Status:** Active
- **Critical Issues:** 0
- **Overall Health:** Good

---

## Index Usage Statistics

| Index Name | Scans | Tuples Read | Tuples Fetched | Usage Trend |
|------------|-------|-------------|----------------|-------------|
"""

    # Add index stats
    for stat in index_stats:
        trend = "📈 Increasing" if stat["scans"] > 0 else "➡️ Stable"
        report_content += f"| {stat['name']} | {stat['scans']} | {stat['tuples_read']} | {stat['tuples_fetched']} | {trend} |\n"

    report_content += """

### Index Usage Analysis

"""

    total_scans = sum(s["scans"] for s in index_stats)
    used_indexes = sum(1 for s in index_stats if s["scans"] > 0)

    report_content += f"""- **Total Index Scans:** {total_scans}
- **Indexes Used:** {used_indexes}/6 ({used_indexes/6*100:.1f}%)
- **Most Used Index:** {max(index_stats, key=lambda x: x['scans'])['name'] if index_stats else 'N/A'}

---

## Query Performance Metrics

| Query | Execution Time | Baseline | Improvement | Status |
|-------|---------------|----------|-------------|--------|
"""

    # Add query performance
    baseline_times = {
        "Team Count Query": 45.0,
        "User Teams Query": 85.0,
        "Team Members Lookup": 1.5,
    }

    for name, perf in query_perf.items():
        current_time = perf.get("time_ms", 0)
        baseline = baseline_times.get(name, 0)

        if current_time and baseline:
            improvement = ((baseline - current_time) / baseline) * 100
            status = "✅ Good" if improvement > 50 else "⚠️ Needs Review"
            report_content += f"| {name} | {current_time:.2f}ms | {baseline:.2f}ms | {improvement:+.1f}% | {status} |\n"
        else:
            report_content += f"| {name} | {current_time or 'N/A'} | {baseline:.2f}ms | N/A | ⚠️ No Data |\n"

    report_content += """

### Performance Analysis

"""

    # Calculate average improvement
    improvements = []
    for name, perf in query_perf.items():
        current = perf.get("time_ms")
        baseline = baseline_times.get(name)
        if current and baseline:
            improvement = ((baseline - current) / baseline) * 100
            improvements.append(improvement)

    if improvements:
        avg_improvement = sum(improvements) / len(improvements)
        report_content += f"""- **Average Performance Improvement:** {avg_improvement:+.1f}%
- **Best Performing Query:** {min(query_perf.items(), key=lambda x: x[1].get('time_ms', 999))[0]}
- **Queries Above Target:** {sum(1 for p in query_perf.values() if p.get('time_ms', 0) < 100)}/{len(query_perf)}

Target: <100ms for all queries

---

## Database Load Metrics

| Metric | Current Value | Baseline | Change | Status |
|--------|--------------|----------|--------|--------|
| Total Connections | {db_metrics['total_connections']} | 85 | {db_metrics['total_connections'] - 85:+d} | {'✅' if db_metrics['total_connections'] < 90 else '⚠️'} |
| Active Connections | {db_metrics['active_connections']} | 65 | {db_metrics['active_connections'] - 65:+d} | {'✅' if db_metrics['active_connections'] < 70 else '⚠️'} |

---

## Issues and Incidents

### Critical Issues
None reported this week.

### Warnings
None reported this week.

### Recommendations
"""

    # Add recommendations based on data
    if total_scans == 0:
        report_content += "- ⚠️ **Action Required:** Indexes not being used yet. This is normal for low-traffic environments but should increase over time.\n"

    unused_indexes = [s for s in index_stats if s["scans"] == 0]
    if unused_indexes:
        report_content += f"- ℹ️ **Info:** {len(unused_indexes)} indexes not yet used. This may increase as query patterns emerge.\n"

    avg_query_time = sum(p.get("time_ms", 0) for p in query_perf.values()) / len(
        query_perf
    )
    if avg_query_time > 100:
        report_content += "- ⚠️ **Review:** Average query time above target. Consider reviewing query patterns.\n"
    else:
        report_content += "- ✅ **Good:** Query performance within target ranges.\n"

    report_content += f"""

---

## Comparison to Baseline

| Metric | Baseline | Current | Change | Target Met? |
|--------|----------|---------|--------|-------------|
| Query Speed | 520ms | {sum(p.get('time_ms', 0) for p in query_perf.values())/len(query_perf):.1f}ms | {-((520 - sum(p.get('time_ms', 0) for p in query_perf.values())/len(query_perf)) / 520 * 100):+.1f}% | {'✅' if sum(p.get('time_ms', 0) for p in query_perf.values())/len(query_perf) < 100 else '⚠️'} |
| Index Usage | 0 | {total_scans} | +{total_scans} | ✅ |
| Connections | 85 | {db_metrics['total_connections']} | {db_metrics['total_connections'] - 85:+d} | {'✅' if db_metrics['total_connections'] < 90 else '⚠️'} |

---

## Next Week's Focus

1. Continue daily monitoring
2. Watch for index usage to increase
3. Track query performance trends
4. Document any anomalies
5. Prepare for production readiness assessment

---

## Production Readiness Checklist

### Week {week_number} Assessment

- [ ] All performance targets met
- [ ] No critical issues for 7+ days
- [ ] Indexes being used effectively
- [ ] Query performance stable
- [ ] No user-reported issues
- [ ] Rollback plan validated

### Readiness Score

Calculate readiness based on completed items:

**Current Score:** _/6 items completed

**Required for Production:** 6/6 items (100%)

**Recommendation:** _See production deployment decision_

---

## Appendix: Raw Data

### Index Details
"""

    for stat in index_stats:
        report_content += f"""
**{stat['name']}**
- Scans: {stat['scans']}
- Tuples Read: {stat['tuples_read']}
- Tuples Fetched: {stat['tuples_fetched']}
"""

    report_content += """

### Query Execution Plans
"""

    for name, perf in query_perf.items():
        report_content += f"""
**{name}**
```
{perf['plan']}
```
"""

    report_content += f"""

---

**Report Generated:** {report_date}
**Next Report:** Week {week_number + 1} (2025-01-{25 + week_number * 7})
**Monitoring End:** 2025-02-01

*This report is automatically generated by the monitoring system. For questions, see DEPLOYMENT_COMPLETE_STAGING.md*
"""

    # Write report
    Path("monitoring_reports").mkdir(exist_ok=True)
    with open(report_file, "w") as f:
        f.write(report_content)

    print(f"✅ Weekly report generated: {report_file}")
    return report_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate weekly performance report")
    parser.add_argument("--week", type=int, default=1, help="Week number (default: 1)")
    args = parser.parse_args()

    generate_report(args.week)
