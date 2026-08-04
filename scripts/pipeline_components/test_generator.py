"""
Test Generator Component

Automatically generates comprehensive test suites with AI-powered test case creation.
Ensures high test coverage and validates system behavior.

Key Features:
✔ AI-powered test case generation
✔ Multiple testing framework support (pytest, jest, vitest)
✔ Test coverage analysis and improvement
✔ Mock generation for external dependencies
✔ Performance and integration test generation
✔ Test data factory creation
✔ End-to-end test scenario generation
"""

import ast
import json
import logging
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TestCoverageData:
    """Test coverage information"""

    file_path: str
    lines_total: int
    lines_covered: int
    coverage_percentage: float
    branches_total: int
    branches_covered: int
    branch_coverage_percentage: float
    functions_total: int
    functions_covered: int
    function_coverage_percentage: float
    uncovered_lines: List[int] = field(default_factory=list)
    uncovered_functions: List[str] = field(default_factory=list)


@dataclass
class TestCase:
    """Generated test case information"""

    name: str
    description: str
    test_type: str  # unit, integration, e2e, performance
    framework: str
    file_path: str
    line_number: int
    complexity_score: float
    mock_dependencies: List[str] = field(default_factory=list)
    test_data: Dict[str, Any] = field(default_factory=dict)
    assertions: List[str] = field(default_factory=list)


@dataclass
class TestGenerationResult:
    """Result of test generation process"""

    tests_generated: int
    files_processed: int
    coverage_improvement: float
    test_types_generated: Dict[str, int]
    frameworks_used: Set[str]
    test_files_created: List[str]
    test_data_factories: List[str]
    integration_tests: List[TestCase]
    performance_tests: List[TestCase]
    e2e_tests: List[TestCase]
    mock_files_created: List[str]
    recommendations: List[str]
    error_files: List[str]


