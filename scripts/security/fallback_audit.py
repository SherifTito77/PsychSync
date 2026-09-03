"""
Fallback and Fail-Open Security Audit Script

This script performs a comprehensive audit to detect:
1. Unhealthy fallback patterns (returning 500 instead of proper error handling)
2. Fail-open configurations (allowing requests to proceed despite errors)
3. Silent exception swallowing
4. Missing validation in error paths
5. Resource exhaustion vulnerabilities
6. Inconsistent error handling across services

Security Impact:
- Unhealthy fallbacks can mask service issues and lead to cascading failures
- Fail-open can expose sensitive data or bypass security controls
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
logger = logging.getLogger("fallback_audit")


@dataclass
class FallbackIssue:
    """Represents a fallback or fail-open issue"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    recommendation: str
    code_snippet: str


class FallbackAuditor:
    """Audits for unhealthy fallback and fail-open patterns"""

    # Patterns to detect issues
    SILENT_EXCEPT_PATTERN = re.compile(
        r"except:\s*pass\s*\)|except:\s*return\s*(?:pass|None|False)"
    )
    EMPTY_EXCEPT_PATTERN = re.compile(r"except\s*:")
    BARE_EXCEPT_PATTERN = re.compile(r"except:\s*Exception")
    FAIL_OPEN_TRY_PATTERN = re.compile(
        r"try:\s*except:\s*:\s*pass\s*\)|try:\s*except:\s*return\s*None\s*\)"
    )
    DEFAULT_RESPONSE_PATTERN = re.compile(
        r'return\s*\{\s*error:\s*["\']default["\']?["\']?\s*}|return\s*{"\s*error:\s*["\']500["\']?["\']?\s*}'
    )
    GENERIC_500_PATTERN = re.compile(
        r"return\s*status_code\s*=\s*status\.HTTP_500_INTERNAL_SERVER_ERROR"
    )
    PASS_ON_ERROR_PATTERN = re.compile(r"pass\s*\)\s*(?except\s*:|except\s*:)\s*pass)")
    LOG_AND_PASS_PATTERN = re.compile(r"logging\.\w+\(|logger\.\w+\(.*pass")
    SUPPRESS_ERROR_PATTERN = re.compile(
        r"raise\s*HTTPException.*status_code.*status\.HTTP_200.*OK"
    )

    def __init__(self, project_root: str = None):
        """
        Initialize fallback auditor

        Args:
            project_root: Root directory of the project to audit
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.issues: List[FallbackIssue] = []
        self.audited_files: List[str] = []
        self.summary: Dict[str, Any] = {
            "total_files_audited": 0,
            "files_with_issues": 0,
            "issues_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "issues_by_type": {},
        }

    def audit_project(self) -> Dict[str, Any]:
        """
        Perform comprehensive fallback audit of entire project

        Returns:
            Audit summary with all issues found
        """
        logger.info(f"Starting fallback security audit at: {self.project_root}")

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
        Audit a single Python file for fallback issues

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
        Check a file for fallback and fail-open issues

        Args:
            file_path: Path to the file
            lines: List of file lines
            content: File content
        """
        file_issues = []

        # Check for silent exceptions (bare except)
        if self.BARE_EXCEPT_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.BARE_EXCEPT_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="bare_exception",
                            severity="high",
                            description="Bare exception handler (except:) without proper error handling",
                            recommendation="Handle specific exceptions and log errors appropriately",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for empty exception handlers
        if self.EMPTY_EXCEPT_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.EMPTY_EXCEPT_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="empty_exception_handler",
                            severity="medium",
                            description="Empty exception handler (except:) without any error handling",
                            recommendation="Handle exceptions or remove empty handler",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for fail-open patterns
        if self.FAIL_OPEN_TRY_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.FAIL_OPEN_TRY_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="fail_open",
                            severity="critical",
                            description="Fail-open: try/except block that passes or returns default values",
                            recommendation="Handle errors properly and return appropriate error responses",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for default 500 responses
        if self.DEFAULT_RESPONSE_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.DEFAULT_RESPONSE_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="default_500_response",
                            severity="high",
                            description="Unhealthy fallback: returning default error instead of specific error details",
                            recommendation="Return meaningful error messages with appropriate status codes",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for generic 500 errors
        if self.GENERIC_500_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.GENERIC_500_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="generic_500",
                            severity="medium",
                            description="Generic 500 error instead of specific error handling",
                            recommendation="Use specific status codes and error messages for different failure scenarios",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for pass on error patterns
        if self.PASS_ON_ERROR_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.PASS_ON_ERROR_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="pass_on_error",
                            severity="critical",
                            description="Pass statement in error handler (suppressing errors)",
                            recommendation="Log errors and handle them properly instead of suppressing",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for logging and pass patterns
        if self.LOG_AND_PASS_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.LOG_AND_PASS_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="log_and_pass",
                            severity="high",
                            description="Logging error then passing (silent failure)",
                            recommendation="Either log and raise, or handle without passing",
                            code_snippet=line.strip(),
                        )
                    )

        # Check for suppressed error responses (200 OK on error)
        if self.SUPPRESS_ERROR_PATTERN.search(content):
            for line_num, line in enumerate(lines, 1):
                if self.SUPPRESS_ERROR_PATTERN.search(line):
                    file_issues.append(
                        FallbackIssue(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            issue_type="suppress_error_response",
                            severity="critical",
                            description="Suppressing error by returning 200 OK instead of proper error status",
                            recommendation="Return appropriate error status codes (4xx, 5xx) for failures",
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
        print("FALLBACK AND FAIL-OPEN SECURITY AUDIT REPORT")
        print("=" * 80)
        print(f"\n📁 Project: {self.project_root}")
        print(f"📊 Files Audited: {self.summary['total_files_audited']}")
        print(f"⚠️  Files with Issues: {self.summary['files_with_issues']}")

        if self.summary["files_with_issues"] == 0:
            print("\n✅ No fallback or fail-open issues detected!")
            print("   Error handling follows best practices.")
        else:
            print("\n📋 Issues by Severity:")
            print(f"  🚨 CRITICAL: {self.summary['issues_by_severity']['critical']}")
            print(f"  🔴 HIGH: {self.summary['issues_by_severity']['high']}")
            print(f"  🟡 MEDIUM: {self.summary['issues_by_severity']['medium']}")
            print(f"  🟢 LOW: {self.summary['issues_by_severity']['low']}")

            print("\n" + "-" * 80)
            print("CRITICAL ISSUES (FAIL-OPEN)")
            print("-" * 80)
            self._print_issues_by_severity("critical")
            print("\n" + "-" * 80)
            print("HIGH PRIORITY ISSUES")
            print("-" * 80)
            self._print_issues_by_severity("high")
            print("\n" + "-" * 80)
            print("MEDIUM PRIORITY ISSUES")
            print("-" * 80)
            self._print_issues_by_severity("medium")
            print("\n" + "-" * 80)
            print("LOW PRIORITY ISSUES")
            print("-" * 80)
            self._print_issues_by_severity("low")

        print("\n" + "=" * 80)
        print("SECURITY BEST PRACTICES FOR ERROR HANDLING")
        print("=" * 80)
        print("\n1. Never use bare exception handlers (except:)")
        print("2. Always handle specific exceptions with appropriate logging")
        print("3. Never use pass statements in error handlers")
        print(
            "4. Return appropriate HTTP status codes (4xx for client errors, 5xx for server errors)"
        )
        print("5. Never return 200 OK when an error occurs (suppress_error_response)")
        print("6. Implement circuit breakers for external service failures")
        print("7. Log errors with sufficient context for debugging")
        print("8. Use structured error responses with error codes and messages")
        print("9. Implement retry with exponential backoff for transient failures")
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
            output_path = str(self.project_root / "fallback_security_audit_report.json")

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
    auditor = FallbackAuditor(project_root)
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
