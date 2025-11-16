# tests/devops_architecture_validation.py
"""
Comprehensive DevOps Testing & Architecture Validation
Part 1: Application Architecture Assessment

Tests layer separation, dependency injection, async consistency,
and architectural pattern compliance for PsychSync AI platform.
"""

import asyncio
import importlib
import inspect
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, asdict
from datetime import datetime
import pytest
import ast
import sys
from datetime import datetime, timezone

# Setup test environment
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class ArchitectureTestResult:
    """Architecture test result data structure"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    details: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    execution_time: float = 0.0

class ArchitectureValidator:
    """Comprehensive architecture validation tool"""

    def __init__(self):
        self.results: List[ArchitectureTestResult] = []
        self.project_root = Path(__file__).parent.parent
        self.app_dir = self.project_root / "app"
        self.ai_dir = self.project_root / "ai"
        self.frontend_dir = self.project_root / "frontend"

        # Architecture patterns to validate
        self.layer_patterns = {
            'api': r'^app/api/',
            'services': r'^app/services/',
            'crud': r'^app/crud/',
            'models': r'^app/db/models/',
            'schemas': r'^app/schemas/',
            'core': r'^app/core/',
            'processors': r'^ai/processors/'
        }

        self.forbidden_imports = {
            'api_from_services': (r'^app/services/', r'^app/api/', "Service layer should not import API layer"),
            'models_from_api': (r'^app/api/', r'^app/db/models/', "API layer should use schemas, not models directly"),
            'crud_from_api': (r'^app/api/', r'^app/crud/', "API layer should use services, not CRUD directly")
        }

    def run_test(self, test_name: str, test_func):
        """Run a test with timing and error handling"""
        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time

            if isinstance(result, ArchitectureTestResult):
                result.execution_time = execution_time
                self.results.append(result)
            else:
                # Convert boolean result to ArchitectureTestResult
                status = 'PASS' if result else 'FAIL'
                self.results.append(ArchitectureTestResult(
                    test_name=test_name,
                    status=status,
                    details=f"Test {status.lower()}ed",
                    execution_time=execution_time
                ))

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Test {test_name} failed: {str(e)}")
            self.results.append(ArchitectureTestResult(
                test_name=test_name,
                status='FAIL',
                details=f"Test execution failed: {str(e)}",
                execution_time=execution_time
            ))

    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Python file for architectural patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            analysis = {
                'imports': [],
                'classes': [],
                'functions': [],
                'async_functions': [],
                'decorators': [],
                'docstrings': [],
                'complexity': 0
 }

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            analysis['imports'].append({
                                'module': f"{node.module}.{alias.name}",
                                'alias': alias.asname,
                                'line': node.lineno
                            })

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'bases': [base.id if isinstance(base, ast.Name) else str(base)
                                for base in node.bases],
                        'methods': []
                    }

                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                'name': item.name,
                                'line': item.lineno,
                                'is_async': isinstance(item, ast.AsyncFunctionDef),
                                'args': [arg.arg for arg in item.args.args],
                                'decorators': [d.id if isinstance(d, ast.Name) else str(d)
                                             for d in item.decorator_list]
                            }
                            class_info['methods'].append(method_info)

                    analysis['classes'].append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'is_async': False,
                        'args': [arg.arg for arg in node.args.args]
                    }
                    analysis['functions'].append(func_info)

                elif isinstance(node, ast.AsyncFunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'is_async': True,
                        'args': [arg.arg for arg in node.args.args]
                    }
                    analysis['functions'].append(func_info)
                    analysis['async_functions'].append(func_info)

            # Calculate complexity (simplified)
            analysis['complexity'] = len(analysis['classes']) + len(analysis['functions'])

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {str(e)}")
            return {}

    def test_layer_separation(self) -> ArchitectureTestResult:
        """Test 1.1: Layer Separation Validation"""
        logger.info("Testing layer separation...")

        violations = []
        files_analyzed = 0

        # Analyze all Python files in app directory
        for py_file in self.app_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue

            files_analyzed += 1
            file_path = str(py_file.relative_to(self.project_root))
            analysis = self.analyze_python_file(py_file)

            # Check for forbidden import patterns
            for imp in analysis['imports']:
                module_path = imp['module']

                for violation_name, (pattern_from, pattern_to, message) in \
                        self.forbidden_imports.items():
                    # Check if current file matches pattern_from
                    import re
                    if re.match(pattern_from, file_path):
                        if re.match(pattern_to, module_path):
                            violations.append({
                                'file': file_path,
                                'line': imp['line'],
                                'import': module_path,
                                'violation': violation_name,
                                'message': message,
                                'suggestion': self._get_import_fix_suggestion(violation_name)
                            })

        # Determine test result
        if len(violations) == 0:
            return ArchitectureTestResult(
                test_name="Layer Separation Validation",
                status="PASS",
                details=f"Analyzed {files_analyzed} files, no layer violations found",
                execution_time=0.0
            )
        elif len(violations) <= 5:
            return ArchitectureTestResult(
                test_name="Layer Separation Validation",
                status="WARN",
                details=f"Analyzed {files_analyzed} files, found {len(violations)} minor violations",
                suggestion="Review and fix import violations for better layer separation",
                execution_time=0.0
            )
        else:
            # Format violations for details
            violation_summary = "\n".join([
                f"- {v['file']}:{v['line']} imports {v['import']} ({v['message']})"
                for v in violations[:5]
            ])

            return ArchitectureTestResult(
                test_name="Layer Separation Validation",
                status="FAIL",
                details=f"Found {len(violations)} layer violations:\n{violation_summary}",
                suggestion="Restructure imports to follow layer separation rules",
                execution_time=0.0
            )

    def test_dependency_injection(self) -> ArchitectureTestResult:
        """Test 1.2: Dependency Injection Validation"""
        logger.info("Testing dependency injection patterns...")

        di_patterns_found = []
        anti_patterns = []
        files_analyzed = 0

        # Key files to check for DI patterns
        di_files = [
            "app/main.py",
            "app/api/v1/endpoints/auth.py",
            "app/api/v1/endpoints/users.py",
            "app/api/v1/endpoints/assessments.py",
            "app/services/user_service.py",
            "app/services/assessment_service.py"
        ]

        for file_path_str in di_files:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue

            files_analyzed += 1
            analysis = self.analyze_python_file(file_path)

            # Check for DI patterns
            for func in analysis['functions']:
                # Look for dependency injection via function parameters
                if 'db:' in func['args'] or 'session:' in func['args']:
                    di_patterns_found.append({
                        'file': file_path_str,
                        'function': func['name'],
                        'line': func['line'],
                        'pattern': 'database_session_injection'
                    })

                # Check for async context
                if func['is_async'] and any(arg in func['args']
                                          for arg in ['db', 'session', 'user_service']):
                    di_patterns_found.append({
                        'file': file_path_str,
                        'function': func['name'],
                        'line': func['line'],
                        'pattern': 'async_dependency_injection'
                    })

            # Check for anti-patterns (hard-coded dependencies)
            content = file_path.read_text()

            # Look for direct imports that should be injected
            anti_pattern_imports = [
                'from app.core.database import SessionLocal',
                'SessionLocal()',
                'get_db()'
            ]

            for anti_pattern in anti_pattern_imports:
                if anti_pattern in content:
                    anti_patterns.append({
                        'file': file_path_str,
                        'anti_pattern': anti_pattern,
                        'suggestion': 'Use dependency injection instead of direct imports'
                    })

        # Scoring
        di_score = len(di_patterns_found)
        anti_pattern_score = len(anti_patterns)

        if di_score >= 5 and anti_pattern_score == 0:
            return ArchitectureTestResult(
                test_name="Dependency Injection Validation",
                status="PASS",
                details=f"Found {di_score} good DI patterns, no anti-patterns in {files_analyzed} files",
                execution_time=0.0
            )
        elif di_score >= 3 and anti_pattern_score <= 2:
            return ArchitectureTestResult(
                test_name="Dependency Injection Validation",
                status="WARN",
                details=f"Found {di_score} DI patterns but {anti_pattern_score} anti-patterns",
                suggestion="Refactor anti-patterns to use proper dependency injection",
                execution_time=0.0
            )
        else:
            return ArchitectureTestResult(
                test_name="Dependency Injection Validation",
                status="FAIL",
                details=f"Insufficient DI patterns ({di_score}) and too many anti-patterns ({anti_pattern_score})",
                suggestion="Implement proper dependency injection throughout the application",
                execution_time=0.0
            )

    def test_async_sync_consistency(self) -> ArchitectureTestResult:
        """Test 1.3: Async/Sync Consistency Checks"""
        logger.info("Testing async/sync consistency...")

        inconsistencies = []
        async_files = []
        sync_files = []
        mixed_files = []

        # Analyze service layer files
        service_files = list((self.project_root / "app/services").rglob("*.py"))
        api_files = list((self.project_root / "app/api").rglob("*.py"))

        for file_path in service_files + api_files:
            if '__pycache__' in str(file_path):
                continue

            analysis = self.analyze_python_file(file_path)

            async_count = len(analysis['async_functions'])
            sync_count = len(analysis['functions']) - async_count

            if async_count > 0 and sync_count > 0:
                mixed_files.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'async_count': async_count,
                    'sync_count': sync_count,
                    'functions': [f['name'] for f in analysis['functions']]
                })
                inconsistencies.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'issue': 'mixed_async_sync',
                    'details': f"File has {async_count} async and {sync_count} sync functions"
                })
            elif async_count > 0:
                async_files.append(str(file_path.relative_to(self.project_root)))
            elif sync_count > 0:
                sync_files.append(str(file_path.relative_to(self.project_root)))

        # Check for improper async/await usage
        improper_usage = []
        for file_path in service_files + api_files:
            if '__pycache__' in str(file_path):
                continue

            content = file_path.read_text()

            # Look for async functions calling sync operations without proper handling
            if 'async def' in content:
                # Check for sync database operations in async functions
                sync_patterns_in_async = [
                    '.query(',
                    '.add(',
                    '.commit(',
                    '.execute(',
                    'SessionLocal()'
                ]

                lines = content.split('\n')
                in_async_func = False
                async_func_name = None

                for i, line in enumerate(lines, 1):
                    if 'async def ' in line:
                        in_async_func = True
                        async_func_name = line.split('async def ')[1].split('(')[0].strip()
                    elif line.strip().startswith(('def ', 'async def ', 'class ')):
                        in_async_func = False
                        async_func_name = None
                    elif in_async_func:
                        for pattern in sync_patterns_in_async:
                            if pattern in line and 'await' not in line:
                                improper_usage.append({
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'function': async_func_name,
                                    'line': i,
                                    'pattern': pattern,
                                    'suggestion': 'Use async database operations or proper await'
                                })

        # Determine results
        total_issues = len(inconsistencies) + len(improper_usage)

        if total_issues == 0:
            return ArchitectureTestResult(
                test_name="Async/Sync Consistency",
                status="PASS",
                details=f"Analyzed {len(async_files + sync_files)} files, no inconsistencies found",
                execution_time=0.0
            )
        elif total_issues <= 3:
            return ArchitectureTestResult(
                test_name="Async/Sync Consistency",
                status="WARN",
                details=f"Found {total_issues} minor async/sync issues",
                suggestion="Review and fix async/sync inconsistencies",
                execution_time=0.0
            )
        else:
            issue_summary = []
            if inconsistencies:
                issue_summary.append(f"{len(inconsistencies)} files with mixed async/sync")
            if improper_usage:
                issue_summary.append(f"{len(improper_usage)} improper async usages")

            return ArchitectureTestResult(
                test_name="Async/Sync Consistency",
                status="FAIL",
                details=f"Found {', '.join(issue_summary)}",
                suggestion="Standardize async patterns and fix improper usage",
                execution_time=0.0
            )

    def test_architecture_compliance(self) -> ArchitectureTestResult:
        """Test 1.4: Architecture Pattern Compliance"""
        logger.info("Testing architecture pattern compliance...")

        compliance_score = 0
        max_score = 10
        issues = []

        # Check 1: Service layer exists and follows patterns
        service_dir = self.project_root / "app/services"
        if service_dir.exists() and len(list(service_dir.glob("*.py"))) >= 3:
            compliance_score += 2
        else:
            issues.append("Service layer is incomplete or missing")

        # Check 2: API versioning exists
        api_v1_dir = self.project_root / "app/api/v1"
        if api_v1_dir.exists():
            compliance_score += 1
        else:
            issues.append("API versioning structure missing")

        # Check 3: Proper model separation
        models_dir = self.project_root / "app/db/models"
        if models_dir.exists() and len(list(models_dir.glob("*.py"))) >= 5:
            compliance_score += 2
        else:
            issues.append("Models layer is incomplete")

        # Check 4: Schema definitions exist
        schemas_dir = self.project_root / "app/schemas"
        if schemas_dir.exists() and len(list(schemas_dir.glob("*.py"))) >= 3:
            compliance_score += 1
        else:
            issues.append("Schema definitions missing")

        # Check 5: Configuration management
        config_file = self.project_root / "app/core/config.py"
        if config_file.exists():
            compliance_score += 1
        else:
            issues.append("Configuration management missing")

        # Check 6: Database connection management
        db_file = self.project_root / "app/core/database.py"
        if db_file.exists():
            compliance_score += 1
        else:
            issues.append("Database connection management missing")

        # Check 7: Error handling structure
        exceptions_file = self.project_root / "app/core/exceptions.py"
        if exceptions_file.exists():
            compliance_score += 1
        else:
            issues.append("Error handling structure missing")

        # Check 8: AI processor structure
        ai_processors_dir = self.project_root / "ai/processors"
        if ai_processors_dir.exists() and len(list(ai_processors_dir.glob("*.py"))) >= 3:
            compliance_score += 1
        else:
            issues.append("AI processor structure incomplete")

        # Determine result
        compliance_percentage = (compliance_score / max_score) * 100

        if compliance_percentage >= 90:
            status = "PASS"
            details = f"Excellent architecture compliance: {compliance_percentage:.1f}%"
        elif compliance_percentage >= 70:
            status = "WARN"
            details = f"Good architecture compliance: {compliance_percentage:.1f}% - Minor issues: {', '.join(issues)}"
        else:
            status = "FAIL"
            details = f"Poor architecture compliance: {compliance_percentage:.1f}% - Issues: {', '.join(issues)}"

        return ArchitectureTestResult(
            test_name="Architecture Pattern Compliance",
            status=status,
            details=details,
            suggestion="Address identified architectural gaps" if compliance_percentage < 90 else None,
            execution_time=0.0
        )

    def _get_import_fix_suggestion(self, violation_name: str) -> str:
        """Get fix suggestion for import violation"""
        suggestions = {
            'api_from_services': "Service should not import API. Move shared logic to core module.",
            'models_from_api': "API should use schemas, not models directly. Import schemas instead.",
            'crud_from_api': "API should use services, not CRUD directly. Use service layer."
        }
        return suggestions.get(violation_name, "Review import structure")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive architecture validation report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])
        warned_tests = len([r for r in self.results if r.status == 'WARN'])

        total_time = sum(r.execution_time for r in self.results)

        return {
            'test_suite': 'Architecture Validation',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warned_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_execution_time': total_time
            },
            'test_results': [asdict(result) for result in self.results],
            'recommendations': self._generate_recommendations(),
            'architecture_grade': self._calculate_architecture_grade()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate architecture improvement recommendations"""
        recommendations = []

        failed_tests = [r for r in self.results if r.status == 'FAIL']
        warned_tests = [r for r in self.results if r.status == 'WARN']

        if failed_tests:
            recommendations.append("CRITICAL: Fix all failed architecture tests before production deployment")

        if warned_tests:
            recommendations.append("Address warnings to improve code quality and maintainability")

        # Specific recommendations based on test results
        for result in self.results:
            if result.suggestion:
                recommendations.append(f"- {result.suggestion}")

        # General recommendations
        recommendations.extend([
            "Implement comprehensive automated testing in CI/CD pipeline",
            "Consider using dependency injection framework (FastAPI Depends)",
            "Standardize async patterns throughout the application",
            "Document architectural decisions and patterns"
        ])

        return recommendations

    def _calculate_architecture_grade(self) -> str:
        """Calculate overall architecture grade"""
        if not self.results:
            return "NO_GRADE"

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])

        pass_rate = (passed_tests / total_tests) * 100

        if pass_rate >= 90 and failed_tests == 0:
            return "A"
        elif pass_rate >= 80 and failed_tests == 0:
            return "B+"
        elif pass_rate >= 70 and failed_tests <= 1:
            return "B"
        elif pass_rate >= 60 and failed_tests <= 2:
            return "C"
        else:
            return "F"

