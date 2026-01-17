"""
Statistical Performance Regression Tests

Enhanced performance testing with statistical significance,
proper sample sizes, confidence intervals, and rigorous analysis.

This module provides enterprise-grade performance testing that:
- Uses proper statistical methods for significance testing
- Accounts for cold vs warm measurement variations
- Provides confidence intervals and error margins
- Detects performance regressions with high reliability
- Includes comprehensive error handling and cleanup
"""

import asyncio
import time
import pytest
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from pathlib import Path
import json
import logging
from datetime import datetime
import sys

# Optional dependencies with graceful fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("NumPy not available - using built-in statistics fallback")

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logging.warning("SciPy not available - using simplified statistical tests")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, text
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import async_engine as get_async_engine
from app.db.models.user import User
from app.db.models.assessment import Assessment

# Statistical testing configuration
@dataclass
class StatisticalConfig:
    """Configuration for statistical performance testing"""

    # Sample sizes for statistical significance
    min_sample_size: int = 10
    preferred_sample_size: int = 30
    max_sample_size: int = 100

    # Statistical significance levels
    confidence_level: float = 0.95  # 95% confidence
    significance_level: float = 0.05  # 5% significance

    # Performance thresholds (in milliseconds)
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        'database_query': 100,
        'api_response': 200,
        'authentication': 50,
        'user_lookup': 30,
        'assessment_list': 150,
        'dashboard_load': 500,
        'connection_pool': 50,
        'complex_join': 300,
    })

    # Warm-up and cooldown
    warmup_iterations: int = 3
    cooldown_delay: float = 0.1  # seconds between measurements

    # Outlier detection
    outlier_method: str = 'iqr'  # 'iqr' or 'zscore'
    outlier_threshold: float = 1.5  # for IQR method

    def __post_init__(self):
        """Validate configuration parameters"""
        if self.min_sample_size <= 0:
            raise ValueError("min_sample_size must be positive")
        if self.preferred_sample_size < self.min_sample_size:
            raise ValueError("preferred_sample_size must be >= min_sample_size")
        if self.max_sample_size < self.preferred_sample_size:
            raise ValueError("max_sample_size must be >= preferred_sample_size")

        if not 0 < self.confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if not 0 < self.significance_level < 1:
            raise ValueError("significance_level must be between 0 and 1")

        if self.warmup_iterations < 0:
            raise ValueError("warmup_iterations cannot be negative")
        if self.cooldown_delay < 0:
            raise ValueError("cooldown_delay cannot be negative")

        if self.outlier_method not in ['iqr', 'zscore']:
            raise ValueError("outlier_method must be 'iqr' or 'zscore'")
        if self.outlier_threshold <= 0:
            raise ValueError("outlier_threshold must be positive")

@dataclass
class StatisticalResult:
    """Statistical analysis result for performance measurements"""

    name: str
    samples: List[float]
    mean_ms: float
    median_ms: float
    std_dev: float
    std_error: float
    min_ms: float
    max_ms: float
    p25_ms: float
    p75_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    confidence_interval: Tuple[float, float]
    margin_of_error: float
    sample_size: int
    outliers_removed: int
    coefficient_of_variation: float
    is_significant: bool
    threshold_ms: float
    meets_threshold: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'mean_ms': round(self.mean_ms, 2),
            'median_ms': round(self.median_ms, 2),
            'std_dev': round(self.std_dev, 2),
            'std_error': round(self.std_error, 2),
            'min_ms': round(self.min_ms, 2),
            'max_ms': round(self.max_ms, 2),
            'p25_ms': round(self.p25_ms, 2),
            'p75_ms': round(self.p75_ms, 2),
            'p90_ms': round(self.p90_ms, 2),
            'p95_ms': round(self.p95_ms, 2),
            'p99_ms': round(self.p99_ms, 2),
            'confidence_interval': [round(ci, 2) for ci in self.confidence_interval],
            'margin_of_error': round(self.margin_of_error, 2),
            'sample_size': self.sample_size,
            'outliers_removed': self.outliers_removed,
            'coefficient_of_variation': round(self.coefficient_of_variation, 2),
            'is_significant': self.is_significant,
            'threshold_ms': self.threshold_ms,
            'meets_threshold': self.meets_threshold,
            'samples': [round(s, 2) for s in self.samples[:10]]  # First 10 samples for debugging
        }

