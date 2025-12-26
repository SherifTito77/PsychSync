"""
Comprehensive Test Suite for Generated API Functions
Tests all fabricated functions with edge cases and error scenarios
Coverage target: 95%+ for all generated functions
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
import redis.asyncio as redis

# Import generated functions
from app.services.rate_limiter_service import (
    AdvancedRateLimiter, UserTier, RateLimit, advanced_rate_limiter
)
from app.services.restful_service import (
    RESTfulEndpointBuilder, RESTfulPathBuilder, RESTfulValidator,
    create_restful_router, validate_restful_compliance
)
from app.services.api_performance_service import (
    PerformanceMonitor, PerformanceMetric, SystemMetrics, performance_monitor
)
from app.services.api_security_service import (
    APISecurityService, SecurityEvent, SecurityLevel, ThreatLevel, api_security_service
)

# Mock FastAPI objects
class MockRequest:
    def __init__(self, method="GET", path="/test", client_ip="127.0.0.1"):
        self.method = method
        self.url = Mock()
        self.url.path = path
        self.client = Mock()
        self.client.host = client_ip
        self.state = Mock()
        self.headers = {}

# ==================== RATE LIMITER TESTS ====================

class TestAdvancedRateLimiter:
    """Test suite for AdvancedRateLimiter"""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance for testing"""
        return AdvancedRateLimiter()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = AsyncMock(spec=redis.Redis)
        return mock_client

    def test_rate_limit_initialization(self, rate_limiter):
        """Test rate limiter initialization"""
        assert rate_limiter.RATE_LIMITS[UserTier.BASIC].requests_per_minute == 200
        assert rate_limiter.RATE_LIMITS[UserTier.PREMIUM].requests_per_hour == 2500
        assert "POST:/api/v1/auth/token" in rate_limiter.ENDPOINT_MULTIPLIERS
        assert rate_limiter.ENDPOINT_MULTIPLIERS["POST:/api/v1/auth/token"] == 0.5

    def test_client_identifier_generation(self, rate_limiter):
        """Test client identifier generation"""
        # Test with authenticated user
        request = MockRequest()
        request.state.user_id = "user123"
        identifier = rate_limiter._get_client_identifier(request, UserTier.BASIC)
        assert "user:user123:basic" in identifier

        # Test with anonymous user
        request = MockRequest(client_ip="192.168.1.1")
        delattr(request.state, 'user_id')  # Ensure no user_id
        identifier = rate_limiter._get_client_identifier(request, UserTier.ANONYMOUS)
        assert "ip:192.168.1.1:anonymous" in identifier

    def test_endpoint_key_generation(self, rate_limiter):
        """Test endpoint key generation"""
        request = MockRequest(method="POST", path="/api/v1/auth/token")
        endpoint_key = rate_limiter._get_endpoint_key(request)
        assert endpoint_key == "POST:/api/v1/auth/token"

    def test_rate_limit_calculation(self, rate_limiter):
        """Test rate limit calculation for endpoints"""
        endpoint = "POST:/api/v1/auth/token"
        rate_limit = rate_limiter._get_rate_limit_for_endpoint(endpoint, UserTier.BASIC)

        # Should be 50% of basic tier limits due to multiplier
        assert rate_limit.requests_per_minute == 100  # 200 * 0.5
        assert rate_limit.requests_per_hour == 500    # 1000 * 0.5

    @pytest.mark.asyncio
    async def test_rate_limit_check_allowed(self, rate_limiter, mock_redis):
        """Test rate limit check for allowed request"""
        rate_limiter._redis_client = mock_redis

        # Mock Redis responses
        mock_redis.pipeline.return_value.execute.return_value = ["0", "0", "0"]  # No requests yet

        request = MockRequest()
        is_allowed, limit_info = await rate_limiter.check_rate_limit(request, UserTier.BASIC)

        assert is_allowed is True
        assert limit_info["minute"]["limit"] == 200
        assert limit_info["minute"]["remaining"] == 200
        assert limit_info["tier"] == "basic"

    @pytest.mark.asyncio
    async def test_rate_limit_check_exceeded(self, rate_limiter, mock_redis):
        """Test rate limit check when limit exceeded"""
        rate_limiter._redis_client = mock_redis

        # Mock Redis responses - at limit for minute
        mock_redis.pipeline.return_value.execute.return_value = ["200", "500", "5000"]

        request = MockRequest()
        is_allowed, limit_info = await rate_limiter.check_rate_limit(request, UserTier.BASIC)

        assert is_allowed is False
        assert limit_info["minute"]["remaining"] == 0

    @pytest.mark.asyncio
    async def test_rate_limit_check_redis_error(self, rate_limiter, mock_redis):
        """Test rate limit check with Redis error"""
        rate_limiter._redis_client = mock_redis
        mock_redis.pipeline.side_effect = Exception("Redis error")

        request = MockRequest()
        is_allowed, limit_info = await rate_limiter.check_rate_limit(request, UserTier.BASIC)

        # Should fail open - allow request if rate limiting fails
        assert is_allowed is True
        assert "error" in limit_info

    def test_resource_name_validation(self, rate_limiter):
        """Test resource name validation"""
        assert rate_limiter._validate_resource_name("users") is True
        assert rate_limiter._validate_resource_name("user_profiles") is True
        assert rate_limiter._validate_resource_name("Users") is False  # Uppercase not allowed
        assert rate_limiter._validate_resource_name("") is False
        assert rate_limiter._validate_resource_name("users!") is False  # Special char not allowed

