# tests/load_testing.py
"""
Comprehensive load testing framework for PsychSync
Includes performance testing, stress testing, and scalability analysis
"""

import asyncio
import time
import json
import logging
import statistics
import aiohttp
import random
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Configuration for load tests"""
    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    test_duration: int = 60  # seconds
    ramp_up_time: int = 10  # seconds
    requests_per_second: int = 100
    endpoints: List[str] = None
    headers: Dict[str, str] = None
    timeout: int = 30
    verify_ssl: bool = False

@dataclass
class RequestMetrics:
    """Individual request metrics"""
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    response_time: float
    response_size: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class LoadTestResults:
    """Comprehensive load test results"""
    test_name: str
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    throughput_mbps: float
    endpoints_stats: Dict[str, Dict[str, Any]]
    errors: List[str]

class LoadTestRunner:
    """Advanced load testing runner"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.metrics: List[RequestMetrics] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_tokens: List[str] = []  # Pool of authenticated user tokens
        self.test_data: Dict[str, Any] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        # Create HTTP session with optimized settings
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users * 2,
            limit_per_host=self.config.concurrent_users,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=5,
            sock_read=self.config.timeout
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.headers or {}
        )

        # Prepare test data
        await self.prepare_test_data()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def prepare_test_data(self):
        """Prepare test data including user accounts and tokens"""
        logger.info("Preparing test data...")

        # Create test users and get tokens
        for i in range(50):  # Create 50 test users
            user_data = {
                "email": f"testuser{i}@example.com",
                "full_name": f"Test User {i}",
                "password": "TestPassword123!"
            }

            try:
                async with self.session.post(
                    f"{self.config.base_url}/api/v1/auth/register",
                    json=user_data
                ) as response:
                    if response.status == 201:
                        user_info = await response.json()

                        # Login to get token
                        login_data = {
                            "username": user_data["email"],
                            "password": user_data["password"]
                        }

                        async with self.session.post(
                            f"{self.config.base_url}/api/v1/auth/token",
                            data=login_data
                        ) as token_response:
                            if token_response.status == 200:
                                token_info = await token_response.json()
                                self.user_tokens.append(token_info["access_token"])

            except Exception as e:
                logger.warning(f"Failed to create test user {i}: {str(e)}")

        logger.info(f"Created {len(self.user_tokens)} test user tokens")

        # Prepare test data for assessments
        self.test_data['assessment_templates'] = [
            {
                "name": f"Big Five Assessment {i}",
                "description": "Test Big Five personality assessment",
                "template_type": "assessment",
                "content": {
                    "framework": "big_five",
                    "questions": [
                        {"id": 1, "text": "I see myself as extraverted", "type": "scale"},
                        {"id": 2, "text": "I see myself as critical", "type": "scale"},
                        {"id": 3, "text": "I see myself as dependable", "type": "scale"},
                        {"id": 4, "text": "I see myself as anxious", "type": "scale"},
                        {"id": 5, "text": "I see myself as open to new experiences", "type": "scale"}
                    ]
                }
            } for i in range(10)
        ]

    async def run_load_test(self, test_name: str) -> LoadTestResults:
        """Run comprehensive load test"""
        logger.info(f"Starting load test: {test_name}")
        start_time = datetime.utcnow()

        # Initialize metrics collection
        self.metrics.clear()

        # Define endpoints to test
        if not self.config.endpoints:
            self.config.endpoints = [
                # Auth endpoints
                {"method": "POST", "path": "/api/v1/auth/login", "weight": 5},
                {"method": "POST", "path": "/api/v1/auth/register", "weight": 1},

                # User endpoints
                {"method": "GET", "path": "/api/v1/users/me", "weight": 10, "auth": True},
                {"method": "GET", "path": "/api/v1/users", "weight": 3, "auth": True},

                # Template endpoints
                {"method": "GET", "path": "/api/v1/templates", "weight": 8},
                {"method": "POST", "path": "/api/v1/templates", "weight": 2, "auth": True},

                # Health endpoint
                {"method": "GET", "path": "/health", "weight": 2}
            ]

        # Calculate total weight
        total_weight = sum(ep.get("weight", 1) for ep in self.config.endpoints)

        # Start load generation
        tasks = []
        for i in range(self.config.concurrent_users):
            # Stagger user start times for ramp-up
            delay = (i * self.config.ramp_up_time) / self.config.concurrent_users
            task = asyncio.create_task(
                self.user_simulation(i, delay, total_weight)
            )
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.utcnow()

        # Generate results
        results = self.generate_results(test_name, start_time, end_time)

        logger.info(f"Load test completed: {test_name}")
        logger.info(f"Total requests: {results.total_requests}")
        logger.info(f"Success rate: {100 - results.error_rate:.2f}%")
        logger.info(f"Avg response time: {results.avg_response_time:.3f}s")
        logger.info(f"RPS: {results.requests_per_second:.2f}")

        return results

    async def user_simulation(self, user_id: int, start_delay: float, total_weight: int):
        """Simulate user behavior"""
        await asyncio.sleep(start_delay)

        end_time = time.time() + self.config.test_duration

        # Get user token for authenticated requests
        user_token = None
        if self.user_tokens:
            user_token = random.choice(self.user_tokens)

        while time.time() < end_time:
            # Select endpoint based on weight
            endpoint = self.weighted_random_endpoint(total_weight)

            # Prepare request
            url = f"{self.config.base_url}{endpoint['path']}"
            method = endpoint['method']
            headers = {}

            if endpoint.get('auth', False) and user_token:
                headers['Authorization'] = f'Bearer {user_token}'

            # Prepare request data
            json_data = None
            if method == 'POST' and endpoint['path'] == '/api/v1/templates':
                json_data = random.choice(self.test_data['assessment_templates'])
            elif method == 'POST' and endpoint['path'] == '/api/v1/auth/register':
                json_data = {
                    "email": f"loadtest{user_id}{int(time.time())}@example.com",
                    "full_name": f"Load Test User {user_id}",
                    "password": "LoadTest123!"
                }
            elif method == 'POST' and endpoint['path'] == '/api/v1/auth/login':
                json_data = {
                    "username": f"loadtest{user_id}@example.com",
                    "password": "LoadTest123!"
                }

            # Execute request
            await self.execute_request(url, method, headers, json_data)

            # Respect requests per second limit
            await asyncio.sleep(1.0 / self.config.requests_per_second)

    def weighted_random_endpoint(self, total_weight: int) -> Dict[str, Any]:
        """Select endpoint based on weight"""
        random_weight = random.randint(1, total_weight)
        current_weight = 0

        for endpoint in self.config.endpoints:
            current_weight += endpoint.get("weight", 1)
            if random_weight <= current_weight:
                return endpoint

        return self.config.endpoints[0]  # Fallback

    async def execute_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None
    ):
        """Execute single HTTP request and collect metrics"""
        start_time = time.time()
        timestamp = datetime.utcnow()

        try:
            if method == 'GET':
                async with self.session.get(url, headers=headers) as response:
                    content = await response.read()
                    status_code = response.status
                    response_size = len(content)
                    success = 200 <= status_code < 400

            elif method == 'POST':
                async with self.session.post(url, headers=headers, json=json_data) as response:
                    content = await response.read()
                    status_code = response.status
                    response_size = len(content)
                    success = 200 <= status_code < 400

            elif method == 'PUT':
                async with self.session.put(url, headers=headers, json=json_data) as response:
                    content = await response.read()
                    status_code = response.status
                    response_size = len(content)
                    success = 200 <= status_code < 400

            elif method == 'DELETE':
                async with self.session.delete(url, headers=headers) as response:
                    content = await response.read()
                    status_code = response.status
                    response_size = len(content)
                    success = 200 <= status_code < 400

            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response_time = time.time() - start_time

            # Record metrics
            metric = RequestMetrics(
                timestamp=timestamp,
                endpoint=url,
                method=method,
                status_code=status_code,
                response_time=response_time,
                response_size=response_size,
                success=success,
                error_message=None if success else f"HTTP {status_code}"
            )
            self.metrics.append(metric)

        except Exception as e:
            response_time = time.time() - start_time
            metric = RequestMetrics(
                timestamp=timestamp,
                endpoint=url,
                method=method,
                status_code=0,
                response_time=response_time,
                response_size=0,
                success=False,
                error_message=str(e)
            )
            self.metrics.append(metric)

    def generate_results(
        self,
        test_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> LoadTestResults:
        """Generate comprehensive test results"""
        if not self.metrics:
            return LoadTestResults(
                test_name=test_name,
                config=self.config,
                start_time=start_time,
                end_time=end_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                requests_per_second=0.0,
                error_rate=100.0,
                throughput_mbps=0.0,
                endpoints_stats={},
                errors=["No requests executed"]
            )

        # Basic statistics
        total_requests = len(self.metrics)
        successful_requests = sum(1 for m in self.metrics if m.success)
        failed_requests = total_requests - successful_requests
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # Response time statistics
        response_times = [m.response_time for m in self.metrics]
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        p95_response_time = self.percentile(response_times, 95)
        p99_response_time = self.percentile(response_times, 99)

        # Throughput calculations
        test_duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        total_bytes = sum(m.response_size for m in self.metrics)
        throughput_mbps = (total_bytes * 8) / (test_duration * 1024 * 1024) if test_duration > 0 else 0

        # Endpoint statistics
        endpoints_stats = {}
        for metric in self.metrics:
            endpoint = metric.endpoint
            if endpoint not in endpoints_stats:
                endpoints_stats[endpoint] = {
                    'count': 0,
                    'success_count': 0,
                    'total_response_time': 0.0,
                    'min_response_time': float('inf'),
                    'max_response_time': 0.0,
                    'status_codes': {}
                }

            stats = endpoints_stats[endpoint]
            stats['count'] += 1
            if metric.success:
                stats['success_count'] += 1
            stats['total_response_time'] += metric.response_time
            stats['min_response_time'] = min(stats['min_response_time'], metric.response_time)
            stats['max_response_time'] = max(stats['max_response_time'], metric.response_time)

            status_code = str(metric.status_code)
            stats['status_codes'][status_code] = stats['status_codes'].get(status_code, 0) + 1

        # Calculate per-endpoint averages
        for endpoint, stats in endpoints_stats.items():
            if stats['count'] > 0:
                stats['avg_response_time'] = stats['total_response_time'] / stats['count']
                stats['success_rate'] = (stats['success_count'] / stats['count'] * 100)
                stats['error_rate'] = 100 - stats['success_rate']

        # Collect errors
        errors = [
            f"{m.error_message} ({m.endpoint})"
            for m in self.metrics
            if not m.success and m.error_message
        ]

        return LoadTestResults(
            test_name=test_name,
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            throughput_mbps=throughput_mbps,
            endpoints_stats=endpoints_stats,
            errors=errors[:100]  # Limit to first 100 errors
        )

    @staticmethod
    def percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

# Load test scenarios
class LoadTestScenarios:
    """Predefined load test scenarios"""

    @staticmethod
    def baseline_test() -> LoadTestConfig:
        """Baseline performance test"""
        return LoadTestConfig(
            concurrent_users=10,
            test_duration=60,
            ramp_up_time=10,
            requests_per_second=50,
            timeout=30
        )

    @staticmethod
    def stress_test() -> LoadTestConfig:
        """Stress test with high load"""
        return LoadTestConfig(
            concurrent_users=100,
            test_duration=300,  # 5 minutes
            ramp_up_time=30,
            requests_per_second=500,
            timeout=60
        )

    @staticmethod
    def spike_test() -> LoadTestConfig:
        """Spike test to simulate traffic spikes"""
        return LoadTestConfig(
            concurrent_users=200,
            test_duration=120,  # 2 minutes
            ramp_up_time=5,    # Quick ramp-up
            requests_per_second=1000,
            timeout=45
        )

    @staticmethod
    def endurance_test() -> LoadTestConfig:
        """Endurance test for stability"""
        return LoadTestConfig(
            concurrent_users=50,
            test_duration=3600,  # 1 hour
            ramp_up_time=60,
            requests_per_second=100,
            timeout=30
        )

# Pytest integration
@pytest.mark.asyncio
@pytest.mark.loadtesting
class TestLoadTesting:
    """Load testing test suite"""

    async def test_baseline_performance(self):
        """Test baseline performance under normal load"""
        config = LoadTestScenarios.baseline_test()

        async with LoadTestRunner(config) as runner:
            results = await runner.run_load_test("baseline_test")

            # Assertions
            assert results.error_rate < 5.0, f"Error rate too high: {results.error_rate}%"
            assert results.avg_response_time < 1.0, f"Average response time too high: {results.avg_response_time}s"
            assert results.p95_response_time < 2.0, f"P95 response time too high: {results.p95_response_time}s"
            assert results.requests_per_second > 40, f"RPS too low: {results.requests_per_second}"

    async def test_stress_performance(self):
        """Test performance under stress"""
        config = LoadTestScenarios.stress_test()

        async with LoadTestRunner(config) as runner:
            results = await runner.run_load_test("stress_test")

            # Stress test assertions (more lenient)
            assert results.error_rate < 20.0, f"Error rate too high under stress: {results.error_rate}%"
            assert results.avg_response_time < 5.0, f"Average response time too high under stress: {results.avg_response_time}s"
            assert results.requests_per_second > 200, f"RPS too low under stress: {results.requests_per_second}"

    async def test_api_endpoints_performance(self):
        """Test specific API endpoints performance"""
        config = LoadTestConfig(
            concurrent_users=20,
            test_duration=120,
            ramp_up_time=15,
            requests_per_second=100,
            endpoints=[
                {"method": "GET", "path": "/health", "weight": 10},
                {"method": "GET", "path": "/api/v1/templates", "weight": 5},
                {"method": "POST", "path": "/api/v1/auth/register", "weight": 2}
            ]
        )

        async with LoadTestRunner(config) as runner:
            results = await runner.run_load_test("endpoints_test")

            # Analyze per-endpoint performance
            for endpoint, stats in results.endpoints_stats.items():
                assert stats['error_rate'] < 10.0, f"High error rate for {endpoint}: {stats['error_rate']}%"
                assert stats['avg_response_time'] < 2.0, f"Slow response time for {endpoint}: {stats['avg_response_time']}s"

# Command-line interface for running load tests
async def run_load_test_scenario(scenario_name: str):
    """Run a specific load test scenario"""
    scenarios = {
        'baseline': LoadTestScenarios.baseline_test(),
        'stress': LoadTestScenarios.stress_test(),
        'spike': LoadTestScenarios.spike_test(),
        'endurance': LoadTestScenarios.endurance_test()
    }

    if scenario_name not in scenarios:
        logger.error(f"Unknown scenario: {scenario_name}")
        logger.info(f"Available scenarios: {list(scenarios.keys())}")
        return

    config = scenarios[scenario_name]

    logger.info(f"Running {scenario_name} load test...")
    logger.info(f"Configuration: {asdict(config)}")

    async with LoadTestRunner(config) as runner:
        results = await runner.run_load_test(scenario_name)

    # Print results
    print(f"\n{'='*60}")
    print(f"LOAD TEST RESULTS: {scenario_name.upper()}")
    print(f"{'='*60}")
    print(f"Test Duration: {(results.end_time - results.start_time).total_seconds():.1f}s")
    print(f"Total Requests: {results.total_requests:,}")
    print(f"Successful Requests: {results.successful_requests:,}")
    print(f"Failed Requests: {results.failed_requests:,}")
    print(f"Error Rate: {results.error_rate:.2f}%")
    print(f"Requests/Second: {results.requests_per_second:.2f}")
    print(f"Throughput: {results.throughput_mbps:.2f} Mbps")
    print(f"\nResponse Times:")
    print(f"  Average: {results.avg_response_time:.3f}s")
    print(f"  Minimum: {results.min_response_time:.3f}s")
    print(f"  Maximum: {results.max_response_time:.3f}s")
    print(f"  95th Percentile: {results.p95_response_time:.3f}s")
    print(f"  99th Percentile: {results.p99_response_time:.3f}s")

    print(f"\nEndpoint Performance:")
    for endpoint, stats in results.endpoints_stats.items():
        print(f"  {endpoint}:")
        print(f"    Requests: {stats['count']}")
        print(f"    Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"    Avg Response Time: {stats.get('avg_response_time', 0):.3f}s")

    if results.errors:
        print(f"\nTop Errors (first 10):")
        for error in results.errors[:10]:
            print(f"  - {error}")

    # Save results to file
    results_file = f"load_test_results_{scenario_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(results), f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python load_testing.py <scenario>")
        print("Available scenarios: baseline, stress, spike, endurance")
        sys.exit(1)

    scenario = sys.argv[1]
    asyncio.run(run_load_test_scenario(scenario))