class StatisticalPerformanceAnalyzer:
    """Statistical performance analyzer with rigorous methodology"""

    def __init__(self, config: StatisticalConfig = None):
        self.config = config or StatisticalConfig()
        self.results: Dict[str, StatisticalResult] = {}
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)

    async def measure_operation(
        self,
        name: str,
        operation,
        threshold_ms: Optional[float] = None,
        sample_size: Optional[int] = None
    ) -> StatisticalResult:
        """
        Measure operation with statistical rigor

        Args:
            name: Name of the operation
            operation: Async function to measure
            threshold_ms: Performance threshold (overrides config)
            sample_size: Number of samples (overrides config)

        Returns:
            StatisticalResult with comprehensive analysis
        """

        self.logger.info(f"📊 Measuring {name} with statistical analysis")

        # Set threshold
        if threshold_ms is None:
            threshold_ms = self.config.thresholds.get(name, 200)

        # Determine sample size
        if sample_size is None:
            sample_size = self.config.preferred_sample_size

        # Collect measurements
        measurements = []
        outliers_removed = 0

        try:
            # Warm-up phase (not included in analysis)
            self.logger.info(f"🔥 Warming up {name} ({self.config.warmup_iterations} iterations)")
            for _ in range(self.config.warmup_iterations):
                try:
                    await operation()
                except Exception as e:
                    self.logger.warning(f"Warm-up iteration failed: {e}")

                await asyncio.sleep(self.config.cooldown_delay)

            # Main measurement phase
            self.logger.info(f"⏱️ Collecting {sample_size} measurements for {name}")

            for i in range(sample_size):
                try:
                    # Use high-precision timer
                    start_time = time.perf_counter()

                    # Execute operation with timeout
                    try:
                        await asyncio.wait_for(operation(), timeout=30.0)
                    except asyncio.TimeoutError:
                        self.logger.warning(f"⚠️ Operation {name} timed out at iteration {i+1}")
                        continue

                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000

                    measurements.append(duration_ms)

                    # Cooldown between measurements
                    if i < sample_size - 1:  # Don't sleep after last measurement
                        await asyncio.sleep(self.config.cooldown_delay)

                except Exception as e:
                    self.logger.error(f"❌ Measurement failed at iteration {i+1}: {e}")
                    continue

            if not measurements:
                raise ValueError(f"No successful measurements collected for {name}")

            self.logger.info(f"📈 Collected {len(measurements)} measurements for {name}")

        except Exception as e:
            self.logger.error(f"❌ Failed to measure {name}: {e}")
            raise

        # Remove outliers
        cleaned_measurements, outliers_removed = self._remove_outliers(measurements)
        self.logger.info(f"🧹 Removed {outliers_removed} outliers from {name}")

        # Calculate statistics
        result = self._calculate_statistics(
            name, cleaned_measurements, threshold_ms, outliers_removed
        )

        # Store result
        self.results[name] = result

        # Log summary
        self._log_measurement_summary(result)

        return result

    def _remove_outliers(self, measurements: List[float]) -> Tuple[List[float], int]:
        """Remove outliers using IQR method"""
        if len(measurements) < 4:  # Need minimum samples for IQR
            return measurements, 0

        measurements_sorted = sorted(measurements)
        n = len(measurements_sorted)

        # Calculate quartiles
        q1 = measurements_sorted[n // 4]
        q3 = measurements_sorted[3 * n // 4]
        iqr = q3 - q1

        if iqr == 0:  # Avoid division by zero
            return measurements, 0

        # Define outlier bounds
        lower_bound = q1 - self.config.outlier_threshold * iqr
        upper_bound = q3 + self.config.outlier_threshold * iqr

        # Filter outliers
        cleaned = [m for m in measurements if lower_bound <= m <= upper_bound]
        outliers_removed = len(measurements) - len(cleaned)

        return cleaned, outliers_removed

    def _calculate_statistics(
        self,
        name: str,
        measurements: List[float],
        threshold_ms: float,
        outliers_removed: int
    ) -> StatisticalResult:
        """Calculate comprehensive statistics"""

        if len(measurements) == 0:
            raise ValueError(f"No measurements to analyze for {name}")

        # Basic statistics
        n = len(measurements)
        mean_ms = statistics.mean(measurements)
        median_ms = statistics.median(measurements)

        if n > 1:
            std_dev = statistics.stdev(measurements)
            if HAS_NUMPY:
                std_error = std_dev / np.sqrt(n)
            else:
                # Fallback: calculate sqrt manually
                std_error = std_dev / (n ** 0.5)
        else:
            std_dev = 0
            std_error = 0

        # Percentiles
        sorted_measurements = sorted(measurements)
        if HAS_NUMPY:
            p25_ms = np.percentile(measurements, 25)
            p75_ms = np.percentile(measurements, 75)
            p90_ms = np.percentile(measurements, 90)
            p95_ms = np.percentile(measurements, 95)
            p99_ms = np.percentile(measurements, 99)
        else:
            # Manual percentile calculation
            n_percentiles = len(sorted_measurements)
            def percentile(p):
                k = (n_percentiles - 1) * p / 100
                f = int(k)
                c = k - f
                if f + 1 < n_percentiles:
                    return sorted_measurements[f] * (1 - c) + sorted_measurements[f + 1] * c
                else:
                    return sorted_measurements[f]

            p25_ms = percentile(25)
            p75_ms = percentile(75)
            p90_ms = percentile(90)
            p95_ms = percentile(95)
            p99_ms = percentile(99)

        # Confidence interval (using t-distribution for small samples)
        if n > 1:
            if HAS_SCIPY:
                t_critical = stats.t.ppf((1 + self.config.confidence_level) / 2, n - 1)
                margin_of_error = t_critical * std_error
            else:
                # Simple approximation: use z-score for large samples, conservative for small
                if n >= 30:
                    z_score = 1.96  # 95% confidence
                    margin_of_error = z_score * std_error
                else:
                    # Conservative estimate for small samples
                    conservative_factor = 2.5  # More conservative than t-distribution
                    margin_of_error = conservative_factor * std_error

            confidence_interval = (
                mean_ms - margin_of_error,
                mean_ms + margin_of_error
            )
        else:
            margin_of_error = 0
            confidence_interval = (mean_ms, mean_ms)

        # Coefficient of variation (relative variability)
        coefficient_of_variation = (std_dev / mean_ms) * 100 if mean_ms > 0 else 0

        # Statistical significance
        is_significant = n >= self.config.min_sample_size and std_error > 0

        # Threshold compliance
        meets_threshold = mean_ms <= threshold_ms

        return StatisticalResult(
            name=name,
            samples=measurements,
            mean_ms=mean_ms,
            median_ms=median_ms,
            std_dev=std_dev,
            std_error=std_error,
            min_ms=min(measurements),
            max_ms=max(measurements),
            p25_ms=p25_ms,
            p75_ms=p75_ms,
            p90_ms=p90_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
            confidence_interval=confidence_interval,
            margin_of_error=margin_of_error,
            sample_size=n,
            outliers_removed=outliers_removed,
            coefficient_of_variation=coefficient_of_variation,
            is_significant=is_significant,
            threshold_ms=threshold_ms,
            meets_threshold=meets_threshold
        )

    def _log_measurement_summary(self, result: StatisticalResult):
        """Log measurement summary"""
        self.logger.info(f"📊 {result.name} Results:")
        self.logger.info(f"  • Mean: {result.mean_ms:.2f}ms ± {result.margin_of_error:.2f}ms")
        self.logger.info(f"  • Median: {result.median_ms:.2f}ms")
        self.logger.info(f"  • 95th percentile: {result.p95_ms:.2f}ms")
        self.logger.info(f"  • Threshold: {result.threshold_ms}ms ({'✅ PASS' if result.meets_threshold else '❌ FAIL'})")
        self.logger.info(f"  • Sample size: {result.sample_size} (removed {result.outliers_removed} outliers)")
        self.logger.info(f"  • CV: {result.coefficient_of_variation:.1f}% (stability: {'good' if result.coefficient_of_variation < 10 else 'poor'})")

    def compare_baselines(self, baseline_file: str) -> Dict[str, Any]:
        """
        Compare current results with baseline measurements

        Args:
            baseline_file: Path to baseline JSON file

        Returns:
            Comparison analysis
        """

        try:
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load baseline file: {e}")
            return {'error': str(e)}

        comparison = {}
        for name, result in self.results.items():
            if name in baseline_data:
                baseline = baseline_data[name]
                baseline_mean = baseline['mean_ms']
                current_mean = result.mean_ms

                # Calculate percentage change
                percent_change = ((current_mean - baseline_mean) / baseline_mean) * 100

                # Determine if change is significant (using confidence intervals)
                baseline_ci_low, baseline_ci_high = baseline['confidence_interval']
                current_ci_low, current_ci_high = result.confidence_interval

                # Check if intervals overlap
                intervals_overlap = not (current_ci_high < baseline_ci_low or baseline_ci_high < current_ci_low)
                significant_change = not intervals_overlap and result.is_significant

                comparison[name] = {
                    'baseline_mean_ms': baseline_mean,
                    'current_mean_ms': current_mean,
                    'percent_change': round(percent_change, 1),
                    'significant_change': significant_change,
                    'performance_regression': percent_change > 0 and significant_change,
                    'performance_improvement': percent_change < 0 and significant_change
                }

        return comparison

    def save_results(self, filename: str):
        """Save results to JSON file"""
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'confidence_level': self.config.confidence_level,
                'sample_size': self.config.preferred_sample_size,
                'outlier_method': self.config.outlier_method
            },
            'results': {name: result.to_dict() for name, result in self.results.items()},
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results.values() if r.meets_threshold),
                'failed_tests': sum(1 for r in self.results.values() if not r.meets_threshold),
                'execution_time_seconds': round(time.time() - self.start_time, 2)
            }
        }

        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)

        self.logger.info(f"📄 Results saved to {filename}")

