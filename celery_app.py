"""
Celery application entry point

This module provides the main Celery application instance.
Import from celery_config to avoid circular imports.
"""

from app.core.config.celery_config import celery_app

__all__ = ["celery_app"]