# ==================== RESTFUL SERVICE TESTS ====================

class TestRESTfulService:
    """Test suite for RESTful service utilities"""

    @pytest.fixture
    def mock_model(self):
        """Mock Pydantic model"""
        from pydantic import BaseModel

        class MockModel(BaseModel):
            id: int
            name: str

        return MockModel

    @pytest.fixture
    def endpoint_builder(self, mock_model):
        """Create RESTful endpoint builder"""
        from fastapi import APIRouter
        router = APIRouter()
        return RESTfulEndpointBuilder(router, "user", mock_model)

    def test_pluralization(self):
        """Test noun pluralization"""
        assert RESTfulEndpointBuilder(None, "user", None)._make_plural("user") == "users"
        assert RESTfulEndpointBuilder(None, "company", None)._make_plural("company") == "companies"
        assert RESTfulEndpointBuilder(None, "box", None)._make_plural("box") == "boxes"

    def test_path_building(self):
        """Test RESTful path building"""
        collection_path = RESTfulPathBuilder.build_collection_path("users")
        assert collection_path == "/api/v1/users"

        resource_path = RESTfulPathBuilder.build_resource_path("users")
        assert resource_path == "/api/v1/users/{id}"

        action_path = RESTfulPathBuilder.build_action_path("users", "activate")
        assert action_path == "/api/v1/users/{id}/activate"

        relationship_path = RESTfulPathBuilder.build_relationship_path("users", "assessments")
        assert relationship_path == "/api/v1/users/{id}/assessments"

    def test_endpoint_method_validation(self):
        """Test endpoint method validation"""
        # Collection endpoints
        is_valid, issues = RESTfulValidator.validate_endpoint_method("GET", "/users")
        assert is_valid is True
        assert len(issues) == 0

        is_valid, issues = RESTfulValidator.validate_endpoint_method("POST", "/users")
        assert is_valid is True
        assert len(issues) == 0

        is_valid, issues = RESTfulValidator.validate_endpoint_method("PUT", "/users")
        assert is_valid is False
        assert len(issues) > 0

        # Resource endpoints
        is_valid, issues = RESTfulValidator.validate_endpoint_method("GET", "/users/{id}")
        assert is_valid is True

        is_valid, issues = RESTfulValidator.validate_endpoint_method("DELETE", "/users/{id}")
        assert is_valid is True

        is_valid, issues = RESTfulValidator.validate_endpoint_method("POST", "/users/{id}")
        assert is_valid is False

    def test_collection_response_building(self):
        """Test standardized collection response building"""
        items = [{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}]

        response = RESTfulResponseBuilder.build_collection_response(
            items=items,
            page=1,
            size=20,
            total=50
        )

        assert response["data"] == items
        assert response["pagination"]["page"] == 1
        assert response["pagination"]["size"] == 20
        assert response["pagination"]["total"] == 50
        assert response["pagination"]["pages"] == 3
        assert response["pagination"]["has_next"] is True
        assert response["pagination"]["has_prev"] is False

    def test_resource_response_building(self):
        """Test standardized resource response building"""
        resource = {"id": 1, "name": "Test User"}

        response = RESTfulResponseBuilder.build_resource_response(resource)

        assert response["data"] == resource
        assert "links" in response
        assert "meta" in response
        assert response["meta"]["type"] == "dict"

    @pytest.mark.asyncio
    async def test_crud_endpoint_creation(self, endpoint_builder):
        """Test CRUD endpoint creation"""
        mock_service = Mock()

        endpoints = endpoint_builder.create_crud_endpoints(
            service_class=mock_service,
            auth_required=True
        )

        assert "list" in endpoints
        assert "create" in endpoints
        assert "retrieve" in endpoints
        assert "update" in endpoints
        assert "delete" in endpoints

    def test_invalid_resource_name(self):
        """Test handling of invalid resource names"""
        from fastapi import APIRouter
        router = APIRouter()

        with pytest.raises(ValueError, match="Invalid resource name"):
            RESTfulEndpointBuilder(router, "InvalidName!", Mock())