# Pytest integration functions
@pytest.fixture
def architecture_validator():
    """Pytest fixture for ArchitectureValidator"""
    return ArchitectureValidator()

def test_layer_separation(architecture_validator):
    """Pytest wrapper for layer separation test"""
    result = architecture_validator.test_layer_separation()
    assert result.status in ['PASS', 'WARN'], f"Layer separation test failed: {result.details}"

def test_dependency_injection(architecture_validator):
    """Pytest wrapper for dependency injection test"""
    result = architecture_validator.test_dependency_injection()
    assert result.status in ['PASS', 'WARN'], f"Dependency injection test failed: {result.details}"

def test_async_sync_consistency(architecture_validator):
    """Pytest wrapper for async/sync consistency test"""
    result = architecture_validator.test_async_sync_consistency()
    assert result.status in ['PASS', 'WARN'], f"Async/sync consistency test failed: {result.details}"

def test_architecture_compliance(architecture_validator):
    """Pytest wrapper for architecture compliance test"""
    result = architecture_validator.test_architecture_compliance()
    assert result.status in ['PASS', 'WARN'], f"Architecture compliance test failed: {result.details}"

def test_architecture_validation_complete(architecture_validator):
    """Complete architecture validation test suite"""
    # Run all architecture tests
    architecture_validator.run_test("Layer Separation", architecture_validator.test_layer_separation)
    architecture_validator.run_test("Dependency Injection", architecture_validator.test_dependency_injection)
    architecture_validator.run_test("Async/Sync Consistency", architecture_validator.test_async_sync_consistency)
    architecture_validator.run_test("Architecture Compliance", architecture_validator.test_architecture_compliance)

    # Generate report
    report = architecture_validator.generate_report()

    # Save report to file
    report_path = Path(__file__).parent.parent / "test_reports" / "architecture_validation_report.json"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Architecture validation report saved to: {report_path}")

    # Assertions
    assert report['summary']['success_rate'] >= 70, "Architecture validation success rate below 70%"
    assert report['architecture_grade'] not in ['F'], "Architecture grade is F - critical issues found"

    # Print summary
    print(f"\n🏗️  Architecture Validation Results:")
    print(f"   Grade: {report['architecture_grade']}")
    print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Warnings: {report['summary']['warnings']}")
    print(f"   Report: {report_path}")

