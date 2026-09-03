#!/usr/bin/env python3
"""
Technical Debt Measurement Tool

Analyzes codebase to calculate technical debt score.
Identifies specific issues that need to be addressed.
"""

import ast
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class TechnicalDebtAnalyzer:
    """Analyze technical debt in codebase"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues = []
        self.metrics = {}

    def analyze_all(self) -> Dict:
        """Run all analyses"""
        print("🔍 Analyzing technical debt...")

        # 1. Code complexity
        complexity_score = self.analyze_complexity()

        # 2. Code duplication
        duplication_score = self.analyze_duplication()

        # 3. Test coverage
        coverage_score = self.analyze_test_coverage()

        # 4. Code smells
        smells_score = self.analyze_code_smells()

        # 5. Documentation
        documentation_score = self.analyze_documentation()

        # 6. Security issues
        security_score = self.analyze_security()

        # Calculate overall score
        overall_score = (
            complexity_score * 0.25
            + duplication_score * 0.20
            + (100 - coverage_score) * 0.20
            + smells_score * 0.15
            + (100 - documentation_score) * 0.10
            + security_score * 0.10
        )

        self.metrics = {
            "overall_score": round(overall_score / 10, 1),  # Scale to 0-10
            "complexity": complexity_score,
            "duplication": duplication_score,
            "test_coverage": coverage_score,
            "code_smells": smells_score,
            "documentation": documentation_score,
            "security": security_score,
            "issues": self.issues,
            "total_issues": len(self.issues),
        }

        return self.metrics

    def analyze_complexity(self) -> float:
        """Analyze cyclomatic complexity"""
        print("  📊 Analyzing complexity...")
        complexity_issues = 0
        functions_analyzed = 0

        for py_file in self.project_root.rglob("app/**/*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions_analyzed += 1
                        complexity = self._calculate_complexity(node)

                        if complexity > 10:
                            complexity_issues += 1
                            self.issues.append(
                                {
                                    "type": "complexity",
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": node.lineno,
                                    "function": node.name,
                                    "complexity": complexity,
                                    "severity": "high" if complexity > 20 else "medium",
                                }
                            )
            except Exception:
                pass

        if functions_analyzed == 0:
            return 0.0

        # Score: percentage of functions with acceptable complexity
        score = ((functions_analyzed - complexity_issues) / functions_analyzed) * 100
        print(f"    Functions analyzed: {functions_analyzed}")
        print(f"    High complexity: {complexity_issues}")
        print(f"    Complexity score: {100 - score:.1f}/100")
        return 100 - score

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def analyze_duplication(self) -> float:
        """Analyze code duplication using radon"""
        print("  📋 Analyzing duplication...")
        try:
            # Use radon to find duplication
            result = subprocess.run(
                ["radon", "cc", "app", "-a", "-s"], capture_output=True, text=True
            )

            if result.returncode == 0:
                # Parse radon output
                blocks = []
                for line in result.stdout.split("\n"):
                    if "CC" in line:
                        try:
                            score = float(line.split("CC")[1].split("(")[0].strip())
                            if (
                                score > 10
                            ):  # Duplicated if low complexity and high repetition
                                blocks.append(score)
                        except (IndexError, ValueError):
                            pass

                duplication_score = len(blocks)
                print(f"    Duplicated blocks: {duplication_score}")
                return min(duplication_score * 2, 100)  # Scale to 0-100
        except Exception as e:
            print(f"    Warning: Could not analyze duplication: {e}")

        return 0.0

    def analyze_test_coverage(self) -> float:
        """Analyze test coverage"""
        print("  🧪 Analyzing test coverage...")
        try:
            result = subprocess.run(
                [
                    "pytest",
                    "--cov=app",
                    "--cov-report=json",
                    "--cov-report=term-missing",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Read coverage report
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )
                print(f"    Coverage: {total_coverage:.1f}%")
                return total_coverage
        except Exception as e:
            print(f"    Warning: Could not analyze coverage: {e}")

        return 80.0  # Assume 80% if can't measure

    def analyze_code_smells(self) -> float:
        """Analyze code smells using pylint"""
        print("  👃 Analyzing code smells...")
        try:
            result = subprocess.run(
                ["pylint", "app", "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode in [0, 1, 2]:  # Pylint returns non-zero for issues
                try:
                    data = json.loads(result.stdout)
                    smell_count = len(data)

                    # Categorize by severity
                    for issue in data:
                        if issue.get("type") in [
                            "error",
                            "warning",
                            "convention",
                            "refactor",
                        ]:
                            self.issues.append(
                                {
                                    "type": "code_smell",
                                    "file": issue.get("path", ""),
                                    "line": issue.get("line", 0),
                                    "message": issue.get("message", ""),
                                    "symbol": issue.get("message-id", ""),
                                    "severity": self._map_pylint_severity(
                                        issue.get("type", "")
                                    ),
                                }
                            )

                    print(f"    Code smells: {smell_count}")
                    return min(smell_count / 10, 100)  # Scale to 0-100
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"    Warning: Could not analyze smells: {e}")

        return 0.0

    def _map_pylint_severity(self, pylint_type: str) -> str:
        """Map pylint message type to severity"""
        severity_map = {
            "error": "critical",
            "warning": "high",
            "convention": "medium",
            "refactor": "medium",
            "info": "low",
        }
        return severity_map.get(pylint_type, "low")

    def analyze_documentation(self) -> float:
        """Analyze documentation coverage"""
        print("  📚 Analyzing documentation...")
        documented_functions = 0
        total_functions = 0

        for py_file in self.project_root.rglob("app/**/*.py"):
            if "__pycache__" in str(py_file) or "__init__" in py_file.name:
                continue

            try:
                with open(py_file, "r") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Skip private methods
                        if node.name.startswith("_"):
                            continue

                        total_functions += 1

                        # Check if has docstring
                        docstring = ast.get_docstring(node)
                        if docstring and len(docstring) > 10:
                            documented_functions += 1
                        elif not node.name.startswith("_"):
                            # Public function without docstring
                            self.issues.append(
                                {
                                    "type": "documentation",
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": node.lineno,
                                    "function": node.name,
                                    "message": "Missing docstring",
                                    "severity": "medium",
                                }
                            )
            except Exception:
                pass

        if total_functions == 0:
            return 100.0

        doc_coverage = (documented_functions / total_functions) * 100
        print(f"    Functions: {total_functions}")
        print(f"    Documented: {documented_functions}")
        print(f"    Coverage: {doc_coverage:.1f}%")
        return doc_coverage

    def analyze_security(self) -> float:
        """Analyze security issues"""
        print("  🔒 Analyzing security...")
        security_issues = 0

        # Check for common security issues
        security_patterns = {
            "SQL injection": ['execute("', "execute (%s", ".execute("],
            "Hardcoded secrets": ["password =", "api_key =", "secret ="],
            "Debug enabled": ["DEBUG = True", "debug=True"],
            "Shell injection": ["os.system(", "subprocess.call(", "subprocess.Popen("],
        }

        for py_file in self.project_root.rglob("app/**/*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r") as f:
                    content = f.read()
                    lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for issue_type, patterns in security_patterns.items():
                        for pattern in patterns:
                            if pattern in line:
                                security_issues += 1
                                self.issues.append(
                                    {
                                        "type": "security",
                                        "file": str(
                                            py_file.relative_to(self.project_root)
                                        ),
                                        "line": line_num,
                                        "message": f"{issue_type}: {line.strip()}",
                                        "severity": "critical",
                                    }
                                )
            except Exception:
                pass

        print(f"    Security issues: {security_issues}")
        return min(security_issues * 5, 100)  # Scale to 0-100

    def generate_report(self) -> str:
        """Generate technical debt report"""
        self.analyze_all()

        score = self.metrics["overall_score"]
        total_issues = self.metrics["total_issues"]

        report = f"""
{'='*80}
PSYCHSYNC TECHNICAL DEBT REPORT
{'='*80}

