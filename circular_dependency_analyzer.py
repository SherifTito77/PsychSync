#!/usr/bin/env python3
"""
Circular Dependency Analyzer for PsychSync Codebase
Analyzes Python files to detect circular import dependencies
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import re


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.imports: Set[str] = set()
        self.relative_imports: Set[str] = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            if node.level > 0:
                # Relative import
                self.relative_imports.add(f"{'.' * node.level}{node.module}")
            else:
                # Absolute import from module
                self.imports.add(node.module)
        self.generic_visit(node)


class CircularDependencyAnalyzer:
    """Analyzes circular dependencies in Python codebase"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.module_map: Dict[str, Path] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.circular_dependencies: List[List[str]] = []

    def build_module_map(self):
        """Build mapping from module names to file paths"""
        python_files = list(self.root_dir.rglob("*.py"))

        for file_path in python_files:
            # Skip __pycache__ and test files for now
            if "__pycache__" in str(file_path):
                continue

            # Calculate module path relative to root_dir
            relative_path = file_path.relative_to(self.root_dir)
            module_parts = list(relative_path.parts[:-1])  # Exclude .py extension

            if file_path.name == "__init__.py":
                # This is a package directory
                module_name = ".".join(module_parts) if module_parts else file_path.parent.name
            else:
                # This is a regular module
                module_name = ".".join(module_parts + [file_path.stem])

            self.module_map[module_name] = file_path
            self.dependency_graph[module_name] = set()

    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            visitor = ImportVisitor(file_path)
            visitor.visit(tree)

            imports = set()

            # Convert imports to module names
            for imp in visitor.imports:
                if imp.startswith('app.'):
                    imports.add(imp)
                elif '.' in imp and not imp.startswith('.'):
                    # Handle imports like 'core.database' -> 'app.core.database'
                    if any(part in ['core', 'api', 'services', 'db', 'schemas', 'middleware', 'utils'] for part in imp.split('.')):
                        imports.add(f"app.{imp}")

            # Handle relative imports
            for rel_imp in visitor.relative_imports:
                # Calculate absolute module path for relative import
                current_module_parts = self.get_module_name_from_path(file_path).split('.')

                if rel_imp == '.':
                    imports.add(".".join(current_module_parts[:-1]) if current_module_parts else "")
                else:
                    level = rel_imp.count('.')
                    base_parts = current_module_parts[:-level] if level > 0 else current_module_parts

                    if rel_imp[level:]:
                        module_part = rel_imp[level:]
                        if module_part:
                            full_module = ".".join(base_parts + [module_part])
                        else:
                            full_module = ".".join(base_parts)
                    else:
                        full_module = ".".join(base_parts) if base_parts else ""

                    if full_module.startswith('app'):
                        imports.add(full_module)

            return imports

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return set()

    def get_module_name_from_path(self, file_path: Path) -> str:
        """Get module name from file path"""
        relative_path = file_path.relative_to(self.root_dir)
        module_parts = list(relative_path.parts[:-1])

        if file_path.name == "__init__.py":
            return ".".join(module_parts) if module_parts else "app"
        else:
            return ".".join(module_parts + [file_path.stem])

    def build_dependency_graph(self):
        """Build the dependency graph"""
        for module_name, file_path in self.module_map.items():
            imports = self.extract_imports(file_path)

            # Only keep imports that are in our module map
            valid_imports = {imp for imp in imports if imp in self.module_map}
            self.dependency_graph[module_name] = valid_imports

    def find_circular_dependencies(self):
        """Find all circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self.circular_dependencies.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, []):
                dfs(neighbor)

            path.pop()
            rec_stack.remove(node)

        for module in self.dependency_graph:
            if module not in visited:
                dfs(module)

    def analyze_specific_patterns(self):
        """Analyze specific problematic patterns"""
        issues = []

        # Check for services importing other services
        for module in self.module_map:
            if 'services.' in module:
                for dep in self.dependency_graph.get(module, []):
                    if 'services.' in dep and module != dep:
                        issues.append({
                            'type': 'service_importing_service',
                            'from': module,
                            'to': dep,
                            'severity': 'high'
                        })

        # Check for models importing services
        for module in self.module_map:
            if 'db.models.' in module:
                for dep in self.dependency_graph.get(module, []):
                    if 'services.' in dep:
                        issues.append({
                            'type': 'model_importing_service',
                            'from': module,
                            'to': dep,
                            'severity': 'high'
                        })

        # Check for API endpoints importing models directly
        for module in self.module_map:
            if 'api.' in module:
                for dep in self.dependency_graph.get(module, []):
                    if 'db.models.' in dep:
                        issues.append({
                            'type': 'api_importing_model_directly',
                            'from': module,
                            'to': dep,
                            'severity': 'medium'
                        })

        # Check for config importing business logic
        for module in self.module_map:
            if 'core.config' in module:
                for dep in self.dependency_graph.get(module, []):
                    if any(x in dep for x in ['services.', 'api.', 'db.models.']):
                        issues.append({
                            'type': 'config_importing_business_logic',
                            'from': module,
                            'to': dep,
                            'severity': 'high'
                        })

        return issues

    def generate_report(self) -> str:
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("CIRCULAR DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Root Directory: {self.root_dir}")
        report.append(f"Total Python Files Analyzed: {len(self.module_map)}")
        report.append(f"Total Dependencies Found: {sum(len(deps) for deps in self.dependency_graph.values())}")
        report.append("")

        # Circular Dependencies
        if self.circular_dependencies:
            report.append(f"FOUND {len(self.circular_dependencies)} CIRCULAR DEPENDENCIES:")
            report.append("-" * 60)

            for i, cycle in enumerate(self.circular_dependencies, 1):
                report.append(f"\n{i}. Circular Dependency Chain:")
                for j, module in enumerate(cycle):
                    arrow = " -> " if j < len(cycle) - 1 else ""
                    report.append(f"   {module}{arrow}")
        else:
            report.append("NO CIRCULAR DEPENDENCIES FOUND ✓")

        report.append("")

        # Specific Issues
        issues = self.analyze_specific_patterns()
        if issues:
            report.append(f"FOUND {len(issues)} SPECIFIC ARCHITECTURAL ISSUES:")
            report.append("-" * 60)

            issue_types = {}
            for issue in issues:
                issue_type = issue['type']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)

            for issue_type, type_issues in issue_types.items():
                report.append(f"\n{issue_type.replace('_', ' ').title()} ({len(type_issues)} instances):")
                for issue in type_issues[:5]:  # Show first 5 examples
                    report.append(f"   {issue['from']} -> {issue['to']}")
                if len(type_issues) > 5:
                    report.append(f"   ... and {len(type_issues) - 5} more")
        else:
            report.append("NO SPECIFIC ARCHITECTURAL ISSUES FOUND ✓")

        return "\n".join(report)

    def suggest_solutions(self) -> str:
        """Suggest solutions for found issues"""
        solutions = []
        solutions.append("=" * 80)
        solutions.append("RECOMMENDED SOLUTIONS")
        solutions.append("=" * 80)

        if self.circular_dependencies:
            solutions.append("\nFOR CIRCULAR DEPENDENCIES:")
            solutions.append("-" * 40)

            for i, cycle in enumerate(self.circular_dependencies, 1):
                solutions.append(f"\n{i}. For cycle: {' -> '.join(cycle)}")
                solutions.append("   Recommended Solution:")

                # Analyze the cycle to suggest specific solutions
                if len(cycle) == 2:
                    solutions.append("   - Extract common functionality into a shared utility module")
                    solutions.append("   - Use dependency injection to break the circularity")
                    solutions.append("   - Move one dependency to a separate layer")
                else:
                    solutions.append("   - Identify the weakest link in the chain")
                    solutions.append("   - Extract interfaces to decouple modules")
                    solutions.append("   - Consider moving shared functionality to a new module")

        # Solutions for specific issues
        issues = self.analyze_specific_patterns()
        if issues:
            solutions.append("\nFOR ARCHITECTURAL ISSUES:")
            solutions.append("-" * 40)

            issue_types = {}
            for issue in issues:
                issue_type = issue['type']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []

            if 'service_importing_service' in issue_types:
                solutions.append("\nService-to-Service Imports:")
                solutions.append("- Create a shared service interface or base class")
                solutions.append("- Use dependency injection container")
                solutions.append("- Move common functionality to utility modules")

            if 'model_importing_service' in issue_types:
                solutions.append("\nModel Importing Services:")
                solutions.append("- Remove service imports from models")
                solutions.append("- Use service layer to handle business logic")
                solutions.append("- Consider using domain events or signals")

            if 'api_importing_model_directly' in issue_types:
                solutions.append("\nAPI Importing Models Directly:")
                solutions.append("- Use schemas for data transfer")
                solutions.append("- Import models through service layer")
                solutions.append("- Follow repository pattern")

            if 'config_importing_business_logic' in issue_types:
                solutions.append("\nConfig Importing Business Logic:")
                solutions.append("- Keep config files pure configuration")
                solutions.append("- Use factory pattern for complex initialization")
                solutions.append("- Move business logic out of configuration")

        return "\n".join(solutions)


def main():
    """Main function to run the analysis"""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "/Users/sheriftito/Downloads/psychsync/app"

    print("Starting circular dependency analysis...")
    analyzer = CircularDependencyAnalyzer(root_dir)

    print("Building module map...")
    analyzer.build_module_map()

    print("Building dependency graph...")
    analyzer.build_dependency_graph()

    print("Finding circular dependencies...")
    analyzer.find_circular_dependencies()

    print("\nGenerating report...")
    report = analyzer.generate_report()
    print(report)

    solutions = analyzer.suggest_solutions()
    print(solutions)

    # Save reports to files
    with open("circular_dependency_report.txt", "w") as f:
        f.write(report)

    with open("circular_dependency_solutions.txt", "w") as f:
        f.write(solutions)

    print(f"\nReports saved to:")
    print(f"  - circular_dependency_report.txt")
    print(f"  - circular_dependency_solutions.txt")


if __name__ == "__main__":
    main()