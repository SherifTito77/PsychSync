"""
Architecture Validator Component

Validates code architecture, design patterns, and quality metrics.
Identifies code smells, anti-patterns, and architectural issues.

Key Features:
✔ Analyzes cyclomatic complexity and maintainability
✔ Detects design patterns and anti-patterns
✔ Validates dependency management
✔ Ensures SOLID principles compliance
✔ Provides actionable improvement recommendations
"""

import ast
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class ArchitectureMetrics:
    """Metrics for code architecture analysis"""
    file_path: str
    lines_of_code: int
    cyclomatic_complexity: float
    maintainability_index: float
    coupling_score: float
    cohesion_score: float
    dependency_depth: int
    design_patterns: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    code_smells: List[str] = field(default_factory=list)
    solid_violations: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)


@dataclass
class ArchitectureAnalysisResult:
    """Result of architecture analysis"""
    total_files_analyzed: int
    overall_quality_score: float
    complexity_distribution: Dict[str, int]
    maintainability_distribution: Dict[str, int]
    design_patterns_found: Dict[str, int]
    anti_patterns_found: Dict[str, int]
    code_smells_found: Dict[str, int]
    solid_violations: Dict[str, int]
    dependency_analysis: Dict[str, Any]
    recommendations: List[str]
    critical_issues: List[str]
    detailed_metrics: List[ArchitectureMetrics]


