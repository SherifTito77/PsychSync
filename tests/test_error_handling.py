"""
Tests for structured error handling

Tests all custom exception classes to ensure:
- Correct error codes
- Correct status codes
- Proper error details
- Correct error response format
"""

import pytest

from app.core.exceptions import (  # Authentication & Security; Assessment errors; Team errors; Database errors; Billing errors; Base exception
    AccountLockedError,
    AssessmentExpiredError,
    AssessmentLimitExceededError,
    AssessmentLockedError,
    AssessmentNotFoundError,
    DuplicateRecordError,
    ErrorCode,
    ForbiddenError,
    InvalidCredentialsError,
    InvalidEmailError,
    MFARRequiredError,
    MissingFieldError,
    PaymentFailedError,
    PsychSyncException,
    RateLimitExceededError,
    RecordNotFoundError,
    ResponseAlreadySubmittedError,
    SessionExpiredError,
    TeamAccessDeniedError,
    TeamLimitExceededError,
    TeamNotFoundError,
    UpgradeRequiredError,
    UserInactiveError,
    WeakPasswordError,
)


class TestAuthenticationErrors:
    """Test authentication and security error exceptions"""

    def test_account_locked_error(self):
        """Test AccountLockedError"""
        exc = AccountLockedError()

        assert exc.error_code == ErrorCode.ACCOUNT_LOCKED
        assert exc.status_code == 403
        assert exc.message == "Account has been locked"
        assert isinstance(exc.details, dict)

    def test_session_expired_error(self):
        """Test SessionExpiredError"""
        exc = SessionExpiredError()

        assert exc.error_code == ErrorCode.SESSION_EXPIRED
        assert exc.status_code == 401
        assert "expired" in exc.message.lower()

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError"""
        exc = RateLimitExceededError(retry_after=60, limit=100)

        assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED_AUTH
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60
        assert exc.details["limit"] == 100
        assert "60" in exc.message

    def test_mfa_required_error(self):
        """Test MFARRequiredError"""
        exc = MFARequiredError()

        assert exc.error_code == ErrorCode.MFA_REQUIRED
        assert exc.status_code == 401
        assert "MFA" in exc.message

    def test_weak_password_error(self):
        """Test WeakPasswordError"""
        requirements = {
            "min_length": 8,
            "requires_uppercase": True,
            "requires_number": True,
        }
        exc = WeakPasswordError(requirements=requirements)

        assert exc.error_code == ErrorCode.WEAK_PASSWORD
        assert exc.status_code == 400
        assert exc.details["requirements"] == requirements

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError"""
        exc = InvalidCredentialsError()

        assert exc.error_code == ErrorCode.INVALID_CREDENTIALS
        assert exc.status_code == 401
        assert "credentials" in exc.message.lower()

    def test_forbidden_error(self):
        """Test ForbiddenError"""
        message = "You do not have permission"
        exc = ForbiddenError(message=message)

        assert exc.error_code == ErrorCode.FORBIDDEN
        assert exc.status_code == 403
        assert exc.message == message

    def test_missing_field_error(self):
        """Test MissingFieldError"""
        exc = MissingFieldError(field="email")

        assert exc.error_code == ErrorCode.MISSING_REQUIRED_FIELD
        assert exc.status_code == 422
        assert exc.details["field"] == "email"
        assert "email" in exc.message

    def test_invalid_email_error(self):
        """Test InvalidEmailError"""
        exc = InvalidEmailError(email="invalid-email")

        assert exc.error_code == ErrorCode.INVALID_EMAIL
        assert exc.status_code == 422
        assert exc.details["email"] == "invalid-email"


class TestAssessmentErrors:
    """Test assessment-related error exceptions"""

    def test_assessment_not_found_error(self):
        """Test AssessmentNotFoundError"""
        assessment_id = "123e4567-e89b-12d3-a456-426614174000"
        exc = AssessmentNotFoundError(assessment_id=assessment_id)

        assert exc.error_code == ErrorCode.ASSESSMENT_NOT_FOUND
        assert exc.status_code == 404
        assert exc.details["assessment_id"] == assessment_id
        assert assessment_id in exc.message

    def test_assessment_expired_error(self):
        """Test AssessmentExpiredError"""
        assessment_id = "123"
        expiry_date = "2026-01-01T00:00:00Z"
        exc = AssessmentExpiredError(
            assessment_id=assessment_id, expiry_date=expiry_date
        )

        assert exc.error_code == ErrorCode.ASSESSMENT_EXPIRED
        assert exc.status_code == 410
        assert exc.details["assessment_id"] == assessment_id
        assert exc.details["expiry_date"] == expiry_date
        assert expiry_date in exc.message

    def test_assessment_limit_exceeded_error(self):
        """Test AssessmentLimitExceededError"""
        limit = 10
        exc = AssessmentLimitExceededError(limit=limit)

        assert exc.error_code == ErrorCode.ASSESSMENT_LIMIT_EXCEEDED
        assert exc.status_code == 429
        assert exc.details["limit"] == limit
        assert str(limit) in exc.message

    def test_assessment_locked_error(self):
        """Test AssessmentLockedError"""
        assessment_id = "456"
        exc = AssessmentLockedError(assessment_id=assessment_id)

        assert exc.error_code == ErrorCode.ASSESSMENT_LOCKED
        assert exc.status_code == 423
        assert exc.details["assessment_id"] == assessment_id
        assert "locked" in exc.message.lower()

    def test_response_already_submitted_error(self):
        """Test ResponseAlreadySubmittedError"""
        assessment_id = "789"
        exc = ResponseAlreadySubmittedError(assessment_id=assessment_id)

        assert exc.error_code == ErrorCode.RESPONSE_ALREADY_SUBMITTED
        assert exc.status_code == 409
        assert exc.details["assessment_id"] == assessment_id
        assert "already submitted" in exc.message.lower()


