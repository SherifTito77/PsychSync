#!/usr/bin/env python3
"""
API Downtime Handling Testing Module
Tests frontend graceful handling of API service failures and outages
"""

import asyncio
import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import pytest as pytest


class APIStatus(Enum):
    """API server status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    RECOVERING = "recovering"


@dataclass
class APIResponse:
    """Simulated API response"""

    status_code: int
    response_time: float
    data: Dict[str, Any]
    error: Optional[str] = None
    retry_after: Optional[int] = None


@dataclass
class DowntimeTestResult:
    """Result of API downtime testing"""

    test_name: str
    success: bool
    response_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MockAPIServer:
    """Mock API server with configurable failure modes"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.status = APIStatus.HEALTHY
        self.failure_rate = 0.0
        self.response_time_range = (0.1, 0.5)
        self.error_modes = []
        self.endpoints = {
            "/api/v1/health": "OK",
            "/api/v1/users/profile": {"user": "test_user", "role": "admin"},
            "/api/v1/assessments": [
                {"id": 1, "type": "MBTI"},
                {"id": 2, "type": "Big Five"},
            ],
            "/api/v1/analytics": {
                "users": 150,
                "assessments": 500,
                "completion_rate": 87.3,
            },
            "/api/v1/teams": [
                {"id": 1, "name": "Team Alpha"},
                {"id": 2, "name": "Team Beta"},
            ],
        }
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_failures = 0
        self.circuit_breaker_open = False

    async def handle_request(self, endpoint: str, method: str = "GET") -> APIResponse:
        """Handle API request with simulated failures"""
        start_time = time.time()

        # Check circuit breaker
        if self.circuit_breaker_open:
            await asyncio.sleep(random.uniform(0.05, 0.1))
            return APIResponse(
                status_code=503,
                response_time=time.time() - start_time,
                data={},
                error="Service Unavailable - Circuit Breaker Open",
                retry_after=30,
            )

        # Simulate response time
        processing_time = random.uniform(*self.response_time_range)
        await asyncio.sleep(processing_time)

        # Check for failure based on status and failure rate
        if self.status == APIStatus.OFFLINE:
            self._increment_circuit_breaker()
            return APIResponse(
                status_code=503,
                response_time=processing_time,
                data={},
                error="Service Unavailable",
            )

        elif self.status == APIStatus.DEGRADED:
            if random.random() < 0.7:  # 70% failure rate in degraded mode
                self._increment_circuit_breaker()
                error_mode = (
                    random.choice(self.error_modes) if self.error_modes else "timeout"
                )

                if error_mode == "timeout":
                    await asyncio.sleep(5.0)  # Long timeout
                    return APIResponse(
                        status_code=408,
                        response_time=5.0 + processing_time,
                        data={},
                        error="Request Timeout",
                    )
                elif error_mode == "server_error":
                    return APIResponse(
                        status_code=500,
                        response_time=processing_time,
                        data={},
                        error="Internal Server Error",
                    )
                elif error_mode == "rate_limit":
                    return APIResponse(
                        status_code=429,
                        response_time=processing_time,
                        data={},
                        error="Rate Limit Exceeded",
                        retry_after=60,
                    )
                else:
                    return APIResponse(
                        status_code=502,
                        response_time=processing_time,
                        data={},
                        error="Bad Gateway",
                    )

        # Random failure based on failure_rate
        if random.random() < self.failure_rate:
            self._increment_circuit_breaker()
            return APIResponse(
                status_code=random.choice([500, 502, 503, 504]),
                response_time=processing_time,
                data={},
                error="Random Service Failure",
            )

        # Success case
        if endpoint in self.endpoints:
            return APIResponse(
                status_code=200,
                response_time=processing_time,
                data=self.endpoints[endpoint],
            )
        else:
            return APIResponse(
                status_code=404,
                response_time=processing_time,
                data={},
                error="Endpoint Not Found",
            )

    def _increment_circuit_breaker(self):
        """Increment circuit breaker failure count"""
        self.circuit_breaker_failures += 1
        if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True
            # Schedule circuit breaker reset after 30 seconds
            asyncio.create_task(self._reset_circuit_breaker())

    async def _reset_circuit_breaker(self):
        """Reset circuit breaker after timeout"""
        await asyncio.sleep(30)
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0

    def set_status(self, status: APIStatus):
        """Set API server status"""
        self.status = status

    def set_failure_rate(self, rate: float):
        """Set random failure rate (0.0 to 1.0)"""
        self.failure_rate = max(0.0, min(1.0, rate))

    def set_error_modes(self, modes: List[str]):
        """Set specific error modes"""
        self.error_modes = modes


