#!/usr/bin/env python3
"""
SSH Brute Force Protection Tester
Tests SSH server against brute force attacks and evaluates security controls
"""

import os
import sys
import socket
import time
import threading
import queue
import json
import hashlib
import logging
import paramiko
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BruteForceAttempt:
    """Brute force attempt data class"""
    attempt_id: str
    timestamp: datetime
    ip_address: str
    username: str
    password: str
    success: bool
    response_time: float
    error_message: str
    blocked: bool

@dataclass
class SSHSecurityTestResult:
    """SSH security test result"""
    ssh_host: str
    ssh_port: int
    total_attempts: int
    successful_attempts: int
    blocked_attempts: int
    average_response_time: float
    max_concurrent_attempts: int
    rate_limiting_detected: bool
    ip_blocking_detected: bool
    account_lockout_detected: bool
    security_score: int
    recommendations: List[str]

class SSHBruteForceTester:
    """SSH brute force protection tester"""

    def __init__(self, ssh_host: str = "localhost", ssh_port: int = 22):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.attempts = []
        self.start_time = None
        self.end_time = None
        self.concurrent_attempts = 0
        self.max_concurrent = 0
        self.concurrent_lock = threading.Lock()

        # Test configurations
        self.test_usernames = ["admin", "root", "user", "test", "guest", "administrator"]
        self.test_passwords = [
            "password", "123456", "admin", "root", "password123",
            "qwerty", "letmein", "welcome", "changeme", "default",
            "pass", "test", "user", "guest", "111111", "123123"
        ]

    def run_comprehensive_test(self) -> SSHSecurityTestResult:
        """Run comprehensive SSH brute force protection tests"""
        print("🔐 Starting SSH Brute Force Protection Test")
        print("=" * 60)

        self.start_time = datetime.now()

        try:
            # Test 1: Basic brute force attempt
            print("🔍 Test 1: Basic brute force attempt...")
            self._test_basic_brute_force()

            # Test 2: Rapid successive attempts
            print("\n🔍 Test 2: Rapid successive attempts...")
            self._test_rapid_attempts()

            # Test 3: Distributed brute force simulation
            print("\n🔍 Test 3: Distributed brute force simulation...")
            self._test_distributed_brute_force()

            # Test 4: Single account focus attack
            print("\n🔍 Test 4: Single account focus attack...")
            self._test_account_focus_attack()

            # Test 5: Credential stuffing simulation
            print("\n🔍 Test 5: Credential stuffing simulation...")
            self._test_credential_stuffing()

        except Exception as e:
            logger.error(f"SSH brute force test failed: {str(e)}")

        self.end_time = datetime.now()

        # Analyze results and generate recommendations
        return self._analyze_test_results()

    def _test_basic_brute_force(self, attempts: int = 50) -> None:
        """Test basic brute force with common credentials"""
        print(f"  Testing {attempts} credential combinations...")

        attempt_queue = queue.Queue()

        # Generate credential combinations
        for i in range(min(attempts, len(self.test_usernames) * len(self.test_passwords))):
            username = self.test_usernames[i % len(self.test_usernames)]
            password = self.test_passwords[i % len(self.test_passwords)]
            attempt_queue.put((username, password))

        # Execute attempts with limited concurrency
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for _ in range(min(attempts, 20)):  # Limit to 20 concurrent attempts
                try:
                    username, password = attempt_queue.get_nowait()
                    future = executor.submit(self._attempt_ssh_login, username, password, "basic_test")
                    futures.append(future)
                except queue.Empty:
                    break

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    self.attempts.append(result)

                    if result.blocked:
                        print(f"    ⛔ Attempt blocked: {result.username}@{result.ip_address}")
                        break  # Stop if blocking is detected

                except Exception as e:
                    logger.error(f"Basic brute force attempt failed: {str(e)}")

    def _test_rapid_attempts(self, attempts: int = 100) -> None:
        """Test rapid successive attempts to trigger rate limiting"""
        print(f"  Testing {attempts} rapid attempts...")

        start_time = time.time()

        for i in range(min(attempts, 50)):  # Limit to prevent system overload
            username = f"user{i}"
            password = f"pass{i}"

            attempt = self._attempt_ssh_login(username, password, "rapid_test")
            self.attempts.append(attempt)

            # Check if we're being rate limited
            if i > 0:
                time_diff = (attempt.timestamp - self.attempts[-2].timestamp).total_seconds()
                if time_diff < 0.1:  # Very fast response might indicate rate limiting
                    print(f"    ⚡ Rapid response detected ({time_diff:.3f}s)")

            if attempt.blocked:
                print(f"    ⛔ Rapid attempt blocked after {i+1} tries")
                break

    def _test_distributed_brute_force(self, num_threads: int = 10) -> None:
        """Test distributed brute force from multiple threads"""
        print(f"  Testing distributed brute force with {num_threads} threads...")

        def distributed_worker(thread_id: int, attempts_per_thread: int = 10):
            """Worker thread for distributed brute force"""
            for i in range(attempts_per_thread):
                username = f"dist_user_{thread_id}_{i}"
                password = f"dist_pass_{thread_id}_{i}"

                attempt = self._attempt_ssh_login(
                    username,
                    password,
                    f"distributed_test_thread_{thread_id}"
                )
                self.attempts.append(attempt)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(distributed_worker, thread_id)
                for thread_id in range(num_threads)
            ]

            for future in as_completed(futures):
                try:
                    future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Distributed worker failed: {str(e)}")

    def _test_account_focus_attack(self, target_username: str = "admin", attempts: int = 50) -> None:
        """Test focused brute force on single account"""
        print(f"  Testing focused attack on '{target_username}' account...")

        successful_blocked = False

        for i, password in enumerate(self.test_passwords[:attempts]):
            attempt = self._attempt_ssh_login(
                target_username,
                password,
                f"account_focus_test_{i}"
            )
            self.attempts.append(attempt)

            if attempt.blocked:
                print(f"    ⛔ Account focus attack blocked after {i+1} attempts")
                successful_blocked = True
                break

            if attempt.success:
                print(f"    ❌ SUCCESSFUL LOGIN DETECTED! This is a critical security issue!")
                break

        if not successful_blocked and not any(a.success for a in self.attempts[-attempts:]):
            print(f"    ⚠️  Account focus attack completed without blocking")

    def _test_credential_stuffing(self) -> None:
        """Test credential stuffing with realistic password patterns"""
        print("  Testing credential stuffing patterns...")

        # Realistic credential patterns
        credential_patterns = [
            ("admin", "admin123"),
            ("root", "root123"),
            ("user", "user123"),
            ("admin", "password"),
            ("root", "password"),
            ("admin", "letmein"),
            ("root", "changeme"),
            ("administrator", "administrator"),
            ("guest", "guest"),
            ("test", "test123")
        ]

        for username, password in credential_patterns:
            attempt = self._attempt_ssh_login(
                username,
                password,
                "credential_stuffing_test"
            )
            self.attempts.append(attempt)

            if attempt.blocked:
                print(f"    ⛔ Credential stuffing blocked")
                break

    def _attempt_ssh_login(self, username: str, password: str, test_type: str) -> BruteForceAttempt:
        """Attempt SSH login and track results"""
        attempt_id = hashlib.md5(f"{username}{password}{time.time()}".encode()).hexdigest()[:16]
        timestamp = datetime.now()
        ip_address = "127.0.0.1"  # Local testing

        with self.concurrent_lock:
            self.concurrent_attempts += 1
            self.max_concurrent = max(self.max_concurrent, self.concurrent_attempts)

        success = False
        blocked = False
        error_message = ""
        response_time = 0

        start_time = time.time()

        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Attempt connection
            ssh.connect(
                hostname=self.ssh_host,
                port=self.ssh_port,
                username=username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )

            # If we get here, login was successful (this shouldn't happen in secure configuration)
            success = True
            ssh.close()

        except paramiko.AuthenticationException as e:
            # Expected for invalid credentials
            error_message = "Authentication failed"
        except paramiko.SSHException as e:
            # Check for specific error messages that might indicate blocking
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in [
                "blocked", "too many", "rate limit", "temporarily",
                "connection refused", "connection timed out"
            ]):
                blocked = True
                error_message = f"Connection blocked: {str(e)}"
            else:
                error_message = f"SSH error: {str(e)}"
        except socket.timeout:
            error_message = "Connection timeout (possible rate limiting)"
            blocked = True
        except socket.error as e:
            if e.errno == 61:  # Connection refused
                error_message = "Connection refused (possible IP blocking)"
                blocked = True
            else:
                error_message = f"Socket error: {str(e)}"
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time = time.time() - start_time

        with self.concurrent_lock:
            self.concurrent_attempts -= 1

        return BruteForceAttempt(
            attempt_id=attempt_id,
            timestamp=timestamp,
            ip_address=ip_address,
            username=username,
            password=password,
            success=success,
            response_time=response_time,
            error_message=error_message,
            blocked=blocked
        )

    def _analyze_test_results(self) -> SSHSecurityTestResult:
        """Analyze test results and generate security assessment"""
        print("\n📊 Analyzing SSH Security Test Results...")
        print("=" * 60)

        total_attempts = len(self.attempts)
        successful_attempts = len([a for a in self.attempts if a.success])
        blocked_attempts = len([a for a in self.attempts if a.blocked])

        # Calculate response times
        response_times = [a.response_time for a in self.attempts if a.response_time > 0]
        average_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Detect security controls
        rate_limiting_detected = self._detect_rate_limiting()
        ip_blocking_detected = self._detect_ip_blocking()
        account_lockout_detected = self._detect_account_lockout()

        # Calculate security score
        security_score = self._calculate_security_score(
            total_attempts, successful_attempts, blocked_attempts,
            rate_limiting_detected, ip_blocking_detected, account_lockout_detected
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            successful_attempts, blocked_attempts, rate_limiting_detected,
            ip_blocking_detected, account_lockout_detected, security_score
        )

        # Create result object
        result = SSHSecurityTestResult(
            ssh_host=self.ssh_host,
            ssh_port=self.ssh_port,
            total_attempts=total_attempts,
            successful_attempts=successful_attempts,
            blocked_attempts=blocked_attempts,
            average_response_time=average_response_time,
            max_concurrent_attempts=self.max_concurrent,
            rate_limiting_detected=rate_limiting_detected,
            ip_blocking_detected=ip_blocking_detected,
            account_lockout_detected=account_lockout_detected,
            security_score=security_score,
            recommendations=recommendations
        )

        # Print results
        print(f"🎯 SSH Security Score: {security_score}/100")
        print(f"📈 Total Attempts: {total_attempts}")
        print(f"✅ Blocked Attempts: {blocked_attempts}")
        print(f"❌ Successful Attempts: {successful_attempts}")
        print(f"⚡ Max Concurrent: {self.max_concurrent}")
        print(f"📊 Avg Response Time: {average_response_time:.3f}s")
        print(f"🛡️  Rate Limiting: {'✅ Detected' if rate_limiting_detected else '❌ Not Detected'}")
        print(f"🚫 IP Blocking: {'✅ Detected' if ip_blocking_detected else '❌ Not Detected'}")
        print(f"🔒 Account Lockout: {'✅ Detected' if account_lockout_detected else '❌ Not Detected'}")

        if successful_attempts > 0:
            print(f"\n🚨 CRITICAL: {successful_attempts} successful SSH logins detected!")
            print("   This indicates serious security vulnerabilities!")

        if security_score < 50:
            print(f"\n⚠️  WARNING: SSH security score is {security_score}/100")
            print("   SSH server requires immediate security hardening!")

        print(f"\n📋 Security Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

        return result

    def _detect_rate_limiting(self) -> bool:
        """Detect if rate limiting is active"""
        if len(self.attempts) < 10:
            return False

        # Check for increasing response times
        recent_attempts = self.attempts[-20:]
        response_times = [a.response_time for a in recent_attempts if a.response_time > 0]

        if len(response_times) >= 5:
            # Check if response times are increasing significantly
            first_half_avg = sum(response_times[:len(response_times)//2]) / (len(response_times)//2)
            second_half_avg = sum(response_times[len(response_times)//2:]) / (len(response_times)//2)

            if second_half_avg > first_half_avg * 2:
                return True

        # Check for connection refused errors
        connection_refused_count = len([
            a for a in self.attempts
            if "connection refused" in a.error_message.lower()
        ])

        if connection_refused_count > len(self.attempts) * 0.3:
            return True

        return False

    def _detect_ip_blocking(self) -> bool:
        """Detect if IP blocking is active"""
        if len(self.attempts) < 5:
            return False

        # Check for consecutive blocked attempts
        recent_attempts = self.attempts[-10:]
        consecutive_blocked = 0
        max_consecutive = 0

        for attempt in recent_attempts:
            if attempt.blocked:
                consecutive_blocked += 1
                max_consecutive = max(max_consecutive, consecutive_blocked)
            else:
                consecutive_blocked = 0

        return max_consecutive >= 3

    def _detect_account_lockout(self) -> bool:
        """Detect if account lockout is active"""
        if len(self.attempts) < 5:
            return False

        # Check for repeated attempts with same username that result in consistent blocking
        user_attempts = {}
        for attempt in self.attempts:
            if attempt.username not in user_attempts:
                user_attempts[attempt.username] = []
            user_attempts[attempt.username].append(attempt)

        for username, attempts in user_attempts.items():
            if len(attempts) >= 5:
                # Check if all recent attempts are blocked
                recent_attempts = attempts[-5:]
                if all(a.blocked for a in recent_attempts):
                    return True

        return False

    def _calculate_security_score(
        self,
        total_attempts: int,
        successful_attempts: int,
        blocked_attempts: int,
        rate_limiting_detected: bool,
        ip_blocking_detected: bool,
        account_lockout_detected: bool
    ) -> int:
        """Calculate SSH security score (0-100)"""
        score = 100

        # Penalty for successful login attempts
        score -= min(50, successful_attempts * 25)  # Each successful login = -25 points, max -50

        # Bonus for blocked attempts
        score += min(30, blocked_attempts * 2)  # Each blocked attempt = +2 points, max +30

        # Bonus for security controls
        if rate_limiting_detected:
            score += 15
        if ip_blocking_detected:
            score += 10
        if account_lockout_detected:
            score += 10

        # Penalty for no security controls
        if not rate_limiting_detected and not ip_blocking_detected:
            score -= 20

        # Penalty for low block rate
        if total_attempts > 10:
            block_rate = blocked_attempts / total_attempts
            if block_rate < 0.5:
                score -= 15

        return max(0, min(100, score))

    def _generate_recommendations(
        self,
        successful_attempts: int,
        blocked_attempts: int,
        rate_limiting_detected: bool,
        ip_blocking_detected: bool,
        account_lockout_detected: bool,
        security_score: int
    ) -> List[str]:
        """Generate security recommendations based on test results"""
        recommendations = []

        if successful_attempts > 0:
            recommendations.append("URGENT: Disable any successful test accounts immediately")
            recommendations.append("Review all SSH accounts and remove unnecessary ones")
            recommendations.append("Implement strong password policies for SSH accounts")

        if not rate_limiting_detected:
            recommendations.append("Implement SSH rate limiting (e.g., fail2ban)")
            recommendations.append("Configure MaxAuthTries in SSH configuration")
            recommendations.append("Set reasonable connection timeout values")

        if not ip_blocking_detected:
            recommendations.append("Implement IP blocking after failed attempts")
            recommendations.append("Use tools like fail2ban or denyhosts")
            recommendations.append("Configure firewall to block suspicious IPs")

        if not account_lockout_detected:
            recommendations.append("Implement account lockout after failed attempts")
            recommendations.append("Set MaxAuthTries to a reasonable number (e.g., 3-5)")
            recommendations.append("Configure automatic account unlocking policies")

        # General SSH security recommendations
        general_recommendations = [
            "Disable password authentication, use key-based auth only",
            "Disable root login (PermitRootLogin no)",
            "Change default SSH port (22) to non-standard port",
            "Implement strong cryptography (disable weak algorithms)",
            "Use two-factor authentication (2FA) for SSH access",
            "Regularly monitor SSH access logs for suspicious activity",
            "Implement intrusion detection for SSH brute force attempts",
            "Use SSH bastion host for multi-tier access",
            "Regularly update OpenSSH to latest version"
        ]

        recommendations.extend(general_recommendations)

        return recommendations

    def save_detailed_report(self, result: SSHSecurityTestResult, filename: str = None) -> str:
        """Save detailed test report to file"""
        if filename is None:
            filename = f"ssh_brute_force_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_data = {
            "test_id": hashlib.md5(f"{self.ssh_host}{self.ssh_port}{datetime.now()}".encode()).hexdigest()[:16],
            "timestamp": datetime.now().isoformat(),
            "ssh_host": self.ssh_host,
            "ssh_port": self.ssh_port,
            "test_duration": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
            "results": {
                "total_attempts": result.total_attempts,
                "successful_attempts": result.successful_attempts,
                "blocked_attempts": result.blocked_attempts,
                "average_response_time": result.average_response_time,
                "max_concurrent_attempts": result.max_concurrent_attempts,
                "rate_limiting_detected": result.rate_limiting_detected,
                "ip_blocking_detected": result.ip_blocking_detected,
                "account_lockout_detected": result.account_lockout_detected,
                "security_score": result.security_score
            },
            "detailed_attempts": [
                {
                    "attempt_id": a.attempt_id,
                    "timestamp": a.timestamp.isoformat(),
                    "username": a.username,
                    "success": a.success,
                    "blocked": a.blocked,
                    "response_time": a.response_time,
                    "error_message": a.error_message
                }
                for a in self.attempts
            ],
            "recommendations": result.recommendations
        }

        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)

        return filename

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="SSH Brute Force Protection Tester")
    parser.add_argument("--host", default="localhost", help="SSH host to test")
    parser.add_argument("--port", type=int, default=22, help="SSH port to test")
    parser.add_argument("--output", help="Output file for detailed report")

    args = parser.parse_args()

    tester = SSHBruteForceTester(args.host, args.port)

    try:
        print(f"🚀 Starting SSH Brute Force Test against {args.host}:{args.port}")
        print("⚠️  WARNING: This test will attempt brute force attacks.")
        print("   Ensure you have permission to test the target system.")
        print("   Unauthorized testing may be illegal.")

        # Ask for confirmation
        confirm = input("\nDo you want to continue? (y/N): ").lower().strip()
        if confirm != 'y':
            print("Test cancelled by user.")
            sys.exit(0)

        result = tester.run_comprehensive_test()

        # Save detailed report
        if args.output:
            report_file = tester.save_detailed_report(result, args.output)
            print(f"\n📄 Detailed report saved: {report_file}")

        # Exit with appropriate code
        if result.successful_attempts > 0:
            print(f"\n🚨 CRITICAL: Successful SSH logins detected!")
            sys.exit(2)  # Critical
        elif result.security_score < 50:
            print(f"\n⚠️  WARNING: SSH security score is {result.security_score}/100")
            sys.exit(1)  # Warning
        else:
            print(f"\n✅ SSH security score is {result.security_score}/100")
            sys.exit(0)  # Good

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    main()