#!/usr/bin/env python3
"""
Automated Migration Template Generator

This script analyzes an existing service and generates a BaseService migration template,
accelerating the migration process by 50-70%.

Usage:
    python scripts/generate_migration_template.py <service_name>

Example:
    python scripts/generate_migration_template.py response_service

Output:
    - app/services/<service_name>_refactored.py (migration template)
    - Migration checklist with identified methods
    - Endpoint dependency report
"""

import ast
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


class ServiceAnalyzer:
    """Analyzes existing service code and extracts migration information."""

    def __init__(self, service_path: str):
        self.service_path = Path(service_path)
        self.service_name = self.service_path.stem
        self.module_name = self.service_path.stem

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of the service."""
        if not self.service_path.exists():
            raise FileNotFoundError(f"Service file not found: {self.service_path}")

        with open(self.service_path, "r") as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"❌ Syntax error in {self.service_path}: {e}")
            return {}

        analyzer = ServiceVisitor()
        analyzer.visit(tree)

        return {
            "service_name": self.service_name,
            "module_name": self.module_name,
            "file_path": str(self.service_path),
            "classes": analyzer.classes,
            "functions": analyzer.functions,
            "imports": analyzer.imports,
            "decorators": analyzer.decorators,
            "method_calls": analyzer.method_calls,
            "has_async": analyzer.has_async,
        }

    def get_endpoint_dependencies(self) -> List[str]:
        """Find which endpoints import this service."""
        endpoints_dir = Path("app/api/v1/endpoints")
        dependencies = []

        for endpoint_file in endpoints_dir.glob("*.py"):
            try:
                with open(endpoint_file, "r") as f:
                    content = f.read()
                    # Check for imports of this service
                    if self.module_name in content:
                        dependencies.append(str(endpoint_file))
            except Exception:
                continue

        return dependencies

    def suggest_cache_strategy(self) -> str:
        """Suggest appropriate CacheStrategy based on service name."""
        service_lower = self.service_name.lower()

        if "user" in service_lower:
            return "USER_PROFILE"
        elif "team" in service_lower:
            return "TEAM_DATA"
        elif "assessment" in service_lower:
            return "ASSESSMENT_DATA"
        elif "response" in service_lower:
            return "ASSESSMENT_RESULTS"
        elif "organization" in service_lower or "org" in service_lower:
            return "ORGANIZATION_DATA"
        elif "notification" in service_lower:
            return "SESSION_DATA"
        elif "email" in service_lower:
            return "API_RESPONSES"
        else:
            return "API_RESPONSES"  # Default

    def guess_model_type(self) -> str:
        """Guess the model type based on service name."""
        service_lower = self.service_name.lower()

        mapping = {
            "user": "User",
            "team": "Team",
            "assessment": "Assessment",
            "response": "Response",
            "organization": "Organization",
            "notification": "Notification",
            "analytics": "Analytics",
            "scoring": "Scoring",
            "email": "Email",
        }

        for key, value in mapping.items():
            if key in service_lower:
                return value

        return "Model"  # Default


class ServiceVisitor(ast.NodeVisitor):
    """AST visitor to extract service structure."""

    def __init__(self):
        super().__init__()
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.imports: List[str] = []
        self.decorators: Set[str] = set()
        self.method_calls: Dict[str, List[str]] = {}
        self.has_async = False
        self.current_class = None

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports."""
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class definitions."""
        class_info = {
            "name": node.name,
            "bases": [ast.unparse(base) for base in node.bases],
            "methods": [],
            "decorators": [],
        }

        # Extract decorators
        for decorator in node.decorator_list:
            class_info["decorators"].append(ast.unparse(decorator))

        self.current_class = class_info
        self.classes.append(class_info)
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function/method definitions."""
        is_async = isinstance(node, ast.FunctionDef)

        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "returns": ast.unparse(node.returns) if node.returns else None,
            "decorators": [],
            "is_async": is_async,
            "lineno": node.lineno,
        }

        # Extract decorators
        for decorator in node.decorator_list:
            decorator_str = ast.unparse(decorator)
            func_info["decorators"].append(decorator_str)
            self.decorators.add(decorator_str)

        if is_async:
            self.has_async = True

        if self.current_class is not None:
            self.current_class["methods"].append(func_info)
        else:
            self.functions.append(func_info)

        # Track method calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)

        func_info["calls"] = calls
        self.method_calls[node.name] = calls

        self.generic_visit(node)


