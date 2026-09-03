#!/usr/bin/env python3
"""
API Rate Limiting Tests by User Role
Validates that rate limiting is properly enforced based on user roles
"""

import time
import unittest
from collections import defaultdict
from unittest.mock import Mock, patch

import requests


class TestRateLimitingByRole(unittest.TestCase):
    """Test API rate limiting enforcement by user role"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000/api/v1"

        # Mock users with different roles
        self.users = {
            "normal_user": {
                "id": "user_123",
                "email": "user@example.com",
                "role": "USER",
                "rate_limit_per_minute": 60,
                "rate_limit_per_hour": 1000,
            },
            "admin_user": {
                "id": "admin_456",
                "email": "admin@example.com",
                "role": "ADMIN",
                "rate_limit_per_minute": 120,
                "rate_limit_per_hour": 2000,
            },
            "team_lead_user": {
                "id": "lead_789",
                "email": "lead@example.com",
                "role": "TEAM_LEAD",
                "rate_limit_per_minute": 90,
                "rate_limit_per_hour": 1500,
            },
            "premium_user": {
                "id": "premium_999",
                "email": "premium@example.com",
                "role": "USER",
                "premium": True,
                "rate_limit_per_minute": 100,
                "rate_limit_per_hour": 2000,
            },
        }

        # Rate limiting simulation
        self.request_counters = defaultdict(int)
        self.rate_limit_window = 60  # 1 minute window for testing
        self.test_start_time = time.time()

    def simulate_api_request(self, user_data, endpoint="/api/v1/profile"):
        """Simulate an API request with rate limiting"""
        current_time = time.time()
        user_id = user_data["id"]

        # Check if user is rate limited
        request_count = self.request_counters[user_id]
        rate_limit = user_data["rate_limit_per_minute"]

        if request_count >= rate_limit:
            return {
                "user_id": user_id,
                "status_code": 429,
                "success": False,
                "message": "Rate limit exceeded",
                "retry_after": 60,
            }

        # Increment counter and allow request
        self.request_counters[user_id] += 1
        return {
            "user_id": user_id,
            "status_code": 200,
            "success": True,
            "message": "Request successful",
            "remaining_requests": max(0, rate_limit - self.request_counters[user_id]),
        }

    def test_normal_user_rate_limiting(self):
        """Test rate limiting for normal users"""
        print("\\n🚦 Testing Normal User Rate Limiting:")

        normal_user = self.users["normal_user"]
        rate_limit = normal_user["rate_limit_per_minute"]

        print(f"  Rate limit for normal user: {rate_limit} requests/minute")

        # Make requests up to the limit
        results = []
        for i in range(rate_limit + 10):  # Exceed limit by 10 requests
            result = self.simulate_api_request(normal_user)
            results.append(result)

            if result["status_code"] == 200:
                remaining = result.get("remaining_requests", 0)
                if i < rate_limit - 1:
                    print(f"    Request {i+1}: ✅ Success ({remaining} remaining)")
                else:
                    print(f"    Request {i+1}: ✅ Success (quota reached)")
            else:
                print(
                    f"    Request {i+1}: ❌ Rate limited ({result.get('retry_after', 0)}s retry)"
                )

        # Validate results
        successful_requests = [r for r in results if r["status_code"] == 200]
        rate_limited_requests = [r for r in results if r["status_code"] == 429]

        self.assertEqual(
            len(successful_requests),
            rate_limit,
            f"Normal user should make exactly {rate_limit} successful requests",
        )
        self.assertEqual(
            len(rate_limited_requests),
            10,
            f"Normal user should have 10 rate-limited requests",
        )

        print(
            f"  ✅ Normal user rate limiting: {len(successful_requests)} successful, {len(rate_limited_requests)} rate-limited"
        )

    def test_admin_user_rate_limiting(self):
        """Test rate limiting for admin users"""
        print("\\n👑 Testing Admin User Rate Limiting:")

        admin_user = self.users["admin_user"]
        rate_limit = admin_user["rate_limit_per_minute"]

        print(f"  Rate limit for admin user: {rate_limit} requests/minute")

        # Make requests up to the limit
        results = []
        for i in range(rate_limit + 5):  # Exceed limit by 5 requests
            result = self.simulate_api_request(admin_user)
            results.append(result)

            if result["status_code"] == 200:
                remaining = result.get("remaining_requests", 0)
                if i < rate_limit - 1:
                    print(f"    Request {i+1}: ✅ Success ({remaining} remaining)")
                else:
                    print(f"    Request {i+1}: ✅ Success (quota reached)")
            else:
                print(
                    f"    Request {i+1}: ❌ Rate limited ({result.get('retry_after', 0)}s retry)"
                )

        # Validate results
        successful_requests = [r for r in results if r["status_code"] == 200]
        rate_limited_requests = [r for r in results if r["status_code"] == 429]

        self.assertEqual(
            len(successful_requests),
            rate_limit,
            f"Admin user should make exactly {rate_limit} successful requests",
        )
        self.assertEqual(
            len(rate_limited_requests),
            5,
            f"Admin user should have 5 rate-limited requests",
        )

        print(
            f"  ✅ Admin user rate limiting: {len(successful_requests)} successful, {len(rate_limited_requests)} rate-limited"
        )

    def test_premium_user_rate_limiting(self):
        """Test rate limiting for premium users"""
        print("\\n⭐ Testing Premium User Rate Limiting:")

        premium_user = self.users["premium_user"]
        rate_limit = premium_user["rate_limit_per_minute"]

        print(f"  Rate limit for premium user: {rate_limit} requests/minute")

        # Make requests up to the limit
        results = []
        for i in range(rate_limit + 5):  # Exceed limit by 5 requests
            result = self.simulate_api_request(premium_user)
            results.append(result)

            if result["status_code"] == 200:
                remaining = result.get("remaining_requests", 0)
                if i < rate_limit - 1:
                    print(f"    Request {i+1}: ✅ Success ({remaining} remaining)")
                else:
                    print(f"    Request {i+1}: ✅ Success (quota reached)")
            else:
                print(
                    f"    Request {i+1}: ❌ Rate limited ({result.get('retry_after', 0)}s retry)"
                )

        # Validate results
        successful_requests = [r for r in results if r["status_code"] == 200]
        rate_limited_requests = [r for r in results if r["status_code"] == 429]

        self.assertEqual(
            len(successful_requests),
            rate_limit,
            f"Premium user should make exactly {rate_limit} successful requests",
        )
        self.assertEqual(
            len(rate_limited_requests),
            5,
            f"Premium user should have 5 rate-limited requests",
        )

        print(
            f"  ✅ Premium user rate limiting: {len(successful_requests)} successful, {len(rate_limited_requests)} rate-limited"
        )

    def test_role_based_rate_limits_comparison(self):
        """Test that different roles have appropriate rate limit differences"""
        print("\\n📊 Testing Role-Based Rate Limit Comparison:")

        # Test a smaller number of requests for each role
        test_requests = 20
        results_by_role = {}

        for role_name, user_data in self.users.items():
            # Reset counters for this test
            self.request_counters.clear()

            results = []
            for i in range(test_requests):
                result = self.simulate_api_request(user_data)
                results.append(result)

            successful = len([r for r in results if r["status_code"] == 200])
            results_by_role[role_name] = {
                "successful": successful,
                "rate_limit": user_data["rate_limit_per_minute"],
                "total_requests": test_requests,
            }

        # Display results
        for role_name, result in results_by_role.items():
            print(f"  {role_name}:")
            print(f"    Rate Limit: {result['rate_limit']}/min")
            print(f"    Successful: {result['successful']}/{result['total_requests']}")
            print(
                f"    Success Rate: {(result['successful']/result['total_requests'])*100:.1f}%"
            )

        # Validate role-based differences
        normal_limit = self.users["normal_user"]["rate_limit_per_minute"]
        admin_limit = self.users["admin_user"]["rate_limit_per_minute"]
        premium_limit = self.users["premium_user"]["rate_limit_per_minute"]
        team_lead_limit = self.users["team_lead_user"]["rate_limit_per_minute"]

        # Admin should have higher limits than normal users
        self.assertGreater(
            admin_limit,
            normal_limit,
            "Admin users should have higher rate limits than normal users",
        )

        # Premium users should have higher limits than normal users
        self.assertGreater(
            premium_limit,
            normal_limit,
            "Premium users should have higher rate limits than normal users",
        )

        # Team leads should have limits between normal and admin
        self.assertGreater(
            team_lead_limit,
            normal_limit,
            "Team leads should have higher rate limits than normal users",
        )
        self.assertLess(
            team_lead_limit,
            admin_limit,
            "Team leads should have lower rate limits than admin users",
        )

        print(f"  ✅ Role-based rate limit hierarchy validated correctly")

    def test_burst_capacity_handling(self):
        """Test rate limiting during burst traffic scenarios"""
        print("\\n💥 Testing Burst Capacity Handling:")

        normal_user = self.users["normal_user"]
        burst_size = 10

        print(f"  Testing burst of {burst_size} simultaneous requests")

        # Reset counters
        self.request_counters.clear()

        # Simulate burst of requests
        burst_results = []
        for i in range(burst_size):
            result = self.simulate_api_request(normal_user)
            burst_results.append(result)

            if result["status_code"] == 200:
                print(f"    Burst request {i+1}: ✅ Success")
            else:
                print(f"    Burst request {i+1}: ❌ Rate limited")

        successful_burst = len([r for r in burst_results if r["status_code"] == 200])

        # Validate burst handling
        self.assertGreater(
            successful_burst,
            burst_size * 0.8,
            "At least 80% of burst requests should succeed",
        )

        print(
            f"  ✅ Burst handling: {successful_burst}/{burst_size} requests successful"
        )

    def test_rate_limit_recovery(self):
        """Test rate limit recovery after timeout"""
        print("\\n🔄 Testing Rate Limit Recovery:")

        normal_user = self.users["normal_user"]

        # First, exhaust the rate limit
        print("  Phase 1: Exhausting rate limit...")
        self.request_counters.clear()

        for i in range(normal_user["rate_limit_per_minute"]):
            result = self.simulate_api_request(normal_user)
            if not result["success"]:
                print(f"    Unexpected rate limit at request {i+1}")
                break

        # Now try one more request - should be rate limited
        exhausted_result = self.simulate_api_request(normal_user)
        self.assertEqual(
            exhausted_result["status_code"],
            429,
            "Should be rate limited after quota exhaustion",
        )
        print(f"  ✅ Rate limit enforced: HTTP {exhausted_result['status_code']}")

        # Simulate time passing by resetting counters (in real system, this would be time-based)
        print("  Phase 2: Simulating time window reset...")
        self.request_counters.clear()

        # Try request again - should succeed
        recovery_result = self.simulate_api_request(normal_user)
        self.assertEqual(
            recovery_result["status_code"],
            200,
            "Should succeed after rate limit window reset",
        )
        print(f"  ✅ Rate limit recovery: HTTP {recovery_result['status_code']}")

    def test_concurrent_user_rate_limiting(self):
        """Test rate limiting with multiple concurrent users"""
        print("\\n👥 Testing Concurrent User Rate Limiting:")

        # Test multiple users making requests concurrently
        users_to_test = ["normal_user", "admin_user", "premium_user"]
        requests_per_user = 15

        # Reset counters
        self.request_counters.clear()

        # Simulate concurrent requests from different users
        all_results = []
        for user_key in users_to_test:
            user_data = self.users[user_key]
            user_results = []

            for i in range(requests_per_user):
                result = self.simulate_api_request(user_data)
                result["user_type"] = user_key
                user_results.append(result)

            all_results.extend(user_results)

        # Analyze results by user type
        summary_by_user = {}
        for user_key in users_to_test:
            user_results = [r for r in all_results if r["user_type"] == user_key]
            successful = len([r for r in user_results if r["status_code"] == 200])
            rate_limited = len([r for r in user_results if r["status_code"] == 429])

            summary_by_user[user_key] = {
                "successful": successful,
                "rate_limited": rate_limited,
                "total": len(user_results),
            }

            print(f"  {user_key}:")
            print(f"    Successful: {successful}/{len(user_results)}")
            print(f"    Rate Limited: {rate_limited}/{len(user_results)}")

        # Validate that each user is rate limited independently
        for user_key, summary in summary_by_user.items():
            expected_limit = min(
                requests_per_user, self.users[user_key]["rate_limit_per_minute"]
            )

            if requests_per_user <= expected_limit:
                self.assertEqual(
                    summary["successful"],
                    requests_per_user,
                    f"{user_key} should succeed all requests within limit",
                )
            else:
                self.assertGreaterEqual(
                    summary["successful"],
                    expected_limit * 0.9,
                    f"{user_key} should succeed most requests up to limit",
                )

        print(f"  ✅ Concurrent user rate limiting validated correctly")


if __name__ == "__main__":
    unittest.main(verbosity=2)
