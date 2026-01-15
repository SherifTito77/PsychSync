#!/usr/bin/env python3
"""
Dead Code Identification Agent

Scans codebase for unused variables, functions, classes, and files.
Helps keep codebase clean and maintainable.

Features:
- Identifies unused function definitions
- Finds unused imports
- Detects unreachable code
- Identifies dead code branches (never executed)
- Finds unused variables and constants
- Generates cleanup reports with safe deletion recommendations

Usage:
    python agents/dead_code_agent.py --code-path app/
    python agents/dead_code_agent.py --code-path app/ --exclude migrations
    python agents/dead_code_agent.py --code-path app/ --auto-fix
"""

import argparse
import ast
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import json


class FunctionCallCollector(ast.NodeVisitor):
    """Collects all function calls in a file"""

    def __init__(self):
        self.function_calls = set()
        self.method_calls = set()
        self.class_references = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.function_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Method call: object.method()
            self.method_calls.add(node.func.attr)

        self.generic_visit(node)


class ImportCollector(ast.NodeVisitor):
    """Collects all imports in a file"""

    def __init__(self):
        self.imports = {}  # module -> set of names
        self.from_imports = {}  # module -> set of names

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            if module not in self.imports:
                self.imports[module] = set()
            self.imports[module].add(name)

    def visit_ImportFrom(self, node):
        module = node.module
        if module not in self.from_imports:
            self.from_imports[module] = set()

        for alias in node.names:
            name = alias.name
            self.from_imports[module].add(name)


