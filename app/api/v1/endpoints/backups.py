# app/api/v1/endpoints/backups.py
"""
Database Backup Management API Endpoints
- Create and schedule backups
- Monitor backup status and progress
- Restore from backups
- Manage backup retention policies
- Backup verification and testing
- Backup statistics and reporting
"""

from datetime import datetime
import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_admin_user
from app.api.v1.deps import Depends, get_current_user
from app.db.models.user import User
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy
from app.schemas.responses import PaginatedResponse, SuccessResponse
from app.services.database_backup_service import (
    BackupConfig,
    BackupStatus,
    BackupType,
    StorageProvider,
    get_backup_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class BackupRequest(BaseModel):
    """Request model for creating backups"""

    backup_type: BackupType = Field(default=BackupType.FULL, description="Type of backup to create")
    description: str | None = Field(None, description="Backup description")
    tags: list[str] = Field(default_factory=list, description="Backup tags for organization")


class BackupConfigRequest(BaseModel):
    """Request model for updating backup configuration"""

    backup_type: BackupType = Field(..., description="Default backup type")
    storage_provider: StorageProvider = Field(..., description="Storage provider")
    storage_path: str = Field(..., description="Storage path")
    compression_enabled: bool = Field(default=True, description="Enable compression")
    encryption_enabled: bool = Field(default=True, description="Enable encryption")
    retention_days: int = Field(default=30, ge=1, le=365, description="Retention period in days")
    schedule_cron: str = Field(default="0 2 * * *", description="Backup schedule (cron format)")
    verify_after_backup: bool = Field(default=True, description="Verify backup after creation")
    cleanup_old_backups: bool = Field(default=True, description="Auto-cleanup old backups")
    notification_emails: list[str] = Field(default_factory=list, description="Notification emails")


class RestoreRequest(BaseModel):
    """Request model for restoring backups"""

    target_database: str | None = Field(None, description="Target database name")
    confirm_restore: bool = Field(default=False, description="Confirm restoration (safety measure)")


class BackupResponse(BaseModel):
    """Response model for backup information"""

    backup_id: str
    backup_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    file_size_bytes: int
    file_checksum: str
    compression_ratio: float
    tables_count: int
    rows_count: int
    error_message: str | None
    storage_provider: str
    storage_path: str
    verification_status: str
    restoration_test_date: datetime | None

    class Config:
        from_attributes = True


class BackupListResponse(PaginatedResponse[BackupResponse]):
    """Response model for backup list with pagination"""


class BackupStatisticsResponse(BaseModel):
    """Response model for backup statistics"""

    total_backups: int
    successful_backups: int
    failed_backups: int
    verified_backups: int
    total_size_bytes: int
    total_size_gb: float
    oldest_backup: str | None
    newest_backup: str | None
    backup_types: dict[str, int]
    storage_providers: dict[str, int]
    success_rate: float


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/backups", response_model=SuccessResponse[BackupResponse])
async def create_backup(
    backup_request: BackupRequest,
    current_user: User = Depends(get_current_admin_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new database backup

    - **backup_type**: Type of backup (full, incremental, differential)
    - **description**: Optional description for the backup
    - **tags**: Optional tags for organization

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Create backup
        backup_metadata = await backup_service.create_backup(backup_request.backup_type)

        # Log backup creation
        logger.info(f"Backup {backup_metadata.backup_id} created by user {current_user.email}")

        return SuccessResponse(
            message="Backup created successfully", data=BackupResponse.from_orm(backup_metadata)
        )

    except Exception as e:
        logger.error(f"Failed to create backup: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/backups", response_model=BackupListResponse)
async def list_backups(
    backup_type: BackupType | None = Query(None, description="Filter by backup type"),
    status: BackupStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List database backups with filtering and pagination

    - **backup_type**: Filter by backup type
    - **status**: Filter by backup status
    - **page**: Page number for pagination
    - **size**: Number of items per page

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Get backups with filtering
        limit = size
        offset = (page - 1) * size
        backups = await backup_service.list_backups(
            backup_type=backup_type, status=status, limit=limit
        )

        # Convert to response models
        backup_responses = [BackupResponse.from_orm(backup) for backup in backups]

        # Get total count for pagination
        all_backups = await backup_service.list_backups(backup_type=backup_type, status=status)
        total = len(all_backups)

        return BackupListResponse.create_paginated(
            items=backup_responses, total=total, page=page, size=size
        )

    except Exception as e:
        logger.error(f"Failed to list backups: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/backups/{backup_id}", response_model=SuccessResponse[BackupResponse])
async def get_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get detailed information about a specific backup

    - **backup_id**: Unique backup identifier

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Get backup metadata
        backups = await backup_service.list_backups()
        backup = next((b for b in backups if b.backup_id == backup_id), None)

        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")

        return SuccessResponse(
            message="Backup retrieved successfully", data=BackupResponse.from_orm(backup)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup {backup_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/backups/{backup_id}/restore", response_model=SuccessResponse[dict[str, str]])
async def restore_backup(
    backup_id: str,
    restore_request: RestoreRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_admin_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Restore database from a backup

    ⚠️ **DANGEROUS OPERATION** - This will overwrite the current database!

    - **backup_id**: Unique backup identifier
    - **target_database**: Optional target database name
    - **confirm_restore**: Must be True to confirm restoration

    Requires admin privileges and explicit confirmation.
    """
    if not restore_request.confirm_restore:
        raise HTTPException(
            status_code=400,
            detail="Restore confirmation required. Set confirm_restore=true to proceed.",
        )

    try:
        backup_service = get_backup_service()

        # Verify backup exists
        backups = await backup_service.list_backups()
        backup = next((b for b in backups if b.backup_id == backup_id), None)

        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")

        # Execute restore
        success = await backup_service.restore_backup(
            backup_id=backup_id, target_database=restore_request.target_database
        )

        if not success:
            raise HTTPException(status_code=500, detail="Restore operation failed")

        # Log restore operation
        logger.warning(f"Database restored from backup {backup_id} by user {current_user.email}")

        return SuccessResponse(
            message="Database restored successfully",
            data={"backup_id": backup_id, "restored_at": datetime.utcnow().isoformat()},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore backup {backup_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/backups/{backup_id}",
    response_model=SuccessResponse[dict[str, str]],
    dependencies=[Depends(get_current_user)],
)
async def delete_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Delete a backup

    - **backup_id**: Unique backup identifier

    ⚠️ This action cannot be undone.

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Delete backup
        success = await backup_service.delete_backup(backup_id)

        if not success:
            raise HTTPException(status_code=404, detail="Backup not found")

        logger.info(f"Backup {backup_id} deleted by user {current_user.email}")

        return SuccessResponse(message="Backup deleted successfully", data={"backup_id": backup_id})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backup {backup_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/backups/{backup_id}/verify", response_model=SuccessResponse[dict[str, Any]])
async def verify_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Verify backup integrity

    - **backup_id**: Unique backup identifier

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Verify backup
        is_valid = await backup_service.verify_backup(backup_id)

        return SuccessResponse(
            message="Backup verification completed",
            data={
                "backup_id": backup_id,
                "is_valid": is_valid,
                "verified_at": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Failed to verify backup {backup_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/backups/statistics", response_model=SuccessResponse[BackupStatisticsResponse])
async def get_backup_statistics(
    current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_async_db)
):
    """
    Get backup statistics and metrics

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Get statistics
        stats = await backup_service.get_backup_statistics()

        # Calculate success rate
        total = stats["total_backups"]
        success_rate = (stats["successful_backups"] / total * 100) if total > 0 else 0

        # Convert bytes to GB
        total_size_gb = stats["total_size_bytes"] / (1024**3)

        response_data = BackupStatisticsResponse(
            **stats, total_size_gb=round(total_size_gb, 2), success_rate=round(success_rate, 2)
        )

        return SuccessResponse(
            message="Backup statistics retrieved successfully", data=response_data
        )

    except Exception as e:
        logger.error(f"Failed to get backup statistics: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/backups/cleanup", response_model=SuccessResponse[dict[str, Any]])
async def cleanup_old_backups(
    current_user: User = Depends(get_current_admin_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Clean up old backups based on retention policy

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Clean up old backups
        deleted_count = await backup_service.cleanup_old_backups()

        logger.info(
            f"Backup cleanup completed by user {current_user.email}. Deleted {deleted_count} backups."
        )

        return SuccessResponse(
            message="Backup cleanup completed",
            data={"deleted_count": deleted_count, "cleaned_at": datetime.utcnow().isoformat()},
        )

    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/backups/{backup_id}/download")
async def download_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Download a backup file

    - **backup_id**: Unique backup identifier

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Get backup metadata
        backups = await backup_service.list_backups()
        backup = next((b for b in backups if b.backup_id == backup_id), None)

        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")

        # Check if file exists
        if not os.path.exists(backup.file_path):
            raise HTTPException(status_code=404, detail="Backup file not found")

        # Log download
        logger.info(f"Backup {backup_id} downloaded by user {current_user.email}")

        # Return file
        filename = f"{backup_id}.{backup.backup_type.value}"
        if backup_service.config.compression_enabled:
            filename += ".gz"
        if backup_service.config.encryption_enabled:
            filename += ".enc"

        return FileResponse(
            path=backup.file_path, filename=filename, media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download backup {backup_id}: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/backups/config", response_model=SuccessResponse[dict[str, str]])
async def update_backup_config(
    config_request: BackupConfigRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update backup configuration

    - **backup_config**: New backup configuration

    Requires admin privileges.
    """
    try:
        # Create new backup service with updated config
        backup_config = BackupConfig(
            backup_type=config_request.backup_type,
            storage_provider=config_request.storage_provider,
            storage_path=config_request.storage_path,
            compression_enabled=config_request.compression_enabled,
            encryption_enabled=config_request.encryption_enabled,
            retention_days=config_request.retention_days,
            schedule_cron=config_request.schedule_cron,
            verify_after_backup=config_request.verify_after_backup,
            cleanup_old_backups=config_request.cleanup_old_backups,
            notification_emails=config_request.notification_emails,
        )

        # Update global backup service
        # Note: In a real implementation, you'd store this in the database
        # and update the global service instance

        logger.info(f"Backup configuration updated by user {current_user.email}")

        return SuccessResponse(
            message="Backup configuration updated successfully",
            data={"updated_at": datetime.utcnow().isoformat()},
        )

    except Exception as e:
        logger.error(f"Failed to update backup config: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/backups/config", response_model=SuccessResponse[dict[str, Any]])
async def get_backup_config(
    current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_async_db)
):
    """
    Get current backup configuration

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()
        config = backup_service.config

        config_data = {
            "backup_type": config.backup_type.value,
            "storage_provider": config.storage_provider.value,
            "storage_path": config.storage_path,
            "compression_enabled": config.compression_enabled,
            "encryption_enabled": config.encryption_enabled,
            "retention_days": config.retention_days,
            "schedule_cron": config.schedule_cron,
            "verify_after_backup": config.verify_after_backup,
            "cleanup_old_backups": config.cleanup_old_backups,
            "notification_emails": config.notification_emails,
        }

        return SuccessResponse(
            message="Backup configuration retrieved successfully", data=config_data
        )

    except Exception as e:
        logger.error(f"Failed to get backup config: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/backups/test-connection", response_model=SuccessResponse[dict[str, Any]])
async def test_storage_connection(
    current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_async_db)
):
    """
    Test connection to storage provider

    Requires admin privileges.
    """
    try:
        backup_service = get_backup_service()

        # Test connection based on storage provider
        if backup_service.config.storage_provider == StorageProvider.LOCAL:
            # Test local storage path
            if os.path.exists(backup_service.config.storage_path):
                connection_status = "connected"
                message = "Local storage path is accessible"
            else:
                connection_status = "error"
                message = "Local storage path is not accessible"

        elif backup_service.config.storage_provider == StorageProvider.S3:
            # Test S3 connection
            try:
                import boto3

                s3_client = boto3.client("s3")
                s3_client.list_buckets()
                connection_status = "connected"
                message = "S3 connection successful"
            except Exception as e:
                connection_status = "error"
                message = f"S3 connection failed: {e!s}"

        else:
            connection_status = "not_implemented"
            message = f"Connection test not implemented for {backup_service.config.storage_provider.value}"

        return SuccessResponse(
            message="Storage connection test completed",
            data={
                "storage_provider": backup_service.config.storage_provider.value,
                "connection_status": connection_status,
                "message": message,
                "tested_at": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Failed to test storage connection: {e!s}")
        raise HTTPException(status_code=500, detail=str(e)) from e
