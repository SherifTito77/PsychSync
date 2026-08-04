# tests/test_coverage_validator.py
"""
Test Coverage Validation and Reporting System
Provides comprehensive coverage analysis and reporting for the PsychSync test suite
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class CoverageReport:
    """Coverage report data structure"""

    total_coverage: float
    coverage_by_module: Dict[str, float]
    uncovered_lines: List[str]
    covered_lines: int
    total_lines: int
    missing_coverage: List[Dict[str, Any]]
    timestamp: str


class CoverageValidator:
    """Comprehensive test coverage validation and reporting"""

    def __init__(self, target_coverage: float = 85.0):
        self.target_coverage = target_coverage
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"

    def run_coverage_analysis(self, output_format: str = "json") -> CoverageReport:
        """
        Run comprehensive coverage analysis
        """
        print("🔍 Running Test Coverage Analysis...")
        print("=" * 60)

        # Run pytest with coverage
        coverage_data = self._run_pytest_coverage()

        # Parse coverage results
        coverage_report = self._parse_coverage_data(coverage_data)

        # Generate report
        self._generate_coverage_report(coverage_report, output_format)

        return coverage_report

    def _run_pytest_coverage(self) -> Dict[str, Any]:
        """Run pytest with coverage plugin"""
        try:
            # Install pytest-cov if not available
            self._ensure_coverage_tool()

            # Coverage configuration
            cov_config = self.project_root / "pyproject.toml"
            if not cov_config.exists():
                self._create_coverage_config()

            # Run tests with coverage
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "--cov=app",
                "--cov-report=json",
                "--cov-report=term-missing",
                "--cov-report=html",
                "tests/",
                "--tb=short",
            ]

            print(f"📊 Running: {' '.join(cmd)}")

            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            end_time = time.time()

            print(f"⏱️  Test execution time: {end_time - start_time:.2f} seconds")

            if result.returncode != 0:
                print("❌ Test execution failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return {"error": result.stderr, "stdout": result.stdout}

            # Read coverage report
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    return json.load(f)

            return {"error": "Coverage report not generated", "stdout": result.stdout}

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out", "timeout": True}
        except Exception as e:
            return {"error": f"Coverage analysis failed: {str(e)}"}

    def _parse_coverage_data(self, coverage_data: Dict[str, Any]) -> CoverageReport:
        """Parse coverage data from pytest-cov output"""
        if "error" in coverage_data:
            return CoverageReport(
                total_coverage=0.0,
                coverage_by_module={},
                uncovered_lines=[],
                covered_lines=0,
                total_lines=0,
                missing_coverage=[],
                timestamp=datetime.utcnow().isoformat(),
            )

        totals = coverage_data.get("totals", {})
        files = coverage_data.get("files", {})

        total_coverage = totals.get("percent_covered", 0.0)
        covered_lines = totals.get("covered_lines", 0)
        total_lines = totals.get("num_statements", 0)

        coverage_by_module = {}
        uncovered_lines = []
        missing_coverage = []

        for file_path, file_data in files.items():
            module_name = self._get_module_name(file_path)
            file_coverage = file_data.get("summary", {}).get("percent_covered", 0.0)
            coverage_by_module[module_name] = file_coverage

            # Find uncovered lines
            missing_lines = file_data.get("missing_lines", [])
            if missing_lines:
                uncovered_lines.extend(
                    [f"{module_name}:{line}" for line in missing_lines]
                )

                missing_coverage.append(
                    {
                        "module": module_name,
                        "file": file_path,
                        "uncovered_lines": missing_lines,
                        "coverage_percent": file_coverage,
                    }
                )

        return CoverageReport(
            total_coverage=total_coverage,
            coverage_by_module=coverage_by_module,
            uncovered_lines=uncovered_lines,
            covered_lines=covered_lines,
            total_lines=total_lines,
            missing_coverage=missing_coverage,
            timestamp=datetime.utcnow().isoformat(),
        )

    def _generate_coverage_report(
        self, report: CoverageReport, output_format: str = "json"
    ):
        """Generate comprehensive coverage report"""
        print("\n📊 Coverage Analysis Results")
        print("=" * 60)
        print(f"🎯 Target Coverage: {self.target_coverage}%")
        print(f"📈 Actual Coverage: {report.total_coverage:.2f}%")
        print(f"📋 Total Lines: {report.total_lines:,}")
        print(f"✅ Covered Lines: {report.covered_lines:,}")
        print(f"❌ Missing Lines: {report.total_lines - report.covered_lines:,}")

        # Module coverage
        print(f"\n📚 Coverage by Module:")
        for module, coverage in sorted(report.coverage_by_module.items()):
            status = "✅" if coverage >= self.target_coverage else "❌"
            print(f"  {status} {module}: {coverage:.1f}%")

        # Missing coverage details
        if report.missing_coverage:
            print(f"\n🔍 Missing Coverage Details:")
            for item in report.missing_coverage[:10]:  # Show first 10
                print(
                    f"  📂 {item['module']}: {len(item['uncovered_lines'])} lines ({item['coverage_percent']:.1f}%)"
                )

        if len(report.missing_coverage) > 10:
            print(f"  ... and {len(report.missing_coverage) - 10} more files")

        # Save detailed report
        self._save_coverage_report(report, output_format)

        # Validate against target
        self._validate_coverage_target(report)

    def _save_coverage_report(self, report: CoverageReport, output_format: str):
        """Save detailed coverage report"""
        reports_dir = self.project_root / "test_reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # JSON report
        json_file = reports_dir / f"coverage_report_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(
                {
                    "metadata": {
                        "target_coverage": self.target_coverage,
                        "timestamp": report.timestamp,
                        "project_root": str(self.project_root),
                    },
                    "summary": {
                        "total_coverage": report.total_coverage,
                        "covered_lines": report.covered_lines,
                        "total_lines": report.total_lines,
                        "missing_lines": len(report.uncovered_lines),
                    },
                    "modules": report.coverage_by_module,
                    "missing_coverage": report.missing_coverage,
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed report saved: {json_file}")

        # Text report
        text_file = reports_dir / f"coverage_report_{timestamp}.txt"
        with open(text_file, "w") as f:
            f.write(f"PsychSync Test Coverage Report\n")
            f.write(f"Generated: {report.timestamp}\n")
            f.write(f"Target Coverage: {self.target_coverage}%\n")
            f.write(f"Actual Coverage: {report.total_coverage:.2f}%\n")
            f.write(
                f"Status: {'✅ PASSED' if report.total_coverage >= self.target_coverage else '❌ FAILED'}\n\n"
            )

            f.write("Module Coverage:\n")
            for module, coverage in sorted(report.coverage_by_module.items()):
                status = "✅" if coverage >= self.target_coverage else "❌"
                f.write(f"{status} {module}: {coverage:.1f}%\n")

            if report.missing_coverage:
                f.write("\nMissing Coverage Details:\n")
                for item in report.missing_coverage:
                    f.write(f"\n{item['module']} ({item['coverage_percent']:.1f}%):\n")
                    for line in item["uncovered_lines"][:20]:  # Show first 20 lines
                        f.write(f"  Line {line}\n")
                    if len(item["uncovered_lines"]) > 20:
                        f.write(
                            f"  ... and {len(item['uncovered_lines']) - 20} more lines\n"
                        )

        print(f"📄 Text report saved: {text_file}")

    def _validate_coverage_target(self, report: CoverageReport):
        """Validate coverage against target"""
        print(f"\n🎯 Coverage Validation:")
        print("=" * 30)

        if report.total_coverage >= self.target_coverage:
            print(
                f"✅ PASSED: Coverage {report.total_coverage:.2f}% exceeds target {self.target_coverage}%"
            )
            return True
        else:
            deficit = self.target_coverage - report.total_coverage
            print(
                f"❌ FAILED: Coverage {report.total_coverage:.2f}% below target {self.target_coverage}%"
            )
            print(f"📉 Coverage deficit: {deficit:.2f}%")
            print(f"\n💡 Recommendations:")
            print(
                f"  • Add tests for uncovered lines in {len(report.missing_coverage)} files"
            )
            print(f"   Top files needing tests:")

            # Sort by missing lines count
            sorted_missing = sorted(
                report.missing_coverage,
                key=lambda x: len(x["uncovered_lines"]),
                reverse=True,
            )

            for item in sorted_missing[:5]:
                print(
                    f"     - {item['module']}: {len(item['uncovered_lines'])} uncovered lines"
                )

            return False

    def _ensure_coverage_tool(self):
        """Ensure pytest-cov is installed"""
        try:
            import pytest_cov
        except ImportError:
            print("📦 Installing pytest-cov...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pytest-cov"], check=True
            )

    def _create_coverage_config(self):
        """Create pytest coverage configuration"""
        config_content = """
