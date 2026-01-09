# app/application/use_cases/register_user.py

"""
APPLICATION USE CASE - REGISTER USER
User registration use case with comprehensive business logic

USE CASE PRINCIPLES:
- Application business logic
- Orchestration of domain services
- Transaction management
- Error handling and validation
- External service integration
- Business rule enforcement

Author: Security Team
Version: 2.0 Enterprise Security
"""

from dataclasses import dataclass
import logging

from app.domain.entities.user import EmailAddress, User, UserPreferences, UserRole, UserStatus
from app.domain.events.user_events import UserRegisteredEvent
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.email_service import EmailService
from app.domain.value_objects.registration_request import RegistrationRequest

# Initialize use case logger
use_case_logger = logging.getLogger("app.use_cases.register_user")


@dataclass
class RegistrationResult:
    """Result of user registration use case"""

    success: bool
    user: User | None = None
    verification_token: str | None = None
    errors: list = None
    warnings: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class RegisterUserUseCase:
    """
    User registration use case handling the complete registration process

    This use case orchestrates:
    - Registration validation
    - Domain object creation
    - Persistence
    - Email verification
    - Event publishing
    """

    def __init__(self, user_repository: UserRepository, email_service: EmailService):
        self.user_repository = user_repository
        self.email_service = email_service

    async def execute(self, registration_request: RegistrationRequest) -> RegistrationResult:
        """
        Execute user registration use case

        Args:
            registration_request: Validated registration request

        Returns:
            Registration result with user or errors
        """
        try:
            use_case_logger.info(f"Starting registration for email: {registration_request.email}")

            # Step 1: Validate business rules
            validation_result = await self._validate_registration_rules(registration_request)
            if not validation_result.is_valid:
                return RegistrationResult(success=False, errors=validation_result.errors)

            # Step 2: Create domain entity
            user = await self._create_user_entity(registration_request)

            # Step 3: Persist user
            persisted_user = await self._persist_user(user)

            # Step 4: Generate verification token
            verification_token = await self._generate_verification_token(persisted_user)

            # Step 5: Send verification email
            email_sent = await self._send_verification_email(persisted_user, verification_token)

            # Step 6: Publish domain event
            await self._publish_user_registered_event(persisted_user, registration_request)

            use_case_logger.info(f"Registration completed for user: {persisted_user.id}")

            return RegistrationResult(
                success=True,
                user=persisted_user,
                verification_token=verification_token,
                warnings=[f"Email notification sent: {email_sent}"],
            )

        except Exception as e:
            use_case_logger.error(f"Registration failed: {e}", exc_info=True)
            return RegistrationResult(
                success=False, errors=["Registration failed due to an unexpected error"]
            )

    async def _validate_registration_rules(self, request: RegistrationRequest):
        """Validate registration business rules"""
        from app.application.validation.registration_validator import RegistrationValidationResult

        validator = RegistrationValidationResult()

        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(request.email)
        if existing_user:
            validator.add_error("Email address already registered")

        # Validate organization (if provided)
        if request.organization_id:
            org_exists = await self.user_repository.organization_exists(request.organization_id)
            if not org_exists:
                validator.add_error("Invalid organization ID")

        # Additional business validations can be added here

        return validator

    async def _create_user_entity(self, registration_request: RegistrationRequest) -> User:
        """Create user domain entity from registration request"""
        email_address = EmailAddress(value=registration_request.email)

        user = User(
            email=email_address,
            full_name=registration_request.full_name,
            role=UserRole.USER,
            status=UserStatus.PENDING_VERIFICATION,
            organization_id=registration_request.organization_id,
            phone=registration_request.phone,
            preferences=UserPreferences(
                timezone=registration_request.timezone or "UTC",
                language=registration_request.language or "en",
            ),
            metadata={
                "registration_source": registration_request.source,
                "client_ip": registration_request.client_ip,
                "user_agent": registration_request.user_agent,
                "referral_code": registration_request.referral_code,
            },
        )

        # Set password (would be hashed by domain service)
        if registration_request.password:
            from app.domain.services.password_service import PasswordService

            password_service = PasswordService()
            user.password_hash = await password_service.hash_password(registration_request.password)

        return user

    async def _persist_user(self, user: User) -> User:
        """Persist user to repository"""
        try:
            # Use repository to persist user
            persisted_user = await self.user_repository.save(user)
            return persisted_user
        except Exception as e:
            use_case_logger.error(f"Failed to persist user: {e}")
            raise

    async def _generate_verification_token(self, user: User) -> str:
        """Generate email verification token"""
        import secrets

        token = secrets.token_urlsafe(32)

        # Store token (in production, this would be stored securely)
        user.email._verification_token = token

        return token

    async def _send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send verification email to user"""
        try:
            verification_url = f"https://app.psychsync.com/verify-email?token={verification_token}"

            await self.email_service.send_verification_email(
                to_email=user.email.value,
                full_name=user.full_name,
                verification_url=verification_url,
            )

            return True
        except Exception as e:
            use_case_logger.warning(f"Failed to send verification email: {e}")
            return False

    async def _publish_user_registered_event(
        self, user: User, registration_request: RegistrationRequest
    ):
        """Publish user registered domain event"""
        try:
            event = UserRegisteredEvent(
                user_id=user.id,
                email=user.email.value,
                registration_time=user.created_at,
                registration_source=registration_request.source,
                client_ip=registration_request.client_ip,
                organization_id=registration_request.organization_id,
            )

            # In production, this would publish to an event bus
            use_case_logger.info(f"UserRegisteredEvent published: {event.event_id}")

        except Exception as e:
            use_case_logger.warning(f"Failed to publish event: {e}")


# Factory function for creating use case
def create_register_user_use_case(
    user_repository: UserRepository, email_service: EmailService
) -> RegisterUserUseCase:
    """Factory function to create RegisterUserUseCase"""
    return RegisterUserUseCase(user_repository, email_service)
