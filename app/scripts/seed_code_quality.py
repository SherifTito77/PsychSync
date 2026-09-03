#!/usr/bin/env python3
"""
Seed Code Quality Monitoring Data

This script creates sample code quality metrics, issues, and PR quality data
for testing the Product Operations Dashboard.

Usage:
    python -m app.scripts.seed_code_quality
"""

import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models.code_quality import CodeQualityIssue, CodeQualityMetric
from app.db.models.user import User

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample data
SAMPLE_ISSUES = [
    {
        "issue_type": "code_smell",
        "severity": "major",
        "category": "maintainability",
        "file_path": "app/services/user_service.py",
        "line_number": 45,
        "function_name": "get_user_profile",
        "title": "Function has high cyclomatic complexity",
        "description": "This function has a cyclomatic complexity of 15, which is above the recommended threshold of 10.",
        "rule_id": "S001",
        "effort": "30min",
    },
    {
        "issue_type": "vulnerability",
        "severity": "critical",
        "category": "security",
        "file_path": "app/api/v1/endpoints/auth.py",
        "line_number": 123,
        "function_name": "login",
        "title": "SQL injection vulnerability",
        "description": "User input is directly concatenated into SQL query without proper sanitization.",
        "rule_id": "S001",
        "effort": "2h",
    },
    {
        "issue_type": "bug",
        "severity": "major",
        "category": "reliability",
        "file_path": "app/crud/crud_assessment.py",
        "line_number": 78,
        "function_name": "create_assessment",
        "title": "Potential null pointer dereference",
        "description": "Variable 'user_id' may be None when passed to database query.",
        "rule_id": "B001",
        "effort": "1h",
    },
    {
        "issue_type": "code_smell",
        "severity": "minor",
        "category": "performance",
        "file_path": "app/services/analytics.py",
        "line_number": 234,
        "function_name": "calculate_metrics",
        "title": "Inefficient database query in loop",
        "description": "Database query executed inside loop. Consider batch processing.",
        "rule_id": "P001",
        "effort": "15min",
    },
    {
        "issue_type": "vulnerability",
        "severity": "major",
        "category": "security",
        "file_path": "app/utils/file_handler.py",
        "line_number": 56,
        "function_name": "upload_file",
        "title": "Unrestricted file upload",
        "description": "File type validation is bypassable. Content-Type header should not be trusted.",
        "rule_id": "S002",
        "effort": "1h",
    },
]

