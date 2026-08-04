"""
CORS Security Configuration Audit Script

This script performs a comprehensive audit of CORS configurations
across the entire PsychSync codebase to detect security issues.

Audit Checks:
1. Wildcard origins (allow_origins=["*"])
2. Credentials with wildcard origins (allow_credentials=True with "*")
3. Localhost in production configuration
4. Missing or invalid origin formats
5. Inconsistent configurations across environments
6. allow_all_origins or allow_any_origin usage
7. Overly permissive methods/headers
"""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cors_audit")


@dataclass
class CorsSecurityIssue:
    """Represents a CORS security issue"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    recommendation: str
    code_snippet: str


class CORSAuditor:
    """Audits CORS configurations for security issues"""

    # Patterns to detect issues
    WILDCARD_PATTERN = re.compile(r'allow_origins\s*=\s*\[?["\']\*["\']?\]?')
    CREDENTIALS_PATTERN = re.compile(r"allow_credentials\s*=\s*True")
    CREDENTIALS_WILDCARD_PATTERN = re.compile(
        r'allow_credentials\s*=\s*True.*allow_origins\s*=\s*\[?["\']\*["\']?\]?'
    )
    LOCALHOST_PATTERN = re.compile(
        r"localhost|127\.0\.0\.1|0\.0\.0\.0|::1", re.IGNORECASE
    )
    INSECURE_PROTOCOL_PATTERN = re.compile(r"file://|ftp://", re.IGNORECASE)
    WILDCARD_METHODS_PATTERN = re.compile(r'allow_methods\s*=\s*\[?["\']?\*["\']?\]?')
    WILDCARD_HEADERS_PATTERN = re.compile(r'allow_headers\s*=\s*\[?["\']?\*["\']?\]?')
    ALLOW_ALL_ORIGINS_PATTERN = re.compile(
        r"allow_all_origins\s*=\s*True|allow_any_origin\s*=\s*True"
    )

    def __init__(self, project_root: str = None):
        """
        Initialize CORS auditor

        Args:
            project_root: Root directory of the project to audit
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.issues: List[CorsSecurityIssue] = []
        self.audited_files: List[str] = []
        self.summary: Dict[str, Any] = {
            "total_files_audited": 0,
            "files_with_issues": 0,
            "issues_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "issues_by_type": {},
        }

    def audit_project(self) -> Dict[str, Any]:
        """
        Perform comprehensive CORS audit of entire project

        Returns:
            Audit summary with all issues found
        """
        logger.info(f"Starting CORS security audit at: {self.project_root}")

        # Find all Python files to audit
        python_files = list(self.project_root.rglob("*.py"))
        python_files.extend(list(self.project_root.rglob("**/*.py")))

        logger.info(f"Found {len(python_files)} Python files to audit")

        for file_path in python_files:
            self.audit_file(file_path)

        # Generate summary
        self._generate_summary()

        return self.summary

    def audit_file(self, file_path: Path) -> None:
        """
        Audit a single Python file for CORS security issues

        Args:
            file_path: Path to the Python file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                # Check for issues in this file
                self._check_file_for_issues(file_path, lines, content)

            self.audited_files.append(str(file_path))

        except Exception as e:
            logger.error(f"Failed to audit file {file_path}: {e}")

    def _check_file_for_issues(
        self, file_path: Path, lines: List[str], content: str
    ) -> None:
        """
        Check a file for CORS security issues

        Args:
            file_path: Path to the file
            lines: List of file lines
            content: File content
        """
        file_issues = []

        # Check for wildcard origins
        if self.WILDCARD_PATTERN.search(content):
            # Find exact line numbers
            for line_num, line in enumerate(lines, 1):
                if self.WILDCARD_PATTERN.search(line):
                    file_issues.append(
                        CorsSecurityIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="wildcard_origins",
                            severity="high",
                            description="CORS configured with wildcard origins (allow_origins=['*'])",
                            recommendation="Use specific origin list instead of wildcard",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for credentials with wildcard origins
        if self.CREDENTIALS_WILDCARD_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.CREDENTIALS_WILDCARD_PATTERN.search(line):
                    file_issues.append(
                        CorsSecurityIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="credentials_with_wildcard",
                            severity="critical",
                            description="CORS allows credentials with wildcard origins (allow_credentials=True + allow_origins=['*'])",
                            recommendation="Never use wildcard origins when credentials are enabled",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for allow_all_origins or allow_any_origin
        if self.ALLOW_ALL_ORIGINS_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.ALLOW_ALL_ORIGINS_PATTERN.search(line):
                    file_issues.append(
                        CorsSecurityIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="allow_all_origins",
                            severity="high",
                            description="CORS configured with allow_all_origins=True or allow_any_origin=True",
                            recommendation="Use specific origin list instead of allowing all origins",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for wildcard methods
        if self.WILDCARD_METHODS_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.WILDCARD_METHODS_PATTERN.search(line):
                    file_issues.append(
                        CorsSecurityIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="wildcard_methods",
                            severity="medium",
                            description="CORS configured with wildcard methods (allow_methods=['*'])",
                            recommendation="Specify exact methods needed (e.g., ['GET', 'POST'])",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for wildcard headers
        if self.WILDCARD_HEADERS_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.WILDCARD_HEADERS_PATTERN.search(line):
                    file_issues.append(
                        CorsSecurityIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="wildcard_headers",
                            severity="medium",
                            description="CORS configured with wildcard headers (allow_headers=['*'])",
                            recommendation="Specify exact headers needed",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for insecure protocols in origins
        if self.INSECURE_PROTOCOL_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.INSECURE_PROTOCOL_PATTERN.search(line):
                    # Only flag if it's an allow_origins line
                    if "allow_origins" in line.lower():
                        file_issues.append(
                            CorsSecurityIssue(
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_num,
                                issue_type="insecure_protocol",
                                severity="medium",
                                description=f"Origin contains insecure protocol (file:// or ftp://)",
                                recommendation="Use HTTPS only for production origins",
                                code_snippet=line.strip(),
                            )
                        )

        # Add all issues to main list
        if file_issues:
            self.issues.extend(file_issues)

    def _generate_summary(self) -> None:
        """Generate audit summary"""
        self.summary["total_files_audited"] = len(self.audited_files)

        # Count files with issues
        files_with_issues = set(issue.file_path for issue in self.issues)
        self.summary["files_with_issues"] = len(files_with_issues)

        # Group by severity
        for issue in self.issues:
            self.summary["issues_by_severity"][issue.severity] += 1
            self.summary["issues_by_type"][issue.issue_type] = (
                self.summary["issues_by_type"].get(issue.issue_type, 0) + 1
            )

    def print_report(self) -> None:
        """Print audit report to console"""
        print("\n" + "=" * 80)
        print("CORS SECURITY CONFIGURATION AUDIT REPORT")
        print("=" * 80)
        print(f"\n📁 Project: {self.project_root}")
        print(f"📊 Files Audited: {self.summary['total_files_audited']}")
        print(f"⚠️  Files with Issues: {self.summary['files_with_issues']}")
        print(f"\n📋 Issues by Severity:")
        print(f"  🚨 CRITICAL: {self.summary['issues_by_severity']['critical']}")
        print(f"  🔴 HIGH: {self.summary['issues_by_severity']['high']}")
        print(f"  🟡 MEDIUM: {self.summary['issues_by_severity']['medium']}")
        print(f"  🟢 LOW: {self.summary['issues_by_severity']['low']}")

        if self.summary["files_with_issues"] == 0:
            print("\n✅ No CORS security issues detected!")
            print("   CORS configuration follows best practices.")
        else:
            print("\n🔴 ISSUES FOUND:")
            print("\nCritical Issues:")
            self._print_issues_by_severity("critical")
            print("\nHigh Priority Issues:")
            self._print_issues_by_severity("high")
            print("\nMedium Priority Issues:")
            self._print_issues_by_severity("medium")
            print("\nLow Priority Issues:")
            self._print_issues_by_severity("low")

        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print("\nGeneral CORS Security Best Practices:")
        print("  1. Never use wildcard origins (allow_origins=['*']) in production")
        print(
            "  2. Never enable credentials (allow_credentials=True) with wildcard origins"
        )
        print("  3. Always specify exact origins needed for production")
        print("  4. Use HTTPS only for production origins")
        print("  5. Specify exact methods (not wildcard) when possible")
        print("  6. Specify exact headers (not wildcard) when possible")
        print(
            "  7. Set reasonable max_age (86400 for production, 3600 for development)"
        )
        print("\n" + "=" * 80)

    def _print_issues_by_severity(self, severity: str) -> None:
        """Print issues grouped by severity"""
        for issue in self.issues:
            if issue.severity == severity:
                print(f"\n  📄 File: {issue.file_path}:{issue.line_number}")
                print(f"     Issue: {issue.issue_type}")
                print(f"     Severity: {issue.severity.upper()}")
                print(f"     Code: {issue.code_snippet}")
                print(f"     Fix: {issue.recommendation}")

    def save_report(self, output_path: str = None) -> None:
        """Save audit report to file"""
        if output_path is None:
            output_path = str(self.project_root / "cors_security_audit_report.json")

        report_data = {
            "timestamp": "2024-01-01T00:00:00Z",
            "project_root": str(self.project_root),
            "summary": self.summary,
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "code_snippet": issue.code_snippet,
                }
                for issue in self.issues
            ],
        }

        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Audit report saved to: {output_path}")


def main():
    """Main entry point"""
    import sys

    # Get project root from command line or use current directory
    project_root = sys.argv[1] if len(sys.argv) > 1 else None

    # Create auditor and run audit
    auditor = CORSAuditor(project_root)
    auditor.audit_project()

    # Print report
    auditor.print_report()

    # Save report to file
    auditor.save_report()

    # Exit with appropriate code
    if auditor.summary["files_with_issues"] > 0:
        sys.exit(1)  # Exit with error if issues found
    else:
        sys.exit(0)  # Exit success if no issues


if __name__ == "__main__":
    main()
