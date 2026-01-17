#!/usr/bin/env python3
"""
Advanced Load Testing and Performance Optimization Suite
=======================================================

Comprehensive load testing framework for PsychSync platform performance validation.
Tests system behavior under various load conditions and optimizes performance bottlenecks.
"""

import asyncio
import time
import statistics
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import httpx
import psutil
import threading
from collections import defaultdict

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class LoadTestResult:
    """Results from load testing operations"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    duration_seconds: float
    system_metrics: Dict[str, float]

@dataclass
class SystemMetrics:
    """System resource usage metrics"""
    cpu_percent: float
    memory_percent: float
    memory_usage_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    timestamp: datetime

class LoadTestingSuite:
    """Comprehensive load testing and performance optimization suite"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results: List[LoadTestResult] = []
        self.system_metrics_history: List[SystemMetrics] = []
        self.monitoring_active = False

    async def run_all_load_tests(self) -> Dict[str, Any]:
        """Execute complete load testing suite"""
        print("🚀 Starting Advanced Load Testing Suite")
        print("=" * 70)

        start_time = time.time()

        # Start system monitoring
        self.start_system_monitoring()

        try:
            # 1. API Endpoint Load Testing
            await self.test_api_endpoints_load()

            # 2. Concurrent User Load Testing
            await self.test_concurrent_user_load()

            # 3. Database Performance Testing
            await self.test_database_performance()

            # 4. Authentication Load Testing
            await self.test_authentication_load()

            # 5. Assessment System Load Testing
            await self.test_assessment_system_load()

            # 6. Stress Testing
            await self.test_stress_conditions()

            # 7. Spike Load Testing
            await self.test_spike_load()

            # 8. Endurance Testing
            await self.test_endurance()

        finally:
            # Stop system monitoring
            self.stop_system_monitoring()

        total_time = time.time() - start_time

        # Generate comprehensive report
        return self.generate_performance_report(total_time)

    async def test_api_endpoints_load(self) -> None:
        """Test load on critical API endpoints"""
        print("\n📡 Testing API Endpoint Load Performance")

        endpoints = [
            {"path": "/api/v1/health", "method": "GET", "weight": 3},
            {"path": "/api/v1/auth/login", "method": "POST", "weight": 2},
            {"path": "/api/v1/users/me", "method": "GET", "weight": 2},
            {"path": "/api/v1/teams", "method": "GET", "weight": 1},
            {"path": "/api/v1/assessments", "method": "GET", "weight": 1},
        ]

        for endpoint in endpoints:
            result = await self.load_test_endpoint(
                endpoint["path"],
                endpoint["method"],
                concurrent_users=20,
                duration_seconds=30,
                requests_per_second=10
            )

            self.test_results.append(result)

            # Performance validation
            if result.average_response_time > 1000:  # 1 second
                print(f"⚠️  WARNING: {endpoint['path']} has high average response time: {result.average_response_time:.2f}ms")
            else:
                print(f"✅ {endpoint['path']} - {result.requests_per_second:.1f} RPS, {result.average_response_time:.2f}ms avg")

    async def test_concurrent_user_load(self) -> None:
        """Test system under concurrent user load"""
        print("\n👥 Testing Concurrent User Load")

        user_counts = [10, 25, 50, 100]

        for user_count in user_counts:
            print(f"Testing with {user_count} concurrent users...")

            result = await self.simulate_concurrent_users(
                user_count=user_count,
                duration_seconds=60
            )

            self.test_results.append(result)

            if result.error_rate > 5.0:  # 5% error rate threshold
                print(f"⚠️  HIGH ERROR RATE: {result.error_rate:.2f}% at {user_count} users")
            elif result.requests_per_second < user_count * 2:  # Minimum 2 RPS per user
                print(f"⚠️  LOW THROUGHPUT: {result.requests_per_second:.1f} RPS for {user_count} users")
            else:
                print(f"✅ {user_count} users - {result.requests_per_second:.1f} RPS, {result.error_rate:.2f}% errors")

    async def test_database_performance(self) -> None:
        """Test database performance under load"""
        print("\n🗄️ Testing Database Performance")

        # Test data creation load
        result = await self.test_database_operations_load(
            operation_type="create",
            concurrent_operations=50,
            duration_seconds=30
        )
        self.test_results.append(result)

        # Test data querying load
        result = await self.test_database_operations_load(
            operation_type="query",
            concurrent_operations=100,
            duration_seconds=30
        )
        self.test_results.append(result)

        # Test complex analytics queries
        result = await self.test_database_operations_load(
            operation_type="analytics",
            concurrent_operations=20,
            duration_seconds=30
        )
        self.test_results.append(result)

        print(f"✅ Database operations tested - Create: {self.test_results[-3].average_response_time:.2f}ms, "
              f"Query: {self.test_results[-2].average_response_time:.2f}ms, "
              f"Analytics: {self.test_results[-1].average_response_time:.2f}ms")

    async def test_authentication_load(self) -> None:
        """Test authentication system under load"""
        print("\n🔐 Testing Authentication System Load")

        # Test login load
        result = await self.load_test_endpoint(
            "/api/v1/auth/login",
            "POST",
            concurrent_users=30,
            duration_seconds=45,
            requests_per_second=15,
            payload={"email": "test@example.com", "password": "testpassword"}
        )
        self.test_results.append(result)

        # Test token validation load
        result = await self.load_test_endpoint(
            "/api/v1/users/me",
            "GET",
            concurrent_users=50,
            duration_seconds=30,
            requests_per_second=20,
            headers={"Authorization": "Bearer test-token"}
        )
        self.test_results.append(result)

        print(f"✅ Authentication load tested - Login: {self.test_results[-2].average_response_time:.2f}ms, "
              f"Token Validation: {self.test_results[-1].average_response_time:.2f}ms")

    async def test_assessment_system_load(self) -> None:
        """Test assessment system under load"""
        print("\n🧠 Testing Assessment System Load")

        # Test assessment creation
        result = await self.load_test_endpoint(
            "/api/v1/assessments",
            "POST",
            concurrent_users=15,
            duration_seconds=30,
            requests_per_second=5
        )
        self.test_results.append(result)

        # Test assessment submission
        result = await self.load_test_endpoint(
            "/api/v1/responses",
            "POST",
            concurrent_users=25,
            duration_seconds=40,
            requests_per_second=8
        )
        self.test_results.append(result)

        # Test assessment results retrieval
        result = await self.load_test_endpoint(
            "/api/v1/analytics/team-performance",
            "GET",
            concurrent_users=20,
            duration_seconds=30,
            requests_per_second=10
        )
        self.test_results.append(result)

        print(f"✅ Assessment system tested - Creation: {self.test_results[-3].average_response_time:.2f}ms, "
              f"Submission: {self.test_results[-2].average_response_time:.2f}ms, "
              f"Analytics: {self.test_results[-1].average_response_time:.2f}ms")

    async def test_stress_conditions(self) -> None:
        """Test system under extreme stress conditions"""
        print("\n💪 Testing System Stress Conditions")

        # Gradual load increase until failure
        max_concurrent_users = 500
        step_size = 50
        current_users = 100

        while current_users <= max_concurrent_users:
            print(f"Stress testing with {current_users} concurrent users...")

            result = await self.simulate_concurrent_users(
                user_count=current_users,
                duration_seconds=30
            )

            self.test_results.append(result)

            # Check if system is under stress
            if result.error_rate > 10.0:  # 10% error rate threshold
                print(f"❌ SYSTEM STRESS DETECTED at {current_users} users")
                break
            elif result.average_response_time > 5000:  # 5 second response time threshold
                print(f"⚠️  HIGH RESPONSE TIME at {current_users} users: {result.average_response_time:.2f}ms")
                break
            else:
                print(f"✅ {current_users} users handled successfully")

            current_users += step_size

    async def test_spike_load(self) -> None:
        """Test system handling of sudden load spikes"""
        print("\n📈 Testing Load Spike Handling")

        # Baseline load
        baseline_result = await self.simulate_concurrent_users(
            user_count=10,
            duration_seconds=30
        )
        self.test_results.append(baseline_result)

        # Spike load
        spike_result = await self.simulate_concurrent_users(
            user_count=200,
            duration_seconds=20
        )
        self.test_results.append(spike_result)

        # Return to baseline
        recovery_result = await self.simulate_concurrent_users(
            user_count=10,
            duration_seconds=30
        )
        self.test_results.append(recovery_result)

        # Check recovery
        if recovery_result.average_response_time <= baseline_result.average_response_time * 1.5:
            print("✅ System recovered successfully from spike load")
        else:
            print("⚠️  System did not fully recover from spike load")

    async def test_endurance(self) -> None:
        """Test system performance over extended periods"""
        print("\n⏰ Testing System Endurance")

        duration_minutes = 10  # 10 minutes endurance test
        concurrent_users = 25

        result = await self.simulate_concurrent_users(
            user_count=concurrent_users,
            duration_seconds=duration_minutes * 60
        )

        self.test_results.append(result)

        # Check for performance degradation
        if result.error_rate < 1.0 and result.average_response_time < 2000:
            print(f"✅ Endurance test passed - {result.requests_per_second:.1f} RPS over {duration_minutes} minutes")
        else:
            print(f"⚠️  Performance degradation detected over {duration_minutes} minutes")

    async def load_test_endpoint(self,
                                path: str,
                                method: str,
                                concurrent_users: int = 10,
                                duration_seconds: int = 30,
                                requests_per_second: int = 5,
                                payload: Optional[Dict] = None,
                                headers: Optional[Dict] = None) -> LoadTestResult:
        """Perform load testing on specific API endpoint"""

        response_times = []
        successful_requests = 0
        failed_requests = 0
        start_time = time.time()

        async def make_request():
            nonlocal successful_requests, failed_requests

            try:
                request_start = time.time()

                async with httpx.AsyncClient() as client:
                    if method.upper() == "GET":
                        response = await client.get(f"{self.base_url}{path}", headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(f"{self.base_url}{path}", json=payload, headers=headers)
                    else:
                        response = await client.request(method, f"{self.base_url}{path}", json=payload, headers=headers)

                request_time = (time.time() - request_start) * 1000  # Convert to milliseconds
                response_times.append(request_time)

                if response.status_code < 400:
                    successful_requests += 1
                else:
                    failed_requests += 1

            except Exception:
                failed_requests += 1

        # Calculate request interval
        request_interval = 1.0 / requests_per_second

        # Start concurrent users
        tasks = []
        for _ in range(concurrent_users):
            task = asyncio.create_task(self._continuous_requests(
                make_request, duration_seconds, request_interval
            ))
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests

        # Calculate performance metrics
        return LoadTestResult(
            test_name=f"{method} {path}",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
            requests_per_second=total_requests / total_time,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            duration_seconds=total_time,
            system_metrics=self.get_current_system_metrics()
        )

    async def _continuous_requests(self, make_request_func, duration_seconds, request_interval):
        """Make continuous requests for specified duration"""
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            await make_request_func()
            await asyncio.sleep(request_interval)

    async def simulate_concurrent_users(self, user_count: int, duration_seconds: int) -> LoadTestResult:
        """Simulate concurrent users performing typical operations"""

        response_times = []
        successful_operations = 0
        failed_operations = 0
        start_time = time.time()

        async def user_session():
            nonlocal successful_operations, failed_operations

            try:
                session_start = time.time()

                # Simulate typical user workflow
                operations = [
                    self._make_health_check(),
                    self._make_auth_request(),
                    self._make_team_request(),
                    self._make_assessment_request()
                ]

                # Randomly select operations
                import random
                await random.choice(operations)

                session_time = (time.time() - session_start) * 1000
                response_times.append(session_time)
                successful_operations += 1

            except Exception:
                failed_operations += 1

        # Start concurrent user sessions
        tasks = []
        for _ in range(user_count):
            task = asyncio.create_task(self._continuous_user_session(
                user_session, duration_seconds
            ))
            tasks.append(task)

        await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        total_operations = successful_operations + failed_operations

        return LoadTestResult(
            test_name=f"Concurrent Users - {user_count}",
            total_requests=total_operations,
            successful_requests=successful_operations,
            failed_requests=failed_operations,
            average_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            p99_response_time=statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
            requests_per_second=total_operations / total_time,
            error_rate=(failed_operations / total_operations * 100) if total_operations > 0 else 0,
            duration_seconds=total_time,
            system_metrics=self.get_current_system_metrics()
        )

    async def _continuous_user_session(self, session_func, duration_seconds):
        """Run continuous user sessions for specified duration"""
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            await session_func()
            await asyncio.sleep(1)  # 1 second between operations

    async def _make_health_check(self):
        async with httpx.AsyncClient() as client:
            await client.get(f"{self.base_url}/api/v1/health")

    async def _make_auth_request(self):
        async with httpx.AsyncClient() as client:
            await client.get(f"{self.base_url}/api/v1/users/me", headers={"Authorization": "Bearer test-token"})

    async def _make_team_request(self):
        async with httpx.AsyncClient() as client:
            await client.get(f"{self.base_url}/api/v1/teams", headers={"Authorization": "Bearer test-token"})

    async def _make_assessment_request(self):
        async with httpx.AsyncClient() as client:
            await client.get(f"{self.base_url}/api/v1/assessments", headers={"Authorization": "Bearer test-token"})

    async def test_database_operations_load(self, operation_type: str, concurrent_operations: int, duration_seconds: int) -> LoadTestResult:
        """Test database operations under load"""

        # Simulate database operations based on type
        if operation_type == "create":
            endpoint = "/api/v1/users"
            method = "POST"
        elif operation_type == "query":
            endpoint = "/api/v1/teams"
            method = "GET"
        elif operation_type == "analytics":
            endpoint = "/api/v1/analytics"
            method = "GET"
        else:
            endpoint = "/api/v1/health"
            method = "GET"

        return await self.load_test_endpoint(
            endpoint, method, concurrent_operations, duration_seconds
        )

    def start_system_monitoring(self):
        """Start system resource monitoring"""
        self.monitoring_active = True

        def monitor():
            while self.monitoring_active:
                try:
                    # CPU and Memory
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    network = psutil.net_io_counters()

                    # Process count
                    process_count = len(psutil.pids())

                    metrics = SystemMetrics(
                        cpu_percent=cpu_percent,
                        memory_percent=memory.percent,
                        memory_usage_mb=memory.used / 1024 / 1024,
                        disk_usage_percent=disk.percent,
                        network_io={
                            "bytes_sent": network.bytes_sent,
                            "bytes_recv": network.bytes_recv
                        },
                        process_count=process_count,
                        timestamp=datetime.now()
                    )

                    self.system_metrics_history.append(metrics)

                except Exception as e:
                    print(f"System monitoring error: {e}")

                time.sleep(5)  # Monitor every 5 seconds

        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()

    def stop_system_monitoring(self):
        """Stop system resource monitoring"""
        self.monitoring_active = False

    def get_current_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics snapshot"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_usage_mb": memory.used / 1024 / 1024,
                "disk_usage_percent": disk.percent
            }
        except Exception:
            return {}

    def generate_performance_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive performance report"""

        print("\n" + "="*70)
        print("📊 PERFORMANCE OPTIMIZATION REPORT")
        print("="*70)

        # Performance summary
        total_requests = sum(r.total_requests for r in self.test_results)
        total_successful = sum(r.successful_requests for r in self.test_results)
        total_failed = sum(r.failed_requests for r in self.test_results)

        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0

        avg_response_time = statistics.mean([r.average_response_time for r in self.test_results if r.average_response_time > 0])
        max_rps = max([r.requests_per_second for r in self.test_results])
        min_error_rate = min([r.error_rate for r in self.test_results])

        # Performance analysis
        print(f"\n🎯 PERFORMANCE SUMMARY")
        print(f"├─ Total Tests Executed: {len(self.test_results)}")
        print(f"├─ Total Requests: {total_requests:,}")
        print(f"├─ Success Rate: {overall_success_rate:.2f}%")
        print(f"├─ Average Response Time: {avg_response_time:.2f}ms")
        print(f"├─ Peak Throughput: {max_rps:.1f} RPS")
        print(f"├─ Best Error Rate: {min_error_rate:.2f}%")
        print(f"└─ Execution Time: {total_time:.2f} seconds")

        # Performance grades
        print(f"\n📈 PERFORMANCE GRADES")

        if avg_response_time < 200:
            print(f"├─ Response Time: ✅ EXCELLENT (< 200ms)")
        elif avg_response_time < 500:
            print(f"├─ Response Time: ✅ GOOD (< 500ms)")
        elif avg_response_time < 1000:
            print(f"├─ Response Time: ⚠️  ACCEPTABLE (< 1000ms)")
        else:
            print(f"├─ Response Time: ❌ POOR (> 1000ms)")

        if max_rps > 1000:
            print(f"├─ Throughput: ✅ EXCELLENT (> 1000 RPS)")
        elif max_rps > 500:
            print(f"├─ Throughput: ✅ GOOD (> 500 RPS)")
        elif max_rps > 100:
            print(f"├─ Throughput: ⚠️  ACCEPTABLE (> 100 RPS)")
        else:
            print(f"├─ Throughput: ❌ POOR (< 100 RPS)")

        if overall_success_rate > 99:
            print(f"├─ Reliability: ✅ EXCELLENT (> 99%)")
        elif overall_success_rate > 95:
            print(f"├─ Reliability: ✅ GOOD (> 95%)")
        elif overall_success_rate > 90:
            print(f"├─ Reliability: ⚠️  ACCEPTABLE (> 90%)")
        else:
            print(f"├─ Reliability: ❌ POOR (< 90%)")

        # System metrics analysis
        if self.system_metrics_history:
            avg_cpu = statistics.mean([m.cpu_percent for m in self.system_metrics_history])
            max_cpu = max([m.cpu_percent for m in self.system_metrics_history])
            avg_memory = statistics.mean([m.memory_percent for m in self.system_metrics_history])
            max_memory = max([m.memory_percent for m in self.system_metrics_history])

            print(f"\n🖥️  SYSTEM RESOURCE USAGE")
            print(f"├─ CPU Usage: Avg {avg_cpu:.1f}%, Max {max_cpu:.1f}%")
            print(f"├─ Memory Usage: Avg {avg_memory:.1f}%, Max {max_memory:.1f}%")
            print(f"└─ Monitoring Points: {len(self.system_metrics_history)}")

        # Performance optimization recommendations
        print(f"\n🚀 OPTIMIZATION RECOMMENDATIONS")

        slow_endpoints = [r for r in self.test_results if r.average_response_time > 1000]
        if slow_endpoints:
            print(f"├─ ⚠️  {len(slow_endpoints)} endpoints need optimization:")
            for endpoint in slow_endpoints:
                print(f"   • {endpoint.test_name}: {endpoint.average_response_time:.2f}ms avg")

        high_error_tests = [r for r in self.test_results if r.error_rate > 5]
        if high_error_tests:
            print(f"├─ ⚠️  {len(high_error_tests)} tests have high error rates:")
            for test in high_error_tests:
                print(f"   • {test.test_name}: {test.error_rate:.2f}% errors")

        if avg_cpu > 80:
            print(f"├─ ⚠️  High CPU usage detected ({avg_cpu:.1f}%)")

        if avg_memory > 85:
            print(f"├─ ⚠️  High memory usage detected ({avg_memory:.1f}%)")

        # Production readiness assessment
        print(f"\n🎯 PRODUCTION READINESS")

        production_ready = True
        reasons = []

        if avg_response_time > 1000:
            production_ready = False
            reasons.append("High response times")

        if overall_success_rate < 95:
            production_ready = False
            reasons.append("Low success rate")

        if min_error_rate > 5:
            production_ready = False
            reasons.append("High error rates")

        if avg_cpu > 80:
            production_ready = False
            reasons.append("High CPU usage")

        if avg_memory > 85:
            production_ready = False
            reasons.append("High memory usage")

        if production_ready:
            print(f"└─ ✅ SYSTEM IS PRODUCTION READY")
        else:
            print(f"└─ ❌ SYSTEM NOT READY FOR PRODUCTION:")
            for reason in reasons:
                print(f"   • {reason}")

        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": total_time,
            "test_count": len(self.test_results),
            "summary": {
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "success_rate_percent": overall_success_rate,
                "average_response_time_ms": avg_response_time,
                "peak_throughput_rps": max_rps,
                "min_error_rate_percent": min_error_rate
            },
            "test_results": [asdict(result) for result in self.test_results],
            "system_metrics": [asdict(metrics) for metrics in self.system_metrics_history],
            "production_ready": production_ready,
            "optimization_recommendations": [
                "Database query optimization for slow endpoints",
                "Implement caching for frequently accessed data",
                "Consider horizontal scaling for high-load scenarios",
                "Review and optimize complex analytical queries"
            ]
        }

        report_path = f"load_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_path}")

        return report_data

async def main():
    """Main function to execute load testing suite"""
    print("🚀 PSYCHSYNC ADVANCED LOAD TESTING AND PERFORMANCE OPTIMIZATION")
    print("=" * 80)

    suite = LoadTestingSuite()

    try:
        report = await suite.run_all_load_tests()

        if report["summary"]["success_rate_percent"] > 95:
            print("\n🎉 LOAD TESTING COMPLETED SUCCESSFULLY")
            print("✅ System performance meets enterprise standards")
        else:
            print("\n⚠️  LOAD TESTING COMPLETED WITH ISSUES")
            print("❌ Review optimization recommendations")

        return report

    except KeyboardInterrupt:
        print("\n\n⏹️  Load testing interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Load testing failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