SAMPLE_PULL_REQUESTS = [
    {
        "pr_number": 142,
        "pr_title": "feat: Add dark mode support",
        "source_branch": "feature/dark-mode",
        "target_branch": "main",
        "author_name": "John Doe",
        "created_at": datetime.now() - timedelta(days=2),
        "merged_at": datetime.now() - timedelta(days=1),
        "files_changed": 12,
        "lines_added": 450,
        "lines_deleted": 120,
        "commits_count": 5,
        "overall_score": 85.0,
        "code_quality_score": 88.0,
        "test_coverage_score": 82.0,
        "documentation_score": 90.0,
        "risk_level": "low",
        "risk_factors": [],
        "complexity_increase": 2.3,
        "new_debt_added": 0.5,
        "tests_added": 15,
        "coverage_delta": 3.2,
        "review_count": 2,
        "review_time_hours": 4.5,
        "approval_count": 2,
        "is_merged": True,
    },
    {
        "pr_number": 141,
        "pr_title": "refactor: Restructure API endpoints",
        "source_branch": "refactor/api-structure",
        "target_branch": "main",
        "author_name": "Jane Smith",
        "created_at": datetime.now() - timedelta(days=4),
        "merged_at": datetime.now() - timedelta(days=3),
        "files_changed": 45,
        "lines_added": 1200,
        "lines_deleted": 800,
        "commits_count": 12,
        "overall_score": 72.0,
        "code_quality_score": 75.0,
        "test_coverage_score": 65.0,
        "documentation_score": 85.0,
        "risk_level": "medium",
        "risk_factors": ["large_change", "low_coverage"],
        "complexity_increase": 8.5,
        "new_debt_added": 2.1,
        "tests_added": 8,
        "coverage_delta": -2.5,
        "review_count": 3,
        "review_time_hours": 12.0,
        "approval_count": 2,
        "request_changes_count": 1,
        "critical_issues_count": 1,
        "major_issues_count": 3,
        "is_merged": True,
    },
    {
        "pr_number": 140,
        "pr_title": "fix: Resolve authentication timeout issue",
        "source_branch": "bugfix/auth-timeout",
        "target_branch": "main",
        "author_name": "Bob Johnson",
        "created_at": datetime.now() - timedelta(days=5),
        "files_changed": 3,
        "lines_added": 25,
        "lines_deleted": 10,
        "commits_count": 2,
        "overall_score": 92.0,
        "code_quality_score": 95.0,
        "test_coverage_score": 90.0,
        "documentation_score": 88.0,
        "risk_level": "low",
        "risk_factors": [],
        "complexity_increase": -1.2,
        "new_debt_added": 0.0,
        "tests_added": 5,
        "coverage_delta": 1.8,
        "review_count": 1,
        "review_time_hours": 1.5,
        "approval_count": 1,
        "is_merged": True,
    },
    {
        "pr_number": 139,
        "pr_title": "feat: Implement real-time notifications",
        "source_branch": "feature/notifications",
        "target_branch": "main",
        "author_name": "Alice Williams",
        "created_at": datetime.now() - timedelta(days=6),
        "merged_at": None,
        "closed_at": None,
        "files_changed": 28,
        "lines_added": 950,
        "lines_deleted": 150,
        "commits_count": 8,
        "overall_score": 68.0,
        "code_quality_score": 70.0,
        "test_coverage_score": 55.0,
        "documentation_score": 75.0,
        "risk_level": "high",
        "risk_factors": ["large_change", "low_coverage", "complex_code"],
        "complexity_increase": 12.3,
        "new_debt_added": 3.5,
        "duplication_added": 25,
        "tests_added": 3,
        "coverage_delta": -5.2,
        "review_count": 1,
        "review_time_hours": 8.0,
        "approval_count": 0,
        "request_changes_count": 2,
        "critical_issues_count": 2,
        "major_issues_count": 5,
        "minor_issues_count": 8,
        "is_merged": False,
    },
]


async def get_test_user(db: AsyncSession) -> User | None:
    """Retrieve resource(s).

    Args:
        db: Database session
        **kwargs: Filter criteria

    Returns:
        Resource object or list of resources

    Raises:
        NotFoundError: If resource doesn't exist
    """
    """Retrieve resource(s).

Args:
    db: Database session
    **kwargs: Filter criteria

Returns:
    Resource object or list of resources

Raises:
    NotFoundError: If resource doesn't exist
    """
    """Get a test user for PR associations"""
    result = await db.execute(select(User).where(User.email == "admin@psychsync.test"))
    return result.scalar_one_or_none()


