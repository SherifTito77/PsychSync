#!/usr/bin/env python3
"""
Archive Old Data Script

Automated script for archiving data that exceeds retention thresholds.
Designed to run as a scheduled job (cron) for automated data archival.

Usage:
    python scripts/archive_old_data.py --policy assessment_responses
    python scripts/archive_old_data.py --all
    python scripts/archive_old_data.py --policy assessment_responses --dry-run

Author: PsychSync Data Governance Team
Version: 1.0
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_async_session
from app.services.data_retention_service import RETENTION_POLICIES, DataRetentionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/psychsync/archive_old_data.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def archive_policy(policy_name: str, dry_run: bool = False) -> dict:
    """
    Archive data for a specific retention policy

    Args:
        policy_name: Name of the retention policy
        dry_run: If True, only identify candidates without archiving

    Returns:
        Archive operation result
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Processing policy: {policy_name}")

    async with get_async_session() as db:
        service = DataRetentionService(db)

        # Check candidates first
        candidates = await service.check_archival_candidates(policy_name)
        logger.info(f"Found {len(candidates)} archival candidates for {policy_name}")

        if dry_run:
            logger.info(f"[DRY RUN] Would archive {len(candidates)} records")
            return {
                "policy": policy_name,
                "status": "dry_run",
                "candidates_found": len(candidates),
                "would_archive": len(candidates),
            }

        # Perform archival
        result = await service.archive_data(policy_name)

        if result["status"] == "success":
            logger.info(
                f"Successfully archived {result['records_archived']} records "
                f"in {result['duration_seconds']:.2f}s"
            )
        else:
            logger.error(f"Archival failed: {result.get('error', 'Unknown error')}")

        return result


async def archive_all_policies(dry_run: bool = False) -> dict:
    """
    Archive data for all retention policies

    Args:
        dry_run: If True, only identify candidates without archiving

    Returns:
        Overall operation result
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Processing all retention policies")

    results = {}
    total_archived = 0
    total_failed = 0

    for policy_name in RETENTION_POLICIES.keys():
        try:
            result = await archive_policy(policy_name, dry_run)
            results[policy_name] = result

            if result["status"] == "success":
                total_archived += result["records_archived"]
            elif result["status"] == "error":
                total_failed += 1

        except Exception as e:
            logger.error(f"Failed to process policy {policy_name}: {e}")
            results[policy_name] = {"status": "error", "error": str(e)}
            total_failed += 1

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_policies": len(RETENTION_POLICIES),
        "policies_succeeded": len(RETENTION_POLICIES) - total_failed,
        "policies_failed": total_failed,
        "total_records_archived": total_archived,
        "dry_run": dry_run,
        "results": results,
    }

    logger.info(
        f"Archival complete: {summary['policies_succeeded']}/{summary['total_policies']} "
        f"policies succeeded, {total_archived} records archived"
    )

    return summary


async def show_retention_stats():
    """Display current retention statistics"""
    logger.info("Fetching retention statistics...")

    async with get_async_session() as db:
        service = DataRetentionService(db)

        # Get statistics
        stats = await service.get_retention_statistics()
        logger.info("\n=== Retention Statistics ===")
        logger.info(f"Timestamp: {stats['timestamp']}")

        for key, value in sorted(stats.items()):
            if key != "timestamp":
                logger.info(f"  {key}: {value:,}")

        # Check compliance
        logger.info("\n=== GDPR Compliance Check ===")
        compliance = await service.check_gdpr_compliance()
        logger.info(f"Compliance Score: {compliance['compliance_score']}%")
        logger.info(f"Status: {compliance['status']}")

        if compliance["retention_violations"]:
            logger.info("Retention Violations:")
            for key, value in compliance["retention_violations"].items():
                if value > 0:
                    logger.warning(f"  {key}: {value:,} records")


async def list_policies():
    """List all available retention policies"""
    logger.info("=== Available Retention Policies ===")

    for policy_name, policy in RETENTION_POLICIES.items():
        logger.info(f"\n{policy_name}:")
        logger.info(f"  Source Table: {policy.source_table}")
        logger.info(
            f"  Retention Period: {policy.retention_period_days} days "
            f"({policy.retention_period_days // 365} years)"
        )
        logger.info(
            f"  Archive After: {policy.archive_after_days} days "
            f"({policy.archive_after_days // 30} months)"
        )
        logger.info(f"  Anonymize: {policy.anonymize_before_archive}")
        logger.info(f"  Target Storage: {policy.target_storage}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Archive old data according to retention policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive assessment responses
  python scripts/archive_old_data.py --policy assessment_responses

  # Archive all data types
  python scripts/archive_old_data.py --all

  # Dry run (don't actually archive)
  python scripts/archive_old_data.py --all --dry-run

  # Show retention statistics
  python scripts/archive_old_data.py --stats

  # List all policies
  python scripts/archive_old_data.py --list-policies
        """,
    )

    parser.add_argument(
        "--policy", type=str, help="Specific retention policy to process"
    )

    parser.add_argument(
        "--all", action="store_true", help="Process all retention policies"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Identify candidates without archiving"
    )

    parser.add_argument(
        "--stats", action="store_true", help="Show retention statistics"
    )

    parser.add_argument(
        "--list-policies", action="store_true", help="List all retention policies"
    )

    args = parser.parse_args()

    # Run async function
    try:
        if args.list_policies:
            asyncio.run(list_policies())

        elif args.stats:
            asyncio.run(show_retention_stats())

        elif args.all:
            result = asyncio.run(archive_all_policies(dry_run=args.dry_run))

            # Exit with error code if any policies failed
            if result["policies_failed"] > 0:
                sys.exit(1)

        elif args.policy:
            if args.policy not in RETENTION_POLICIES:
                logger.error(f"Unknown policy: {args.policy}")
                logger.error(
                    f"Available policies: {', '.join(RETENTION_POLICIES.keys())}"
                )
                sys.exit(1)

            result = asyncio.run(archive_policy(args.policy, dry_run=args.dry_run))

            if result["status"] == "error":
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(130)

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
