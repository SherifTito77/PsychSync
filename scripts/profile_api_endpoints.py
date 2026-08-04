#!/usr/bin/env python3
"""
API Performance Profiling Script

This script profiles API endpoints to identify latency hotspots.
It measures actual response times and identifies slow operations.

Usage:
    python scripts/profile_api_endpoints.py

Requirements:
    - Backend server running on http://localhost:8000
    - httpx library installed
"""

import asyncio
import statistics
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


class Colors:
    """Terminal colors"""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"


class ProfilerMetrics:
    """Track profiling metrics for an endpoint"""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: List[str] = []

    def record_request(self, response_time: float, status_code: int, error: str = None):
        self.response_times.append(response_time)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        if error:
            self.errors.append(error)

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)

    @property
    def p50_response_time(self) -> float:
        if len(self.response_times) < 2:
            return self.avg_response_time
        return statistics.quantiles(self.response_times, n=2)[0]

    @property
    def p95_response_time(self) -> float:
        if len(self.response_times) < 2:
            return self.avg_response_time
        return statistics.quantiles(self.response_times, n=20)[18]

    @property
    def p99_response_time(self) -> float:
        if len(self.response_times) < 2:
            return self.avg_response_time
        return statistics.quantiles(self.response_times, n=100)[98]

    @property
    def success_rate(self) -> float:
        if not self.response_times:
            return 0
        successful = self.status_codes.get(200, 0)
        return (successful / len(self.response_times)) * 100


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.NC}\n")


def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}▸ {text}{Colors.NC}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.NC}")


def color_metric(value: float, thresholds: Tuple[float, float, float]) -> str:
    """Color code a metric based on thresholds"""
    good, warning, critical = thresholds
    if value < good:
        return f"{Colors.GREEN}{value:.0f}ms{Colors.NC}"
    elif value < warning:
        return f"{Colors.YELLOW}{value:.0f}ms{Colors.NC}"
    else:
        return f"{Colors.RED}{value:.0f}ms{Colors.NC}"


async def profile_endpoint(
    client: httpx.AsyncClient,
    endpoint: str,
    method: str = "GET",
    num_requests: int = 10,
    **kwargs,
) -> ProfilerMetrics:
    """Profile a single endpoint"""
    metrics = ProfilerMetrics(endpoint)
    url = f"http://localhost:8000{endpoint}"

    for i in range(num_requests):
        start = time.time()
        try:
            if method.upper() == "GET":
                response = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")

            elapsed = (time.time() - start) * 1000  # Convert to ms
            metrics.record_request(elapsed, response.status_code)

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            metrics.record_request(elapsed, 500, str(e))

        # Small delay between requests
        await asyncio.sleep(0.1)

    return metrics


async def profile_data_export(client: httpx.AsyncClient) -> ProfilerMetrics:
    """Profile data export endpoint - known hotspot"""
    print_section("Data Export Endpoint (Known N+1 Query Issue)")

    # First, create an assessment to export
    try:
        response = await client.post(
            "http://localhost:8000/api/v1/assessments",
            json={"title": "Performance Test Assessment"},
        )
        if response.status_code != 200:
            print(f"{Colors.YELLOW}⚠ Could not create test assessment{Colors.NC}")
            return None

        assessment_id = response.json().get("id")
        print(f"  Created test assessment: {assessment_id}")

    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Skipping data export test: {e}{Colors.NC}")
        return None

    # Profile the export endpoint
    metrics = await profile_endpoint(
        client,
        f"/api/v1/data-export/assessment/{assessment_id}",
        method="POST",
        json={"format": "csv"},
        num_requests=5,  # Fewer requests due to slowness
    )

    return metrics


async def profile_analytics(client: httpx.AsyncClient) -> ProfilerMetrics:
    """Profile analytics endpoint - known hotspot"""
    print_section("Analytics Endpoint (Known Missing Cache Issue)")

    metrics = await profile_endpoint(client, "/api/v1/analytics/stats", num_requests=10)

    return metrics


async def profile_teams_list(client: httpx.AsyncClient) -> ProfilerMetrics:
    """Profile teams list endpoint"""
    print_section("Teams List Endpoint")

    metrics = await profile_endpoint(client, "/api/v1/teams", num_requests=20)

    return metrics


async def profile_health_check(client: httpx.AsyncClient) -> ProfilerMetrics:
    """Profile health check - should be fast"""
    print_section("Health Check Endpoint (Baseline)")

    metrics = await profile_endpoint(client, "/api/v1/health", num_requests=50)

    return metrics


async def profile_user_list(client: httpx.AsyncClient) -> ProfilerMetrics:
    """Profile user list endpoint - potential N+1 issue"""
    print_section("User List Endpoint (Potential N+1 Issue)")

    metrics = await profile_endpoint(client, "/api/v1/users", num_requests=10)

    return metrics


