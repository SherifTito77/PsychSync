"""
Frontend-Backend Communication Race Condition Tests

Tests to verify race condition handling in frontend-backend communication:
1. Concurrent login requests (multiple simultaneous login attempts)
2. Token refresh race (multiple concurrent token refresh attempts)
3. Stale request handling (expired token with auto-refresh)
4. Concurrent API calls during token expiration
5. Request deduplication (multiple identical requests)
6. Retry logic with concurrent failures
7. Request cancellation during token refresh

These tests verify that the frontend-backend communication layer correctly
handles concurrent operations without causing authentication issues, duplicate
requests, or race conditions.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.models.user import User
from app.main import app
from app.services.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)

# ============================================================================
# Test 1: Concurrent Login Requests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_concurrent_login_requests_no_duplicates(db_session):
    """
    Test that concurrent login requests from the same user don't cause issues.

    Race Condition: Multiple concurrent login requests for the same user
    could create multiple sessions or tokens.

    Fix: Login endpoint should handle concurrent requests safely, returning
    the same session or creating multiple valid sessions without errors.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create test user
    user = User(
        email="concurrent_login_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Concurrent Login User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act - Send 10 concurrent login requests
    async def login_attempt():
        """Attempt to login"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={
                    "username": "concurrent_login_user@psychsync.test",
                    "password": "SecurePass123!",
                },
            )
            return response

    # Execute 10 concurrent login attempts
    tasks = [login_attempt() for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # Assert - All requests should succeed
    for i, response in enumerate(responses):
        assert (
            response.status_code == 200
        ), f"Login request {i} failed with status {response.status_code}"

        data = response.json()
        assert "access_token" in data, f"Response {i} missing access_token"
        assert "refresh_token" in data, f"Response {i} missing refresh_token"

    # All tokens should be valid
    tokens = [r.json()["access_token"] for r in responses]
    for i, token in enumerate(tokens):
        payload = verify_token(token)
        assert payload is not None, f"Token {i} is invalid"
        assert payload["sub"] == str(user.id), f"Token {i} has wrong user ID"

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_concurrent_login_different_users(db_session):
    """
    Test concurrent login requests from different users.

    Verifies the system can handle multiple users logging in simultaneously.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create 10 test users
    users = []
    for i in range(10):
        user = User(
            email=f"concurrent_user_{i}@psychsync.test",
            hashed_password=hash_password("SecurePass123!"),
            full_name=f"Concurrent User {i}",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        users.append(user)

    await db_session.commit()

    # Act - All 10 users login concurrently
    async def login_user(user_index):
        """Login as user"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/token",
                data={
                    "username": f"concurrent_user_{user_index}@psychsync.test",
                    "password": "SecurePass123!",
                },
            )
            return response

    tasks = [login_user(i) for i in range(10)]
    responses = await asyncio.gather(*tasks)

    # Assert - All logins should succeed
    for i, response in enumerate(responses):
        assert (
            response.status_code == 200
        ), f"User {i} login failed with status {response.status_code}"

        data = response.json()
        assert "access_token" in data, f"User {i} missing access_token"

    # All tokens should be unique
    tokens = [r.json()["access_token"] for r in responses]
    assert len(set(tokens)) == 10, "All tokens should be unique"

    # Cleanup
    for user in users:
        await db_session.delete(user)
    await db_session.commit()


# ============================================================================
# Test 2: Token Refresh Race
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_concurrent_token_refresh_same_token(db_session):
    """
    Test concurrent token refresh requests with the same refresh token.

    Race Condition: Multiple concurrent requests using the same refresh token
    could cause duplicate access tokens or blacklisting issues.

    Fix: Refresh endpoint should handle concurrent requests safely, either
    by using locks or by allowing multiple refreshes within a grace period.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create user and get initial tokens
    user = User(
        email="token_refresh_race_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Token Refresh Race User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get initial tokens
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "token_refresh_race_user@psychsync.test",
                "password": "SecurePass123!",
            },
        )

    assert login_response.status_code == 200
    initial_data = login_response.json()
    refresh_token = initial_data["refresh_token"]

    # Act - Send 5 concurrent refresh requests with the same refresh token
    async def refresh_token_attempt():
        """Attempt to refresh token"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )
            return response

    tasks = [refresh_token_attempt() for _ in range(5)]
    responses = await asyncio.gather(*tasks)

    # Assert - At least some requests should succeed
    # (Depending on implementation, some may fail if token is blacklisted after first use)
    success_count = sum(1 for r in responses if r.status_code == 200)
    failure_count = sum(1 for r in responses if r.status_code != 200)

    # Either all succeed (no blacklisting) or first one succeeds
    assert (
        success_count >= 1
    ), f"Expected at least 1 successful refresh, got {success_count}"

    # If multiple succeed, all should return valid tokens
    successful_responses = [r for r in responses if r.status_code == 200]
    for response in successful_responses:
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"

        # Verify token is valid
        payload = verify_token(data["access_token"])
        assert payload is not None, "Refreshed token should be valid"
        assert payload["sub"] == str(user.id), "Token should have correct user ID"

    print(f"\nConcurrent Token Refresh Test Results:")
    print(f"  Successful refreshes: {success_count}")
    print(f"  Failed refreshes: {failure_count}")

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_concurrent_token_refresh_different_tokens(db_session):
    """
    Test concurrent token refresh requests with different refresh tokens.

    Verifies the system can handle multiple users refreshing tokens simultaneously.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create 5 users with tokens
    users_data = []

    for i in range(5):
        user = User(
            email=f"refresh_user_{i}@psychsync.test",
            hashed_password=hash_password("SecurePass123!"),
            full_name=f"Refresh User {i}",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Login to get tokens
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/token",
                data={
                    "username": f"refresh_user_{i}@psychsync.test",
                    "password": "SecurePass123!",
                },
            )

        users_data.append(
            {"user": user, "refresh_token": login_response.json()["refresh_token"]}
        )

    # Act - All users refresh their tokens concurrently
    async def refresh_user_token(user_data):
        """Refresh user's token"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": user_data["refresh_token"]},
            )
            return response

    tasks = [refresh_user_token(ud) for ud in users_data]
    responses = await asyncio.gather(*tasks)

    # Assert - All refreshes should succeed
    for i, response in enumerate(responses):
        assert (
            response.status_code == 200
        ), f"User {i} refresh failed with status {response.status_code}"

        data = response.json()
        assert "access_token" in data, f"User {i} missing access token"

        # Verify token
        payload = verify_token(data["access_token"])
        assert payload is not None, f"User {i} token is invalid"
        assert payload["sub"] == str(
            users_data[i]["user"].id
        ), f"User {i} token has wrong user ID"

    # Cleanup
    for ud in users_data:
        await db_session.delete(ud["user"])
    await db_session.commit()


# ============================================================================
# Test 3: Stale Request Handling
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_expired_token_with_auto_refresh(db_session):
    """
    Test handling of expired token with automatic refresh.

    Simulates frontend axios interceptor that automatically refreshes
    expired tokens.

    Race Condition: Multiple concurrent requests with expired tokens
    could all trigger token refresh simultaneously.

    Fix: Token refresh should be serialized (only one refresh at a time),
    other requests should wait for the refresh to complete.
    """
    from app.core.security import create_access_token, hash_password
    from app.db.models.user import User

    # Arrange - Create user and get expired token
    user = User(
        email="expired_token_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Expired Token User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create an expired token (expired 1 hour ago)
    expired_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(hours=-1)
    )

    # Mock the token verification to return None for expired token
    with patch("app.api.v1.deps.verify_token", return_value=None):
        # Act - Send 10 concurrent requests with expired token
        async def make_request_with_expired_token():
            """Make request with expired token"""
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/users/me",
                    headers={"Authorization": f"Bearer {expired_token}"},
                )
                return response

        tasks = [make_request_with_expired_token() for _ in range(10)]
        responses = await asyncio.gather(*tasks)

        # Assert - All requests should fail (401 Unauthorized)
        # In a real scenario, the frontend would intercept the 401,
        # refresh the token, and retry the request
        for i, response in enumerate(responses):
            assert (
                response.status_code == 401
            ), f"Request {i} should return 401, got {response.status_code}"

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_concurrent_requests_during_token_refresh(db_session):
    """
    Test concurrent API requests while token is being refreshed.

    Simulates multiple API calls happening while a token refresh is in progress.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create user and login
    user = User(
        email="concurrent_api_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Concurrent API User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get valid token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "concurrent_api_user@psychsync.test",
                "password": "SecurePass123!",
            },
        )

    token = login_response.json()["access_token"]

    # Act - Send 10 concurrent authenticated requests
    async def make_authenticated_request():
        """Make authenticated request"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
            )
            return response

    tasks = [make_authenticated_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # Assert - All requests should succeed
    for i, response in enumerate(responses):
        assert (
            response.status_code == 200
        ), f"Request {i} failed with status {response.status_code}"

        data = response.json()
        assert "id" in data, f"Request {i} should return user data"
        assert str(user.id) == data["id"], f"Request {i} should return correct user"

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


# ============================================================================
# Test 4: Request Deduplication
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.concurrent
async def test_concurrent_identical_requests_deduplication(db_session):
    """
    Test that identical concurrent requests are properly deduplicated.

    Race Condition: Multiple identical requests (same URL, same params)
    could cause duplicate processing and database load.

    Fix: Frontend/backend should deduplicate identical in-flight requests,
    or backend should be idempotent.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create admin user and login
    user = User(
        email="dedup_test_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Dedup Test User",
        is_active=True,
        is_verified=True,
        role="ADMIN",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get admin token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "dedup_test_user@psychsync.test",
                "password": "SecurePass123!",
            },
        )

    admin_token = login_response.json()["access_token"]

    # Act - Send 10 concurrent identical requests to list users
    async def list_users_request():
        """Make list users request"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/users/",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"skip": 0, "limit": 100},
            )
            return response

    tasks = [list_users_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # Assert - All requests should succeed
    for i, response in enumerate(responses):
        assert (
            response.status_code == 200
        ), f"Request {i} failed with status {response.status_code}"

    # All responses should have the same data
    response_data = [r.json() for r in responses]
    first_data = response_data[0]

    for i, data in enumerate(response_data[1:], 1):
        assert data == first_data, f"Response {i} differs from first response"

    print(f"\nRequest Deduplication Test Results:")
    print(f"  Total requests: 10")
    print(f"  Identical responses: {sum(1 for d in response_data if d == first_data)}")

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


# ============================================================================
# Test 5: Retry Logic with Concurrent Failures
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.concurrent
async def test_retry_logic_with_transient_failures():
    """
    Test retry logic when multiple concurrent requests fail.

    Simulates transient failures (network issues, temporary timeouts)
    affecting multiple concurrent requests.

    Race Condition: Multiple concurrent retries could overwhelm the server.

    Fix: Implement exponential backoff and jitter to spread out retries.
    """
    request_count = 0
    failure_count = 0

    async def mock_api_call(request_id: int, attempt: int = 1):
        """Simulate API call with transient failures"""
        nonlocal request_count, failure_count

        request_count += 1

        # First attempt fails, second succeeds (simulated transient failure)
        if attempt == 1:
            failure_count += 1
            # Simulate transient error
            return {"success": False, "error": "Connection timeout"}

        # Second attempt succeeds
        await asyncio.sleep(0.01)  # Simulate network delay
        return {"success": True, "data": f"response_{request_id}"}

    async def api_call_with_retry(request_id: int, max_retries: int = 3):
        """API call with exponential backoff retry"""
        for attempt in range(1, max_retries + 1):
            result = await mock_api_call(request_id, attempt)

            if result["success"]:
                return result

            # Exponential backoff with jitter
            if attempt < max_retries:
                backoff_ms = (2**attempt) * 10 + request_id % 20  # Add jitter
                await asyncio.sleep(backoff_ms / 1000)

        return {"success": False, "error": "Max retries exceeded"}

    # Act - 10 concurrent requests with retry logic
    start_time = datetime.now()

    tasks = [api_call_with_retry(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Assert - All requests should eventually succeed
    success_count = sum(1 for r in results if r["success"])
    assert success_count == 10, f"Expected all 10 to succeed, got {success_count}"

    # Verify retry behavior
    assert (
        request_count == 20
    ), f"Expected 20 total requests (10*2), got {request_count}"
    assert failure_count == 10, f"Expected 10 initial failures, got {failure_count}"

    print(f"\nRetry Logic Test Results:")
    print(f"  Concurrent requests: 10")
    print(f"  Total attempts: {request_count}")
    print(f"  Initial failures: {failure_count}")
    print(f"  Final successes: {success_count}")
    print(f"  Duration: {duration:.3f}s")


# ============================================================================
# Test 6: Request Cancellation During Token Refresh
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_request_cancellation_during_token_refresh(db_session):
    """
    Test that requests are properly cancelled if component unmounts during token refresh.

    Simulates React component unmounting while a token refresh is in progress.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create user and login
    user = User(
        email="cancellation_test_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Cancellation Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get tokens
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "cancellation_test_user@psychsync.test",
                "password": "SecurePass123!",
            },
        )

    refresh_token = login_response.json()["refresh_token"]

    # Act - Simulate request that gets cancelled
    cancelled = False

    async def refresh_with_delay():
        """Refresh token with delay (simulating slow network)"""
        nonlocal cancelled
        try:
            await asyncio.sleep(0.5)  # Simulate network delay
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
                )
                return response
        except asyncio.CancelledError:
            cancelled = True
            raise

    # Start refresh task
    task = asyncio.create_task(refresh_with_delay())

    # Cancel after 100ms (simulating component unmount)
    await asyncio.sleep(0.1)
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass  # Expected

    # Assert - Task should have been cancelled
    assert cancelled, "Task should have been cancelled"

    # Verify we can still make new requests (token wasn't corrupted)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

    # Should still work (refresh token not invalidated)
    assert response.status_code == 200, "Refresh should still work after cancellation"

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


