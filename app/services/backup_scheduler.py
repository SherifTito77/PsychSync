# app/services/backup_scheduler.py
"""
Automated Backup Scheduler
- Cron-based backup scheduling
- Multiple backup schedules
- Backup policy management
- Schedule monitoring and alerts
- Backup history and reporting
- Configuration management
"""

import asyncio
import aiofiles
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database_backup_service import (
    DatabaseBackupService,
    BackupType,
    BackupConfig,
    BackupMetadata,
    get_backup_service
)
from app.core.path_utils import sanitize_path, safe_filename
from app.core.background_jobs import get_background_worker

logger = logging.getLogger(__name__)


class ScheduleStatus(Enum):
    """Backup schedule status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class BackupSchedule:
    """Backup schedule configuration"""
    schedule_id: str
    name: str
    backup_type: BackupType
    cron_expression: str
    is_active: bool = True
    description: Optional[str] = None
    retention_days: int = 30
    backup_config: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    status: ScheduleStatus = ScheduleStatus.ACTIVE

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def calculate_next_run(self) -> datetime:
        """Calculate next scheduled run time"""
        try:
            cron = croniter(self.cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression '{self.cron_expression}': {str(e)}")
            return None

    def is_due(self) -> bool:
        """Check if backup is due to run"""
        if not self.is_active or self.status != ScheduleStatus.ACTIVE:
            return False

        if self.next_run is None:
            return False

        return datetime.utcnow() >= self.next_run

    def update_run_stats(self, success: bool, error_message: Optional[str] = None):
        """Update run statistics"""
        self.last_run = datetime.utcnow()
        self.run_count += 1
        self.next_run = self.calculate_next_run()
        self.updated_at = datetime.utcnow()

        if success:
            self.success_count += 1
            self.last_error = None
            if self.status == ScheduleStatus.ERROR:
                self.status = ScheduleStatus.ACTIVE
        else:
            self.error_count += 1
            self.last_error = error_message
            self.status = ScheduleStatus.ERROR


class BackupScheduler:
    """Automated backup scheduler service"""

    def __init__(self, schedules_dir: str = "backup_schedules"):
        self.schedules_dir = Path(schedules_dir)
        self.schedules_dir.mkdir(parents=True, exist_ok=True)
        self.schedules: Dict[str, BackupSchedule] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.background_worker = get_background_worker()

    async def start(self):
        """Start the backup scheduler"""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return

        logger.info("Starting backup scheduler")
        self.running = True

        # Load existing schedules
        await self.load_schedules()

        # Start scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

        logger.info(f"Backup scheduler started with {len(self.schedules)} schedules")

    async def stop(self):
        """Stop the backup scheduler"""
        if not self.running:
            return

        logger.info("Stopping backup scheduler")
        self.running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # Save schedules
        await self.save_schedules()

        logger.info("Backup scheduler stopped")

    async def add_schedule(self, schedule: BackupSchedule) -> BackupSchedule:
        """
        Add a new backup schedule

        Args:
            schedule: Backup schedule configuration

        Returns:
            BackupSchedule: Added schedule
        """
        # Validate cron expression
        if not schedule.calculate_next_run():
            raise ValueError(f"Invalid cron expression: {schedule.cron_expression}")

        # Save schedule
        self.schedules[schedule.schedule_id] = schedule
        await self.save_schedule(schedule)

        logger.info(f"Added backup schedule '{schedule.name}' ({schedule.schedule_id})")
        return schedule

    async def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> Optional[BackupSchedule]:
        """
        Update an existing backup schedule

        Args:
            schedule_id: Schedule ID to update
            updates: Updates to apply

        Returns:
            BackupSchedule: Updated schedule or None if not found
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)

        # Update timestamps and recalculate next run
        schedule.updated_at = datetime.utcnow()
        schedule.next_run = schedule.calculate_next_run()

        # Save updated schedule
        await self.save_schedule(schedule)

        logger.info(f"Updated backup schedule '{schedule.name}' ({schedule_id})")
        return schedule

    async def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a backup schedule

        Args:
            schedule_id: Schedule ID to remove

        Returns:
            bool: True if schedule was removed
        """
        schedule = self.schedules.pop(schedule_id, None)
        if not schedule:
            return False

        # Remove schedule file
        schedule_file = self.schedules_dir / f"{schedule_id}.json"
        if schedule_file.exists():
            schedule_file.unlink()

        logger.info(f"Removed backup schedule '{schedule.name}' ({schedule_id})")
        return True

    async def get_schedule(self, schedule_id: str) -> Optional[BackupSchedule]:
        """
        Get a backup schedule by ID

        Args:
            schedule_id: Schedule ID

        Returns:
            BackupSchedule: Schedule or None if not found
        """
        return self.schedules.get(schedule_id)

    async def list_schedules(self, status: Optional[ScheduleStatus] = None) -> List[BackupSchedule]:
        """
        List backup schedules

        Args:
            status: Filter by status (optional)

        Returns:
            List[BackupSchedule]: List of schedules
        """
        schedules = list(self.schedules.values())

        if status:
            schedules = [s for s in schedules if s.status == status]

        # Sort by next run time
        schedules.sort(key=lambda x: x.next_run or datetime.max)

        return schedules

    async def pause_schedule(self, schedule_id: str) -> bool:
        """
        Pause a backup schedule

        Args:
            schedule_id: Schedule ID to pause

        Returns:
            bool: True if schedule was paused
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.is_active = False
        schedule.status = ScheduleStatus.PAUSED
        schedule.updated_at = datetime.utcnow()
        await self.save_schedule(schedule)

        logger.info(f"Paused backup schedule '{schedule.name}' ({schedule_id})")
        return True

    async def resume_schedule(self, schedule_id: str) -> bool:
        """
        Resume a paused backup schedule

        Args:
            schedule_id: Schedule ID to resume

        Returns:
            bool: True if schedule was resumed
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return False

        schedule.is_active = True
        schedule.status = ScheduleStatus.ACTIVE
        schedule.next_run = schedule.calculate_next_run()
        schedule.updated_at = datetime.utcnow()
        await self.save_schedule(schedule)

        logger.info(f"Resumed backup schedule '{schedule.name}' ({schedule_id})")
        return True

    async def run_schedule_now(self, schedule_id: str) -> bool:
        """
        Run a backup schedule immediately

        Args:
            schedule_id: Schedule ID to run

        Returns:
            bool: True if backup was started
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return False

        # Enqueue backup task
        task_id = await self.background_worker.enqueue_task(
            "execute_scheduled_backup",
            schedule_id=schedule_id,
            backup_type=schedule.backup_type.value,
            config=schedule.backup_config or {}
        )

        logger.info(f"Manually triggered backup schedule '{schedule.name}' ({schedule_id}) - Task: {task_id}")
        return True

    async def get_schedule_statistics(self) -> Dict[str, Any]:
        """
        Get scheduler statistics

        Returns:
            Dict[str, Any]: Scheduler statistics
        """
        schedules = list(self.schedules.values())

        stats = {
            "total_schedules": len(schedules),
            "active_schedules": len([s for s in schedules if s.status == ScheduleStatus.ACTIVE]),
            "paused_schedules": len([s for s in schedules if s.status == ScheduleStatus.PAUSED]),
            "error_schedules": len([s for s in schedules if s.status == ScheduleStatus.ERROR]),
            "total_runs": sum(s.run_count for s in schedules),
            "successful_runs": sum(s.success_count for s in schedules),
            "failed_runs": sum(s.error_count for s in schedules),
            "next_due_schedules": []
        }

        # Calculate success rate
        total_runs = stats["total_runs"]
        if total_runs > 0:
            stats["success_rate"] = (stats["successful_runs"] / total_runs) * 100
        else:
            stats["success_rate"] = 0

        # Get next due schedules (next 24 hours)
        next_24h = datetime.utcnow() + timedelta(hours=24)
        stats["next_due_schedules"] = [
            {
                "schedule_id": s.schedule_id,
                "name": s.name,
                "next_run": s.next_run.isoformat() if s.next_run else None,
                "backup_type": s.backup_type.value
            }
            for s in schedules
            if s.next_run and s.next_run <= next_24h and s.status == ScheduleStatus.ACTIVE
        ]

        return stats

    async def load_schedules(self):
        """Load schedules from disk"""
        for schedule_file in self.schedules_dir.glob("*.json"):
            try:
                with open(schedule_file, 'r') as f:
                    data = json.load(f)

                # Convert string fields back to proper types
                data['backup_type'] = BackupType(data['backup_type'])
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                if data.get('last_run'):
                    data['last_run'] = datetime.fromisoformat(data['last_run'])
                if data.get('next_run'):
                    data['next_run'] = datetime.fromisoformat(data['next_run'])

                schedule = BackupSchedule(**data)
                self.schedules[schedule.schedule_id] = schedule

            except Exception as e:
                logger.error(f"Failed to load schedule from {schedule_file}: {str(e)}")
                continue

        logger.info(f"Loaded {len(self.schedules)} backup schedules")

    async def save_schedule(self, schedule: BackupSchedule):
        """Save a schedule to disk"""
        schedule_file = self.schedules_dir / f"{schedule.schedule_id}.json"

        # Convert to dict and handle datetime serialization
        data = asdict(schedule)
        data['backup_type'] = schedule.backup_type.value
        data['created_at'] = schedule.created_at.isoformat()
        data['updated_at'] = schedule.updated_at.isoformat()
        if schedule.last_run:
            data['last_run'] = schedule.last_run.isoformat()
        if schedule.next_run:
            data['next_run'] = schedule.next_run.isoformat()

        with open(schedule_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def save_schedules(self):
        """Save all schedules to disk"""
        for schedule in self.schedules.values():
            await self.save_schedule(schedule)

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Backup scheduler loop started")

        while self.running:
            try:
                current_time = datetime.utcnow()

                # Check for due schedules
                due_schedules = [
                    schedule for schedule in self.schedules.values()
                    if schedule.is_due()
                ]

                if due_schedules:
                    logger.info(f"Found {len(due_schedules)} due backup schedules")

                    for schedule in due_schedules:
                        try:
                            # Enqueue backup task
                            task_id = await self.background_worker.enqueue_task(
                                "execute_scheduled_backup",
                                schedule_id=schedule.schedule_id,
                                backup_type=schedule.backup_type.value,
                                config=schedule.backup_config or {}
                            )

                            logger.info(f"Enqueued scheduled backup '{schedule.name}' - Task: {task_id}")

                        except Exception as e:
                            logger.error(f"Failed to enqueue scheduled backup '{schedule.name}': {str(e)}")
                            schedule.update_run_stats(False, str(e))
                            await self.save_schedule(schedule)

                # Sleep for 1 minute before next check
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)

        logger.info("Backup scheduler loop ended")


