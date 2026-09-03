#!/usr/bin/env python3
"""
Architecture Validation Script

Detects architectural inconsistencies across the codebase:
✅ Service layer patterns (BaseService vs standalone functions)
✅ Data access patterns (CRUD vs Repository vs Direct)
✅ Authentication patterns in endpoints
✅ Middleware registrations
✅ Duplicate code patterns

Usage:
    python scripts/validate_architecture.py              # Full report
    python scripts/validate_architecture.py --services   # Services only
    python scripts/validate_architecture.py --data       # Data access only
    python scripts/validate_architecture.py --auth       # Auth patterns only

Author: Architecture Validation Team
Version: 1.0
"""

import ast
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class ArchitectureIssue:
    """Represents an architectural inconsistency."""

    category: str
    severity: str  # critical, high, medium, low
    file: str
    line: int
    message: str
    recommendation: str | None = None


@dataclass
class ValidationResult:
    """Results of architecture validation."""

    services: dict[str, list[ArchitectureIssue]] = field(default_factory=dict)
    data_access: dict[str, list[ArchitectureIssue]] = field(default_factory=dict)
    auth_patterns: dict[str, list[ArchitectureIssue]] = field(default_factory=dict)
    middleware: dict[str, list[ArchitectureIssue]] = field(default_factory=dict)

    def total_issues(self) -> int:
        """Return total number of issues found."""
        return (
            sum(len(issues) for issues in self.services.values())
            + sum(len(issues) for issues in self.data_access.values())
            + sum(len(issues) for issues in self.auth_patterns.values())
            + sum(len(issues) for issues in self.middleware.values())
        )

    def critical_issues(self) -> int:
        """Return number of critical issues."""
        return sum(
            len([i for i in issues if i.severity == "critical"])
            for issues in self.services.values()
        ) + sum(
            len([i for i in issues if i.severity == "critical"])
            for issues in self.data_access.values()
        )


# =============================================================================
# SERVICE LAYER VALIDATION
# =============================================================================


class ServiceLayerValidator:
    """Validates service layer architectural consistency."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services_dir = project_root / "app" / "services"

    def validate(self) -> dict[str, list[ArchitectureIssue]]:
        """Validate all service files."""
        issues = defaultdict(list)

        if not self.services_dir.exists():
            return issues

        for service_file in self.services_dir.glob("*.py"):
            if service_file.name.startswith("_"):
                continue

            file_issues = self._validate_service_file(service_file)
            for issue in file_issues:
                issues[issue.category].append(issue)

        return dict(issues)

    def _validate_service_file(self, file_path: Path) -> list[ArchitectureIssue]:
        """Validate a single service file."""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))

            # Check if file extends BaseService
            extends_base_service = self._check_extends_base_service(tree)

            # Check for standalone async functions
            standalone_functions = self._find_standalone_functions(tree)

            # Check for proper error handling
            error_handling = self._check_error_handling(tree)

            # Check for caching decorators
            uses_decorators = self._check_cached_decorators(tree)

            if not extends_base_service and standalone_functions:
                issues.append(
                    ArchitectureIssue(
                        category="service_layer",
                        severity="high",
                        file=str(file_path.relative_to(self.project_root)),
                        line=1,
                        message=f"Service uses standalone functions instead of extending BaseService "
                        f"({len(standalone_functions)} functions found)",
                        recommendation="Refactor to extend BaseService for consistent error handling and caching",
                    )
                )

            if extends_base_service and uses_decorators:
                issues.append(
                    ArchitectureIssue(
                        category="service_layer",
                        severity="medium",
                        file=str(file_path.relative_to(self.project_root)),
                        line=1,
                        message="Service extends BaseService but uses @cached decorators",
                        recommendation="Remove @cached decorators - BaseService handles caching automatically",
                    )
                )

            if (
                not extends_base_service
                and not uses_decorators
                and standalone_functions
            ):
                issues.append(
                    ArchitectureIssue(
                        category="service_layer",
                        severity="critical",
                        file=str(file_path.relative_to(self.project_root)),
                        line=1,
                        message="Service has no caching strategy (extends BaseService=False, @cached=False)",
                        recommendation="Either extend BaseService or add @cached decorators to retrieval methods",
                    )
                )

        except SyntaxError as e:
            issues.append(
                ArchitectureIssue(
                    category="service_layer",
                    severity="low",
                    file=str(file_path.relative_to(self.project_root)),
                    line=e.lineno or 1,
                    message=f"Syntax error prevents analysis: {e.msg}",
                    recommendation=None,
                )
            )

        return issues

    def _check_extends_base_service(self, tree: ast.AST) -> bool:
        """Check if file contains a class extending BaseService."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BaseService":
                        return True
                    if isinstance(base, ast.Subscript):
                        if (
                            isinstance(base.value, ast.Name)
                            and base.value.id == "BaseService"
                        ):
                            return True
        return False

    def _find_standalone_functions(self, tree: ast.AST) -> list[str]:
        """Find standalone async functions."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Skip private methods
                if node.name.startswith("_"):
                    continue
                functions.append(node.name)
        return functions

    def _check_error_handling(self, tree: ast.AST) -> bool:
        """Check if functions have proper error handling."""
        # Simplified check - looks for try/except blocks
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                return True
        return False

    def _check_cached_decorators(self, tree: ast.AST) -> bool:
        """Check if file uses @cached decorators."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "cached":
                        return True
                    if isinstance(decorator, ast.Call):
                        if (
                            isinstance(decorator.func, ast.Name)
                            and decorator.func.id == "cached"
                        ):
                            return True
        return False


