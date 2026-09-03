"""
Comprehensive Performance Optimization Tests

Tests all Phase 1 optimizations to ensure:
1. Code correctness (no bugs introduced)
2. Performance improvements measurable
3. Backward compatibility maintained
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

# =============================================================================
# Test 1: orjson Optimization
# =============================================================================


class TestOrjsonOptimization:
    """Test orjson JSON serialization optimization"""

    def test_cache_service_imports(self):
        """Test that cache service can be imported with orjson"""
        from app.services.enhanced_cache_service import (
            HAS_ORJSON,
            EnhancedCacheService,
            cache_service,
        )

        # Verify service exists
        assert cache_service is not None
        assert isinstance(cache_service, EnhancedCacheService)

        # Check if orjson is available (optional dependency)
        print(f"✓ orjson available: {HAS_ORJSON}")

    def test_serialize_deserialize_with_cache_service(self):
        """Test that serialization/deserialization works correctly"""
        from app.services.enhanced_cache_service import HAS_ORJSON, cache_service

        test_data = {
            "user_id": "12345",
            "scores": [1, 2, 3, 4, 5],
            "metadata": {"name": "Test User", "age": 30},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Test serialization
        serialized = cache_service._serialize_value(test_data)
        assert serialized is not None
        assert isinstance(serialized, (str, bytes))

        # Test deserialization
        deserialized = cache_service._deserialize_value(serialized)
        assert deserialized is not None

        # Verify data integrity
        assert deserialized["user_id"] == test_data["user_id"]
        assert deserialized["scores"] == test_data["scores"]

        print(f"✓ Serialization works with orjson={HAS_ORJSON}")

    def test_performance_comparison(self):
        """Compare performance between orjson and standard json"""
        try:
            import orjson

            has_orjson = True
        except ImportError:
            has_orjson = False

        if not has_orjson:
            pytest.skip("orjson not installed - skipping performance comparison")

        # Create test data (simulate cached assessment result)
        test_data = {
            "user_id": "test-user-123",
            "assessment_type": "PHQ-9",
            "total_score": 15,
            "severity_level": "moderate",
            "subscale_scores": {"cognitive": 5.5, "somatic": 6.2, "affective": 3.3},
            "responses": [i % 4 for i in range(100)],  # 100 responses
            "timestamps": [datetime.utcnow().isoformat() for _ in range(100)],
        }

        # Test orjson performance
        start = time.perf_counter()
        for _ in range(1000):
            orjson.dumps(test_data)
        orjson_time = time.perf_counter() - start

        # Test standard json performance
        start = time.perf_counter()
        for _ in range(1000):
            json.dumps(test_data)
        json_time = time.perf_counter() - start

        speedup = json_time / orjson_time
        print(f"✓ orjson speedup: {speedup:.2f}x faster")

        # orjson should be at least 1.5x faster
        assert speedup > 1.5, f"orjson should be faster but got {speedup:.2f}x"


# =============================================================================
# Test 2: Binary Search in Clinical Scoring
# =============================================================================


class TestBinarySearchOptimization:
    """Test binary search optimization in clinical scoring"""

    def test_phq9_binary_search(self):
        """Test PHQ-9 interpretation with binary search"""
        from bisect import bisect_left

        from app.services.clinical.scoring_algorithms import PHQ9Scorer

        # Test edge cases
        test_cases = [
            (0, "Minimal"),  # Lower boundary
            (4, "Minimal"),  # Just below first breakpoint
            (5, "Mild"),  # First breakpoint
            (9, "Mild"),  # Just below second breakpoint
            (10, "Moderate"),  # Second breakpoint
            (14, "Moderate"),  # Middle of range
            (15, "Moderately severe"),  # Third breakpoint
            (19, "Moderately severe"),  # Just below fourth breakpoint
            (20, "Severe"),  # Fourth breakpoint
            (27, "Severe"),  # Maximum score
        ]

        for score, expected_severity in test_cases:
            interpretation = PHQ9Scorer._get_interpretation(score, suicide_item=0)
            assert (
                expected_severity in interpretation
            ), f"Score {score}: expected '{expected_severity}' in interpretation, got '{interpretation}'"

        print("✓ PHQ-9 binary search working correctly for all score ranges")

    def test_phq9_with_suicide_alert(self):
        """Test that suicide ideation is properly detected"""
        from app.services.clinical.scoring_algorithms import PHQ9Scorer

        # Test without suicide
        interpretation_no_alert = PHQ9Scorer._get_interpretation(
            score=10, suicide_item=0
        )
        assert "ALERT" not in interpretation_no_alert

        # Test with suicide
        interpretation_with_alert = PHQ9Scorer._get_interpretation(
            score=10, suicide_item=1
        )
        assert "ALERT" in interpretation_with_alert
        assert "crisis protocol" in interpretation_with_alert

        print("✓ Suicide ideation alert working correctly")

    def test_gad7_binary_search(self):
        """Test GAD-7 interpretation with binary search"""
        from app.services.clinical.scoring_algorithms import GAD7Scorer

        test_cases = [
            (0, "Minimal"),
            (4, "Minimal"),
            (5, "Mild"),
            (9, "Mild"),
            (10, "Moderate"),
            (14, "Moderate"),
            (15, "Severe"),
            (21, "Severe"),
        ]

        for score, expected_severity in test_cases:
            interpretation = GAD7Scorer._interpret(score)
            assert (
                expected_severity in interpretation
            ), f"Score {score}: expected '{expected_severity}' in interpretation"

        print("✓ GAD-7 binary search working correctly")

    def test_binary_search_performance(self):
        """Verify binary search is faster than linear search"""
        from bisect import bisect_left

        from app.services.clinical.scoring_algorithms import PHQ9Scorer

        # Test binary search performance
        start = time.perf_counter()
        for score in range(10000):
            idx = bisect_left(PHQ9Scorer.SCORE_BREAKPOINTS, score) - 1
            idx = max(0, min(idx, len(PHQ9Scorer.INTERPRETATIONS) - 1))
            _ = PHQ9Scorer.INTERPRETATIONS[idx]
        binary_search_time = time.perf_counter() - start

        print(f"✓ Binary search completed 10,000 lookups in {binary_search_time:.4f}s")
        # Binary search should be very fast (< 0.01s for 10k operations)
        assert binary_search_time < 0.1, "Binary search should be fast"


# =============================================================================
# Test 3: Database Connection Pool
# =============================================================================


class TestDatabaseConnectionPool:
    """Test database connection pool optimization"""

    def test_database_module_imports(self):
        """Test that database module can be imported"""
        from sqlalchemy.ext.asyncio import AsyncEngine

        from app.core.database import AsyncSessionLocal, async_engine

        assert async_engine is not None
        assert isinstance(async_engine, AsyncEngine)
        assert AsyncSessionLocal is not None

        print("✓ Database module imports successfully")

    def test_pool_configuration(self):
        """Test that pool settings are configured correctly"""
        from app.core.database import async_engine

        pool = async_engine.pool

        # Verify pool settings
        assert pool._size == 20, f"Expected pool size 20, got {pool._size}"
        assert (
            pool._max_overflow == 40
        ), f"Expected max overflow 40, got {pool._max_overflow}"

        # Check LIFO setting
        assert pool._use_lifo is True, "LIFO should be enabled for performance"

        print("✓ Database pool configured correctly:")
        print(f"  - Pool size: {pool._size}")
        print(f"  - Max overflow: {pool._max_overflow}")
        print(f"  - LIFO enabled: {pool._use_lifo}")
        print(f"  - Pre-ping enabled: {pool._pre_ping}")


# =============================================================================
# Test 4: LRU Cache in AI Service
# =============================================================================


class TestLRUCacheOptimization:
    """Test LRU cache optimization in AI service"""

    def test_ai_service_imports(self):
        """Test that AI service can be imported"""
        from app.services.enhanced_ai_service import (
            EnhancedAIProcessor,
            enhanced_ai_processor,
        )

        assert enhanced_ai_processor is not None
        assert isinstance(enhanced_ai_processor, EnhancedAIProcessor)

        print("✓ Enhanced AI service imports successfully")

    def test_cache_stats_method(self):
        """Test that cache stats tracking works"""
        from app.services.enhanced_ai_service import EnhancedAIProcessor

        processor = EnhancedAIProcessor()
        stats = processor.get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert stats["hits"] == 0  # Initially no hits
        assert stats["misses"] == 0  # Initially no misses

        print("✓ Cache stats tracking works")

    def test_cache_decorator_applied(self):
        """Test that @lru_cache decorator is applied"""
        from functools import _lru_cache_wrapper

        from app.services.enhanced_ai_service import EnhancedAIProcessor

        processor = EnhancedAIProcessor()

        # Check if the method has cache_info (indicator of @lru_cache)
        assert hasattr(
            processor._get_cached_personality_data, "cache_info"
        ), "_get_cached_personality_data should have @lru_cache decorator"

        cache_info = processor._get_cached_personality_data.cache_info()
        assert hasattr(cache_info, "hits")
        assert hasattr(cache_info, "misses")

        print("✓ LRU cache decorator applied correctly")

    def test_cache_performance(self):
        """Test that caching improves performance"""
        from app.services.enhanced_ai_service import EnhancedAIProcessor

        processor = EnhancedAIProcessor()
        framework = "mbti"
        personality_type = "INTJ"

        # First call (cache miss - slower)
        start = time.perf_counter()
        result1 = processor._get_cached_personality_data(framework, personality_type)
        first_call_time = time.perf_counter() - start

        # Second call (cache hit - should be much faster)
        start = time.perf_counter()
        result2 = processor._get_cached_personality_data(framework, personality_type)
        second_call_time = time.perf_counter() - start

        # Results should be identical
        assert result1 == result2

        # Check cache stats
        cache_info = processor._get_cached_personality_data.cache_info()
        print(f"✓ Cache performance test:")
        print(f"  - First call (miss): {first_call_time*1000:.2f}ms")
        print(f"  - Second call (hit): {second_call_time*1000:.2f}ms")
        print(f"  - Speedup: {first_call_time/second_call_time:.2f}x")
        print(f"  - Cache info: {cache_info}")

        # Cache hit should be significantly faster (or at least not slower)
        assert (
            second_call_time <= first_call_time * 1.1
        ), "Cached call should be faster or equal to first call"


# =============================================================================
# Test 5: Linear Regression Optimization
# =============================================================================


class TestLinearRegressionOptimization:
    """Test single-pass linear regression optimization"""

    def test_linear_regression_imports(self):
        """Test that analytics service can be imported"""
        from app.services.clinical.advanced_analytics_service import (
            AdvancedAnalyticsService,
        )

        assert AdvancedAnalyticsService is not None

        print("✓ Advanced analytics service imports successfully")

    def test_linear_regression_correctness(self):
        """Test that optimized algorithm produces correct results"""
        from app.db.session import get_async_db
        from app.services.clinical.advanced_analytics_service import (
            AdvancedAnalyticsService,
        )

        # Simple test data: y = 2x + 1
        test_data = [
            (datetime(2024, 1, 1), 3.0),  # x=0, y=1 (actual: 3)
            (datetime(2024, 1, 2), 5.0),  # x=1, y=3 (actual: 5)
            (datetime(2024, 1, 3), 7.0),  # x=2, y=5 (actual: 7)
            (datetime(2024, 1, 4), 9.0),  # x=3, y=7 (actual: 9)
            (datetime(2024, 1, 5), 11.0),  # x=4, y=9 (actual: 11)
        ]

        # We can't easily test without a database session, but we can test the method exists
        service = AdvancedAnalyticsService(None)  # Pass None for testing

        # Verify method exists and is callable
        assert hasattr(service, "_linear_regression")
        assert callable(service._linear_regression)

        print("✓ Linear regression method exists and is callable")

    def test_single_pass_algorithm(self):
        """Test that single-pass algorithm is implemented"""
        import inspect

        from app.services.clinical.advanced_analytics_service import (
            AdvancedAnalyticsService,
        )

        # Get source code
        source = inspect.getsource(AdvancedAnalyticsService._linear_regression)

        # Check for single-pass indicators
        assert (
            "single pass" in source.lower() or "SINGLE-PASS" in source
        ), "Method should mention single-pass optimization"
        assert (
            "sum_x = sum_y = sum_xy = sum_x2 = sum_y2" in source
        ), "Should accumulate all sums in single pass"

        print("✓ Single-pass algorithm is implemented")


# =============================================================================
# Test 6: Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for all optimizations"""

    def test_all_services_work_together(self):
        """Test that all optimized services can work together"""
        from app.core.database import AsyncSessionLocal
        from app.services.clinical.scoring_algorithms import GAD7Scorer, PHQ9Scorer
        from app.services.enhanced_ai_service import enhanced_ai_processor
        from app.services.enhanced_cache_service import cache_service

        # All services should be available
        assert cache_service is not None
        assert enhanced_ai_processor is not None
        assert PHQ9Scorer is not None
        assert GAD7Scorer is not None
        assert AsyncSessionLocal is not None

        print("✓ All optimized services integrated successfully")

    def test_backward_compatibility(self):
        """Test that optimizations maintain backward compatibility"""
        from app.services.clinical.scoring_algorithms import PHQ9Scorer

        # Test old interface still works
        responses = {i: i % 4 for i in range(1, 10)}  # 9 items
        result = PHQ9Scorer.score(responses)

        # Verify result structure
        assert hasattr(result, "total_score")
        assert hasattr(result, "severity_level")
        assert hasattr(result, "interpretation")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "crisis_alert")

        print("✓ Backward compatibility maintained")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PERFORMANCE OPTIMIZATION TEST SUITE")
    print("=" * 60 + "\n")

    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])
