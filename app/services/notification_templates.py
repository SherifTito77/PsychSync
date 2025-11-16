"""
Notification templates for PsychSync SaaS
"""

class NotificationTemplates:
    """
    Templates for different types of push notifications.
    """
    
    def __init__(self):
        self.templates = {
            "daily_mindfulness_reminder": {
                "title": "Time for Mindfulness",
                "body": "Take a moment to practice mindfulness today. A few minutes can make a big difference.",
                "type": "mindfulness",
                "deep_link": "/mindfulness",
                "data": {"category": "mindfulness"}
            },
            "appointment_reminder": {
                "title": "Upcoming Appointment",
                "body": "You have an appointment with {therapist_name} on {date} at {time}.",
                "type": "appointment",
                "deep_link": "/appointments/{appointment_id}",
                "data": {"category": "appointment"}
            },
            "medication_reminder": {
                "title": "Medication Reminder",
                "body": "It's time to take your {medication_name}. {dosage_instructions}",
                "type": "medication",
                "deep_link": "/medications",
                "data": {"category": "medication"}
            },
            "journal_prompt": {
                "title": "Journal Prompt",
                "body": "{prompt_text}",
                "type": "journal",
                "deep_link": "/journal",
                "data": {"category": "journal"}
            },
            "mood_check_reminder": {
                "title": "How are you feeling?",
                "body": "Take a moment to check in with your emotions. Your mood tracker is ready.",
                "type": "mood",
                "deep_link": "/mood-tracker",
                "data": {"category": "mood"}
            },
            "achievement_unlocked": {
                "title": "Achievement Unlocked!",
                "body": "Congratulations! You've unlocked the {achievement_name} achievement.",
                "type": "achievement",
                "deep_link": "/achievements",
                "data": {"category": "achievement"}
            },
            "session_feedback_request": {
                "title": "How was your session?",
                "body": "Please share feedback about your recent session with {therapist_name}.",
                "type": "feedback",
                "deep_link": "/feedback/{session_id}",
                "data": {"category": "feedback"}
            },
            "reengagement": {
                "title": "We miss you!",
                "body": "It's been {days_inactive} days since your last check-in. Your mental health journey continues.",
                "type": "reengagement",
                "deep_link": "/dashboard",
                "data": {"category": "reengagement"}
            }
        }
    
    def get_template(self, template_name: str) -> dict:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(template_name)
    
    def render_template(self, template_name: str, data: dict) -> dict:
        """
        Render a template with the provided data.
        
        Args:
            template_name: Name of the template
            data: Data to populate the template
            
        Returns:
            Rendered template dictionary
        """
        template = self.get_template(template_name)
        if not template:
            return {}
        
        # Create a copy of the template
        rendered = template.copy()
        
        # Replace placeholders in title and body
        if "title" in rendered:
            rendered["title"] = rendered["title"].format(**data)
        
        if "body" in rendered:
            rendered["body"] = rendered["body"].format(**data)
        
        # Replace placeholders in deep_link
        if "deep_link" in rendered:
            rendered["deep_link"] = rendered["deep_link"].format(**data)
        
        # Copy data and merge with template data
        template_data = template.get("data", {}).copy()
        template_data.update(data)
        rendered["data"] = template_data
        
        return rendered
        