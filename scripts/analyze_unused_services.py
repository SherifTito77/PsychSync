#!/usr/bin/env python3
"""
Analyze unused services in the codebase.

Identifies which service files are imported and used, which are unused,
and categorizes them for archival.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import ast

def get_all_python_files():
    """Get all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk('app'):
        # Skip __pycache__ and virtual environments
        dirs[:] = [d for d in dirs if d != '__pycache__' and d != '.venv' and d != 'venv']

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports_from_file(filepath):
    """Extract all imports from a Python file."""
    imports = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content, filename=filepath)

        for node in ast.walk(tree):
            # Import statements: import x
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])

            # Import from statements: from x import y
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

    except (SyntaxError, UnicodeDecodeError):
        # Skip files that can't be parsed
        pass

    return imports

def get_service_files():
    """Get all service files."""
    service_files = {}
    services_dir = Path('app/services')

    if not services_dir.exists():
        return service_files

    for file in services_dir.glob('*.py'):
        if file.name == '__init__.py':
            continue
        if file.name.startswith('.!'):  # Emergency/backup files
            continue

        # Extract service name from filename
        service_name = file.stem
        service_files[service_name] = str(file)

    return service_files

def analyze_service_usage():
    """Analyze which services are used and which are unused."""

    print("🔍 Analyzing service usage across codebase...\n")

    # Get all service files
    service_files = get_service_files()
    print(f"📊 Found {len(service_files)} service files\n")

    # Get all Python files
    python_files = get_all_python_files()
    print(f"📄 Analyzing {len(python_files)} Python files...\n")

    # Collect all imports
    all_imports = defaultdict(set)
    for filepath in python_files:
        imports = extract_imports_from_file(filepath)
        for imp in imports:
            all_imports[imp].add(filepath)

    # Categorize services
    used_services = {}
    unused_services = {}
    core_services = {}
    api_endpoints = {}

    for service_name, service_path in service_files.items():
        # Check if this service is imported anywhere
        is_used = False
        importers = []

        # Check for various import patterns
        patterns = [
            f'app.services.{service_name}',
            f'services.{service_name}',
            service_name
        ]

        for pattern in patterns:
            if pattern in all_imports:
                is_used = True
                importers.extend(list(all_imports[pattern]))
                break

        if is_used:
            used_services[service_name] = {
                'path': service_path,
                'imported_by': list(set(importers)),
                'import_count': len(set(importers))
            }
        else:
            unused_services[service_name] = {
                'path': service_path
            }

    # Categorize used services by frequency
    heavily_used = {k: v for k, v in used_services.items() if v['import_count'] > 10}
    moderately_used = {k: v for k, v in used_services.items() if 3 <= v['import_count'] <= 10}
    lightly_used = {k: v for k, v in used_services.items() if v['import_count'] < 3}

    return {
        'heavily_used': heavily_used,
        'moderately_used': moderately_used,
        'lightly_used': lightly_used,
        'unused': unused_services,
        'total_services': len(service_files),
        'used_count': len(used_services),
        'unused_count': len(unused_services)
    }

def print_results(results):
    """Print analysis results."""

    print("=" * 80)
    print("SERVICE USAGE ANALYSIS RESULTS")
    print("=" * 80)
    print()

    print(f"📊 SUMMARY")
    print(f"   Total Services: {results['total_services']}")
    print(f"   Used Services:  {results['used_count']} ({100*results['used_count']//results['total_services']}%)")
    print(f"   Unused Services: {results['unused_count']} ({100*results['unused_count']//results['total_services']}%)")
    print()

    print(f"🔥 HEAVILY USED SERVICES (>10 imports)")
    print(f"   Count: {len(results['heavily_used'])}")
    for service, info in sorted(results['heavily_used'].items(), key=lambda x: x[1]['import_count'], reverse=True):
        print(f"   - {service} ({info['import_count']} imports)")
    print()

    print(f"⚖️  MODERATELY USED SERVICES (3-10 imports)")
    print(f"   Count: {len(results['moderately_used'])}")
    for service, info in sorted(results['moderately_used'].items(), key=lambda x: x[1]['import_count'], reverse=True):
        print(f"   - {service} ({info['import_count']} imports)")
    print()

    print(f"❄️  LIGHTLY USED SERVICES (<3 imports)")
    print(f"   Count: {len(results['lightly_used'])}")
    for service, info in sorted(results['lightly_used'].items(), key=lambda x: x[1]['import_count'], reverse=True):
        print(f"   - {service} ({info['import_count']} imports)")
    print()

    print(f"🗑️  UNUSED SERVICES (0 imports)")
    print(f"   Count: {len(results['unused'])}")
    for service in sorted(results['unused'].keys()):
        print(f"   - {service}")
    print()

if __name__ == '__main__':
    results = analyze_service_usage()
    print_results(results)
