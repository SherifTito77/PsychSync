# app/services/churnScheduler.py
"""
Automated Churn Risk Scoring Scheduler

Periodically calculates churn risk scores for all users and executes intervention triggers.
This can be run as:
- A standalone scheduled job (cron)
- A background task in the application
- An AWS Lambda function or similar cloud scheduler

Run with: python -m app.services.churnScheduler
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.db.models.churn_prediction import ChurnRiskScore
from app.db.models.user import User
from app.services.churnPredictionService import ChurnTriggerService


class ChurnScoringScheduler:
    """Scheduler for automated churn risk scoring"""

    def __init__(self, batch_size: int = 100):
        """
        Initialize the scheduler

        Args:
            batch_size: Number of users to process per batch
        """
        self.batch_size = batch_size

    async def score_all_users(self):
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
        """
        Calculate churn risk scores for all active users.

        This method processes users in batches to avoid memory issues.
        """
        start_time = datetime.utcnow()
        users_processed = 0
        triggers_executed = 0

        print(f"🚀 Starting churn risk scoring at {start_time.isoformat()}")

        async with AsyncSessionLocal() as db:
            # Get all active users (created in last 90 days or with recent activity)
            # For now, we'll get all users - in production, you'd filter by activity
            result = await db.execute(
                select(User.id)
                .where(User.created_at >= datetime.utcnow() - timedelta(days=365))
                .order_by(User.created_at.desc())
            )
            user_ids = [row[0] for row in result]

            total_users = len(user_ids)
            print(f"📊 Found {total_users} users to score")

            # Process in batches
            for i in range(0, total_users, self.batch_size):
                batch = user_ids[i : i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (total_users + self.batch_size - 1) // self.batch_size

                print(
                    f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} users)"
                )

                batch_processed, batch_triggers = await self._process_batch(db, batch)

                users_processed += batch_processed
                triggers_executed += batch_triggers

                # Progress
                progress = (users_processed / total_users) * 100
                print(
                    f"   Progress: {progress:.1f}% ({users_processed}/{total_users} users)"
                )

        # Summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Scoring complete!")
        print(f"   Users processed: {users_processed}")
        print(f"   Triggers executed: {triggers_executed}")
        print(f"   Duration: {duration:.2f} seconds")
        print(
            f"   Average time per user: {duration / users_processed:.3f} seconds"
            if users_processed > 0
            else ""
        )

        return {
            "users_processed": users_processed,
            "triggers_executed": triggers_executed,
            "duration_seconds": duration,
        }

    async def _process_batch(self, db, user_ids: List[str]) -> tuple[int, int]:
        """Process data or request.

        Args:
            **kwargs: Input data

        Returns:
            Processed result
        """
        """Process data or request.

Args:
    **kwargs: Input data

