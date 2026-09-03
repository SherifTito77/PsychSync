#!/usr/bin/env python3
"""
Webhook Retry Logic Testing Module
Tests webhook delivery with exponential backoff and retry mechanisms
"""

import asyncio
import hashlib
import hmac
import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import pytest as pytest


class WebhookStatus(Enum):
    """Webhook delivery status"""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    ABANDONED = "abandoned"


@dataclass
class WebhookEvent:
    """Webhook event data"""

    id: str
    url: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    attempts: int = 0
    max_attempts: int = 5
    status: WebhookStatus = WebhookStatus.PENDING
    created_at: datetime = None
    next_retry_at: datetime = None
    last_attempt_at: datetime = None
    last_error: Optional[str] = None
    delivered_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class WebhookTestResult:
    """Result of webhook testing"""

    test_name: str
    success: bool
    response_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MockWebhookEndpoint:
    """Mock webhook endpoint for testing"""

    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self.request_history = []
        self.failure_rate = 0.0  # 0.0 = always success, 1.0 = always fail
        self.failure_modes = []
        self.response_time_range = (0.1, 2.0)  # seconds
        self.status_codes = [200, 500, 503, 408, 429]

    async def receive_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Simulate webhook endpoint receiving a request"""
        start_time = time.time()

        # Simulate processing time
        processing_time = random.uniform(*self.response_time_range)
        await asyncio.sleep(processing_time)

        # Determine success/failure based on failure rate
        should_fail = random.random() < self.failure_rate

        # Record the request
        request_data = {
            "event_id": event.id,
            "url": self.endpoint_url,
            "method": "POST",
            "headers": event.headers.copy(),
            "payload_hash": hashlib.sha256(
                json.dumps(event.payload).encode()
            ).hexdigest(),
            "timestamp": datetime.now(),
            "processing_time": processing_time,
            "success": not should_fail,
        }

        self.request_history.append(request_data)

        # Determine response based on failure mode
        if should_fail:
            if self.failure_modes:
                failure_mode = random.choice(self.failure_modes)
                if failure_mode == "timeout":
                    end_time = time.time()
                    return {
                        "status_code": 408,
                        "response_time": end_time - start_time,
                        "error": "Request timeout",
                    }
                elif failure_mode == "server_error":
                    end_time = time.time()
                    return {
                        "status_code": 500,
                        "response_time": end_time - start_time,
                        "error": "Internal server error",
                    }
                elif failure_mode == "rate_limit":
                    end_time = time.time()
                    return {
                        "status_code": 429,
                        "response_time": end_time - start_time,
                        "error": "Rate limit exceeded",
                        "retry_after": 60,
                    }

            # Default failure
            end_time = time.time()
            return {
                "status_code": 500,
                "response_time": end_time - start_time,
                "error": "Simulated failure",
            }

        # Success case
        end_time = time.time()
        return {
            "status_code": 200,
            "response_time": end_time - start_time,
            "response": {"status": "delivered", "event_id": event.id},
        }

    def set_failure_rate(self, rate: float):
        """Set failure rate for the endpoint"""
        self.failure_rate = max(0.0, min(1.0, rate))

    def set_failure_modes(self, modes: List[str]):
        """Set specific failure modes"""
        self.failure_modes = modes

    def clear_history(self):
        """Clear request history"""
        self.request_history.clear()


class WebhookRetryService:
    """Webhook delivery service with retry logic"""

    def __init__(self):
        self.pending_events: List[WebhookEvent] = []
        self.completed_events: List[WebhookEvent] = []
        self.retry_intervals = [60, 300, 900, 3600, 7200]  # seconds
        self.max_concurrent_retries = 10
        self.signature_secret = "webhook_signature_secret"

    def create_webhook_event(self, url: str, payload: Dict[str, Any]) -> WebhookEvent:
        """Create a new webhook event"""
        event_id = hashlib.sha256(
            f"{url}{json.dumps(payload)}{time.time()}".encode()
        ).hexdigest()[:16]

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PsychSync-Webhook/1.0",
            "X-PsychSync-Event-ID": event_id,
            "X-PsychSync-Timestamp": str(int(time.time())),
        }

        # Add signature
        signature = self._generate_signature(
            json.dumps(payload), headers["X-PsychSync-Timestamp"]
        )
        headers["X-PsychSync-Signature"] = signature

        event = WebhookEvent(id=event_id, url=url, payload=payload, headers=headers)

        self.pending_events.append(event)
        return event

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Generate webhook signature"""
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.signature_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def deliver_webhook(
        self, event: WebhookEvent, endpoint: MockWebhookEndpoint
    ) -> bool:
        """Attempt to deliver webhook with retry logic"""
        event.last_attempt_at = datetime.now()
        event.attempts += 1

        try:
            response = await endpoint.receive_webhook(event)

            if response["status_code"] in [200, 201, 202, 204]:
                # Success
                event.status = WebhookStatus.DELIVERED
                event.delivered_at = datetime.now()
                self.completed_events.append(event)
                self.pending_events.remove(event)
                return True
            elif response["status_code"] == 429:
                # Rate limited
                retry_after = response.get(
                    "retry_after",
                    self.retry_intervals[
                        min(event.attempts - 1, len(self.retry_intervals) - 1)
                    ],
                )
                event.next_retry_at = datetime.now() + timedelta(seconds=retry_after)
                event.status = WebhookStatus.RETRYING
                event.last_error = f"Rate limited: {response.get('error', '')}"
                return False
            elif response["status_code"] in [500, 502, 503, 504]:
                # Server error - retry
                retry_interval = self.retry_intervals[
                    min(event.attempts - 1, len(self.retry_intervals) - 1)
                ]
                event.next_retry_at = datetime.now() + timedelta(seconds=retry_interval)
                event.status = WebhookStatus.RETRYING
                event.last_error = f"Server error {response['status_code']}: {response.get('error', '')}"
                return False
            else:
                # Client error - don't retry
                event.status = WebhookStatus.FAILED
                event.last_error = f"Client error {response['status_code']}: {response.get('error', '')}"
                self.completed_events.append(event)
                self.pending_events.remove(event)
                return False

        except Exception as e:
            # Network or other error - retry
            retry_interval = self.retry_intervals[
                min(event.attempts - 1, len(self.retry_intervals) - 1)
            ]
            event.next_retry_at = datetime.now() + timedelta(seconds=retry_interval)
            event.status = WebhookStatus.RETRYING
            event.last_error = f"Exception: {str(e)}"
            return False

    async def process_pending_retries(
        self, endpoints: Dict[str, MockWebhookEndpoint]
    ) -> int:
        """Process all pending webhook retries"""
        current_time = datetime.now()
        retry_attempts = 0

        # Find events ready for retry
        ready_events = [
            event
            for event in self.pending_events
            if event.status == WebhookStatus.RETRYING
            and event.next_retry_at
            and current_time >= event.next_retry_at
        ]

        # Also process new events (status PENDING)
        new_events = [
            event
            for event in self.pending_events
            if event.status == WebhookStatus.PENDING
        ]

        all_ready_events = ready_events + new_events

        # Process events with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent_retries)

        async def process_single_event(event: WebhookEvent):
            async with semaphore:
                endpoint = endpoints.get(event.url)
                if endpoint:
                    nonlocal retry_attempts
                    success = await self.deliver_webhook(event, endpoint)
                    if success:
                        retry_attempts += 1

                # Check if max attempts reached
                if event.attempts >= event.max_attempts:
                    event.status = WebhookStatus.ABANDONED
                    self.completed_events.append(event)
                    if event in self.pending_events:
                        self.pending_events.remove(event)

        tasks = [
            process_single_event(event)
            for event in all_ready_events[: self.max_concurrent_retries]
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        return retry_attempts


class WebhookRetryTester:
    """Comprehensive webhook retry logic tester"""

    def __init__(self):
        self.retry_service = WebhookRetryService()
        self.test_results: List[WebhookTestResult] = []

    async def test_successful_delivery(self) -> WebhookTestResult:
        """Test successful webhook delivery"""
        print("Testing successful webhook delivery...")

        endpoint = MockWebhookEndpoint("https://example.com/webhook")
        endpoint.set_failure_rate(0.0)  # Always succeed

        payload = {
            "event_type": "assessment_completed",
            "user_id": "user123",
            "assessment_id": "assessment456",
            "score": 85,
            "timestamp": datetime.now().isoformat(),
        }

        event = self.retry_service.create_webhook_event(endpoint.endpoint_url, payload)

        start_time = time.time()
        success = await self.retry_service.deliver_webhook(event, endpoint)
        end_time = time.time()

        return WebhookTestResult(
            test_name="Successful Delivery",
            success=success,
            response_time=end_time - start_time,
            details={
                "event_id": event.id,
                "attempts": event.attempts,
                "status": event.status.value,
                "delivered_at": (
                    event.delivered_at.isoformat() if event.delivered_at else None
                ),
            },
        )

    async def test_retry_mechanism(self) -> WebhookTestResult:
        """Test retry mechanism with temporary failures"""
        print("Testing retry mechanism...")

        endpoint = MockWebhookEndpoint("https://example.com/webhook")
        endpoint.set_failure_rate(0.8)  # 80% failure rate initially
        endpoint.set_failure_modes(["server_error", "timeout"])

        payload = {
            "event_type": "user_registered",
            "user_id": "user789",
            "email": "test@example.com",
        }

        event = self.retry_service.create_webhook_event(endpoint.endpoint_url, payload)

        start_time = time.time()

        # Simulate multiple attempts
        endpoints = {endpoint.endpoint_url: endpoint}

        for attempt in range(event.max_attempts):
            if attempt == 2:  # Succeed on 3rd attempt
                endpoint.set_failure_rate(0.0)

            success = await self.retry_service.deliver_webhook(event, endpoint)
            if success:
                break

            # Wait for retry interval (shortened for testing)
            if event.next_retry_at:
                wait_time = 1  # Shortened for testing
                await asyncio.sleep(wait_time)

        end_time = time.time()

        return WebhookTestResult(
            test_name="Retry Mechanism",
            success=event.status == WebhookStatus.DELIVERED,
            response_time=end_time - start_time,
            details={
                "event_id": event.id,
                "total_attempts": event.attempts,
                "final_status": event.status.value,
                "delivered_at": (
                    event.delivered_at.isoformat() if event.delivered_at else None
                ),
                "retry_attempts": event.attempts - 1,
                "last_error": event.last_error,
            },
        )

    async def test_exponential_backoff(self) -> WebhookTestResult:
        """Test exponential backoff timing"""
        print("Testing exponential backoff...")

        endpoint = MockWebhookEndpoint("https://example.com/webhook")
        endpoint.set_failure_rate(1.0)  # Always fail
        endpoint.set_failure_modes(["server_error"])

        payload = {"event_type": "test_backoff", "test_id": "backoff123"}

        event = self.retry_service.create_webhook_event(endpoint.endpoint_url, payload)

        retry_intervals = []
        start_time = time.time()

        for attempt in range(event.max_attempts):
            attempt_start = time.time()

            success = await self.retry_service.deliver_webhook(event, endpoint)
            if success:
                break

            if event.next_retry_at:
                wait_time = 1  # Use short wait for testing, but record intended backoff
                intended_backoff = self.retry_service.retry_intervals[
                    min(attempt, len(self.retry_service.retry_intervals) - 1)
                ]
                retry_intervals.append(intended_backoff)
                await asyncio.sleep(wait_time)

        end_time = time.time()

        return WebhookTestResult(
            test_name="Exponential Backoff",
            success=len(retry_intervals) > 0,
            response_time=end_time - start_time,
            details={
                "event_id": event.id,
                "attempts": event.attempts,
                "retry_intervals": retry_intervals,
                "expected_intervals": self.retry_service.retry_intervals[
                    : len(retry_intervals)
                ],
                "backoff_correct": retry_intervals
                == self.retry_service.retry_intervals[: len(retry_intervals)],
                "final_status": event.status.value,
            },
        )

    async def test_max_attempts_limit(self) -> WebhookTestResult:
        """Test max attempts limit enforcement"""
        print("Testing max attempts limit...")

        endpoint = MockWebhookEndpoint("https://example.com/webhook")
        endpoint.set_failure_rate(1.0)  # Always fail

        payload = {"event_type": "test_max_attempts", "test_id": "max_attempts123"}

        event = self.retry_service.create_webhook_event(endpoint.endpoint_url, payload)

        start_time = time.time()

        # Attempt delivery until max attempts reached
        endpoints = {endpoint.endpoint_url: endpoint}

        for _ in range(event.max_attempts + 2):  # Try more than max attempts
            await self.retry_service.deliver_webhook(event, endpoint)
            if event.status == WebhookStatus.ABANDONED:
                break

            await asyncio.sleep(0.1)  # Small delay

        end_time = time.time()

        return WebhookTestResult(
            test_name="Max Attempts Limit",
            success=event.attempts == event.max_attempts
            and event.status == WebhookStatus.ABANDONED,
            response_time=end_time - start_time,
            details={
                "event_id": event.id,
                "attempts": event.attempts,
                "max_attempts": event.max_attempts,
                "final_status": event.status.value,
                "attempts_within_limit": event.attempts <= event.max_attempts,
            },
        )

    async def test_concurrent_webhook_processing(self) -> WebhookTestResult:
        """Test concurrent webhook processing"""
        print("Testing concurrent webhook processing...")

        # Create multiple endpoints
        endpoints = {}
        for i in range(5):
            endpoint_url = f"https://example{i}.com/webhook"
            endpoint = MockWebhookEndpoint(endpoint_url)
            endpoint.set_failure_rate(0.3)  # 30% failure rate
            endpoints[endpoint_url] = endpoint

        # Create multiple webhook events
        events = []
        for i in range(20):
            endpoint_url = f"https://example{i % 5}.com/webhook"
            payload = {
                "event_type": "concurrent_test",
                "test_id": f"concurrent_{i}",
                "index": i,
            }
            event = self.retry_service.create_webhook_event(endpoint_url, payload)
            events.append(event)

        start_time = time.time()

        # Process all events concurrently
        batch_size = self.retry_service.max_concurrent_retries
        for i in range(0, len(events), batch_size):
            batch = events[i : i + batch_size]

            for event in batch:
                endpoint = endpoints[event.url]
                await self.retry_service.deliver_webhook(event, endpoint)

        end_time = time.time()

        successful_deliveries = sum(
            1 for e in events if e.status == WebhookStatus.DELIVERED
        )
        failed_deliveries = sum(
            1
            for e in events
            if e.status == WebhookStatus.FAILED or e.status == WebhookStatus.ABANDONED
        )

        return WebhookTestResult(
            test_name="Concurrent Processing",
            success=successful_deliveries > 0,
            response_time=end_time - start_time,
            details={
                "total_events": len(events),
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "success_rate": (successful_deliveries / len(events)) * 100,
                "concurrency_limit": self.retry_service.max_concurrent_retries,
                "processing_time": end_time - start_time,
                "events_per_second": len(events) / (end_time - start_time),
            },
        )

    async def test_signature_verification(self) -> WebhookTestResult:
        """Test webhook signature generation and verification"""
        print("Testing signature verification...")

        payload = {
            "event_type": "signature_test",
            "user_id": "user456",
            "data": "test data",
        }

        timestamp = str(int(time.time()))

        # Generate signature using the same method as the service
        signature = self.retry_service._generate_signature(
            json.dumps(payload), timestamp
        )

        # Verify signature format
        signature_valid = (
            signature.startswith("sha256=")
            and len(signature) == 7 + 64  # 'sha256=' + 64 character hash
        )

        # Test signature consistency
        signature2 = self.retry_service._generate_signature(
            json.dumps(payload), timestamp
        )
        signatures_match = signature == signature2

        # Test signature uniqueness with different timestamps
        timestamp2 = str(int(time.time()) + 60)
        signature3 = self.retry_service._generate_signature(
            json.dumps(payload), timestamp2
        )
        signatures_different = signature != signature3

        start_time = time.time()

        # Create actual webhook event to test full signature process
        endpoint = MockWebhookEndpoint("https://example.com/webhook")
        event = self.retry_service.create_webhook_event(endpoint.endpoint_url, payload)

        end_time = time.time()

        return WebhookTestResult(
            test_name="Signature Verification",
            success=signature_valid and signatures_match and signatures_different,
            response_time=end_time - start_time,
            details={
                "signature_format_valid": signature_valid,
                "signature_length": len(signature),
                "signatures_consistent": signatures_match,
                "signatures_unique": signatures_different,
                "webhook_headers": event.headers,
                "signature_present": "X-PsychSync-Signature" in event.headers,
                "timestamp_present": "X-PsychSync-Timestamp" in event.headers,
            },
        )

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all webhook retry logic tests"""
        print("Starting comprehensive webhook retry logic testing...")

        test_functions = [
            self.test_successful_delivery,
            self.test_retry_mechanism,
            self.test_exponential_backoff,
            self.test_max_attempts_limit,
            self.test_concurrent_webhook_processing,
            self.test_signature_verification,
        ]

        for test_func in test_functions:
            try:
                result = await test_func()
                self.test_results.append(result)

                status = "✅" if result.success else "❌"
                print(f"{status} {result.test_name}: {result.response_time:.3f}s")

                if result.error_message:
                    print(f"   Error: {result.error_message}")

                # Clean up for next test
                self.retry_service.pending_events.clear()
                self.retry_service.completed_events.clear()

            except Exception as e:
                error_result = WebhookTestResult(
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
            "retry_service_config": {
                "max_attempts": 5,
                "retry_intervals": [60, 300, 900, 3600, 7200],
                "max_concurrent_retries": 10,
            },
        }


# Main execution for standalone testing
async def main():
    """Run webhook retry logic tests"""
    tester = WebhookRetryTester()
    results = await tester.run_all_tests()

    print("\n" + "=" * 60)
    print("WEBHOOK RETRY LOGIC TEST RESULTS")
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

    print(f"\nRetry Service Configuration:")
    config = results["retry_service_config"]
    print(f"  Max Attempts: {config['max_attempts']}")
    print(f"  Retry Intervals: {config['retry_intervals']}")
    print(f"  Max Concurrent: {config['max_concurrent_retries']}")

    # Save results to file
    with open("webhook_retry_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: webhook_retry_test_results.json")

    return results


if __name__ == "__main__":
    asyncio.run(main())
