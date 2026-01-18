#!/usr/bin/env python3
"""
Systematically fix bare except: clauses in the codebase.

This script:
1. Finds all bare except: clauses
2. Analyzes context to suggest appropriate exception types
3. Categorizes by severity and file type
4. Generates a report before making changes
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BareExceptLocation:
    """Location of a bare except clause."""
    file_path: str
    line_number: int
    context_code: str
    suggested_fix: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'security', 'api', 'database', 'file_ops', 'test', 'other'


class BareExceptionAnalyzer(ast.NodeVisitor):
    """AST visitor to find bare except clauses."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[BareExceptLocation] = []
        self.source_lines: List[str] = []

    def analyze(self) -> List[BareExceptLocation]:
        """Analyze the file and return findings."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                self.source_lines = source.splitlines()
        except Exception:
            return []

        try:
            tree = ast.parse(source)
            self.visit(tree)
        except SyntaxError:
            # Skip files with syntax errors
            pass

        return self.findings

    def visit_Try(self, node: ast.Try):
        """Visit try statements and check for bare except."""
        for handler in node.handlers:
            if handler.type is None:  # Bare except
                finding = self._analyze_except_context(node, handler)
                if finding:
                    self.findings.append(finding)

        self.generic_visit(node)

    def _analyze_except_context(self, try_node: ast.Try, handler: ast.ExceptHandler) -> BareExceptLocation:
        """Analyze the context around a bare except to suggest appropriate fix."""
        line_num = handler.lineno

        # Get context code (3 lines before and after)
        start = max(0, line_num - 4)
        end = min(len(self.source_lines), line_num + 3)
        context = '\n'.join(self.source_lines[start:end])

        # Determine category and suggested fix based on context
        category, suggested_fix, severity = self._categorize_exception(try_node, handler, context)

        return BareExceptLocation(
            file_path=str(self.file_path),
            line_number=line_num,
            context_code=context,
            suggested_fix=suggested_fix,
            severity=severity,
            category=category
        )

    def _categorize_exception(self, try_node: ast.Try, handler: ast.ExceptHandler, context: str) -> Tuple[str, str, str]:
        """Categorize the exception and suggest appropriate fix."""

        # Look for common patterns in the try block
        try_code = ast.unparse(try_node) if hasattr(ast, 'unparse') else context.lower()

        # File operations
        if any(keyword in try_code.lower() for keyword in ['open(', 'zipfile.', 'gzip.', 'file.read', 'file.write']):
            return 'file_ops', 'except (OSError, IOError) as e:', 'medium'

        # Database operations
        if any(keyword in try_code.lower() for keyword in ['session.execute', 'session.query', 'db.execute', '.fetch', '.commit']):
            return 'database', 'except Exception as e:', 'high'

        # API/HTTP operations
        if any(keyword in try_code.lower() for keyword in ['requests.', 'httpx.', 'fetch(', 'response.', 'api.']):
            return 'api', 'except Exception as e:', 'high'

        # Security/crypto operations
        if any(keyword in try_code.lower() for keyword in ['encrypt', 'decrypt', 'hash.', 'crypto.', 'jwt.', 'password.']):
            return 'security', 'except Exception as e:', 'critical'

        # JSON operations
        if any(keyword in try_code.lower() for keyword in ['json.loads', 'json.dumps', 'json.parse']):
            return 'other', 'except (json.JSONDecodeError, TypeError) as e:', 'medium'

        # Test files - lower severity
        if 'test' in str(self.file_path).lower():
            return 'test', 'except Exception as e:', 'low'

        # Default to Exception
        return 'other', 'except Exception as e:', 'medium'


def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the directory."""
    python_files = []
    for path in root_dir.rglob('*.py'):
        # Skip virtual environments and build directories
        if 'venv' not in str(path) and '__pycache__' not in str(path):
            python_files.append(path)
    return python_files


def generate_report(findings: List[BareExceptLocation]) -> str:
    """Generate a comprehensive report."""
    report = ["# Bare Exception Handler Analysis Report\n"]
    report.append(f"**Total findings:** {len(findings)}\n")

    # Group by severity
    by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
    for finding in findings:
        by_severity[finding.severity].append(finding)

    report.append("\n## By Severity\n")
    for severity in ['critical', 'high', 'medium', 'low']:
        count = len(by_severity[severity])
        if count > 0:
            report.append(f"- **{severity.upper()}**: {count} occurrences")

    # Group by category
    by_category: Dict[str, List[BareExceptLocation]] = {}
    for finding in findings:
        if finding.category not in by_category:
            by_category[finding.category] = []
        by_category[finding.category].append(finding)

    report.append("\n## By Category\n")
    for category, items in sorted(by_category.items()):
        report.append(f"- **{category}**: {len(items)} occurrences")

    # Top critical files
    file_counts: Dict[str, int] = {}
    for finding in findings:
        file_counts[finding.file_path] = file_counts.get(finding.file_path, 0) + 1

    report.append("\n## Top Files With Most Issues\n")
    for file_path, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        report.append(f"- {file_path}: {count} issues")

    # Detailed findings for critical and high severity
    if by_severity['critical'] or by_severity['high']:
        report.append("\n## Critical & High Priority Details\n")
        for finding in by_severity['critical'] + by_severity['high']:
            report.append(f"\n### {finding.file_path}:{finding.line_number}")
            report.append(f"**Severity:** {finding.severity} | **Category:** {finding.category}")
            report.append(f"**Suggested fix:** `{finding.suggested_fix}`")
            report.append(f"```")
            report.append(finding.context_code)
            report.append(f"```")

    return '\n'.join(report)


def main():
    """Main entry point."""
    import sys

    root_dir = Path(__file__).parent.parent
    print(f"🔍 Analyzing Python files in {root_dir}...")

    python_files = find_python_files(root_dir)
    print(f"📁 Found {len(python_files)} Python files")

    all_findings: List[BareExceptLocation] = []

    for py_file in python_files:
        try:
            analyzer = BareExceptionAnalyzer(py_file)
            findings = analyzer.analyze()
            all_findings.extend(findings)
        except Exception as e:
            print(f"⚠️  Error analyzing {py_file}: {e}")

    # Generate and save report
    report = generate_report(all_findings)

    report_path = root_dir / "BARE_EXCEPTIONS_ANALYSIS.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Analysis complete!")
    print(f"📊 Found {len(all_findings)} bare exception handlers")
    print(f"📄 Report saved to: {report_path}")

    # Print summary
    print("\n📈 Summary:")
    by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for finding in all_findings:
        by_severity[finding.severity] += 1

    for severity, count in by_severity.items():
        if count > 0:
            print(f"   {severity.upper()}: {count}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