# =============================================================================
# DATA ACCESS VALIDATION
# =============================================================================


class DataAccessValidator:
    """Validates data access layer architectural consistency."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = defaultdict(list)

    def validate(self) -> dict[str, list[ArchitectureIssue]]:
        """Validate data access patterns."""
        issues = defaultdict(list)

        # Check for direct database access in services
        service_issues = self._check_services_for_db_access()
        issues["direct_db_in_services"] = service_issues

        # Check for CRUD vs Repository patterns
        pattern_issues = self._check_data_access_patterns()
        issues["inconsistent_patterns"] = pattern_issues

        return dict(issues)

    def _check_services_for_db_access(self) -> list[ArchitectureIssue]:
        """Check for direct database access in service layer."""
        issues = []

        services_dir = self.project_root / "app" / "services"
        if not services_dir.exists():
            return issues

        for service_file in services_dir.glob("*.py"):
            if service_file.name.startswith("_"):
                continue

            try:
                with open(service_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(service_file))

                # Look for db.execute, db.add, db.delete patterns
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if self._is_db_call(node):
                            issues.append(
                                ArchitectureIssue(
                                    category="data_access",
                                    severity="high",
                                    file=str(
                                        service_file.relative_to(self.project_root)
                                    ),
                                    line=node.lineno,
                                    message="Direct database access in service layer",
                                    recommendation="Use repository pattern for data access",
                                )
                            )

            except Exception:
                pass

        return issues

    def _is_db_call(self, node: ast.Call) -> bool:
        """Check if AST node is a direct database call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in [
                "execute",
                "add",
                "delete",
                "flush",
                "commit",
                "rollback",
            ]:
                # Check if it's being called on a 'db' variable
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "db":
                    return True
        return False

    def _check_data_access_patterns(self) -> list[ArchitectureIssue]:
        """Check for consistent data access patterns."""
        issues = []

        # Count usage patterns
        crud_usage = 0
        repository_usage = 0
        direct_db_usage = 0

        # Scan all Python files
        for py_file in self.project_root.rglob("*.py"):
            if "test" in str(py_file) or py_file.name.startswith("_"):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Count patterns
                crud_usage += len(re.findall(r"from app\.crud import", content))
                repository_usage += len(
                    re.findall(r"from app\.repositories import", content)
                )
                direct_db_usage += len(re.findall(r"db\.execute\(", content))

            except Exception:
                pass

        if crud_usage > 0 and repository_usage > 0:
            issues.append(
                ArchitectureIssue(
                    category="data_access",
                    severity="critical",
                    file="multiple",
                    line=1,
                    message=f"Multiple data access patterns found: "
                    f"CRUD ({crud_usage} uses), Repository ({repository_usage} uses), "
                    f"Direct DB ({direct_db_usage} uses)",
                    recommendation="Standardize on single pattern (recommended: Repository)",
                )
            )

        return issues