async def seed_code_quality_metrics(db: AsyncSession) -> list[CodeQualityMetric]:
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
    """Create sample code quality metrics for the past 7 days"""

    metrics = []

    for days_ago in range(7, 0, -1):
        scan_date = datetime.now() - timedelta(days=days_ago)

        # Generate slightly varying metrics
        base_complexity = 8.5 + (random.random() * 2 - 1)
        base_coverage = 78.0 + (random.random() * 10 - 5)
        base_debt = 4.2 + (random.random() * 2 - 1)

        metric = CodeQualityMetric(
            scan_date=scan_date,
            module_name=None,  # Overall codebase
            cyclomatic_complexity=round(base_complexity, 2),
            cognitive_complexity=round(base_complexity * 1.3, 2),
            maintainability_index=round(75 + (random.random() * 15 - 7.5), 2),
            duplication_percentage=round(3.5 + (random.random() * 2 - 1), 2),
            duplicated_lines=random.randint(1200, 1600),
            total_lines=random.randint(42000, 43000),
            test_coverage_percentage=round(base_coverage, 2),
            test_count=random.randint(850, 900),
            code_violations_count=random.randint(45, 65),
            security_hotspots_count=random.randint(3, 8),
            bugs_count=random.randint(5, 12),
            technical_debt_ratio=round(base_debt, 2),
            estimated_remediation_cost=round(120 + random.random() * 40, 2),
            file_count=random.randint(320, 340),
            code_lines=random.randint(38000, 40000),
            comment_lines=random.randint(3500, 4000),
            blank_lines=random.randint(2000, 2500),
            language_metrics={
                "python": 28000,
                "typescript": 12000,
                "sql": 1500,
                "yaml": 500,
            },
            scan_duration_seconds=round(45 + random.random() * 20, 2),
            scanner_version="1.0.0",
        )

        # Calculate quality score and grade
        from app.crud.crud_code_quality import code_quality_metric as crud_metric

        metric.quality_score = crud_metric._calculate_quality_score(metric)
        metric.quality_grade = crud_metric._calculate_quality_grade(
            metric.quality_score
        )

        db.add(metric)
        await db.flush()

        metrics.append(metric)

    logger.info(f"✅ Created {len(metrics)} code quality metrics")
    return metrics


async def seed_code_quality_issues(
    db: AsyncSession, metric: CodeQualityMetric
) -> list[CodeQualityIssue]:
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
    """Create sample quality issues for a metric"""

    issues = []

    for issue_data in SAMPLE_ISSUES:
        issue = CodeQualityIssue(
            **issue_data,
            metric_id=metric.id,
            remediation_cost={
                "15min": 0.25,
                "30min": 0.5,
                "1h": 1.0,
                "2h": 2.0,
            }.get(issue_data["effort"], 1.0),
            ai_suggestion=f"Consider refactoring this code to improve {issue_data['category']}.",
            ai_confidence=round(0.75 + random.random() * 0.2, 2),
            auto_fixable=round(random.random() * 0.3, 2),
        )

        db.add(issue)
        await db.flush()

        issues.append(issue)

    logger.info(f"✅ Created {len(issues)} quality issues")
    return issues