class ArchitectureValidator:
    """
    Validates software architecture and code quality

    Features:
    - Cyclomatic complexity analysis
    - Maintainability index calculation
    - Design pattern detection
    - Anti-pattern identification
    - SOLID principles validation
    - Dependency analysis
    - Code smell detection
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.complexity_threshold = config.get("complexity_threshold", 10)
        self.maintainability_threshold = config.get("maintainability_threshold", 70)
        self.max_dependency_depth = config.get("max_dependency_depth", 5)
        self.project_root = Path(__file__).parent.parent.parent

        # Architecture analysis cache
        self.analysis_cache = {}
        self.dependency_graph = nx.DiGraph()

    async def validate_architecture(self, file_paths: Optional[List[str]] = None) -> ArchitectureAnalysisResult:
        """
        Perform comprehensive architecture validation

        Args:
            file_paths: List of file paths to analyze. If None, analyzes all Python files

        Returns:
            ArchitectureAnalysisResult with detailed findings
        """
        logger.info("📐 Starting architecture validation...")

        if file_paths is None:
            file_paths = self._discover_python_files()

        if not file_paths:
            logger.warning("No Python files found for analysis")
            return self._empty_result()

        # Analyze all files
        metrics = []
        for file_path in file_paths:
            try:
                file_metrics = await self._analyze_file_architecture(file_path)
                metrics.append(file_metrics)

                # Update dependency graph
                self._update_dependency_graph(file_metrics)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        if not metrics:
            logger.error("No files could be analyzed")
            return self._empty_result()

        # Compile comprehensive results
        return self._compile_analysis_results(metrics)

    def _discover_python_files(self) -> List[str]:
        """Discover all Python files in the project"""
        python_files = []

        for pattern in ["**/*.py", "app/**/*.py"]:
            for file_path in self.project_root.glob(pattern):
                # Skip common non-source directories
                if any(skip in str(file_path) for skip in [
                    "venv", "__pycache__", ".git", "node_modules",
                    "migrations", "alembic/versions"
                ]):
                    continue

                python_files.append(str(file_path))

        return python_files

    async def _analyze_file_architecture(self, file_path: str) -> ArchitectureMetrics:
        """Analyze architecture metrics for a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            file_path_obj = Path(file_path)

            # Basic metrics
            lines_of_code = len([line for line in content.splitlines() if line.strip()])
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
            maintainability_index = self._calculate_maintainability_index(content, tree, lines_of_code)

            # Dependency analysis
            dependencies = self._extract_dependencies(tree)
            coupling_score = self._calculate_coupling_score(dependencies)
            dependency_depth = self._calculate_dependency_depth(file_path_obj, dependencies)

            # Extract classes and functions
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

            # Design pattern detection
            design_patterns = self._detect_design_patterns(tree)

            # Anti-pattern detection
            anti_patterns = self._detect_anti_patterns(content, tree)

            # Code smell detection
            code_smells = self._detect_code_smells(content, tree, classes, functions)

            # SOLID principles validation
            solid_violations = self._validate_solid_principles(tree, classes)

            # Cohesion calculation
            cohesion_score = self._calculate_cohesion_score(tree, classes)

            return ArchitectureMetrics(
                file_path=file_path,
                lines_of_code=lines_of_code,
                cyclomatic_complexity=cyclomatic_complexity,
                maintainability_index=maintainability_index,
                coupling_score=coupling_score,
                cohesion_score=cohesion_score,
                dependency_depth=dependency_depth,
                design_patterns=design_patterns,
                anti_patterns=anti_patterns,
                code_smells=code_smells,
                solid_violations=solid_violations,
                dependencies=dependencies,
                classes=classes,
                functions=functions
            )

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return ArchitectureMetrics(
                file_path=file_path,
                lines_of_code=0,
                cyclomatic_complexity=0.0,
                maintainability_index=0.0,
                coupling_score=0.0,
                cohesion_score=0.0,
                dependency_depth=0,
                dependencies=[],
                classes=[],
                functions=[]
            )

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """
        Calculate cyclomatic complexity using McCabe's method

        Complexity = E - N + 2P
        Where:
        E = Number of edges
        N = Number of nodes
        P = Number of connected components
        """
        complexity = 1  # Base complexity for simple functions

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers) + 1  # +1 for try block
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
            elif isinstance(node, ast.Lambda):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            elif isinstance(node, ast.AsyncWith):
                complexity += 1
            elif isinstance(node, ast.Match):
                complexity += len(node.cases)

        return float(complexity)

    def _calculate_maintainability_index(self, content: str, tree: ast.AST, lines_of_code: int) -> float:
        """
        Calculate maintainability index using Microsoft's formula

        MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        """
        if lines_of_code == 0:
            return 0.0

        # Halstead volume calculation (simplified)
        operators = len(re.findall(r'\+\+|--|\+\=|-\=|\*|\/|\%|\=\=|\!\=|\>\=|\<\=|\&\&|\|\||\!|\&|\||\^|\~|\<\<|\>\>', content))
        operands = len(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b|\b\d+\b', content))

        if operators == 0 or operands == 0:
            halstead_volume = 1.0
        else:
            vocabulary = operators + operands
            length = operators + operands
            halstead_volume = length * (vocabulary / (operators + operands)) if vocabulary > 0 else 1.0

        # Simplified maintainability index
        try:
            import math
            mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * self._calculate_cyclomatic_complexity(tree) - 16.2 * math.log(lines_of_code)
        except (ValueError, ZeroDivisionError):
            mi = 50.0  # Default value

        return max(0, min(100, mi))

    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        """Extract all module dependencies from AST"""
        dependencies = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:  # Only absolute imports
                    dependencies.add(node.module)

        return sorted(list(dependencies))

    def _calculate_coupling_score(self, dependencies: List[str]) -> float:
        """
        Calculate coupling score based on number of dependencies
        Lower is better (less coupled)
        """
        # Different weights for different types of dependencies
        external_libs = 0
        internal_deps = 0
        std_lib_deps = 0

        std_lib_modules = {
            'os', 'sys', 'json', 'datetime', 'time', 'logging', 'pathlib',
            'collections', 'itertools', 'functools', 'operator', 're',
            'math', 'random', 'string', 'typing', 'dataclasses', 'enum',
            'asyncio', 'threading', 'multiprocessing', 'queue',
            'http', 'urllib', 'socket', 'ssl', 'hashlib', 'hmac',
            'csv', 'xml', 'html', 'email', 'mimetypes', 'base64'
        }

        for dep in dependencies:
            if any(dep.startswith(lib) for lib in std_lib_modules):
                std_lib_deps += 1
            elif dep.startswith(('app.', 'scripts.')):
                internal_deps += 1
            else:
                external_libs += 1

        # Weighted score (external dependencies cost more)
        weighted_deps = (external_libs * 2.0 + internal_deps * 1.5 + std_lib_deps * 0.5)
        coupling_score = min(100, weighted_deps * 2)  # Normalize to 0-100

        return coupling_score

    def _calculate_dependency_depth(self, file_path: Path, dependencies: List[str]) -> int:
        """Calculate maximum dependency depth"""
        # This is a simplified implementation
        # In a real scenario, you'd analyze the entire dependency tree
        return min(len(dependencies), self.max_dependency_depth + 2)

    def _calculate_cohesion_score(self, tree: ast.AST, classes: List[str]) -> float:
        """
        Calculate cohesion score for classes
        Higher is better (more cohesive)
        """
        if not classes:
            return 100.0  # No classes = no cohesion issues

        total_cohesion = 0.0
        class_count = len(classes)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count related methods and attributes
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                attributes = []

                # Look for instance attributes in __init__
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if isinstance(child.value, ast.Name) and child.value.id == 'self':
                            attributes.append(child.attr)

                # Simple cohesion calculation based on method/attribute ratio
                if len(methods) > 0:
                    cohesion = min(100, (len(attributes) / len(methods)) * 50)
                else:
                    cohesion = 50.0  # Default for classes without methods

                total_cohesion += cohesion

        return total_cohesion / class_count if class_count > 0 else 100.0

    def _detect_design_patterns(self, tree: ast.AST) -> List[str]:
        """Detect common design patterns in the code"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                patterns.extend(self._detect_class_patterns(node))

        return list(set(patterns))

    def _detect_class_patterns(self, class_node: ast.ClassDef) -> List[str]:
        """Detect patterns in a specific class"""
        patterns = []
        method_names = [n.name for n in class_node.body if isinstance(n, ast.FunctionDef)]
        class_name = class_node.name.lower()

        # Singleton Pattern
        if any('instance' in method_name or 'getInstance' in method_name for method_name in method_names):
            if any('__new__' in method_name for method_name in method_names):
                patterns.append("Singleton")

        # Factory Pattern
        if any('create' in method_name or 'build' in method_name or 'factory' in method_name.lower()
               for method_name in method_names):
            patterns.append("Factory")

        # Observer Pattern
        if any('notify' in method_name or 'update' in method_name or 'attach' in method_name
               or 'detach' in method_name for method_name in method_names):
            patterns.append("Observer")

        # Strategy Pattern
        if 'strategy' in class_name or any('execute' in method_name for method_name in method_names):
            patterns.append("Strategy")

        # Decorator Pattern
        if 'decorator' in class_name or any('wrap' in method_name or 'decorate' in method_name
                                          for method_name in method_names):
            patterns.append("Decorator")

        # Command Pattern
        if 'command' in class_name or any('execute' in method_name or 'undo' in method_name
                                         for method_name in method_names):
            patterns.append("Command")

        # Template Method Pattern
        if any('template' in class_name.lower() or
               (method_name.startswith('_') and method_name.endswith('_template'))
               for method_name in method_names):
            patterns.append("Template Method")

        return patterns

    def _detect_anti_patterns(self, content: str, tree: ast.AST) -> List[str]:
        """Detect common architectural anti-patterns"""
        anti_patterns = []

        # God Class/Object
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                lines_of_code = len([line for line in content.splitlines() if line.strip()])

                if len(methods) > 20 or (len(methods) > 10 and lines_of_code > 500):
                    anti_patterns.append(f"God Class: {node.name}")

        # Long Method
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    method_length = node.end_lineno - node.lineno
                    if method_length > 50:
                        anti_patterns.append(f"Long Method: {node.name} ({method_length} lines)")

        # Duplicate Code (simplified detection)
        lines = content.splitlines()
        line_counts = defaultdict(int)
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 10 and not stripped.startswith('#'):
                line_counts[stripped] += 1

        duplicates = sum(1 for count in line_counts.values() if count > 2)
        if duplicates > 5:
            anti_patterns.append(f"Duplicate Code: {duplicates} potential duplications")

        # Magic Numbers
        magic_numbers = re.findall(r'\b\d{2,}\b', content)
        if len(magic_numbers) > 10:
            anti_patterns.append(f"Magic Numbers: {len(magic_numbers)} instances")

        # Dead Code (imports that aren't used)
        # This is a simplified detection
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        # Check if imports are actually used (simplified)
        used_imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id in imports:
                    used_imports.add(node.id)

        unused_imports = imports - used_imports
        if len(unused_imports) > 3:
            anti_patterns.append(f"Unused Imports: {len(unused_imports)} potentially unused")

        return anti_patterns[:20]  # Limit to top 20 anti-patterns

    def _detect_code_smells(self, content: str, tree: ast.AST, classes: List[str], functions: List[str]) -> List[str]:
        """Detect code smells that impact maintainability"""
        code_smells = []

        # Long Parameter List
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > 7:
                    code_smells.append(f"Long Parameter List: {node.name} ({len(node.args.args)} parameters)")

        # Feature Envy
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                for method in methods:
                    # Simplified detection: look for many method calls on other objects
                    method_calls = 0
                    for child in ast.walk(method):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Attribute):
                                method_calls += 1

                    if method_calls > 10:
                        code_smells.append(f"Feature Envy: {class_name}.{method.name} ({method_calls} external calls)")

        # Data Clumps
        parameters_seen = defaultdict(int)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_names = [arg.arg for arg in node.args.args]
                if len(param_names) > 2:
                    for combo in self._parameter_combinations(param_names, 3):
                        parameters_seen[tuple(combo)] += 1

        for combo, count in parameters_seen.items():
            if count > 3:
                code_smells.append(f"Data Clump: Parameters {combo} appear together {count} times")

        # Inappropriate Intimacy
        class_dependencies = defaultdict(set)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if hasattr(child.value, 'id') and child.value.id != 'self':
                            class_dependencies[class_name].add(child.value.id)

        for class_name, deps in class_dependencies.items():
            if len(deps) > 10:
                code_smells.append(f"Inappropriate Intimacy: {class_name} depends on {len(deps)} other classes")

        # Speculative Generality
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                abstract_methods = [m for m in methods if
                                  any(decorator.id == 'abstractmethod' for decorator in m.decorator_list
                                      if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod')]

                if len(abstract_methods) > len(methods) * 0.7:
                    code_smells.append(f"Speculative Generality: {node.name} has too many abstract methods")

        return code_smells[:20]  # Limit to top 20 code smells

    def _parameter_combinations(self, params: List[str], size: int):
        """Generate all combinations of parameters of given size"""
        from itertools import combinations
        return list(combinations(params, size))

    def _validate_solid_principles(self, tree: ast.AST, classes: List[str]) -> List[str]:
        """Validate SOLID principles compliance"""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Single Responsibility Principle
                violations.extend(self._check_srp_violations(node))

                # Open/Closed Principle
                violations.extend(self._check_ocp_violations(node))

                # Liskov Substitution Principle
                violations.extend(self._check_lsp_violations(node))

                # Interface Segregation Principle
                violations.extend(self._check_isp_violations(node))

                # Dependency Inversion Principle
                violations.extend(self._check_dip_violations(node))

        return violations[:15]  # Limit to top 15 violations

    def _check_srp_violations(self, class_node: ast.ClassDef) -> List[str]:
        """Check Single Responsibility Principle violations"""
        violations = []

        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]

        # Too many responsibilities (simplified)
        if len(methods) > 15:
            violations.append(f"SRP Violation: {class_node.name} has {len(methods)} methods (too many responsibilities)")

        # Methods doing unrelated things (simplified heuristic)
        method_topics = []
        for method in methods:
            # Extract topic words from method name and docstring
            topic_words = set()
            topic_words.update(method.name.lower().split('_'))

            # Simple topic analysis based on method name patterns
            if any(word in method.name.lower() for word in ['save', 'load', 'read', 'write', 'persist']):
                topic_words.add('data')
            if any(word in method.name.lower() for word in ['validate', 'check', 'verify']):
                topic_words.add('validation')
            if any(word in method.name.lower() for word in ['render', 'display', 'show', 'view']):
                topic_words.add('ui')
            if any(word in method.name.lower() for word in ['send', 'notify', 'email', 'message']):
                topic_words.add('communication')

            method_topics.append(topic_words)

        # Count unique topics
        all_topics = set()
        for topics in method_topics:
            all_topics.update(topics)

        if len(all_topics) > 3:
            violations.append(f"SRP Violation: {class_node.name} handles {len(all_topics)} different concerns")

        return violations

    def _check_ocp_violations(self, class_node: ast.ClassDef) -> List[str]:
        """Check Open/Closed Principle violations"""
        violations = []

        # Look for hard-coded logic that should be extensible
        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                # Look for long if-elif chains
                if self._count_decision_points(method) > 5:
                    violations.append(f"OCP Violation: {class_node.name}.{method.name} has complex conditional logic")

        return violations

    def _check_lsp_violations(self, class_node: ast.ClassDef) -> List[str]:
        """Check Liskov Substitution Principle violations"""
        violations = []

        # Check for inheritance
        bases = [base.id for base in class_node.bases if isinstance(base, ast.Name)]

        if bases:
            for method in class_node.body:
                if isinstance(method, ast.FunctionDef):
                    # Look for methods that raise exceptions that base classes wouldn't
                    for node in ast.walk(method):
                        if isinstance(node, ast.Raise):
                            violations.append(f"LSP Violation: {class_node.name}.{method.name} may break substitution")
                            break

        return violations

    def _check_isp_violations(self, class_node: ast.ClassDef) -> List[str]:
        """Check Interface Segregation Principle violations"""
        violations = []

        # Look for classes with many methods that could be split
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]

        if len(methods) > 12:
            violations.append(f"ISP Violation: {class_node.name} has {len(methods)} methods (consider splitting interface)")

        return violations

    def _check_dip_violations(self, class_node: ast.ClassDef) -> List[str]:
        """Check Dependency Inversion Principle violations"""
        violations = []

        # Look for concrete class dependencies
        for node in ast.walk(class_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Calling a concrete class constructor
                    violations.append(f"DIP Violation: {class_node.name} depends on concrete class {node.func.id}")

        return violations[:5]  # Limit DIP violations

    def _count_decision_points(self, node: ast.AST) -> int:
        """Count decision points in a function"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp)):
                count += 1
        return count

    def _update_dependency_graph(self, metrics: ArchitectureMetrics):
        """Update the dependency graph with new metrics"""
        file_path = Path(metrics.file_path)
        module_name = file_path.stem

        # Add node
        self.dependency_graph.add_node(module_name, **asdict(metrics))

        # Add edges for dependencies
        for dep in metrics.dependencies:
            if '.' in dep and not dep.startswith(('os', 'sys', 'json', 'datetime', 'logging')):
                dep_module = dep.split('.')[0]
                self.dependency_graph.add_edge(module_name, dep_module)

    def _compile_analysis_results(self, metrics: List[ArchitectureMetrics]) -> ArchitectureAnalysisResult:
        """Compile comprehensive analysis results from individual file metrics"""

        # Calculate distributions
        complexity_distribution = self._calculate_complexity_distribution(metrics)
        maintainability_distribution = self._calculate_maintainability_distribution(metrics)

        # Aggregate pattern counts
        design_patterns_found = defaultdict(int)
        anti_patterns_found = defaultdict(int)
        code_smells_found = defaultdict(int)
        solid_violations = defaultdict(int)

        for metric in metrics:
            for pattern in metric.design_patterns:
                design_patterns_found[pattern] += 1
            for anti_pattern in metric.anti_patterns:
                anti_patterns_found[anti_pattern] += 1
            for smell in metric.code_smells:
                code_smells_found[smell] += 1
            for violation in metric.solid_violations:
                solid_violations[violation] += 1

        # Dependency analysis
        dependency_analysis = {
            "total_dependencies": sum(len(m.dependencies) for m in metrics),
            "average_coupling": sum(m.coupling_score for m in metrics) / len(metrics) if metrics else 0,
            "max_dependency_depth": max(m.dependency_depth for m in metrics) if metrics else 0,
            "circular_dependencies": self._detect_circular_dependencies(),
            "isolated_modules": self._detect_isolated_modules(metrics)
        }

        # Calculate overall quality score
        overall_quality_score = self._calculate_overall_quality_score(metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, complexity_distribution, maintainability_distribution)

        # Identify critical issues
        critical_issues = self._identify_critical_issues(metrics, anti_patterns_found, solid_violations)

        return ArchitectureAnalysisResult(
            total_files_analyzed=len(metrics),
            overall_quality_score=overall_quality_score,
            complexity_distribution=complexity_distribution,
            maintainability_distribution=maintainability_distribution,
            design_patterns_found=dict(design_patterns_found),
            anti_patterns_found=dict(anti_patterns_found),
            code_smells_found=dict(code_smells_found),
            solid_violations=dict(solid_violations),
            dependency_analysis=dependency_analysis,
            recommendations=recommendations,
            critical_issues=critical_issues,
            detailed_metrics=metrics
        )

    def _calculate_complexity_distribution(self, metrics: List[ArchitectureMetrics]) -> Dict[str, int]:
        """Calculate distribution of complexity levels"""
        distribution = {"low": 0, "medium": 0, "high": 0, "very_high": 0}

        for metric in metrics:
            if metric.cyclomatic_complexity <= 5:
                distribution["low"] += 1
            elif metric.cyclomatic_complexity <= 10:
                distribution["medium"] += 1
            elif metric.cyclomatic_complexity <= 20:
                distribution["high"] += 1
            else:
                distribution["very_high"] += 1

        return distribution

    def _calculate_maintainability_distribution(self, metrics: List[ArchitectureMetrics]) -> Dict[str, int]:
        """Calculate distribution of maintainability levels"""
        distribution = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}

        for metric in metrics:
            if metric.maintainability_index >= 85:
                distribution["excellent"] += 1
            elif metric.maintainability_index >= 70:
                distribution["good"] += 1
            elif metric.maintainability_index >= 50:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the dependency graph"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles[:10]  # Limit to first 10 cycles
        except Exception:
            return []

    def _detect_isolated_modules(self, metrics: List[ArchitectureMetrics]) -> List[str]:
        """Detect modules with no dependencies or dependents"""
        isolated = []
        for metric in metrics:
            module_name = Path(metric.file_path).stem
            if (self.dependency_graph.out_degree(module_name) == 0 and
                self.dependency_graph.in_degree(module_name) == 0):
                isolated.append(module_name)
        return isolated

    def _calculate_overall_quality_score(self, metrics: List[ArchitectureMetrics]) -> float:
        """Calculate overall architecture quality score"""
        if not metrics:
            return 0.0

        # Weight different factors
        avg_complexity = sum(m.cyclomatic_complexity for m in metrics) / len(metrics)
        avg_maintainability = sum(m.maintainability_index for m in metrics) / len(metrics)
        avg_coupling = sum(m.coupling_score for m in metrics) / len(metrics)
        avg_cohesion = sum(m.cohesion_score for m in metrics) / len(metrics)

        # Calculate penalty scores
        complexity_penalty = min(50, (avg_complexity - self.complexity_threshold) * 2)
        maintainability_penalty = max(0, self.maintainability_threshold - avg_maintainability) / 2
        coupling_penalty = avg_coupling / 2
        cohesion_bonus = (100 - avg_cohesion) / 4  # Higher cohesion = better

        # Base score with penalties and bonuses
        quality_score = 100 - complexity_penalty - maintainability_penalty - coupling_penalty + cohesion_bonus

        return max(0, min(100, quality_score))

    def _generate_recommendations(self, metrics: List[ArchitectureMetrics],
                                complexity_dist: Dict[str, int],
                                maintainability_dist: Dict[str, int]) -> List[str]:
        """Generate actionable improvement recommendations"""
        recommendations = []

        # Complexity recommendations
        if complexity_dist["high"] + complexity_dist["very_high"] > len(metrics) * 0.3:
            recommendations.append(
                f"High complexity detected in {complexity_dist['high'] + complexity_dist['very_high']} files. "
                "Consider refactoring complex functions using the Extract Method pattern."
            )

        # Maintainability recommendations
        if maintainability_dist["poor"] > len(metrics) * 0.2:
            recommendations.append(
                f"Poor maintainability in {maintainability_dist['poor']} files. "
                "Improve documentation, reduce complexity, and add unit tests."
            )

        # Coupling recommendations
        avg_coupling = sum(m.coupling_score for m in metrics) / len(metrics) if metrics else 0
        if avg_coupling > 40:
            recommendations.append(
                f"High average coupling ({avg_coupling:.1f}). "
                "Consider implementing Dependency Injection and using interfaces."
            )

        # SOLID principles recommendations
        solid_violations = sum(len(m.solid_violations) for m in metrics)
        if solid_violations > len(metrics):
            recommendations.append(
                f"{solid_violations} SOLID principle violations found. "
                "Review class responsibilities and inheritance hierarchies."
            )

        # Design pattern recommendations
        design_patterns_used = set()
        for metric in metrics:
            design_patterns_used.update(metric.design_patterns)

        if len(design_patterns_used) < 3:
            recommendations.append(
                "Consider using established design patterns to improve code structure. "
                "Good candidates: Factory, Observer, Strategy, or Singleton patterns."
            )

        # Testing recommendations
        files_without_tests = [m for m in metrics if m.lines_of_code > 100]
        if len(files_without_tests) > len(metrics) * 0.5:
            recommendations.append(
                f"Many files ({len(files_without_tests)}) appear to lack tests. "
                "Improve test coverage to enhance maintainability."
            )

        # Documentation recommendations
        recommendations.append("Ensure all public APIs have comprehensive docstrings.")

        return recommendations[:15]  # Limit to top 15 recommendations

    def _identify_critical_issues(self, metrics: List[ArchitectureMetrics],
                               anti_patterns: Dict[str, int],
                               solid_violations: Dict[str, int]) -> List[str]:
        """Identify critical architectural issues requiring immediate attention"""
        critical_issues = []

        # Very high complexity
        very_complex = [m for m in metrics if m.cyclomatic_complexity > 50]
        if very_complex:
            critical_issues.append(f"CRITICAL: {len(very_complex)} files with very high complexity (>50)")

        # Very poor maintainability
        very_poor_maintainability = [m for m in metrics if m.maintainability_index < 20]
        if very_poor_maintainability:
            critical_issues.append(f"CRITICAL: {len(very_poor_maintainability)} files with very poor maintainability (<20)")

        # Critical anti-patterns
        critical_anti_patterns = {k: v for k, v in anti_patterns.items()
                                if "God Class" in k and v > 0}
        if critical_anti_patterns:
            critical_issues.append(f"CRITICAL: God Class pattern detected - refactoring required")

        # Circular dependencies
        circular_deps = self._detect_circular_dependencies()
        if circular_deps:
            critical_issues.append(f"CRITICAL: {len(circular_deps)} circular dependency chains detected")

        return critical_issues

    def _empty_result(self) -> ArchitectureAnalysisResult:
        """Return empty result for cases where no files could be analyzed"""
        return ArchitectureAnalysisResult(
            total_files_analyzed=0,
            overall_quality_score=0.0,
            complexity_distribution={"low": 0, "medium": 0, "high": 0, "very_high": 0},
            maintainability_distribution={"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            design_patterns_found={},
            anti_patterns_found={},
            code_smells_found={},
            solid_violations={},
            dependency_analysis={
                "total_dependencies": 0,
                "average_coupling": 0,
                "max_dependency_depth": 0,
                "circular_dependencies": [],
                "isolated_modules": []
            },
            recommendations=["No files found for analysis"],
            critical_issues=["Unable to perform architecture analysis"],
            detailed_metrics=[]
        )