async def run_concurrent_load_test(client: httpx.AsyncClient):
    """Test performance under concurrent load"""
    print_section("Concurrent Load Test (100 Concurrent Requests)")

    endpoint = "/api/v1/health"
    num_concurrent = 100

    async def make_request(client, request_id):
        start = time.time()
        try:
            response = await client.get(f"http://localhost:8000{endpoint}")
            elapsed = (time.time() - start) * 1000
            return response.status_code, elapsed
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return 500, elapsed

    start_time = time.time()

    # Launch all requests concurrently
    tasks = [make_request(client, i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    # Analyze results
    response_times = [rt for _, rt in results]
    status_codes = [sc for sc, _ in results]
    successful = sum(1 for sc in status_codes if sc == 200)

    print(f"  Concurrent requests: {num_concurrent}")
    print(f"  Successful: {successful}/{num_concurrent}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {num_concurrent/total_time:.1f} req/s")
    print(f"  Avg response time: {statistics.mean(response_times):.0f}ms")
    print(f"  Min response time: {min(response_times):.0f}ms")
    print(f"  Max response time: {max(response_times):.0f}ms")

    return {
        "throughput": num_concurrent / total_time,
        "avg_response_time": statistics.mean(response_times),
        "p95_response_time": (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) > 1
            else 0
        ),
    }


def print_metrics_summary(metrics: ProfilerMetrics):
    """Print formatted metrics summary"""
    if not metrics or not metrics.response_times:
        print(f"  {Colors.YELLOW}No data available{Colors.NC}")
        return

    print(f"  Endpoint: {Colors.BOLD}{metrics.endpoint}{Colors.NC}")
    print(f"  Requests: {len(metrics.response_times)}")
    print(f"  Success rate: {metrics.success_rate:.1f}%")
    print(f"  Status codes: {metrics.status_codes}")
    print(f"\n  {Colors.BOLD}Response Times:{Colors.NC}")
    print(f"    Average: {color_metric(metrics.avg_response_time, (100, 300, 500))}")
    print(f"    P50:     {color_metric(metrics.p50_response_time, (100, 300, 500))}")
    print(f"    P95:     {color_metric(metrics.p95_response_time, (200, 500, 1000))}")
    print(f"    P99:     {color_metric(metrics.p99_response_time, (300, 800, 1500))}")

    if metrics.errors:
        print(f"\n  {Colors.RED}Errors:{Colors.NC}")
        for error in metrics.errors[:5]:  # Show first 5 errors
            print(f"    - {error}")

    # Performance assessment
    print(f"\n  {Colors.BOLD}Assessment:{Colors.NC}")
    if metrics.p95_response_time < 200:
        print(f"    {Colors.GREEN}✓ Excellent performance{Colors.NC}")
    elif metrics.p95_response_time < 500:
        print(f"    {Colors.YELLOW}⚠ Acceptable performance{Colors.NC}")
    else:
        print(f"    {Colors.RED}✗ Poor performance - needs optimization{Colors.NC}")


async def main():
    """Run comprehensive profiling"""
    print_header("API Performance Profiling Tool")
    print(
        f"{Colors.CYAN}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}"
    )

    # Check if server is running
    print(f"\n{Colors.BOLD}Checking backend server...{Colors.NC}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/api/v1/health")
        print(f"{Colors.GREEN}✓ Server is running{Colors.NC}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Cannot connect to server: {e}{Colors.NC}")
        print(f"\n{Colors.YELLOW}Please start the server first:{Colors.NC}")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return

    # Run profiling
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Baseline: Health check
        health_metrics = await profile_health_check(client)
        print_metrics_summary(health_metrics)

        # Test known hotspots
        analytics_metrics = await profile_analytics(client)
        print_metrics_summary(analytics_metrics)

        teams_metrics = await profile_teams_list(client)
        print_metrics_summary(teams_metrics)

        # Optional: Slower endpoints
        print(
            f"\n{Colors.YELLOW}Profile slower endpoints? (may take 1-2 minutes) [y/N]: {Colors.NC}",
            end="",
        )
        # Auto-skip for non-interactive, but you can uncomment to prompt:
        # choice = input().strip().lower()
        choice = "n"  # Default to no

        if choice == "y":
            export_metrics = await profile_data_export(client)
            if export_metrics:
                print_metrics_summary(export_metrics)

            user_metrics = await profile_user_list(client)
            print_metrics_summary(user_metrics)

        # Concurrent load test
        load_metrics = await run_concurrent_load_test(client)

    # Print summary
    print_header("Profiling Summary")

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Key Findings:{Colors.NC}\n")

    # Compare against baseline
    if health_metrics and analytics_metrics:
        overhead = (
            analytics_metrics.avg_response_time - health_metrics.avg_response_time
        )
        print(f"  Analytics overhead vs baseline: {overhead:.0f}ms")
        if overhead > 500:
            print(
                f"    {Colors.RED}✗ Significant overhead - likely needs caching{Colors.NC}"
            )
        else:
            print(f"    {Colors.GREEN}✓ Acceptable overhead{Colors.NC}")

    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Recommendations:{Colors.NC}\n")

    if analytics_metrics and analytics_metrics.p95_response_time > 500:
        print(
            f"  {Colors.YELLOW}1. Analytics endpoint is slow - implement caching{Colors.NC}"
        )
        print(f"     See: PERFORMANCE_ANALYSIS.md - Hotspot #3")

    if health_metrics and health_metrics.p95_response_time > 100:
        print(
            f"  {Colors.YELLOW}2. Baseline health check is slow - check database/query{Colors.NC}"
        )

    print(
        f"\n  {Colors.GREEN}3. Run database query analysis to find N+1 problems{Colors.NC}"
    )
    print(f"     See: PERFORMANCE_ANALYSIS.md - Hotspot #2")

    print(f"\n  {Colors.GREEN}4. Check for missing database indexes{Colors.NC}")
    print(f"     See: PERFORMANCE_ANALYSIS.md - Hotspot #5")

    print(
        f"\n{Colors.CYAN}See PERFORMANCE_ANALYSIS.md for detailed optimization proposals{Colors.NC}\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
