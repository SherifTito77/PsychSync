"""
User preferences service for PsychSync SaaS
"""

import logging
from typing import Dict, Union

# Django imports (if using Django)
try:
    from django.contrib.auth import get_user_model
except ImportError:
    get_user_model = None

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """
    Service for managing user notification preferences.
    """
    
    def __init__(self):
        """Initialize the user preferences service."""
        # Default notification preferences
        self.default_preferences = {
            "mindfulness": True,
            "appointment": True,
            "medication": True,
            "journal": True,
            "mood": True,
            "achievement": True,
            "feedback": True,
            "reengagement": True,
            "general": True
        }
    
    def is_notification_enabled(self, user_id: Union[str, int], notification_type: str) -> bool:
        """
        Check if a notification type is enabled for a user.
        
        Args:
            user_id: ID of the user
            notification_type: Type of notification
            
        Returns:
            True if the notification type is enabled, False otherwise
        """
        try:
            # Get user model if using Django
            User = get_user_model() if get_user_model else None
            
            if User:
                try:
                    user = User.objects.get(id=user_id)
                    # Assuming a UserProfile model with a notification_preferences field
                    # Implementation depends on your actual model
                    try:
                        from .models import UserProfile
                        profile = UserProfile.objects.get(user=user)
                        preferences = profile.notification_preferences or {}
                        return preferences.get(notification_type, self.default_preferences.get(notification_type, True))
                    except ImportError:
                        # Fallback for when the model doesn't exist
                        return self.default_preferences.get(notification_type, True)
                except User.DoesNotExist:
                    logger.error(f"User with ID {user_id} does not exist")
                    return False
            else:
                # Fallback for non-Django environments
                return self.default_preferences.get(notification_type, True)
        except Exception as e:
            logger.error(f"Error checking notification preferences: {str(e)}")
            return self.default_preferences.get(notification_type, True)
    
    def update_notification_preferences(self, user_id: Union[str, int], preferences: Dict) -> bool:
        """
        Update a user's notification preferences.
        
        Args:
            user_id: ID of the user
            preferences: Dictionary of notification preferences
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user model if using Django
            User = get_user_model() if get_user_model else None
            
            if User:
                try:
                    user = User.objects.get(id=user_id)
                    # Assuming a UserProfile model with a notification_preferences field
                    # Implementation depends on your actual model
                    try:
                        from .models import UserProfile
                        profile, created = UserProfile.objects.get_or_create(user=user)
                        
                        # Get current preferences
                        current_preferences = profile.notification_preferences or {}
                        
                        # Update with new preferences
                        current_preferences.update(preferences)
                        
                        # Save updated preferences
                        profile.notification_preferences = current_preferences
                        profile.save()
                        
                        return True
                    except ImportError:
                        # Fallback for when the model doesn't exist
                        logger.warning("UserProfile model not found. Cannot update notification preferences.")
                        return False
                except User.DoesNotExist:
                    logger.error(f"User with ID {user_id} does not exist")
                    return False
            else:
                # Fallback for non-Django environments
                logger.warning("Django not available. Cannot update notification preferences.")
                return False
        except Exception as e:
            logger.error(f"Error updating notification preferences: {str(e)}")
            return False
        