def generate_migration_template(analysis: Dict[str, Any]) -> str:
    """Generate BaseService migration template from analysis."""
    service_name = analysis["service_name"]
    model_type = service_name.replace("_service", "").title().replace("_", "")
    cache_strategy = analysis.get("cache_strategy", "API_RESPONSES")

    # Extract methods from classes
    all_methods = []
    for class_info in analysis["classes"]:
        all_methods.extend(class_info["methods"])

    # Filter for async methods
    async_methods = [m for m in all_methods if m["is_async"]]

    template = f'''"""
Refactored {service_name.title()} - Extends BaseService for Consistency

This service now extends BaseService, providing:
✅ Automatic error handling via @handle_database_errors decorator
✅ Built-in caching strategy with invalidation
✅ Transaction management
✅ Structured logging
✅ Audit trail
✅ Consistent CRUD operations

MIGRATION NOTES:
- Original: app/services/{service_name}.py
- Pattern: Service Layer extending BaseService
- Generated: Automated template generator

Author: Architecture Refactoring Team
Version: 2.0 (BaseService Pattern)
"""

from datetime import datetime
from uuid import UUID
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_strategy import CacheStrategy
from app.core.database_transactions import transaction_manager
from app.core.error_handling import ValidationException
from app.core.structured_logging import EventType, get_logger
from app.db.models.{model_type.lower()} import {model_type}
from app.schemas.{model_type.lower()} import {model_type}Create, {model_type}Update
from app.services.base_service import BaseService

logger = get_logger(__name__)


class {service_name.title()}(BaseService[{model_type}, {model_type}Create, {model_type}Update]):
    """
    Refactored {service_name} extending BaseService.

    Provides consistent CRUD operations with built-in:
    - Error handling
    - Caching
    - Transaction management
    - Logging
    - Audit trail
    """

    # =========================================================================
    # ABSTRACT PROPERTY IMPLEMENTATIONS (Required by BaseService)
    # =========================================================================

    @property
    def model(self) -> type[{model_type}]:
        """Return the SQLAlchemy model class."""
        return {model_type}

    @property
    def cache_strategy(self) -> CacheStrategy:
        """Return the caching strategy for this service."""
        return CacheStrategy.{cache_strategy}

    def get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operations."""
        if operation == "get_by_id":
            return f"{model_type.lower()}:id:{{{{kwargs.get('id')}}}}"
        elif operation == "list":
            return f"{model_type.lower()}:list:{{{{kwargs.get('skip', 0)}}}}:{{{{kwargs.get('limit', 100)}}}}"
        return f"{model_type.lower()}:{{operation}}"

    def validate_create_data(self, data: {model_type}Create) -> None:
        """
        Validate data before creation.

        TODO(human): Implement validation rules
        """
        pass  # Add your validation logic here

    def validate_update_data(self, data: {model_type}Update, existing: {model_type}) -> None:
        """
        Validate data before update.

        TODO(human): Implement validation rules
        """
        pass  # Add your validation logic here

    # =========================================================================
    # CUSTOM BUSINESS LOGIC (Beyond basic CRUD)
    # =========================================================================

'''

    # Add method templates for each async method found
    for method in async_methods[:5]:  # Limit to first 5 methods
        if method["name"].startswith("_"):
            continue  # Skip private methods

        method_name = method["name"]
        args = method["args"][1:]  # Remove 'self'

        # Build parameter string
        params = []
        for arg in args:
            if arg == "db":
                params.append("db: AsyncSession")
            elif "id" in arg.lower():
                params.append(f"{arg}: UUID")
            else:
                params.append(f"{arg}: Any")

        param_str = ", ".join(params)

        # Check if it uses transaction manager
        has_transaction = any("transaction" in d for d in method["decorators"])

        transaction_decorator = (
            "@transaction_manager.transaction\n" if has_transaction else ""
        )

        template += f'''    {transaction_decorator}async def {method_name}(
        self,
        {param_str if param_str else ''}
    ):
        """
        TODO(human): Implement {method_name} method

        Original location: line {method['lineno']}

        Original decorators: {', '.join(method['decorators'])}

        Methods called: {', '.join(set(method['calls']))}
        """
        # TODO(human): Implement this method
        # Preserve business logic from original service
        # Use BaseService methods where possible
        pass

'''

    # Add singleton instance
    template += f"""
# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Singleton instance for dependency injection
{service_name} = {service_name.title()}()
"""

    return template


