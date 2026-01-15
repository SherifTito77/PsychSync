#!/usr/bin/env python3
"""
Seed Jira Integration Data

This script creates sample Jira issues, bug summaries, and sprint metrics
for testing the Product Operations Dashboard.

Usage:
    python -m app.scripts.seed_jira_data
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models.jira_integration import JiraIssue, JiraBugSummary, JiraSprintMetrics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample data
SAMPLE_BUGS = [
    {
        "issue_key": "PROJ-101",
        "summary": "Login button not responding on mobile devices",
        "description": "Users report that the login button is unresponsive on iOS Safari",
        "severity": "critical",
        "category": "UI",
        "assignee_name": "John Doe",
        "status": "Open",
    },
    {
        "issue_key": "PROJ-102",
        "summary": "Database connection timeout in production",
        "description": "Intermittent connection timeouts when load is high",
        "severity": "major",
        "category": "Backend",
        "assignee_name": "Jane Smith",
        "status": "In Progress",
    },
    {
        "issue_key": "PROJ-103",
        "summary": "Email notifications not sending for password resets",
        "description": "Users not receiving password reset emails",
        "severity": "major",
        "category": "Backend",
        "assignee_name": "Bob Johnson",
        "status": "Resolved",
    },
    {
        "issue_key": "PROJ-104",
        "summary": "Dashboard charts render incorrectly on Firefox",
        "description": "Charts overlap and display incorrectly on Firefox browser",
        "severity": "minor",
        "category": "UI",
        "assignee_name": "Alice Williams",
        "status": "Open",
    },
    {
        "issue_key": "PROJ-105",
        "summary": "SQL injection vulnerability in search endpoint",
        "description": "Search endpoint is vulnerable to SQL injection attacks",
        "severity": "critical",
        "category": "Security",
        "assignee_name": "John Doe",
        "status": "In Progress",
    },
    {
        "issue_key": "PROJ-106",
        "summary": "Export to CSV fails for large datasets",
        "description": "Export functionality times out for datasets > 10k rows",
        "severity": "minor",
        "category": "Backend",
        "assignee_name": "Jane Smith",
        "status": "Closed",
    },
    {
        "issue_key": "PROJ-107",
        "summary": "User profile image upload fails",
        "description": "Image upload returns 500 error",
        "severity": "major",
        "category": "UI",
        "assignee_name": "Bob Johnson",
        "status": "Open",
    },
    {
        "issue_key": "PROJ-108",
        "summary": "API rate limiting not working correctly",
        "description": "Rate limits are not being enforced properly",
        "severity": "major",
        "category": "Backend",
        "assignee_name": "Alice Williams",
        "status": "In Progress",
    },
]

SAMPLE_SPRINTS = [
    {
        "sprint_id": "sprint-42",
        "sprint_name": "Sprint 42 - Performance Optimization",
        "start_date": datetime.now() - timedelta(days=21),
        "end_date": datetime.now() - timedelta(days=7),
        "completed_at": datetime.now() - timedelta(days=7),
        "state": "closed",
        "committed_points": 50,
        "completed_points": 45,
        "total_issues": 12,
        "completed_issues": 10,
        "in_progress_issues": 0,
        "todo_issues": 2,
        "bugs_found": 5,
        "bugs_fixed": 4,
        "bugs_carried_over": 1,
        "team_velocity": 45,
        "velocity_change": -5.0,
        "sprint_goal": "Optimize database queries and improve API response times",
        "goal_achieved": 85.0,
    },
    {
        "sprint_id": "sprint-43",
        "sprint_name": "Sprint 43 - Feature Enhancements",
        "start_date": datetime.now() - timedelta(days=7),
        "end_date": datetime.now() + timedelta(days=7),
        "state": "active",
        "committed_points": 55,
        "completed_points": 30,
        "total_issues": 15,
        "completed_issues": 8,
        "in_progress_issues": 5,
        "todo_issues": 2,
        "bugs_found": 3,
        "bugs_fixed": 2,
        "bugs_carried_over": 0,
        "team_velocity": None,
        "velocity_change": None,
        "sprint_goal": "Implement dark mode and improve mobile responsiveness",
        "goal_achieved": None,
    },
]


async def seed_jira_issues(db: AsyncSession) -> list[JiraIssue]:
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
    """Create sample Jira issues (bugs and stories)"""

    issues = []
    project_key = "PROJ"
    project_name = "PsychSync"

    for bug_data in SAMPLE_BUGS:
        created_date = datetime.now() - timedelta(days=random.randint(1, 30))

        issue = JiraIssue(
            issue_key=bug_data["issue_key"],
            issue_type="Bug",
            summary=bug_data["summary"],
            description=bug_data["description"],
            status=bug_data["status"],
            priority=random.choice(["Highest", "High", "Medium", "Low"]),
            is_bug=1.0,
            severity=bug_data["severity"],
            category=bug_data["category"],
            assignee_name=bug_data["assignee_name"],
            created_at=created_date,
            updated_at=created_date + timedelta(hours=random.randint(1, 48)),
            resolved_at=created_date + timedelta(days=random.randint(1, 14)) if bug_data["status"] in ["Resolved", "Closed"] else None,
            time_estimate=random.randint(3600, 14400),  # 1-4 hours in seconds
            time_spent=random.randint(1800, 10800) if bug_data["status"] in ["Resolved", "Closed"] else None,
            sprint_id="sprint-42" if random.random() > 0.5 else "sprint-43",
            sprint_name="Sprint 42" if random.random() > 0.5 else "Sprint 43",
            project_key=project_key,
            project_name=project_name,
            labels=["bug", bug_data["category"].lower()],
            components=[bug_data["category"]],
            attachment_count=random.randint(0, 5),
            comment_count=random.randint(0, 10),
        )

        db.add(issue)
        await db.flush()

        issues.append(issue)

    logger.info(f"✅ Created {len(issues)} Jira issues")
    return issues


async def seed_bug_summaries(db: AsyncSession) -> list[JiraBugSummary]:
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
    """Create daily bug summaries for the past 14 days"""

    summaries = []
    project_key = "PROJ"

    for days_ago in range(14, 0, -1):
        summary_date = datetime.now() - timedelta(days=days_ago)

        # Vary the metrics
        new_bugs = random.randint(0, 4)
        resolved_bugs = random.randint(1, 5)
        total_bugs = 15 + random.randint(-3, 5)

        summary = JiraBugSummary(
            summary_date=summary_date,
            project_key=project_key,
            sprint_id="sprint-42" if days_ago > 7 else "sprint-43",
            total_bugs=total_bugs,
            new_bugs=new_bugs,
            resolved_bugs=resolved_bugs,
            reopened_bugs=random.randint(0, 2),
            critical_bugs=random.randint(1, 3),
            major_bugs=random.randint(3, 6),
            minor_bugs=random.randint(2, 5),
            avg_bug_age_hours=random.uniform(24, 120),
            oldest_bug_age_hours=random.uniform(120, 360),
            bugs_over_sla=random.randint(0, 4),
            bugs_by_category={
                "UI": random.randint(2, 5),
                "Backend": random.randint(3, 7),
                "Security": random.randint(0, 2),
            },
            ai_summary=f"Daily bug summary for {summary_date.strftime('%Y-%m-%d')}. Team resolved {resolved_bugs} bugs and identified {new_bugs} new issues.",
            ai_insights=[
                "Critical bugs are being resolved within SLA",
                "Backend category has highest bug count",
                "Bug resolution rate is stable",
            ],
            ai_recommendations=[
                "Schedule bug bash for UI issues",
                "Focus on reducing backend bug count",
            ],
            trend_new_bugs=random.choice(["increasing", "decreasing", "stable"]),
            trend_resolution_rate=random.choice(["increasing", "decreasing", "stable"]),
            assignee_workload={
                "John Doe": random.randint(2, 5),
                "Jane Smith": random.randint(2, 5),
                "Bob Johnson": random.randint(1, 4),
                "Alice Williams": random.randint(1, 4),
            },
            resolution_time_avg_hours=random.uniform(24, 72),
            generated_by="ai_agent",
        )

        db.add(summary)
        await db.flush()

        summaries.append(summary)

    logger.info(f"✅ Created {len(summaries)} bug summaries")
    return summaries


async def seed_sprint_metrics(db: AsyncSession) -> list[JiraSprintMetrics]:
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
    """Create sample sprint metrics"""

    sprints = []
    project_key = "PROJ"

    for sprint_data in SAMPLE_SPRINTS:
        sprint = JiraSprintMetrics(
            **sprint_data,
            project_key=project_key,
            ai_retrospective=f"Sprint {sprint_data['sprint_id']} completed successfully. Team velocity was {sprint_data.get('team_velocity', 'N/A')} points.",
            ai_improvements=[
                "Improve sprint planning accuracy",
                "Focus on reducing carry-over bugs",
                "Better time estimates for complex tasks",
            ],
        )

        db.add(sprint)
        await db.flush()

        sprints.append(sprint)

    logger.info(f"✅ Created {len(sprints)} sprint metrics")
    return sprints


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
    """Seed all Jira integration data"""

    # Create async engine
    engine = create_async_engine(settings.get_database_url(async_driver=True))

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        logger.info("🌱 Starting Jira integration data seeding...")

        # Seed issues
        issues = await seed_jira_issues(db)

        # Seed bug summaries
        summaries = await seed_bug_summaries(db)

        # Seed sprint metrics
        sprints = await seed_sprint_metrics(db)

        # Commit all changes
        await db.commit()

        logger.info("🎉 Jira integration data seeding completed successfully!")

        # Summary
        logger.info("\n📊 Seeding Summary:")
        logger.info(f"   - Jira issues: {len(issues)}")
        logger.info(f"   - Bug summaries: {len(summaries)}")
        logger.info(f"   - Sprint metrics: {len(sprints)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_all_data())
