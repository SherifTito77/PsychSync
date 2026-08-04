#!/usr/bin/env python3
"""
Test Coverage Audit Script

Analyzes the codebase to identify test coverage gaps.
Generates a report of modules that need tests.
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Set


def find_python_files(directory: str, exclude_dirs: List[str] = None) -> List[Path]:
    """Find all Python files in directory."""
    if exclude_dirs is None:
        exclude_dirs = [".venv", ".venv-py314", "__pycache__", "node_modules"]

    python_files = []
    root = Path(directory)

    for file in root.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in file.parts for excluded in exclude_dirs):
            continue

        python_files.append(file)

    return python_files


def extract_imports(file_path: Path) -> Set[str]:
    """Extract all imports from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        return imports

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return set()


def analyze_app_modules() -> Dict[str, Dict]:
    """Analyze all app modules to identify what needs testing."""
    app_dir = Path("app")

    modules_info = {}

    # Key directories to analyze
    key_dirs = [
        "domain",
        "infrastructure",
        "services",
        "api",
        "core",
        "crud",
        "schemas",
    ]

    for key_dir in key_dirs:
        dir_path = app_dir / key_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            # Get relative path
            rel_path = py_file.relative_to(app_dir)

            # Extract module path
            module_path = str(rel_path.with_suffix("")).replace("/", ".")

            # Parse the file
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                # Count classes and functions
                classes = []
                functions = []
                testable_items = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append(node.name)

                        # Count methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                if not item.name.startswith("_"):
                                    testable_items.append(
                                        {
                                            "type": "method",
                                            "name": f"{node.name}.{item.name}",
                                            "lineno": item.lineno,
                                        }
                                    )

                    elif isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):
                            functions.append(node.name)
                            testable_items.append(
                                {
                                    "type": "function",
                                    "name": node.name,
                                    "lineno": node.lineno,
                                }
                            )

                modules_info[module_path] = {
                    "path": str(rel_path),
                    "classes": classes,
                    "functions": functions,
                    "testable_items": testable_items,
                    "total_testable": len(testable_items),
                }

            except Exception as e:
                print(f"Warning: Could not parse {py_file}: {e}")

    return modules_info


def analyze_test_coverage() -> Dict[str, Dict]:
    """Analyze existing test files."""
    tests_dir = Path("tests")

    test_info = {"unit": [], "integration": [], "e2e": [], "total_tests": 0}

    if not tests_dir.exists():
        return test_info

    for test_file in tests_dir.rglob("test_*.py"):
        if test_file.name.startswith("__"):
            continue

        rel_path = test_file.relative_to(tests_dir)

        # Categorize test
        if "unit" in str(test_file):
            test_info["unit"].append(str(rel_path))
        elif "integration" in str(test_file) or "e2e" in str(test_file):
            test_info["integration"].append(str(rel_path))
        else:
            test_info["e2e"].append(str(rel_path))

        # Count test functions
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(test_file))

            test_count = sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            )

            test_info["total_tests"] += test_count

        except Exception:
            pass

    return test_info


def match_tests_to_modules(app_modules: Dict, test_info: Dict) -> Dict[str, Dict]:
    """Match test files to app modules."""
    coverage_map = {}

    for module_path, module_info in app_modules.items():
        # Look for corresponding test file
        possible_test_names = [
            f"tests/{module_path.replace('.', '/')}_test.py",
            f"tests/{module_path.replace('.', '/')}/test_{module_path.split('.')[-1]}.py",
            f"tests/unit/{module_path.replace('.', '/')}_test.py",
        ]

        test_exists = any(Path(name).exists() for name in possible_test_names)

        coverage_map[module_path] = {
            **module_info,
            "has_tests": test_exists,
            "test_files": [name for name in possible_test_names if Path(name).exists()],
        }

    return coverage_map