class TestTeamErrors:
    """Test team-related error exceptions"""

    def test_team_not_found_error(self):
        """Test TeamNotFoundError"""
        team_id = "team-123"
        exc = TeamNotFoundError(team_id=team_id)

        assert exc.error_code == ErrorCode.TEAM_NOT_FOUND
        assert exc.status_code == 404
        assert exc.details["team_id"] == team_id
        assert team_id in exc.message

    def test_team_access_denied_error(self):
        """Test TeamAccessDeniedError"""
        team_id = "team-456"
        user_id = "user-789"
        exc = TeamAccessDeniedError(team_id=team_id, user_id=user_id)

        assert exc.error_code == ErrorCode.TEAM_ACCESS_DENIED
        assert exc.status_code == 403
        assert exc.details["team_id"] == team_id
        assert exc.details["user_id"] == user_id
        assert "permission" in exc.message.lower()

    def test_team_limit_exceeded_error(self):
        """Test TeamLimitExceededError"""
        limit = 5
        exc = TeamLimitExceededError(limit=limit)

        assert exc.error_code == ErrorCode.TEAM_LIMIT_EXCEEDED
        assert exc.status_code == 429
        assert exc.details["limit"] == limit
        assert str(limit) in exc.message


class TestDatabaseErrors:
    """Test database-related error exceptions"""

    def test_record_not_found_error(self):
        """Test RecordNotFoundError"""
        resource = "User"
        identifier = "user-123"
        exc = RecordNotFoundError(resource=resource, identifier=identifier)

        assert exc.error_code == ErrorCode.RECORD_NOT_FOUND
        assert exc.status_code == 404
        assert exc.details["resource"] == resource
        assert exc.details["identifier"] == identifier
        assert resource in exc.message
        assert identifier in exc.message

    def test_duplicate_record_error(self):
        """Test DuplicateRecordError"""
        resource = "Team"
        field = "name"
        value = "Engineering"
        exc = DuplicateRecordError(resource=resource, field=field, value=value)

        assert exc.error_code == ErrorCode.DUPLICATE_RECORD
        assert exc.status_code == 409
        assert exc.details["resource"] == resource
        assert exc.details["field"] == field
        assert exc.details["value"] == value


class TestBillingErrors:
    """Test billing-related error exceptions"""

    def test_payment_failed_error(self):
        """Test PaymentFailedError"""
        reason = "Card declined"
        exc = PaymentFailedError(reason=reason)

        assert exc.error_code == ErrorCode.PAYMENT_FAILED
        assert exc.status_code == 402
        assert exc.details["reason"] == reason

    def test_upgrade_required_error(self):
        """Test UpgradeRequiredError"""
        feature = "advanced_analytics"
        required_plan = "Professional"
        exc = UpgradeRequiredError(feature=feature, required_plan=required_plan)

        assert exc.error_code == ErrorCode.UPGRADE_REQUIRED
        assert exc.status_code == 402
        assert exc.details["feature"] == feature
        assert exc.details["required_plan"] == required_plan
        assert feature in exc.message
        assert required_plan in exc.message


class TestErrorResponseFormat:
    """Test error response format"""

    def test_to_dict_method(self):
        """Test PsychSyncException.to_dict() method"""
        exc = TeamNotFoundError(team_id="team-123")

        error_dict = exc.to_dict()

        assert error_dict["error"] == True
        assert error_dict["error_code"] == "BIZ_4300"
        assert "message" in error_dict
        assert error_dict["status_code"] == 404
        assert "details" in error_dict
        assert "timestamp" in error_dict

    def test_to_dict_includes_details(self):
        """Test that to_dict includes all details"""
        exc = RateLimitExceededError(retry_after=60, limit=100)

        error_dict = exc.to_dict()

        assert error_dict["details"]["retry_after"] == 60
        assert error_dict["details"]["limit"] == 100

    def test_to_dict_timestamp_format(self):
        """Test that timestamp is ISO format"""
        exc = AssessmentNotFoundError(assessment_id="123")

        error_dict = exc.to_dict()

        # Should be ISO format datetime string
        assert isinstance(error_dict["timestamp"], str)
        assert "T" in error_dict["timestamp"]  # ISO format indicator