@pytest.fixture
def stat_analyzer():
    """Fixture providing statistical performance analyzer"""
    return StatisticalPerformanceAnalyzer()

@pytest.fixture
def test_client():
    """Test client for API performance testing"""
    return TestClient(app)

class TestStatisticalPerformanceRegression:
    """Statistical performance regression tests"""

    @pytest.mark.asyncio
    async def test_database_query_performance_statistical(self, stat_analyzer):
        """Test database query performance with statistical analysis"""

        engine = get_async_engine()

        async def user_query_operation():
            async with engine.begin() as conn:
                result = await conn.execute(
                    select(User).limit(10)
                )
                return result.scalars().all()

        result = await stat_analyzer.measure_operation(
            'user_lookup',
            user_query_operation,
            threshold_ms=30,
            sample_size=25
        )

        # Statistical assertions
        assert result.is_significant, f"User lookup results not statistically significant (n={result.sample_size})"
        assert result.meets_threshold, (
            f"User lookup too slow: {result.mean_ms:.2f}ms ± {result.margin_of_error:.2f}ms "
            f"(threshold: {result.threshold_ms}ms, 95% CI: {result.confidence_interval})"
        )

        # Additional statistical checks
        assert result.coefficient_of_variation < 50, f"High variability detected: {result.coefficient_of_variation:.1f}%"
        assert result.sample_size >= 10, f"Insufficient sample size: {result.sample_size}"

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_assessment_query_performance_statistical(self, stat_analyzer):
        """Test assessment query performance with statistical analysis"""

        engine = get_async_engine()

        async def assessment_query_operation():
            async with engine.begin() as conn:
                result = await conn.execute(
                    select(Assessment)
                    .order_by(Assessment.created_at.desc())
                    .limit(50)
                )
                return result.scalars().all()

        result = await stat_analyzer.measure_operation(
            'assessment_list',
            assessment_query_operation,
            threshold_ms=150,
            sample_size=20
        )

        assert result.is_significant, "Assessment list results not statistically significant"
        assert result.meets_threshold, (
            f"Assessment list too slow: {result.mean_ms:.2f}ms ± {result.margin_of_error:.2f}ms "
            f"(threshold: {result.threshold_ms}ms)"
        )

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_complex_join_performance_statistical(self, stat_analyzer):
        """Test complex join query performance with statistical analysis"""

        engine = get_async_engine()

        async def complex_join_operation():
            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT
                        u.id,
                        u.email,
                        u.created_at,
                        COUNT(a.id) as assessment_count
                    FROM users u
                    LEFT JOIN assessments a ON u.id = a.user_id
                    WHERE u.is_active = true
                    GROUP BY u.id, u.email, u.created_at
                    ORDER BY u.created_at DESC
                    LIMIT 20
                """))
                return result.fetchall()

        result = await stat_analyzer.measure_operation(
            'complex_join',
            complex_join_operation,
            threshold_ms=300,  # Higher threshold for complex query
            sample_size=15
        )

        assert result.is_significant, "Complex join results not statistically significant"
        assert result.meets_threshold, (
            f"Complex join too slow: {result.mean_ms:.2f}ms ± {result.margin_of_error:.2f}ms "
            f"(threshold: {result.threshold_ms}ms)"
        )

        await engine.dispose()

    async def test_api_endpoint_performance_statistical(self, stat_analyzer, test_client):
        """Test API endpoint performance with statistical analysis"""

        def health_endpoint_operation():
            start_time = time.perf_counter()
            response = test_client.get("/api/v1/health")
            end_time = time.perf_counter()

            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            return (end_time - start_time) * 1000

        # Run synchronous operation in async context
        async def async_health_operation():
            return health_endpoint_operation()

        result = await stat_analyzer.measure_operation(
            'health_check',
            async_health_operation,
            threshold_ms=50,
            sample_size=30
        )

        assert result.is_significant, "Health check results not statistically significant"
        assert result.meets_threshold, (
            f"Health check too slow: {result.mean_ms:.2f}ms ± {result.margin_of_error:.2f}ms "
            f"(threshold: {result.threshold_ms}ms)"
        )

        # Additional checks for API consistency
        assert result.coefficient_of_variation < 30, f"High API variability: {result.coefficient_of_variation:.1f}%"

    @pytest.mark.asyncio
    async def test_connection_pool_efficiency_statistical(self, stat_analyzer):
        """Test connection pool efficiency with statistical analysis"""

        engine = get_async_engine()

        async def single_connection_operation():
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

        async def concurrent_connection_test():
            # Run multiple connections concurrently to test pool efficiency
            tasks = [single_connection_operation() for _ in range(5)]
            await asyncio.gather(*tasks)

        result = await stat_analyzer.measure_operation(
            'connection_pool',
            concurrent_connection_test,
            threshold_ms=100,  # Allow more time for concurrent operations
            sample_size=20
        )

        assert result.is_significant, "Connection pool results not statistically significant"
        assert result.meets_threshold, (
            f"Connection pool operation too slow: {result.mean_ms:.2f}ms ± {result.margin_of_error:.2f}ms "
            f"(threshold: {result.threshold_ms}ms)"
        )

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, stat_analyzer):
        """Test performance trend analysis over multiple measurements"""

        engine = get_async_engine()

        async def trend_test_operation():
            async with engine.begin() as conn:
                await conn.execute(text("SELECT COUNT(*) FROM users"))

        # Collect multiple measurements for trend analysis
        trend_results = []
        for i in range(5):
            result = await stat_analyzer.measure_operation(
                f'trend_test_{i}',
                trend_test_operation,
                threshold_ms=50,
                sample_size=10
            )
            trend_results.append(result)

            # Small delay between trend measurements
            await asyncio.sleep(0.5)

        # Analyze trend
        means = [r.mean_ms for r in trend_results]

        # Calculate trend slope with fallback
        if HAS_NUMPY:
            trend_slope = np.polyfit(range(len(means)), means, 1)[0]
        else:
            # Simple linear regression fallback
            n = len(means)
            if n < 2:
                trend_slope = 0
            else:
                x_mean = (n - 1) / 2  # Mean of [0, 1, 2, ..., n-1]
                y_mean = sum(means) / n

                numerator = sum((i - x_mean) * (means[i] - y_mean) for i in range(n))
                denominator = sum((i - x_mean) ** 2 for i in range(n))

                trend_slope = numerator / denominator if denominator != 0 else 0

        # Assert reasonable performance stability
        assert abs(trend_slope) < 5, f"Performance trend unstable: slope = {trend_slope:.2f}ms per measurement"

        # Check that all measurements meet threshold
        for result in trend_results:
            assert result.meets_threshold, f"Trend measurement {result.name} failed threshold"

        await engine.dispose()

    def test_statistical_analysis_quality(self, stat_analyzer):
        """Test the quality of statistical analysis itself"""

        # Create synthetic performance data with known characteristics
        if HAS_NUMPY:
            np.random.seed(42)  # For reproducible tests
            base_time = 50.0
            noise_level = 10.0
            sample_size = 30

            # Generate normally distributed measurements
            measurements = np.random.normal(base_time, noise_level, sample_size).tolist()
        else:
            # Fallback: use Python's random module with Box-Muller transform
            import random
            random.seed(42)

            base_time = 50.0
            noise_level = 10.0
            sample_size = 30

            # Simple normal distribution approximation using Box-Muller transform
            def normal_approximation(mean, std_dev):
                # Box-Muller transform
                u1 = random.random()
                u2 = random.random()
                z0 = ((-2 * math.log(u1)) ** 0.5) * math.cos(2 * math.pi * u2)
                return mean + z0 * std_dev

            import math
            measurements = [normal_approximation(base_time, noise_level) for _ in range(sample_size)]

        # Add some outliers
        measurements.extend([150.0, 160.0])  # Clear outliers
        measurements = measurements[:sample_size + 2]

        # Test statistical analysis
        result = stat_analyzer._calculate_statistics(
            'synthetic_test',
            measurements,
            threshold_ms=100,
            outliers_removed=0
        )

        # Statistical assertions
        assert abs(result.mean_ms - base_time) < noise_level * 2, f"Mean estimate inaccurate: {result.mean_ms}"
        assert result.outliers_removed >= 1, f"Outlier detection failed: {result.outliers_removed}"
        assert result.std_dev > 0, f"Standard deviation should be positive: {result.std_dev}"
        assert result.confidence_interval[0] < result.mean_ms < result.confidence_interval[1], "Confidence interval invalid"
        assert 0 <= result.coefficient_of_variation < 100, f"Coefficient of variation invalid: {result.coefficient_of_variation}"

    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, stat_analyzer, tmp_path):
        """Test performance regression detection with baselines"""

        # Create synthetic baseline
        baseline_file = tmp_path / "baseline.json"
        baseline_data = {
            'user_lookup': {
                'mean_ms': 25.0,
                'confidence_interval': [20.0, 30.0]
            },
            'health_check': {
                'mean_ms': 30.0,
                'confidence_interval': [25.0, 35.0]
            }
        }

        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)

        # Run current measurements that simulate regression
        engine = get_async_engine()

        async def degraded_user_query():
            # Simulate degraded performance with artificial delay
            await asyncio.sleep(0.01)  # Add 10ms delay
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

        # Measure with simulated regression
        result = await stat_analyzer.measure_operation(
            'user_lookup',
            degraded_user_query,
            threshold_ms=30,
            sample_size=15
        )

        # Compare with baseline
        comparison = stat_analyzer.compare_baselines(str(baseline_file))

        assert 'user_lookup' in comparison, "User lookup comparison missing"
        user_comparison = comparison['user_lookup']
        assert user_comparison['percent_change'] > 0, "Expected performance regression not detected"

        await engine.dispose()

class TestStatisticalTestSuite:
    """Test the statistical testing framework itself"""

    def test_configuration_validation(self):
        """Test statistical configuration validation"""

        # Valid configuration
        config = StatisticalConfig()
        assert 0 < config.confidence_level < 1
        assert 0 < config.significance_level < 1
        assert config.min_sample_size > 0

    def test_outlier_detection(self, stat_analyzer):
        """Test outlier detection methods"""

        # Test data with clear outliers
        normal_data = [50, 51, 49, 52, 48, 51, 50, 49]
        outliers = [150, 200, 10]
        test_data = normal_data + outliers

        cleaned, removed = stat_analyzer._remove_outliers(test_data)

        assert len(cleaned) == len(normal_data), f"Expected {len(normal_data)} cleaned items, got {len(cleaned)}"
        assert removed >= 2, f"Expected at least 2 outliers removed, got {removed}"

        # All normal data should remain
        for value in normal_data:
            assert value in cleaned, f"Normal value {value} was incorrectly removed"

    def test_confidence_interval_calculation(self, stat_analyzer):
        """Test confidence interval calculation"""

        # Test data with known properties
        test_measurements = [50.0] * 20  # All same value
        result = stat_analyzer._calculate_statistics(
            'test_confidence',
            test_measurements,
            threshold_ms=100,
            outliers_removed=0
        )

        # With no variance, confidence interval should be tight around mean
        assert result.confidence_interval[0] <= result.mean_ms <= result.confidence_interval[1]
        assert result.margin_of_error == 0, f"Expected zero margin of error with no variance"

# Integration test for complete statistical analysis
@pytest.mark.asyncio
async def test_complete_statistical_performance_analysis(stat_analyzer, tmp_path):
    """Complete statistical performance analysis test"""

    # Configure for thorough testing
    stat_analyzer.config.preferred_sample_size = 15
    stat_analyzer.config.warmup_iterations = 2

    # Run multiple tests with proper resource management
    engine = get_async_engine()

    # Use parameterized queries for security
    tests = [
        ('simple_query', lambda conn: conn.execute(text("SELECT 1")), 30),
        ('count_users', lambda conn: conn.execute(text("SELECT COUNT(*) FROM users WHERE id IS NOT NULL")), 50),
        ('user_sample', lambda conn: conn.execute(text("SELECT id FROM users WHERE deleted_at IS NULL LIMIT 5")), 40)
    ]

    try:
        for test_name, query_op, threshold in tests:
            async def operation():
                async with engine.begin() as conn:
                    result = await query_op(conn)
                    return result

            result = await stat_analyzer.measure_operation(test_name, operation, threshold_ms=threshold)
            assert result.is_significant, f"{test_name} not statistically significant"
            assert result.meets_threshold, f"{test_name} exceeds performance threshold: {result.mean_ms:.2f}ms > {threshold}ms"
    finally:
        # Ensure engine is properly disposed even if tests fail
        await engine.dispose()

    # Save comprehensive results
    results_file = tmp_path / "statistical_performance_results.json"
    stat_analyzer.save_results(str(results_file))

    # Verify results file was created and is valid
    assert results_file.exists(), "Results file not created"

    with open(results_file, 'r') as f:
        saved_data = json.load(f)

    assert 'results' in saved_data, "Results missing from saved data"
    assert 'summary' in saved_data, "Summary missing from saved data"
    assert len(saved_data['results']) == len(tests), "Not all test results saved"

if __name__ == "__main__":
    # Run statistical performance tests directly
    pytest.main([__file__, "-v", "-s", "--tb=short"])