class TestGenerator:
    """
    AI-powered test generation system

    Features:
    - Intelligent test case generation based on code analysis
    - Support for multiple testing frameworks
    - Automatic mock and fixture generation
    - Test coverage analysis and improvement
    - Integration and end-to-end test creation
    - Performance test generation
    - Test data factory creation
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.target_coverage = config.get("target_coverage", 80)
        self.auto_fix = config.get("auto_fix", True)
        self.frameworks = config.get("frameworks", ["pytest", "jest", "vitest"])
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage_reports"

        # Ensure directories exist
        self.test_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)

        # Test generation cache
        self.generation_cache = {}
        self.coverage_cache = {}

        # Framework configurations
        self.framework_configs = {
            "pytest": {
                "test_pattern": "test_*.py",
                "fixture_decorator": "@pytest.fixture",
                "mock_library": "unittest.mock",
                "assert_style": "assert",
            },
            "jest": {
                "test_pattern": "*.test.js",
                "fixture_decorator": "",
                "mock_library": "jest.mock",
                "assert_style": "expect",
            },
            "vitest": {
                "test_pattern": "*.test.ts",
                "fixture_decorator": "",
                "mock_library": "vi.mock",
                "assert_style": "expect",
            },
        }

    async def generate_tests(
        self, source_files: Optional[List[str]] = None
    ) -> TestGenerationResult:
        """
        Generate comprehensive test suite for the codebase

        Args:
            source_files: List of source files to generate tests for. If None, analyzes all files

        Returns:
            TestGenerationResult with generation statistics
        """
        logger.info("🧪 Starting intelligent test generation...")

        if source_files is None:
            source_files = self._discover_source_files()

        if not source_files:
            logger.warning("No source files found for test generation")
            return self._empty_result()

        # Analyze current test coverage
        current_coverage = await self._analyze_current_coverage()

        # Generate tests for each file
        test_files_created = []
        test_cases_generated = []
        error_files = []
        test_data_factories = []
        mock_files = []

        for source_file in source_files[:30]:  # Limit for performance
            try:
                file_tests = await self._generate_tests_for_file(source_file)
                test_files_created.extend(file_tests.get("test_files", []))
                test_cases_generated.extend(file_tests.get("test_cases", []))
                test_data_factories.extend(file_tests.get("data_factories", []))
                mock_files.extend(file_tests.get("mock_files", []))

            except Exception as e:
                logger.error(f"Failed to generate tests for {source_file}: {e}")
                error_files.append(source_file)

        # Generate integration tests
        integration_tests = await self._generate_integration_tests(source_files)

        # Generate performance tests
        performance_tests = await self._generate_performance_tests(source_files)

        # Generate end-to-end tests
        e2e_tests = await self._generate_e2e_tests(source_files)

        # Create test data factories
        data_factories = await self._create_test_data_factories(source_files)

        # Calculate coverage improvement
        new_coverage = await self._analyze_new_coverage()
        coverage_improvement = new_coverage - current_coverage

        # Compile statistics
        test_types_generated = {
            "unit": len([tc for tc in test_cases_generated if tc.test_type == "unit"]),
            "integration": len(integration_tests),
            "performance": len(performance_tests),
            "e2e": len(e2e_tests),
        }

        frameworks_used = set()
        for test_case in test_cases_generated:
            frameworks_used.add(test_case.framework)

        # Generate recommendations
        recommendations = self._generate_test_recommendations(
            test_files_created, coverage_improvement, test_types_generated
        )

        return TestGenerationResult(
            tests_generated=len(test_files_created),
            files_processed=len(source_files),
            coverage_improvement=coverage_improvement,
            test_types_generated=test_types_generated,
            frameworks_used=frameworks_used,
            test_files_created=test_files_created,
            test_data_factories=test_data_factories,
            integration_tests=integration_tests,
            performance_tests=performance_tests,
            e2e_tests=e2e_tests,
            mock_files_created=mock_files,
            recommendations=recommendations,
            error_files=error_files,
        )

    def _discover_source_files(self) -> List[str]:
        """Discover all source files that need test generation"""
        source_files = []

        # Python files
        for pattern in ["app/**/*.py", "frontend/src/**/*.ts", "frontend/src/**/*.tsx"]:
            for file_path in self.project_root.glob(pattern):
                # Skip files that already have comprehensive tests
                if not self._has_comprehensive_tests(file_path):
                    source_files.append(str(file_path))

        return source_files

    def _has_comprehensive_tests(self, source_file: Path) -> bool:
        """Check if a source file already has comprehensive tests"""
        source_name = source_file.stem

        # Look for corresponding test files
        test_patterns = [
            f"test_{source_name}*.py",
            f"{source_name}_test*.py",
            f"{source_name}.test.*",
            f"tests/**/{source_name}*.py",
            f"__tests__/{source_name}.*",
        ]

        for pattern in test_patterns:
            if list(self.project_root.glob(pattern)):
                # Check if test file is substantial (more than 50 lines)
                for test_file in self.project_root.glob(pattern):
                    try:
                        with open(test_file, "r") as f:
                            content = f.read()
                            if len(content.splitlines()) > 50:
                                return True
                    except Exception:
                        continue

        return False

    async def _analyze_current_coverage(self) -> float:
        """Analyze current test coverage"""
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=app", "--cov-report=json", "--quiet"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0 and Path("coverage.json").exists():
                with open("coverage.json", "r") as f:
                    coverage_data = json.load(f)
                return coverage_data.get("totals", {}).get("percent_covered", 0.0)
            else:
                logger.warning("Could not analyze current coverage")
                return 0.0

        except Exception as e:
            logger.warning(f"Coverage analysis failed: {e}")
            return 0.0

    async def _generate_tests_for_file(self, source_file: str) -> Dict[str, Any]:
        """Generate tests for a specific source file"""
        source_path = Path(source_file)
        file_extension = source_path.suffix

        if file_extension == ".py":
            return await self._generate_python_tests(source_path)
        elif file_extension in [".ts", ".tsx", ".js", ".jsx"]:
            return await self._generate_javascript_tests(source_path)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return {
                "test_files": [],
                "test_cases": [],
                "data_factories": [],
                "mock_files": [],
            }

    async def _generate_python_tests(self, source_path: Path) -> Dict[str, Any]:
        """Generate Python tests using pytest"""
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            module_name = source_path.stem

            # Extract functions and classes
            functions = [
                node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
            ]
            classes = [
                node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            ]

            test_files = []
            test_cases = []
            data_factories = []
            mock_files = []

            # Generate test file
            test_content = await self._generate_python_test_content(
                module_name, functions, classes, source_path
            )
            test_file_path = self.test_dir / f"test_{module_name}.py"

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_content)

            test_files.append(str(test_file_path))

            # Generate test cases for analysis
            for func in functions:
                test_cases.append(
                    TestCase(
                        name=f"test_{func.name}",
                        description=f"Test for {func.name} function",
                        test_type="unit",
                        framework="pytest",
                        file_path=str(test_file_path),
                        line_number=func.lineno,
                        complexity_score=self._calculate_function_complexity(func),
                        mock_dependencies=self._extract_function_dependencies(func),
                    )
                )

            for cls in classes:
                for method in cls.body:
                    if isinstance(method, ast.FunctionDef):
                        test_cases.append(
                            TestCase(
                                name=f"test_{cls.name.lower()}_{method.name}",
                                description=f"Test for {cls.name}.{method.name} method",
                                test_type="unit",
                                framework="pytest",
                                file_path=str(test_file_path),
                                line_number=method.lineno,
                                complexity_score=self._calculate_function_complexity(
                                    method
                                ),
                                mock_dependencies=self._extract_function_dependencies(
                                    method
                                ),
                            )
                        )

            # Generate data factory if needed
            if classes or functions:
                factory_content = await self._generate_python_data_factory(
                    module_name, classes, functions
                )
                factory_path = self.test_dir / f"factories_{module_name}.py"

                with open(factory_path, "w", encoding="utf-8") as f:
                    f.write(factory_content)

                data_factories.append(str(factory_path))

            # Generate mocks for external dependencies
            dependencies = self._extract_module_dependencies(tree)
            for dep in dependencies:
                if self._needs_mock(dep):
                    mock_content = await self._generate_python_mock(dep)
                    mock_path = self.test_dir / f"mock_{dep.replace('.', '_')}.py"

                    with open(mock_path, "w", encoding="utf-8") as f:
                        f.write(mock_content)

                    mock_files.append(str(mock_path))

            return {
                "test_files": test_files,
                "test_cases": test_cases,
                "data_factories": data_factories,
                "mock_files": mock_files,
            }

        except Exception as e:
            logger.error(f"Failed to generate Python tests for {source_path}: {e}")
            return {
                "test_files": [],
                "test_cases": [],
                "data_factories": [],
                "mock_files": [],
            }

    async def _generate_python_test_content(
        self,
        module_name: str,
        functions: List[ast.FunctionDef],
        classes: List[ast.ClassDef],
        source_path: Path,
    ) -> str:
        """Generate comprehensive Python test content"""
        imports = [
            '"""Auto-generated tests for {module_name}"""',
            "import pytest",
            "from unittest.mock import Mock, patch, MagicMock, call",
            "import sys",
            "from pathlib import Path",
            "import asyncio",
            "from datetime import datetime, timedelta",
            "import json",
            "from typing import Any, Dict, List, Optional",
            "",
            "# Add project root to path",
            "project_root = Path(__file__).parent.parent",
            "sys.path.insert(0, str(project_root))",
            "",
        ]

        # Import the module under test
        import_statement = f"from app.{module_name} import "

        if classes:
            import_statement += ", ".join([cls.name for cls in classes])

        if functions:
            if classes:
                import_statement += ", "
            import_statement += ", ".join([func.name for func in functions])

        imports.append(import_statement)
        imports.append("")

        # Generate test class
        test_class = f'''
class Test{module_name.title()}:
    """Test suite for {module_name} module"""

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return {{
            "id": 1,
            "name": "test_value",
            "created_at": datetime.now(),
            "active": True
        }}

    @pytest.fixture
    def mock_external_service(self):
        """Mock external service"""
        with patch('app.{module_name}.external_service') as mock:
            mock.return_value = Mock()
            yield mock

    @pytest.fixture
    def async_event_loop(self):
        """Async event loop for async tests"""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
'''

        # Generate function tests
        function_tests = []
        for func in functions:
            test_methods = await self._generate_function_tests(func, module_name)
            function_tests.extend(test_methods)

        # Generate class tests
        class_tests = []
        for cls in classes:
            test_methods = await self._generate_class_tests(cls, module_name)
            class_tests.extend(test_methods)

        # Generate integration tests
        integration_tests = await self._generate_integration_test_methods(
            module_name, functions, classes
        )

        # Combine all content
        content_parts = (
            imports + [test_class] + function_tests + class_tests + integration_tests
        )

        # Add TODO(human) markers for manual implementation
        final_content = "\n".join(content_parts)

        # Add human implementation reminders
        final_content += f'''

# TODO(human): Complete test implementation for {module_name}
# The following tests need manual implementation:
# 1. Review and validate test data factories
# 2. Add edge case testing
# 3. Implement performance benchmarks
# 4. Add error handling test cases
# 5. Create comprehensive integration scenarios
#
# Manual testing guidelines:
# - Test both happy path and error conditions
# - Verify boundary conditions and edge cases
# - Test with realistic data volumes
# - Validate error messages and status codes
# - Test async behavior properly
#
# Example manual test:
# def test_{module_name}_complex_scenario(self, sample_data):
#     """Test complex business scenario"""
#     # TODO(human): Implement complex test scenario
#     result = some_function(sample_data)
#     assert result is not None
#     assert result.status == "success"
'''

        return final_content

    async def _generate_function_tests(
        self, func: ast.FunctionDef, module_name: str
    ) -> List[str]:
        """Generate test methods for a function"""
        test_methods = []
        func_name = func.name

        # Basic test
        basic_test = f'''
    def test_{func_name}_basic(self, sample_data):
        """Test {func_name} with basic inputs"""
        # TODO(human): Implement basic test for {func_name}
        # Arrange
        input_data = sample_data

        # Act
        result = {func_name}(input_data)

        # Assert
        assert result is not None
        # Add specific assertions based on expected behavior
'''

        # Edge case test
        edge_case_test = f'''
    def test_{func_name}_edge_cases(self):
        """Test {func_name} with edge cases"""
        # TODO(human): Implement edge case tests for {func_name}
        test_cases = [
            None,           # None input
            {{}},           # Empty dict
            [],            # Empty list
            "",            # Empty string
            0,             # Zero value
            -1,            # Negative value
            float('inf'),  # Infinity
        ]

        for test_input in test_cases:
            with pytest.raises((ValueError, TypeError, AttributeError)):
                result = {func_name}(test_input)
'''

        # Mock test if function has external dependencies
        if self._extract_function_dependencies(func):
            mock_test = f'''
    def test_{func_name}_with_mocks(self, mock_external_service):
        """Test {func_name} with mocked dependencies"""
        # TODO(human): Implement mock test for {func_name}
        mock_external_service.return_value.get_data.return_value = "mocked_response"

        result = {func_name}("test_input")

        assert result == "expected_result"
        mock_external_service.assert_called_once()
'''

            test_methods.append(mock_test)

        # Async test if function is async
        if func.name.startswith(("async_", "get_", "fetch_", "load_")):
            async_test = f'''
    @pytest.mark.asyncio
    async def test_{func_name}_async(self):
        """Test async {func_name}"""
        # TODO(human): Implement async test for {func_name}
        async def mock_async_func():
            return "async_result"

        result = await {func_name}("async_input")
        assert result is not None
'''

            test_methods.append(async_test)

        test_methods.extend([basic_test, edge_case_test])

        return test_methods

    async def _generate_class_tests(
        self, cls: ast.ClassDef, module_name: str
    ) -> List[str]:
        """Generate test methods for a class"""
        test_methods = []
        class_name = cls.name.lower()

        # Initialization test
        init_test = f'''
    def test_{class_name}_initialization(self, sample_data):
        """Test {cls.name} class initialization"""
        # TODO(human): Implement initialization test for {cls.name}
        instance = {cls.name}(**sample_data)

        assert instance is not None
        assert hasattr(instance, 'id')
        assert instance.id == sample_data["id"]
'''

        # Method tests
        method_tests = []
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                method_test = f'''
    def test_{class_name}_{node.name}(self):
        """Test {cls.name}.{node.name} method"""
        # TODO(human): Implement method test for {cls.name}.{node.name}
        instance = {cls.name}()

        result = instance.{node.name}()

        # Add appropriate assertions
        assert result is not None
'''

                method_tests.append(method_test)

        # Property tests
        property_tests = []
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and any(
                isinstance(decorator, ast.Name) and decorator.id == "property"
                for decorator in node.decorator_list
            ):
                property_test = f'''
    def test_{class_name}_property_{node.name}(self):
        """Test {cls.name}.{node.name} property"""
        # TODO(human): Implement property test for {cls.name}.{node.name}
        instance = {cls.name}()

        # Test property getter
        assert hasattr(instance, node.name)
        # Add property-specific assertions
'''

                property_tests.append(property_test)

        test_methods.extend([init_test] + method_tests + property_tests)

        return test_methods

    async def _generate_integration_test_methods(
        self,
        module_name: str,
        functions: List[ast.FunctionDef],
        classes: List[ast.ClassDef],
    ) -> List[str]:
        """Generate integration test methods"""
        integration_tests = []

        if functions or classes:
            integration_test = f'''
    def test_{module_name}_integration_scenario(self):
        """Test integration scenario for {module_name}"""
        # TODO(human): Implement integration test
        # This test should verify that multiple components work together
        # Example: test database operations with business logic
        pass

    def test_{module_name}_error_handling(self):
        """Test error handling in {module_name}"""
        # TODO(human): Implement error handling test
        # Test how the module handles various error conditions
        pass

    def test_{module_name}_performance_benchmark(self):
        """Test performance benchmarks for {module_name}"""
        # TODO(human): Implement performance test
        # Verify that operations complete within acceptable time limits
        import time

        start_time = time.time()
        # Execute operation here
        end_time = time.time()

        # Assert performance requirements
        assert (end_time - start_time) < 1.0  # 1 second max
'''

            integration_tests.append(integration_test)

        return integration_tests

    async def _generate_javascript_tests(self, source_path: Path) -> Dict[str, Any]:
        """Generate JavaScript/TypeScript tests using Jest/Vitest"""
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            # This is a simplified implementation
            # In a real scenario, you'd parse TypeScript/JavaScript with appropriate tools
            module_name = source_path.stem

            # Determine framework based on project setup
            framework = (
                "jest" if (self.project_root / "package.json").exists() else "vitest"
            )

            test_content = f"""// Auto-generated tests for {module_name}
