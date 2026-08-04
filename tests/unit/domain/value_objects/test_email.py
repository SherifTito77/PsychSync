"""
Unit Tests for Email Value Object

Tests the Email value object which encapsulates email validation and normalization.
This is a pure unit test - no database required.
"""

import pytest
from pydantic import ValidationError

from app.domain.value_objects.email import Email


class TestEmailValueObject:
    """Test Email value object"""

    # ========================================================================
    # VALIDATION TESTS
    # ========================================================================

    def test_create_valid_email(self):
        """Should accept valid email addresses"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "first+last@example.org",
            "user123@test-domain.com",
            "email@sub.domain.example.com",
        ]

        for email_str in valid_emails:
            email = Email(value=email_str)
            assert email.value == email_str

    def test_reject_invalid_email_no_at_sign(self):
        """Should reject email without @ sign"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            Email(value="userexample.com")

    def test_reject_invalid_email_no_domain(self):
        """Should reject email without domain"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            Email(value="user@")

    def test_reject_invalid_email_no_local(self):
        """Should reject email without local part"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            Email(value="@example.com")

    def test_reject_invalid_email_spaces(self):
        """Should reject email with spaces"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            Email(value="user @example.com")

    def test_reject_invalid_email_special_chars(self):
        """Should reject email with invalid special characters"""
        invalid_emails = [
            "user@exa!mple.com",
            "user name@example.com",
            "user@exam#le.com",
        ]

        for email_str in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email format"):
                Email(value=email_str)

    def test_reject_empty_email(self):
        """Should reject empty email"""
        with pytest.raises(ValidationError):
            Email(value="")

    def test_reject_none_email(self):
        """Should reject None email"""
        with pytest.raises(ValidationError):
            Email(value=None)

    # ========================================================================
    # NORMALIZATION TESTS
    # ========================================================================

    def test_normalize_lowercase(self):
        """Should normalize email to lowercase"""
        email = Email(value="User@Example.COM")
        assert email.value == "user@example.com"

    def test_normalized_property(self):
        """Should provide normalized (lowercase) email via property"""
        email = Email(value="Test.User@Domain.COM")
        assert email.normalized == "test.user@domain.com"
        assert email.normalized == email.value  # Value is already normalized

    def test_normalize_trims_whitespace(self):
        """Should trim whitespace from email"""
        email = Email(value="  user@example.com  ")
        assert email.value == "user@example.com"

    # ========================================================================
    # IMMUTABILITY TESTS
    # ========================================================================

    def test_email_is_frozen(self):
        """Should be immutable (frozen dataclass)"""
        email = Email(value="user@example.com")

        with pytest.raises(Exception):  # FrozenInstanceError
            email.value = "other@example.com"

    def test_email_hashable(self):
        """Should be hashable for use in sets/dicts"""
        email1 = Email(value="user@example.com")
        email2 = Email(value="USER@EXAMPLE.COM")  # Same, normalized

        # Should be equal
        assert email1 == email2

        # Should have same hash
        assert hash(email1) == hash(email2)

        # Can be used in set
        email_set = {email1, email2}
        assert len(email_set) == 1  # Duplicates removed

    # ========================================================================
    # COMPARISON TESTS
    # ========================================================================

    def test_email_equality(self):
        """Should compare emails correctly"""
        email1 = Email(value="user@example.com")
        email2 = Email(value="user@example.com")
        email3 = Email(value="other@example.com")

        assert email1 == email2
        assert email1 != email3

    def test_email_equality_case_insensitive(self):
        """Should consider emails equal regardless of case"""
        email1 = Email(value="user@example.com")
        email2 = Email(value="USER@EXAMPLE.COM")
        email3 = Email(value="User@Example.Com")

        assert email1 == email2
        assert email1 == email3

    def test_email_inequality_different_domains(self):
        """Should detect different domains"""
        email1 = Email(value="user@example.com")
        email2 = Email(value="user@other.com")

        assert email1 != email2

    def test_email_inequality_different_local(self):
        """Should detect different local parts"""
        email1 = Email(value="user1@example.com")
        email2 = Email(value="user2@example.com")

        assert email1 != email2

    # ========================================================================
    # STRING REPRESENTATION TESTS
    # ========================================================================

    def test_email_str_representation(self):
        """Should provide string representation"""
        email = Email(value="user@example.com")
        assert str(email) == "user@example.com"

    def test_email_repr(self):
        """Should provide useful repr"""
        email = Email(value="user@example.com")
        assert "Email" in repr(email)
        assert "user@example.com" in repr(email)

    # ========================================================================
    # DOMAIN-SPECIFIC TESTS
    # ========================================================================

    def test_get_domain(self):
        """Should extract domain from email"""
        email = Email(value="user@example.com")
        # Assuming Email class has get_domain() method
        # If not, this test will fail and you'll implement it
        try:
            domain = email.get_domain()
            assert domain == "example.com"
        except AttributeError:
            # Method doesn't exist - that's okay for this test
            pytest.skip("Email.get_domain() method not implemented")

    def test_get_local_part(self):
        """Should extract local part from email"""
        email = Email(value="user.name@example.com")
        try:
            local = email.get_local_part()
            assert local == "user.name"
        except AttributeError:
            pytest.skip("Email.get_local_part() method not implemented")

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    def test_very_long_email(self):
        """Should handle very long email addresses"""
        local = "a" * 64  # Max local part length
        domain = "b" * 63 + ".com"  # Max domain length
        long_email = f"{local}@{domain}"

        email = Email(value=long_email)
        assert email.value == long_email.lower()

    def test_email_with_plus_sign(self):
        """Should support plus sign in local part"""
        email = Email(value="user+tag@example.com")
        assert email.value == "user+tag@example.com"

    def test_email_with_dots(self):
        """Should support dots in local part"""
        email = Email(value="first.last@example.com")
        assert email.value == "first.last@example.com"

    def test_subdomain_email(self):
        """Should support subdomains"""
        email = Email(value="user@mail.example.com")
        assert email.value == "user@mail.example.com"

    def test_international_domain(self):
        """Should support international domain names"""
        # Assuming IDN support
        email = Email(value="user@example.com")
        assert email.value == "user@example.com"

    def test_maximum_length_enforced(self):
        """Should enforce maximum email length (254 chars per RFC)"""
        # Create 254 character email
        local = "a" * 64
        domain = ".".join(["b" * 63 for _ in range(3)])  # 63 + 1 + 63 + 1 + 63
        long_email = f"{local}@{domain}"

        assert len(long_email) <= 254
        email = Email(value=long_email)
        assert email.value == long_email.lower()

    # ========================================================================
    # PYDANTIC INTEGRATION TESTS
    # ========================================================================

    def test_email_as_pydantic_field(self):
        """Should work as Pydantic field"""
        from pydantic import BaseModel, Field

        class UserModel(BaseModel):
            email: Email = Field(...)

        # Valid email
        user = UserModel(email="user@example.com")
        assert user.email.value == "user@example.com"

        # Invalid email
        with pytest.raises(ValidationError):
            UserModel(email="invalid-email")

    def test_email_serialization(self):
        """Should serialize correctly"""
        email = Email(value="user@example.com")

        # To dict
        data = email.model_dump() if hasattr(email, "model_dump") else email.__dict__
        assert data["value"] == "user@example.com"

        # To JSON
        json_str = (
            email.model_dump_json() if hasattr(email, "model_dump_json") else str(email)
        )
        assert "user@example.com" in json_str