Returns:
    Processed result
        """
        """
        Process a batch of users

        Args:
            db: Database session
            user_ids: List of user IDs to process

        Returns:
            Tuple of (users_processed, triggers_executed)
        """
        trigger_service = ChurnTriggerService(db)
        users_processed = 0
        triggers_executed = 0

        for user_id in user_ids:
            try:
                # Evaluate triggers (which also calculates and stores risk scores)
                executed = trigger_service.evaluate_and_execute_triggers(user_id)

                users_processed += 1
                triggers_executed += len(executed)

                # Log high-risk users
                if executed:
                    risk_data = trigger_service.calculator.calculate_user_risk(user_id)
                    if risk_data["overall_risk"] in ["critical", "high"]:
                        print(
                            f"   ⚠️  User {user_id}: {risk_data['overall_risk'].upper()} risk (score: {risk_data['overall_score']})"
                        )
                        print(
                            f"      Factors: {', '.join(risk_data['primary_risk_factors'])}"
                        )

            except Exception as e:
                print(f"   ❌ Error processing user {user_id}: {e}")
                continue

        return users_processed, triggers_executed

    async def score_recent_users(self, days: int = 7):
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
        """
        Score only users who were created or active in the last N days.

        This is useful for more frequent, incremental scoring runs.

        Args:
            days: Number of days to look back
        """
        start_time = datetime.utcnow()
        cutoff_date = start_time - timedelta(days=days)

        print(f"🚀 Starting incremental churn risk scoring (last {days} days)")

        async with AsyncSessionLocal() as db:
            # Get users created in the last N days
            result = await db.execute(
                select(User.id)
                .where(User.created_at >= cutoff_date)
                .order_by(User.created_at.desc())
            )
            user_ids = [row[0] for row in result]

            total_users = len(user_ids)
            print(f"📊 Found {total_users} recent users to score")

            if total_users == 0:
                print("ℹ️  No recent users found")
                return {
                    "users_processed": 0,
                    "triggers_executed": 0,
                    "duration_seconds": 0,
                }

            # Process all recent users
            _, triggers_executed = await self._process_batch(db, user_ids)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Incremental scoring complete!")
        print(f"   Users processed: {total_users}")
        print(f"   Triggers executed: {triggers_executed}")
        print(f"   Duration: {duration:.2f} seconds")

        return {
            "users_processed": total_users,
            "triggers_executed": triggers_executed,
            "duration_seconds": duration,
        }

    async def get_risk_summary(self) -> Dict[str, Any]:
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
        """
        Get a summary of churn risk scores across all users.

        Returns:
            Dictionary with risk distribution and high-risk users
        """
        async with AsyncSessionLocal() as db:
            # Count users by risk level
            result = await db.execute(
                select(
                    ChurnRiskScore.overall_risk, func.count(ChurnRiskScore.id)
                ).group_by(ChurnRiskScore.overall_risk)
            )
            risk_counts = {row[0]: row[1] for row in result}

            # Get critical/high risk users from last 7 days
            result = await db.execute(
                select(ChurnRiskScore)
                .where(
                    ChurnRiskScore.overall_risk.in_(["critical", "high"]),
                    ChurnRiskScore.calculated_at
                    >= datetime.utcnow() - timedelta(days=7),
                )
                .order_by(ChurnRiskScore.overall_score.desc())
                .limit(20)
            )
            high_risk_users = result.scalars().all()

            return {
                "risk_distribution": risk_counts,
                "high_risk_users": [
                    {
                        "user_id": str(u.user_id),
                        "risk_level": u.overall_risk,
                        "score": u.overall_score,
                        "primary_factors": u.primary_risk_factors,
                    }
                    for u in high_risk_users
                ],
                "total_scored": sum(risk_counts.values()),
            }


async def main():
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
    """Main entry point for running the scheduler"""
    import argparse

    parser = argparse.ArgumentParser(description="Churn Risk Scoring Scheduler")
    parser.add_argument(
        "--mode",
        choices=["all", "recent", "summary"],
        default="all",
        help="Scoring mode: all users, recent users, or summary only",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for 'recent' mode",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of users to process per batch",
    )

    args = parser.parse_args()

    scheduler = ChurnScoringScheduler(batch_size=args.batch_size)

    if args.mode == "all":
        await scheduler.score_all_users()
    elif args.mode == "recent":
        await scheduler.score_recent_users(days=args.days)
    elif args.mode == "summary":
        summary = await scheduler.get_risk_summary()
        print("\n📊 Churn Risk Summary")
        print(f"   Total users scored: {summary['total_scored']}")
        print(f"   Risk distribution:")
        for risk, count in summary["risk_distribution"].items():
            print(f"      {risk}: {count}")
        print(f"\n   High-risk users (last 7 days):")
        for user in summary["high_risk_users"]:
            print(
                f"      {user['user_id']}: {user['risk_level'].upper()} (score: {user['score']})"
            )


if __name__ == "__main__":
    asyncio.run(main())
