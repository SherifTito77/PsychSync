"""
Push Notification Service for PsychSync SaaS

This service handles sending push notifications to users across different platforms
(iOS, Android, Web) to increase user engagement and retention.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

# Third-party imports
try:
    from pyfcm import FCMNotification
    from apns2.client import APNsClient
    from apns2.payload import Payload, PayloadAlert
    from apns2.credentials import TokenCredentials
except ImportError:
    logging.warning("Push notification libraries not installed. Install with: pip install pyfcm apns2")

# Django imports (if using Django)
try:
    from django.conf import settings
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from django.core.exceptions import ImproperlyConfigured
except ImportError:
    # Fallback for non-Django environments
    settings = None
    timezone = None
    get_user_model = None

# App imports
from .notification_templates import NotificationTemplates
from .user_preferences import UserPreferencesService

# Set up logging
logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service for sending push notifications to users across different platforms.
    """
    
    def __init__(self):
        """Initialize the push notification service with required credentials."""
        self.fcm_service = None
        self.apns_client = None
        
        # Initialize FCM (Firebase Cloud Messaging) for Android and Web
        self._initialize_fcm()
        
        # Initialize APNs (Apple Push Notification Service) for iOS
        self._initialize_apns()
        
        # Initialize templates and preferences
        self.templates = NotificationTemplates()
        self.preferences_service = UserPreferencesService()
    
    def _initialize_fcm(self):
        """Initialize Firebase Cloud Messaging service."""
        try:
            # Get FCM server key from settings or environment
            fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None) if settings else os.environ.get('FCM_SERVER_KEY')
            
            if not fcm_server_key:
                logger.warning("FCM server key not configured. Android/Web push notifications will not work.")
                return
                
            self.fcm_service = FCMNotification(api_key=fcm_server_key)
            logger.info("FCM service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FCM service: {str(e)}")
    
    def _initialize_apns(self):
        """Initialize Apple Push Notification Service client."""
        try:
            # Get APNs credentials from settings or environment
            apns_key_id = getattr(settings, 'APNS_KEY_ID', None) if settings else os.environ.get('APNS_KEY_ID')
            apns_team_id = getattr(settings, 'APNS_TEAM_ID', None) if settings else os.environ.get('APNS_TEAM_ID')
            apns_key_path = getattr(settings, 'APNS_KEY_PATH', None) if settings else os.environ.get('APNS_KEY_PATH')
            apns_use_sandbox = getattr(settings, 'APNS_USE_SANDBOX', True) if settings else os.environ.get('APNS_USE_SANDBOX', 'true').lower() == 'true'
            
            if not all([apns_key_id, apns_team_id, apns_key_path]):
                logger.warning("APNs credentials not fully configured. iOS push notifications will not work.")
                return
                
            # Create token credentials
            token_credentials = TokenCredentials(
                auth_key_path=apns_key_path,
                key_id=apns_key_id,
                team_id=apns_team_id
            )
            
            # Initialize APNs client
            self.apns_client = APNsClient(
                credentials=token_credentials,
                use_sandbox=apns_use_sandbox
            )
            
            logger.info("APNs client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize APNs client: {str(e)}")
    
    def send_notification(
        self,
        user_id: Union[str, int],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None,
        deep_link: Optional[str] = None,
        notification_type: str = "general",
        platform: Optional[str] = None
    ) -> Dict:
        """
        Send a push notification to a user.
        
        Args:
            user_id: The ID of the user to send the notification to
            title: The notification title
            body: The notification body text
            data: Additional data to send with the notification
            image_url: URL to an image to display with the notification
            deep_link: Deep link to open when notification is tapped
            notification_type: Type of notification (e.g., "appointment", "medication", "general")
            platform: Target platform ("ios", "android", "web", or None for all)
            
        Returns:
            Dict with results of the notification sending attempt
        """
        # Get user model if using Django
        User = get_user_model() if get_user_model else None
        
        # Get user and their device tokens
        if User:
            try:
                user = User.objects.get(id=user_id)
                device_tokens = self._get_user_device_tokens(user, platform)
            except User.DoesNotExist:
                logger.error(f"User with ID {user_id} does not exist")
                return {"success": False, "error": "User not found"}
        else:
            # Fallback for non-Django environments
            device_tokens = self._get_user_device_tokens_by_id(user_id, platform)
        
        if not device_tokens:
            logger.warning(f"No device tokens found for user {user_id}")
            return {"success": False, "error": "No device tokens found"}
        
        # Check user preferences
        if not self.preferences_service.is_notification_enabled(user_id, notification_type):
            logger.info(f"User {user_id} has disabled {notification_type} notifications")
            return {"success": False, "error": "Notification type disabled by user"}
        
        # Prepare notification data
        notification_data = data or {}
        if deep_link:
            notification_data["deep_link"] = deep_link
        
        # Group tokens by platform
        ios_tokens = device_tokens.get("ios", [])
        android_tokens = device_tokens.get("android", [])
        web_tokens = device_tokens.get("web", [])
        
        results = {
            "success": True,
            "user_id": user_id,
            "notification_type": notification_type,
            "results": {}
        }
        
        # Send to iOS devices
        if ios_tokens and (platform is None or platform == "ios"):
            ios_result = self._send_to_ios(
                tokens=ios_tokens,
                title=title,
                body=body,
                data=notification_data,
                image_url=image_url
            )
            results["results"]["ios"] = ios_result
            if not ios_result.get("success", False):
                results["success"] = False
        
        # Send to Android devices
        if android_tokens and (platform is None or platform == "android"):
            android_result = self._send_to_android(
                tokens=android_tokens,
                title=title,
                body=body,
                data=notification_data,
                image_url=image_url
            )
            results["results"]["android"] = android_result
            if not android_result.get("success", False):
                results["success"] = False
        
        # Send to Web devices
        if web_tokens and (platform is None or platform == "web"):
            web_result = self._send_to_web(
                tokens=web_tokens,
                title=title,
                body=body,
                data=notification_data,
                image_url=image_url
            )
            results["results"]["web"] = web_result
            if not web_result.get("success", False):
                results["success"] = False
        
        # Log the notification for analytics
        self._log_notification(user_id, notification_type, title, body, results)
        
        return results
    
    def send_template_notification(
        self,
        user_id: Union[str, int],
        template_name: str,
        template_data: Dict,
        platform: Optional[str] = None
    ) -> Dict:
        """
        Send a notification using a predefined template.
        
        Args:
            user_id: The ID of the user to send the notification to
            template_name: Name of the template to use
            template_data: Data to populate the template
            platform: Target platform ("ios", "android", "web", or None for all)
            
        Returns:
            Dict with results of the notification sending attempt
        """
        # Get the template
        template = self.templates.get_template(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return {"success": False, "error": f"Template '{template_name}' not found"}
        
        # Render the template with the provided data
        rendered = self.templates.render_template(template_name, template_data)
        
        # Send the notification
        return self.send_notification(
            user_id=user_id,
            title=rendered["title"],
            body=rendered["body"],
            data=rendered.get("data", {}),
            image_url=rendered.get("image_url"),
            deep_link=rendered.get("deep_link"),
            notification_type=template.get("type", "general"),
            platform=platform
        )
    
    def send_bulk_notification(
        self,
        user_ids: List[Union[str, int]],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None,
        deep_link: Optional[str] = None,
        notification_type: str = "general",
        platform: Optional[str] = None
    ) -> Dict:
        """
        Send a push notification to multiple users.
        
        Args:
            user_ids: List of user IDs to send the notification to
            title: The notification title
            body: The notification body text
            data: Additional data to send with the notification
            image_url: URL to an image to display with the notification
            deep_link: Deep link to open when notification is tapped
            notification_type: Type of notification (e.g., "appointment", "medication", "general")
            platform: Target platform ("ios", "android", "web", or None for all)
            
        Returns:
            Dict with results of the bulk notification sending attempt
        """
        results = {
            "success": True,
            "total_users": len(user_ids),
            "successful_sends": 0,
            "failed_sends": 0,
            "results": {}
        }
        
        for user_id in user_ids:
            result = self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
                image_url=image_url,
                deep_link=deep_link,
                notification_type=notification_type,
                platform=platform
            )
            
            results["results"][str(user_id)] = result
            
            if result.get("success", False):
                results["successful_sends"] += 1
            else:
                results["failed_sends"] += 1
                results["success"] = False
        
        return results
    
    def _get_user_device_tokens(self, user, platform: Optional[str] = None) -> Dict:
        """
        Get device tokens for a user, optionally filtered by platform.
        
        Args:
            user: User object
            platform: Filter by platform ("ios", "android", "web", or None for all)
            
        Returns:
            Dict of device tokens grouped by platform
        """
        # This would typically query a database for the user's device tokens
        # Implementation depends on your data model
        
        # Example implementation (adjust based on your actual model)
        try:
            # Assuming a DeviceToken model with fields: token, platform, is_active
            from .models import DeviceToken
            
            tokens = DeviceToken.objects.filter(user=user, is_active=True)
            
            if platform:
                tokens = tokens.filter(platform=platform.lower())
            
            # Group tokens by platform
            result = {"ios": [], "android": [], "web": []}
            for token in tokens:
                if token.platform.lower() in result:
                    result[token.platform.lower()].append(token.token)
            
            return result
        except ImportError:
            # Fallback for when the model doesn't exist
            logger.warning("DeviceToken model not found. Using fallback implementation.")
            return {"ios": [], "android": [], "web": []}
    
    def _get_user_device_tokens_by_id(self, user_id: Union[str, int], platform: Optional[str] = None) -> Dict:
        """
        Fallback method to get device tokens by user ID when Django models aren't available.
        
        Args:
            user_id: User ID
            platform: Filter by platform ("ios", "android", "web", or None for all)
            
        Returns:
            Dict of device tokens grouped by platform
        """
        # This would typically query a database for the user's device tokens
        # Implementation depends on your data model
        
        # Example implementation (adjust based on your actual model)
        # This is a placeholder - replace with your actual implementation
        return {"ios": [], "android": [], "web": []}
    
    def _send_to_ios(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Dict,
        image_url: Optional[str] = None
    ) -> Dict:
        """
        Send push notification to iOS devices.
        
        Args:
            tokens: List of iOS device tokens
            title: Notification title
            body: Notification body
            data: Additional data
            image_url: URL to an image
            
        Returns:
            Dict with results of the notification sending attempt
        """
        if not self.apns_client:
            logger.error("APNs client not initialized")
            return {"success": False, "error": "APNs client not initialized"}
        
        if not tokens:
            return {"success": False, "error": "No tokens provided"}
        
        # Create payload
        alert = PayloadAlert(title=title, body=body)
        
        # Add image if provided
        if image_url:
            # iOS 10+ supports rich notifications with images
            alert.title = title
            alert.body = body
        
        payload = Payload(
            alert=alert,
            sound="default",
            badge=1,
            custom=data
        )
        
        results = {
            "success": True,
            "total_tokens": len(tokens),
            "successful_sends": 0,
            "failed_sends": 0,
            "failed_tokens": []
        }
        
        # Send to each token
        for token in tokens:
            try:
                self.apns_client.send_notification(
                    token_hex=token,
                    notification=payload,
                    topic=getattr(settings, 'APNS_BUNDLE_ID', 'com.psychsync.app') if settings else os.environ.get('APNS_BUNDLE_ID', 'com.psychsync.app')
                )
                results["successful_sends"] += 1
            except Exception as e:
                logger.error(f"Failed to send iOS notification to token {token}: {str(e)}")
                results["failed_sends"] += 1
                results["failed_tokens"].append(token)
                results["success"] = False
        
        return results
    
    def _send_to_android(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Dict,
        image_url: Optional[str] = None
    ) -> Dict:
        """
        Send push notification to Android devices.
        
        Args:
            tokens: List of Android device tokens
            title: Notification title
            body: Notification body
            data: Additional data
            image_url: URL to an image
            
        Returns:
            Dict with results of the notification sending attempt
        """
        if not self.fcm_service:
            logger.error("FCM service not initialized")
            return {"success": False, "error": "FCM service not initialized"}
        
        if not tokens:
            return {"success": False, "error": "No tokens provided"}
        
        # Prepare notification message
        message_title = title
        message_body = body
        
        # Prepare data payload
        data_payload = data.copy()
        if image_url:
            data_payload["image_url"] = image_url
        
        # Send notification
        try:
            result = self.fcm_service.notify_multiple_devices(
                registration_ids=tokens,
                message_title=message_title,
                message_body=message_body,
                data_message=data_payload,
                sound="Default",
                click_action=data.get("deep_link", "")
            )
            
            # Process results
            results = {
                "success": True,
                "total_tokens": len(tokens),
                "successful_sends": 0,
                "failed_sends": 0,
                "failed_tokens": []
            }
            
            # FCM returns results in a specific format
            if isinstance(result, dict):
                if "results" in result:
                    for i, item in enumerate(result["results"]):
                        if "error" in item:
                            results["failed_sends"] += 1
                            results["failed_tokens"].append(tokens[i])
                            results["success"] = False
                        else:
                            results["successful_sends"] += 1
                elif "failure" in result and result["failure"] > 0:
                    results["success"] = False
                    results["failed_sends"] = result["failure"]
                    results["successful_sends"] = result["success"]
            
            return results
        except Exception as e:
            logger.error(f"Failed to send Android notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _send_to_web(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Dict,
        image_url: Optional[str] = None
    ) -> Dict:
        """
        Send push notification to web browsers.
        
        Args:
            tokens: List of web push subscription tokens
            title: Notification title
            body: Notification body
            data: Additional data
            image_url: URL to an image
            
        Returns:
            Dict with results of the notification sending attempt
        """
        if not self.fcm_service:
            logger.error("FCM service not initialized")
            return {"success": False, "error": "FCM service not initialized"}
        
        if not tokens:
            return {"success": False, "error": "No tokens provided"}
        
        # Prepare notification message
        message_title = title
        message_body = body
        
        # Prepare data payload
        data_payload = data.copy()
        if image_url:
            data_payload["image_url"] = image_url
        
        # Send notification
        try:
            result = self.fcm_service.notify_multiple_devices(
                registration_ids=tokens,
                message_title=message_title,
                message_body=message_body,
                data_message=data_payload,
                sound="Default",
                click_action=data.get("deep_link", "")
            )
            
            # Process results
            results = {
                "success": True,
                "total_tokens": len(tokens),
                "successful_sends": 0,
                "failed_sends": 0,
                "failed_tokens": []
            }
            
            # FCM returns results in a specific format
            if isinstance(result, dict):
                if "results" in result:
                    for i, item in enumerate(result["results"]):
                        if "error" in item:
                            results["failed_sends"] += 1
                            results["failed_tokens"].append(tokens[i])
                            results["success"] = False
                        else:
                            results["successful_sends"] += 1
                elif "failure" in result and result["failure"] > 0:
                    results["success"] = False
                    results["failed_sends"] = result["failure"]
                    results["successful_sends"] = result["success"]
            
            return results
        except Exception as e:
            logger.error(f"Failed to send Web notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _log_notification(
        self,
        user_id: Union[str, int],
        notification_type: str,
        title: str,
        body: str,
        results: Dict
    ):
        """
        Log notification for analytics and debugging purposes.
        
        Args:
            user_id: ID of the user the notification was sent to
            notification_type: Type of notification
            title: Notification title
            body: Notification body
            results: Results of the notification sending attempt
        """
        try:
            # This would typically save to a database or analytics service
            # Implementation depends on your data model
            
            # Example implementation (adjust based on your actual model)
            try:
                from .models import NotificationLog
                
                NotificationLog.objects.create(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    sent_at=timezone.now() if timezone else datetime.now(),
                    success=results.get("success", False),
                    details=json.dumps(results)
                )
            except ImportError:
                # Fallback for when the model doesn't exist
                logger.info(f"Notification sent to user {user_id}: {title} - Success: {results.get('success', False)}")
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
    
    def schedule_notification(
        self,
        user_id: Union[str, int],
        title: str,
        body: str,
        scheduled_time: datetime,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None,
        deep_link: Optional[str] = None,
        notification_type: str = "general",
        platform: Optional[str] = None
    ) -> Dict:
        """
        Schedule a push notification to be sent at a later time.
        
        Args:
            user_id: The ID of the user to send the notification to
            title: The notification title
            body: The notification body text
            scheduled_time: When to send the notification
            data: Additional data to send with the notification
            image_url: URL to an image to display with the notification
            deep_link: Deep link to open when notification is tapped
            notification_type: Type of notification (e.g., "appointment", "medication", "general")
            platform: Target platform ("ios", "android", "web", or None for all)
            
        Returns:
            Dict with results of the scheduling attempt
        """
        try:
            # This would typically save to a database and use a task queue like Celery
            # Implementation depends on your task queue system
            
            # Example implementation (adjust based on your actual model)
            try:
                from .models import ScheduledNotification
                
                scheduled_notification = ScheduledNotification.objects.create(
                    user_id=user_id,
                    title=title,
                    body=body,
                    scheduled_time=scheduled_time,
                    data=json.dumps(data or {}),
                    image_url=image_url,
                    deep_link=deep_link,
                    notification_type=notification_type,
                    platform=platform,
                    is_sent=False
                )
                
                return {
                    "success": True,
                    "scheduled_notification_id": scheduled_notification.id,
                    "scheduled_time": scheduled_time.isoformat()
                }
            except ImportError:
                # Fallback for when the model doesn't exist
                logger.info(f"Scheduled notification for user {user_id} at {scheduled_time}")
                return {
                    "success": True,
                    "scheduled_time": scheduled_time.isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to schedule notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def cancel_scheduled_notification(self, scheduled_notification_id: Union[str, int]) -> Dict:
        """
        Cancel a scheduled push notification.
        
        Args:
            scheduled_notification_id: ID of the scheduled notification to cancel
            
        Returns:
            Dict with results of the cancellation attempt
        """
        try:
            # This would typically update a database record
            # Implementation depends on your data model
            
            # Example implementation (adjust based on your actual model)
            try:
                from .models import ScheduledNotification
                
                notification = ScheduledNotification.objects.get(id=scheduled_notification_id)
                notification.is_cancelled = True
                notification.save()
                
                return {"success": True, "cancelled_notification_id": scheduled_notification_id}
            except ImportError:
                # Fallback for when the model doesn't exist
                logger.info(f"Cancelled scheduled notification {scheduled_notification_id}")
                return {"success": True, "cancelled_notification_id": scheduled_notification_id}
        except Exception as e:
            logger.error(f"Failed to cancel scheduled notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_daily_mindfulness_reminder(self, user_id: Union[str, int]) -> Dict:
        """
        Send a daily mindfulness reminder notification.
        
        Args:
            user_id: The ID of the user to send the reminder to
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="daily_mindfulness_reminder",
            template_data={}
        )
    
    def send_appointment_reminder(self, user_id: Union[str, int], appointment_details: Dict) -> Dict:
        """
        Send an appointment reminder notification.
        
        Args:
            user_id: The ID of the user to send the reminder to
            appointment_details: Details of the appointment
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="appointment_reminder",
            template_data=appointment_details
        )
    
    def send_medication_reminder(self, user_id: Union[str, int], medication_details: Dict) -> Dict:
        """
        Send a medication reminder notification.
        
        Args:
            user_id: The ID of the user to send the reminder to
            medication_details: Details of the medication
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="medication_reminder",
            template_data=medication_details
        )
    
    def send_journal_prompt(self, user_id: Union[str, int], prompt_text: str) -> Dict:
        """
        Send a journal prompt notification.
        
        Args:
            user_id: The ID of the user to send the prompt to
            prompt_text: The journal prompt text
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="journal_prompt",
            template_data={"prompt_text": prompt_text}
        )
    
    def send_mood_check_reminder(self, user_id: Union[str, int]) -> Dict:
        """
        Send a mood check reminder notification.
        
        Args:
            user_id: The ID of the user to send the reminder to
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="mood_check_reminder",
            template_data={}
        )
    
    def send_achievement_unlocked(self, user_id: Union[str, int], achievement_details: Dict) -> Dict:
        """
        Send an achievement unlocked notification.
        
        Args:
            user_id: The ID of the user to send the notification to
            achievement_details: Details of the achievement
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="achievement_unlocked",
            template_data=achievement_details
        )
    
    def send_session_feedback_request(self, user_id: Union[str, int], session_details: Dict) -> Dict:
        """
        Send a session feedback request notification.
        
        Args:
            user_id: The ID of the user to send the request to
            session_details: Details of the session
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="session_feedback_request",
            template_data=session_details
        )
    
    def send_reengagement_notification(self, user_id: Union[str, int], days_inactive: int) -> Dict:
        """
        Send a re-engagement notification to an inactive user.
        
        Args:
            user_id: The ID of the user to send the notification to
            days_inactive: Number of days the user has been inactive
            
        Returns:
            Dict with results of the notification sending attempt
        """
        return self.send_template_notification(
            user_id=user_id,
            template_name="reengagement",
            template_data={"days_inactive": days_inactive}
        )
        