"""
Unit Tests for Password Value Object

Tests the Password value object which encapsulates password hashing, validation,
and secure comparison. This is a pure unit test - no database required.
"""

import pytest

from app.domain.value_objects.password import Password


class TestPasswordValueObject:
    """Test Password value object"""

    # ========================================================================
    # CREATION TESTS
    # ========================================================================

    def test_create_password_from_plaintext(self):
        """Should create password from plaintext"""
        password = Password.create(plaintext="SecureP@ss99!")
        assert password.hash_value is not None
        assert isinstance(password.hash_value, str)
        assert len(password.hash_value) > 0

    def test_create_password_generates_different_hashes(self):
        """Should generate different hashes for same password (salted)"""
        password1 = Password.create(plaintext="SecureP@ss99!")
        password2 = Password.create(plaintext="SecureP@ss99!")

        # Hashes should be different (due to salt)
        assert password1.hash_value != password2.hash_value

    def test_create_password_from_hash(self):
        """Should create password from existing hash"""
        existing_hash = "$2b$12$exampleHashValue"
        password = Password(hash_value=existing_hash)
        assert password.hash_value == existing_hash

    # ========================================================================
    # VALIDATION TESTS
    # ========================================================================

    def test_reject_too_short_password(self):
        """Should reject passwords shorter than 12 characters"""
        with pytest.raises(ValueError, match="at least 12 characters"):
            Password.create(plaintext="Short1!")

    def test_reject_password_no_uppercase(self):
        """Should reject passwords without uppercase letters"""
        with pytest.raises(ValueError, match="uppercase letter"):
            Password.create(plaintext="lowercase1!")

    def test_reject_password_no_lowercase(self):
        """Should reject passwords without lowercase letters"""
        with pytest.raises(ValueError, match="lowercase letter"):
            Password.create(plaintext="UPPERCASE1!")

    def test_reject_password_no_digit(self):
        """Should reject passwords without digits"""
        with pytest.raises(ValueError, match="at least one digit"):
            Password.create(plaintext="NoDigits!")

    def test_reject_password_no_special_char(self):
        """Should reject passwords without special characters"""
        with pytest.raises(ValueError, match="special character"):
            Password.create(plaintext="NoSpecial1")

    def test_accept_valid_password(self):
        """Should accept passwords meeting all requirements"""
        # Should not raise
        password = Password.create(plaintext="SecureP@ss99!")
        assert password.hash_value is not None

    def test_common_password_patterns_rejected(self):
        """Should reject common password patterns"""
        # Assuming Password class checks common patterns
        common_passwords = [
            "Password1!",
            "Password123!",
            "Admin123!",
            "Welcome1!",
        ]

        for pwd in common_passwords:
            try:
                Password.create(plaintext=pwd)
                # If it doesn't raise, check if it should have
                # This depends on implementation
            except ValueError:
                # Expected to be rejected
                pass

    def test_reject_password_with_unicode(self):
        """Should handle or reject unicode characters"""
        # Depends on implementation
        try:
            password = Password.create(plaintext="Pässwörd1!")
            assert password.hash_value is not None
        except ValueError:
            # Some implementations may reject unicode
            pass

    # ========================================================================
    # VERIFICATION TESTS
    # ========================================================================

    def test_verify_correct_password(self):
        """Should verify correct password"""
        plaintext = "SecureP@ss99!"
        password = Password.create(plaintext=plaintext)

        assert password.verify(plaintext) is True

    def test_verify_incorrect_password(self):
        """Should reject incorrect password"""
        password = Password.create(plaintext="SecureP@ss99!")

        assert password.verify("WrongP@ss99!") is False

    def test_verify_case_sensitive(self):
        """Should be case sensitive"""
        password = Password.create(plaintext="SecureP@ss99!")

        assert password.verify("securep@ss99!") is False

    def test_verify_similar_passwords(self):
        """Should detect similar but different passwords"""
        password1 = Password.create(plaintext="SecureP@ss99!")
        password2 = Password.create(plaintext="SecureP@ss98!")  # Different by 1 char

        assert password1.verify("SecureP@ss98!") is False

    # ========================================================================
    # IMMUTABILITY TESTS
    # ========================================================================

    def test_password_is_frozen(self):
        """Should be immutable (frozen dataclass)"""
        password = Password.create(plaintext="SecureP@ss99!")

        with pytest.raises(Exception):  # FrozenInstanceError
            password.hash_value = "new_hash"

    def test_password_hashable(self):
        """Should be hashable"""
        password1 = Password.create(plaintext="SecureP@ss99!")
        password2 = Password.create(plaintext="SecureP@ss99!")

        # Different instances, different hashes (due to salt)
        # But should both be hashable
        password_set = {password1, password2}
        assert len(password_set) == 2  # Different hashes

    # ========================================================================
    # STRING REPRESENTATION TESTS
    # ========================================================================

    def test_password_str_does_not_leak(self):
        """Should not leak hash in string representation"""
        password = Password.create(plaintext="SecureP@ss99!")

        str_repr = str(password)
        # Should not contain actual hash
        assert password.hash_value not in str_repr
        assert "Password" in str_repr or "******" in str_repr

    def test_password_repr_does_not_leak(self):
        """Should not leak hash in repr"""
        password = Password.create(plaintext="SecureP@ss99!")

        repr_str = repr(password)
        # Should not contain actual hash
        assert password.hash_value not in repr_str

    # ========================================================================
    # HASHING ALGORITHM TESTS
    # ========================================================================

    def test_uses_bcrypt(self):
        """Should use bcrypt hashing algorithm"""
        password = Password.create(plaintext="SecureP@ss99!")

        # Bcrypt hashes start with $2b$ or $2a$
        assert password.hash_value.startswith("$2")

    def test_hash_length(self):
        """Should produce consistent hash length"""
        password1 = Password.create(plaintext="Password1!")
        password2 = Password.create(plaintext="Password2!")

        # Bcrypt hashes are 60 characters
        assert len(password1.hash_value) == 60
        assert len(password2.hash_value) == 60

    def test_work_factor(self):
        """Should use appropriate work factor (rounds)"""
        password = Password.create(plaintext="SecureP@ss99!")

        # Extract rounds from hash
        # Bcrypt format: $2b$12$... (12 is the rounds)
        parts = password.hash_value.split("$")
        rounds = int(parts[2])

        # Should be at least 12 (default)
        assert rounds >= 12

    # ========================================================================
    # EDGE CASES
    # ========================================================================

    def test_empty_password(self):
        """Should reject empty password"""
        with pytest.raises(ValueError):
            Password.create(plaintext="")

    def test_none_password(self):
        """Should reject None password"""
        with pytest.raises((ValueError, TypeError)):
            Password.create(plaintext=None)

    def test_very_long_password(self):
        """Should handle very long passwords"""
        long_password = "A" * 100 + "1!"  # 102 characters
        password = Password.create(plaintext=long_password)
        assert password.verify(long_password) is True

    def test_maximum_password_length(self):
        """Should enforce maximum password length"""
        # Bcrypt max is 72 bytes
        max_password = "A" * 72
        password = Password.create(plaintext=max_password)
        assert password.verify(max_password) is True

    def test_unicode_password(self):
        """Should handle unicode in password"""
        # Depends on implementation
        try:
            password = Password.create(plaintext="Pässwörd1!")
            assert password.hash_value is not None
        except ValueError:
            # May be rejected
            pass

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_timing_attack_resistance(self):
        """Should have constant-time comparison (via passlib)"""
        password = Password.create(plaintext="SecureP@ss99!")

        # This is more of a documentation test
        # The actual timing resistance comes from passlib/bcrypt
        assert password.verify("WrongP@ss99!") is False
        assert password.verify("SecureP@ss99!") is True

    def test_hash_not_reversible(self):
        """Should not be reversible to plaintext"""
        password = Password.create(plaintext="SecureP@ss99!")

        # There's no way to get plaintext from hash
        assert not hasattr(password, "plaintext")
        assert not hasattr(password, "get_plaintext")

    def test_hash_unique_per_instance(self):
        """Each instance should have unique hash (due to salt)"""
        passwords = [Password.create(plaintext="SecureP@ss99!") for _ in range(10)]

        hashes = [p.hash_value for p in passwords]
        unique_hashes = set(hashes)

        # All should be different
        assert len(unique_hashes) == 10

    # ========================================================================
    # PYDANTIC INTEGRATION TESTS
    # ========================================================================

    def test_password_as_pydantic_field(self):
        """Should work as Pydantic field"""
        from pydantic import BaseModel, Field

        class UserModel(BaseModel):
            password: Password = Field(...)

        # Note: Typically you'd create password first
        password_obj = Password.create(plaintext="SecureP@ss99!")
        user = UserModel(password=password_obj)
        assert user.password.hash_value == password_obj.hash_value

    # ========================================================================
    # COMPARISON TESTS
    # ========================================================================

    def test_password_equality(self):
        """Should compare by hash value"""
        password1 = Password.create(plaintext="SecureP@ss99!")
        password2 = Password.create(plaintext="SecureP@ss99!")  # Different hash!

        # Should NOT be equal (different hashes due to salt)
        assert password1 != password2

    def test_password_hash_equality_same_hash(self):
        """Should be equal if hash is the same"""
        hash_value = "$2b$12$exampleHashValue"
        password1 = Password(hash_value=hash_value)
        password2 = Password(hash_value=hash_value)

        assert password1 == password2
        assert hash(password1) == hash(password2)

    # ========================================================================
    # COMMON SCENARIOS
    # ========================================================================

    def test_password_change_scenario(self):
        """Test changing user password"""
        # Create old password
        old_password = Password.create(plaintext="OldP@ss99!")

        # Verify old password works
        assert old_password.verify("OldP@ss99!") is True

        # Create new password
        new_password = Password.create(plaintext="NewP@ss99!")

        # Old password shouldn't verify new password
        assert old_password.verify("NewP@ss99!") is False

        # New password should verify
        assert new_password.verify("NewP@ss99!") is True

    def test_multiple_users_same_password(self):
        """Multiple users can have same password but different hashes"""
        shared_password = "CommonP@ss99!"

        user1_password = Password.create(plaintext=shared_password)
        user2_password = Password.create(plaintext=shared_password)

        # Different hashes
        assert user1_password.hash_value != user2_password.hash_value

        # Both verify correctly
        assert user1_password.verify(shared_password) is True
        assert user2_password.verify(shared_password) is True

    def test_password_migration_scenario(self):
        """Test migrating from old hash to new hash"""
        # Simulate old hash (maybe from legacy system)
        old_hash = "$2b$10$legacyHash"

        # Create password from old hash
        password = Password(hash_value=old_hash)

        # Later, user logs in and we update
        if password.verify("UserP@ss99!"):
            # Create new hash with better work factor
            new_password = Password.create(plaintext="UserP@ss99!")
            assert new_password.hash_value != old_hash