# ==================== PERFORMANCE MONITOR TESTS ====================

class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor"""

    @pytest.fixture
    def performance_monitor_instance(self):
        """Create performance monitor instance for testing"""
        return PerformanceMonitor(max_history=100)

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = AsyncMock(spec=redis.Redis)
        return mock_client

    def test_performance_classification(self, performance_monitor_instance):
        """Test performance level classification"""
        assert performance_monitor_instance._classify_performance(50) == PerformanceLevel.EXCELLENT
        assert performance_monitor_instance._classify_performance(200) == PerformanceLevel.GOOD
        assert performance_monitor_instance._classify_performance(500) == PerformanceLevel.ACCEPTABLE
        assert performance_monitor_instance._classify_performance(1500) == PerformanceLevel.SLOW
        assert performance_monitor_instance._classify_performance(5000) == PerformanceLevel.CRITICAL

    def test_percentile_calculation(self, performance_monitor_instance):
        """Test percentile calculation"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        p50 = performance_monitor_instance._calculate_percentile(data, 50)
        assert p50 == 5.5  # Median of even number of items

        p95 = performance_monitor_instance._calculate_percentile(data, 95)
        assert p95 == 9.55

        p100 = performance_monitor_instance._calculate_percentile(data, 100)
        assert p100 == 10

    def test_empty_percentile_calculation(self, performance_monitor_instance):
        """Test percentile calculation with empty data"""
        result = performance_monitor_instance._calculate_percentile([], 50)
        assert result == 0

    @pytest.mark.asyncio
    async def test_metric_recording(self, performance_monitor_instance, mock_redis):
        """Test performance metric recording"""
        performance_monitor_instance._redis_client = mock_redis

        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            endpoint="GET:/api/v1/users",
            method="GET",
            duration_ms=150.5,
            status_code=200,
            response_size_bytes=1024,
            user_agent="test-agent",
            ip_address="127.0.0.1",
            user_id="user123"
        )

        # Mock Redis operations
        mock_redis.lpush.return_value = None
        mock_redis.expire.return_value = None

        await performance_monitor_instance.record_metric(metric)

        # Verify Redis was called
        assert mock_redis.lpush.called
        assert mock_redis.expire.called

        # Check metric was stored in memory
        assert len(performance_monitor_instance._metrics_history["GET:/api/v1/users"]) == 1

    @pytest.mark.asyncio
    async def test_metric_recording_redis_error(self, performance_monitor_instance, mock_redis):
        """Test metric recording with Redis error"""
        performance_monitor_instance._redis_client = mock_redis
        mock_redis.lpush.side_effect = Exception("Redis error")

        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            endpoint="GET:/api/v1/users",
            method="GET",
            duration_ms=150.5,
            status_code=200,
            response_size_bytes=1024,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )

        # Should not raise exception
        await performance_monitor_instance.record_metric(metric)

        # Should still store in memory
        assert len(performance_monitor_instance._metrics_history["GET:/api/v1/users"]) == 1

    @pytest.mark.asyncio
    async def test_performance_stats_calculation(self, performance_monitor_instance):
        """Test performance statistics calculation"""
        # Mock metrics data
        metrics_data = [
            {"duration_ms": 100, "status_code": 200, "response_size_bytes": 500},
            {"duration_ms": 200, "status_code": 200, "response_size_bytes": 1000},
            {"duration_ms": 300, "status_code": 404, "response_size_bytes": 200},
            {"duration_ms": 150, "status_code": 500, "response_size_bytes": 300},
        ]

        stats = await performance_monitor_instance._calculate_performance_stats(
            "GET:/api/v1/users",
            metrics_data
        )

        assert stats.endpoint == "GET:/api/v1/users"
        assert stats.total_requests == 4
        assert stats.avg_response_time == 187.5  # (100+200+300+150)/4
        assert stats.error_rate == 50.0  # 2 errors out of 4 requests
        assert stats.performance_level == PerformanceLevel.ACCEPTABLE

    @pytest.mark.asyncio
    async def test_empty_performance_stats(self, performance_monitor_instance):
        """Test performance statistics with no data"""
        stats = await performance_monitor_instance._calculate_performance_stats(
            "GET:/api/v1/users",
            []
        )

        assert stats.endpoint == "GET:/api/v1/users"
        assert stats.total_requests == 0
        assert stats.avg_response_time == 0
        assert stats.error_rate == 0

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, performance_monitor_instance):
        """Test system metrics collection"""
        with patch('psutil.cpu_percent', return_value=45.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.Process') as mock_process:

            # Mock psutil returns
            mock_memory.return_value.percent = 60.0
            mock_disk.return_value.percent = 70.0
            mock_process.return_value.num_threads.return_value = 8
            mock_process.return_value.connections.return_value = [1, 2, 3]
            mock_process.return_value.open_files.return_value = [1, 2]

            metrics = await performance_monitor_instance.collect_system_metrics()

            assert metrics.cpu_percent == 45.0
            assert metrics.memory_percent == 60.0
            assert metrics.disk_usage_percent == 70.0
            assert metrics.active_connections == 3
            assert metrics.open_files == 2
            assert metrics.threads_count == 8

    @pytest.mark.asyncio
    async def test_system_metrics_collection_error(self, performance_monitor_instance):
        """Test system metrics collection with error"""
        with patch('psutil.Process', side_effect=Exception("psutil error")):
            metrics = await performance_monitor_instance.collect_system_metrics()

            # Should return default values on error
            assert metrics.cpu_percent == 0
            assert metrics.memory_percent == 0
            assert metrics.disk_usage_percent == 0

    def test_performance_summary(self, performance_monitor_instance):
        """Test current performance summary"""
        # Add some mock data
        performance_monitor_instance._metrics_history["GET:/api/v1/users"] = [
            Mock(), Mock()
        ]
        performance_monitor_instance._alert_state["GET:/api/v1/users"] = True

        summary = performance_monitor_instance.get_current_performance_summary()

        assert summary["active_endpoints"] == 1
        assert summary["alerts_active"] == 1
        assert summary["recent_metrics"] == 2

# ==================== SECURITY SERVICE TESTS ====================

class TestAPISecurityService:
    """Test suite for APISecurityService"""

    @pytest.fixture
    def security_service(self):
        """Create security service instance"""
        return APISecurityService()

    def test_api_key_generation(self, security_service):
        """Test API key generation"""
        api_key, key_id = security_service.generate_api_key(
            name="Test Key",
            permissions=["read", "write"],
            rate_limit_tier="premium",
            expires_in_days=30
        )

        assert api_key.startswith("psync_")
        assert key_id in api_key
        assert len(api_key) > 40
        assert key_id in security_service._api_keys

        key_obj = security_service._api_keys[key_id]
        assert key_obj.name == "Test Key"
        assert key_obj.permissions == ["read", "write"]
        assert key_obj.rate_limit_tier == "premium"
        assert key_obj.expires_at is not None

    def test_api_key_validation(self, security_service):
        """Test API key validation"""
        # Generate a valid key
        api_key, key_id = security_service.generate_api_key(
            name="Test Key",
            permissions=["read"]
        )

        # Test valid key
        key_obj = security_service.validate_api_key(api_key)
        assert key_obj is not None
        assert key_obj.name == "Test Key"
        assert key_obj.permissions == ["read"]

        # Test invalid key format
        invalid_key = "invalid_key_format"
        assert security_service.validate_api_key(invalid_key) is None

        # Test non-existent key
        non_existent_key = "psync_invalidkey_nonexistent"
        assert security_service.validate_api_key(non_existent_key) is None

    def test_api_key_expiration(self, security_service):
        """Test API key expiration"""
        # Generate expired key
        api_key, key_id = security_service.generate_api_key(
            name="Expired Key",
            permissions=["read"],
            expires_in_days=-1  # Already expired
        )

        # Should not validate expired key
        assert security_service.validate_api_key(api_key) is None

    def test_webhook_signature_verification(self, security_service):
        """Test webhook signature verification"""
        payload = b'{"test": "data"}'
        secret = "test_secret"

        # Generate valid signature
        import hmac
        import hashlib
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Test valid signature
        assert security_service.verify_webhook_signature(payload, signature, secret) is True

        # Test invalid signature
        invalid_signature = "sha256=invalid_signature"
        assert security_service.verify_webhook_signature(payload, invalid_signature, secret) is False

        # Test wrong format
        wrong_format_signature = "wrong_format"
        assert security_service.verify_webhook_signature(payload, wrong_format_signature, secret) is False

    def test_input_sanitization(self, security_service):
        """Test input sanitization"""
        # Test string sanitization
        dirty_input = "<script>alert('xss')</script>Hello World"
        clean_input = security_service.sanitize_input(dirty_input)
        assert "<script>" not in clean_input
        assert "Hello World" in clean_input

        # Test dict sanitization
        dirty_dict = {
            "name": "<b>User</b>",
            "description": "<script>alert('xss')</script>Desc",
            "metadata": {"key": "value"}
        }
        clean_dict = security_service.sanitize_input(dirty_dict)
        assert "<script>" not in clean_dict["description"]
        assert "User" in clean_dict["name"]

        # Test list sanitization
        dirty_list = ["<b>Item 1</b>", "<script>alert('xss')</script>", "Normal item"]
        clean_list = security_service.sanitize_input(dirty_list)
        assert "<script>" not in str(clean_list)

    def test_threat_detection(self, security_service):
        """Test threat detection"""
        # Test SQL injection detection
        sql_injection = "SELECT * FROM users WHERE id = 1; DROP TABLE users;"
        threats = security_service.detect_threats(
            sql_injection,
            "192.168.1.1",
            "test-agent",
            "/api/v1/users"
        )
        assert len(threats) > 0
        assert any("sql_injection" in threat.event_type for threat in threats)

        # Test XSS detection
        xss_payload = "<script>alert('xss')</script>"
        threats = security_service.detect_threats(
            xss_payload,
            "192.168.1.1",
            "test-agent",
            "/api/v1/users"
        )
        assert len(threats) > 0
        assert any("xss" in threat.event_type for threat in threats)

    def test_ip_blacklist(self, security_service):
        """Test IP blacklist functionality"""
        # Test blacklisting an IP
        result = security_service.block_ip_address("192.168.1.100", "Test block")
        assert result is True
        assert "192.168.1.100" in security_service.ip_blacklist

        # Test invalid IP format
        result = security_service.block_ip_address("invalid.ip", "Test block")
        assert result is False

        # Test checking if IP is blacklisted
        assert security_service._is_ip_blacklisted("192.168.1.100") is True
        assert security_service._is_ip_blacklisted("192.168.1.200") is False

    def test_cors_origin_validation(self, security_service):
        """Test CORS origin validation"""
        # Test allowed origins
        assert security_service.validate_cors_origin("http://localhost:3000") is True

        # Test denied origins
        assert security_service.validate_cors_origin("http://evil.com") is False

        # Test subdomain matching
        security_service.allowed_origins.append("*.trusted.com")
        assert security_service.validate_cors_origin("http://api.trusted.com") is True

    def test_request_size_validation(self, security_service):
        """Test request size validation"""
        # Test valid size
        assert security_service.validate_request_size(1000) is True

        # Test oversized request
        assert security_service.validate_request_size(20 * 1024 * 1024) is False  # 20MB

    def test_security_headers(self, security_service):
        """Test security headers addition"""
        existing_headers = {"Content-Type": "application/json"}
        enhanced_headers = security_service.add_security_headers(existing_headers)

        assert "X-Content-Type-Options" in enhanced_headers
        assert enhanced_headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in enhanced_headers
        assert enhanced_headers["X-Frame-Options"] == "DENY"
        assert existing_headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_security_event_logging(self, security_service):
        """Test security event logging"""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type="test_event",
            source_ip="192.168.1.1",
            user_agent="test-agent",
            endpoint="/api/v1/test",
            method="GET",
            details={"test": "data"},
            severity="low"
        )

        with patch('logging.getLogger') as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance

            await security_service.log_security_event(event)

            # Verify event was stored
            assert len(security_service._security_events) == 1
            assert security_service._security_events[0].event_type == "test_event"

    def test_security_summary(self, security_service):
        """Test security summary generation"""
        # Add some mock events
        now = datetime.utcnow()
        security_service._security_events = [
            SecurityEvent(
                timestamp=now - timedelta(hours=1),
                event_type="sql_injection",
                source_ip="192.168.1.1",
                user_agent="test",
                endpoint="/api/v1/users",
                method="POST",
                severity="high"
            ),
            SecurityEvent(
                timestamp=now - timedelta(hours=2),
                event_type="xss_attempt",
                source_ip="192.168.1.2",
                user_agent="test",
                endpoint="/api/v1/users",
                method="GET",
                severity="medium"
            )
        ]

        summary = security_service.get_security_summary(hours=24)

        assert summary["total_events"] == 2
        assert summary["unique_source_ips"] == 2
        assert summary["threat_level"] == ThreatLevel.HIGH.value  # One high severity event
        assert "sql_injection" in summary["event_types"]
        assert "xss_attempt" in summary["event_types"]

