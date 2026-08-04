#!/usr/bin/env python3
"""
Quick Rate Limit Validation Test

This standalone script quickly validates that rate limiting is working
without requiring full test infrastructure.

Usage:
    python tests/load/quick_rate_limit_test.py

Requirements:
    - Backend server running on http://localhost:8000
    - No additional test endpoints needed (uses public endpoints)
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import List, Tuple

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


class Colors:
    """Terminal colors for output"""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.NC}")
    print(f"{Colors.BLUE}{text:^70}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.NC} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.NC} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {text}")


async def test_rate_limit_health_endpoint():
    """
    Test rate limiting on the public health endpoint.
    Anonymous users: 50 requests/minute (with lenient multiplier)
    """
    print_header("TEST 1: Health Endpoint Rate Limiting")

    url = "http://localhost:8000/api/v1/health"
    num_requests = 60  # Slightly over typical limit

    print(f"Sending {num_requests} requests to {url}")
    print(f"Expected: ~50 successful, ~10 throttled (429)\n")

    successful = 0
    throttled = 0
    errors = 0
    response_times = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(num_requests):
            start = time.time()
            try:
                response = await client.get(url)
                elapsed = time.time() - start
                response_times.append(elapsed)

                if response.status_code == 200:
                    successful += 1
                elif response.status_code == 429:
                    throttled += 1
                else:
                    print_warning(f"Unexpected status code: {response.status_code}")

                # Print progress every 10 requests
                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i+1}/{num_requests} requests sent...")

            except Exception as e:
                errors += 1
                print_error(f"Request failed: {e}")

            # Small delay to be realistic
            await asyncio.sleep(0.02)

    # Print results
    print(f"\n{Colors.BLUE}Results:{Colors.NC}")
    print(f"  Successful (200): {successful}")
    print(f"  Throttled (429):  {throttled}")
    print(f"  Errors:           {errors}")
    print(f"  Total:            {num_requests}")

    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"\n{Colors.BLUE}Response Times:{Colors.NC}")
        print(f"  Average: {avg_time*1000:.1f}ms")
        print(f"  Min:     {min(response_times)*1000:.1f}ms")
        print(f"  Max:     {max(response_times)*1000:.1f}ms")

    # Validate rate limiting is working
    print(f"\n{Colors.BLUE}Validation:{Colors.NC}")

    if throttled > 0:
        print_success("Rate limiting is WORKING - requests were throttled")
        return True
    else:
        print_warning(
            "No requests were throttled - rate limit may be too lenient or not enforced"
        )
        return False


async def test_concurrent_burst():
    """
    Test rate limiting under concurrent burst load.
    """
    print_header("TEST 2: Concurrent Burst Test")

    url = "http://localhost:8000/api/v1/health"
    concurrent_requests = 100

    print(f"Sending {concurrent_requests} concurrent requests to {url}")
    print(f"Expected: Significant throttling under burst load\n")

    async def make_request(client, request_id):
        start = time.time()
        try:
            response = await client.get(url)
            elapsed = time.time() - start
            return response.status_code, elapsed
        except Exception as e:
            return 500, time.time() - start

    async with httpx.AsyncClient(
        timeout=10.0, limits=httpx.Limits(max_connections=200)
    ) as client:
        start_time = time.time()

        # Launch all requests concurrently
        tasks = [make_request(client, i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

    # Analyze results
    successful = sum(1 for status, _ in results if status == 200)
    throttled = sum(1 for status, _ in results if status == 429)
    errors = sum(1 for status, _ in results if status not in [200, 429])

    response_times = [rt for _, rt in results]
    avg_response_time = (
        sum(response_times) / len(response_times) if response_times else 0
    )

    print(f"{Colors.BLUE}Results:{Colors.NC}")
    print(f"  Successful (200): {successful}")
    print(f"  Throttled (429):  {throttled}")
    print(f"  Errors:           {errors}")
    print(f"  Total:            {concurrent_requests}")
    print(f"\n{Colors.BLUE}Performance:{Colors.NC}")
    print(f"  Total time:       {elapsed:.2f}s")
    print(f"  Avg response:     {avg_response_time*1000:.1f}ms")
    print(f"  Throughput:       {concurrent_requests/elapsed:.1f} req/s")

    print(f"\n{Colors.BLUE}Validation:{Colors.NC}")

    if throttled > 0:
        print_success(f"Burst rate limiting working - {throttled} requests throttled")
        return True
    else:
        print_warning("No throttling under burst - may indicate rate limit issues")
        return False


async def test_rate_limit_headers():
    """
    Test that rate limit headers are present and accurate.
    """
    print_header("TEST 3: Rate Limit Headers Validation")

    url = "http://localhost:8000/api/v1/health"

    print(f"Checking rate limit headers from {url}\n")

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)

    headers_to_check = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-RateLimit-Reset-After",  # Optional
    ]

    print(f"{Colors.BLUE}Headers Found:{Colors.NC}")
    headers_present = 0
    for header in headers_to_check:
        value = response.headers.get(header)
        if value:
            print(f"  {Colors.GREEN}✓{Colors.NC} {header}: {value}")
            headers_present += 1
        else:
            print(f"  {Colors.YELLOW}○{Colors.NC} {header}: (not present)")

    print(f"\n{Colors.BLUE}All Response Headers:{Colors.NC}")
    for key, value in response.headers.items():
        if "rate" in key.lower() or "limit" in key.lower():
            print(f"  {key}: {value}")

    print(f"\n{Colors.BLUE}Validation:{Colors.NC}")

    if headers_present >= 2:  # At least limit and remaining
        print_success(
            f"Rate limit headers present ({headers_present}/{len(headers_to_check)})"
        )
        return True
    else:
        print_warning("Insufficient rate limit headers")
        return False


async def test_sliding_window_reset():
    """
    Test that rate limit window resets properly.
    """
    print_header("TEST 4: Sliding Window Reset Test")

    url = "http://localhost:8000/api/v1/health"

    print("Phase 1: Exhaust rate limit")
    print(f"Sending requests until throttled...\n")

    exhausted = False
    requests_sent = 0

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Send requests until we get throttled
        for i in range(100):
            response = await client.get(url)
            requests_sent += 1

            if response.status_code == 429:
                exhausted = True
                print_success(f"Rate limit exhausted after {requests_sent} requests")
                break

            if (i + 1) % 10 == 0:
                print(f"  Sent {i+1} requests...")

            await asyncio.sleep(0.01)

    if not exhausted:
        print_warning("Rate limit not exhausted (may be too lenient)")
        return False

    # Wait for window to reset
    wait_time = 65  # Slightly more than typical 60s window
    print(f"\nWaiting {wait_time}s for rate limit window to reset...")
    print("(This tests the sliding window behavior)\n")

    for i in range(wait_time):
        print(f"  {i+1}/{wait_time}s", end="\r")
        await asyncio.sleep(1)

    print("\n\nPhase 2: Verify window reset")
    print("Sending requests after window should have reset...\n")

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)

    print(f"{Colors.BLUE}Result:{Colors.NC}")
    print(f"  Status code: {response.status_code}")

    print(f"\n{Colors.BLUE}Validation:{Colors.NC}")

    if response.status_code == 200:
        print_success("Rate limit window reset properly - request accepted")
        return True
    elif response.status_code == 429:
        print_warning(
            "Still being throttled - window may not have reset or limit is stricter"
        )
        return False
    else:
        print_warning(f"Unexpected status code: {response.status_code}")
        return False


async def main():
    """Run all quick tests"""
    print(
        f"\n{Colors.BLUE}╔═══════════════════════════════════════════════════════════════╗{Colors.NC}"
    )
    print(
        f"{Colors.BLUE}║         Rate Limiting Quick Validation Test                  ║{Colors.NC}"
    )
    print(
        f"{Colors.BLUE}╚═══════════════════════════════════════════════════════════════╝{Colors.NC}"
    )
    print(
        f"\n{Colors.BLUE}Started at:{Colors.NC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Check if server is running
    print(f"\n{Colors.BLUE}Checking if backend server is running...{Colors.NC}")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:8000/api/v1/health")
        print_success(f"Server is running (status: {response.status_code})")
    except Exception as e:
        print_error(f"Cannot connect to backend server: {e}")
        print(f"\n{Colors.YELLOW}Please start the backend server:{Colors.NC}")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return

    results = []

    # Run tests
    try:
        results.append(await test_rate_limit_health_endpoint())
        results.append(await test_concurrent_burst())
        results.append(await test_rate_limit_headers())

        # Sliding window test takes longer, make it optional
        print(
            f"\n{Colors.YELLOW}Run sliding window test? (takes ~65 seconds){Colors.NC}"
        )
        print("  Press Ctrl+C to skip...")
        try:
            results.append(await test_sliding_window_reset())
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Skipped sliding window test{Colors.NC}")

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.NC}")
        return

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(results)
    total = len(results)

    print(f"{Colors.BLUE}Tests Passed:{Colors.NC} {passed}/{total}")

    if passed == total:
        print(f"\n{Colors.GREEN}{'═' * 70}{Colors.NC}")
        print(
            f"{Colors.GREEN}{'✓ ALL TESTS PASSED - Rate limiting is working correctly!':^70}{Colors.NC}"
        )
        print(f"{Colors.GREEN}{'═' * 70}{Colors.NC}")
    else:
        print(f"\n{Colors.YELLOW}{'═' * 70}{Colors.NC}")
        print(
            f"{Colors.YELLOW}{'⚠ SOME TESTS HAD ISSUES - Review results above':^70}{Colors.NC}"
        )
        print(f"{Colors.YELLOW}{'═' * 70}{Colors.NC}")

    print(
        f"\n{Colors.BLUE}Completed at:{Colors.NC} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