async def seed_pull_requests(db: AsyncSession, author_id: str | None = None) -> int:
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
    """Create sample pull request quality records using raw SQL"""

    prs_created = 0

    for pr_data in SAMPLE_PULL_REQUESTS:
        # Build the SQL INSERT statement
        ai_recommendations = []
        merge_confidence = None

        if pr_data["risk_level"] in ["high", "medium"]:
            ai_recommendations = [
                {
                    "type": "coverage",
                    "message": "Test coverage is below 80%. Consider adding more tests.",
                    "priority": "high" if pr_data["risk_level"] == "high" else "medium",
                },
                {
                    "type": "review",
                    "message": "Consider additional code review due to complexity increase.",
                    "priority": "medium",
                },
            ]
            merge_confidence = round(0.6 + random.random() * 0.3, 2)

        # Convert dates to strings
        created_at = pr_data["created_at"].isoformat()
        merged_at = (
            pr_data.get("merged_at").isoformat() if pr_data.get("merged_at") else None
        )
        closed_at = (
            pr_data.get("closed_at").isoformat() if pr_data.get("closed_at") else None
        )

        # Use JSONB for arrays and objects
        import json

        insert_query = text(
            """
            INSERT INTO pull_request_quality (
                pr_number, pr_title, source_branch, target_branch, author_id, author_name,
                created_at, merged_at, closed_at, analyzed_at, files_changed, lines_added,
                lines_deleted, commits_count, overall_score, code_quality_score,
                test_coverage_score, documentation_score, risk_level, risk_factors,
                complexity_increase, new_debt_added, duplication_added, review_count,
                review_time_hours, approval_count, request_changes_count, tests_added,
                coverage_delta, critical_issues_count, major_issues_count, minor_issues_count,
                ai_recommendations, merge_confidence, repository, is_merged
            ) VALUES (
                :pr_number, :pr_title, :source_branch, :target_branch, :author_id, :author_name,
                :created_at, :merged_at, :closed_at, NOW(), :files_changed, :lines_added,
                :lines_deleted, :commits_count, :overall_score, :code_quality_score,
                :test_coverage_score, :documentation_score, :risk_level, :risk_factors,
                :complexity_increase, :new_debt_added, :duplication_added, :review_count,
                :review_time_hours, :approval_count, :request_changes_count, :tests_added,
                :coverage_delta, :critical_issues_count, :major_issues_count, :minor_issues_count,
                :ai_recommendations, :merge_confidence, :repository, :is_merged
            )
        """
        )

        try:
            await db.execute(
                insert_query,
                {
                    "pr_number": pr_data["pr_number"],
                    "pr_title": pr_data["pr_title"],
                    "source_branch": pr_data["source_branch"],
                    "target_branch": pr_data["target_branch"],
                    "author_id": author_id,
                    "author_name": pr_data["author_name"],
                    "created_at": created_at,
                    "merged_at": merged_at,
                    "closed_at": closed_at,
                    "files_changed": pr_data["files_changed"],
                    "lines_added": pr_data["lines_added"],
                    "lines_deleted": pr_data["lines_deleted"],
                    "commits_count": pr_data["commits_count"],
                    "overall_score": pr_data["overall_score"],
                    "code_quality_score": pr_data["code_quality_score"],
                    "test_coverage_score": pr_data["test_coverage_score"],
                    "documentation_score": pr_data["documentation_score"],
                    "risk_level": pr_data["risk_level"],
                    "risk_factors": json.dumps(pr_data["risk_factors"]),
                    "complexity_increase": pr_data["complexity_increase"],
                    "new_debt_added": pr_data["new_debt_added"],
                    "duplication_added": pr_data.get("duplication_added"),
                    "review_count": pr_data["review_count"],
                    "review_time_hours": pr_data["review_time_hours"],
                    "approval_count": pr_data["approval_count"],
                    "request_changes_count": pr_data.get("request_changes_count", 0),
                    "tests_added": pr_data["tests_added"],
                    "coverage_delta": pr_data["coverage_delta"],
                    "critical_issues_count": pr_data.get("critical_issues_count", 0),
                    "major_issues_count": pr_data.get("major_issues_count", 0),
                    "minor_issues_count": pr_data.get("minor_issues_count", 0),
                    "ai_recommendations": (
                        json.dumps(ai_recommendations) if ai_recommendations else None
                    ),
                    "merge_confidence": merge_confidence,
                    "repository": "psychsync",
                    "is_merged": 1.0 if pr_data["is_merged"] else 0.0,
                },
            )
            prs_created += 1
        except Exception as e:
            logger.warning(f"Could not create PR {pr_data['pr_number']}: {e}")

    logger.info(f"✅ Created {prs_created} pull request quality records")
    return prs_created


async def seed_all_data():
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
    """Seed all code quality monitoring data"""

    # Create async engine
    engine = create_async_engine(settings.get_database_url(async_driver=True))

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        logger.info("🌱 Starting code quality data seeding...")

        # Get test user for PR author
        test_user = await get_test_user(db)
        author_id = str(test_user.id) if test_user else None

        # Seed metrics
        metrics = await seed_code_quality_metrics(db)

        # Seed issues for the latest metric
        if metrics:
            latest_metric = max(metrics, key=lambda m: m.scan_date)
            await seed_code_quality_issues(db, latest_metric)

        # Seed pull requests
        await seed_pull_requests(db, author_id)

        # Commit all changes
        await db.commit()

        logger.info("🎉 Code quality data seeding completed successfully!")

        # Summary
        logger.info("\n📊 Seeding Summary:")
        logger.info(f"   - Code quality metrics: {len(metrics)}")
        logger.info(f"   - Quality issues: {len(SAMPLE_ISSUES)}")
        logger.info(f"   - Pull requests: {len(SAMPLE_PULL_REQUESTS)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_all_data())
