#!/usr/bin/env python3
"""
Debug Mode Bypass Detection and Fix Script

This script finds security controls that are bypassed in debug/development mode
and provides suggestions for fixing them.

Usage:
    # Scan for bypasses
    python scripts/fix_debug_bypasses.py --scan

    # Generate detailed report
    python scripts/fix_debug_bypasses.py --report > bypass_report.md

    # Apply automatic fixes where safe
    python scripts/fix_debug_bypasses.py --fix --dry-run
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class DebugBypassFinder:
    """Finds security controls bypassed by debug mode checks."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.findings = {
            "rate_limit_bypasses": [],
            "auth_bypasses": [],
            "cors_bypasses": [],
            "validation_bypasses": [],
            "ssl_bypasses": [],
            "logging_bypasses": [],
        }
        self.stats = {
            "files_scanned": 0,
            "total_bypasses": 0,
        }

    def find_python_files(self) -> List[Path]:
        """Find all Python files."""
        files = []
        for pattern in ["**/*.py"]:
            files.extend(self.root_path.rglob(pattern))

        ignored_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".pytest_cache",
            "dist",
            "build",
        }

        return [
            f
            for f in files
            if not any(ignored_dir in f.parts for ignored_dir in ignored_dirs)
        ]

    def find_typescript_files(self) -> List[Path]:
        """Find all TypeScript files."""
        files = []
        for pattern in ["**/*.ts", "**/*.tsx"]:
            files.extend(self.root_path.rglob(pattern))

        ignored_dirs = {
            "node_modules",
            ".git",
            "dist",
            "build",
            ".next",
            "coverage",
            ".cache",
        }

        return [
            f
            for f in files
            if not any(ignored_dir in f.parts for ignored_dir in ignored_dirs)
        ]

    def check_rate_limit_bypass(self, content: str, file_path: Path) -> List[Dict]:
        """Check for rate limiting bypassed by debug mode."""
        findings = []

        # Pattern 1: if not debug: return (skip rate limit in debug)
        patterns = [
            (
                r"if\s+.*(?:debug|DEBUG|development|DEV)\s*:\s*return",
                "Rate limit completely bypassed in debug mode",
            ),
            (
                r"if\s+not\s+.*(?:debug|DEBUG)\s*:\s*.*(?:rate_limit|check_rate)",
                "Rate limit only checked when NOT in debug mode",
            ),
            (
                r"(?:rate_limit|check_rate)\(.*\)\s*if\s+.*(?:debug|DEBUG)",
                "Rate limit call conditional on debug mode",
            ),
        ]

        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1]

                findings.append(
                    {
                        "line": line_num,
                        "pattern": pattern,
                        "description": description,
                        "code": line.strip(),
                        "severity": "HIGH",
                        "file": str(file_path.relative_to(self.root_path)),
                    }
                )

        return findings

    def check_auth_bypass(self, content: str, file_path: Path) -> List[Dict]:
        """Check for authentication bypassed by debug mode."""
        findings = []

        patterns = [
            (
                r"if\s+.*(?:debug|DEBUG)\s*:\s*return\s+.*(?:True|None|skip)",
                "Authentication check skipped in debug mode",
            ),
            (
                r"if\s+not\s+.*(?:debug|DEBUG)\s*:\s*.*(?:authenticate|verify.*token|check.*auth)",
                "Authentication only checked when NOT in debug mode",
            ),
            (
                r"@.*(?:skip_auth|bypass_auth|no_auth)",
                "Decorator bypasses authentication (possibly debug-only)",
            ),
        ]

        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1]

                findings.append(
                    {
                        "line": line_num,
                        "pattern": pattern,
                        "description": description,
                        "code": line.strip(),
                        "severity": "CRITICAL",
                        "file": str(file_path.relative_to(self.root_path)),
                    }
                )

        return findings

    def check_cors_bypass(self, content: str, file_path: Path) -> List[Dict]:
        """Check for CORS configurations that are unsafe in debug mode."""
        findings = []

        patterns = [
            (r"allow_origins\s*=\s*\[?['\"]\*['\"]\]?", "CORS allows all origins (*)"),
            (
                r"if\s+.*(?:debug|DEBUG)\s*:\s*.*allow_origins.*\*",
                "CORS allows all origins in debug mode",
            ),
            (
                r"allow_credentials\s*=\s*True.*allow_origins.*\*",
                "CORS credentials allowed with all origins (unsafe)",
            ),
        ]

        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1]

                findings.append(
                    {
                        "line": line_num,
                        "pattern": pattern,
                        "description": description,
                        "code": line.strip(),
                        "severity": "MEDIUM",
                        "file": str(file_path.relative_to(self.root_path)),
                    }
                )

        return findings

    def check_validation_bypass(self, content: str, file_path: Path) -> List[Dict]:
        """Check for validation bypassed by debug mode."""
        findings = []

        patterns = [
            (
                r"if\s+not\s+.*(?:debug|DEBUG|test)\s*:\s*.*(?:validate|verify|check)",
                "Validation only runs when NOT in debug/test mode",
            ),
            (
                r"if\s+.*(?:debug|DEBUG)\s*:\s*.*(?:skip.*val|no.*val)",
                "Validation explicitly skipped in debug mode",
            ),
        ]

        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1]

                findings.append(
                    {
                        "line": line_num,
                        "pattern": pattern,
                        "description": description,
                        "code": line.strip(),
                        "severity": "MEDIUM",
                        "file": str(file_path.relative_to(self.root_path)),
                    }
                )

        return findings

    def check_ssl_bypass(self, content: str, file_path: Path) -> List[Dict]:
        """Check for SSL verification bypassed by debug mode."""
        findings = []

        patterns = [
            (r"verify\s*=\s*False", "SSL verification disabled"),
            (r"ssl_verify\s*=\s*False", "SSL verification disabled"),
            (
                r"if\s+.*(?:debug|DEBUG)\s*:\s*.*verify\s*=\s*False",
                "SSL verification disabled in debug mode",
            ),
        ]

        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1]

                findings.append(
                    {
                        "line": line_num,
                        "pattern": pattern,
                        "description": description,
                        "code": line.strip(),
                        "severity": "HIGH",
                        "file": str(file_path.relative_to(self.root_path)),
                    }
                )

        return findings

    def scan_file(self, file_path: Path) -> Dict:
        """Scan a single file for debug bypasses."""
        result = {"file": str(file_path.relative_to(self.root_path)), "findings": []}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.stats["files_scanned"] += 1

            # Run all checks
            checks = [
                ("rate_limit_bypasses", self.check_rate_limit_bypass),
                ("auth_bypasses", self.check_auth_bypass),
                ("cors_bypasses", self.check_cors_bypass),
                ("validation_bypasses", self.check_validation_bypass),
                ("ssl_bypasses", self.check_ssl_bypass),
            ]

            for category, check_func in checks:
                findings = check_func(content, file_path)
                if findings:
                    self.findings[category].extend(findings)
                    result["findings"].extend(findings)
                    self.stats["total_bypasses"] += len(findings)

        except Exception as e:
            result["error"] = str(e)

        return result

    def scan(self) -> List[Dict]:
        """Scan all files for debug bypasses."""
        print("🔍 Scanning for debug mode security bypasses...\n")

        # Scan Python files
        print("Scanning Python files...")
        python_files = self.find_python_files()
        for file_path in python_files:
            self.scan_file(file_path)

        # Scan TypeScript files
        print("Scanning TypeScript files...")
        typescript_files = self.find_typescript_files()
        for file_path in typescript_files:
            self.scan_file(file_path)

        print(f"\n✅ Scanned {self.stats['files_scanned']} files")
        print(f"⚠️  Found {self.stats['total_bypasses']} potential security bypasses\n")

        return []

    def print_findings(self):
        """Print findings grouped by category."""
        if self.stats["total_bypasses"] == 0:
            print("✅ No debug mode bypasses found!")
            return

        for category, findings in self.findings.items():
            if not findings:
                continue

            category_name = category.replace("_", " ").title()
            print(f"\n{'='*80}")
            print(f"{category_name} ({len(findings)} found)")
            print("=" * 80)

            for finding in findings[:10]:  # Show first 10
                severity_emoji = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢",
                }.get(finding["severity"], "⚪")

                print(f"\n{severity_emoji} {finding['file']}:{finding['line']}")
                print(f"   Severity: {finding['severity']}")
                print(f"   Issue: {finding['description']}")
                print(f"   Code: {finding['code']}")

            if len(findings) > 10:
                print(f"\n... and {len(findings) - 10} more in this category")

    def generate_fix_suggestions(self, category: str) -> List[str]:
        """Generate fix suggestions for a category."""
        suggestions = {
            "rate_limit_bypasses": [
                "Remove debug mode checks from rate limiting logic",
                "Use a configurable rate limit that's higher in debug but still present",
                "Consider using environment-based rate limits instead of boolean debug flags",
            ],
            "auth_bypasses": [
                "NEVER skip authentication in debug mode",
                "Use test credentials or a test user instead",
                "Consider feature flags instead of debug checks for auth testing",
            ],
            "cors_bypasses": [
                "Use explicit allowed origins list",
                "For debug, use localhost with port, not wildcard",
                "Never use wildcard origins with credentials enabled",
            ],
            "validation_bypasses": [
                "Keep validation in all environments",
                "Use test data that passes validation",
                "Consider a separate 'fast validation' mode for testing",
            ],
            "ssl_bypasses": [
                "Never disable SSL verification, even in debug",
                "Use a proper SSL certificate for local development",
                "Configure local CA certs instead of disabling verification",
            ],
            "validation_bypasses": [
                "Keep validation in all environments",
                "Use mock/test data that passes validation",
                "Consider a 'strict' mode instead of a 'debug' mode",
            ],
        }

        return suggestions.get(category, [])

    def generate_report(self):
        """Generate a detailed markdown report."""
        report = [
            "# Debug Mode Security Bypass Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"\n## Summary",
            f"\n- Files scanned: {self.stats['files_scanned']}",
            f"- Total bypasses found: {self.stats['total_bypasses']}",
            "\n## Findings by Category\n",
        ]

        for category, findings in self.findings.items():
            if not findings:
                continue

            category_name = category.replace("_", " ").title()
            report.append(f"### {category_name} ({len(findings)} found)\n")

            for finding in findings:
                report.append(f"#### {finding['file']}:{finding['line']}")
                report.append(f"- **Severity:** {finding['severity']}")
                report.append(f"- **Issue:** {finding['description']}")
                report.append(f"- **Code:** `{finding['code']}`")
                report.append("")

            # Add fix suggestions
            suggestions = self.generate_fix_suggestions(category)
            if suggestions:
                report.append("**Suggested Fixes:**")
                for suggestion in suggestions:
                    report.append(f"- {suggestion}")
                report.append("")

        # Add general recommendations
        report.extend(
            [
                "## General Recommendations\n",
                "1. **Remove Debug Mode from Security-Critical Code**",
                "   Security controls (auth, rate limiting, SSL, validation) should never be",
                "   disabled based on debug mode. Use proper testing infrastructure instead.",
                "",
                "2. **Use Feature Flags**",
                "   Replace debug mode checks with explicit feature flags that can be",
                "   configured per environment and audited.",
                "",
                "3. **Environment-Based Configuration**",
                "   Use environment variables to configure security parameters, not",
                "   boolean debug flags that enable/disable entire controls.",
                "",
                "4. **Test with Real Security**",
                "   Integration tests should run with real security controls enabled.",
                "   Use test credentials and proper SSL certificates.",
                "",
                "## Next Steps\n",
                "1. Review all CRITICAL and HIGH severity findings",
                "2. Fix security bypasses before deploying to production",
                "3. Add tests to prevent reintroduction of debug bypasses",
                "4. Document secure development practices for the team",
                "",
            ]
        )

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Find and fix debug mode security bypasses"
    )
    parser.add_argument(
        "--path", default=".", help="Path to scan (default: current directory)"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Scan for bypasses and print findings"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed markdown report"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Apply automatic fixes (where safe)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )

    args = parser.parse_args()

    if not any([args.scan, args.report, args.fix]):
        args.scan = True  # Default to scanning

    finder = DebugBypassFinder(args.path)
    finder.scan()

    if args.scan:
        finder.print_findings()

    if args.report:
        report = finder.generate_report()
        print(report)

    if args.fix:
        print("\n⚠️  Automatic fixes not yet implemented")
        print("   Please review the findings and apply fixes manually")
        print("   See QUICK_FIX_GUIDE.md for detailed fix patterns")


if __name__ == "__main__":
    main()
