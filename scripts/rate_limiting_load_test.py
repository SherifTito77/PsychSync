#!/usr/bin/env python3
"""
Rate Limiting Load Testing Script
Comprehensive load testing for PsychSync rate limiting system

Usage:
    python rate_limiting_load_test.py --scenario=basic --users=100 --rps=50
    python rate_limiting_load_test.py --scenario=burst --users=1000 --duration=60
    python rate_limiting_load_test.py --scenario=comprehensive --report=json
"""

import argparse
import asyncio
import concurrent.futures
import json
import random
import statistics
import sys
import threading
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp


@dataclass
class LoadTestResult:
    """Represents a single request result"""

    timestamp: float
    status_code: int
    response_time: float
    user_id: str
    endpoint: str
    rate_limited: bool = False
    error_message: Optional[str] = None


@dataclass
class LoadTestSummary:
    """Summary of load test results"""

    scenario: str
    total_requests: int
    successful_requests: int
    rate_limited_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    duration: float
    rate_limit_hit_rate: float
    error_rate: float


class RateLimitingLoadTester:
    """Load testing client for rate limiting scenarios"""

    def __init__(
        self, base_url: str = "http://localhost:8000", max_concurrent: int = 100
    ):
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.session = None
        self.results = []
        self.start_time = None
        self.end_time = None

        # Test user credentials
        self.test_users = [
            {"email": f"loadtestuser{i}@example.com", "password": "LoadTest123!"}
            for i in range(1, 101)  # 100 test users
        ]

        # Rate limiting test endpoints
        self.endpoints = {
            "public": [
                {"method": "GET", "path": "/api/v1/health", "auth": False},
                {"method": "GET", "path": "/api/v1/docs", "auth": False},
            ],
            "auth": [
                {"method": "POST", "path": "/api/v1/auth/login", "auth": False},
                {"method": "POST", "path": "/api/v1/auth/register", "auth": False},
                {"method": "POST", "path": "/api/v1/auth/refresh", "auth": True},
            ],
            "protected": [
                {"method": "GET", "path": "/api/v1/users/me", "auth": True},
                {"method": "GET", "path": "/api/v1/assessments", "auth": True},
                {"method": "POST", "path": "/api/v1/assessments", "auth": True},
            ],
        }

        self.auth_tokens = {}  # Store auth tokens per user

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=5)
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent, limit_per_host=self.max_concurrent
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "RateLimitLoadTester/1.0"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def get_auth_headers(self, user_id: str) -> Dict[str, str]:
        """Get authentication headers for a user"""
        if user_id in self.auth_tokens:
            return {"Authorization": f"Bearer {self.auth_tokens[user_id]}"}
        return {}

    async def authenticate_user(self, user_data: Dict) -> Optional[str]:
        """Authenticate a user and return access token"""
        try:
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"],
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if "data" in result and "access_token" in result["data"]:
                        return result["data"]["access_token"]
                    elif "access_token" in result:
                        return result["access_token"]
        except Exception as e:
            print(f"Authentication failed for {user_data['email']}: {e}")

        return None

    async def setup_users(self, num_users: int) -> List[str]:
        """Setup and authenticate test users"""
        print(f"🔐 Setting up {num_users} test users...")

        active_users = []
        for i in range(min(num_users, len(self.test_users))):
            user = self.test_users[i]
            user_id = f"user_{i+1}"

            # Try to authenticate user
            token = await self.authenticate_user(user)
            if token:
                self.auth_tokens[user_id] = token
                active_users.append(user_id)
            else:
                # Try to register user first
                try:
                    register_data = {
                        "email": user["email"],
                        "password": user["password"],
                        "full_name": f"Load Test User {i+1}",
                    }

                    async with self.session.post(
                        f"{self.base_url}/api/v1/auth/register", json=register_data
                    ) as response:
                        if response.status in [200, 201]:
                            # Now try to login
                            token = await self.authenticate_user(user)
                            if token:
                                self.auth_tokens[user_id] = token
                                active_users.append(user_id)
                except Exception as e:
                    print(f"Failed to setup user {user_id}: {e}")

        print(f"✅ Successfully setup {len(active_users)} users")
        return active_users

    async def make_request(
        self, endpoint: Dict, user_id: Optional[str] = None
    ) -> LoadTestResult:
        """Make a single request and measure rate limiting behavior"""
        timestamp = time.time()
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint['path']}"
            headers = {}

            # Add authentication if required
            if endpoint.get("auth") and user_id:
                headers.update(self.get_auth_headers(user_id))

            # Make request
            async with self.session.request(
                method=endpoint["method"],
                url=url,
                headers=headers,
                json={} if endpoint["method"] in ["POST", "PUT"] else None,
            ) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms

                # Check if rate limited
                rate_limited = response.status == 429

                # Read response for additional context
                response_text = await response.text()
                error_message = None
                if response.status >= 400:
                    try:
                        error_data = json.loads(response_text)
                        error_message = error_data.get("detail", response_text)
                    except (ValueError, TypeError, json.JSONDecodeError) as e:
                        error_message = response_text

                return LoadTestResult(
                    timestamp=timestamp,
                    status_code=response.status,
                    response_time=response_time,
                    user_id=user_id or "anonymous",
                    endpoint=endpoint["path"],
                    rate_limited=rate_limited,
                    error_message=error_message,
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return LoadTestResult(
                timestamp=timestamp,
                status_code=0,
                response_time=response_time,
                user_id=user_id or "anonymous",
                endpoint=endpoint["path"],
                rate_limited=False,
                error_message=str(e),
            )

    async def run_constant_load_test(
        self,
        requests_per_second: int,
        duration: int,
        users: List[str],
        endpoint_types: List[str],
    ) -> List[LoadTestResult]:
        """Run constant load test with specified RPS for duration"""
        print(
            f"🚀 Running constant load test: {requests_per_second} RPS for {duration}s"
        )

        results = []
        interval = 1.0 / requests_per_second
        end_time = time.time() + duration

        tasks = []
        request_count = 0

        while time.time() < end_time:
            # Select random user and endpoint
            user_id = random.choice(users) if users else None
            endpoint_type = random.choice(endpoint_types)
            endpoint = random.choice(self.endpoints[endpoint_type])

            # Schedule request
            tasks.append(self.make_request(endpoint, user_id))
            request_count += 1

            # Wait for interval
            await asyncio.sleep(interval)

            # Limit concurrent tasks
            if len(tasks) >= self.max_concurrent:
                # Wait for some tasks to complete
                done, pending = await asyncio.wait(
                    tasks[: self.max_concurrent // 2],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    results.append(task.result())
                tasks = list(pending)

        # Wait for remaining tasks
        for task in asyncio.as_completed(tasks):
            results.append(task.result())

        print(f"✅ Completed {len(results)} requests")
        return results

    async def run_burst_test(
        self, users: List[str], burst_size: int, burst_interval: float = 1.0
    ) -> List[LoadTestResult]:
        """Run burst test with sudden high traffic spikes"""
        print(f"💥 Running burst test: {burst_size} requests every {burst_interval}s")

        results = []
        bursts = 10  # Number of bursts

        for burst in range(bursts):
            print(f"   Burst {burst + 1}/{bursts}")

            # Create burst of requests
            tasks = []
            for i in range(burst_size):
                user_id = random.choice(users) if users else None
                endpoint = random.choice(
                    self.endpoints["public"] + self.endpoints["auth"]
                )
                tasks.append(self.make_request(endpoint, user_id))

            # Wait for all burst requests to complete
            burst_results = await asyncio.gather(*tasks)
            results.extend(burst_results)

            # Wait between bursts
            if burst < bursts - 1:
                await asyncio.sleep(burst_interval)

        print(f"✅ Burst test completed with {len(results)} total requests")
        return results

    async def run_tier_test(
        self, tier_users: Dict[str, List[str]]
    ) -> List[LoadTestResult]:
        """Test rate limiting across different user tiers"""
        print(f"🏆 Running tier-based test across {len(tier_users)} user tiers")

        results = []

        for tier, users in tier_users.items():
            print(f"   Testing {tier} tier with {len(users)} users")

            # Each tier gets different request patterns
            if tier == "anonymous":
                rps = 100  # High RPS for anonymous
                duration = 30
            elif tier == "basic":
                rps = 200
                duration = 30
            elif tier == "premium":
                rps = 500
                duration = 30
            else:
                rps = 1000
                duration = 30

            tier_results = await self.run_constant_load_test(
                requests_per_second=rps,
                duration=duration,
                users=users,
                endpoint_types=["public", "protected"] if users else ["public"],
            )
            results.extend(tier_results)

        print(f"✅ Tier test completed with {len(results)} total requests")
        return results

    def calculate_summary(
        self, results: List[LoadTestResult], scenario: str
    ) -> LoadTestSummary:
        """Calculate test summary statistics"""
        if not results:
            return LoadTestSummary(
                scenario=scenario,
                total_requests=0,
                successful_requests=0,
                rate_limited_requests=0,
                failed_requests=0,
                average_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                requests_per_second=0,
                duration=0,
                rate_limit_hit_rate=0,
                error_rate=0,
            )

        successful = [r for r in results if 200 <= r.status_code < 300]
        rate_limited = [r for r in results if r.rate_limited]
        failed = [r for r in results if r.status_code >= 400 or r.status_code == 0]

        response_times = [r.response_time for r in results if r.response_time > 0]

        duration = max(r.timestamp for r in results) - min(r.timestamp for r in results)
        rps = len(results) / duration if duration > 0 else 0

        return LoadTestSummary(
            scenario=scenario,
            total_requests=len(results),
            successful_requests=len(successful),
            rate_limited_requests=len(rate_limited),
            failed_requests=len(failed),
            average_response_time=(
                statistics.mean(response_times) if response_times else 0
            ),
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=(
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) > 20
                else 0
            ),
            p99_response_time=(
                statistics.quantiles(response_times, n=100)[98]
                if len(response_times) > 100
                else 0
            ),
            requests_per_second=rps,
            duration=duration,
            rate_limit_hit_rate=len(rate_limited) / len(results) * 100,
            error_rate=len(failed) / len(results) * 100,
        )

    def print_summary(self, summary: LoadTestSummary) -> None:
        """Print test summary"""
        print(f"\n📊 {summary.scenario.upper()} Load Test Results")
        print("=" * 50)
        print(f"Total Requests: {summary.total_requests:,}")
        print(
            f"Successful: {summary.successful_requests:,} ({(summary.successful_requests/summary.total_requests*100):.1f}%)"
        )
        print(
            f"Rate Limited: {summary.rate_limited_requests:,} ({summary.rate_limit_hit_rate:.1f}%)"
        )
        print(f"Failed: {summary.failed_requests:,} ({summary.error_rate:.1f}%)")
        print(f"Duration: {summary.duration:.1f}s")
        print(f"Requests/Second: {summary.requests_per_second:.1f}")

        print(f"\n⚡ Response Times:")
        print(f"Average: {summary.average_response_time:.0f}ms")
        print(f"Min: {summary.min_response_time:.0f}ms")
        print(f"Max: {summary.max_response_time:.0f}ms")
        print(f"95th percentile: {summary.p95_response_time:.0f}ms")
        print(f"99th percentile: {summary.p99_response_time:.0f}ms")

    def save_detailed_report(
        self, results: List[LoadTestResult], summary: LoadTestSummary, filename: str
    ) -> None:
        """Save detailed test report to JSON file"""
        report_data = {
            "test_info": {
                "scenario": summary.scenario,
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "max_concurrent": self.max_concurrent,
            },
            "summary": asdict(summary),
            "detailed_results": [
                {
                    "timestamp": r.timestamp,
                    "status_code": r.status_code,
                    "response_time_ms": r.response_time,
                    "user_id": r.user_id,
                    "endpoint": r.endpoint,
                    "rate_limited": r.rate_limited,
                    "error_message": r.error_message,
                }
                for r in results
            ],
            "analysis": {
                "rate_limiting_effectiveness": summary.rate_limit_hit_rate > 0,
                "performance_acceptable": summary.average_response_time < 1000,
                "error_rate_acceptable": summary.error_rate < 5,
                "rate_limiting_working": (
                    "✅" if summary.rate_limit_hit_rate > 0 else "❌"
                ),
                "performance_acceptable": (
                    "✅" if summary.average_response_time < 1000 else "❌"
                ),
                "error_rate_acceptable": "✅" if summary.error_rate < 5 else "❌",
            },
        }

        report_path = Path(filename)
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Rate limiting load tester")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL for API"
    )
    parser.add_argument(
        "--scenario",
        choices=["basic", "burst", "tier", "comprehensive"],
        default="basic",
        help="Test scenario to run",
    )
    parser.add_argument(
        "--users", type=int, default=50, help="Number of concurrent users"
    )
    parser.add_argument(
        "--rps", type=int, default=100, help="Requests per second for basic test"
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Test duration in seconds"
    )
    parser.add_argument(
        "--burst-size", type=int, default=1000, help="Burst size for burst test"
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=100, help="Maximum concurrent requests"
    )
    parser.add_argument(
        "--report", choices=["console", "json"], default="console", help="Report format"
    )
    parser.add_argument("--output", help="Save detailed report to file")

    args = parser.parse_args()

    print("🔧 Rate Limiting Load Tester")
    print("=" * 40)
    print(f"Base URL: {args.url}")
    print(f"Scenario: {args.scenario}")
    print(f"Users: {args.users}")
    print(f"Max Concurrent: {args.max_concurrent}")

    async with RateLimitingLoadTester(args.url, args.max_concurrent) as tester:
        results = []

        if args.scenario == "basic":
            # Basic constant load test
            users = await tester.setup_users(args.users)
            results = await tester.run_constant_load_test(
                requests_per_second=args.rps,
                duration=args.duration,
                users=users,
                endpoint_types=["public", "auth"],
            )

        elif args.scenario == "burst":
            # Burst test
            users = await tester.setup_users(args.users)
            results = await tester.run_burst_test(
                users=users, burst_size=args.burst_size, burst_interval=2.0
            )

        elif args.scenario == "tier":
            # Tier-based test
            users = await tester.setup_users(args.users)
            # For demo, split users into different tiers
            tier_users = {
                "anonymous": [],  # No auth users
                "basic": users[: len(users) // 2],
                "premium": users[len(users) // 2 :],
            }
            results = await tester.run_tier_test(tier_users)

        elif args.scenario == "comprehensive":
            # Comprehensive test with multiple scenarios
            users = await tester.setup_users(args.users)

            print("\n🎯 Running comprehensive test suite...")

            # 1. Basic load test
            print("\n1️⃣ Basic load test...")
            basic_results = await tester.run_constant_load_test(
                requests_per_second=args.rps,
                duration=args.duration // 3,
                users=users,
                endpoint_types=["public"],
            )
            results.extend(basic_results)

            # 2. Authenticated load test
            print("\n2️⃣ Authenticated load test...")
            auth_results = await tester.run_constant_load_test(
                requests_per_second=args.rps // 2,
                duration=args.duration // 3,
                users=users,
                endpoint_types=["protected"],
            )
            results.extend(auth_results)

            # 3. Burst test
            print("\n3️⃣ Burst test...")
            burst_results = await tester.run_burst_test(
                users=users, burst_size=args.burst_size // 2, burst_interval=1.0
            )
            results.extend(burst_results)

        # Calculate and display results
        summary = tester.calculate_summary(results, args.scenario)
        tester.print_summary(summary)

        if args.output:
            tester.save_detailed_report(results, summary, args.output)

        if args.report == "json":
            print(json.dumps(asdict(summary), indent=2))

        # Return exit code based on results
        success = (
            summary.rate_limit_hit_rate > 0
            and summary.error_rate < 10  # Rate limiting should be working
            and summary.average_response_time  # Error rate should be reasonable
            < 2000  # Response time should be acceptable
        )

        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
