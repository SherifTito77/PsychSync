##app/api/routes/health.py


"""
Health check endpoint for monitoring system status
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_async_db
from app.core.cache import redis_health_check
import psutil
import time

router = APIRouter()


@router.get("")
@router.get("/")
async def health_check(db: AsyncSession = Depends(get_async_db)):
    """
    Comprehensive health check endpoint
    Returns status of database, cache, and system resources
    """
    start_time = time.time()
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_message = "Database connection successful"
    except Exception as e:
        db_status = "unhealthy"
        db_message = f"Database error: {str(e)}"
    
    # Redis check
    redis_status = redis_health_check()
    
    # System resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    response_time = (time.time() - start_time) * 1000  # ms
    
    overall_status = "healthy" if db_status == "healthy" and redis_status.get("status") == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "response_time_ms": round(response_time, 2),
        "services": {
            "database": {
                "status": db_status,
                "message": db_message
            },
            "cache": redis_status
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
    }


@router.get("/db")
async def database_health(db: AsyncSession = Depends(get_async_db)):
    """Quick database health check"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Database is responsive"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/cache")
async def cache_health():
    """Quick cache health check"""
    return redis_health_check()


@router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancer health checks"""
    return {"status": "ok", "message": "pong"}


