#!/usr/bin/env python3
"""
Production Readiness Verification Script

This script verifies that all components of the security monitoring system
are correctly installed and ready for production use.

Run this before deploying to production.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(title):
    """Print a section header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def print_success(message):
    """Print a success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    """Print an error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_warning(message):
    """Print a warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")


def print_info(message):
    """Print an info message"""
    print(f"{BLUE}ℹ {message}{RESET}")


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} NOT FOUND: {filepath}")
        return False


def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if os.path.isdir(dirpath):
        print_success(f"{description}: {dirpath}")
        return True
    else:
        print_error(f"{description} NOT FOUND: {dirpath}")
        return False


def check_file_content(filepath, required_strings, description):
    """Check if file contains required strings"""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        missing = []
        for required in required_strings:
            if required not in content:
                missing.append(required)

        if not missing:
            print_success(f"{description} contains all required elements")
            return True
        else:
            print_warning(f"{description} missing: {', '.join(missing)}")
            return False
    except Exception as e:
        print_error(f"Failed to check {description}: {e}")
        return False


def run_tests():
    """Run the test suite"""
    print_info("Running test suite...")
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/integration/test_security_metrics.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            # Count passed tests
            passed = result.stdout.count("PASSED")
            print_success(f"All tests passed ({passed} tests)")
            return True
        else:
            print_error("Some tests failed")
            print(result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print_error("Tests timed out")
        return False
    except Exception as e:
        print_error(f"Failed to run tests: {e}")
        return False


def verify_github_actions_workflows():
    """Verify GitHub Actions workflow files"""
    print_header("GitHub Actions Workflows")

    checks = []

    # Check workflow files
    workflows = [
        (".github/workflows/sast-semgrep.yml", "SAST Workflow"),
        (".github/workflows/dast-zap.yml", "DAST Workflow"),
        (".github/workflows/sca-trivy-snyk.yml", "SCA Workflow"),
    ]

    for filepath, description in workflows:
        checks.append(check_file_exists(filepath, description))

    # Check script files
    scripts = [
        (".github/scripts/zap-to-sarif.py", "ZAP to SARIF Converter"),
        (".github/scripts/merge-sboms.py", "SBOM Merger"),
    ]

    for filepath, description in scripts:
        checks.append(check_file_exists(filepath, description))

    # Verify workflow content
    sast_workflow = ".github/workflows/sast-semgrep.yml"
    if os.path.exists(sast_workflow):
        required = ["semgrep", "publish-sarif", "security-review-required"]
        checks.append(check_file_content(sast_workflow, required, "SAST Workflow"))

    return all(checks)


def verify_monitoring_system():
    """Verify monitoring system files"""
    print_header("Security Monitoring System")

    checks = []

    # Check monitoring modules
    modules = [
        ("app/monitoring/security_metrics.py", "Security Metrics Collector"),
        ("app/monitoring/prometheus_metrics.py", "Prometheus Exporter"),
        ("app/monitoring/README.md", "Monitoring Documentation"),
    ]

    for filepath, description in modules:
        checks.append(check_file_exists(filepath, description))

    # Verify key functions exist
    metrics_file = "app/monitoring/security_metrics.py"
    if os.path.exists(metrics_file):
        required = [
            "class SecurityMetricsCollector",
            "def collect_from_sast",
            "def collect_from_dast",
            "def collect_from_sca",
            "def calculate_security_score",
            "def get_compliance_status",
        ]
        checks.append(
            check_file_content(metrics_file, required, "Security Metrics Module")
        )

    # Check Prometheus exporter
    prometheus_file = "app/monitoring/prometheus_metrics.py"
    if os.path.exists(prometheus_file):
        required = ["generate_prometheus_metrics", "psychsync_security_score"]
        checks.append(
            check_file_content(prometheus_file, required, "Prometheus Exporter")
        )

    return all(checks)


def verify_api_endpoints():
    """Verify API endpoint implementation"""
    print_header("API Endpoints")

    monitoring_file = "app/api/v1/endpoints/monitoring.py"

    if not os.path.exists(monitoring_file):
        print_error("Monitoring endpoints file not found")
        return False

    # Check for security endpoints
    required_endpoints = [
        "get_security_overview",
        "get_security_vulnerabilities",
        "get_security_by_tool",
        "get_security_compliance",
        "get_security_score",
        "get_security_trend",
        "get_security_dashboard",
        "trigger_security_scan",
        "metrics_endpoint",
    ]

    with open(monitoring_file, "r") as f:
        content = f.read()

    checks = []
    for endpoint in required_endpoints:
        if endpoint in content:
            print_success(f"Endpoint: {endpoint}")
        else:
            print_error(f"Endpoint NOT FOUND: {endpoint}")
        checks.append(endpoint in content)

    return all(checks)


def verify_observability_integration():
    """Verify Prometheus and Grafana configuration"""
    print_header("Observability Integration")

    checks = []

    # Check Prometheus configuration
    prometheus_files = [
        ("deploy/prometheus/prometheus.yml", "Prometheus Configuration"),
        (
            "deploy/prometheus/alerts/psychsync_security_alerts.yml",
            "Prometheus Alert Rules",
        ),
    ]

    for filepath, description in prometheus_files:
        checks.append(check_file_exists(filepath, description))

    # Check Grafana dashboard
    grafana_dashboard = "deploy/grafana/dashboards/psychsync-security-dashboard.json"
    if os.path.exists(grafana_dashboard):
        with open(grafana_dashboard, "r") as f:
            dashboard = json.load(f)

        if "dashboard" in dashboard:
            print_success(
                f"Grafana Dashboard: {len(dashboard['dashboard'].get('panels', []))} panels"
            )
            checks.append(True)
        else:
            print_error("Invalid Grafana dashboard format")
            checks.append(False)
    else:
        print_error("Grafana dashboard not found")
        checks.append(False)

    return all(checks)


def verify_documentation():
    """Verify documentation files"""
    print_header("Documentation")

    docs = [
        ("docs/GITHUB_ACTIONS_SECURITY_SUMMARY.md", "GitHub Actions Guide"),
        ("docs/SECURITY_BADGES.md", "Security Badges Reference"),
        ("docs/MONITORING_QUICK_START.md", "Monitoring Quick Start"),
        ("docs/SECURITY_MONITORING_COMPLETE.md", "Implementation Summary"),
        ("app/monitoring/README.md", "Monitoring Module Documentation"),
    ]

    checks = []
    for filepath, description in docs:
        checks.append(check_file_exists(filepath, description))

    return all(checks)


def verify_tests():
    """Verify test implementation"""
    print_header("Test Suite")

    test_file = "tests/integration/test_security_metrics.py"

    if not os.path.exists(test_file):
        print_error("Test file not found")
        return False

    # Check for test classes
    with open(test_file, "r") as f:
        content = f.read()

    required_classes = [
        "class TestSecurityMetricsCollector",
        "class TestSecurityMetrics",
        "class TestComplianceChecking",
        "class TestPrometheusMetrics",
        "class TestConvenienceFunctions",
        "class TestEndToEndWorkflow",
    ]

    checks = []
    for test_class in required_classes:
        if test_class in content:
            print_success(f"Test class: {test_class}")
        else:
            print_error(f"Test class NOT FOUND: {test_class}")
        checks.append(test_class in content)

    # Run actual tests
    if all(checks):
        print_info("Running integration tests...")
        checks.append(run_tests())

    return all(checks)


def verify_demo_script():
    """Verify demo script works"""
    print_header("Demo Script")

    demo_script = "scripts/demo_security_monitoring.py"

    if not os.path.exists(demo_script):
        print_error("Demo script not found")
        return False

    print_info("Running demo script...")
    try:
        result = subprocess.run(
            ["python", demo_script], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print_success("Demo script executed successfully")
            return True
        else:
            print_error("Demo script failed")
            print(result.stderr[:500])  # Print first 500 chars of error
            return False
    except subprocess.TimeoutExpired:
        print_error("Demo script timed out")
        return False
    except Exception as e:
        print_error(f"Failed to run demo: {e}")
        return False


def main():
    """Run all verification checks"""
    print(f"\n{GREEN}{'='*70}{RESET}")
    print(f"{GREEN}PRODUCTION READINESS VERIFICATION{RESET}")
    print(f"{GREEN}PsychSync Security Monitoring System{RESET}")
    print(f"{GREEN}{'='*70}{RESET}")

    all_checks_passed = True

    # Run all verification checks
    all_checks_passed &= verify_github_actions_workflows()
    all_checks_passed &= verify_monitoring_system()
    all_checks_passed &= verify_api_endpoints()
    all_checks_passed &= verify_observability_integration()
    all_checks_passed &= verify_documentation()
    all_checks_passed &= verify_tests()
    all_checks_passed &= verify_demo_script()

    # Final summary
    print_header("VERIFICATION SUMMARY")

    if all_checks_passed:
        print(f"{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✓ ALL CHECKS PASSED{RESET}")
        print(f"{GREEN}System is production ready!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        return 0
    else:
        print(f"{RED}{'='*70}{RESET}")
        print(f"{RED}✗ SOME CHECKS FAILED{RESET}")
        print(f"{RED}Please review the errors above{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
