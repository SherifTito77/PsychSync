# app/domain/services/email_service.py

"""
DOMAIN EMAIL SERVICE INTERFACE
Abstract email service interface for the domain layer

This interface defines the contract for email services in the domain,
following clean architecture principles.

Author: Security Team
Version: 2.0 Enterprise Security
"""

from abc import ABC, abstractmethod


class EmailService(ABC):
    """
    Abstract email service interface for the domain layer

    This interface defines the contract for email operations that domain
    use cases can depend on without knowing the implementation details.
    """

    @abstractmethod
    async def send_verification_email(
        self,
        to_email: str,
        full_name: str,
        verification_url: str
    ) -> bool:
        """
        Send email verification to a user

        Args:
            to_email: The recipient's email address
            full_name: The recipient's full name
            verification_url: The URL for email verification

        Returns:
            True if email was sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def send_welcome_email(
        self,
        to_email: str,
        full_name: str,
        login_url: str
    ) -> bool:
        """
        Send welcome email to a newly registered user

        Args:
            to_email: The recipient's email address
            full_name: The recipient's full name
            login_url: URL for the user to log in

        Returns:
            True if email was sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def send_password_reset_email(
        self,
        to_email: str,
        full_name: str,
        reset_url: str
    ) -> bool:
        """
        Send password reset email to a user

        Args:
            to_email: The recipient's email address
            full_name: The recipient's full name
            reset_url: URL for password reset

        Returns:
            True if email was sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def send_security_alert_email(
        self,
        to_email: str,
        full_name: str,
        alert_message: str,
        recommendations: str
    ) -> bool:
        """
        Send security alert email to a user

        Args:
            to_email: The recipient's email address
            full_name: The recipient's full name
            alert_message: The security alert message
            recommendations: Security recommendations

        Returns:
            True if email was sent successfully, False otherwise
        """
        pass