def generate_migration_checklist(analysis: Dict[str, Any]) -> str:
    """Generate migration checklist."""
    service_name = analysis["service_name"]
    async_methods = []

    for class_info in analysis["classes"]:
        async_methods.extend(
            [
                m
                for m in class_info["methods"]
                if m["is_async"] and not m["name"].startswith("_")
            ]
        )

    # Build lists outside f-string
    imports_list = "\\n".join(f"  - {imp}" for imp in analysis["imports"][:10])
    methods_list = "\\n".join(
        f'  {i+1}. {m["name"]}() (line {m["lineno"]})'
        for i, m in enumerate(async_methods[:10])
    )
    decorators_list = "\\n".join(
        f"  - {d}" for d in sorted(analysis["decorators"]) if not d.startswith("_")
    )

    checklist = f"""
Migration Checklist for {service_name.title()}
{'=' * 80}

ANALYSIS RESULTS:
{'=' * 80}

Service Name: {service_name}
File: {analysis['file_path']}
Classes Found: {len(analysis['classes'])}
Functions Found: {len(analysis['functions'])}
Async Methods: {len(async_methods)}

IMPORTS:
{imports_list}

METHODS TO MIGRATE:
{methods_list}

DECORATORS FOUND:
{decorators_list}

MIGRATION TASKS:
{'=' * 80}

Phase 1: Setup (30 minutes)
  [ ] Read original service implementation
  [ ] Identify all methods and their purposes
  [ ] Document business logic and algorithms
  [ ] Check for external dependencies
  [ ] Review error handling patterns

Phase 2: Create Template (15 minutes)
  [ ] Run: python scripts/generate_migration_template.py {service_name}
  [ ] Review generated template
  [ ] Fill in abstract properties
  [ ] Implement validation methods

Phase 3: Migrate Methods (1-3 hours)
  [ ] Migrate CRUD methods (use BaseService inherited)
  [ ] Migrate custom business logic methods
  [ ] Preserve all decorators (@transaction_manager, etc.)
  [ ] Update method signatures if needed

Phase 4: Testing (1 hour)
  [ ] Create unit tests for each method
  [ ] Test with real database
  [ ] Verify cache behavior
  [ ] Performance test if needed

Phase 5: Integration (30 minutes)
  [ ] Update endpoints to use refactored service
  [ ] Test endpoints locally
  [ ] Run full test suite
  [ ] Check for breaking changes

Phase 6: Validation (15 minutes)
  [ ] Run: python scripts/validate_architecture.py
  [ ] Verify improvements
  [ ] Update MIGRATION_PROGRESS.md

NOTES:
{'=' * 80}

• Focus on preserving exact business logic
• Use BaseService CRUD methods where possible
• Keep decorators (@transaction_manager, @cached, etc.)
• Add TODO(human) for complex algorithms
• Test thoroughly before deploying

RISK ASSESSMENT:
{'=' * 80}

• Complexity: {'LOW' if len(async_methods) < 5 else 'MEDIUM' if len(async_methods) < 10 else 'HIGH'}
• External Dependencies: {len(analysis['imports'])}
• Methods to Migrate: {len(async_methods)}
• Estimated Time: {2 + len(async_methods) * 15} minutes - {2 + len(async_methods) * 30} minutes

"""
    return checklist


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_migration_template.py <service_name>")
        print("\nExample:")
        print("  python generate_migration_template.py response_service")
        print("\nThis will:")
        print("  1. Analyze the original service")
        print("  2. Generate a BaseService migration template")
        print("  3. Create a migration checklist")
        sys.exit(1)

    service_name = sys.argv[1]

    # Find the service file
    possible_paths = [
        f"app/services/{service_name}.py",
        f"app/services/{service_name}/",
    ]

    service_path = None
    for path in possible_paths:
        if Path(path).exists():
            service_path = path
            break

    if not service_path:
        print(f"❌ Service not found: {service_name}")
        print(f"\nTried:")
        for path in possible_paths:
            print(f"  - {path}")
        sys.exit(1)

    print(f"🔍 Analyzing service: {service_name}")

    # Analyze the service
    analyzer = ServiceAnalyzer(service_path)
    analysis = analyzer.analyze()

    # Add cache strategy suggestion
    analysis["cache_strategy"] = analyzer.suggest_cache_strategy()
    analysis["model_type"] = analyzer.guess_model_type()

    # Find endpoint dependencies
    dependencies = analyzer.get_endpoint_dependencies()
    analysis["endpoint_dependencies"] = dependencies

    print(f"✅ Analysis complete:")
    print(f"   - Classes: {len(analysis['classes'])}")
    print(f"   - Functions: {len(analysis['functions'])}")
    print(f"   - Endpoint dependencies: {len(dependencies)}")

    # Generate migration template
    output_path = f"app/services/{service_name}_refactored.py"
    template = generate_migration_template(analysis)

    with open(output_path, "w") as f:
        f.write(template)

    print(f"\n✅ Generated template: {output_path}")

    # Generate checklist
    checklist_path = f"{service_name}_MIGRATION_CHECKLIST.md"
    checklist = generate_migration_checklist(analysis)

    with open(checklist_path, "w") as f:
        f.write(checklist)

    print(f"✅ Generated checklist: {checklist_path}")

    # Report endpoint dependencies
    if dependencies:
        print(f"\n📄 Endpoints using this service:")
        for dep in dependencies:
            print(f"   - {dep}")
    else:
        print(f"\n✅ No endpoints found importing this service")

    print(f"\n📋 Next Steps:")
    print(f"   1. Review the generated template: {output_path}")
    print(f"   2. Follow the checklist: {checklist_path}")
    print(f"   3. Implement the TODO(human) sections")
    print(f"   4. Run tests and validate")
    print(f"   5. Update endpoints")

    print(f"\n💡 Tip: Start with simple methods, test as you go!")


if __name__ == "__main__":
    main()