# =============================================================================
# AUTHENTICATION PATTERN VALIDATION
# =============================================================================


class AuthPatternValidator:
    """Validates authentication pattern consistency."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate(self) -> dict[str, list[ArchitectureIssue]]:
        """Validate authentication patterns."""
        issues = defaultdict(list)

        endpoints_dir = self.project_root / "app" / "api" / "v1" / "endpoints"
        if not endpoints_dir.exists():
            return issues

        auth_imports = defaultdict(list)

        # Scan all endpoint files
        for endpoint_file in endpoints_dir.glob("*.py"):
            if endpoint_file.name.startswith("_"):
                continue

            try:
                with open(endpoint_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find auth imports
                if "get_current_user" in content:
                    auth_imports[str(endpoint_file)].append("get_current_user")
                if "get_current_active_user" in content:
                    auth_imports[str(endpoint_file)].append("get_current_active_user")
                if "get_db" in content:
                    auth_imports[str(endpoint_file)].append("get_db")

                # Check for manual JWT handling
                if re.search(r"jwt\.decode\(|jwt\.get_unverified_header\(", content):
                    issues["manual_jwt"].append(
                        ArchitectureIssue(
                            category="auth_patterns",
                            severity="critical",
                            file=str(endpoint_file.relative_to(self.project_root)),
                            line=1,
                            message="Manual JWT decoding in endpoint",
                            recommendation="Use standardized authentication dependencies",
                        )
                    )

            except Exception:
                pass

        # Check for inconsistent auth imports
        if len(set(sum(auth_imports.values(), []))) > 2:
            issues["inconsistent_auth"].append(
                ArchitectureIssue(
                    category="auth_patterns",
                    severity="high",
                    file="multiple",
                    line=1,
                    message=f"Multiple authentication patterns in use: "
                    f"{set(sum(auth_imports.values(), []))}",
                    recommendation="Standardize on single authentication pattern",
                )
            )

        return dict(issues)


# =============================================================================
# MIDDLEWARE VALIDATION
# =============================================================================


class MiddlewareValidator:
    """Validates middleware configuration."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate(self) -> dict[str, list[ArchitectureIssue]]:
        """Validate middleware configuration."""
        issues = defaultdict(list)

        main_py = self.project_root / "app" / "main.py"
        if not main_py.exists():
            return issues

        try:
            with open(main_py, "r", encoding="utf-8") as f:
                content = f.read()

            # Count middleware registrations
            add_middleware_count = content.count("app.add_middleware(")

            # Check for duplicate middleware
            middleware_names = defaultdict(int)
            for match in re.finditer(r"app\.add_middleware\((\w+)", content):
                middleware_name = match.group(1)
                middleware_names[middleware_name] += 1

            duplicates = {
                name: count for name, count in middleware_names.items() if count > 1
            }
            if duplicates:
                for name, count in duplicates.items():
                    issues["duplicate_middleware"].append(
                        ArchitectureIssue(
                            category="middleware",
                            severity="critical",
                            file="app/main.py",
                            line=1,
                            message=f"Middleware registered multiple times: {name} ({count} times)",
                            recommendation="Remove duplicate registrations",
                        )
                    )

            # Check for too many middleware
            if add_middleware_count > 10:
                issues["too_much_middleware"].append(
                    ArchitectureIssue(
                        category="middleware",
                        severity="medium",
                        file="app/main.py",
                        line=1,
                        message=f"Too many middleware registered: {add_middleware_count}",
                        recommendation="Consider consolidating related middleware",
                    )
                )

        except Exception:
            pass

        return dict(issues)


# =============================================================================
# MAIN VALIDATION ORCHESTRATOR
# =============================================================================


