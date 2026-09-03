"""
Comprehensive Test Suite for Advanced Generated Functions
Tests all fabricated advanced functions with edge cases and performance benchmarks
Coverage target: 95%+ for all advanced functions
"""

import asyncio
import gzip
import json
import time
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis.asyncio as redis

from app.services.intelligent_cache import (
    CacheEntry,
    CacheLevel,
    IntelligentCache,
    MemoryCache,
    cache_warm,
    cached,
    intelligent_cache,
)

# Import advanced functions
from app.services.request_processor import (
    ProcessingResult,
    RequestContext,
    RequestProcessor,
    deduplicate_request,
    process_request,
    request_processor,
)
from app.services.response_transformer import (
    ResponseMetadata,
    ResponseTransformer,
    TransformationConfig,
    response_transformer,
    transform_response,
)
from app.services.validation_framework import (
    RequestValidator,
    ValidationError,
    ValidationResult,
    ValidationRule,
    field_validator,
    request_validator,
    validate,
)


# Mock FastAPI objects
class MockRequest:
    def __init__(
        self,
        method="GET",
        path="/test",
        headers=None,
        query_params=None,
        json_data=None,
    ):
        self.method = method
        self.url = Mock()
        self.url.path = path
        self.client = Mock()
        self.client.host = "127.0.0.1"
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.state = Mock()
        self._json = json_data or {}

    async def json(self):
        return self._json


# ==================== REQUEST PROCESSOR TESTS ====================


class TestRequestProcessor:
    """Test suite for RequestProcessor"""

    @pytest.fixture
    def processor(self):
        """Create request processor instance"""
        return RequestProcessor()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = AsyncMock(spec=redis.Redis)
        return mock_client

    def test_request_context_creation(self, processor):
        """Test request context creation"""
        request = MockRequest(
            method="POST",
            path="/api/v1/users",
            headers={"User-Agent": "test-client"},
            query_params={"page": "1", "size": "20"},
        )

        context = processor.create_request_context(request)

        assert context.method == "POST"
        assert context.path == "/api/v1/users"
        assert context.client_ip == "127.0.0.1"
        assert context.user_agent == "test-client"
        assert context.query_params == {"page": "1", "size": "20"}
        assert context.priority.value in ["low", "normal", "high", "critical"]

    def test_priority_determination(self, processor):
        """Test request priority determination"""
        # Health check - critical priority
        request = MockRequest(path="/api/v1/health")
        priority = processor._determine_request_priority(request, "basic")
        assert priority.value == "critical"

        # Auth endpoint - high priority
        request = MockRequest(path="/api/v1/auth/login")
        priority = processor._determine_request_priority(request, "basic")
        assert priority.value == "high"

        # Analytics endpoint - low priority
        request = MockRequest(path="/api/v1/analytics")
        priority = processor._determine_request_priority(request, "basic")
        assert priority.value == "low"

    @pytest.mark.asyncio
    async def test_request_processing_context_manager(self, processor):
        """Test request processing context manager"""
        request = MockRequest()

        async with processor.process_request(request) as context:
            assert context is not None
            assert hasattr(context, "request_id")
            assert hasattr(context, "processing_start_time")
            assert processor.stats["active_concurrent"] == 1

        # After context exit
        assert processor.stats["active_concurrent"] == 0
        assert context.request_id not in processor.active_requests

    @pytest.mark.asyncio
    async def test_response_compression(self, processor):
        """Test response compression"""
        # Small data - should not be compressed
        small_data = "Hello World"
        compressed, compression_type = await processor.compress_response(small_data)
        assert compression_type == processor.CompressionType.NONE

        # Large data - should be compressed
        large_data = "x" * 2000
        compressed, compression_type = await processor.compress_response(large_data)
        assert compression_type != processor.CompressionType.NONE
        assert len(compressed) < len(large_data.encode())

        # Test with different compression types
        compressed, compression_type = await processor.compress_response(
            large_data, [processor.CompressionType.GZIP]
        )
        assert compression_type == processor.CompressionType.GZIP

    def test_optimized_response_creation(self, processor):
        """Test optimized response creation"""
        context = RequestContext(
            request_id="test-123",
            timestamp=datetime.utcnow(),
            client_ip="127.0.0.1",
            user_agent="test",
            method="GET",
            path="/api/v1/test",
            query_params={},
            headers={},
        )

        data = {"message": "Hello World"}
        response = processor.create_optimized_response(data, context)

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == "test-123"

    @pytest.mark.asyncio
    async def test_request_deduplication(self, processor, mock_redis):
        """Test request deduplication"""
        processor._redis_client = mock_redis

        # Mock Redis responses
        mock_redis.get.return_value = None  # No existing result
        mock_redis.setex.return_value = None

        context = RequestContext(
            request_id="test-123",
            timestamp=datetime.utcnow(),
            client_ip="127.0.0.1",
            user_agent="test",
            method="GET",
            path="/api/v1/users",
            query_params={"id": "123"},
            headers={},
        )

        cache_key = processor.create_deduplication_key(context)

        # First request - should not find cached result
        result = await processor.deduplicate_request(context, cache_key)
        assert result is None

        # Cache the result
        await processor.cache_deduplication_result(cache_key, {"data": "test"})

    def test_batch_processing_configuration(self, processor):
        """Test batch processing configuration"""
        assert processor.batch_processing_enabled is True
        assert processor.batch_size == 10
        assert processor.batch_timeout_ms == 50

    def test_processing_statistics(self, processor):
        """Test processing statistics"""
        stats = processor.get_processing_stats()

        assert "total_processed" in stats
        assert "active_concurrent" in stats
        assert "cache_hit_rate_percent" in stats
        assert "avg_processing_time_ms" in stats