class TestExceptionInheritance:
    """Test exception inheritance and type checking"""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from PsychSyncException"""
        exceptions_to_test = [
            TeamNotFoundError,
            TeamAccessDeniedError,
            AssessmentNotFoundError,
            AssessmentExpiredError,
            InvalidCredentialsError,
            RateLimitExceededError,
            WeakPasswordError,
            ForbiddenError,
            MissingFieldError,
            PaymentFailedError,
            UpgradeRequiredError,
        ]

        for exc_class in exceptions_to_test:
            assert issubclass(exc_class, PsychSyncException)

    def test_exception_can_be_caught_as_base(self):
        """Test that custom exceptions can be caught as PsychSyncException"""
        try:
            raise TeamNotFoundError(team_id="123")
        except PsychSyncException as exc:
            assert exc.error_code == ErrorCode.TEAM_NOT_FOUND


class TestErrorCodeEnum:
    """Test ErrorCode enum values"""

    def test_error_codes_are_strings(self):
        """Test that all error codes are strings"""
        codes_to_test = [
            ErrorCode.TEAM_NOT_FOUND,
            ErrorCode.ASSESSMENT_NOT_FOUND,
            ErrorCode.INVALID_CREDENTIALS,
            ErrorCode.RATE_LIMIT_EXCEEDED_AUTH,
            ErrorCode.WEAK_PASSWORD,
        ]

        for code in codes_to_test:
            assert isinstance(code.value, str)

    def test_error_code_format(self):
        """Test that error codes follow CATEGORY_NUMBER format"""
        codes_to_test = [
            ErrorCode.TEAM_NOT_FOUND,  # BIZ_4300
            ErrorCode.ASSESSMENT_NOT_FOUND,  # BIZ_4100
            ErrorCode.INVALID_CREDENTIALS,  # AUTH_1002
            ErrorCode.RATE_LIMIT_EXCEEDED_AUTH,  # AUTH_1106
        ]

        for code in codes_to_test:
            value = code.value
            assert "_" in value  # Should have underscore
            parts = value.split("_")
            assert len(parts) == 2  # Should be 2 parts
            assert parts[1].isdigit()  # Second part should be number


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    def test_exception_with_custom_details(self):
        """Test exception with custom details dict"""
        custom_details = {"custom_field": "custom_value", "another_field": 123}
        exc = PsychSyncException(
            message="Custom error",
            error_code=ErrorCode.GENERIC_ERROR,
            details=custom_details,
        )

        assert exc.details == custom_details

    def test_exception_with_empty_details(self):
        """Test exception with no details"""
        exc = InvalidCredentialsError()

        assert exc.details == {}

    def test_exception_message_can_be_overridden(self):
        """Test that exception message can be customized"""
        custom_message = "Custom not found message"
        exc = TeamNotFoundError(team_id="123")
        exc.message = custom_message

        assert exc.message == custom_message


@pytest.mark.parametrize(
    "exception_class,error_code,expected_status",
    [
        (TeamNotFoundError, ErrorCode.TEAM_NOT_FOUND, 404),
        (AssessmentNotFoundError, ErrorCode.ASSESSMENT_NOT_FOUND, 404),
        (InvalidCredentialsError, ErrorCode.INVALID_CREDENTIALS, 401),
        (ForbiddenError, ErrorCode.FORBIDDEN, 403),
        (RateLimitExceededError, ErrorCode.RATE_LIMIT_EXCEEDED_AUTH, 429),
        (WeakPasswordError, ErrorCode.WEAK_PASSWORD, 400),
        (MissingFieldError, ErrorCode.MISSING_REQUIRED_FIELD, 422),
    ],
)
def test_exception_status_codes(exception_class, error_code, expected_status):
    """Parametrized test for exception status codes"""
    # Create exception with minimal args
    if exception_class == RateLimitExceededError:
        exc = exception_class(retry_after=60, limit=100)
    elif exception_class == MissingFieldError:
        exc = exception_class(field="test")
    elif exception_class == TeamNotFoundError:
        exc = exception_class(team_id="123")
    elif exception_class == AssessmentNotFoundError:
        exc = exception_class(assessment_id="123")
    else:
        exc = exception_class()

    assert exc.error_code == error_code
    assert exc.status_code == expected_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