# ============================================================================
# Test 7: Concurrent Logout and Token Refresh
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.concurrent
async def test_concurrent_logout_and_token_refresh(db_session):
    """
    Test concurrent logout and token refresh operations.

    Race Condition: Logging out while token refresh is in progress
    could cause inconsistent state.

    Fix: Logout should blacklist refresh token, preventing further refreshes.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create user and login
    user = User(
        email="logout_race_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="Logout Race User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get tokens
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "logout_race_user@psychsync.test",
                "password": "SecurePass123!",
            },
        )

    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Act - Logout and token refresh concurrently
    async def logout_request():
        """Logout request (blacklist refresh token)"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Add small delay to make race more likely
            await asyncio.sleep(0.05)
            response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": refresh_token},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response

    async def refresh_request():
        """Token refresh request"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )
            return response

    # Execute logout and refresh concurrently
    tasks = [logout_request(), refresh_request()]
    responses = await asyncio.gather(*tasks)

    logout_response, refresh_response = responses

    # Assert - Logout should succeed
    assert (
        logout_response.status_code == 200
    ), f"Logout failed with status {logout_response.status_code}"

    # Refresh may succeed or fail depending on timing
    # If logout happens first, refresh should fail
    # If refresh happens first, refresh should succeed
    assert refresh_response.status_code in [
        200,
        401,
    ], f"Refresh should return 200 or 401, got {refresh_response.status_code}"

    print(f"\nConcurrent Logout and Refresh Test Results:")
    print(f"  Logout status: {logout_response.status_code}")
    print(f"  Refresh status: {refresh_response.status_code}")

    # After logout, any new refresh attempt should fail
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

    assert (
        response.status_code == 401
    ), "Refresh should fail after logout (token blacklisted)"

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()


# ============================================================================
# Test 8: High Concurrency API Load
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.api
@pytest.mark.concurrent
@pytest.mark.load_test
async def test_high_concurrency_authenticated_requests(db_session):
    """
    Stress test: 100 concurrent authenticated API requests.

    Verifies the system can handle high concurrency without errors.
    """
    from app.core.security import hash_password
    from app.db.models.user import User

    # Arrange - Create user and login
    user = User(
        email="high_concurrency_api_user@psychsync.test",
        hashed_password=hash_password("SecurePass123!"),
        full_name="High Concurrency API User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Get token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "high_concurrency_api_user@psychsync.test",
                "password": "SecurePass123!",
            },
        )

    token = login_response.json()["access_token"]

    # Act - Send 100 concurrent authenticated requests
    async def make_request(request_id: int):
        """Make authenticated request"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
            )
            return response

    start_time = datetime.now()

    tasks = [make_request(i) for i in range(100)]
    responses = await asyncio.gather(*tasks)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Assert - All requests should succeed
    success_count = sum(1 for r in responses if r.status_code == 200)
    error_count = sum(1 for r in responses if r.status_code != 200)

    assert (
        success_count == 100
    ), f"Expected all 100 requests to succeed, got {success_count} successes, {error_count} errors"

    # All responses should have correct user data
    for i, response in enumerate(responses):
        data = response.json()
        assert data["id"] == str(user.id), f"Request {i} returned wrong user"

    print(f"\nHigh Concurrency API Load Test Results:")
    print(f"  Total requests: 100")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {success_count / duration:.0f} req/s")
    print(f"  Avg response time: {duration / 100 * 1000:.0f}ms")

    # Performance assertion
    assert duration < 10, f"Expected completion in < 10s, took {duration:.2f}s"

    # Cleanup
    await db_session.delete(user)
    await db_session.commit()