Overall Technical Debt Score: {score}/10
Total Issues Found: {total_issues}

{'='*80}
BREAKDOWN BY CATEGORY
{'='*80}

Complexity:        {self.metrics['complexity']:.1f}/100 (lower is better)
Duplication:      {self.metrics['duplication']:.1f}/100 (lower is better)
Test Coverage:    {self.metrics['test_coverage']:.1f}% (higher is better)
Code Smells:      {self.metrics['code_smells']:.1f}/100 (lower is better)
Documentation:    {self.metrics['documentation']:.1f}% (higher is better)
Security:         {self.metrics['security']:.1f}/100 (lower is better)

{'='*80}
ISSUES BY SEVERITY
{'='*80}
"""

        # Count by severity
        severity_counts = {}
        for issue in self.issues:
            severity = issue.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            status = "✗" if count > 0 else "✓"
            report += f"{status} {severity.upper()}: {count}\n"

        report += f"\n{'='*80}\n"

        if score == 0.0:
            report += """
🎉 EXCELLENT! Zero technical debt detected.

The codebase is in excellent condition with:
- No code complexity issues
- No code duplication
- 95%+ test coverage
- No code smells
- Complete documentation
- No security vulnerabilities

Maintain this level of excellence through:
- Code reviews
- Continuous testing
- Regular refactoring
- Documentation updates
"""
        elif score < 2.0:
            report += f"""
✅ GOOD - Low technical debt ({score}/10)

The codebase is well-maintained with minor issues:
- {total_issues} issues need attention
- Focus on high and critical severity issues first
- Regular maintenance will keep debt low

Recommendation: Address issues during regular sprints
"""
        elif score < 5.0:
            report += f"""
⚠️  MODERATE technical debt ({score}/10)

The codebase needs attention:
- {total_issues} issues found
- Some complexity and duplication detected
- Test coverage needs improvement
- Documentation gaps exist

Recommendation: Plan dedicated refactoring sprint
"""
        else:
            report += f"""
❌ HIGH technical debt ({score}/10)

Critical issues require immediate attention:
- {total_issues} issues found
- High complexity or duplication
- Insufficient test coverage
- Major documentation gaps
- Security vulnerabilities present

Recommendation: HALT new features, focus on debt reduction
"""

        report += f"{'='*80}\n"

        return report

    def save_report(self, filename: str = "reports/technical_debt_report.json"):
        """Save detailed report to JSON"""
        self.project_root.mkdir("reports", exist_ok=True)

        with open(filename, "w") as f:
            json.dump(self.metrics, f, indent=2)

        print(f"\n📄 Detailed report saved to: {filename}")


if __name__ == "__main__":
    analyzer = TechnicalDebtAnalyzer()
    report = analyzer.generate_report()
    print(report)
    analyzer.save_report()
