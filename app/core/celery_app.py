"""
Celery Configuration for PsychSync AI Background Processing
"""

from celery import Celery

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "psychsync_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_disable_rate_limits=False,
)


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@celery_app.task
def test_ai_processing():
    """Test AI processing in background"""
    from app.ai.processors.mbti_processor import MBTIProcessor

    try:
        processor = MBTIProcessor()
        result = processor.process({"type": "INTJ", "confidence": 0.9})
        return {
            "success": True,
            "result": result,
            "message": "Background AI processing successful",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Background AI processing failed",
        }


if __name__ == "__main__":
    celery_app.start()
