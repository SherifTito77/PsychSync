#!/usr/bin/env python3
"""
Pre-Production Security Validation Script

This script runs comprehensive security checks before production deployment.
It aggregates findings from all security fix scripts and generates a go/no-go report.

Usage:
    # Run full validation
    python scripts/pre_production_validation.py

    # Generate detailed report
    python scripts/pre_production_validation.py --report > production_readiness.md

    # Check specific category
    python scripts/pre_production_validation.py --check console-logs,debug-bypass

    # Exit with non-zero if blockers found (for CI/CD)
    python scripts/pre_production_validation.py --strict
"""

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class ValidationCheck:
    """Represents a single validation check."""

    name: str
    category: str
    status: str = "PENDING"  # PASS, FAIL, WARN, PENDING
    message: str = ""
    details: List[str] = field(default_factory=list)
    is_blocker: bool = False

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "is_blocker": self.is_blocker,
        }


class PreProductionValidator:
    """Comprehensive pre-production security validation."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.checks: List[ValidationCheck] = []
        self.results = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "blockers": 0,
        }

    def add_check(self, check: ValidationCheck) -> None:
        """Add a validation check result."""
        self.checks.append(check)
        self.results["total_checks"] += 1

        if check.status == "PASS":
            self.results["passed"] += 1
        elif check.status == "FAIL":
            self.results["failed"] += 1
            if check.is_blocker:
                self.results["blockers"] += 1
        elif check.status == "WARN":
            self.results["warnings"] += 1

    # ==================== Console Log Checks ====================

    def check_console_logs(self) -> None:
        """Check for console.log statements in frontend code."""
        check = ValidationCheck(
            name="Console Log Removal",
            category="code_quality",
            is_blocker=False,  # Not a security blocker, but should be fixed
        )

        try:
            # Count console statements in TypeScript files
            frontend_path = self.root_path / "frontend" / "src"
            if not frontend_path.exists():
                check.status = "WARN"
                check.message = "Frontend directory not found"
                self.add_check(check)
                return

            console_count = 0
            files_with_consoles = []

            for ts_file in frontend_path.rglob("**/*.ts"):
                if "node_modules" in str(ts_file):
                    continue

                with open(ts_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    count = sum(
                        content.count(pattern)
                        for pattern in [
                            "console.log",
                            "console.debug",
                            "console.info",
                            "console.warn",
                            "console.error",
                        ]
                    )
                    if count > 0:
                        console_count += count
                        files_with_consoles.append(
                            (str(ts_file.relative_to(frontend_path)), count)
                        )

            if console_count == 0:
                check.status = "PASS"
                check.message = "No console statements found"
            else:
                check.status = "WARN"
                check.message = f"Found {console_count} console statements in {len(files_with_consoles)} files"
                check.details = [
                    f"Top files with console statements:",
                    *[
                        f"  - {file}: {count}"
                        for file, count in files_with_consoles[:10]
                    ],
                ]

        except Exception as e:
            check.status = "FAIL"
            check.message = f"Error checking console logs: {e}"

        self.add_check(check)

    # ==================== Debug Mode Bypass Checks ====================

    def check_debug_bypasses(self) -> None:
        """Check for debug mode security bypasses."""
        check = ValidationCheck(
            name="Debug Mode Security Bypasses",
            category="security",
            is_blocker=True,  # Security bypasses are blockers
        )

        try:
            # Import the bypass finder script
            script_path = self.root_path / "scripts" / "fix_debug_bypasses.py"

            if not script_path.exists():
                check.status = "WARN"
                check.message = "Debug bypass checker script not found"
                self.add_check(check)
                return

            # Run the script and capture output
            result = subprocess.run(
                [sys.executable, str(script_path), "--path", str(self.root_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # Parse output for bypass count
            if "Found 0 potential security bypasses" in output:
                check.status = "PASS"
                check.message = "No debug mode bypasses found"
            else:
                # Extract count from output
                match = re.search(r"Found (\d+) potential security bypasses", output)
                if match:
                    bypass_count = int(match.group(1))

                    if bypass_count == 0:
                        check.status = "PASS"
                        check.message = "No debug mode bypasses found"
                    else:
                        check.status = "FAIL"
                        check.message = (
                            f"Found {bypass_count} debug mode security bypasses"
                        )
                        check.is_blocker = True

                        # Extract CRITICAL and HIGH severity findings
                        critical_count = output.count("CRITICAL")
                        high_count = output.count("HIGH")

                        check.details = [
                            f"CRITICAL severity: {critical_count}",
                            f"HIGH severity: {high_count}",
                            "",
                            "Run for details:",
                            f"  python {script_path} --scan",
                        ]

        except subprocess.TimeoutExpired:
            check.status = "WARN"
            check.message = "Debug bypass check timed out"
        except Exception as e:
            check.status = "FAIL"
            check.message = f"Error checking debug bypasses: {e}"

        self.add_check(check)

    # ==================== Security TODO Checks ====================

    def check_security_todos(self) -> None:
        """Check for incomplete security TODOs."""
        check = ValidationCheck(
            name="Security TODOs",
            category="security",
            is_blocker=True,  # Critical security TODOs are blockers
        )

        try:
            script_path = self.root_path / "scripts" / "security_todo_tracker.py"

            if not script_path.exists():
                check.status = "WARN"
                check.message = "Security TODO tracker not found"
                self.add_check(check)
                return

            # Run the tracker
            result = subprocess.run(
                [sys.executable, str(script_path), "--path", str(self.root_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # Check for CRITICAL and HIGH TODOs
            critical_match = re.search(
                r"🔴 CRITICAL.*?\((\d+) items\)", output, re.DOTALL
            )
            high_match = re.search(r"🟠 HIGH.*?\((\d+) items\)", output, re.DOTALL)

            critical_count = int(critical_match.group(1)) if critical_match else 0
            high_count = int(high_match.group(1)) if high_match else 0

            if critical_count == 0 and high_count == 0:
                check.status = "PASS"
                check.message = "No critical security TODOs remaining"
            else:
                check.status = "FAIL"
                check.message = f"Found {critical_count} CRITICAL and {high_count} HIGH priority security TODOs"
                check.is_blocker = True

                check.details = [
                    f"CRITICAL TODOs: {critical_count}",
                    f"HIGH TODOs: {high_count}",
                    "",
                    "View details:",
                    f"  python {script_path} --find",
                ]

        except subprocess.TimeoutExpired:
            check.status = "WARN"
            check.message = "Security TODO check timed out"
        except Exception as e:
            check.status = "FAIL"
            check.message = f"Error checking security TODOs: {e}"

        self.add_check(check)

    # ==================== Environment Configuration Checks ====================

    def check_environment_config(self) -> None:
        """Check environment configuration security."""
        check = ValidationCheck(
            name="Environment Configuration", category="config", is_blocker=True
        )

        issues = []

        # Check for .env files in git
        git_env = self.root_path / ".env"
        if git_env.exists():
            issues.append(
                ".env file exists in repository root (should be in .gitignore)"
            )

        # Check for hardcoded secrets
        config_files = [
            self.root_path / "app" / "core" / "config.py",
            self.root_path / "frontend" / ".env",
        ]

        for config_file in config_files:
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # Check for common secret patterns
                    secret_patterns = [
                        (r'password\s*=\s*["\'].+["\']', "Hardcoded password"),
                        (r'api_key\s*=\s*["\'].+["\']', "Hardcoded API key"),
                        (r'secret\s*=\s*["\'].+["\']', "Hardcoded secret"),
                        (r'token\s*=\s*["\'].+["\']', "Hardcoded token"),
                    ]

                    for pattern, description in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(
                                f"{description} in {config_file.relative_to(self.root_path)}"
                            )

        if issues:
            check.status = "FAIL"
            check.message = f"Found {len(issues)} environment configuration issues"
            check.details = issues
            check.is_blocker = True
        else:
            check.status = "PASS"
            check.message = "Environment configuration looks secure"

        self.add_check(check)

    # ==================== CORS Configuration Checks ====================

    def check_cors_config(self) -> None:
        """Check CORS configuration."""
        check = ValidationCheck(
            name="CORS Configuration", category="security", is_blocker=True
        )

        try:
            # Check backend CORS config
            main_py = self.root_path / "app" / "main.py"

            if not main_py.exists():
                check.status = "WARN"
                check.message = "Could not find main.py to check CORS config"
                self.add_check(check)
                return

            with open(main_py, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for wildcard origins
            if re.search(r"allow_origins\s*=\s*\[?['\"]\*['\"]", content):
                check.status = "FAIL"
                check.message = "CORS allows all origins (*)"
                check.is_blocker = True
                check.details = [
                    "Wildcard CORS origins are unsafe in production",
                    "Use explicit allowed origins list instead",
                ]
            else:
                check.status = "PASS"
                check.message = "CORS configuration looks secure"

        except Exception as e:
            check.status = "FAIL"
            check.message = f"Error checking CORS config: {e}"

        self.add_check(check)

    # ==================== Performance Services Check ====================

    def check_performance_services(self) -> None:
        """Check if performance optimization services are enabled."""
        check = ValidationCheck(
            name="Performance Optimization Services",
            category="performance",
            is_blocker=False,
        )

        try:
            main_py = self.root_path / "app" / "main.py"

            if not main_py.exists():
                check.status = "WARN"
                check.message = "Could not find main.py"
                self.add_check(check)
                return

            with open(main_py, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if performance services are commented out
            if re.search(r"#.*performance.*service", content, re.IGNORECASE):
                check.status = "WARN"
                check.message = "Performance services may be disabled"
                check.details = [
                    "Performance optimization services appear to be commented out",
                    "Consider enabling for production",
                ]
            else:
                check.status = "PASS"
                check.message = "Performance services appear enabled"

        except Exception as e:
            check.status = "WARN"
            check.message = f"Error checking performance services: {e}"

        self.add_check(check)

    # ==================== Main Validation Run ====================

    def run_all_checks(self, categories: List[str] = None) -> None:
        """Run all validation checks."""
        print("🔍 Running Pre-Production Security Validation")
        print("=" * 80)
        print()

        all_checks = [
            ("console_logs", self.check_console_logs),
            ("debug_bypasses", self.check_debug_bypasses),
            ("security_todos", self.check_security_todos),
            ("environment", self.check_environment_config),
            ("cors", self.check_cors_config),
            ("performance", self.check_performance_services),
        ]

        # Filter by category if specified
        if categories:
            all_checks = [(cat, func) for cat, func in all_checks if cat in categories]

        for category, check_func in all_checks:
            print(f"Checking {category}...", end=" ")
            try:
                check_func()
                print("✅")
            except Exception as e:
                print(f"❌ Error: {e}")

        print()

    # ==================== Reporting ====================

    def print_results(self) -> None:
        """Print validation results."""
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print()

        for check in self.checks:
            emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "PENDING": "⏳"}.get(
                check.status, "❓"
            )

            blocker = " 🚫 BLOCKER" if check.is_blocker else ""
            print(f"{emoji} {check.name}{blocker}")
            print(f"   Status: {check.status}")
            print(f"   Message: {check.message}")

            if check.details:
                print("   Details:")
                for detail in check.details:
                    print(f"     {detail}")
            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Checks:    {self.results['total_checks']}")
        print(f"✅ Passed:        {self.results['passed']}")
        print(f"❌ Failed:        {self.results['failed']}")
        print(f"⚠️  Warnings:      {self.results['warnings']}")
        print(f"🚫 Blockers:      {self.results['blockers']}")
        print()

        # Go/No-Go decision
        if self.results["blockers"] > 0:
            print("🚫 NO-GO for production deployment")
            print(f"   {self.results['blockers']} critical blockers must be resolved")
        elif self.results["failed"] > 0:
            print("⚠️  CAUTION - Non-critical failures present")
            print("   Review failed checks before deploying")
        else:
            print("✅ GO for production deployment")
            print("   All critical checks passed")

    def generate_report(self) -> str:
        """Generate detailed markdown report."""
        lines = [
            "# Pre-Production Security Validation Report",
            f"\n**Generated:** {datetime.now().isoformat()}",
            f"**Status:** {'NO-GO' if self.results['blockers'] > 0 else 'GO'}",
            "\n## Executive Summary\n",
            f"- **Total Checks:** {self.results['total_checks']}",
            f"- **Passed:** {self.results['passed']}",
            f"- **Failed:** {self.results['failed']}",
            f"- **Warnings:** {self.results['warnings']}",
            f"- **Blockers:** {self.results['blockers']}",
            "\n## Validation Results\n",
        ]

        for check in self.checks:
            status_emoji = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARN": "⚠️",
            }.get(check.status, "❓")

            blocker_indicator = " 🚫 **BLOCKER**" if check.is_blocker else ""

            lines.extend(
                [
                    f"### {status_emoji} {check.name}{blocker_indicator}\n",
                    f"- **Status:** {check.status}",
                    f"- **Category:** {check.category}",
                    f"- **Message:** {check.message}",
                ]
            )

            if check.details:
                lines.append("- **Details:**")
                for detail in check.details:
                    lines.append(f"  - {detail}")

            lines.append("")

        # Recommendations
        lines.extend(
            [
                "## Recommendations\n",
            ]
        )

        if self.results["blockers"] > 0:
            lines.extend(
                [
                    "### 🚫 CRITICAL - Resolve Before Deployment\n",
                    "The following blockers must be resolved:\n",
                ]
            )

            for check in self.checks:
                if check.is_blocker and check.status == "FAIL":
                    lines.extend(
                        [
                            f"- **{check.name}:** {check.message}",
                        ]
                    )

        if self.results["warnings"] > 0:
            lines.extend(
                [
                    "\n### ⚠️  Recommended Actions\n",
                    "Consider addressing these warnings:\n",
                ]
            )

            for check in self.checks:
                if check.status == "WARN":
                    lines.extend(
                        [
                            f"- **{check.name}:** {check.message}",
                        ]
                    )

        lines.extend(
            [
                "\n## Next Steps\n",
                "1. Address all CRITICAL and HIGH priority security TODOs",
                "2. Remove or replace console.log statements with proper logging",
                "3. Remove debug mode security bypasses",
                "4. Verify environment configuration is secure",
                "5. Re-run validation: `python scripts/pre_production_validation.py`",
                "",
                "## Automated Checks\n",
                "- Console logs: `python scripts/remove_console_logs.py --dry-run`",
                "- Debug bypasses: `python scripts/fix_debug_bypasses.py --scan`",
                "- Security TODOs: `python scripts/security_todo_tracker.py --find`",
                "",
            ]
        )

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Pre-production security validation")
    parser.add_argument(
        "--path", default=".", help="Path to validate (default: current directory)"
    )
    parser.add_argument("--check", help="Comma-separated list of categories to check")
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed markdown report"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if blockers found",
    )

    args = parser.parse_args()

    validator = PreProductionValidator(args.path)

    categories = args.check.split(",") if args.check else None
    validator.run_all_checks(categories)

    if args.report:
        report = validator.generate_report()
        print(report)
    else:
        validator.print_results()

    # Exit code for CI/CD
    if args.strict and validator.results["blockers"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