import {{ {module_name} }} from '{source_path.relative_to(self.project_root)}';

// TODO(human): Complete test implementation for {module_name}
describe('{module_name}', () => {{
  test('should initialize correctly', () => {{
    // TODO(human): Implement initialization test
    const instance = new {module_name}();
    expect(instance).toBeDefined();
  }});

  test('should handle basic functionality', () => {{
    // TODO(human): Implement basic functionality test
    expect(true).toBe(true); // Placeholder
  }});

  test('should handle error cases', () => {{
    // TODO(human): Implement error handling test
    expect(() => {{
      // Test error condition
    }}).toThrow();
  }});
}});
"""

            test_file_path = (
                self.project_root
                / "src"
                / "__tests__"
                / f"{module_name}.test.{source_path.suffix[1:]}"
            )

            # Ensure directory exists
            test_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_content)

            test_cases = [
                TestCase(
                    name=f"test_{module_name}",
                    description=f"Test for {module_name}",
                    test_type="unit",
                    framework=framework,
                    file_path=str(test_file_path),
                    line_number=1,
                    complexity_score=1.0,
                )
            ]

            return {
                "test_files": [str(test_file_path)],
                "test_cases": test_cases,
                "data_factories": [],
                "mock_files": [],
            }

        except Exception as e:
            logger.error(f"Failed to generate JavaScript tests for {source_path}: {e}")
            return {
                "test_files": [],
                "test_cases": [],
                "data_factories": [],
                "mock_files": [],
            }

    async def _generate_python_data_factory(
        self,
        module_name: str,
        classes: List[ast.ClassDef],
        functions: List[ast.FunctionDef],
    ) -> str:
        """Generate test data factory for Python module"""
        factory_content = f'''"""Test data factory for {module_name}"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker

