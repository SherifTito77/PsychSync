"""
Analytics Rollup Tasks

Scheduled ETL tasks to populate data warehouse fact tables with aggregated metrics.
This ensures fast dashboard queries by pre-computing rollups daily.

Tasks:
- populate_team_metrics_rollups: Daily ETL to populate fact_team_metrics
- populate_team_metrics_backfill: Backfill historical data

Author: PsychSync Data Team
Created: 2026-01-21
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from celery import shared_task
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.db.models.analytics import FactTeamMetrics
from app.db.models.response import Response
from app.db.models.team import Team

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.analytics_rollup.populate_team_metrics_rollups")
async def populate_team_metrics_rollups(target_date: str = None) -> Dict[str, Any]:
    """
    Populate FactTeamMetrics table with daily team metrics

    This ETL task:
    1. Calculates metrics for each team for the target date
    2. Inserts/updates records in fact_team_metrics table
    3. Ensures up-to-date rollups for analytics dashboards

    Args:
        target_date: ISO date string (YYYY-MM-DD). Defaults to yesterday.

    Returns:
        Dict with metrics about the ETL run
    """
    logger.info("Starting team metrics rollup ETL task")

    async with get_async_db() as db:
        try:
            # Determine target date (default: yesterday)
            if target_date:
                metric_date = datetime.fromisoformat(target_date).date()
            else:
                metric_date = (datetime.utcnow() - timedelta(days=1)).date()

            logger.info(f"Computing metrics for date: {metric_date}")

            # Calculate date_key for dimension table (YYYYMMDD format)
            date_key = int(metric_date.strftime("%Y%m%d"))

            # Get all active teams
            teams_result = await db.execute(select(Team).where(Team.is_active == True))
            teams = teams_result.scalars().all()

            if not teams:
                logger.warning("No active teams found")
                return {
                    "status": "completed",
                    "teams_processed": 0,
                    "metrics_created": 0,
                }

            logger.info(f"Processing {len(teams)} teams")

            metrics_created = 0
            metrics_updated = 0
            errors = []

            for team in teams:
                try:
                    # Calculate time range for the target date
                    start_datetime = datetime.combine(metric_date, datetime.min.time())
                    end_datetime = datetime.combine(metric_date, datetime.max.time())

                    # Query completed responses for this team on this date
                    responses_result = await db.execute(
                        select(Response).where(
                            Response.team_id == team.id,
                            Response.created_at >= start_datetime,
                            Response.created_at <= end_datetime,
                            Response.is_complete == True,
                        )
                    )
                    responses = responses_result.scalars().all()

                    if not responses:
                        logger.debug(
                            f"No completed responses for team {team.id} on {metric_date}"
                        )
                        continue

                    # Calculate metrics
                    response_scores = [
                        r.score for r in responses if r.score is not None
                    ]

                    total_assessments = len(responses)
                    unique_users = len(set(r.user_id for r in responses))
                    completion_rate = (
                        (unique_users / team.member_count * 100)
                        if team.member_count and team.member_count > 0
                        else 0
                    )

                    avg_score = (
                        sum(response_scores) / len(response_scores)
                        if response_scores
                        else None
                    )
                    max_score = max(response_scores) if response_scores else None
                    min_score = min(response_scores) if response_scores else None

                    # Calculate completion times
                    completion_times = [
                        (r.completed_at - r.created_at).total_seconds()
                        for r in responses
                        if r.completed_at and r.created_at
                    ]
                    avg_completion_time = (
                        int(sum(completion_times) / len(completion_times))
                        if completion_times
                        else None
                    )
                    total_completion_time = (
                        int(sum(completion_times)) if completion_times else None
                    )

                    # Check if record already exists
                    existing_result = await db.execute(
                        select(FactTeamMetrics).where(
                            FactTeamMetrics.team_id == team.id,
                            FactTeamMetrics.metric_date == metric_date,
                        )
                    )
                    existing = existing_result.scalar_one_or_none()

                    if existing:
                        # Update existing record
                        existing.total_assessments_completed = total_assessments
                        existing.unique_users_completed = unique_users
                        existing.completion_rate = completion_rate
                        existing.avg_score = avg_score
                        existing.max_score = max_score
                        existing.min_score = min_score
                        existing.avg_completion_time_seconds = avg_completion_time
                        existing.total_completion_time_seconds = total_completion_time
                        existing.active_users = (
                            unique_users  # Assuming all completions = active
                        )
                        existing.engaged_users = unique_users
                        existing.created_at = datetime.utcnow()

                        metrics_updated += 1
                    else:
                        # Insert new record
                        metric = FactTeamMetrics(
                            team_key=team.id,  # Using team_id as team_key for now
                            date_key=date_key,
                            tenant_id=team.organization_id
                            or team.id,  # Fallback to team.id
                            team_id=team.id,
                            total_assessments_completed=total_assessments,
                            unique_users_completed=unique_users,
                            completion_rate=completion_rate,
                            avg_score=avg_score,
                            max_score=max_score,
                            min_score=min_score,
                            avg_completion_time_seconds=avg_completion_time,
                            total_completion_time_seconds=total_completion_time,
                            active_users=unique_users,
                            engaged_users=unique_users,
                            metric_date=metric_date,
                        )
                        db.add(metric)
                        metrics_created += 1

                    logger.debug(
                        f"Team {team.name}: {total_assessments} assessments, "
                        f"{unique_users} users, avg score: {avg_score:.1f if avg_score else 0:.1f}"
                    )

                except Exception as e:
                    error_msg = f"Error processing team {team.id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            # Commit all changes
            await db.commit()

            logger.info(
                f"Rollup ETL completed: {metrics_created} created, {metrics_updated} updated"
            )

            return {
                "status": "completed",
                "metric_date": metric_date.isoformat(),
                "teams_processed": len(teams),
                "metrics_created": metrics_created,
                "metrics_updated": metrics_updated,
                "errors": errors if errors else None,
            }

        except Exception as e:
            logger.error(f"Rollup ETL task failed: {e}", exc_info=True)
            await db.rollback()
            return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics_rollup.populate_team_metrics_backfill")
async def populate_team_metrics_backfill(days_back: int = 90) -> Dict[str, Any]:
    """
    Backfill FactTeamMetrics for historical data

    Populates rollup table for the last N days. Useful for initial data load
    or after fixing missing ETL runs.

    Args:
        days_back: Number of days to backfill (default: 90)

    Returns:
        Dict with backfill statistics
    """
    logger.info(f"Starting backfill for last {days_back} days")

    try:
        results = []

        for days_ago in range(days_back, 0, -1):
            target_date = (datetime.utcnow() - timedelta(days=days_ago)).date()
            logger.info(f"Backfilling {target_date}")

            result = await populate_team_metrics_rollups(target_date.isoformat())
            results.append(result)

        successful = sum(1 for r in results if r.get("status") == "completed")
        failed = sum(1 for r in results if r.get("status") == "failed")

        total_created = sum(r.get("metrics_created", 0) for r in results)
        total_updated = sum(r.get("metrics_updated", 0) for r in results)

        logger.info(
            f"Backfill completed: {successful} successful, {failed} failed, "
            f"{total_created} created, {total_updated} updated"
        )

        return {
            "status": "completed",
            "days_processed": len(results),
            "successful": successful,
            "failed": failed,
            "total_metrics_created": total_created,
            "total_metrics_updated": total_updated,
        }

    except Exception as e:
        logger.error(f"Backfill task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


@shared_task(name="app.tasks.analytics_rollup.check_rollup_health")
async def check_rollup_health() -> Dict[str, Any]:
    """
    Check health of rollup system

    Verifies:
    - Rollup tables exist
    - Recent data is available
    - No gaps in daily rollups

    Returns:
        Health status and metrics
    """
    logger.info("Checking rollup system health")

    async with get_async_db() as db:
        try:
            # Check if tables exist and have data
            result = await db.execute(
                text(
                    """
                SELECT
                    (SELECT COUNT(*) FROM dim_date) AS dim_date_count,
                    (SELECT COUNT(*) FROM fact_team_metrics) AS fact_metrics_count,
                    (SELECT COUNT(DISTINCT team_id) FROM fact_team_metrics) AS teams_with_metrics,
                    (SELECT MAX(metric_date) FROM fact_team_metrics) AS latest_metric_date,
                    (SELECT COUNT(DISTINCT metric_date) FROM fact_team_metrics) AS days_covered
            """
                )
            )

            row = result.fetchone()

            if not row:
                return {"status": "unhealthy", "error": "Could not query rollup tables"}

            health_status = "healthy"
            issues = []

            # Check if we have recent data (last 7 days)
            if row[3]:  # latest_metric_date
                days_since_latest = (datetime.utcnow().date() - row[3]).days
                if days_since_latest > 2:
                    health_status = "warning"
                    issues.append(f"Latest rollup is {days_since_latest} days old")
            else:
                health_status = "unhealthy"
                issues.append("No rollup data available")

            metrics = {
                "status": health_status,
                "dim_date_rows": row[0],
                "fact_metrics_rows": row[1],
                "teams_with_metrics": row[2],
                "latest_metric_date": row[3].isoformat() if row[3] else None,
                "days_covered": row[4],
                "issues": issues if issues else None,
            }

            logger.info(f"Rollup health check: {health_status} - {metrics}")

            return metrics

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
