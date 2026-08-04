# Initialize a default email provider - in production this would be configured via settings
# Here we use a placeholder or dummy implementation to ensure it initializes
from app.core.config import settings
from app.presentation.email_template_renderer import email_template_renderer
from app.services.email_providers import EmailServiceManager, SendGridProvider

# This is a basic implementation to provide an email_provider object
# Replace 'SendGridProvider' with the actual provider configuration logic
email_provider = SendGridProvider(api_key=settings.SENDGRID_API_KEY or "dummy_key")

__all__ = ["email_template_renderer", "email_provider"]