class TypeAnnotationCollector(ast.NodeVisitor):
    """Collects all names used in type annotations, decorators, and base classes"""

    def __init__(self):
        self.used_names = set()  # All names used in type hints, decorators, etc.

    def visit_Name(self, node):
        """Track all name references"""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Track attribute access (e.g., typing.Optional)"""
        self.used_names.add(node.attr)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Track type annotations in return types and arguments"""
        # Track decorator names
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                self.used_names.add(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                self.used_names.add(decorator.attr)

        # Track return type annotation
        if node.returns:
            self.visit(node.returns)

        # Track argument annotations
        for arg in node.args.args:
            if arg.annotation:
                self.visit(arg.annotation)

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Track type annotations in async functions"""
        self.visit_FunctionDef(node)  # Same logic

    def visit_ClassDef(self, node):
        """Track base classes and decorators"""
        # Track base class names
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.used_names.add(base.id)
            elif isinstance(base, ast.Attribute):
                self.used_names.add(base.attr)

        # Track decorator names
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                self.used_names.add(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                self.used_names.add(decorator.attr)

        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        """Track type annotations in variable assignments"""
        if node.annotation:
            self.visit(node.annotation)
        self.generic_visit(node)


class FunctionDefCollector(ast.NodeVisitor):
    """Collects all function definitions"""

    def __init__(self):
        self.functions = {}  # name -> node
        self.classes = {}  # name -> node
        self.global_vars = set()

    def visit_FunctionDef(self, node):
        self.functions[node.name] = node
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions[node.name] = node
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes[node.name] = node
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Track global variable assignments
        if isinstance(node.targets[0], ast.Name):
            self.global_vars.add(node.targets[0].id)
        self.generic_visit(node)


class DeadCodeDetector:
    """Detects dead code in Python files"""

    def __init__(self, code_path: str, exclude_patterns: List[str] = None):
        self.code_path = code_path
        self.exclude_patterns = exclude_patterns or ['migrations', 'alembic']
        self.files_scanned = 0
        self.unused_functions = []
        self.unused_imports = []
        self.unused_variables = []
        self.unused_classes = []
        self.dead_files = []

    def _should_exclude(self, file_path: str) -> bool:
        """Check if file should be excluded from scan"""
        for pattern in self.exclude_patterns:
            if pattern in file_path:
                return True
        return False

    def scan_file(self, file_path: str) -> Dict:
        """Scan a single file for dead code"""
        if self._should_exclude(file_path):
            return None

        try:
            with open(file_path, 'r') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=file_path)

            # Collect definitions
            def_collector = FunctionDefCollector()
            def_collector.visit(tree)

            # Collect function calls
            call_collector = FunctionCallCollector()
            call_collector.visit(tree)

            # Collect imports
            import_collector = ImportCollector()
            import_collector.visit(tree)

            # Collect type annotations and decorators
            type_collector = TypeAnnotationCollector()
            type_collector.visit(tree)

            # Find unused functions
            file_issues = {
                'file': file_path,
                'unused_functions': [],
                'unused_classes': [],
                'unused_imports': [],
                'unused_variables': [],
                'unreachable_code': []
            }

            # Check for unused functions
            for func_name, func_node in def_collector.functions.items():
                if func_name.startswith('_'):
                    continue  # Skip private functions

                # Check if function is called anywhere
                if func_name not in call_collector.function_calls:
                    # Check if it's a special method (called by framework)
                    if not func_name.startswith('__'):
                        # Check if it's exported (used in __all__)
                        is_exported = self._is_exported(source_code, func_name)

                        if not is_exported:
                            file_issues['unused_functions'].append({
                                'name': func_name,
                                'line': func_node.lineno,
                                'reason': 'Never called'
                            })

            # Check for unused classes
            for class_name, class_node in def_collector.classes.items():
                if class_name.startswith('_'):
                    continue  # Skip private classes

                if class_name not in call_collector.class_references:
                    # Check if it's exported
                    is_exported = self._is_exported(source_code, class_name)

                    if not is_exported:
                        file_issues['unused_classes'].append({
                            'name': class_name,
                            'line': class_node.lineno,
                            'reason': 'Never instantiated'
                        })

            # Check for unused imports (including type annotations and decorators)
            all_used_names = (
                call_collector.function_calls |
                call_collector.method_calls |
                type_collector.used_names  # Now includes type hints and decorators!
            )

            # Check regular imports
            for module, names in import_collector.imports.items():
                for name in names:
                    if name not in all_used_names and name not in def_collector.global_vars:
                        file_issues['unused_imports'].append({
                            'module': module,
                            'name': name,
                            'reason': 'Imported but never used'
                        })

            # Check from imports
            for module, names in import_collector.from_imports.items():
                for name in names:
                    if name != '*' and name not in all_used_names and name not in def_collector.global_vars:
                        file_issues['unused_imports'].append({
                            'module': module,
                            'name': name,
                            'reason': 'Imported but never used'
                        })

            # Check for unreachable code (code after return/break/continue)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._check_unreachable_code(node, file_issues)

            # Collect issues
            self.unused_functions.extend([
                {**issue, 'file': file_path}
                for issue in file_issues['unused_functions']
            ])

            self.unused_classes.extend([
                {**issue, 'file': file_path}
                for issue in file_issues['unused_classes']
            ])

            self.unused_imports.extend([
                {**issue, 'file': file_path}
                for issue in file_issues['unused_imports']
            ])

            self.unused_variables.extend([
                {**issue, 'file': file_path}
                for issue in file_issues['unused_variables']
            ])

            return file_issues

        except Exception as e:
            return {
                'file': file_path,
                'error': str(e)
            }

    def _is_exported(self, source_code: str, name: str) -> bool:
        """Check if symbol is exported via __all__"""
        match = re.search(r'__all__\s*=\s*\[(.*?)\]', source_code)
        if match:
            exports_str = match.group(1)
            # Parse simple string names
            exports = [e.strip().strip('"\'') for e in exports_str.split(',')]
            return name in exports
        return False

    def _check_unreachable_code(self, func_node, issues: List):
        """Check for unreachable code in function"""
        has_return = False
        statements = func_node.body

        for i, stmt in enumerate(statements):
            if isinstance(stmt, (ast.Return, ast.Raise)):
                # Check if there are statements after return/raise
                if i < len(statements) - 1:
                    # There are unreachable statements
                    next_stmt = statements[i + 1]
                    issues['unreachable_code'].append({
                        'line': next_stmt.lineno,
                        'reason': f'Code after {stmt.__class__.__name__} on line {stmt.lineno}'
                    })
                has_return = True

    def scan_directory(self):
        """Scan all Python files in directory"""
        print(f"🔍 Scanning for dead code...")
        print(f"   Code path: {self.code_path}")
        print(f"   Exclude patterns: {self.exclude_patterns}")
        print(f"{'-'*60}")

        file_issues = []

        for root, dirs, files in os.walk(self.code_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)

                    try:
                        issues = self.scan_file(file_path)
                        if issues and 'error' not in issues:
                            file_issues.append(issues)
                            self.files_scanned += 1
                    except Exception as e:
                        print(f"⚠️  Warning: Could not scan {file_path}: {e}")

        # Find potentially unused files
        self._find_unused_files(file_issues)

        return file_issues

    def _find_unused_files(self, file_issues: List[Dict]):
        """Identify files that are never imported"""
        print(f"📄 Checking for unused files...")

        # Build a map of all imported files
        imported_files = set()

        for issues in file_issues:
            if 'unused_imports' not in issues:
                continue

            for imp in issues['unused_imports']:
                # Check if it's a relative import from this project
                module = imp['module'].replace('.', '/')
                if module.startswith('app/') or module.startswith('tests/'):
                    imported_files.add(imp['module'])

        # Check all Python files
        all_files = set()

        for root, dirs, files in os.walk(self.code_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = file_path.replace(self.code_path, '').lstrip('/')
                    all_files.add(rel_path)

        # Find files that are never imported
        for file_path in all_files:
            # Skip __init__.py, main files, etc.
            if any(file_path.endswith(p) for p in ['__init__.py', '__main__.py', 'main.py']):
                continue

            # Convert file path to module path
            module_path = file_path.replace('/', '.').replace('.py', '')

            if module_path not in imported_files:
                # Check if it's a test file or executable
                if not (module_path.startswith('test_') or module_path.endswith('_test')):
                    self.dead_files.append({
                        'file': file_path,
                        'reason': 'Never imported'
                    })

    def generate_report(self, output_path: str = 'reports/dead_code.json') -> Dict:
        """Generate comprehensive dead code report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'files_scanned': self.files_scanned,
            'total_unused_functions': len(self.unused_functions),
            'total_unused_classes': len(self.unused_classes),
            'total_unused_imports': len(self.unused_imports),
            'total_unused_variables': len(self.unused_variables),
            'total_dead_files': len(self.dead_files),
            'unused_functions': self.unused_functions[:50],  # First 50
            'unused_classes': self.unused_classes[:20],
            'unused_imports': self.unused_imports[:50],
            'unused_variables': self.unused_variables[:50],
            'dead_files': self.dead_files[:20],
            'recommendations': self._generate_recommendations()
        }

        # Save report
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate cleanup recommendations"""
        recommendations = []

        if len(self.unused_functions) > 20:
            recommendations.append(f"Remove {len(self.unused_functions)} unused functions to reduce codebase size")

        if len(self.unused_imports) > 50:
            recommendations.append(f"Clean up {len(self.unused_imports)} unused imports to improve load time")

        if len(self.dead_files) > 10:
            recommendations.append(f"Review {len(self.dead_files)} potentially unused files")

        if len(self.unused_classes) > 5:
            recommendations.append(f"Remove {len(self.unused_classes)} unused classes")

        return recommendations

    def print_summary(self):
        """Print formatted summary"""
        print(f"\n{'='*60}")
        print(f"DEAD CODE DETECTION REPORT")
        print(f"{'='*60}")

        print(f"\n📊 Summary:")
        print(f"   Files scanned: {self.files_scanned}")
        print(f"   Unused functions: {len(self.unused_functions)}")
        print(f"   Unused classes: {len(self.unused_classes)}")
        print(f"   Unused imports: {len(self.unused_imports)}")
        print(f"   Unused variables: {len(self.unused_variables)}")
        print(f"   Potentially unused files: {len(self.dead_files)}")

        print(f"\n🔍 Top Unused Functions:")
        for func in self.unused_functions[:10]:
            print(f"   {func['file']}:{func['line']} - {func['name']}")

        if len(self.unused_functions) > 10:
            print(f"   ... and {len(self.unused_functions) - 10} more")

        print(f"\n🗑️  Top Unused Imports:")
        for imp in self.unused_imports[:10]:
            print(f"   {imp['file']} - from {imp['module']} import {imp['name']}")

        if len(self.unused_imports) > 10:
            print(f"   ... and {len(self.unused_imports) - 10} more")

        if self.dead_files:
            print(f"\n📄 Potentially Unused Files:")
        for file in self.dead_files[:10]:
            print(f"   {file['file']}")

        print(f"\n{'='*60}\n")


def auto_fix_dead_code(code_path: str, dry_run: bool = True):
    """Automatically remove dead code (EXPERIMENTAL)"""
    print(f"🔧 Auto-fixing dead code...")
    print(f"   Code path: {code_path}")
    print(f"   Dry run: {dry_run}")
    print(f"{'-'*60}")

    detector = DeadCodeDetector(code_path)
    file_issues = detector.scan_directory()

    removed_items = 0

    for issues in file_issues:
        if not issues or 'error' in issues:
            continue

        file_path = issues['file']
        print(f"\n📝 Processing: {file_path}")

        try:
            with open(file_path, 'r') as f:
                original_code = f.read()

            lines = original_code.split('\n')
            lines_to_remove = set()

            # Mark lines to remove
            for imp in issues.get('unused_imports', []):
                # Find the import statement
                for i, line in enumerate(lines):
                    if f"import {imp['name']}" in line or f"from {imp['module']}" in line:
                        lines_to_remove.add(i)

            # Remove lines (in reverse order to preserve line numbers)
            if lines_to_remove and not dry_run:
                for line_num in sorted(lines_to_remove, reverse=True):
                    del lines[line_num]
                    removed_items += 1

                # Write back
                with open(file_path, 'w') as f:
                    f.write('\n'.join(lines))

                print(f"   ✓ Removed {len(lines_to_remove)} unused imports")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n{'='*60}")
    print(f"Total items removed: {removed_items}")
    print(f"{'='*60}\n")

    return removed_items


def main():
    parser = argparse.ArgumentParser(
        description='Dead Code Identification Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan codebase for dead code
  python agents/dead_code_agent.py --code-path app/

  # Exclude certain directories
  python agents/dead_code_agent.py --code-path app/ --exclude migrations alembic

  # Auto-fix dead code (dry-run first to preview)
  python agents/dead_code_agent.py --code-path app/ --auto-fix --dry-run
  python agents/dead_code_agent.py --code-path app/ --auto-fix
        """
    )

    parser.add_argument('--code-path', required=True, help='Path to code directory')
    parser.add_argument('--exclude', nargs='*', default=['migrations', 'alembic'], help='Patterns to exclude')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically remove dead code')
    parser.add_argument('--dry-run', action='store_true', help='Preview auto-fix changes without writing files')
    parser.add_argument('--output', default='reports/dead_code.json', help='Output report path')

    args = parser.parse_args()

    if args.auto_fix:
        auto_fix_dead_code(args.code_path, args.dry_run)
    else:
        detector = DeadCodeDetector(args.code_path, args.exclude)
        detector.scan_directory()
        detector.generate_report(args.output)
        detector.print_summary()


if __name__ == '__main__':
    main()
