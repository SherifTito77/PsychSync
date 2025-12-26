#!/usr/bin/env python3
"""
Advanced API Load Testing Suite for 10K Concurrent Users
Comprehensive testing with multiple frameworks and scenarios
"""

import asyncio
import aiohttp
import time
import json
import statistics
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import logging
import sys
import os
import traceback
import hashlib
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('load_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Individual test result data structure"""
    user_id: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class LoadTestMetrics:
    """Comprehensive load test metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percentage: float
    total_data_transferred_mb: float

    def __post_init__(self):
        if self.median_response_time_ms == 0 and self.total_requests > 0:
            response_times = [r.response_time_ms for r in self._results if r.response_time_ms > 0]
            if response_times:
                self.median_response_time_ms = statistics.median(response_times)
                self.p95_response_time_ms = sorted(response_times)[int(len(response_times) * 0.95)]
                self.p99_response_time_ms = sorted(response_times)[int(len(response_times) * 0.99)]

class AdvancedAPILoadTester:
    """
    Advanced API load testing suite with multiple testing strategies
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[TestResult] = []
        self.concurrent_users = 10000
        self.ramp_up_time_seconds = 30
        self.test_duration_seconds = 120

        # Test endpoints and scenarios
        self.test_endpoints = {
            "health_check": {
                "path": "/api/v1/health",
                "method": "GET",
                "weight": 20,  # 20% of traffic
                "auth_required": False
            },
            "user_login": {
                "path": "/api/v1/auth/login",
                "method": "POST",
                "weight": 15,  # 15% of traffic
                "auth_required": False,
                "payload": {
                    "email": "test@example.com",
                    "password": "testpassword123"
                }
            },
            "get_assessments": {
                "path": "/api/v1/assessments",
                "method": "GET",
                "weight": 25,  # 25% of traffic
                "auth_required": True
            },
            "get_teams": {
                "path": "/api/v1/teams",
                "method": "GET",
                "weight": 20,  # 20% of traffic
                "auth_required": True
            },
            "get_user_profile": {
                "path": "/api/v1/users/me",
                "method": "GET",
                "weight": 10,  # 10% of traffic
                "auth_required": True
            },
            "create_assessment": {
                "path": "/api/v1/assessments",
                "method": "POST",
                "weight": 10,  # 10% of traffic
                "auth_required": True,
                "payload": {
                    "title": "Load Test Assessment",
                    "description": "Generated during load testing",
                    "assessment_type": "mbti"
                }
            }
        }

        # Error scenario testing
        self.error_scenarios = [
            "invalid_endpoint",
            "missing_auth",
            "invalid_payload",
            "rate_limit_bypass",
            "large_payload",
            "concurrent_same_user"
        ]

        # JWT tokens for authenticated requests
        self.auth_tokens: Dict[str, str] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        # Create session with optimized settings for high concurrency
        connector = aiohttp.TCPConnector(
            limit=1000,  # Total connection pool size
            limit_per_host=500,  # Connections per host
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(
            total=30,  # Total timeout
            connect=5,  # Connection timeout
            sock_read=10  # Read timeout
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'PsychSync-LoadTester/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def generate_test_user(self, user_id: int) -> Dict[str, Any]:
        """Generate test user data"""
        return {
            "email": f"loadtestuser{user_id}@example.com",
            "username": f"loadtestuser{user_id}",
            "password": "LoadTest123!@#",
            "full_name": f"Load Test User {user_id}",
            "organization": "Load Test Organization"
        }

    def generate_random_payload(self, base_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate randomized payload for testing"""
        payload = base_payload.copy()

        # Add random variations
        if "title" in payload:
            random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            payload["title"] = f"{payload['title']}-{random_suffix}"

        if "email" in payload:
            random_id = uuid.uuid4().hex[:8]
            payload["email"] = f"test-{random_id}@example.com"

        return payload

    async def register_test_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Register a test user and return JWT token"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    if "access_token" in data:
                        return data["access_token"]
        except Exception as e:
            logger.warning(f"Failed to register test user: {e}")

        return None

    async def authenticate_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Authenticate user and return JWT token"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "access_token" in data:
                        return data["access_token"]
        except Exception as e:
            logger.warning(f"Failed to authenticate user: {e}")

        return None

    async def get_auth_token(self, user_id: int) -> str:
        """Get or create authentication token for user"""
        cache_key = f"user_{user_id}"

        if cache_key not in self.auth_tokens:
            user_data = self.generate_test_user(user_id)

            # Try to register first, then login
            token = await self.register_test_user(user_data)
            if not token:
                token = await self.authenticate_user(user_data)

            if token:
                self.auth_tokens[cache_key] = token
            else:
                # Use a default test token for load testing
                self.auth_tokens[cache_key] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"

        return self.auth_tokens[cache_key]

    async def make_request(self, user_id: int, endpoint_config: Dict[str, Any]) -> TestResult:
        """Make a single API request and record metrics"""
        user_str = f"user_{user_id}"
        start_time = time.time()

        try:
            # Prepare headers
            headers = {}
            if endpoint_config.get("auth_required", False):
                token = await self.get_auth_token(user_id)
                headers["Authorization"] = f"Bearer {token}"

            # Prepare URL and payload
            url = f"{self.base_url}{endpoint_config['path']}"

            if endpoint_config["method"] == "GET":
                async with self.session.get(url, headers=headers) as response:
                    content = await response.read()
                    return TestResult(
                        user_id=user_str,
                        endpoint=endpoint_config["path"],
                        method=endpoint_config["method"],
                        status_code=response.status,
                        response_time_ms=(time.time() - start_time) * 1000,
                        response_size_bytes=len(content)
                    )

            elif endpoint_config["method"] == "POST":
                payload = endpoint_config.get("payload", {})
                if payload:
                    payload = self.generate_random_payload(payload)

                async with self.session.post(url, json=payload, headers=headers) as response:
                    content = await response.read()
                    return TestResult(
                        user_id=user_str,
                        endpoint=endpoint_config["path"],
                        method=endpoint_config["method"],
                        status_code=response.status,
                        response_time_ms=(time.time() - start_time) * 1000,
                        response_size_bytes=len(content)
                    )

        except asyncio.TimeoutError:
            return TestResult(
                user_id=user_str,
                endpoint=endpoint_config["path"],
                method=endpoint_config["method"],
                status_code=0,
                response_time_ms=30000,  # Timeout
                response_size_bytes=0,
                error_message="Request timeout"
            )

        except Exception as e:
            return TestResult(
                user_id=user_str,
                endpoint=endpoint_config["path"],
                method=endpoint_config["method"],
                status_code=0,
                response_time_ms=(time.time() - start_time) * 1000,
                response_size_bytes=0,
                error_message=str(e)
            )

    async def run_user_simulation(self, user_id: int, duration_seconds: int) -> List[TestResult]:
        """Simulate a single user's activity over time"""
        user_results = []
        end_time = time.time() + duration_seconds

        # Weighted random endpoint selection
        endpoints = []
        for name, config in self.test_endpoints.items():
            endpoints.extend([name] * config["weight"])

        while time.time() < end_time:
            # Random delay between requests (1-5 seconds)
            await asyncio.sleep(random.uniform(1, 5))

            # Select random endpoint
            endpoint_name = random.choice(endpoints)
            endpoint_config = self.test_endpoints[endpoint_name]

            # Make request
            result = await self.make_request(user_id, endpoint_config)
            user_results.append(result)

        return user_results

    async def run_ramp_up_load_test(self):
        """Run load test with gradual ramp-up of users"""
        logger.info(f"Starting ramp-up load test: {self.concurrent_users} users over {self.ramp_up_time_seconds}s")

        start_time = time.time()
        tasks = []
        users_per_second = self.concurrent_users / self.ramp_up_time_seconds

        # Gradually start users
        for i in range(self.concurrent_users):
            delay = i / users_per_second
            task = asyncio.create_task(
                self.run_user_simulation(i, self.test_duration_seconds)
            )
            tasks.append(task)

            # Schedule task with delay
            asyncio.get_event_loop().call_later(delay, task)

            # Add small delay to prevent overwhelming the system
            if i % 100 == 0:
                await asyncio.sleep(0.1)

        # Wait for all tasks to complete
        logger.info("All user simulations started, waiting for completion...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all results
        all_results = []
        for user_results in results:
            if isinstance(user_results, list):
                all_results.extend(user_results)
            elif isinstance(user_results, Exception):
                logger.error(f"User simulation failed: {user_results}")

        self.test_results = all_results
        return all_results

    async def run_burst_load_test(self, burst_size: int = 5000):
        """Run burst load test with sudden spike of users"""
        logger.info(f"Starting burst load test: {burst_size} concurrent users")

        # Start all users simultaneously
        tasks = []
        for i in range(burst_size):
            task = asyncio.create_task(
                self.run_user_simulation(i, 30)  # 30 second burst
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        all_results = []
        for user_results in results:
            if isinstance(user_results, list):
                all_results.extend(user_results)

        return all_results

    def calculate_metrics(self, results: List[TestResult]) -> LoadTestMetrics:
        """Calculate comprehensive load test metrics"""
        if not results:
            return LoadTestMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        successful = [r for r in results if 200 <= r.status_code < 300]
        failed = [r for r in results if r.status_code == 0 or r.status_code >= 400]

        response_times = [r.response_time_ms for r in results if r.response_time_ms > 0]

        if response_times:
            response_times.sort()
            median = statistics.median(response_times)
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
        else:
            median = p95 = p99 = 0

        total_time = max([r.timestamp for r in results]) - min([r.timestamp for r in results])
        rps = len(results) / max(total_time.total_seconds(), 1)

        total_bytes = sum([r.response_size_bytes for r in results])

        return LoadTestMetrics(
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            total_response_time_ms=sum(response_times),
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            median_response_time_ms=median,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            requests_per_second=rps,
            error_rate_percentage=(len(failed) / len(results)) * 100,
            total_data_transferred_mb=total_bytes / (1024 * 1024)
        )

    def generate_report(self, metrics: LoadTestMetrics, results: List[TestResult]) -> Dict[str, Any]:
        """Generate comprehensive load test report"""
        # Status code distribution
        status_codes = {}
        for result in results:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1

        # Endpoint performance
        endpoint_stats = {}
        for result in results:
            if result.endpoint not in endpoint_stats:
                endpoint_stats[result.endpoint] = {
                    "requests": 0,
                    "avg_response_time": 0,
                    "success_rate": 0
                }

            endpoint_stats[result.endpoint]["requests"] += 1

        # Error analysis
        errors = [r for r in results if r.error_message or r.status_code >= 400]
        common_errors = {}
        for error in errors:
            error_msg = error.error_message or f"HTTP {error.status_code}"
            common_errors[error_msg] = common_errors.get(error_msg, 0) + 1

        return {
            "test_summary": {
                "test_run_at": datetime.utcnow().isoformat(),
                "total_duration_minutes": (self.test_duration_seconds + self.ramp_up_time_seconds) / 60,
                "concurrent_users": self.concurrent_users,
                "ramp_up_time_seconds": self.ramp_up_time_seconds
            },
            "performance_metrics": asdict(metrics),
            "status_code_distribution": status_codes,
            "endpoint_performance": endpoint_stats,
            "error_analysis": {
                "total_errors": len(errors),
                "common_errors": common_errors,
                "error_rate": f"{metrics.error_rate_percentage:.2f}%"
            },
            "recommendations": self._generate_recommendations(metrics, common_errors)
        }

    def _generate_recommendations(self, metrics: LoadTestMetrics, errors: Dict[str, int]) -> List[str]:
        """Generate performance recommendations based on test results"""
        recommendations = []

        if metrics.avg_response_time_ms > 2000:
            recommendations.append("⚠️ High average response time (>2s). Consider optimizing database queries and adding caching.")

        if metrics.p95_response_time_ms > 5000:
            recommendations.append("🚨 Very high P95 response time (>5s). Server is struggling under load.")

        if metrics.error_rate_percentage > 5:
            recommendations.append(f"❌ High error rate ({metrics.error_rate_percentage:.1f}%). Investigate server capacity and error handling.")

        if "timeout" in str(errors).lower():
            recommendations.append("⏱️ Timeout errors detected. Consider increasing timeouts or optimizing performance.")

        if "connection" in str(errors).lower():
            recommendations.append("🔗 Connection errors detected. Check connection pool limits and server capacity.")

        if metrics.requests_per_second < 100 and self.concurrent_users > 1000:
            recommendations.append("📈 Low RPS for user count. Server may be bottlenecked. Consider horizontal scaling.")

        if metrics.error_rate_percentage < 1 and metrics.avg_response_time_ms < 500:
            recommendations.append("✅ Excellent performance! System handled load well.")

        return recommendations

async def main():
    """Main load testing execution"""
    print("🚀 Starting Advanced API Load Testing Suite")
    print("=" * 60)

    # Configuration
    BASE_URL = "http://localhost:8000"
    CONCURRENT_USERS = 10000
    RAMP_UP_TIME = 30
    TEST_DURATION = 120

    # Create load tester
    async with AdvancedAPILoadTester(BASE_URL) as tester:
        tester.concurrent_users = CONCURRENT_USERS
        tester.ramp_up_time_seconds = RAMP_UP_TIME
        tester.test_duration_seconds = TEST_DURATION

        logger.info(f"Testing against: {BASE_URL}")
        logger.info(f"Concurrent Users: {CONCURRENT_USERS}")
        logger.info(f"Ramp-up Time: {RAMP_UP_TIME}s")
        logger.info(f"Test Duration: {TEST_DURATION}s")

        print(f"\n🎯 Test Configuration:")
        print(f"   • Target API: {BASE_URL}")
        print(f"   • Concurrent Users: {CONCURRENT_USERS:,}")
        print(f"   • Ramp-up Period: {RAMP_UP_TIME}s")
        print(f"   • Test Duration: {TEST_DURATION}s")
        print(f"   • Total Test Time: {RAMP_UP_TIME + TEST_DURATION}s")

        # Run the load test
        start_time = time.time()
        print(f"\n⏱️  Starting load test at {datetime.utcnow().strftime('%H:%M:%S')} UTC...")

        try:
            results = await tester.run_ramp_up_load_test()
            metrics = tester.calculate_metrics(results)
            report = tester.generate_report(metrics, results)

            test_duration = time.time() - start_time

            print(f"\n✅ Load test completed in {test_duration:.1f}s")
            print("=" * 60)

            # Display results
            print(f"\n📊 PERFORMANCE SUMMARY:")
            print(f"   • Total Requests: {metrics.total_requests:,}")
            print(f"   • Successful: {metrics.successful_requests:,} ({(metrics.successful_requests/metrics.total_requests)*100:.1f}%)")
            print(f"   • Failed: {metrics.failed_requests:,} ({metrics.error_rate_percentage:.1f}%)")
            print(f"   • Requests/Second: {metrics.requests_per_second:.1f}")
            print(f"   • Data Transferred: {metrics.total_data_transferred_mb:.1f} MB")

            print(f"\n⚡ RESPONSE TIMES:")
            print(f"   • Average: {metrics.avg_response_time_ms:.0f}ms")
            print(f"   • Median: {metrics.median_response_time_ms:.0f}ms")
            print(f"   • P95: {metrics.p95_response_time_ms:.0f}ms")
            print(f"   • P99: {metrics.p99_response_time_ms:.0f}ms")
            print(f"   • Min: {metrics.min_response_time_ms:.0f}ms")
            print(f"   • Max: {metrics.max_response_time_ms:.0f}ms")

            print(f"\n🔍 ERROR ANALYSIS:")
            status_codes = report["status_code_distribution"]
            for code, count in sorted(status_codes.items()):
                percentage = (count / metrics.total_requests) * 100
                status_text = "✅ Success" if 200 <= code < 300 else "❌ Error"
                print(f"   • HTTP {code}: {count:,} ({percentage:.1f}%) - {status_text}")

            common_errors = report["error_analysis"]["common_errors"]
            if common_errors:
                print(f"\n🚨 COMMON ERRORS:")
                for error, count in sorted(common_errors.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / metrics.failed_requests) * 100
                    print(f"   • {error}: {count} ({percentage:.1f}%)")

            print(f"\n💡 RECOMMENDATIONS:")
            for i, recommendation in enumerate(report["recommendations"], 1):
                print(f"   {i}. {recommendation}")

            # Save detailed report
            report_file = f"load_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n📄 Detailed report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Load test failed: {e}")
            logger.error(traceback.format_exc())
            print(f"\n❌ Load test failed: {e}")

if __name__ == "__main__":
    # Check if server is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/health") as response:
                if response.status in [200, 401]:  # 401 is expected for protected endpoints
                    print("✅ API server is running")
                else:
                    print(f"⚠️  API server returned status {response.status}")
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("Please ensure the API server is running on http://localhost:8000")
        sys.exit(1)

    # Run the load test
    asyncio.run(main())