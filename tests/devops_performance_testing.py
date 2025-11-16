# tests/devops_performance_testing.py
"""
Comprehensive DevOps Testing & Architecture Validation
Part 3: Performance Testing Framework

Advanced load testing, performance profiling, and scalability validation
for PsychSync AI platform using Locust and custom performance metrics.
"""

import asyncio
import json
import logging
import time
import uuid
import statistics
import psutil
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Performance testing configuration
PERFORMANCE_CONFIG = {
    'api_base_url': 'http://localhost:8000',
    'baseline_users': 10,
    'stress_users': 50,
    'spike_users': 100,
    'endurance_duration': 300,  # 5 minutes
    'ramp_up_time': 30,
    'test_timeout': 60,
    'response_time_threshold': 2000,  # 2 seconds
    'cpu_threshold': 80,  # 80% CPU
    'memory_threshold': 80,  # 80% memory
    'error_rate_threshold': 5  # 5% error rate
}

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    timestamp: float
    response_time: float
    status_code: int
    endpoint: str
    user_id: str
    error: Optional[str] = None

@dataclass
class PerformanceTestResult:
    """Performance test result data structure"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    details: str
    execution_time: float = 0.0
    metrics: Optional[List[PerformanceMetric]] = None
    statistics: Optional[Dict[str, Any]] = None
    system_metrics: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

class PerformanceTestFramework:
    """Comprehensive performance testing framework"""

    def __init__(self):
        self.results: List[PerformanceTestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_tokens: Dict[str, str] = {}
        self.test_users: List[Dict[str, Any]] = []

    async def setup(self):
        """Setup test environment"""
        logger.info("Setting up performance test environment...")

        # Create HTTP session with optimized settings for load testing
        connector = aiohttp.TCPConnector(
            limit=200,
            limit_per_host=100,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(total=PERFORMANCE_CONFIG['test_timeout'])
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )

        # Create test users
        await self._create_test_users()

    async def teardown(self):
        """Cleanup test environment"""
        logger.info("Cleaning up performance test environment...")

        if self.session:
            await self.session.close()

    async def _create_test_users(self):
        """Create test users for load testing"""
        logger.info("Creating test users...")

        for i in range(20):  # Create 20 test users
            user_data = {
                "email": f"perf-test-{i}-{uuid.uuid4()}@psychsync.test",
                "password": "TestSecurePassword123!",
                "full_name": f"Performance Test User {i}",
                "organization_name": "Performance Test Org"
            }

            try:
                async with self.session.post(
                    f"{PERFORMANCE_CONFIG['api_base_url']}/api/v1/auth/register",
                    json=user_data
                ) as response:
                    if response.status in [200, 201]:
                        # Login to get token
                        login_data = {
                            "username": user_data['email'],
                            "password": user_data['password']
                        }

                        async with self.session.post(
                            f"{PERFORMANCE_CONFIG['api_base_url']}/api/v1/auth/login",
                            data=login_data,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'}
                        ) as login_response:
                            if login_response.status == 200:
                                token_data = await login_response.json()
                                if 'access_token' in token_data:
                                    self.auth_tokens[user_data['email']] = token_data['access_token']
                                    self.test_users.append(user_data)
            except Exception as e:
                logger.warning(f"Failed to create test user {i}: {e}")

        logger.info(f"Created {len(self.test_users)} test users with authentication")

    async def _get_auth_header(self, user_index: int = 0) -> Dict[str, str]:
        """Get auth header for a test user"""
        if not self.test_users:
            return {}

        user_email = self.test_users[user_index % len(self.test_users)]['email']
        if user_email in self.auth_tokens:
            return {'Authorization': f'Bearer {self.auth_tokens[user_email]}'}
        return {}

    async def _simulate_user_request(self, endpoint: str, method: str = 'GET',
                                    data: Optional[Dict] = None, user_id: str = None) -> PerformanceMetric:
        """Simulate a single user request"""
        start_time = time.time()
        timestamp = start_time

        try:
            url = f"{PERFORMANCE_CONFIG['api_base_url']}{endpoint}"
            headers = await self._get_auth_header()

            async with self.session.request(method, url, json=data, headers=headers) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                await response.text()  # Consume response

                return PerformanceMetric(
                    timestamp=timestamp,
                    response_time=response_time,
                    status_code=response.status,
                    endpoint=endpoint,
                    user_id=user_id or str(uuid.uuid4())
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return PerformanceMetric(
                timestamp=timestamp,
                response_time=response_time,
                status_code=0,
                endpoint=endpoint,
                user_id=user_id or str(uuid.uuid4()),
                error=str(e)
            )

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network metrics
            network = psutil.net_io_counters()
            bytes_sent = network.bytes_sent
            bytes_recv = network.bytes_recv

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'threshold_met': cpu_percent > PERFORMANCE_CONFIG['cpu_threshold']
                },
                'memory': {
                    'percent': memory_percent,
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'threshold_met': memory_percent > PERFORMANCE_CONFIG['memory_threshold']
                },
                'disk': {
                    'percent': disk_percent,
                    'free_gb': disk.free / (1024**3),
                    'used_gb': disk.used / (1024**3)
                },
                'network': {
                    'bytes_sent': bytes_sent,
                    'bytes_recv': bytes_recv
                },
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    async def _calculate_statistics(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate performance statistics from metrics"""
        if not metrics:
            return {}

        response_times = [m.response_time for m in metrics if m.status_code > 0 and not m.error]
        successful_requests = [m for m in metrics if 200 <= m.status_code < 400]
        failed_requests = [m for m in metrics if m.status_code >= 400 or m.error]

        return {
            'total_requests': len(metrics),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': (len(successful_requests) / len(metrics) * 100) if metrics else 0,
            'error_rate': (len(failed_requests) / len(metrics) * 100) if metrics else 0,
            'response_time': {
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'mean': statistics.mean(response_times) if response_times else 0,
                'median': statistics.median(response_times) if response_times else 0,
                'p90': statistics.quantiles(response_times, n=10)[8] if len(response_times) >= 10 else (max(response_times) if response_times else 0),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else (max(response_times) if response_times else 0),
                'p99': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else (max(response_times) if response_times else 0)
            },
            'requests_per_second': len(metrics) / ((max(m.timestamp for m in metrics) - min(m.timestamp for m in metrics)) or 1),
            'endpoints': list(set(m.endpoint for m in metrics))
        }

    async def run_test(self, test_name: str, test_func):
        """Run a performance test with timing and error handling"""
        start_time = time.time()
        try:
            result = await test_func()
            execution_time = time.time() - start_time

            if isinstance(result, PerformanceTestResult):
                result.execution_time = execution_time
                self.results.append(result)
            else:
                # Convert to PerformanceTestResult
                self.results.append(PerformanceTestResult(
                    test_name=test_name,
                    status='PASS',
                    details=f"Test completed successfully",
                    execution_time=execution_time
                ))

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Performance test {test_name} failed: {str(e)}")
            self.results.append(PerformanceTestResult(
                test_name=test_name,
                status='FAIL',
                details=f"Test execution failed: {str(e)}",
                execution_time=execution_time
            ))

    async def test_baseline_performance(self) -> PerformanceTestResult:
        """Test 3.1.1: Baseline Performance Test"""
        logger.info("Running baseline performance test...")

        metrics = []
        num_users = PERFORMANCE_CONFIG['baseline_users']
        requests_per_user = 10

        # Simulate concurrent users
        tasks = []
        for user_id in range(num_users):
            for request_id in range(requests_per_user):
                tasks.append(self._simulate_user_request(
                    "/health",
                    user_id=f"baseline_user_{user_id}"
                ))

        # Execute all requests concurrently
        metrics = await asyncio.gather(*tasks)

        # Calculate statistics
        stats = await self._calculate_statistics(metrics)
        system_metrics = await self._get_system_metrics()

        # Evaluate results
        avg_response_time = stats['response_time']['mean']
        error_rate = stats['error_rate']

        if (avg_response_time <= PERFORMANCE_CONFIG['response_time_threshold'] and
            error_rate <= PERFORMANCE_CONFIG['error_rate_threshold']):
            status = "PASS"
            details = f"Baseline performance acceptable: {avg_response_time:.0f}ms avg, {error_rate:.1f}% error rate"
        elif avg_response_time <= PERFORMANCE_CONFIG['response_time_threshold'] * 1.5:
            status = "WARN"
            details = f"Baseline performance degraded: {avg_response_time:.0f}ms avg, {error_rate:.1f}% error rate"
            suggestions = ["Monitor response times", "Consider performance optimizations"]
        else:
            status = "FAIL"
            details = f"Baseline performance poor: {avg_response_time:.0f}ms avg, {error_rate:.1f}% error rate"
            suggestions = ["Immediate performance optimization required", "Check system resources"]

        return PerformanceTestResult(
            test_name="Baseline Performance Test",
            status=status,
            details=details,
            metrics=metrics,
            statistics=stats,
            system_metrics=system_metrics,
            suggestions=suggestions if status != "PASS" else None
        )

    async def test_stress_performance(self) -> PerformanceTestResult:
        """Test 3.1.2: Stress Performance Test"""
        logger.info("Running stress performance test...")

        metrics = []
        num_users = PERFORMANCE_CONFIG['stress_users']
        requests_per_user = 20

        # Simulate stress load with various endpoints
        endpoints = [
            "/health",
            "/api/v1/assessments",
            "/api/v1/teams"
        ]

        tasks = []
        for user_id in range(num_users):
            for request_id in range(requests_per_user):
                endpoint = endpoints[request_id % len(endpoints)]
                tasks.append(self._simulate_user_request(
                    endpoint,
                    user_id=f"stress_user_{user_id}"
                ))

        # Execute with batching to avoid overwhelming the system
        batch_size = 50
        all_metrics = []

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_metrics = await asyncio.gather(*batch)
            all_metrics.extend(batch_metrics)

            # Small delay between batches
            await asyncio.sleep(0.1)

        metrics = all_metrics
        stats = await self._calculate_statistics(metrics)
        system_metrics = await self._get_system_metrics()

        # Evaluate stress test results
        avg_response_time = stats['response_time']['mean']
        p95_response_time = stats['response_time']['p95']
        error_rate = stats['error_rate']
        cpu_threshold_met = system_metrics.get('cpu', {}).get('threshold_met', False)
        memory_threshold_met = system_metrics.get('memory', {}).get('threshold_met', False)

        # Stress test has higher thresholds
        stress_response_threshold = PERFORMANCE_CONFIG['response_time_threshold'] * 2
        stress_error_threshold = PERFORMANCE_CONFIG['error_rate_threshold'] * 2

        if (avg_response_time <= stress_response_threshold and
            error_rate <= stress_error_threshold and
            not cpu_threshold_met and
            not memory_threshold_met):
            status = "PASS"
            details = f"Stress test passed: {avg_response_time:.0f}ms avg, {error_rate:.1f}% error rate"
        elif (avg_response_time <= stress_response_threshold * 1.5 and
              error_rate <= stress_error_threshold * 1.5):
            status = "WARN"
            details = f"Stress test warning: {avg_response_time:.0f}ms avg, {error_rate:.1f}% error rate"
            suggestions = ["Monitor system under load", "Consider horizontal scaling"]
        else:
            status = "FAIL"
            details = f"Stress test failed: {avg_response_time:.0f}ms avg, {error_rate:.1f}% error rate"
            suggestions = ["System cannot handle stress load", "Immediate scaling required"]

        return PerformanceTestResult(
            test_name="Stress Performance Test",
            status=status,
            details=details,
            metrics=metrics,
            statistics=stats,
            system_metrics=system_metrics,
            suggestions=suggestions if status != "PASS" else None
        )

    async def test_spike_performance(self) -> PerformanceTestResult:
        """Test 3.1.3: Spike Performance Test"""
        logger.info("Running spike performance test...")

        metrics = []
        spike_users = PERFORMANCE_CONFIG['spike_users']

        # Create spike load
        tasks = []
        for user_id in range(spike_users):
            tasks.append(self._simulate_user_request(
                "/health",
                user_id=f"spike_user_{user_id}"
            ))

        # Execute spike load all at once
        spike_start = time.time()
        spike_metrics = await asyncio.gather(*tasks)
        spike_duration = time.time() - spike_start

        # Wait and test recovery
        await asyncio.sleep(5)
        recovery_tasks = []
        for user_id in range(10):  # Small recovery test
            recovery_tasks.append(self._simulate_user_request(
                "/health",
                user_id=f"recovery_user_{user_id}"
            ))

        recovery_metrics = await asyncio.gather(*recovery_tasks)

        # Combine all metrics
        metrics = spike_metrics + recovery_metrics
        stats = await self._calculate_statistics(metrics)

        # Evaluate spike test
        spike_response_times = [m.response_time for m in spike_metrics if m.status_code > 0]
        recovery_response_times = [m.response_time for m in recovery_metrics if m.status_code > 0]

        spike_avg = statistics.mean(spike_response_times) if spike_response_times else 0
        recovery_avg = statistics.mean(recovery_response_times) if recovery_response_times else 0

        if spike_avg <= PERFORMANCE_CONFIG['response_time_threshold'] * 3 and recovery_avg <= PERFORMANCE_CONFIG['response_time_threshold']:
            status = "PASS"
            details = f"Spike test passed: Spike {spike_avg:.0f}ms, Recovery {recovery_avg:.0f}ms"
        elif recovery_avg <= PERFORMANCE_CONFIG['response_time_threshold'] * 2:
            status = "WARN"
            details = f"Spike test warning: Recovery slower than expected ({recovery_avg:.0f}ms)"
            suggestions = ["Monitor recovery time after spikes", "Consider auto-scaling"]
        else:
            status = "FAIL"
            details = f"Spike test failed: System did not recover properly ({recovery_avg:.0f}ms)"
            suggestions = ["System cannot recover from spike loads", "Review scaling strategy"]

        return PerformanceTestResult(
            test_name="Spike Performance Test",
            status=status,
            details=details,
            metrics=metrics,
            statistics=stats,
            suggestions=suggestions if status != "PASS" else None
        )

    async def test_endurance_performance(self) -> PerformanceTestResult:
        """Test 3.1.4: Endurance Performance Test"""
        logger.info("Running endurance performance test...")

        metrics = []
        duration = PERFORMANCE_CONFIG['endurance_duration']
        concurrent_users = 5
        requests_per_second = 2

        start_time = time.time()
        end_time = start_time + duration

        # Run continuous load for specified duration
        async def continuous_user_load(user_id: int):
            user_metrics = []
            current_time = time.time()

            while current_time < end_time:
                metric = await self._simulate_user_request(
                    "/health",
                    user_id=f"endurance_user_{user_id}"
                )
                user_metrics.append(metric)

                # Wait to maintain requests per second rate
                await asyncio.sleep(1.0 / requests_per_second)
                current_time = time.time()

            return user_metrics

        # Start concurrent users
        tasks = [continuous_user_load(i) for i in range(concurrent_users)]
        user_metrics_lists = await asyncio.gather(*tasks)

        # Flatten all metrics
        for user_metrics in user_metrics_lists:
            metrics.extend(user_metrics)

        # Calculate statistics
        stats = await self._calculate_statistics(metrics)

        # Analyze performance degradation over time
        time_windows = 5  # Analyze in 5-minute windows
        if duration >= time_windows * 60:
            window_size = duration / time_windows
            window_stats = []

            for i in range(time_windows):
                window_start = start_time + (i * window_size)
                window_end = window_start + window_size

                window_metrics = [
                    m for m in metrics
                    if window_start <= m.timestamp < window_end
                ]

                if window_metrics:
                    window_response_times = [m.response_time for m in window_metrics if m.status_code > 0]
                    window_avg = statistics.mean(window_response_times) if window_response_times else 0
                    window_stats.append(window_avg)

            # Check for performance degradation
            if len(window_stats) >= 2:
                degradation = (window_stats[-1] - window_stats[0]) / window_stats[0] * 100 if window_stats[0] > 0 else 0
            else:
                degradation = 0
        else:
            degradation = 0

        # Evaluate endurance test
        avg_response_time = stats['response_time']['mean']
        error_rate = stats['error_rate']

        if (avg_response_time <= PERFORMANCE_CONFIG['response_time_threshold'] * 1.5 and
            error_rate <= PERFORMANCE_CONFIG['error_rate_threshold'] and
            degradation <= 20):  # Less than 20% degradation
            status = "PASS"
            details = f"Endurance test passed: {avg_response_time:.0f}ms avg, {degradation:.1f}% degradation"
        elif degradation <= 50:
            status = "WARN"
            details = f"Endurance test warning: {degradation:.1f}% performance degradation over time"
            suggestions = ["Monitor long-term performance", "Check for memory leaks"]
        else:
            status = "FAIL"
            details = f"Endurance test failed: {degradation:.1f}% performance degradation"
            suggestions = ["Significant performance degradation detected", "Investigate resource leaks"]

        return PerformanceTestResult(
            test_name="Endurance Performance Test",
            status=status,
            details=details,
            metrics=metrics,
            statistics=stats,
            suggestions=suggestions if status != "PASS" else None
        )

    async def test_database_performance(self) -> PerformanceTestResult:
        """Test 3.2.1: Database Performance Test"""
        logger.info("Running database performance test...")

        metrics = []

        # Test database-intensive endpoints
        db_endpoints = [
            "/api/v1/assessments",
            "/api/v1/teams",
            "/api/v1/users"
        ]

        for endpoint in db_endpoints:
            for i in range(20):
                metric = await self._simulate_user_request(
                    endpoint,
                    user_id=f"db_test_{i}"
                )
                metrics.append(metric)

        stats = await self._calculate_statistics(metrics)

        # Database-specific evaluation
        avg_response_time = stats['response_time']['mean']
        p95_response_time = stats['response_time']['p95']

        # Database operations should be faster
        db_response_threshold = PERFORMANCE_CONFIG['response_time_threshold'] * 0.8

        if avg_response_time <= db_response_threshold:
            status = "PASS"
            details = f"Database performance acceptable: {avg_response_time:.0f}ms average"
        elif avg_response_time <= db_response_threshold * 1.5:
            status = "WARN"
            details = f"Database performance slower than expected: {avg_response_time:.0f}ms average"
            suggestions = ["Check database query optimization", "Review database indexing"]
        else:
            status = "FAIL"
            details = f"Database performance poor: {avg_response_time:.0f}ms average"
            suggestions = ["Immediate database optimization required", "Check connection pooling"]

        return PerformanceTestResult(
            test_name="Database Performance Test",
            status=status,
            details=details,
            metrics=metrics,
            statistics=stats,
            suggestions=suggestions if status != "PASS" else None
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance testing report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])
        warned_tests = len([r for r in self.results if r.status == 'WARN'])

        total_time = sum(r.execution_time for r in self.results)

        # Aggregate all performance metrics
        all_metrics = []
        for result in self.results:
            if result.metrics:
                all_metrics.extend(result.metrics)

        overall_stats = None
        if all_metrics:
            overall_stats = asyncio.run(self._calculate_statistics(all_metrics))

        return {
            'test_suite': 'Performance Testing',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warned_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_execution_time': total_time,
                'total_requests': len(all_metrics) if all_metrics else 0
            },
            'overall_statistics': overall_stats,
            'test_results': [asdict(result) for result in self.results],
            'recommendations': self._generate_recommendations(),
            'performance_grade': self._calculate_performance_grade()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate performance testing recommendations"""
        recommendations = []

        failed_tests = [r for r in self.results if r.status == 'FAIL']
        warned_tests = [r for r in self.results if r.status == 'WARN']

        if failed_tests:
            recommendations.append("CRITICAL: Address all failed performance tests before production")

        if warned_tests:
            recommendations.append("Monitor and optimize areas with performance warnings")

        # Category-specific recommendations
        for result in self.results:
            if result.suggestions:
                recommendations.extend(result.suggestions)

        # General performance recommendations
        recommendations.extend([
            "Implement application performance monitoring (APM)",
            "Set up automated performance testing in CI/CD",
            "Consider horizontal scaling for high-load scenarios",
            "Optimize database queries and add proper indexing",
            "Implement caching strategies for frequently accessed data"
        ])

        return recommendations

    def _calculate_performance_grade(self) -> str:
        """Calculate overall performance grade"""
        if not self.results:
            return "NO_GRADE"

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])

        pass_rate = (passed_tests / total_tests) * 100

        if pass_rate >= 90 and failed_tests == 0:
            return "A"
        elif pass_rate >= 80 and failed_tests <= 1:
            return "B+"
        elif pass_rate >= 70 and failed_tests <= 2:
            return "B"
        elif pass_rate >= 60 and failed_tests <= 3:
            return "C"
        else:
            return "F"

# Pytest integration functions
@pytest.fixture
async def performance_test_framework():
    """Pytest fixture for PerformanceTestFramework"""
    framework = PerformanceTestFramework()
    await framework.setup()
    yield framework
    await framework.teardown()

@pytest.mark.asyncio
async def test_baseline_performance(performance_test_framework):
    """Pytest wrapper for baseline performance test"""
    await performance_test_framework.run_test(
        "Baseline Performance",
        performance_test_framework.test_baseline_performance
    )

@pytest.mark.asyncio
async def test_performance_validation_complete(performance_test_framework):
    """Complete performance validation test suite"""
    # Run all performance tests
    await performance_test_framework.run_test(
        "Baseline Performance",
        performance_test_framework.test_baseline_performance
    )
    await performance_test_framework.run_test(
        "Stress Performance",
        performance_test_framework.test_stress_performance
    )
    await performance_test_framework.run_test(
        "Spike Performance",
        performance_test_framework.test_spike_performance
    )
    await performance_test_framework.run_test(
        "Endurance Performance",
        performance_test_framework.test_endurance_performance
    )
    await performance_test_framework.run_test(
        "Database Performance",
        performance_test_framework.test_database_performance
    )

    # Generate report
    report = performance_test_framework.generate_report()

    # Save report to file
    report_path = Path(__file__).parent.parent / "test_reports" / "performance_testing_report.json"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Performance testing report saved to: {report_path}")

    # Assertions
    assert report['summary']['success_rate'] >= 60, "Performance testing success rate below 60%"
    assert report['performance_grade'] not in ['F'], "Performance grade is F - critical issues found"

    # Print summary
    print(f"\n⚡ Performance Testing Results:")
    print(f"   Grade: {report['performance_grade']}")
    print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Warnings: {report['summary']['warnings']}")
    print(f"   Total Requests: {report['summary']['total_requests']}")
    print(f"   Report: {report_path}")

# Main execution function
async def run_performance_testing():
    """Run performance testing independently"""
    framework = PerformanceTestFramework()

    try:
        await framework.setup()
        print("⚡ Starting Performance Testing...")
        print("=" * 50)

        # Run all tests
        await framework.run_test("Baseline Performance", framework.test_baseline_performance)
        await framework.run_test("Stress Performance", framework.test_stress_performance)
        await framework.run_test("Spike Performance", framework.test_spike_performance)
        await framework.run_test("Endurance Performance", framework.test_endurance_performance)
        await framework.run_test("Database Performance", framework.test_database_performance)

        # Generate and print report
        report = framework.generate_report()

        print(f"\n📊 Test Results:")
        print(f"   Total Tests: {report['summary']['total_tests']}")
        print(f"   Passed: {report['summary']['passed']}")
        print(f"   Failed: {report['summary']['failed']}")
        print(f"   Warnings: {report['summary']['warnings']}")
        print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"   Performance Grade: {report['performance_grade']}")
        print(f"   Total Requests: {report['summary']['total_requests']}")
        print(f"   Execution Time: {report['summary']['total_execution_time']:.3f}s")

        if report['overall_statistics']:
            stats = report['overall_statistics']
            print(f"\n📈 Overall Performance Statistics:")
            print(f"   Success Rate: {stats['success_rate']:.1f}%")
            print(f"   Error Rate: {stats['error_rate']:.1f}%")
            print(f"   Response Time - Mean: {stats['response_time']['mean']:.0f}ms")
            print(f"   Response Time - P95: {stats['response_time']['p95']:.0f}ms")
            print(f"   Response Time - P99: {stats['response_time']['p99']:.0f}ms")
            print(f"   Requests/Second: {stats['requests_per_second']:.1f}")

        print(f"\n📋 Detailed Results:")
        for result in framework.results:
            status_icon = "✅" if result.status == "PASS" else "⚠️" if result.status == "WARN" else "❌"
            print(f"   {status_icon} {result.test_name}")
            if result.status != "PASS":
                print(f"      → {result.details}")

        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")

        # Save report
        report_path = Path(__file__).parent.parent / "test_reports" / f"performance_testing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Full report saved: {report_path}")

        return report

    finally:
        await framework.teardown()

if __name__ == "__main__":
    asyncio.run(run_performance_testing())