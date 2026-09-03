"""
Notification Service Stub
Provides a NotificationService class for modules that depend on it.
"""

import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Stub notification service for safety and other modules."""

    def __init__(self, db=None):
        self.db = db

    async def send_notification(self, user_id, message, notification_type="info"):
        logger.info("Notification queued for user %s: %s", user_id, message)
        return {"status": "queued", "user_id": str(user_id)}

    async def send_bulk_notification(self, user_ids, message, notification_type="info"):
        logger.info("Bulk notification queued for %d users", len(user_ids))
        return {"status": "queued", "count": len(user_ids)}
