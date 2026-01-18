# app/api/v1/endpoints/health.py
"""
Enhanced Health Check and Monitoring Endpoints
Provides comprehensive system health monitoring with metrics
"""

from datetime import datetime, timedelta
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.core.async_cache import cache_get, cache_set
from app.core.cache_strategy import intelligent_cache
from app.core.config import settings
from app.core.responses import APIResponse, get_request_id
from app.core.structured_logging import EventType, get_logger
from app.db.models.user import User

router = APIRouter()
logger = get_logger(__name__)

# **Fixed Uptime Calculation:** Store application start time at module load
_APP_START_TIME = time.time()


@router.get("/health/public", summary="Public Health Check")
async def public_health_check(request: Request):
    """
    Public health check endpoint for load balancers and monitoring
    Returns minimal information without authentication
    """
    try:
        return APIResponse.success(
            data={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "psychsync-api",
            },
            request_id=get_request_id(request),
        )
    except Exception:
        return APIResponse.server_error(
            message="Health check failed", request_id=get_request_id(request)
        )


@router.get("/health", summary="Basic Health Check")
async def health_check(request: Request):
    """
    Basic health check endpoint (no authentication required)
    Returns system status and basic metrics for monitoring systems
    """
    start_time = time.time()

    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Calculate response time
        response_time = (time.time() - start_time) * 1000

        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": get_uptime_seconds(),
            "version": getattr(settings, "APP_VERSION", "1.0.0"),
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "response_time_ms": round(response_time, 2),
            "system": {
                "cpu_percent": round(cpu_percent, 2),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": round(memory.percent, 2),
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 2),
                },
            },
        }

        logger.info(
            EventType.SYSTEM_EVENT,
            "Health check completed",
            operation_name="health_check",
            response_time_ms=response_time,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=round((disk.used / disk.total) * 100, 2),
        )

        return APIResponse.success(data=health_data, request_id=get_request_id(request))

    except Exception as e:
        logger.log_error(e, operation="health_check")
        return APIResponse.server_error(
            message="Health check failed", request_id=get_request_id(request)
        )


@router.get("/health/detailed", summary="Detailed Health Check")
async def detailed_health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Comprehensive health check including database and cache status
    """
    start_time = time.time()
    health_status = "healthy"
    components = {}

    try:
        # Database health check
        db_start = time.time()
        try:
            result = await db.execute(text("SELECT 1 as health_check"))
            db_health = result.scalar() == 1
            db_response_time = (time.time() - db_start) * 1000

            components["database"] = {
                "status": "healthy" if db_health else "unhealthy",
                "response_time_ms": round(db_response_time, 2),
                "connection": "established" if db_health else "failed",
            }

            if not db_health:
                health_status = "degraded"

        except Exception as db_error:
            components["database"] = {
                "status": "unhealthy",
                "response_time_ms": None,
                "connection": "failed",
                "error": str(db_error),
            }
            health_status = "unhealthy"

        # Redis/Cache health check
        cache_start = time.time()
        try:
            test_key = "health_check_test"
            test_value = {"test": "value", "timestamp": datetime.utcnow().isoformat()}

            # Test cache set
            cache_set_success = await cache_set(test_key, test_value, ttl=10)

            # Test cache get
            cached_value = await cache_get(test_key)

            cache_health = cache_set_success and cached_value == test_value
            cache_response_time = (time.time() - cache_start) * 1000

            components["cache"] = {
                "status": "healthy" if cache_health else "unhealthy",
                "response_time_ms": round(cache_response_time, 2),
                "connection": "established" if cache_health else "failed",
            }

            if not cache_health:
                health_status = "degraded" if health_status == "healthy" else "unhealthy"

        except Exception as cache_error:
            components["cache"] = {
                "status": "unhealthy",
                "response_time_ms": None,
                "connection": "failed",
                "error": str(cache_error),
            }
            health_status = "degraded" if health_status == "healthy" else "unhealthy"

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else None

        # Check for system resource issues
        system_issues = []
        if cpu_percent > 90:
            system_issues.append("High CPU usage")
            health_status = "degraded" if health_status == "healthy" else "unhealthy"

        if memory.percent > 90:
            system_issues.append("High memory usage")
            health_status = "degraded" if health_status == "healthy" else "unhealthy"

        # Application metrics
        app_metrics = await get_application_metrics()

        total_response_time = (time.time() - start_time) * 1000

        health_data = {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": get_uptime_seconds(),
            "version": getattr(settings, "APP_VERSION", "1.0.0"),
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "response_time_ms": round(total_response_time, 2),
            "components": components,
            "system": {
                "cpu_percent": round(cpu_percent, 2),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": round(memory.percent, 2),
                },
                "load_average": load_avg,
                "issues": system_issues,
            },
            "application": app_metrics,
        }

        # Log health status
        log_level = EventType.SYSTEM_EVENT if health_status == "healthy" else EventType.ERROR_EVENT
        logger.log(
            log_level,
            f"Detailed health check: {health_status}",
            operation_name="detailed_health_check",
            health_status=health_status,
            total_response_time_ms=total_response_time,
            component_status=components,
            system_issues=system_issues,
        )

        # Return appropriate status code
        status_code = (
            status.HTTP_200_OK
            if health_status == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return APIResponse.success(
            data=health_data,
            message=f"System status: {health_status}",
            request_id=get_request_id(request),
            status_code=status_code,
        )

    except Exception as e:
        logger.log_error(e, operation="detailed_health_check")
        return APIResponse.server_error(
            message="Detailed health check failed", request_id=get_request_id(request)
        )


@router.get("/metrics", summary="Application Metrics")
async def get_metrics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed application metrics
    Requires authentication for security
    """
    try:
        # Database metrics
        db_metrics = await get_database_metrics(db)

        # Cache metrics
        cache_stats = intelligent_cache.get_cache_stats()

        # Application metrics
        app_metrics = await get_application_metrics()

        # System metrics
        system_metrics = get_system_metrics()

        all_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": get_uptime_seconds(),
            "database": db_metrics,
            "cache": cache_stats,
            "application": app_metrics,
            "system": system_metrics,
        }

        logger.info(
            EventType.PERFORMANCE_METRIC,
            "Metrics retrieved",
            operation_name="get_metrics",
            user_id=str(current_user.id),
        )

        return APIResponse.success(
            data=all_metrics,
            message="Metrics retrieved successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(e, operation="get_metrics", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to retrieve metrics", request_id=get_request_id(request)
        )