def generate_coverage_report():
    """Generate comprehensive coverage report."""
    print("=" * 80)
    print("PSYCHSYNC TEST COVERAGE AUDIT")
    print("=" * 80)
    print()

    # Analyze app modules
    print("📊 Analyzing application modules...")
    app_modules = analyze_app_modules()
    print(f"   Found {len(app_modules)} modules to test")

    # Analyze test files
    print("\n📝 Analyzing existing test files...")
    test_info = analyze_test_coverage()
    print(f"   Unit tests: {len(test_info['unit'])}")
    print(f"   Integration tests: {len(test_info['integration'])}")
    print(f"   E2E tests: {len(test_info['e2e'])}")
    print(f"   Total test functions: {test_info['total_tests']}")

    # Match tests to modules
    print("\n🔍 Matching tests to modules...")
    coverage_map = match_tests_to_modules(app_modules, test_info)

    # Generate statistics
    modules_with_tests = sum(1 for m in coverage_map.values() if m["has_tests"])
    modules_without_tests = len(coverage_map) - modules_with_tests
    total_testable_items = sum(m["total_testable"] for m in coverage_map.values())

    print("\n" + "=" * 80)
    print("COVERAGE SUMMARY")
    print("=" * 80)
    print(f"Total Modules: {len(coverage_map)}")
    print(
        f"Modules with Tests: {modules_with_tests} ({100 * modules_with_tests / len(coverage_map):.1f}%)"
    )
    print(f"Modules without Tests: {modules_without_tests}")
    print(f"Total Testable Items: {total_testable_items}")
    print()

    # Identify priority modules (new architecture)
    print("=" * 80)
    print("PRIORITY MODULES (New Architecture)")
    print("=" * 80)

    priority_modules = {
        "domain.services": "Domain services (business logic)",
        "domain.entities": "Domain entities",
        "domain.value_objects": "Value objects",
        "infrastructure.repositories": "Repository implementations",
        "services.assessment_processing_service": "Assessment processing service",
        "api.endpoints": "API endpoints",
    }

    for module_pattern, description in priority_modules.items():
        matching = [k for k in coverage_map.keys() if k.startswith(module_pattern)]
        if matching:
            print(f"\n{description}:")
            for module in sorted(matching):
                info = coverage_map[module]
                status = "✅" if info["has_tests"] else "❌"
                print(f"  {status} {module} ({info['total_testable']} testable items)")

    # Modules without tests
    print("\n" + "=" * 80)
    print("MODULES MISSING TESTS")
    print("=" * 80)

    missing_tests = [
        (k, v)
        for k, v in coverage_map.items()
        if not v["has_tests"] and v["total_testable"] > 0
    ]

    if missing_tests:
        # Sort by testable items (most complex first)
        missing_tests.sort(key=lambda x: x[1]["total_testable"], reverse=True)

        for module, info in missing_tests[:20]:  # Top 20
            print(f"\n❌ {module}")
            print(f"   Path: {info['path']}")
            print(f"   Testable items: {info['total_testable']}")
            if info["classes"]:
                print(f"   Classes: {', '.join(info['classes'][:5])}")
            if info["functions"]:
                print(f"   Functions: {', '.join(info['functions'][:5])}")
    else:
        print("\n🎉 All modules have tests!")

    # Save detailed report
    report_path = Path("reports/test_coverage_audit.json")
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(
            {
                "summary": {
                    "total_modules": len(coverage_map),
                    "modules_with_tests": modules_with_tests,
                    "modules_without_tests": modules_without_tests,
                    "total_testable_items": total_testable_items,
                    "test_files": {
                        "unit": len(test_info["unit"]),
                        "integration": len(test_info["integration"]),
                        "e2e": len(test_info["e2e"]),
                        "total": test_info["total_tests"],
                    },
                },
                "modules": coverage_map,
                "missing_tests": [{"module": k, **v} for k, v in missing_tests],
            },
            f,
            indent=2,
        )

    print(f"\n📄 Detailed report saved to: {report_path}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("\n1. High Priority Tests:")
    if any("domain.services" in m for m in coverage_map.keys()):
        print("   ✓ Create unit tests for all domain services")
        print("   - Use mocked repositories")
        print("   - Test business logic and validation")

    if any("infrastructure.repositories" in m for m in coverage_map.keys()):
        print("   ✓ Create integration tests for repositories")
        print("   - Test CRUD operations")
        print("   - Test custom queries and filters")

    print("\n2. Medium Priority Tests:")
    print("   ✓ API endpoint tests")
    print("   - Test request/response validation")
    print("   - Test authentication and authorization")

    print("\n3. Test Infrastructure:")
    print("   ✓ Add more test fixtures for common scenarios")
    print("   ✓ Create test data factories for complex objects")
    print("   ✓ Set up continuous coverage monitoring")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    generate_coverage_report()