[tool:pytest]
addopts = --strict-markers
testpaths = tests
python_files = tests.py test_*.py *_test.py

[tool.coverage.run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    */env/*
    */site-packages/*
    */conftest.py

[tool.coverage.report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:  # pragma: no cover
    if TYPE_CHECKING:  # pragma: no cover
    class .*\bProtocol\):  # pragma: no cover
    @(abc\.)?abstractmethod
    """

        config_file = self.project_root / "pyproject.toml"
        with open(config_file, "w") as f:
            f.write(config_content)

        print(f"📄 Created coverage config: {config_file}")

    def _get_module_name(self, file_path: str) -> str:
        """Get module name from file path"""
        # Convert file path to module name
        parts = Path(file_path).parts
        module_parts = []

        # Find 'app' directory
        try:
            app_index = parts.index("app")
            module_parts = parts[app_index:-1]  # Remove .py extension
        except ValueError:
            # No 'app' directory found, use filename
            module_parts = [Path(file_path).stem]

        # Join parts with dots and remove .py extension
        module_name = ".".join(module_parts)
        module_name = module_name.replace(".py", "")

        return module_name

    def analyze_test_files(self) -> Dict[str, Any]:
        """Analyze test files and generate statistics"""
        print("\n📊 Test File Analysis")
        print("=" * 30)

        test_files = list(self.tests_dir.rglob("test_*.py"))
        total_test_files = len(test_files)

        total_lines = 0
        test_functions = 0
        test_classes = 0
        async_tests = 0

        for test_file in test_files:
            try:
                with open(test_file, "r") as f:
                    content = f.read()
                    lines = content.split("\n")
                    total_lines += len(lines)

                    # Count test functions
                    test_functions += len(
                        [line for line in lines if line.strip().startswith("def test_")]
                    )

                    # Count test classes
                    test_classes += len(
                        [line for line in lines if "class Test" in line]
                    )

                    # Count async tests
                    async_tests += len(
                        [line for line in lines if "async def test_" in line]
                    )

            except Exception as e:
                print(f"⚠️  Could not analyze {test_file}: {e}")

        print(f"📁 Test files: {total_test_files}")
        print(f"📏 Total lines: {total_lines}")
        print(f"🧪 Test functions: {test_functions}")
        print(f"📋 Test classes: {test_classes}")
        print(f"⚡ Async tests: {async_tests}")

        if total_test_files > 0:
            avg_lines_per_file = total_lines / total_test_files
            print(f"📊 Avg lines per file: {avg_lines_per_file:.1f}")

        return {
            "total_files": total_test_files,
            "total_lines": total_lines,
            "test_functions": test_functions,
            "test_classes": test_classes,
            "async_tests": async_tests,
        }

    def validate_test_quality(self) -> Dict[str, Any]:
        """Validate test quality and best practices"""
        print("\n🔍 Test Quality Validation")
        print("=" * 30)

        test_files = list(self.tests_dir.rglob("test_*.py"))
        quality_issues = []

        for test_file in test_files:
            try:
                with open(test_file, "r") as f:
                    content = f.read()
                    lines = content.split("\n")

                # Check for test documentation
                docstring_count = len(
                    [line for line in lines if '"""' in line or "'''" in line]
                )

                # Check for assertion usage
                assertion_count = content.count("assert")

                # Check for proper test structure
                has_setup = any(
                    "def setUp" in line or "@pytest.fixture" in line for line in lines
                )
                has_teardown = any("def tearDown" in line for line in lines)

                file_info = {
                    "file": str(test_file),
                    "lines": len(lines),
                    "docstrings": docstring_count,
                    "assertions": assertion_count,
                    "has_setup": has_setup,
                    "has_teardown": has_teardown,
                }

                # Quality checks
                if docstring_count == 0 and len(lines) > 20:
                    quality_issues.append(
                        {
                            "type": "no_docstring",
                            "file": str(test_file),
                            "message": "File lacks test documentation",
                        }
                    )

                if assertion_count < 3 and len(lines) > 20:
                    quality_issues.append(
                        {
                            "type": "insufficient_assertions",
                            "file": str(test_file),
                            "message": f"Only {assertion_count} assertions found",
                        }
                    )

                if len(lines) > 500 and assertion_count < 10:
                    quality_issues.append(
                        {
                            "type": "low_test_ratio",
                            "file": str(test_file),
                            "message": f"Low assertion/line ratio: {assertion_count}/{len(lines)}",
                        }
                    )

            except Exception as e:
                quality_issues.append(
                    {
                        "type": "analysis_error",
                        "file": str(test_file),
                        "message": f"Could not analyze file: {str(e)}",
                    }
                )

        print(f"📊 Quality Issues Found: {len(quality_issues)}")

        if quality_issues:
            print("\nQuality Issues:")
            for issue in quality_issues[:10]:  # Show first 10
                print(f"  ❌ {issue['type']}: {issue['message']}")
                print(f"     📁 {issue['file']}")

            if len(quality_issues) > 10:
                print(f"  ... and {len(quality_issues) - 10} more issues")
        else:
            print("✅ No quality issues found!")

        return {"total_issues": len(quality_issues), "issues": quality_issues}

    def generate_test_suite_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test suite summary"""
        print("\n📋 Test Suite Summary")
        print("=" * 40)

        # Analyze test files
        test_stats = self.analyze_test_files()

        # Validate test quality
        quality_stats = self.validate_test_quality()

        # Run a quick syntax check
        syntax_errors = self._check_test_syntax()

        print(f"\n📊 Test Suite Statistics:")
        print(f"   Test Files: {test_stats['total_files']}")
        print(f"   Total Lines: {test_stats['total_lines']:,}")
        print(f"   Test Functions: {test_stats['test_functions']}")
        print(f"   Test Classes: {test_stats['test_classes']}")
        print(f"   Async Tests: {test_stats['async_tests']}")
        print(f"   Quality Issues: {quality_stats['total_issues']}")
        print(f"   Syntax Errors: {len(syntax_errors)}")

        if syntax_errors:
            print(f"\n❌ Syntax Errors:")
            for error in syntax_errors:
                print(f"   • {error['file']}: {error['error']}")

        return {
            "test_statistics": test_stats,
            "quality_analysis": quality_stats,
            "syntax_errors": syntax_errors,
        }

    def _check_test_syntax(self) -> List[Dict[str, str]]:
        """Check test files for syntax errors"""
        syntax_errors = []
        test_files = list(self.tests_dir.rglob("test_*.py"))

        for test_file in test_files:
            try:
                # Try to compile the file
                py_compile.compile(test_file.read())
            except SyntaxError as e:
                syntax_errors.append(
                    {
                        "file": str(test_file),
                        "error": str(e),
                        "line": e.lineno if hasattr(e, "lineno") else None,
                    }
                )
            except Exception as e:
                syntax_errors.append(
                    {"file": str(test_file), "error": f"Compilation error: {str(e)}"}
                )

        return syntax_errors

    def run_comprehensive_analysis(self):
        """Run comprehensive test analysis"""
        print("🔍 Comprehensive Test Suite Analysis")
        print("=" * 80)

        # Generate test suite summary
        suite_summary = self.generate_test_suite_summary()

        # Run coverage analysis
        coverage_report = self.run_coverage_analysis()

        # Create final summary
        final_summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "project_root": str(self.project_root),
            "target_coverage": self.target_coverage,
            "coverage": {
                "percentage": coverage_report.total_coverage,
                "status": (
                    "PASS"
                    if coverage_report.total_coverage >= self.target_coverage
                    else "FAIL"
                ),
                "total_lines": coverage_report.total_lines,
                "covered_lines": coverage_report.covered_lines,
            },
            "test_suite": suite_summary,
        }

        # Save final summary
        reports_dir = self.project_root / "test_reports"
        reports_dir.mkdir(exist_ok=True)

        summary_file = (
            reports_dir
            / f"test_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(summary_file, "w") as f:
            json.dump(final_summary, f, indent=2)

        print(f"\n📄 Summary report saved: {summary_file}")

        return final_summary


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="PsychSync Coverage Validator")
    parser.add_argument(
        "--target-coverage",
        type=float,
        default=85.0,
        help="Target coverage percentage (default: 85.0)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Report format (default: json)",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze test files, don't run tests",
    )

    args = parser.parse_args()

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Initialize coverage validator
    validator = CoverageValidator(target_coverage=args.target_coverage)

    if args.analyze_only:
        # Only analyze test files
        validator.generate_test_suite_summary()
    else:
        # Run comprehensive analysis
        final_summary = validator.run_comprehensive_analysis()

        # Exit with appropriate code
        if final_summary["coverage"]["status"] == "FAIL":
            print(f"\n❌ Coverage target ({args.target_coverage}%) not met!")
            sys.exit(1)
        else:
            print(f"\n✅ All requirements met!")


if __name__ == "__main__":
    main()