# Global scheduler instance
_backup_scheduler: Optional[BackupScheduler] = None


def get_backup_scheduler() -> BackupScheduler:
    """Get global backup scheduler instance"""
    global _backup_scheduler
    if _backup_scheduler is None:
        _backup_scheduler = BackupScheduler()
    return _backup_scheduler


# Task for executing scheduled backups
@task("execute_scheduled_backup")
async def execute_scheduled_backup_task(
    schedule_id: str,
    backup_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Background task for executing scheduled backups"""
    scheduler = get_backup_scheduler()
    schedule = await scheduler.get_schedule(schedule_id)

    if not schedule:
        return {
            "success": False,
            "schedule_id": schedule_id,
            "error": "Schedule not found"
        }

    try:
        # Create backup service
        backup_config = BackupConfig(**config) if config else None
        backup_service = get_backup_service()

        # Execute backup
        backup_metadata = await backup_service.create_backup(BackupType(backup_type))

        # Update schedule statistics
        schedule.update_run_stats(True)
        await scheduler.save_schedule(schedule)

        logger.info(f"Scheduled backup '{schedule.name}' completed successfully")

        return {
            "success": True,
            "schedule_id": schedule_id,
            "backup_id": backup_metadata.backup_id,
            "backup_type": backup_type
        }

    except Exception as e:
        logger.error(f"Scheduled backup '{schedule.name}' failed: {str(e)}")

        # Update schedule statistics
        schedule.update_run_stats(False, str(e))
        await scheduler.save_schedule(schedule)

        return {
            "success": False,
            "schedule_id": schedule_id,
            "error": str(e)
        }
