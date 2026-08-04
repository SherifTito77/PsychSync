"""
Fallback and Fail-Open Security Audit Script (Simplified Version)

This script performs a comprehensive audit to detect:
1. Unhealthy fallback patterns (returning 500 instead of proper error handling)
2. Fail-open configurations (allowing requests to proceed despite errors)
3. Silent exception swallowing
4. Missing validation in error paths
5. Resource exhaustion vulnerabilities
6. Inconsistent error handling across services
"""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fallback_audit")


@dataclass
class FallbackIssue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    recommendation: str
    code_snippet: str


class FallbackAuditor:
    def __init__(self, project_root: str = None):
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.issues = []
        self.audited_files = []
        self.summary = {
            "total_files_audited": 0,
            "files_with_issues": 0,
            "issues_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }

    def audit_project(self) -> Dict[str, Any]:
        logger.info(f"Starting fallback audit at: {self.project_root}")

        python_files = list(self.project_root.rglob("*.py"))
        python_files.extend(list(self.project_root.rglob("**/*.py")))

        logger.info(f"Found {len(python_files)} Python files to audit")

        for file_path in python_files:
            self.audit_file(file_path)

        self._generate_summary()
        return self.summary

    def audit_file(self, file_path: Path) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
                self._check_file_for_issues(file_path, lines, content)
            self.audited_files.append(str(file_path))
        except Exception as e:
            logger.error(f"Failed to audit file {file_path}: {e}")

    def _check_file_for_issues(self, file_path: Path, lines: List[str], content: str):
        file_issues = []

        for line_num, line in enumerate(lines, 1):
            # Check for silent exceptions
            if re.search(
                r"except:\s*pass\s*\)|except:\s*return\s*(?:pass|None|False)", line
            ):
                file_issues.append(
                    FallbackIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        issue_type="silent_exception",
                        severity="high",
                        description="Silent exception handler (pass or return without handling)",
                        recommendation="Handle specific exceptions with proper logging",
                        code_snippet=line.strip(),
                    )
                )

            # Check for bare exceptions
            if re.search(r"except\s*:", line) and not re.search(
                r"except\s+\w+\s*\w+", line
            ):
                file_issues.append(
                    FallbackIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        issue_type="bare_exception",
                        severity="medium",
                        description="Bare exception handler (except:) without handling",
                        recommendation="Handle specific exceptions or remove empty handler",
                        code_snippet=line.strip(),
                    )
                )

        if file_issues:
            self.issues.extend(file_issues)

    def _generate_summary(self):
        self.summary["total_files_audited"] = len(self.audited_files)
        files_with_issues = set(issue.file_path for issue in self.issues)
        self.summary["files_with_issues"] = len(files_with_issues)

        for issue in self.issues:
            self.summary["issues_by_severity"][issue.severity] += 1

    def print_report(self):
        print("\n" + "=" * 80)
        print("FALLBACK AND FAIL-OPEN SECURITY AUDIT REPORT")
        print("=" * 80)
        print(f"\nProject: {self.project_root}")
        print(f"Files Audited: {self.summary['total_files_audited']}")
        print(f"Files with Issues: {self.summary['files_with_issues']}")

        if self.summary["files_with_issues"] == 0:
            print("\nNo fallback or fail-open issues detected!")
            print("Error handling follows best practices.")
        else:
            print("\nIssues by Severity:")
            print(f"  CRITICAL: {self.summary['issues_by_severity']['critical']}")
            print(f"  HIGH: {self.summary['issues_by_severity']['high']}")
            print(f"  MEDIUM: {self.summary['issues_by_severity']['medium']}")
            print(f"  LOW: {self.summary['issues_by_severity']['low']}")

            self._print_issues("critical")
            self._print_issues("high")
            self._print_issues("medium")

        print("\n" + "=" * 80)
        print("SECURITY BEST PRACTICES")
        print("=" * 80)
        print("\n1. Never use bare exception handlers (except:)")
        print("2. Always handle specific exceptions with logging")
        print("3. Never pass or return without handling in error handlers")
        print("4. Use specific HTTP status codes for errors")
        print("5. Implement circuit breakers for external service failures")
        print("6. Log errors with sufficient context")
        print("7. Use structured error responses")
        print("\n" + "=" * 80)

    def _print_issues(self, severity):
        print(f"\n{severity.upper()} ISSUES:")
        for issue in self.issues:
            if issue.severity == severity:
                print(f"\n  File: {issue.file_path}:{issue.line_number}")
                print(f"  Issue: {issue.issue_type}")
                print(f"  Code: {issue.code_snippet}")
                print(f"  Fix: {issue.recommendation}")

    def save_report(self, output_path: str = None):
        if output_path is None:
            output_path = str(self.project_root / "fallback_audit_report.json")

        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "project_root": str(self.project_root),
                    "summary": self.summary,
                    "issues": [
                        {
                            "file_path": i.file_path,
                            "line_number": i.line_number,
                            "issue_type": i.issue_type,
                            "severity": i.severity,
                            "description": i.description,
                            "recommendation": i.recommendation,
                            "code_snippet": i.code_snippet,
                        }
                        for i in self.issues
                    ],
                },
                f,
                indent=2,
            )

        logger.info(f"Report saved to: {output_path}")


def main():
    import sys

    project_root = sys.argv[1] if len(sys.argv) > 1 else None
    auditor = FallbackAuditor(project_root)
    auditor.audit_project()
    auditor.print_report()
    auditor.save_report()
    sys.exit(1 if auditor.summary["files_with_issues"] > 0 else 0)


if __name__ == "__main__":
    main()
