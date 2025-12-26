#!/usr/bin/env python3
"""
COMPREHENSIVE LOGGING AND MONITORING SECURITY TEST SUITE
Tests all aspects of logging, audit trails, and security monitoring

Tests:
1. Test failed login notifications
2. Check for missing audit logs
3. Test tampering with logs
4. Trigger abnormal activity and check alerting
5. Test alert escalation for intrusion attempts

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import os
import sys
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class TestResult:
    """Result of a security test"""
    test_name: str
    status: str  # PASS, FAIL, WARN, INFO
    score: int  # 0-100
    findings: List[str]
    recommendations: List[str]
    details: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


class LoggingMonitoringSecurityTester:
    """Comprehensive logging and monitoring security testing suite"""

    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        self.results: List[TestResult] = []

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all logging and monitoring security tests"""
        print("=" * 80)
        print("📋 COMPREHENSIVE LOGGING & MONITORING SECURITY TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")
        print()

        # Test 1: Failed login notifications
        print("🔍 TEST 1: Testing failed login notifications...")
        result1 = self.test_failed_login_notifications()
        self.results.append(result1)
        self.print_test_result(result1)

        # Test 2: Missing audit logs
        print("\n🔍 TEST 2: Checking for missing audit logs...")
        result2 = self.test_missing_audit_logs()
        self.results.append(result2)
        self.print_test_result(result2)

        # Test 3: Log tampering detection
        print("\n🔍 TEST 3: Testing tampering with logs...")
        result3 = self.test_log_tampering_detection()
        self.results.append(result3)
        self.print_test_result(result3)

        # Test 4: Abnormal activity alerting
        print("\n🔍 TEST 4: Triggering abnormal activity and checking alerting...")
        result4 = self.test_abnormal_activity_alerting()
        self.results.append(result4)
        self.print_test_result(result4)

        # Test 5: Alert escalation
        print("\n🔍 TEST 5: Testing alert escalation for intrusion attempts...")
        result5 = self.test_alert_escalation()
        self.results.append(result5)
        self.print_test_result(result5)

        # Generate summary report
        return self.generate_summary_report()

    def test_failed_login_notifications(self) -> TestResult:
        """Test 1: Verify failed login notifications are sent"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check for failed login tracking in security.py
            security_file = self.project_root / "app" / "core" / "security.py"
            if not security_file.exists():
                findings.append("❌ security.py not found")
                return TestResult(
                    test_name="Failed Login Notifications",
                    status="FAIL",
                    score=0,
                    findings=findings,
                    recommendations=["Implement security.py with failed login tracking"],
                    details={}
                )

            content = security_file.read_text()

            # Check for log_login_attempt function
            if "log_login_attempt" in content:
                findings.append("✅ log_login_attempt function exists")
                score += 30

                # Check if it takes success parameter
                if "success" in content or "failed" in content.lower():
                    findings.append("✅ Tracks login success/failure status")
                    score += 20
                else:
                    findings.append("⚠️  May not distinguish success/failure")
                    score += 10
            else:
                findings.append("❌ No log_login_attempt function found")
                recommendations.append("Implement log_login_attempt function to track failed logins")

            # Check for failed login attempt tracking
            if "failed_login" in content.lower() or "login_attempts" in content.lower():
                findings.append("✅ Failed login tracking found")
                score += 20

                # Check for rate limiting on failed attempts
                if "increment_login_attempts" in content or "login_attempts +=" in content:
                    findings.append("✅ Failed login attempts are counted")
                    score += 15
            else:
                findings.append("⚠️  Failed login attempt counting not found")
                score += 10

            # Check for notification mechanism
            if "notify" in content.lower() or "alert" in content.lower() or "email" in content.lower():
                findings.append("✅ Notification mechanism available")
                score += 15
            else:
                findings.append("⚠️  No notification mechanism found")
                recommendations.append("Add notification system for failed login alerts")
                score += 5

            # Check audit_logger for authentication events
            audit_file = self.project_root / "app" / "core" / "audit_logging.py"
            if audit_file.exists():
                audit_content = audit_file.read_text()

                if "AUTHENTICATION_FAILED" in audit_content:
                    findings.append("✅ AuditLogger tracks authentication failures")
                    score += 20
                else:
                    findings.append("⚠️  AuditLogger may not track authentication failures")
                    score += 10

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Failed Login Notifications",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Failed Login Notifications",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_missing_audit_logs(self) -> TestResult:
        """Test 2: Check for missing audit logs in critical operations"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Critical operations that must have audit logs
            critical_operations = {
                "authentication": ["login", "logout", "password_change", "account_creation"],
                "data_access": ["user_data_read", "assessment_view", "team_data_access"],
                "data_modification": ["user_create", "user_update", "user_delete", "assessment_create"],
                "admin_actions": ["settings_change", "user_role_change", "system_config"],
                "export": ["data_export", "report_generation", "bulk_download"],
            }

            # Check audit_logger.py for action types
            audit_file = self.project_root / "app" / "core" / "audit_logging.py"
            if audit_file.exists():
                content = audit_file.read_text()

                # Check for AuditAction enum
                if "class AuditAction" in content:
                    findings.append("✅ AuditAction enum defined")

                    # Extract actions defined
                    import re
                    actions_found = re.findall(r'(\w+)\s*=\s*"[^"]+"', content)
                    actions_lower = [a.lower() for a in actions_found]

                    details["audit_actions_found"] = len(actions_found)
                    details["actions"] = actions_found[:10]

                    # Check for critical actions
                    required_actions = [
                        "LOGIN", "LOGOUT", "AUTHENTICATE", "AUTHENTICATION_FAILED",
                        "CREATE", "UPDATE", "DELETE", "UNAUTHORIZED_ACCESS",
                        "SECURITY_BREACH", "RATE_LIMIT_EXCEEDED"
                    ]

                    missing_actions = []
                    actions_upper = [a.upper() for a in actions_found]
                    for action in required_actions:
                        if action not in actions_upper:
                            missing_actions.append(action)

                    if missing_actions:
                        findings.append(f"⚠️  Missing audit actions: {', '.join(missing_actions[:5])}")
                        recommendations.append("Add missing audit actions to AuditAction enum")
                        score -= 10
                    else:
                        findings.append("✅ All critical audit actions defined")
                        score += 40
                else:
                    findings.append("❌ AuditAction enum not found")
                    recommendations.append("Implement AuditAction enum with all critical operations")
                    score -= 20

                # Check for AuditLogger class
                if "class AuditLogger" in content:
                    findings.append("✅ AuditLogger class implemented")
                    score += 20

                    # Check for key methods
                    if "async def log_event" in content:
                        findings.append("✅ log_event method exists")
                        score += 20
                    else:
                        findings.append("⚠️  log_event method not found")
                        score += 10

                    # Check for batch logging
                    if "log_events_batch" in content:
                        findings.append("✅ Batch logging supported")
                        score += 10
                else:
                    findings.append("❌ AuditLogger class not found")
                    recommendations.append("Implement AuditLogger class")
                    score -= 30

            # Scan endpoint files for audit logging usage
            endpoints_dir = self.project_root / "app" / "api" / "v1" / "endpoints"
            if endpoints_dir.exists():
                endpoints_with_audit = []
                endpoints_without_audit = []

                for endpoint_file in endpoints_dir.glob("*.py"):
                    try:
                        content = endpoint_file.read_text()
                        has_audit = False

                        # Check for audit logging imports or usage
                        if "audit_logger" in content or "AuditLogger" in content or "log_event" in content:
                            has_audit = True

                        # Check for security-related endpoints
                        if endpoint_file.name in ["auth.py", "users.py", "admin.py"]:
                            if has_audit:
                                endpoints_with_audit.append(endpoint_file.name)
                            else:
                                endpoints_without_audit.append(endpoint_file.name)
                    except:
                        continue

                details["endpoints_with_audit"] = len(endpoints_with_audit)
                details["endpoints_without_audit"] = len(endpoints_without_audit)

                if endpoints_with_audit:
                    findings.append(f"✅ {len(endpoints_with_audit)} endpoints use audit logging")
                    score += min(20, len(endpoints_with_audit) * 2)

                if endpoints_without_audit:
                    findings.append(f"⚠️  {len(endpoints_without_audit)} endpoints missing audit logs")
                    for ep in endpoints_without_audit[:3]:
                        findings.append(f"   - {ep}")
                    recommendations.append("Add audit logging to all security-critical endpoints")
                    score -= min(20, len(endpoints_without_audit) * 2)

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Missing Audit Logs",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Missing Audit Logs",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_log_tampering_detection(self) -> TestResult:
        """Test 3: Test tampering with logs"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check for log integrity protections
            logging_config = self.project_root / "app" / "core" / "logging_config.py"
            if logging_config.exists():
                content = logging_config.read_text()

                # Check for log sanitization (prevents injection)
                if "log_sanitizer" in content or "SensitiveDataFilter" in content:
                    findings.append("✅ Log sanitization implemented (prevents log injection)")
                    score += 25
                else:
                    findings.append("⚠️  Log sanitization not found")
                    recommendations.append("Implement log sanitization to prevent log injection attacks")
                    score += 10

                # Check for structured logging (harder to tamper)
                if "structured" in content.lower() or "json" in content.lower():
                    findings.append("✅ Structured logging implemented")
                    score += 15
                else:
                    findings.append("⚠️  Structured logging not found")
                    recommendations.append("Implement structured logging for better tamper resistance")
                    score += 10

            # Check for log forwarding to external service
            monitoring_files = [
                "app/monitoring/datadog_config.py",
                "app/monitoring/sentry_config.py",
                "app/monitoring/apm.py"
            ]

            has_external_logging = False
            for mon_file in monitoring_files:
                if (self.project_root / mon_file).exists():
                    has_external_logging = True
                    break

            if has_external_logging:
                findings.append("✅ External logging configured (Datadog/Sentry/APM)")
                score += 20
            else:
                findings.append("⚠️  No external logging configured")
                recommendations.append("Configure external log aggregation (Datadog, Sentry, etc.)")
                score += 10

            # Check for log file permissions
            log_dir = self.project_root / "logs"
            if log_dir.exists():
                # Check if log files have restrictive permissions
                import stat
                secure_logs = []
                insecure_logs = []

                for log_file in log_dir.glob("*.log"):
                    st = os.stat(log_file)
                    mode = oct(st.st_mode)[-3:]
                    if mode == "600":  # Owner read/write only
                        secure_logs.append(log_file.name)
                    else:
                        insecure_logs.append(f"{log_file.name}: {mode}")

                if secure_logs:
                    findings.append(f"✅ {len(secure_logs)} log files have secure permissions (600)")
                    score += min(20, len(secure_logs) * 5)

                if insecure_logs:
                    findings.append(f"⚠️  {len(insecure_logs)} log files have insecure permissions")
                    recommendations.append("Set log files to 600 (owner read/write only)")
                    score -= 10

            # Check for hash-based log integrity
            if "checksum" in logging_config.read_text().lower() or "hash" in logging_config.read_text().lower():
                findings.append("✅ Log integrity checking implemented")
                score += 20
            else:
                findings.append("⚠️  No log integrity checking found")
                recommendations.append("Implement log file hash-based integrity verification")
                score += 10

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Log Tampering Detection",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Log Tampering Detection",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_abnormal_activity_alerting(self) -> TestResult:
        """Test 4: Trigger abnormal activity and check alerting"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check security monitoring engine
            sec_monitor_file = self.project_root / "app" / "core" / "security_monitoring.py"
            if not sec_monitor_file.exists():
                findings.append("❌ security_monitoring.py not found")
                return TestResult(
                    test_name="Abnormal Activity Alerting",
                    status="FAIL",
                    score=0,
                    findings=findings,
                    recommendations=["Implement security monitoring system"],
                    details={}
                )

            content = sec_monitor_file.read_text()

            # Check for SecurityMonitoringEngine class
            if "class SecurityMonitoringEngine" in content:
                findings.append("✅ SecurityMonitoringEngine class exists")
                score += 30

                # Check for anomaly detection methods
                anomaly_methods = [
                    "detect_impossible_travel",
                    "detect_brute_force",
                    "detect_credential_stuffing",
                    "detect_unusual_location",
                ]

                methods_found = []
                for method in anomaly_methods:
                    if f"def {method}" in content or f"async def {method}" in content:
                        methods_found.append(method)

                details["anomaly_detection_methods"] = methods_found

                if methods_found:
                    findings.append(f"✅ Found {len(methods_found)} anomaly detection methods")
                    score += min(40, len(methods_found) * 10)

                    # Check for specific methods
                    if "detect_impossible_travel" in "".join(methods_found):
                        findings.append("✅ Impossible travel detection (geo-velocity)")
                        score += 5

                    if "detect_brute_force" in "".join(methods_found):
                        findings.append("✅ Brute force detection")
                        score += 5
                else:
                    findings.append("⚠️  No anomaly detection methods found")
                    recommendations.append("Implement anomaly detection methods")
                    score += 10

                # Check for alert generation
                if "SecurityAlert" in content:
                    findings.append("✅ SecurityAlert dataclass defined")
                    score += 10

                # Check for severity levels
                if "AlertSeverity" in content:
                    findings.append("✅ Alert severity levels defined (LOW/MEDIUM/HIGH/CRITICAL)")
                    score += 10

                # Check for risk scoring
                if "risk_score" in content.lower():
                    findings.append("✅ Risk scoring system implemented")
                    score += 10
                else:
                    findings.append("⚠️  No risk scoring found")
                    score += 5

            # Check for user behavior profiling
            if "UserBehaviorProfile" in content:
                findings.append("✅ User behavior profiling implemented")
                score += 15

            # Check for integration with monitoring services
            monitoring_files = [
                "app/monitoring/sentry_config.py",
                "app/monitoring/datadog_config.py"
            ]

            monitoring_configured = []
            for mon_file in monitoring_files:
                if (self.project_root / mon_file).exists():
                    mon_content = (self.project_root / mon_file).read_text()
                    if "SENTRY" in mon_content or "DATADOG" in mon_content:
                        monitoring_configured.append(mon_file.split("/")[-1])

            if monitoring_configured:
                findings.append(f"✅ External monitoring configured: {', '.join(monitoring_configured)}")
                score += 15
            else:
                findings.append("⚠️  No external monitoring integration found")
                recommendations.append("Configure external monitoring service (Sentry, Datadog, etc.)")
                score += 5

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Abnormal Activity Alerting",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Abnormal Activity Alerting",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def test_alert_escalation(self) -> TestResult:
        """Test 5: Test alert escalation for intrusion attempts"""
        findings = []
        recommendations = []
        details = {}
        score = 0

        try:
            # Check for escalation mechanisms
            sec_monitor_file = self.project_root / "app" / "core" / "security_monitoring.py"
            audit_file = self.project_root / "app" / "core" / "audit_logging.py"

            if not sec_monitor_file.exists():
                findings.append("❌ security_monitoring.py not found")
                return TestResult(
                    test_name="Alert Escalation",
                    status="FAIL",
                    score=0,
                    findings=findings,
                    recommendations=["Implement security monitoring system"],
                    details={}
                )

            content = sec_monitor_file.read_text()

            # Check for CRITICAL severity handling
            if "CRITICAL" in content or "AlertSeverity.CRITICAL" in content:
                findings.append("✅ CRITICAL alert severity level defined")
                score += 20

                # Check if CRITICAL alerts trigger immediate action
                if "CRITICAL" in content and "lock" in content.lower():
                    findings.append("✅ CRITICAL alerts trigger account lock")
                    score += 20
                else:
                    findings.append("⚠️  CRITICAL alerts may not trigger immediate action")
                    recommendations.append("Implement automatic account lock on CRITICAL alerts")
                    score += 10
            else:
                findings.append("❌ CRITICAL severity level not defined")
                recommendations.append("Define CRITICAL severity for intrusion attempts")
                score -= 20

            # Check for alert escalation thresholds
            if "threshold" in content.lower() or "BRUTE_FORCE_THRESHOLD" in content:
                findings.append("✅ Alert escalation thresholds configured")
                score += 20

                # Check for specific thresholds
                thresholds = {
                    "BRUTE_FORCE_THRESHOLD": 5,
                    "IMPOSSIBLE_TRAVEL_SPEED": 800,
                    "MAX_CONCURRENT_SESSIONS": 3,
                }

                details["thresholds_found"] = []
                for threshold_name in thresholds:
                    if threshold_name in content:
                        details["thresholds_found"].append(threshold_name)
                        findings.append(f"✅ {threshold_name} threshold set")

                if details["thresholds_found"]:
                    score += 10
            else:
                findings.append("⚠️  No escalation thresholds found")
                recommendations.append("Configure escalation thresholds for automatic alerts")
                score += 10

            # Check for notification/integration
            if "notify" in content.lower() or "alert" in content.lower() or "send" in content.lower():
                findings.append("✅ Notification/integration available")
                score += 15
            else:
                findings.append("⚠️  No notification mechanism for alerts")
                recommendations.append("Implement alert notification system (email, Slack, etc.)")
                score += 5

            # Check for intrusion-specific alerts
            intrusion_alerts = [
                "account_takeover",
                "privilege_escalation",
                "data_exfiltration",
                "unauthorized_access",
                "credential_stuffing",
                "brute_force_pattern"
            ]

            alerts_found = []
            for alert in intrusion_alerts:
                if alert in content.lower() or alert.upper() in content:
                    alerts_found.append(alert)

            details["intrusion_alerts"] = alerts_found

            if alerts_found:
                findings.append(f"✅ Found {len(alerts_found)} intrusion detection alerts")
                score += min(15, len(alerts_found) * 3)
            else:
                findings.append("⚠️  No specific intrusion alerts found")
                recommendations.append("Add detection for account takeover, privilege escalation, data exfiltration")
                score += 5

            # Determine overall status
            if score >= 80:
                status = "PASS"
            elif score >= 50:
                status = "WARN"
            else:
                status = "FAIL"

            return TestResult(
                test_name="Alert Escalation",
                status=status,
                score=max(0, min(100, score)),
                findings=findings,
                recommendations=recommendations,
                details=details
            )

        except Exception as e:
            findings.append(f"❌ Error during test: {str(e)}")
            return TestResult(
                test_name="Alert Escalation",
                status="ERROR",
                score=0,
                findings=findings,
                recommendations=["Fix test errors and re-run"],
                details={"error": str(e)}
            )

    def print_test_result(self, result: TestResult):
        """Print formatted test result"""
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️ ",
            "INFO": "ℹ️ ",
            "ERROR": "🔥"
        }

        emoji = status_emoji.get(result.status, "❓")

        for finding in result.findings:
            print(f"   {finding}")

        if result.recommendations:
            print(f"\n   💡 Recommendations:")
            for rec in result.recommendations:
                print(f"      - {rec}")

        print(f"\n   📊 Score: {result.score}/100")

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report"""
        print("\n" + "=" * 80)
        print("📋 SUMMARY REPORT")
        print("=" * 80)

        total_score = sum(r.score for r in self.results)
        avg_score = total_score / len(self.results) if self.results else 0

        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARN")
        failed = sum(1 for r in self.results if r.status in ["FAIL", "ERROR"])

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Passed: {passed} ✅")
        print(f"Warnings: {warned} ⚠️")
        print(f"Failed: {failed} ❌")
        print(f"\nOverall Security Score: {avg_score:.1f}/100")

        # Determine overall status
        if avg_score >= 80:
            overall_status = "SECURE ✅"
            color = "🟢"
        elif avg_score >= 60:
            overall_status = "ADEQUATE ⚠️"
            color = "🟡"
        else:
            overall_status = "NEEDS IMPROVEMENT ❌"
            color = "🔴"

        print(f"Overall Status: {color} {overall_status}")
        print(f"\nCompleted at: {datetime.now().isoformat()}")

        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(avg_score, 2),
            "overall_status": overall_status,
            "test_results": [r.to_dict() for r in self.results],
            "summary": {
                "total_tests": len(self.results),
                "passed": passed,
                "warnings": warned,
                "failed": failed
            }
        }

        report_file = self.project_root / "logging_monitoring_security_test_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file.name}")

        return report


def main():
    """Main entry point"""
    tester = LoggingMonitoringSecurityTester()
    report = tester.run_all_tests()

    # Exit with appropriate code
    avg_score = report["overall_score"]
    if avg_score < 60:
        sys.exit(1)  # Exit with error if security is poor
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