# ==================== INTELLIGENT CACHE TESTS ====================


class TestIntelligentCache:
    """Test suite for IntelligentCache"""

    @pytest.fixture
    def cache(self):
        """Create intelligent cache instance"""
        return IntelligentCache(redis_url="redis://localhost:6379")

    @pytest.fixture
    def memory_cache(self):
        """Create memory cache instance"""
        return MemoryCache(max_size=100, max_memory_mb=1)

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock_client = AsyncMock(spec=redis.Redis)
        return mock_client

    def test_cache_key_generation(self, cache):
        """Test cache key generation"""
        key1 = cache._generate_cache_key("users", 123, active=True)
        key2 = cache._generate_cache_key("users", 123, active=True)
        key3 = cache._generate_cache_key("users", 456, active=True)

        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different key
        assert key1.startswith("cache:users:")

    def test_memory_cache_basic_operations(self, memory_cache):
        """Test memory cache basic operations"""
        # Set and get
        memory_cache.set("test_key", "test_value")
        result = memory_cache.get("test_key")
        assert result == "test_value"

        # Non-existent key
        result = memory_cache.get("non_existent")
        assert result is None

        # Update existing key
        memory_cache.set("test_key", "updated_value")
        result = memory_cache.get("test_key")
        assert result == "updated_value"

    def test_memory_cache_ttl(self, memory_cache):
        """Test memory cache TTL functionality"""
        # Set with TTL
        memory_cache.set("ttl_key", "ttl_value", ttl_seconds=1)
        result = memory_cache.get("ttl_key")
        assert result == "ttl_value"

        # Wait for expiration (simulated)
        entry = memory_cache.cache.get("ttl_key")
        if entry:
            entry.created_at = datetime.utcnow() - timedelta(seconds=2)
            result = memory_cache.get("ttl_key")
            assert result is None  # Should be expired

    def test_memory_cache_lru_eviction(self, memory_cache):
        """Test memory cache LRU eviction"""
        # Fill cache to capacity
        for i in range(150):  # More than max_size (100)
            memory_cache.set(f"key_{i}", f"value_{i}")

        # Should have evicted oldest entries
        assert len(memory_cache.cache) <= 100
        assert memory_cache.stats.evictions > 0

        # Most recently accessed keys should still be present
        assert memory_cache.get("key_149") is not None
        assert memory_cache.get("key_0") is None  # Should be evicted

    def test_memory_cache_tag_invalidation(self, memory_cache):
        """Test memory cache tag-based invalidation"""
        # Set entries with tags
        memory_cache.set("user_1", "data_1", tags=["user"])
        memory_cache.set("user_2", "data_2", tags=["user"])
        memory_cache.set("post_1", "data_3", tags=["post"])

        # Invalidate by tag
        invalidated = memory_cache.invalidate_by_tags(["user"])
        assert invalidated == 2

        # Check results
        assert memory_cache.get("user_1") is None
        assert memory_cache.get("user_2") is None
        assert memory_cache.get("post_1") is not None  # Should still exist

    @pytest.mark.asyncio
    async def test_intelligent_cache_get_set(self, cache, mock_redis):
        """Test intelligent cache get/set operations"""
        cache._redis_client = mock_redis

        # Mock Redis responses
        mock_redis.get.return_value = None  # Cache miss
        mock_redis.setex.return_value = None

        # Set value
        await cache.set("test_key", "test_value", ttl_seconds=3600)

        # Get value (L1 hit)
        result = await cache.get("test_key")
        assert result == "test_value"

        # Verify Redis was called for L2 storage
        mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_intelligent_cache_hierarchy(self, cache, mock_redis):
        """Test cache hierarchy (L1 -> L2)"""
        cache._redis_client = mock_redis

        # Mock L2 hit
        test_value = pickle.dumps("l2_value")
        mock_redis.get.return_value = test_value

        # Get from cache (should hit L2 and populate L1)
        result = await cache.get("test_key")
        assert result == "l2_value"

        # Second get should hit L1
        l1_result = cache.l1_cache.get("test_key")
        assert l1_result == "l2_value"

    @pytest.mark.asyncio
    async def test_cache_warming(self, cache):
        """Test cache warming functionality"""

        # Register cache warmer
        async def sample_warmer():
            return {"user_1": "data_1", "user_2": "data_2"}

        cache.register_cache_warmer("users", sample_warmer)

        # Warm cache
        warmed_count = await cache.warm_cache("users", sample_warmer)
        assert warmed_count == 2

    def test_cache_hit_rate_calculation(self, cache):
        """Test cache hit rate calculation"""
        cache.stats.cache_hits = 80
        cache.stats.cache_misses = 20

        hit_rate = cache.get_hit_rate()
        assert hit_rate.value == "good"  # 80% hit rate

    @pytest.mark.asyncio
    async def test_cache_statistics(self, cache):
        """Test comprehensive cache statistics"""
        stats = cache.get_comprehensive_stats()

        assert "overall" in stats
        assert "l1_memory" in stats
        assert "configuration" in stats
        assert "cache_warmers" in stats

        overall = stats["overall"]
        assert "total_requests" in overall
        assert "hit_rate_percent" in overall
        assert "hit_rate_classification" in overall


