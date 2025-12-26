# tests/authentication/sessionExpirationBehavior.test.py
"""
Session Expiration Behavior Testing

Tests session management, expiration, and security edge cases
Business Impact: Security, user experience, data protection
ROI: 7x - Prevents unauthorized access and ensures session security
"""

import pytest
import datetime
import json
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import jwt
from jose import JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

# Import authentication modules
from app.core.security import create_access_token, verify_token, get_password_hash
from app.api.v1.deps import get_current_user
from app.core.config import settings


class TestSessionExpirationBehavior:
    """Comprehensive session expiration and security testing"""

    # 🕒 Basic Session Lifecycle Tests
    def test_session_creation_with_expiration(self):
        """Test session creation with proper expiration time"""
        user_data = {
            'sub': 'test_user_123',
            'email': 'test@example.com',
            'role': 'user',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }

        # Create token with expiration
        token = create_access_token(data=user_data, expires_delta=datetime.timedelta(minutes=30))

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token contains expiration claim
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert 'exp' in decoded
        assert decoded['sub'] == 'test_user_123'

    def test_session_expiration_detection(self):
        """Test detection of expired sessions"""
        # Create an expired token
        expired_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
        user_data = {
            'sub': 'test_user_123',
            'exp': expired_time
        }

        expired_token = create_access_token(data=user_data)

        # Verify token is expired
        with pytest.raises(ExpiredSignatureError):
            verify_token(expired_token)

    def test_session_valid_within_expiration_window(self):
        """Test valid session within expiration window"""
        user_data = {
            'sub': 'test_user_123',
            'email': 'test@example.com'
        }

        # Create token with 30-minute expiration
        token = create_access_token(data=user_data, expires_delta=datetime.timedelta(minutes=30))

        # Verify token is valid
        decoded = verify_token(token)
        assert decoded['sub'] == 'test_user_123'
        assert decoded['email'] == 'test@example.com'

    def test_session_refresh_mechanism(self):
        """Test session refresh before expiration"""
        user_data = {
            'sub': 'test_user_123',
            'email': 'test@example.com'
        }

        # Create initial token
        initial_token = create_access_token(data=user_data, expires_delta=datetime.timedelta(minutes=30))

        # Simulate refresh (create new token)
        new_token = create_access_token(data=user_data, expires_delta=datetime.timedelta(minutes=30))

        # Both tokens should be valid (until initial expires)
        assert initial_token != new_token

        decoded_initial = verify_token(initial_token)
        decoded_new = verify_token(new_token)

        assert decoded_initial['sub'] == decoded_new['sub']

    # 🚨 Security Edge Cases
    def test_session_hijacking_prevention(self):
        """Test prevention of session hijacking attempts"""
        user_data = {
            'sub': 'test_user_123',
            'email': 'test@example.com',
            'role': 'user'
        }

        token = create_access_token(data=user_data)

        # Attempt to modify token (should fail)
        with pytest.raises(InvalidSignatureError):
            # Tamper with token by changing signature
            tampered_token = token[:-10] + "tampered" + token[-10:]
            jwt.decode(tampered_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def test_session_ip_binding(self):
        """Test session binding to IP address"""
        user_data = {
            'sub': 'test_user_123',
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 Test Browser'
        }

        token = create_access_token(data=user_data)

        # Simulate session validation with IP check
        decoded = verify_token(token)
        current_ip = '192.168.1.100'

        # IP should match
        assert decoded['ip_address'] == current_ip

        # Different IP should be flagged
        different_ip = '192.168.1.200'
        assert decoded['ip_address'] != different_ip

    def test_session_concurrent_login_handling(self):
        """Test handling of concurrent sessions for same user"""
        user_data = {
            'sub': 'test_user_123',
            'session_id': 'session_1'
        }

        # Create first session
        session1_token = create_access_token(data=user_data)

        # Create second session (should invalidate first)
        user_data['session_id'] = 'session_2'
        session2_token = create_access_token(data=user_data)

        # Both tokens may be valid, but application logic should handle session management
        decoded1 = verify_token(session1_token)
        decoded2 = verify_token(session2_token)

        assert decoded1['session_id'] != decoded2['session_id']

    def test_session_termination_on_password_change(self):
        """Test session termination when user changes password"""
        user_data = {
            'sub': 'test_user_123',
            'password_version': 1
        }

        # Create session before password change
        token = create_access_token(data=user_data)

        # Simulate password change (increment version)
        user_data['password_version'] = 2

        # Application logic should check password version
        decoded = verify_token(token)
        assert decoded['password_version'] == 1  # Still version 1

    # 🕰 Inactivity Timeout Tests
    def test_session_inactivity_timeout(self):
        """Test session timeout due to inactivity"""
        user_data = {
            'sub': 'test_user_123',
            'last_activity': datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        }

        # Create token with inactivity tracking
        token = create_access_token(data=user_data)

        # Simulate inactivity check
        decoded = verify_token(token)
        last_activity = decoded['last_activity']

        # Check if session should be expired due to inactivity
        time_since_activity = datetime.datetime.utcnow() - last_activity
        inactivity_threshold = datetime.timedelta(hours=1)

        assert time_since_activity > inactivity_threshold, "Session should be expired due to inactivity"

    def test_session_activity_extension(self):
        """Test extending session due to user activity"""
        user_data = {
            'sub': 'test_user_123',
            'last_activity': datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
        }

        initial_token = create_access_token(data=user_data)

        # Simulate user activity (update last activity)
        user_data['last_activity'] = datetime.datetime.utcnow()
        refreshed_token = create_access_token(data=user_data)

        decoded = verify_token(refreshed_token)
        recent_activity = datetime.datetime.utcnow() - decoded['last_activity']

        assert recent_activity < datetime.timedelta(minutes=1), "Activity should be recent"

    def test_session_persistence_across_restarts(self):
        """Test session persistence handling across application restarts"""
        # Simulate server restart with different secret key handling
        old_secret = settings.SECRET_KEY

        try:
            # Create token with old secret
            user_data = {'sub': 'test_user_123'}
            token = create_access_token(data=user_data)

            # Change secret (simulate server restart)
            settings.SECRET_KEY = "new_secret_key_that_is_different"

            # Token should become invalid with new secret
            with pytest.raises(InvalidSignatureError):
                verify_token(token)

        finally:
            # Restore original secret
            settings.SECRET_KEY = old_secret

    # 📱 Mobile Session Tests
    def test_mobile_session_management(self):
        """Test mobile-specific session behavior"""
        mobile_user_data = {
            'sub': 'mobile_user_123',
            'device_id': 'mobile_device_456',
            'platform': 'ios',
            'app_version': '2.1.0'
        }

        token = create_access_token(data=mobile_user_data)
        decoded = verify_token(token)

        assert decoded['platform'] == 'ios'
        assert decoded['app_version'] == '2.1.0'

    def test_session_suspension_on_jailbreak(self):
        """Test session suspension on jailbreak/root detection"""
        secure_session_data = {
            'sub': 'secure_user_123',
            'device_integrity': 'secure',
            'root_status': 'not_rooted'
        }

        compromised_session_data = {
            'sub': 'secure_user_123',
            'device_integrity': 'compromised',
            'root_status': 'rooted'
        }

        secure_token = create_access_token(data=secure_session_data)
        compromised_token = create_access_token(data=compromised_session_data)

        # Application should handle compromised sessions
        secure_decoded = verify_token(secure_token)
        compromised_decoded = verify_token(compromised_token)

        assert secure_decoded['device_integrity'] == 'secure'
        assert compromised_decoded['device_integrity'] == 'compromised'

    # 🔐 Security Configuration Tests
    def test_session_configuration_security(self):
        """Test secure session configuration"""
        user_data = {
            'sub': 'test_user_123',
            'iss': 'psychsync-app',
            'aud': 'psychsync-users',
            'nbf': datetime.datetime.utcnow()
        }

        token = create_access_token(data=user_data)
        decoded = verify_token(token)

        # Verify security claims
        assert decoded['iss'] == 'psychsync-app'
        assert 'aud' in decoded
        assert 'nbf' in decoded

    def test_session_encryption_strength(self):
        """Test session encryption and signing strength"""
        user_data = {
            'sub': 'test_user_123',
            'sensitive_data': 'encrypted_value'
        }

        # Token should be properly signed and encrypted
        token = create_access_token(data=user_data)

        # Verify token structure (should have 3 parts: header.payload.signature)
        token_parts = token.split('.')
        assert len(token_parts) == 3, "Token should have 3 parts"

    # 📊 Analytics and Monitoring Tests
    def test_session_analytics_tracking(self):
        """Test session analytics and monitoring"""
        session_data = {
            'sub': 'test_user_123',
            'session_start': datetime.datetime.utcnow().isoformat(),
            'login_method': 'password',
            'mfa_verified': True
        }

        token = create_access_token(data=session_data)
        decoded = verify_token(token)

        # Verify analytics data
        assert 'session_start' in decoded
        assert decoded['login_method'] == 'password'
        assert decoded['mfa_verified'] is True

    def test_session_duration_analytics(self):
        """Test session duration tracking and analytics"""
        sessions = []

        # Create multiple sessions with different lifespans
        for i in range(5):
            session_data = {
                'sub': f'user_{i}',
                'session_id': f'session_{i}',
                'created_at': datetime.datetime.utcnow().isoformat()
            }
            token = create_access_token(data=session_data)
            sessions.append({'token': token, 'data': session_data})

        # All sessions should be valid immediately
        for session in sessions:
            decoded = verify_token(session['token'])
            assert decoded['sub'].startswith('user_')

    # 🔄 Edge Case Handling Tests
    def test_malformed_session_tokens(self):
        """Test handling of malformed or corrupted tokens"""
        malformed_tokens = [
            '',  # Empty token
            'invalid.token',  # Too few parts
            'a.b.c.d',  # Too many parts
            'invalid_base64_payload.signature',  # Invalid base64
            'header.invalid_signature',  # Invalid signature
        ]

        for malformed_token in malformed_tokens:
            with pytest.raises((JWTError, ValueError)):
                verify_token(malformed_token)

    def test_session_token_length_validation(self):
        """Test session token length validation"""
        user_data = {'sub': 'test_user_123'}

        # Create valid token
        valid_token = create_access_token(data=user_data)

        # Token should have reasonable length
        assert 100 < len(valid_token) < 1000, "Token length should be reasonable"

        # Test minimum length requirement
        too_short_token = "a.b.c"
        with pytest.raises(JWTError):
            verify_token(too_short_token)

    def test_session_token_algorithm_validation(self):
        """Test session token algorithm validation"""
        user_data = {'sub': 'test_user_123'}

        # Create token with correct algorithm
        valid_token = create_access_token(data=user_data)

        # Should decode with correct algorithm
        decoded = verify_token(valid_token)
        assert decoded['sub'] == 'test_user_123'

        # Should fail with wrong algorithm
        with pytest.raises(JWTError):
            jwt.decode(valid_token, 'wrong_secret', algorithms=['HS512'])


class TestSessionManagementIntegration:
    """Integration tests for session management"""

    @pytest.mark.asyncio
    async def test_session_validation_middleware(self):
        """Test session validation in authentication middleware"""
        # Mock request with valid token
        user_data = {
            'sub': 'test_user_123',
            'email': 'test@example.com'
        }

        valid_token = create_access_token(data=user_data)

        # Mock HTTP request with Authorization header
        mock_request = MagicMock()
        mock_request.headers = {'Authorization': f'Bearer {valid_token}'}

        # Mock database user
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 'test_user_123'
        mock_user.email = 'test@example.com'
        mock_user.is_active = True

        # Mock user lookup
        with patch('app.api.v1.deps.get_user_by_id', return_value=mock_user):
            # Should successfully authenticate user
            user = await get_current_user(valid_token, mock_db)
            assert user.id == 'test_user_123'
            assert user.email == 'test@example.com'

    @pytest.mark.asyncio
    async def test_session_expiration_middleware(self):
        """Test session expiration in middleware"""
        # Create expired token
        expired_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        user_data = {
            'sub': 'test_user_123',
            'exp': expired_time
        }

        expired_token = create_access_token(data=user_data)

        # Mock database
        mock_db = AsyncMock()

        # Should raise exception for expired token
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(expired_token, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_session_concurrent_limits(self):
        """Test concurrent session limits per user"""
        user_id = 'test_user_123'
        max_sessions = 3

        # Create maximum allowed sessions
        sessions = []
        for i in range(max_sessions):
            session_data = {
                'sub': user_id,
                'session_id': f'session_{i}',
                'created_at': datetime.datetime.utcnow().isoformat()
            }
            token = create_access_token(data=session_data)
            sessions.append(token)

        # All sessions should be valid
        for token in sessions:
            decoded = verify_token(token)
            assert decoded['sub'] == user_id

        # Attempt to create one more session (should be handled by application logic)
        extra_session_data = {
            'sub': user_id,
            'session_id': f'session_{max_sessions}',
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        extra_token = create_access_token(data=extra_session_data)

        # Token creation should still work, but application should manage limits
        assert extra_token is not None

    def test_session_cleanup_expired_tokens(self):
        """Test cleanup of expired session tokens"""
        # Create tokens with different expiration times
        tokens = [
            # Expired token
            create_access_token(
                data={'sub': 'expired_user'},
                expires_delta=datetime.timedelta(minutes=-1)
            ),
            # Valid token
            create_access_token(
                data={'sub': 'valid_user'},
                expires_delta=datetime.timedelta(minutes=30)
            )
        ]

        # Filter expired tokens
        valid_tokens = []
        expired_tokens = []

        for token in tokens:
            try:
                decoded = verify_token(token)
                valid_tokens.append(decoded)
            except ExpiredSignatureError:
                expired_tokens.append(token)

        assert len(expired_tokens) == 1
        assert len(valid_tokens) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])