# Main execution function
def run_architecture_validation():
    """Run architecture validation independently"""
    validator = ArchitectureValidator()

    print("🏗️  Starting Architecture Validation Tests...")
    print("=" * 50)

    # Run all tests
    validator.run_test("Layer Separation", validator.test_layer_separation)
    validator.run_test("Dependency Injection", validator.test_dependency_injection)
    validator.run_test("Async/Sync Consistency", validator.test_async_sync_consistency)
    validator.run_test("Architecture Compliance", validator.test_architecture_compliance)

    # Generate and print report
    report = validator.generate_report()

    print(f"\n📊 Test Results:")
    print(f"   Total Tests: {report['summary']['total_tests']}")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Warnings: {report['summary']['warnings']}")
    print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"   Architecture Grade: {report['architecture_grade']}")
    print(f"   Execution Time: {report['summary']['total_execution_time']:.3f}s")

    print(f"\n📋 Detailed Results:")
    for result in validator.results:
        status_icon = "✅" if result.status == "PASS" else "⚠️" if result.status == "WARN" else "❌"
        print(f"   {status_icon} {result.test_name}")
        if result.status != "PASS":
            print(f"      → {result.details}")

    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")

    # Save report
    report_path = Path(__file__).parent.parent / "test_reports" / f"architecture_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Full report saved: {report_path}")

    return report

if __name__ == "__main__":
    run_architecture_validation()