class FrontendClient:
    """Simulated frontend client with graceful error handling"""

    def __init__(self, api_server: MockAPIServer):
        self.api_server = api_server
        self.cache = {}
        self.retry_attempts = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff
        self.offline_mode = False
        self.cached_data_timestamps = {}

    async def make_request(
        self, endpoint: str, method: str = "GET", use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make API request with graceful error handling"""

        # Check cache first
        if use_cache and endpoint in self.cache:
            cache_time = self.cached_data_timestamps.get(endpoint, datetime.now())
            # Use cached data if less than 5 minutes old
            if datetime.now() - cache_time < timedelta(minutes=5):
                return {
                    "success": True,
                    "data": self.cache[endpoint],
                    "source": "cache",
                    "status_code": 200,
                }

        # Attempt API request with retries
        last_response = None

        for attempt in range(self.retry_attempts):
            try:
                response = await self.api_server.handle_request(endpoint, method)
                last_response = response

                if response.status_code == 200:
                    # Success - update cache
                    self.cache[endpoint] = response.data
                    self.cached_data_timestamps[endpoint] = datetime.now()
                    self.offline_mode = False

                    return {
                        "success": True,
                        "data": response.data,
                        "source": "api",
                        "status_code": response.status_code,
                        "response_time": response.response_time,
                    }

                elif response.status_code in [429, 502, 503, 504]:
                    # Retry these errors
                    if attempt < self.retry_attempts - 1:
                        delay = self.retry_delays[
                            min(attempt, len(self.retry_delays) - 1)
                        ]
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Final attempt failed, try fallback
                        return await self._handle_fallback(endpoint, response)

                elif response.status_code == 408:
                    # Timeout - try fallback immediately
                    return await self._handle_fallback(endpoint, response)

                else:
                    # Client error or unrecoverable error
                    return {
                        "success": False,
                        "error": response.error or f"HTTP {response.status_code}",
                        "status_code": response.status_code,
                        "retry_attempts": attempt + 1,
                    }

            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    await asyncio.sleep(delay)
                    continue
                else:
                    # All attempts failed
                    return await self._handle_fallback(endpoint, None)

    async def _handle_fallback(
        self, endpoint: str, last_response: Optional[APIResponse]
    ) -> Dict[str, Any]:
        """Handle fallback when API is unavailable"""

        # Check if we have cached data
        if endpoint in self.cache:
            return {
                "success": True,
                "data": self.cache[endpoint],
                "source": "cache_fallback",
                "status_code": 200,
                "warning": "Using cached data due to API unavailability",
            }

        # Provide default/fallback data
        fallback_data = self._get_fallback_data(endpoint)
        self.offline_mode = True

        return {
            "success": True,
            "data": fallback_data,
            "source": "fallback",
            "status_code": 200,
            "warning": "Using fallback data due to API unavailability",
            "last_error": last_response.error if last_response else "Network Error",
        }

    def _get_fallback_data(self, endpoint: str) -> Dict[str, Any]:
        """Get fallback data for specific endpoints"""
        fallback_responses = {
            "/api/v1/users/profile": {
                "user": "offline_user",
                "role": "user",
                "last_sync": None,
                "offline_mode": True,
            },
            "/api/v1/assessments": [],
            "/api/v1/analytics": {
                "users": 0,
                "assessments": 0,
                "completion_rate": 0,
                "last_sync": None,
                "offline_mode": True,
            },
            "/api/v1/teams": [],
            "/api/v1/health": {
                "status": "offline",
                "timestamp": datetime.now().isoformat(),
            },
        }
        return fallback_responses.get(endpoint, {})

    def clear_cache(self):
        """Clear client cache"""
        self.cache.clear()
        self.cached_data_timestamps.clear()


class APIDowntimeTester:
    """Comprehensive API downtime testing"""

    def __init__(self):
        self.api_server = MockAPIServer()
        self.client = FrontendClient(self.api_server)
        self.test_results: List[DowntimeTestResult] = []

    async def test_healthy_api_response(self) -> DowntimeTestResult:
        """Test normal API response when healthy"""
        print("Testing healthy API response...")

        self.api_server.set_status(APIStatus.HEALTHY)
        self.api_server.set_failure_rate(0.0)
        self.client.clear_cache()

        endpoints = list(self.api_server.endpoints.keys())
        results = []

        start_time = time.time()

        for endpoint in endpoints:
            response = await self.client.make_request(endpoint)
            results.append(
                {
                    "endpoint": endpoint,
                    "success": response["success"],
                    "source": response.get("source", "api"),
                    "status_code": response.get("status_code", 0),
                }
            )

        end_time = time.time()

        successful_requests = sum(1 for r in results if r["success"])
        api_requests = sum(1 for r in results if r.get("source") == "api")

        return DowntimeTestResult(
            test_name="Healthy API Response",
            success=successful_requests == len(endpoints)
            and api_requests == len(endpoints),
            response_time=end_time - start_time,
            details={
                "total_endpoints": len(endpoints),
                "successful_requests": successful_requests,
                "api_requests": api_requests,
                "results": results,
            },
        )

    async def test_intermittent_failures(self) -> DowntimeTestResult:
        """Test handling of intermittent API failures"""
        print("Testing intermittent API failures...")

        self.api_server.set_status(APIStatus.DEGRADED)
        self.api_server.set_failure_rate(0.3)  # 30% random failures
        self.api_server.set_error_modes(["timeout", "server_error", "rate_limit"])
        self.client.clear_cache()

        endpoints = [
            "/api/v1/users/profile",
            "/api/v1/analytics",
            "/api/v1/assessments",
        ]
        results = []

        start_time = time.time()

        for endpoint in endpoints:
            response = await self.client.make_request(endpoint)
            results.append(
                {
                    "endpoint": endpoint,
                    "success": response["success"],
                    "source": response.get("source", "api"),
                    "status_code": response.get("status_code", 0),
                    "warning": response.get("warning"),
                }
            )

        end_time = time.time()

        successful_requests = sum(1 for r in results if r["success"])
        graceful_degradations = sum(
            1 for r in results if r["source"] in ["cache_fallback", "fallback"]
        )

        return DowntimeTestResult(
            test_name="Intermittent Failures",
            success=successful_requests == len(endpoints),
            response_time=end_time - start_time,
            details={
                "total_endpoints": len(endpoints),
                "successful_requests": successful_requests,
                "graceful_degradations": graceful_degradations,
                "success_rate": (successful_requests / len(endpoints)) * 100,
                "results": results,
            },
        )

    async def test_complete_api_outage(self) -> DowntimeTestResult:
        """Test complete API server outage"""
        print("Testing complete API outage...")

        self.api_server.set_status(APIStatus.OFFLINE)
        self.client.clear_cache()

        # First, populate cache with some data
        self.api_server.set_status(APIStatus.HEALTHY)
        await self.client.make_request("/api/v1/users/profile")
        await self.client.make_request("/api/v1/analytics")

        # Now simulate outage
        self.api_server.set_status(APIStatus.OFFLINE)

        endpoints = [
            "/api/v1/users/profile",
            "/api/v1/analytics",
            "/api/v1/teams",
            "/api/v1/health",
        ]
        results = []

        start_time = time.time()

        for endpoint in endpoints:
            response = await self.client.make_request(endpoint)
            results.append(
                {
                    "endpoint": endpoint,
                    "success": response["success"],
                    "source": response.get("source", "api"),
                    "status_code": response.get("status_code", 0),
                    "warning": response.get("warning"),
                    "last_error": response.get("last_error"),
                }
            )

        end_time = time.time()

        successful_requests = sum(1 for r in results if r["success"])
        cache_usage = sum(1 for r in results if r.get("source") == "cache_fallback")
        fallback_usage = sum(1 for r in results if r.get("source") == "fallback")

        return DowntimeTestResult(
            test_name="Complete API Outage",
            success=successful_requests == len(endpoints),
            response_time=end_time - start_time,
            details={
                "total_endpoints": len(endpoints),
                "successful_requests": successful_requests,
                "cache_usage": cache_usage,
                "fallback_usage": fallback_usage,
                "offline_mode_active": self.client.offline_mode,
                "results": results,
            },
        )

    async def test_circuit_breaker_behavior(self) -> DowntimeTestResult:
        """Test circuit breaker functionality"""
        print("Testing circuit breaker behavior...")

        self.api_server.set_status(APIStatus.DEGRADED)
        self.api_server.set_failure_rate(1.0)  # 100% failure rate
        self.client.clear_cache()

        endpoint = "/api/v1/users/profile"
        results = []

        start_time = time.time()

        # Make multiple requests to trigger circuit breaker
        for i in range(10):
            response = await self.client.make_request(endpoint)
            results.append(
                {
                    "attempt": i + 1,
                    "success": response["success"],
                    "source": response.get("source", "api"),
                    "status_code": response.get("status_code", 0),
                    "circuit_breaker_open": self.api_server.circuit_breaker_open,
                }
            )

            if self.api_server.circuit_breaker_open:
                break

        end_time = time.time()

        circuit_breaker_triggered = self.api_server.circuit_breaker_open
        successful_requests = sum(1 for r in results if r["success"])

        return DowntimeTestResult(
            test_name="Circuit Breaker Behavior",
            success=circuit_breaker_triggered
            and successful_requests >= len(results) - 5,
            response_time=end_time - start_time,
            details={
                "total_attempts": len(results),
                "successful_requests": successful_requests,
                "circuit_breaker_triggered": circuit_breaker_triggered,
                "circuit_breaker_threshold": self.api_server.circuit_breaker_threshold,
                "results": results,
            },
        )

    async def test_cache_effectiveness(self) -> DowntimeTestResult:
        """Test cache effectiveness during API degradation"""
        print("Testing cache effectiveness...")

        # Warm up cache
        self.api_server.set_status(APIStatus.HEALTHY)
        endpoints = ["/api/v1/users/profile", "/api/v1/analytics"]

        for endpoint in endpoints:
            await self.client.make_request(endpoint)

        # Simulate API degradation
        self.api_server.set_status(APIStatus.DEGRADED)
        self.api_server.set_failure_rate(0.8)

        results = []

        start_time = time.time()

        # Make requests that should use cache
        for i in range(5):
            for endpoint in endpoints:
                response = await self.client.make_request(endpoint)
                results.append(
                    {
                        "endpoint": endpoint,
                        "request_number": i + 1,
                        "success": response["success"],
                        "source": response.get("source", "api"),
                        "response_time": response.get("response_time", 0),
                    }
                )

        end_time = time.time()

        cache_hits = sum(
            1 for r in results if r["source"] in ["cache", "cache_fallback"]
        )
        total_requests = len(results)
        cache_hit_rate = (cache_hits / total_requests) * 100

        return DowntimeTestResult(
            test_name="Cache Effectiveness",
            success=cache_hit_rate >= 70,  # At least 70% cache hits
            response_time=end_time - start_time,
            details={
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "average_response_time": sum(r["response_time"] for r in results)
                / total_requests,
                "results": results[:10],  # Show first 10 results
            },
        )

    async def test_recovery_after_outage(self) -> DowntimeTestResult:
        """Test system recovery after API comes back online"""
        print("Testing recovery after outage...")

        # Start with healthy API
        self.api_server.set_status(APIStatus.HEALTHY)
        self.client.clear_cache()

        # Populate cache
        await self.client.make_request("/api/v1/users/profile")

        # Simulate outage
        self.api_server.set_status(APIStatus.OFFLINE)

        # Make requests during outage (should use fallback)
        outage_response = await self.client.make_request("/api/v1/users/profile")

        # Restore API
        self.api_server.set_status(APIStatus.HEALTHY)

        # Make requests after recovery
        recovery_responses = []
        for i in range(3):
            response = await self.client.make_request("/api/v1/users/profile")
            recovery_responses.append(response)
            await asyncio.sleep(0.1)

        start_time = time.time()
        end_time = time.time()

        successful_recoveries = sum(
            1 for r in recovery_responses if r.get("source") == "api"
        )
        offline_mode_recovered = not self.client.offline_mode

        return DowntimeTestResult(
            test_name="Recovery After Outage",
            success=successful_recoveries > 0 and offline_mode_recovered,
            response_time=end_time - start_time,
            details={
                "outage_handled": outage_response.get("success", False),
                "outage_source": outage_response.get("source"),
                "recovery_responses": len(recovery_responses),
                "successful_recoveries": successful_recoveries,
                "offline_mode_recovered": offline_mode_recovered,
                "recovery_responses_detail": recovery_responses,
            },
        )

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API downtime handling tests"""
        print("Starting comprehensive API downtime handling testing...")

        test_functions = [
            self.test_healthy_api_response,
            self.test_intermittent_failures,
            self.test_complete_api_outage,
            self.test_circuit_breaker_behavior,
            self.test_cache_effectiveness,
            self.test_recovery_after_outage,
        ]

        for test_func in test_functions:
            try:
                result = await test_func()
                self.test_results.append(result)

                status = "✅" if result.success else "❌"
                print(f"{status} {result.test_name}: {result.response_time:.3f}s")

                if result.error_message:
                    print(f"   Error: {result.error_message}")

            except Exception as e:
                error_result = DowntimeTestResult(
                    test_name=test_func.__name__,
                    success=False,
                    response_time=0,
                    details={},
                    error_message=str(e),
                )
                self.test_results.append(error_result)
                print(f"❌ {test_func.__name__} - {str(e)}")

        # Generate summary
        successful_tests = sum(1 for r in self.test_results if r.success)
        total_tests = len(self.test_results)

        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (
                    (successful_tests / total_tests) * 100 if total_tests > 0 else 0
                ),
            },
            "test_results": [
                {
                    "name": r.test_name,
                    "success": r.success,
                    "response_time": r.response_time,
                    "details": r.details,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.test_results
            ],
            "client_capabilities": {
                "retry_attempts": self.client.retry_attempts,
                "retry_delays": self.client.retry_delays,
                "cache_enabled": True,
                "circuit_breaker_threshold": self.api_server.circuit_breaker_threshold,
                "fallback_data_available": True,
            },
        }


# Main execution for standalone testing
async def main():
    """Run API downtime handling tests"""
    tester = APIDowntimeTester()
    results = await tester.run_all_tests()

    print("\n" + "=" * 60)
    print("API DOWNTIME HANDLING TEST RESULTS")
    print("=" * 60)

    summary = results["summary"]
    print(f"Tests Run: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")

    print("\nDetailed Results:")
    for result in results["test_results"]:
        status = "PASS" if result["success"] else "FAIL"
        print(f"  {status} {result['name']}: {result['response_time']:.3f}s")
        if result["error_message"]:
            print(f"       Error: {result['error_message']}")

    print(f"\nClient Capabilities:")
    capabilities = results["client_capabilities"]
    print(f"  Retry Attempts: {capabilities['retry_attempts']}")
    print(f"  Retry Delays: {capabilities['retry_delays']}")
    print(f"  Cache Enabled: {capabilities['cache_enabled']}")
    print(f"  Circuit Breaker Threshold: {capabilities['circuit_breaker_threshold']}")
    print(f"  Fallback Data Available: {capabilities['fallback_data_available']}")

    # Save results to file
    with open("api_downtime_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: api_downtime_test_results.json")

    return results


if __name__ == "__main__":
    asyncio.run(main())