# ==================== RESPONSE TRANSFORMER TESTS ====================


class TestResponseTransformer:
    """Test suite for ResponseTransformer"""

    @pytest.fixture
    def transformer(self):
        """Create response transformer instance"""
        return ResponseTransformer()

    def test_client_type_detection(self, transformer):
        """Test client type detection"""
        # Mobile client
        request = MockRequest(
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS)"}
        )
        client_type = transformer.detect_client_type(request)
        assert client_type.value == "mobile"

        # Desktop client
        request = MockRequest(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"})
        client_type = transformer.detect_client_type(request)
        assert client_type.value == "desktop"

        # API client
        request = MockRequest(headers={"User-Agent": "", "Accept": "application/json"})
        client_type = transformer.detect_client_type(request)
        assert client_type.value == "api"

    def test_response_format_determination(self, transformer):
        """Test response format determination"""
        # JSON format
        request = MockRequest(headers={"Accept": "application/json"})
        format_type = transformer.determine_response_format(request)
        assert format_type.value == "json"

        # XML format
        request = MockRequest(headers={"Accept": "application/xml"})
        format_type = transformer.determine_response_format(request)
        assert format_type.value == "xml"

        # Query parameter override
        request = MockRequest(query_params={"format": "csv"})
        format_type = transformer.determine_response_format(request)
        assert format_type.value == "csv"

    def test_transformation_config_creation(self, transformer):
        """Test transformation configuration creation"""
        request = MockRequest(
            headers={"User-Agent": "Mozilla/5.0 (iPhone)"},
            query_params={"pretty": "true", "fields": "id,name"},
        )

        config = transformer.create_transformation_config(request)

        assert config.client_type.value == "mobile"
        assert config.pretty_print is True
        assert config.filter_fields == ["id", "name"]

    @pytest.mark.asyncio
    async def test_data_transformation(self, transformer):
        """Test data transformation"""
        config = TransformationConfig(
            case_style=TransformationRule.CAMEL_CASE,
            filter_fields=["user_id", "user_name"],
            pretty_print=True,
        )

        data = {
            "user_id": 123,
            "user_name": "John Doe",
            "email_address": "john@example.com",
            "created_at": "2024-01-01",
        }

        result = await transformer._apply_transformations(data, config)

        assert "userId" in result  # Camel case conversion
        assert "userName" in result
        assert "user_id" not in result  # Original snake case removed
        assert "email_address" not in result  # Filtered out
        assert "created_at" not in result

    def test_case_conversion(self, transformer):
        """Test case style conversion"""
        # Camel case
        result = transformer._to_camel_case("user_name")
        assert result == "userName"

        # Snake case
        result = transformer._to_snake_case("userName")
        assert result == "user_name"

        # Kebab case
        result = transformer._to_kebab_case("user_name")
        assert result == "user-name"

    @pytest.mark.asyncio
    async def test_format_conversion(self, transformer):
        """Test format conversion"""
        data = {"message": "Hello World", "count": 42}

        # JSON format
        json_result = await transformer._to_json(data)
        assert isinstance(json_result, str)
        assert "message" in json_result

        # XML format
        xml_result = await transformer._to_xml(data)
        assert isinstance(xml_result, str)
        assert "<message>" in xml_result
        assert "<count>" in xml_result

        # CSV format
        csv_data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        csv_result = await transformer._to_csv(csv_data)
        assert isinstance(csv_result, str)
        assert "name,age" in csv_result

    @pytest.mark.asyncio
    async def test_response_transformation_pipeline(self, transformer):
        """Test complete response transformation pipeline"""
        config = TransformationConfig(
            format=ResponseFormat.JSON,
            client_type=ClientType.WEB,
            include_metadata=True,
            pretty_print=True,
        )

        metadata = ResponseMetadata(
            request_id="test-123",
            timestamp=datetime.utcnow(),
            processing_time_ms=150.5,
            format=ResponseFormat.JSON,
            client_type=ClientType.WEB,
        )

        data = {"message": "Hello World"}
        response = await transformer.transform_response(data, config, metadata)

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == "test-123"


# ==================== VALIDATION FRAMEWORK TESTS ====================


class TestRequestValidator:
    """Test suite for RequestValidator"""

    @pytest.fixture
    def validator(self):
        """Create request validator instance"""
        return RequestValidator()

    def test_field_rule_addition(self, validator):
        """Test adding field validation rules"""
        validator.add_field_rule(
            field_name="email",
            rule_type=ValidationRule.EMAIL,
            level=ValidationLevel.ERROR,
            message="Invalid email format",
        )

        assert "email" in validator.validation_rules
        rules = validator.validation_rules["email"]
        assert len(rules) == 1
        assert rules[0].rule_type == ValidationRule.EMAIL

    def test_global_validator_addition(self, validator):
        """Test adding global validator"""

        def dummy_validator(data, request):
            return True

        validator.add_global_validator(dummy_validator, ValidationLevel.WARNING)

        assert len(validator.global_validators) == 1
        assert validator.global_validators[0][0] == dummy_validator
        assert validator.global_validators[0][1] == ValidationLevel.WARNING

    def test_field_cleaner_addition(self, validator):
        """Test adding field cleaner"""

        def dummy_cleaner(value):
            return str(value).strip()

        validator.add_field_cleaner("name", dummy_cleaner)

        assert "name" in validator.field_cleaners
        assert len(validator.field_cleaners["name"]) == 1

    @pytest.mark.asyncio
    async def test_request_validation_success(self, validator):
        """Test successful request validation"""
        # Add validation rules
        validator.add_field_rule("email", ValidationRule.REQUIRED)
        validator.add_field_rule("email", ValidationRule.EMAIL)

        data = {"email": "test@example.com"}
        result = await validator.validate_request(data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_request_validation_failure(self, validator):
        """Test request validation failure"""
        validator.add_field_rule("email", ValidationRule.REQUIRED)
        validator.add_field_rule("email", ValidationRule.EMAIL)

        data = {"email": "invalid-email"}
        result = await validator.validate_request(data)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("email" in error.field for error in result.errors)

    @pytest.mark.asyncio
    async def test_validation_with_cleaning(self, validator):
        """Test validation with data cleaning"""

        # Add cleaner
        def uppercase_cleaner(value):
            return str(value).upper()

        validator.add_field_cleaner("name", uppercase_cleaner)
        validator.add_field_rule("name", ValidationRule.REQUIRED)

        data = {"name": "john"}
        result = await validator.validate_request(data)

        assert result.is_valid is True
        assert result.cleaned_data["name"] == "JOHN"

    @pytest.mark.asyncio
    async def test_built_in_validators(self, validator):
        """Test built-in validators"""
        # Email validator
        is_valid = await validator._validate_email("test@example.com", {})
        assert is_valid is True

        is_valid = await validator._validate_email("invalid-email", {})
        assert is_valid is False

        # UUID validator
        is_valid = await validator._validate_uuid(
            "550e8400-e29b-41d4-a716-446655440000", {}
        )
        assert is_valid is True

        is_valid = await validator._validate_uuid("invalid-uuid", {})
        assert is_valid is False

        # Pattern validator
        is_valid = await validator._validate_pattern(
            "test123", {"pattern": r"^[a-z]+[0-9]+$"}
        )
        assert is_valid is True

        is_valid = await validator._validate_pattern(
            "Test123", {"pattern": r"^[a-z]+[0-9]+$"}
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validation_scopes(self, validator):
        """Test validation scopes"""
        # Add rules for different scopes
        validator.add_field_rule(
            "email", ValidationRule.EMAIL, level=ValidationLevel.ERROR
        )
        validator.add_field_rule(
            "age",
            ValidationRule.RANGE,
            level=ValidationLevel.WARNING,
            params={"min_value": 0, "max_value": 120},
        )

        data = {"email": "test@example.com", "age": 150}

        # Basic scope - should only check basic rules
        result = await validator.validate_request(data, scope=ValidationScope.BASIC)
        assert result.is_valid is True  # Email is valid, age not checked in basic scope

        # Comprehensive scope - should check all rules
        result = await validator.validate_request(
            data, scope=ValidationScope.COMPREHENSIVE
        )
        assert len(result.warnings) > 0  # Age should trigger warning

    def test_validation_statistics(self, validator):
        """Test validation statistics"""
        stats = validator.get_stats()

        assert "total_validations" in stats
        assert "successful_validations" in stats
        assert "failed_validations" in stats
        assert "avg_validation_time" in stats
        assert "rule_usage" in stats

    def test_pydantic_schema_creation(self, validator):
        """Test Pydantic schema creation"""
        field_definitions = {
            "name": {"type": str, "required": True},
            "age": {"type": int, "required": False, "default": 0},
            "email": {"type": str, "required": True},
        }

        schema_class = validator.create_pydantic_schema(field_definitions)

        # Test schema creation
        instance = schema_class(name="John", email="john@example.com")
        assert instance.name == "John"
        assert instance.age == 0
        assert instance.email == "john@example.com"


# ==================== BUILT-IN CLEANERS AND VALIDATORS ====================


class TestBuiltInUtilities:
    """Test built-in cleaners and validators"""

    def test_email_cleaner(self):
        """Test email cleaner"""
        from app.services.validation_framework import clean_email

        assert clean_email("  TEST@EXAMPLE.COM  ") == "test@example.com"
        assert clean_email(None) is None
        assert clean_email("") is None

    def test_phone_cleaner(self):
        """Test phone cleaner"""
        from app.services.validation_framework import clean_phone

        assert clean_phone("(555) 123-4567") == "5551234567"
        assert clean_phone("") == ""

    def test_name_cleaner(self):
        """Test name cleaner"""
        from app.services.validation_framework import clean_name

        assert clean_name("  john doe  ") == "John Doe"
        assert clean_name("") == ""

    def test_password_strength_validator(self):
        """Test password strength validator"""
        from app.services.validation_framework import validate_password_strength

        # Strong password
        assert validate_password_strength("Password123!") is True

        # Weak passwords
        assert validate_password_strength("weak") is False
        assert validate_password_strength("nouppercase123!") is False
        assert validate_password_strength("NOLOWERCASE123!") is False
        assert validate_password_strength("NoNumber!") is False
        assert validate_password_strength("NoSymbol123") is False

    def test_business_rules_validator(self):
        """Test business rules validator"""
        from app.services.validation_framework import validate_business_rules

        # Valid date range
        data = {"start_date": "2024-01-01T00:00:00", "end_date": "2024-01-02T00:00:00"}
        assert validate_business_rules(data) is True

        # Invalid date range
        data = {"start_date": "2024-01-02T00:00:00", "end_date": "2024-01-01T00:00:00"}
        assert validate_business_rules(data) is False


# ==================== INTEGRATION TESTS ====================


class TestAdvancedFunctionIntegration:
    """Integration tests for all advanced functions"""

    @pytest.mark.asyncio
    async def test_full_request_processing_pipeline(self):
        """Test complete request processing through all advanced services"""
        # Setup mock request
        request = MockRequest(
            method="POST",
            path="/api/v1/users",
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS)",
                "Content-Type": "application/json",
            },
            query_params={"format": "json", "pretty": "true"},
            json_data={
                "name": "  John Doe  ",
                "email": "JOHN.DOE@EXAMPLE.COM",
                "age": 25,
            },
        )

        # Initialize services
        processor = RequestProcessor()
        cache = IntelligentCache()
        transformer = ResponseTransformer()
        validator = RequestValidator()

        # Setup validation rules
        validator.add_field_rule("name", ValidationRule.REQUIRED)
        validator.add_field_rule("email", ValidationRule.REQUIRED)
        validator.add_field_rule("email", ValidationRule.EMAIL)

        try:
            # 1. Request processing context
            async with processor.process_request(request) as context:
                assert context is not None

            # 2. Data validation and cleaning
            validation_result = await validator.validate_request(
                request._json, request, scope=ValidationScope.COMPREHENSIVE
            )

            assert validation_result.is_valid is True
            assert validation_result.cleaned_data["name"] == "John Doe"
            assert validation_result.cleaned_data["email"] == "john.doe@example.com"

            # 3. Response transformation
            trans_config = transformer.create_transformation_config(request)
            response_data = {"user": validation_result.cleaned_data}
            response = await transformer.transform_response(response_data, trans_config)

            assert response.status_code == 200
            assert "X-Request-ID" in response.headers

        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance characteristics under load"""
        processor = RequestProcessor()
        cache = IntelligentCache()
        transformer = ResponseTransformer()
        validator = RequestValidator()

        # Setup validation
        validator.add_field_rule("id", ValidationRule.UUID)
        validator.add_field_rule("name", ValidationRule.REQUIRED)

        # Simulate high load
        start_time = time.time()
        tasks = []

        for i in range(100):
            request = MockRequest(
                method="GET",
                path=f"/api/v1/items/{i}",
                query_params={"id": f"550e8400-e29b-41d4-a716-44665544{i:04d}"},
            )

            # Create processing task
            task = processor.process_request(request).__aenter__()
            tasks.append(task)

        # Execute all processing tasks concurrently
        contexts = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Performance assertions
        assert duration < 5.0  # Should complete within 5 seconds
        assert len(contexts) == 100
        assert all(
            isinstance(ctx, RequestContext)
            for ctx in contexts
            if not isinstance(ctx, Exception)
        )

        # Test validation performance
        validation_tasks = []
        for i in range(50):
            data = {
                "id": f"550e8400-e29b-41d4-a716-44665544{i:04d}",
                "name": f"Item {i}",
            }
            task = validator.validate_request(data)
            validation_tasks.append(task)

        validation_results = await asyncio.gather(*validation_tasks)
        assert all(result.is_valid for result in validation_results)

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self):
        """Test error handling and resilience"""
        processor = RequestProcessor()
        cache = IntelligentCache()
        transformer = ResponseTransformer()
        validator = RequestValidator()

        # Test validation with invalid data
        validator.add_field_rule("email", ValidationRule.EMAIL)
        invalid_data = {"email": "invalid-email-format"}

        result = await validator.validate_request(invalid_data)
        assert result.is_valid is False
        assert len(result.errors) > 0

        # Test transformation with malformed data
        config = TransformationConfig(format=ResponseFormat.JSON)
        malformed_data = {
            "unserializable": object()
        }  # Object that can't be JSON serialized

        # Should handle gracefully
        response = await transformer.transform_response(malformed_data, config)
        assert response.status_code == 500  # Should return error response

        # Test cache with Redis failure
        with patch("redis.asyncio.from_url", side_effect=Exception("Redis down")):
            cache_result = await cache.get("test_key")
            assert cache_result is None  # Should handle Redis failure gracefully


# ==================== PERFORMANCE BENCHMARKS ====================


class TestPerformanceBenchmarks:
    """Performance benchmarks for advanced functions"""

    @pytest.mark.asyncio
    async def test_request_processor_performance(self):
        """Benchmark request processor performance"""
        processor = RequestProcessor()

        request = MockRequest(method="GET", path="/api/v1/test")

        iterations = 1000
        start_time = time.time()

        for _ in range(iterations):
            async with processor.process_request(request) as context:
                pass  # Just create context

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations * 1000

        # Should complete in under 5ms per request on average
        assert (
            avg_time < 5.0
        ), f"Request processor too slow: {avg_time:.2f}ms per request"

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Benchmark cache performance"""
        cache = MemoryCache(max_size=1000)

        # Benchmark set operations
        iterations = 1000
        start_time = time.time()

        for i in range(iterations):
            cache.set(f"key_{i}", f"value_{i}")

        set_time = (time.time() - start_time) / iterations * 1000

        # Benchmark get operations
        start_time = time.time()
        for i in range(iterations):
            cache.get(f"key_{i}")

        get_time = (time.time() - start_time) / iterations * 1000

        # Should be very fast for in-memory operations
        assert set_time < 1.0, f"Cache set too slow: {set_time:.2f}ms per operation"
        assert get_time < 0.5, f"Cache get too slow: {get_time:.2f}ms per operation"

    @pytest.mark.asyncio
    async def test_transformer_performance(self):
        """Benchmark response transformer performance"""
        transformer = ResponseTransformer()

        data = {
            "message": "Hello World",
            "data": [{"id": i, "name": f"Item {i}"} for i in range(100)],
        }
        config = TransformationConfig(
            format=ResponseFormat.JSON, case_style=TransformationRule.CAMEL_CASE
        )

        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            await transformer._apply_transformations(data, config)

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations * 1000

        # Should complete in under 10ms per transformation
        assert (
            avg_time < 10.0
        ), f"Transformer too slow: {avg_time:.2f}ms per transformation"

    @pytest.mark.asyncio
    async def test_validator_performance(self):
        """Benchmark validation performance"""
        validator = RequestValidator()

        # Add some validation rules
        validator.add_field_rule("id", ValidationRule.REQUIRED)
        validator.add_field_rule("name", ValidationRule.REQUIRED)
        validator.add_field_rule("email", ValidationRule.EMAIL)

        data = {"id": "test", "name": "Test User", "email": "test@example.com"}

        iterations = 500
        start_time = time.time()

        for _ in range(iterations):
            await validator.validate_request(data)

        end_time = time.time()
        avg_time = (end_time - start_time) / iterations * 1000

        # Should complete in under 2ms per validation
        assert avg_time < 2.0, f"Validator too slow: {avg_time:.2f}ms per validation"


# ==================== CONFIGURATION AND FIXTURES ====================


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
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )


# Custom assertions for better test readability
def assert_valid_context(context):
    """Assert that request context is valid"""
    assert context is not None
    assert hasattr(context, "request_id")
    assert hasattr(context, "timestamp")
    assert hasattr(context, "priority")
    assert context.request_id is not None
    assert context.timestamp is not None


def assert_valid_validation_result(result, should_be_valid=True):
    """Assert that validation result is as expected"""
    assert hasattr(result, "is_valid")
    assert hasattr(result, "errors")
    assert hasattr(result, "warnings")
    assert hasattr(result, "cleaned_data")
    assert result.is_valid == should_be_valid


def assert_valid_cache_entry(entry):
    """Assert that cache entry is valid"""
    assert entry is not None
    assert hasattr(entry, "key")
    assert hasattr(entry, "value")
    assert hasattr(entry, "created_at")
    assert entry.key is not None
    assert entry.created_at is not None
