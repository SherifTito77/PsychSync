#!/usr/bin/env python3

"""Module: seed_query_performance

Seed Query Performance functionality.
"""

import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from sqlalchemy import text

from app.core.database import get_async_db


async def seed_data():
    """Perform operation.

    Args:
        **kwargs: Input parameters

    Returns:
        Operation result
    """
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    async for db in get_async_db():
        try:
            # Seed slow queries
            queries_data = [
                (
                    "slow1",
                    "SELECT * FROM users WHERE email LIKE '%@test.com'",
                    "critical",
                    4500.0,
                    "full_scan",
                    "Add index on email",
                    "CREATE INDEX idx_users_email ON users(email)",
                ),
                (
                    "slow2",
                    "SELECT * FROM responses WHERE user_id IN (SELECT id FROM users WHERE active = true)",
                    "critical",
                    3200.0,
                    "n_plus_1",
                    "Use JOIN instead of subquery",
                    None,
                ),
                (
                    "slow3",
                    "SELECT * FROM assessments JOIN responses ON assessments.id = responses.assessment_id",
                    "slow",
                    850.0,
                    "missing_index",
                    "Add composite index",
                    "CREATE INDEX idx_responses_assessment ON responses(assessment_id)",
                ),
            ]

            for (
                q_hash,
                q_text,
                tier,
                avg_ms,
                bottleneck,
                suggestion,
                index_stmt,
            ) in queries_data:
                await db.execute(
                    text(
                        """
                    INSERT INTO slow_queries (query_hash, query_text, query_signature, performance_tier,
                        execution_count, total_time_ms, avg_time_ms, max_time_ms, min_time_ms,
                        impact_score, bottleneck_type, ai_suggestion, suggested_index, is_optimized)
                    VALUES (:h, :t, :t, :tier, 100, :total, :avg, :max, :min, :impact, :bot, :sug, :idx, 0.0)
                    ON CONFLICT (query_hash) DO NOTHING
                """
                    ),
                    {
                        "h": q_hash,
                        "t": q_text,
                        "tier": tier,
                        "total": avg_ms * 100,
                        "avg": avg_ms,
                        "max": avg_ms * 1.5,
                        "min": avg_ms * 0.5,
                        "impact": 95.0 if tier == "critical" else 50.0,
                        "bot": bottleneck,
                        "sug": suggestion,
                        "idx": index_stmt,
                    },
                )

            # Create reports
            for i in range(14):
                date = datetime.utcnow() - timedelta(days=13 - i)
                insights = {
                    "highlights": ["Scan completed"],
                    "recommendations": ["Add indexes"],
                }
                await db.execute(
                    text(
                        """
                    INSERT INTO query_optimization_reports (report_date, total_queries_analyzed,
                        slow_queries_count, critical_queries_count, avg_query_time_ms, p95_query_time_ms, p99_query_time_ms,
                        total_optimization_potential_ms, estimated_speedup_percentage, missing_indexes_count, n_plus_1_count,
                        full_table_scans, inefficient_joins, ai_summary, ai_insights)
                    VALUES (:d, 150, 25, 8, 800.0, 5000.0, 8000.0, 450000.0, 35.0, 12, 8, 15, 5, :sum, :ins)
                """
                    ),
                    {
                        "d": date,
                        "sum": f"Scan for {date.strftime('%Y-%m-%d')}",
                        "ins": json.dumps(insights),
                    },
                )

            await db.commit()
            print("✓ Query Performance data seeded")
        except Exception as e:
            await db.rollback()
            print(f"✗ Error: {e}")
            raise
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(seed_data())