@router.get("/metrics/cache", summary="Cache Performance Metrics")
async def get_cache_metrics(
    request: Request, current_user: User = Depends(get_current_active_user)
):
    """
    Get cache performance metrics
    """
    try:
        cache_stats = intelligent_cache.get_cache_stats()

        logger.info(
            EventType.PERFORMANCE_METRIC,
            "Cache metrics retrieved",
            operation_name="get_cache_metrics",
        )

        return APIResponse.success(
            data=cache_stats,
            message="Cache metrics retrieved successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(e, operation="get_cache_metrics")
        return APIResponse.server_error(
            message="Failed to retrieve cache metrics", request_id=get_request_id(request)
        )


# COMPLETED: Business metrics dashboard implemented
# Provides business-level metrics like user activity, assessment completion rates, team growth


async def get_business_metrics(db: AsyncSession, org_id: UUID | None = None) -> dict[str, Any]:
    """
    Get business-level metrics for dashboard and monitoring
    """
    try:
        # User metrics
        base_user_conditions = []
        if org_id:
            base_user_conditions.append(User.organization_id == org_id)

        total_users_query = text(
            "SELECT COUNT(*) FROM users" + (" WHERE organization_id = :org_id" if org_id else "")
        )
        total_users_result = await db.execute(
            total_users_query, {"org_id": str(org_id)} if org_id else {}
        )
        total_users = total_users_result.scalar()

        # Active users in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users_query = text(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM user_activity_log
            WHERE created_at >= :since_date
        """
            + (
                " AND user_id IN (SELECT id FROM users WHERE organization_id = :org_id)"
                if org_id
                else ""
            )
        )

        try:
            active_users_result = await db.execute(
                active_users_query,
                {"since_date": seven_days_ago, "org_id": str(org_id)}
                if org_id
                else {"since_date": seven_days_ago},
            )
            active_users = active_users_result.scalar() or 0
        except Exception as e:
            # Fallback if user_activity_log table doesn't exist
            active_users = 0

        # New users in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_query = text(
            """
            SELECT COUNT(*) FROM users
            WHERE created_at >= :since_date
        """
            + (" AND organization_id = :org_id" if org_id else "")
        )

        new_users_result = await db.execute(
            new_users_query,
            {"since_date": thirty_days_ago, "org_id": str(org_id)}
            if org_id
            else {"since_date": thirty_days_ago},
        )
        new_users = new_users_result.scalar()

        # Assessment metrics (if assessment tables exist)
        assessment_metrics = {}
        try:
            total_assessments_query = text(
                """
                SELECT COUNT(*) FROM assessments
            """
                + (" WHERE organization_id = :org_id" if org_id else "")
            )

            total_assessments_result = await db.execute(
                total_assessments_query, {"org_id": str(org_id)} if org_id else {}
            )
            total_assessments = total_assessments_result.scalar() or 0

            completed_assessments_query = text(
                """
                SELECT COUNT(*) FROM assessment_responses
                WHERE status = 'completed'
            """
                + (
                    " AND user_id IN (SELECT id FROM users WHERE organization_id = :org_id)"
                    if org_id
                    else ""
                )
            )

            completed_assessments_result = await db.execute(
                completed_assessments_query, {"org_id": str(org_id)} if org_id else {}
            )
            completed_assessments = completed_assessments_result.scalar() or 0

            assessment_metrics = {
                "total_assessments": total_assessments,
                "completed_assessments": completed_assessments,
                "completion_rate": round(
                    (completed_assessments / max(total_assessments, 1)) * 100, 2
                ),
            }
        except Exception as e:            # Tables might not exist in development
            assessment_metrics = {
                "total_assessments": 0,
                "completed_assessments": 0,
                "completion_rate": 0,
            }

        return {
            "users": {
                "total": total_users,
                "active_last_7_days": active_users,
                "new_last_30_days": new_users,
                "active_rate": round((active_users / max(total_users, 1)) * 100, 2),
            },
            "assessments": assessment_metrics,
            "org_id": str(org_id) if org_id else None,
            "period": "last_30_days",
        }

    except Exception as e:
        logger.log_error(
            e, operation="get_business_metrics", org_id=str(org_id) if org_id else None
        )
        return {
            "users": {"total": 0, "active_last_7_days": 0, "new_last_30_days": 0, "active_rate": 0},
            "assessments": {
                "total_assessments": 0,
                "completed_assessments": 0,
                "completion_rate": 0,
            },
            "org_id": str(org_id) if org_id else None,
            "error": str(e),
        }


@router.get("/metrics/business", summary="Business Metrics Dashboard")
async def get_business_metrics_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    org_id: UUID | None = None,
):
    """
    Get business-level metrics for dashboard
    """
    try:
        business_metrics = await get_business_metrics(db, org_id)

        logger.info(
            EventType.BUSINESS_EVENT,
            "Business metrics retrieved",
            operation_name="get_business_metrics",
            user_id=str(current_user.id),
            org_id=str(org_id) if org_id else None,
        )

        return APIResponse.success(
            data=business_metrics,
            message="Business metrics retrieved successfully",
            request_id=get_request_id(request),
        )

    except Exception as e:
        logger.log_error(e, operation="get_business_metrics_endpoint", user_id=str(current_user.id))
        return APIResponse.server_error(
            message="Failed to retrieve business metrics", request_id=get_request_id(request)
        )


# Helper functions


def get_uptime_seconds() -> int:
    """
    Get application uptime in seconds.

    **Fixed Bug:** Previously used os.getpid() (process ID) instead of start time,
    resulting in completely incorrect uptime calculations. Now uses the stored
    application start time from module initialization.
    """
    try:
        return int(time.time() - _APP_START_TIME)
    except Exception as e:
        logger.log_error(e, operation="get_uptime_seconds")
        return 0


async def get_database_metrics(db: AsyncSession) -> dict[str, Any]:
    """Get database performance metrics"""
    try:
        # Connection pool metrics (if available)
        metrics = {
            "connection_pool": {
                "size": "unknown",
                "checked_in": "unknown",
                "checked_out": "unknown",
            }
        }

        # Test query performance
        start_time = time.time()
        result = await db.execute(text("SELECT 1"))
        query_time = (time.time() - start_time) * 1000

        metrics["query_performance_ms"] = round(query_time, 2)
        metrics["connection_test"] = "passed"

        return metrics

    except Exception as e:
        return {"connection_test": "failed", "error": str(e), "query_performance_ms": None}


async def get_application_metrics() -> dict[str, Any]:
    """Get application-level metrics"""
    try:
        process = psutil.Process()
        return {
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "cpu_percent": round(process.cpu_percent(), 2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()) if hasattr(process, "open_files") else 0,
            "connections": len(process.connections()) if hasattr(process, "connections") else 0,
        }
    except Exception as e:
        return {"memory_mb": 0, "cpu_percent": 0, "threads": 0, "open_files": 0, "connections": 0}


def get_system_metrics() -> dict[str, Any]:
    """Get system-level metrics"""
    try:
        return {
            "cpu_percent": round(psutil.cpu_percent(interval=None), 2),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "percent_used": round(psutil.virtual_memory().percent, 2),
            },
            "disk": {
                "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
                "percent_used": round(
                    (psutil.disk_usage("/").used / psutil.disk_usage("/").total) * 100, 2
                ),
            },
            "load_average": psutil.getloadavg() if hasattr(psutil, "getloadavg") else None,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            if hasattr(psutil, "boot_time")
            else None,
        }
    except Exception as e:
        return {
            "cpu_percent": 0,
            "memory": {"total_gb": 0, "available_gb": 0, "percent_used": 0},
            "disk": {"total_gb": 0, "free_gb": 0, "percent_used": 0},
            "load_average": None,
            "boot_time": None,
        }
