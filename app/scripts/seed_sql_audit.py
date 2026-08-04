#!/usr/bin/env python3
"""
app/scripts/seed_sql_audit.py
Seed SQL Audit data for testing
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


async def seed_sql_audit_data():
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
    """Seed SQL audit test data"""
    async for db in get_async_db():
        try:
            # Sample SQL queries with vulnerabilities
            queries = [
                {
                    "query_hash": "a1b2c3d4e5f6",
                    "file_path": "app/crud/crud_user.py",
                    "line_number": 45,
                    "query_text": 'SELECT * FROM users WHERE id = "' + '{user_id}"',
                    "risk_level": "critical",
                    "risk_score": 95.0,
                    "vulnerability_type": "concat",
                    "is_parameterized": 0.0,
                    "uses_orm": 0.0,
                    "has_user_input": 1.0,
                    "ai_suggestion": "Use parameterized query: SELECT * FROM users WHERE id = :user_id",
                    "safe_example": "conn.execute(text('SELECT * FROM users WHERE id = :user_id'), {'user_id': user_id})",
                    "reference_url": "https://owasp.org/www-community/attacks/SQL_Injection",
                    "is_fixed": 0.0,
                    "fix_priority": "urgent",
                    "scanned_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                    "last_scanned": datetime.utcnow()
                    - timedelta(days=random.randint(0, 5)),
                },
                {
                    "query_hash": "f6e5d4c3b2a1",
                    "file_path": "app/api/v1/endpoints/reports.py",
                    "line_number": 123,
                    "query_text": 'SELECT * FROM reports WHERE name = "{report_name}"',
                    "risk_level": "high",
                    "risk_score": 85.0,
                    "vulnerability_type": "format",
                    "is_parameterized": 0.0,
                    "uses_orm": 0.0,
                    "has_user_input": 1.0,
                    "ai_suggestion": "Use SQLAlchemy ORM with parameter binding",
                    "safe_example": "session.query(Report).filter(Report.name == report_name).all()",
                    "reference_url": None,
                    "is_fixed": 0.0,
                    "fix_priority": "high",
                    "scanned_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                    "last_scanned": datetime.utcnow()
                    - timedelta(days=random.randint(0, 5)),
                },
                {
                    "query_hash": "x9y8z7w6v5u4",
                    "file_path": "app/services/assessment.py",
                    "line_number": 78,
                    "query_text": "SELECT * FROM assessments WHERE id = {assessment_id}",
                    "risk_level": "critical",
                    "risk_score": 92.0,
                    "vulnerability_type": "fstring",
                    "is_parameterized": 0.0,
                    "uses_orm": 0.0,
                    "has_user_input": 1.0,
                    "ai_suggestion": "Never use f-strings for SQL queries. Use parameterized queries.",
                    "safe_example": "conn.execute(text('SELECT * FROM assessments WHERE id = :id'), {'id': assessment_id})",
                    "reference_url": None,
                    "is_fixed": 0.0,
                    "fix_priority": "urgent",
                    "scanned_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                    "last_scanned": datetime.utcnow()
                    - timedelta(days=random.randint(0, 5)),
                },
                {
                    "query_hash": "p1o2i3u4y5t6",
                    "file_path": "app/api/v1/endpoints/auth.py",
                    "line_number": 201,
                    "query_text": "SELECT * FROM users WHERE email = :email",
                    "risk_level": "safe",
                    "risk_score": 5.0,
                    "vulnerability_type": None,
                    "is_parameterized": 1.0,
                    "uses_orm": 1.0,
                    "has_user_input": 1.0,
                    "ai_suggestion": None,
                    "safe_example": None,
                    "reference_url": None,
                    "is_fixed": 1.0,
                    "fix_priority": None,
                    "scanned_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                    "last_scanned": datetime.utcnow()
                    - timedelta(days=random.randint(0, 5)),
                },
                {
                    "query_hash": "m7n8b9v0c1x2",
                    "file_path": "app/services/team.py",
                    "line_number": 156,
                    "query_text": 'SELECT * FROM teams WHERE org_id = "{org_id}" AND status = "active"',
                    "risk_level": "high",
                    "risk_score": 80.0,
                    "vulnerability_type": "concat",
                    "is_parameterized": 0.0,
                    "uses_orm": 0.0,
                    "has_user_input": 1.0,
                    "ai_suggestion": "Use parameterized query with proper ORM methods",
                    "safe_example": "session.query(Team).filter(Team.org_id == org_id, Team.status == 'active').all()",
                    "reference_url": None,
                    "is_fixed": 0.0,
                    "fix_priority": "high",
                    "scanned_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                    "last_scanned": datetime.utcnow()
                    - timedelta(days=random.randint(0, 5)),
                },
                {
                    "query_hash": "l3k4j5h6g7f8",
                    "file_path": "app/crud/crud_assessment.py",
                    "line_number": 89,
                    "query_text": "SELECT * FROM responses WHERE user_id = :user_id AND created_at > :since",
                    "risk_level": "safe",
                    "risk_score": 8.0,
                    "vulnerability_type": None,
                    "is_parameterized": 1.0,
                    "uses_orm": 1.0,
                    "has_user_input": 1.0,
                    "ai_suggestion": None,
                    "safe_example": None,
                    "reference_url": None,
                    "is_fixed": 1.0,
                    "fix_priority": None,
                    "scanned_at": datetime.utcnow()
                    - timedelta(days=random.randint(1, 30)),
                    "last_scanned": datetime.utcnow()
                    - timedelta(days=random.randint(0, 5)),
                },
            ]

            # Insert queries
            query_ids = []
            for q in queries:
                result = await db.execute(
                    text(
                        """
                    INSERT INTO sql_queries (
                        query_hash, file_path, line_number, query_text, risk_level, risk_score,
                        vulnerability_type, is_parameterized, uses_orm, has_user_input,
                        ai_suggestion, safe_example, reference_url, is_fixed, fix_priority,
                        scanned_at, last_scanned
                    ) VALUES (
                        :query_hash, :file_path, :line_number, :query_text, :risk_level, :risk_score,
                        :vulnerability_type, :is_parameterized, :uses_orm, :has_user_input,
                        :ai_suggestion, :safe_example, :reference_url, :is_fixed, :fix_priority,
                        :scanned_at, :last_scanned
                    )
                    ON CONFLICT (query_hash) DO NOTHING
                    RETURNING id
                """
                    ),
                    q,
                )
                query_id = result.scalar_one_or_none()
                if query_id:
                    query_ids.append((query_id, q))

            # Insert vulnerabilities for critical/high risk queries
            for query_id, q in query_ids:
                if q["risk_level"] in ["critical", "high"]:
                    await db.execute(
                        text(
                            """
                        INSERT INTO sql_vulnerabilities (
                            query_id, vulnerability_type, severity, description,
                            injection_point, exploit_example, impact_description,
                            remediation_steps, code_fix, verified_safe, discovered_at
                        ) VALUES (
                            :query_id, :vulnerability_type, :severity, :description,
                            :injection_point, :exploit_example, :impact_description,
                            :remediation_steps, :code_fix, :verified_safe, :discovered_at
                        )
                    """
                        ),
                        {
                            "query_id": query_id,
                            "vulnerability_type": q["vulnerability_type"],
                            "severity": q["risk_level"],
                            "description": f"SQL injection vulnerability via {q['vulnerability_type']} method",
                            "injection_point": f"{q['file_path']}:{q['line_number']}",
                            "exploit_example": f"' OR 1=1 --",
                            "impact_description": "Attackers can bypass authentication, access unauthorized data, or modify database content.",
                            "remediation_steps": "1. Use parameterized queries or ORM\n2. Validate and sanitize user input\n3. Implement principle of least privilege for database connections",
                            "code_fix": q["safe_example"],
                            "verified_safe": 0.0,
                            "discovered_at": datetime.utcnow()
                            - timedelta(days=random.randint(1, 30)),
                        },
                    )

            # Create scan reports for the last 14 days
            base_date = datetime.utcnow() - timedelta(days=14)
            for i in range(14):
                scan_date = base_date + timedelta(days=i)
                total_queries = 50 + random.randint(-5, 10)
                safe_count = int(total_queries * random.uniform(0.6, 0.8))
                vuln_count = total_queries - safe_count
                critical = int(vuln_count * random.uniform(0.1, 0.2))
                high = int(vuln_count * random.uniform(0.2, 0.3))
                medium = int(vuln_count * random.uniform(0.3, 0.4))
                low = vuln_count - critical - high - medium

                await db.execute(
                    text(
                        """
                    INSERT INTO sql_scan_reports (
                        scan_date, total_queries_scanned, total_vulnerabilities,
                        critical_vulnerabilities, high_vulnerabilities, medium_vulnerabilities, low_vulnerabilities,
                        safe_queries, parameterized_queries, orm_queries,
                        vulnerability_breakdown, ai_summary, ai_insights, overall_risk_score,
                        risk_trend, vulnerabilities_trend
                    ) VALUES (
                        :scan_date, :total_queries_scanned, :total_vulnerabilities,
                        :critical_vulnerabilities, :high_vulnerabilities, :medium_vulnerabilities, :low_vulnerabilities,
                        :safe_queries, :parameterized_queries, :orm_queries,
                        :vulnerability_breakdown, :ai_summary, :ai_insights, :overall_risk_score,
                        :risk_trend, :vulnerabilities_trend
                    )
                """
                    ),
                    {
                        "scan_date": scan_date,
                        "total_queries_scanned": total_queries,
                        "total_vulnerabilities": vuln_count,
                        "critical_vulnerabilities": critical,
                        "high_vulnerabilities": high,
                        "medium_vulnerabilities": medium,
                        "low_vulnerabilities": low,
                        "safe_queries": safe_count,
                        "parameterized_queries": int(
                            total_queries * random.uniform(0.5, 0.7)
                        ),
                        "orm_queries": int(total_queries * random.uniform(0.4, 0.6)),
                        "vulnerability_breakdown": json.dumps(
                            {
                                "concat": high + critical,
                                "format": medium,
                                "fstring": low,
                            }
                        ),
                        "ai_summary": f"SQL security scan completed. Found {vuln_count} potential issues.",
                        "ai_insights": json.dumps(
                            {
                                "highlights": [
                                    f"{safe_count} queries using safe practices",
                                    f"{int(total_queries * 0.6)} queries using parameterized queries",
                                ],
                                "concerns": [
                                    f"{critical} critical vulnerabilities detected",
                                    f"{high} high-risk queries need immediate attention",
                                ],
                                "recommendations": [
                                    "Prioritize fixing critical vulnerabilities",
                                    "Enable SQL query linting in CI/CD",
                                    "Provide developer training on secure SQL practices",
                                ],
                            }
                        ),
                        "overall_risk_score": round(
                            vuln_count / total_queries * 100, 2
                        ),
                        "risk_trend": random.choice(
                            ["improving", "stable", "declining"]
                        ),
                        "vulnerabilities_trend": random.choice(
                            ["decreasing", "stable", "increasing"]
                        ),
                    },
                )

            await db.commit()
            print("✓ SQL Audit data seeded successfully")
            print(f"  - {len(query_ids)} SQL queries")
            print("  - Scan reports for last 14 days")

        except Exception as e:
            await db.rollback()
            print(f"✗ Error seeding data: {e}")
            raise
        finally:
            await db.close()
        break


if __name__ == "__main__":
    print("Seeding SQL Audit data...")
    asyncio.run(seed_sql_audit_data())
    print("\nDone!")
