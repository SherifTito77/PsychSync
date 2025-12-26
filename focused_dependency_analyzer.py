#!/usr/bin/env python3
"""
Focused Dependency Analyzer for PsychSync Codebase
Analyzes only well-structured Python files to detect circular dependencies
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FocusedDependencyAnalyzer:
    """Analyzes circular dependencies in well-structured Python files"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.module_imports: Dict[str, Set[str]] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        self.circular_deps: List[List[str]] = []
        self.problematic_files: Set[str] = set()

    def is_well_structured_file(self, file_path: Path) -> bool:
        """Check if file is likely well-structured by basic criteria"""
        try:
            # Skip files that are too large (likely problematic)
            if file_path.stat().st_size > 100_000:  # 100KB limit
                return False

            # Read first few lines to check for obvious issues
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline() for _ in range(10)]

            # Skip files with obvious encoding issues
            for line in first_lines:
                if '\x00' in line or '\xa8' in line or '\xa1' in line:
                    return False

            return True
        except Exception:
            return False

    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """Extract imports from a well-structured file using regex"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return set()

        imports = set()

        # Extract regular imports: import module
        import_patterns = [
            r'^from\s+(app\.[\w\.]+)\s+import',
            r'^import\s+(app\.[\w\.]+)',
        ]

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            for pattern in import_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # Clean up the import
                    if 'from' in line:
                        # Handle 'from app.module import something'
                        base_module = match.split('.')[0]
                        if base_module == 'app':
                            imports.add(match)
                    else:
                        # Handle 'import app.module'
                        if match.startswith('app.'):
                            imports.add(match)

        return imports

    def get_module_name_from_path(self, file_path: Path) -> str:
        """Convert file path to module name"""
        relative_path = file_path.relative_to(self.root_dir)
        module_parts = list(relative_path.parts[:-1])  # Exclude .py file

        if file_path.name == '__init__.py':
            # Package module
            module_name = '.'.join(module_parts) if module_parts else 'app'
        else:
            # Regular module
            module_name = '.'.join(module_parts + [file_path.stem])

        return module_name

    def build_dependency_graph(self):
        """Build dependency graph from well-structured files"""
        python_files = []

        # Collect all Python files
        for file_path in self.root_dir.rglob("*.py"):
            # Skip tests, migrations, and problematic directories
            skip_dirs = {'__pycache__', 'migrations', '.pytest_cache', 'venv', 'env'}
            if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
                continue

            if self.is_well_structured_file(file_path):
                python_files.append(file_path)

        logger.info(f"Analyzing {len(python_files)} well-structured Python files")

        # Extract imports for each file
        for file_path in python_files:
            module_name = self.get_module_name_from_path(file_path)
            imports = self.extract_imports_from_file(file_path)

            # Store the raw imports
            self.module_imports[module_name] = imports

            # Filter to only imports that exist in our codebase
            valid_imports = set()
            for imp in imports:
                # Extract base module (e.g., 'app.core.database' from 'app.core.database.Base')
                base_imp = imp
                if '.' in imp:
                    parts = imp.split('.')
                    for i in range(len(parts), 0, -1):
                        test_imp = '.'.join(parts[:i])
                        if test_imp in [self.get_module_name_from_path(f) for f in python_files]:
                            base_imp = test_imp
                            break

                valid_imports.add(base_imp)

            self.import_graph[module_name] = valid_imports

    def find_circular_dependencies(self):
        """Find circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            if node not in self.import_graph:
                return False

            if node in rec_stack:
                # Found cycle - extract the cycle from path
                if node in path:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    self.circular_deps.append(cycle)
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.import_graph.get(node, []):
                if dfs(neighbor):
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        # Check each node
        for node in self.import_graph:
            if node not in visited:
                dfs(node)

    def analyze_patterns(self):
        """Analyze specific problematic patterns"""
        issues = []

        for module, deps in self.import_graph.items():
            # Services importing other services
            if 'services.' in module:
                for dep in deps:
                    if 'services.' in dep and module != dep:
                        issues.append({
                            'type': 'service_importing_service',
                            'from': module,
                            'to': dep,
                            'severity': 'high'
                        })

            # Models importing services (major anti-pattern)
            if 'db.models.' in module:
                for dep in deps:
                    if 'services.' in dep:
                        issues.append({
                            'type': 'model_importing_service',
                            'from': module,
                            'to': dep,
                            'severity': 'critical'
                        })

            # API endpoints importing models directly
            if 'api.' in module and 'endpoints' in module:
                for dep in deps:
                    if 'db.models.' in dep:
                        issues.append({
                            'type': 'api_importing_model_directly',
                            'from': module,
                            'to': dep,
                            'severity': 'medium'
                        })

            # Config importing business logic
            if 'core.config' in module:
                for dep in deps:
                    if any(x in dep for x in ['services.', 'api.', 'db.models.']):
                        issues.append({
                            'type': 'config_importing_business_logic',
                            'from': module,
                            'to': dep,
                            'severity': 'high'
                        })

            # Core modules importing application modules
            if 'core.' in module:
                for dep in deps:
                    if any(x in dep for x in ['services.', 'api.endpoints.', 'db.models.']):
                        issues.append({
                            'type': 'core_importing_app_module',
                            'from': module,
                            'to': dep,
                            'severity': 'high'
                        })

        return issues

    def generate_report(self) -> str:
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("FOCUSED CIRCULAR DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Root Directory: {self.root_dir}")
        report.append(f"Python Files Analyzed: {len(self.import_graph)}")
        report.append(f"Total Dependencies: {sum(len(deps) for deps in self.import_graph.values())}")
        report.append("")

        # Circular Dependencies
        if self.circular_deps:
            report.append(f"FOUND {len(self.circular_deps)} CIRCULAR DEPENDENCIES:")
            report.append("-" * 60)

            for i, cycle in enumerate(self.circular_deps, 1):
                report.append(f"\n{i}. Circular Dependency Chain:")
                for j, module in enumerate(cycle):
                    arrow = " -> " if j < len(cycle) - 1 else ""
                    report.append(f"   {module}{arrow}")
        else:
            report.append("NO CIRCULAR DEPENDENCIES FOUND ✓")

        report.append("")

        # Pattern Issues
        issues = self.analyze_patterns()
        if issues:
            report.append(f"FOUND {len(issues)} ARCHITECTURAL ISSUES:")
            report.append("-" * 60)

            issue_types = {}
            for issue in issues:
                issue_type = issue['type']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)

            for issue_type, type_issues in issue_types.items():
                severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                for issue in type_issues:
                    severity_counts[issue['severity']] += 1

                report.append(f"\n{issue_type.replace('_', ' ').title().upper()}")
                report.append(f"  Total: {len(type_issues)} instances")
                report.append(f"  Severity: {severity_counts['critical']} critical, {severity_counts['high']} high, {severity_counts['medium']} medium")
                report.append("  Examples:")

                for issue in type_issues[:3]:  # Show first 3 examples
                    report.append(f"    {issue['from']} -> {issue['to']} ({issue['severity']})")

                if len(type_issues) > 3:
                    report.append(f"    ... and {len(type_issues) - 3} more")
        else:
            report.append("NO SPECIFIC ARCHITECTURAL ISSUES FOUND ✓")

        # Module Dependency Summary
        report.append("\n" + "=" * 60)
        report.append("MODULE DEPENDENCY SUMMARY")
        report.append("=" * 60)

        deps_count = [(module, len(deps)) for module, deps in self.import_graph.items()]
        deps_count.sort(key=lambda x: x[1], reverse=True)

        report.append(f"\nTop 10 modules with most dependencies:")
        for module, count in deps_count[:10]:
            report.append(f"  {module}: {count} dependencies")

        # Most dependent modules (imported by others)
        imported_by = {}
        for module, deps in self.import_graph.items():
            for dep in deps:
                if dep not in imported_by:
                    imported_by[dep] = set()
                imported_by[dep].add(module)

        most_imported = [(module, len(importers)) for module, importers in imported_by.items()]
        most_imported.sort(key=lambda x: x[1], reverse=True)

        report.append(f"\nTop 10 most imported modules:")
        for module, count in most_imported[:10]:
            report.append(f"  {module}: imported by {count} modules")

        return "\n".join(report)

    def suggest_solutions(self) -> str:
        """Suggest solutions for found issues"""
        solutions = []
        solutions.append("=" * 80)
        solutions.append("RECOMMENDED SOLUTIONS")
        solutions.append("=" * 80)

        if self.circular_deps:
            solutions.append("\nFOR CIRCULAR DEPENDENCIES:")
            solutions.append("-" * 40)

            for i, cycle in enumerate(self.circular_deps, 1):
                solutions.append(f"\n{i}. For cycle: {' -> '.join(cycle)}")
                solutions.append("   Recommended Solution:")

                if len(cycle) == 2:
                    solutions.append("   - Extract common functionality to a shared utility module")
                    solutions.append("   - Use dependency injection to break the circularity")
                    solutions.append("   - Move one dependency to a separate layer")
                else:
                    solutions.append("   - Identify the weakest link in the dependency chain")
                    solutions.append("   - Extract interfaces to decouple modules")
                    solutions.append("   - Move shared functionality to a new module")

        issues = self.analyze_patterns()
        if issues:
            solutions.append("\nFOR ARCHITECTURAL ISSUES:")
            solutions.append("-" * 40)

            issue_types = set(issue['type'] for issue in issues)

            if 'model_importing_service' in issue_types:
                solutions.append("\n🚨 CRITICAL: Models Importing Services")
                solutions.append("   - IMMEDIATE ACTION REQUIRED")
                solutions.append("   - Remove all service imports from model files")
                solutions.append("   - Move business logic to service layer")
                solutions.append("   - Use domain events or signals for model callbacks")
                solutions.append("   - Consider using SQLAlchemy events for model-level hooks")

            if 'service_importing_service' in issue_types:
                solutions.append("\n🔴 HIGH: Service-to-Service Dependencies")
                solutions.append("   - Create shared interfaces/protocols")
                solutions.append("   - Use dependency injection container")
                solutions.append("   - Extract common functionality to utility modules")
                solutions.append("   - Consider implementing a mediator pattern")

            if 'api_importing_model_directly' in issue_types:
                solutions.append("\n🟡 MEDIUM: API Endpoints Importing Models Directly")
                solutions.append("   - Use schemas for data transfer objects")
                solutions.append("   - Import models through service layer")
                solutions.append("   - Follow repository pattern for data access")
                solutions.append("   - Keep API layer thin and focused on HTTP concerns")

            if 'config_importing_business_logic' in issue_types:
                solutions.append("\n🔴 HIGH: Configuration Importing Business Logic")
                solutions.append("   - Keep configuration files pure")
                solutions.append("   - Use factory pattern for complex initializations")
                solutions.append("   - Move business logic out of configuration")
                solutions.append("   - Use environment variables for configuration only")

            if 'core_importing_app_module' in issue_types:
                solutions.append("\n🔴 HIGH: Core Modules Importing Application Modules")
                solutions.append("   - Core modules should not depend on application modules")
                solutions.append("   - Use dependency injection to invert dependencies")
                solutions.append("   - Move shared code to appropriate layers")
                solutions.append("   - Consider using events for decoupling")

        return "\n".join(solutions)


def main():
    """Main function to run the focused analysis"""
    root_dir = "/Users/sheriftito/Downloads/psychsync/app"

    logger.info("Starting focused circular dependency analysis...")
    analyzer = FocusedDependencyAnalyzer(root_dir)

    logger.info("Building dependency graph...")
    analyzer.build_dependency_graph()

    logger.info("Finding circular dependencies...")
    analyzer.find_circular_dependencies()

    logger.info("Analyzing patterns...")
    analyzer.analyze_patterns()

    logger.info("\nGenerating report...")
    report = analyzer.generate_report()
    print(report)

    solutions = analyzer.suggest_solutions()
    print(solutions)

    # Save reports to files
    with open("focused_dependency_report.txt", "w") as f:
        f.write(report)

    with open("focused_dependency_solutions.txt", "w") as f:
        f.write(solutions)

    logger.info(f"\nReports saved to:")
    logger.info(f"  - focused_dependency_report.txt")
    logger.info(f"  - focused_dependency_solutions.txt")


if __name__ == "__main__":
    main()