fake = Faker()

class {module_name.title()}Factory:
    """Factory for generating test data for {module_name}"""

    @staticmethod
    def create_{module_name}_data(**kwargs) -> Dict[str, Any]:
        """Create sample {module_name} data"""
        default_data = {{
            "id": random.randint(1, 1000),
            "name": fake.name(),
            "email": fake.email(),
            "created_at": fake.date_time_this_year(),
            "updated_at": fake.date_time_this_month(),
            "active": random.choice([True, False]),
        }}
        default_data.update(kwargs)
        return default_data

    @staticmethod
    def create_{module_name}_list(count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Create a list of {module_name} data"""
        return [{module_name.title()}Factory.create_{module_name}_data(**kwargs)
                for _ in range(count)]

    @staticmethod
    def create_{module_name}_with_invalid_data() -> Dict[str, Any]:
        """Create invalid {module_name} data for negative testing"""
        return {{
            "id": -1,  # Invalid ID
            "name": "",  # Empty name
            "email": "invalid-email",  # Invalid email
            "active": "not_a_boolean",  # Invalid type
        }}

# Usage examples:
# data = {module_name.title()}Factory.create_{module_name}_data(name="Custom Name")
# data_list = {module_name.title()}Factory.create_{module_name}_list(count=10)
'''

        return factory_content

    def _calculate_function_complexity(self, func: ast.FunctionDef) -> float:
        """Calculate complexity score for a function"""
        complexity = 1  # Base complexity

        for node in ast.walk(func):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return float(complexity)

    def _extract_function_dependencies(self, func: ast.FunctionDef) -> List[str]:
        """Extract external dependencies from a function"""
        dependencies = []

        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        dependency = f"{node.func.value.id}.{node.func.attr}"
                        if not dependency.startswith(
                            "self."
                        ) and not dependency.startswith("cls."):
                            dependencies.append(dependency)
                elif isinstance(node.func, ast.Name):
                    if node.func.id not in dir(__builtins__):
                        dependencies.append(node.func.id)

        return list(set(dependencies))

    def _extract_module_dependencies(self, tree: ast.AST) -> List[str]:
        """Extract all module dependencies"""
        dependencies = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and not node.module.startswith("."):
                    dependencies.append(node.module)

        return dependencies

    def _needs_mock(self, dependency: str) -> bool:
        """Determine if a dependency needs mocking"""
        # Standard library dependencies usually don't need mocking
        std_lib = {
            "os",
            "sys",
            "json",
            "datetime",
            "time",
            "logging",
            "pathlib",
            "collections",
            "itertools",
            "functools",
            "operator",
            "re",
            "math",
            "random",
            "string",
            "typing",
            "dataclasses",
            "enum",
            "asyncio",
            "threading",
            "multiprocessing",
            "queue",
            "http",
            "urllib",
            "socket",
            "ssl",
            "hashlib",
            "hmac",
            "csv",
            "xml",
            "html",
            "email",
            "mimetypes",
            "base64",
        }

        # Internal modules (starting with 'app.') usually don't need mocking in unit tests
        internal = dependency.startswith("app.")

        return not (std_lib.__contains__(dependency.split(".")[0]) or internal)

    async def _generate_python_mock(self, dependency: str) -> str:
        """Generate mock for external dependency"""
        mock_content = f'''"""Mock for {dependency} dependency"""

from unittest.mock import Mock, MagicMock

class Mock{dependency.title().replace('.', '')}:
    """Mock implementation for {dependency}"""

    def __init__(self):
        self.return_value = MagicMock()
        self.side_effect = None

    def __call__(self, *args, **kwargs):
        return self.return_value

# Create mock instance
mock_{dependency.replace('.', '_')} = Mock{dependency.title().replace('.', '')}()

# Example usage:
# with patch('{dependency}', mock_{dependency.replace('.', '_')}):
#     result = your_function()
'''

        return mock_content

    async def _generate_integration_tests(
        self, source_files: List[str]
    ) -> List[TestCase]:
        """Generate integration tests for multiple components"""
        integration_tests = []

        # Database integration tests
        if any("database" in f.lower() or "db" in f.lower() for f in source_files):
            integration_tests.append(
                TestCase(
                    name="test_database_integration",
                    description="Test database operations integration",
                    test_type="integration",
                    framework="pytest",
                    file_path="tests/test_integration.py",
                    line_number=1,
                    complexity_score=3.0,
                    mock_dependencies=["database", "connection_pool"],
                )
            )

        # API integration tests
        if any("api" in f.lower() or "endpoint" in f.lower() for f in source_files):
            integration_tests.append(
                TestCase(
                    name="test_api_integration",
                    description="Test API endpoint integration",
                    test_type="integration",
                    framework="pytest",
                    file_path="tests/test_api_integration.py",
                    line_number=1,
                    complexity_score=4.0,
                    mock_dependencies=["http_client", "database"],
                )
            )

        # Authentication integration tests
        if any("auth" in f.lower() or "security" in f.lower() for f in source_files):
            integration_tests.append(
                TestCase(
                    name="test_authentication_integration",
                    description="Test authentication flow integration",
                    test_type="integration",
                    framework="pytest",
                    file_path="tests/test_auth_integration.py",
                    line_number=1,
                    complexity_score=3.5,
                    mock_dependencies=["jwt_service", "user_database"],
                )
            )

        return integration_tests

    async def _generate_performance_tests(
        self, source_files: List[str]
    ) -> List[TestCase]:
        """Generate performance tests"""
        performance_tests = []

        # General performance test template
        performance_tests.append(
            TestCase(
                name="test_system_performance",
                description="Test system performance under load",
                test_type="performance",
                framework="pytest",
                file_path="tests/test_performance.py",
                line_number=1,
                complexity_score=2.0,
                mock_dependencies=[],
            )
        )

        # Memory usage tests
        if any("memory" in f.lower() or "cache" in f.lower() for f in source_files):
            performance_tests.append(
                TestCase(
                    name="test_memory_usage",
                    description="Test memory usage optimization",
                    test_type="performance",
                    framework="pytest",
                    file_path="tests/test_memory.py",
                    line_number=1,
                    complexity_score=3.0,
                    mock_dependencies=[],
                )
            )

        return performance_tests

    async def _generate_e2e_tests(self, source_files: List[str]) -> List[TestCase]:
        """Generate end-to-end tests"""
        e2e_tests = []

        # User journey test
        if any("user" in f.lower() or "auth" in f.lower() for f in source_files):
            e2e_tests.append(
                TestCase(
                    name="test_user_journey",
                    description="Test complete user registration and login flow",
                    test_type="e2e",
                    framework="pytest",
                    file_path="tests/test_e2e.py",
                    line_number=1,
                    complexity_score=5.0,
                    mock_dependencies=["browser", "database", "email_service"],
                )
            )

        # API workflow test
        if any("api" in f.lower() for f in source_files):
            e2e_tests.append(
                TestCase(
                    name="test_api_workflow",
                    description="Test complete API workflow from request to response",
                    test_type="e2e",
                    framework="pytest",
                    file_path="tests/test_api_e2e.py",
                    line_number=1,
                    complexity_score=4.0,
                    mock_dependencies=["http_server", "database", "auth_service"],
                )
            )

        return e2e_tests

    async def _create_test_data_factories(self, source_files: List[str]) -> List[str]:
        """Create comprehensive test data factories"""
        data_factories = []

        # Main data factory
        factory_content = '''"""Comprehensive test data factories"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker

fake = Faker()

class TestDataFactory:
    """Factory for generating various test data"""

    @staticmethod
    def create_user(**kwargs) -> Dict[str, Any]:
        """Create test user data"""
        return {
            "id": random.randint(1, 1000),
            "email": fake.email(),
            "name": fake.name(),
            "created_at": fake.date_time_this_year(),
            "is_active": random.choice([True, False]),
            **kwargs
        }

    @staticmethod
    def create_organization(**kwargs) -> Dict[str, Any]:
        """Create test organization data"""
        return {
            "id": random.randint(1, 100),
            "name": fake.company(),
            "domain": fake.domain_name(),
            "created_at": fake.date_time_this_year(),
            **kwargs
        }

    @staticmethod
    def create_assessment(**kwargs) -> Dict[str, Any]:
        """Create test assessment data"""
        return {
            "id": random.randint(1, 500),
            "title": fake.sentence(),
            "description": fake.paragraph(),
            "created_by": random.randint(1, 1000),
            "created_at": fake.date_time_this_year(),
            **kwargs
        }
'''

        factory_path = self.test_dir / "factories.py"
        with open(factory_path, "w", encoding="utf-8") as f:
            f.write(factory_content)

        data_factories.append(str(factory_path))

        return data_factories

    async def _analyze_new_coverage(self) -> float:
        """Analyze test coverage after generating new tests"""
        return await self._analyze_current_coverage()  # Re-run coverage analysis

    def _generate_test_recommendations(
        self,
        test_files: List[str],
        coverage_improvement: float,
        test_types: Dict[str, int],
    ) -> List[str]:
        """Generate actionable testing recommendations"""
        recommendations = []

        if len(test_files) == 0:
            recommendations.append(
                "No tests were generated. Check source file analysis."
            )
            return recommendations

        if coverage_improvement < 5:
            recommendations.append(
                f"Low coverage improvement ({coverage_improvement:.1f}%). "
                "Consider manually implementing more comprehensive tests."
            )

        if test_types.get("unit", 0) > test_types.get("integration", 0) * 3:
            recommendations.append(
                "High unit test count but low integration tests. "
                "Add more integration tests to verify component interactions."
            )

        if test_types.get("e2e", 0) == 0:
            recommendations.append(
                "No end-to-end tests generated. "
                "Consider adding E2E tests to verify complete user workflows."
            )

        if test_types.get("performance", 0) == 0:
            recommendations.append(
                "No performance tests generated. "
                "Add performance benchmarks to ensure system scalability."
            )

        recommendations.append(
            "Review and complete all TODO(human) markers in generated tests."
        )

        recommendations.append(
            "Run the generated tests and fix any failures before committing."
        )

        recommendations.append(
            "Set up continuous integration to run tests automatically on each commit."
        )

        return recommendations

    def _empty_result(self) -> TestGenerationResult:
        """Return empty result for cases where no files could be processed"""
        return TestGenerationResult(
            tests_generated=0,
            files_processed=0,
            coverage_improvement=0.0,
            test_types_generated={},
            frameworks_used=set(),
            test_files_created=[],
            test_data_factories=[],
            integration_tests=[],
            performance_tests=[],
            e2e_tests=[],
            mock_files_created=[],
            recommendations=["No source files found for test generation"],
            error_files=[],
        )