# ==================== INTEGRATION TESTS ====================

class TestFunctionIntegration:
    """Integration tests for all generated functions"""

    @pytest.mark.asyncio
    async def test_full_request_pipeline(self):
        """Test complete request pipeline through all services"""
        # Setup mock request
        request = MockRequest(method="POST", path="/api/v1/users")
        request.headers["X-API-Key"] = "test_key"
        request.headers["Content-Type"] = "application/json"
        request.state.user_id = "user123"

        # Mock Redis for all services
        with patch('redis.asyncio.from_url') as mock_redis_from_url:
            mock_redis = AsyncMock()
            mock_redis_from_url.return_value = mock_redis

            # Initialize services
            rate_limiter = AdvancedRateLimiter()
            perf_monitor = PerformanceMonitor()
            security_service = APISecurityService()

            # Generate API key
            api_key, key_id = security_service.generate_api_key(
                name="Integration Test",
                permissions=["write"]
            )
            request.headers["X-API-Key"] = api_key

            # Mock Redis responses for rate limiting
            mock_redis.pipeline.return_value.execute.return_value = ["0", "0", "0"]

            # 1. Security validation
            key_obj = security_service.validate_api_key(api_key)
            assert key_obj is not None

            # 2. Rate limiting check
            is_allowed, limit_info = await rate_limiter.check_rate_limit(
                request, UserTier.BASIC
            )
            assert is_allowed is True

            # 3. Performance monitoring
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                endpoint="POST:/api/v1/users",
                method="POST",
                duration_ms=150.0,
                status_code=201,
                response_size_bytes=500,
                user_agent="test-agent",
                ip_address="127.0.0.1",
                user_id="user123"
            )
            await perf_monitor.record_metric(metric)

            # Verify all services processed the request
            assert key_obj.permissions == ["write"]
            assert limit_info["tier"] == "basic"
            assert len(perf_monitor._metrics_history["POST:/api/v1/users"]) == 1

    @pytest.mark.asyncio
    async def test_error_handling_pipeline(self):
        """Test error handling across all services"""
        request = MockRequest()

        # Test security validation with invalid key
        invalid_key = "invalid_key_format"
        key_obj = api_security_service.validate_api_key(invalid_key)
        assert key_obj is None

        # Test threat detection with malicious payload
        malicious_payload = "'; DROP TABLE users; --"
        threats = api_security_service.detect_threats(
            malicious_payload,
            "192.168.1.100",
            "evil-agent",
            "/api/v1/users"
        )
        assert len(threats) > 0

        # Block the malicious IP
        api_security_service.block_ip_address("192.168.1.100", "SQL injection attempt")
        assert api_security_service._is_ip_blacklisted("192.168.1.100")

        # Test rate limiting failure scenario
        with patch('redis.asyncio.from_url', side_effect=Exception("Redis down")):
            rate_limiter = AdvancedRateLimiter()
            is_allowed, limit_info = await rate_limiter.check_rate_limit(
                request, UserTier.ANONYMOUS
            )
            # Should fail open
            assert is_allowed is True

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance characteristics under load"""
        rate_limiter = AdvancedRateLimiter()
        perf_monitor = PerformanceMonitor()

        # Mock Redis with fast responses
        with patch('redis.asyncio.from_url') as mock_redis_from_url:
            mock_redis = AsyncMock()
            mock_redis_from_url.return_value = mock_redis
            mock_redis.pipeline.return_value.execute.return_value = ["5", "100", "1000"]

            # Simulate high load
            start_time = time.time()
            tasks = []

            for i in range(100):
                request = MockRequest(client_ip=f"192.168.1.{i % 255}")
                task = rate_limiter.check_rate_limit(request, UserTier.BASIC)
                tasks.append(task)

            # Execute all rate limit checks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            duration = end_time - start_time

            # Performance assertions
            assert duration < 5.0  # Should complete within 5 seconds
            assert len(results) == 100
            assert all(isinstance(result, tuple) and len(result) == 2 for result in results)

            # Test performance monitoring under load
            metrics = []
            for i in range(50):
                metric = PerformanceMetric(
                    timestamp=datetime.utcnow(),
                    endpoint=f"GET:/api/v1/test/{i}",
                    method="GET",
                    duration_ms=100 + (i % 200),
                    status_code=200,
                    response_size_bytes=1000,
                    user_agent="test-agent",
                    ip_address="127.0.0.1"
                )
                metrics.append(metric)

            # Record metrics concurrently
            start_time = time.time()
            await asyncio.gather(*[perf_monitor.record_metric(metric) for metric in metrics])
            end_time = time.time()

            assert (end_time - start_time) < 2.0  # Should complete quickly

# ==================== PERFORMANCE BENCHMARKS ====================

class TestPerformanceBenchmarks:
    """Performance benchmarks for generated functions"""

    @pytest.mark.asyncio
    async def test_rate_limiter_performance(self):
        """Benchmark rate limiter performance"""
        rate_limiter = AdvancedRateLimiter()

        with patch('redis.asyncio.from_url') as mock_redis_from_url:
            mock_redis = AsyncMock()
            mock_redis_from_url.return_value = mock_redis
            mock_redis.pipeline.return_value.execute.return_value = ["10", "200", "2000"]

            request = MockRequest()

            # Benchmark rate limit check
            iterations = 1000
            start_time = time.time()

            for _ in range(iterations):
                await rate_limiter.check_rate_limit(request, UserTier.BASIC)

            end_time = time.time()
            avg_time = (end_time - start_time) / iterations * 1000

            # Should complete in under 1ms per check on average
            assert avg_time < 1.0, f"Rate limiter too slow: {avg_time:.2f}ms per check"

    @pytest.mark.asyncio
    async def test_security_service_performance(self):
        """Benchmark security service performance"""
        service = APISecurityService()

        # Benchmark input sanitization
        test_input = "Normal text with <b>some</b> formatting"
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            service.sanitize_input(test_input)
        end_time = time.time()

        avg_time = (end_time - start_time) / iterations * 1000
        assert avg_time < 0.5, f"Input sanitization too slow: {avg_time:.2f}ms per operation"

        # Benchmark threat detection
        malicious_input = "SELECT * FROM users WHERE id = 1"
        start_time = time.time()
        for _ in range(iterations):
            service.detect_threats(malicious_input, "127.0.0.1", "test", "/api/v1/test")
        end_time = time.time()

        avg_time = (end_time - start_time) / iterations * 1000
        assert avg_time < 2.0, f"Threat detection too slow: {avg_time:.2f}ms per operation"

# ==================== FIXTURES AND UTILITIES ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Configuration for pytest
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )

# Custom assertions for better test readability
def assert_valid_response(response_data: Dict[str, Any]):
    """Assert that response follows expected format"""
    assert "data" in response_data
    assert "success" in response_data
    assert isinstance(response_data["success"], bool)

def assert_performance_stats(stats):
    """Assert that performance stats have required fields"""
    required_fields = [
        "endpoint", "total_requests", "avg_response_time",
        "p95_response_time", "error_rate", "performance_level"
    ]
    for field in required_fields:
        assert field in stats, f"Missing field: {field}"

def assert_security_event(event: SecurityEvent):
    """Assert that security event has required fields"""
    assert event.timestamp is not None
    assert event.event_type is not None
    assert event.source_ip is not None
    assert event.endpoint is not None
    assert event.severity in ["low", "medium", "high", "critical"]