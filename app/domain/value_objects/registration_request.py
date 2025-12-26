# app/domain/value_objects/registration_request.py

"""
DOMAIN VALUE OBJECT - REGISTRATION REQUEST
Value object for user registration requests

This value object encapsulates the data required for user registration,
providing validation and type safety for the registration process.

Author: Security Team
Version: 2.0 Enterprise Security
"""

from dataclasses import dataclass
from typing import Optional
import re
import logging

# Initialize domain logger
domain_logger = logging.getLogger("app.domain.registration_request")


@dataclass
class RegistrationRequest:
    """
    Value object for user registration requests

    This value object encapsulates all the data required for user registration
    and provides validation to ensure data integrity.
    """

    email: str
    password: str
    full_name: str
    organization_id: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    referral_code: Optional[str] = None

    def __post_init__(self):
        """Validate registration request data"""
        self._validate_email()
        self._validate_password()
        self._validate_full_name()
        self._validate_phone()
        self._validate_timezone()

    def _validate_email(self):
        """Validate email format"""
        if not self.email:
            raise ValueError("Email is required")

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError(f"Invalid email format: {self.email}")

    def _validate_password(self):
        """Validate password strength"""
        if not self.password:
            raise ValueError("Password is required")

        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for password complexity
        has_upper = any(c.isupper() for c in self.password)
        has_lower = any(c.islower() for c in self.password)
        has_digit = any(c.isdigit() for c in self.password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in self.password)

        complexity_score = sum([has_upper, has_lower, has_digit, has_special])

        if complexity_score < 3:
            raise ValueError(
                "Password must contain at least 3 of: uppercase letter, "
                "lowercase letter, digit, and special character"
            )

    def _validate_full_name(self):
        """Validate full name"""
        if not self.full_name:
            raise ValueError("Full name is required")

        if len(self.full_name.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")

        if len(self.full_name) > 100:
            raise ValueError("Full name must be less than 100 characters")

    def _validate_phone(self):
        """Validate phone number format if provided"""
        if self.phone:
            # Basic phone validation - can be enhanced based on requirements
            phone_pattern = r'^\+?[\d\s\-\(\)]{10,}$'
            if not re.match(phone_pattern, self.phone):
                raise ValueError(f"Invalid phone number format: {self.phone}")

    def _validate_timezone(self):
        """Validate timezone if provided"""
        if self.timezone:
            # Basic timezone validation - can be enhanced with pytz
            valid_timezone_patterns = [
                r'^[A-Za-z_]+/[A-Za-z_]+$',
                r'^UTC[+-]\d+$',
                r'^GMT[+-]\d+$'
            ]

            if not any(re.match(pattern, self.timezone) for pattern in valid_timezone_patterns):
                domain_logger.warning(f"Potentially invalid timezone: {self.timezone}")

    def to_dict(self) -> dict:
        """Convert registration request to dictionary"""
        return {
            "email": self.email,
            "password": self.password,
            "full_name": self.full_name,
            "organization_id": self.organization_id,
            "phone": self.phone,
            "timezone": self.timezone,
            "language": self.language,
            "source": self.source,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "referral_code": self.referral_code
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RegistrationRequest':
        """Create registration request from dictionary"""
        return cls(
            email=data.get("email", ""),
            password=data.get("password", ""),
            full_name=data.get("full_name", ""),
            organization_id=data.get("organization_id"),
            phone=data.get("phone"),
            timezone=data.get("timezone"),
            language=data.get("language"),
            source=data.get("source"),
            client_ip=data.get("client_ip"),
            user_agent=data.get("user_agent"),
            referral_code=data.get("referral_code")
        )

    def is_complete(self) -> bool:
        """Check if all required fields are present"""
        return all([
            self.email,
            self.password,
            self.full_name
        ])

    def get_risk_score(self) -> float:
        """
        Calculate a simple risk score for this registration request

        Returns:
            Risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        risk_score = 0.0

        # Check for suspicious patterns
        if self.client_ip:
            # Add risk for certain IP patterns (simplified)
            if self.client_ip.startswith(("10.", "192.168.", "172.")):
                risk_score += 0.1  # Private IP, slightly suspicious
            elif self.client_ip.startswith(("127.", "0.")):
                risk_score += 0.3  # Localhost, more suspicious

        # Check email domain patterns
        if self.email:
            email_domain = self.email.split('@')[-1].lower()
            disposable_domains = ["10minutemail.com", "tempmail.org", "guerrillamail.com"]
            if any(disposable in email_domain for disposable in disposable_domains):
                risk_score += 0.5

        # Check password strength (inverse relationship)
        if len(self.password) >= 12:
            risk_score -= 0.1
        if self.password.islower() or self.password.isupper():
            risk_score += 0.2

        # Check for missing optional fields
        if not self.organization_id:
            risk_score += 0.1
        if not self.phone:
            risk_score += 0.1

        return max(0.0, min(1.0, risk_score))

    def is_high_risk(self, threshold: float = 0.6) -> bool:
        """Check if this registration request is high risk"""
        return self.get_risk_score() >= threshold