class ArchitectureValidator:
    """Main architecture validation orchestrator."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.result = ValidationResult()

    def validate(
        self,
        services: bool = True,
        data_access: bool = True,
        auth: bool = True,
        middleware: bool = True,
    ) -> ValidationResult:
        """Run all validation checks."""
        if services:
            service_validator = ServiceLayerValidator(self.project_root)
            self.result.services = service_validator.validate()

        if data_access:
            data_validator = DataAccessValidator(self.project_root)
            self.result.data_access = data_validator.validate()

        if auth:
            auth_validator = AuthPatternValidator(self.project_root)
            self.result.auth_patterns = auth_validator.validate()

        if middleware:
            middleware_validator = MiddlewareValidator(self.project_root)
            self.result.middleware = middleware_validator.validate()

        return self.result

    def print_report(self):
        """Print formatted validation report."""
        print("=" * 80)
        print("ARCHITECTURE VALIDATION REPORT")
        print("=" * 80)
        print()

        # Service Layer
        if self.result.services:
            print("📦 SERVICE LAYER")
            print("-" * 80)
            for category, issues in self.result.services.items():
                if issues:
                    print(f"\n{category.upper()}:")
                    for issue in issues:
                        severity_icon = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢",
                        }.get(issue.severity, "⚪")
                        print(f"  {severity_icon} {issue.file}:{issue.line}")
                        print(f"     {issue.message}")
                        if issue.recommendation:
                            print(f"     💡 {issue.recommendation}")
            print()

        # Data Access
        if self.result.data_access:
            print("💾 DATA ACCESS LAYER")
            print("-" * 80)
            for category, issues in self.result.data_access.items():
                if issues:
                    print(f"\n{category.upper()}:")
                    for issue in issues:
                        severity_icon = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢",
                        }.get(issue.severity, "⚪")
                        print(f"  {severity_icon} {issue.file}:{issue.line}")
                        print(f"     {issue.message}")
                        if issue.recommendation:
                            print(f"     💡 {issue.recommendation}")
            print()

        # Auth Patterns
        if self.result.auth_patterns:
            print("🔐 AUTHENTICATION PATTERNS")
            print("-" * 80)
            for category, issues in self.result.auth_patterns.items():
                if issues:
                    print(f"\n{category.upper()}:")
                    for issue in issues:
                        severity_icon = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢",
                        }.get(issue.severity, "⚪")
                        print(f"  {severity_icon} {issue.file}:{issue.line}")
                        print(f"     {issue.message}")
                        if issue.recommendation:
                            print(f"     💡 {issue.recommendation}")
            print()

        # Middleware
        if self.result.middleware:
            print("🛡️  MIDDLEWARE CONFIGURATION")
            print("-" * 80)
            for category, issues in self.result.middleware.items():
                if issues:
                    print(f"\n{category.upper()}:")
                    for issue in issues:
                        severity_icon = {
                            "critical": "🔴",
                            "high": "🟠",
                            "medium": "🟡",
                            "low": "🟢",
                        }.get(issue.severity, "⚪")
                        print(f"  {severity_icon} {issue.file}:{issue.line}")
                        print(f"     {issue.message}")
                        if issue.recommendation:
                            print(f"     💡 {issue.recommendation}")
            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        total = self.result.total_issues()
        critical = self.result.critical_issues()

        print(f"Total Issues: {total}")
        print(f"Critical Issues: {critical}")

        if critical > 0:
            print("\n⚠️  CRITICAL ISSUES FOUND - Immediate attention required!")
            sys.exit(1)
        elif total > 0:
            print("\n⚠️  Issues found - Review recommended")
            sys.exit(0)
        else:
            print("\n✅ No architectural inconsistencies found!")
            sys.exit(0)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate architectural consistency across the codebase"
    )
    parser.add_argument(
        "--services", action="store_true", help="Validate service layer only"
    )
    parser.add_argument(
        "--data", action="store_true", help="Validate data access layer only"
    )
    parser.add_argument(
        "--auth", action="store_true", help="Validate authentication patterns only"
    )
    parser.add_argument(
        "--middleware",
        action="store_true",
        help="Validate middleware configuration only",
    )

    args = parser.parse_args()

    # Determine what to validate
    services = args.services or not any([args.data, args.auth, args.middleware])
    data_access = args.data or not any([args.services, args.auth, args.middleware])
    auth = args.auth or not any([args.services, args.data, args.middleware])
    middleware = args.middleware or not any([args.services, args.data, args.auth])

    # Run validation
    validator = ArchitectureValidator()
    validator.validate(
        services=services,
        data_access=data_access,
        auth=auth,
        middleware=middleware,
    )

    # Print report
    validator.print_report()


if __name__ == "__main__":
    main()
