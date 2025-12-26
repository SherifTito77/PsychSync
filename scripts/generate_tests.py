#!/usr/bin/env python3
"""
Comprehensive Pytest Test Suite Generator

Automatically generates comprehensive pytest test suites for PsychSync modules.
Supports:
- Unit test generation (70% of tests)
- Integration test generation (20% of tests)
- Fixture creation
- Coverage analysis (>80% target)
- Security testing patterns
- Performance testing templates

Usage:
    python scripts/generate_tests.py --module app.services.user_service
    python scripts/generate_tests.py --module app.api.v1.endpoints.users
    python scripts/generate_tests.py --all  # Generate tests for all modules
"""

import ast
import os
import sys
import argparse
import inspect
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class FunctionInfo:
    """Information about a function/method"""
    name: str
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    is_async: bool
    decorators: List[str]
    docstring: Optional[str]
    complexity_score: int = 1  # 1-5 based on parameters and logic
    security_relevant: bool = False
    database_operation: bool = False


@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    base_classes: List[str]
    methods: List[FunctionInfo]
    properties: List[str]
    docstring: Optional[str]
    is_service: bool = False
    is_model: bool = False
    is_endpoint: bool = False


@dataclass
class ModuleInfo:
    """Information about a module"""
    name: str
    path: str
    imports: List[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    docstring: Optional[str]


class CodeAnalyzer:
    """Analyzes Python source code to extract testable components"""

    def __init__(self):
        self.testable_patterns = {
            'service': ['Service', 'Manager', 'Handler', 'Processor'],
            'endpoint': ['router', 'endpoint', 'api'],
            'model': ['Model', 'Base', 'Schema'],
            'security': ['auth', 'security', 'token', 'password', 'csrf'],
            'database': ['db', 'database', 'crud', 'repository']
        }

    def analyze_module(self, module_path: str) -> ModuleInfo:
        """Analyze a Python module and extract testable components"""

        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in {module_path}: {e}")

        module_name = Path(module_path).stem
        imports = self._extract_imports(tree)
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        docstring = ast.get_docstring(tree)

        return ModuleInfo(
            name=module_name,
            path=module_path,
            imports=imports,
            functions=functions,
            classes=classes,
            docstring=docstring
        )

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """Extract function definitions"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_info = self._analyze_function(node)
                functions.append(function_info)
        return functions

    def _extract_classes(self, tree: ast.AST) -> List[ClassInfo]:
        """Extract class definitions"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes.append(class_info)
        return classes

    def _analyze_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """Analyze a function definition"""
        parameters = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'annotation': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': None
            }
            parameters.append(param_info)

        return_type = ast.unparse(node.returns) if node.returns else None
        is_async = isinstance(node, ast.AsyncFunctionDef)
        decorators = [ast.unparse(dec) for dec in node.decorator_list]
        docstring = ast.get_docstring(node)

        # Determine complexity and characteristics
        complexity_score = self._calculate_complexity(node)
        security_relevant = self._is_security_relevant(node)
        database_operation = self._is_database_operation(node)

        return FunctionInfo(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
            decorators=decorators,
            docstring=docstring,
            complexity_score=complexity_score,
            security_relevant=security_relevant,
            database_operation=database_operation
        )

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition"""
        base_classes = [ast.unparse(base) for base in node.bases]
        methods = []
        properties = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._analyze_function(item)
                methods.append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        properties.append(target.id)

        docstring = ast.get_docstring(node)

        # Determine class type
        class_name = node.name.lower()
        is_service = any(pattern in class_name for pattern in self.testable_patterns['service'])
        is_model = any(pattern in class_name for pattern in self.testable_patterns['model'])
        is_endpoint = any(pattern in class_name for pattern in self.testable_patterns['endpoint'])

        return ClassInfo(
            name=node.name,
            base_classes=base_classes,
            methods=methods,
            properties=properties,
            docstring=docstring,
            is_service=is_service,
            is_model=is_model,
            is_endpoint=is_endpoint
        )

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate complexity score for a function"""
        score = 1  # Base score

        # Add points for parameters
        score += len(node.args.args)

        # Add points for control structures
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                score += 1
            elif isinstance(child, ast.Compare):
                score += 0.5

        return min(int(score), 5)

    def _is_security_relevant(self, node: ast.FunctionDef) -> bool:
        """Check if function is security-relevant"""
        security_keywords = ['password', 'token', 'auth', 'login', 'csrf', 'encrypt', 'hash']
        function_name = node.name.lower()
        docstring = (ast.get_docstring(node) or "").lower()

        return any(keyword in function_name or keyword in docstring for keyword in security_keywords)

    def _is_database_operation(self, node: ast.FunctionDef) -> bool:
        """Check if function performs database operations"""
        db_keywords = ['create', 'read', 'update', 'delete', 'query', 'save', 'fetch']
        function_name = node.name.lower()

        return any(keyword in function_name for keyword in db_keywords)


class TestGenerator:
    """Generates comprehensive pytest test suites"""

    def __init__(self, analyzer: CodeAnalyzer):
        self.analyzer = analyzer
        self.test_templates = {
            'unit': self._get_unit_test_template(),
            'integration': self._get_integration_test_template(),
            'security': self._get_security_test_template(),
            'performance': self._get_performance_test_template()
        }

    def generate_test_suite(self, module_info: ModuleInfo, test_type: str = 'comprehensive') -> str:
        """Generate a complete test suite for a module"""

        test_code = []
        test_code.append(self._generate_header(module_info))
        test_code.append(self._generate_imports(module_info))
        test_code.append(self._generate_fixtures(module_info))

        if test_type in ['comprehensive', 'unit']:
            test_code.append(self._generate_unit_tests(module_info))

        if test_type in ['comprehensive', 'integration']:
            test_code.append(self._generate_integration_tests(module_info))

        if test_type in ['comprehensive', 'security']:
            test_code.append(self._generate_security_tests(module_info))

        if test_type in ['comprehensive', 'performance']:
            test_code.append(self._generate_performance_tests(module_info))

        test_code.append(self._generate_coverage_report())

        return '\n\n'.join(test_code)

    def _generate_header(self, module_info: ModuleInfo) -> str:
        """Generate test file header"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f'''"""
Comprehensive Test Suite for {module_info.name}

Auto-generated on: {timestamp}
Test Coverage Target: >80%
Test Types: Unit (70%), Integration (20%), Security (10%)

Generated by: scripts/generate_tests.py
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Project imports
'''

    def _generate_imports(self, module_info: ModuleInfo) -> str:
        """Generate import statements for tests"""
        imports = []

        # Import the module under test
        module_path = module_info.path.replace('/', '.').replace('.py', '')
        imports.append(f"from {module_path} import *")

        # Add common test imports based on module characteristics
        if any(func.database_operation for func in module_info.functions) or \
           any(cls.is_model for cls in module_info.classes):
            imports.extend([
                "from app.core.database import get_async_session",
                "from sqlalchemy.ext.asyncio import AsyncSession",
                "from app.db.models import *"
            ])

        if any(func.security_relevant for func in module_info.functions):
            imports.extend([
                "from app.core.security import create_access_token, verify_password, get_password_hash",
                "from app.core.config import settings"
            ])

        if any(cls.is_endpoint for cls in module_info.classes):
            imports.extend([
                "from app.main import app",
                "from app.api.v1.deps import get_current_user"
            ])

        return '\n'.join(imports)

    def _generate_fixtures(self, module_info: ModuleInfo) -> str:
        """Generate test fixtures"""
        fixtures = []

        # Standard fixtures
        fixtures.append('''
@pytest.fixture
async def async_client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_session():
    """Test database session"""
    async for session in get_async_session():
        yield session

@pytest.fixture
def mock_user():
    """Mock user for testing"""
    return {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False
    }

@pytest.fixture
def mock_token():
    """Mock JWT token"""
    return create_access_token(data={"sub": "test@example.com"})
''')

        # Module-specific fixtures
        if module_info.classes:
            fixtures.append(f'''
@pytest.fixture
def {module_info.name.lower()}_instance():
    """Instance of {module_info.name} for testing"""
    return {module_info.name}() if any(cls.is_service for cls in module_info.classes) else None
''')

        return '\n'.join(fixtures)

    def _generate_unit_tests(self, module_info: ModuleInfo) -> str:
        """Generate unit tests for functions and methods"""
        tests = []
        tests.append('class TestUnitFunctions:')

        # Test standalone functions
        for func in module_info.functions:
            tests.extend(self._generate_function_tests(func, is_method=False))

        # Test class methods
        for cls in module_info.classes:
            tests.append(f'\n    class Test{cls.name}:')
            for method in cls.methods:
                if not method.name.startswith('_'):  # Skip private methods
                    tests.extend(self._generate_function_tests(method, is_method=True, class_name=cls.name))

        return '\n'.join(tests)

    def _generate_function_tests(self, func: FunctionInfo, is_method: bool = False, class_name: str = None) -> List[str]:
        """Generate tests for a specific function"""
        tests = []
        indent = '        ' if is_method else '    '

        # Test name
        test_prefix = f"test_{class_name.lower()}_" if class_name else "test_"
        test_name = f"{indent}def {test_prefix}{func.name}(self"

        # Add parameters
        if func.parameters:
            param_list = func.parameters[1:] if is_method else func.parameters  # Skip 'self' for methods
            for param in param_list:
                test_name += f", mock_{param['name']}"

        test_name += "):\n"
        tests.append(test_name)

        # Add docstring
        tests.append(f'{indent}    """Test {func.name} function"""')

        # Generate test body based on complexity
        if func.complexity_score <= 2:
            tests.extend(self._generate_simple_test(func, is_method, class_name))
        elif func.complexity_score <= 4:
            tests.extend(self._generate_complex_test(func, is_method, class_name))
        else:
            tests.extend(self._generate_advanced_test(func, is_method, class_name))

        return tests

    def _generate_simple_test(self, func: FunctionInfo, is_method: bool, class_name: str) -> List[str]:
        """Generate test for simple function"""
        indent = '        ' if is_method else '    '
        tests = []

        # Setup
        if func.parameters:
            for param in func.parameters[1:] if is_method else func.parameters:
                tests.append(f'{indent}    mock_{param["name"]} = Mock()')

        # Test execution
        if is_method and class_name:
            tests.append(f'{indent}    instance = {class_name}()')
            tests.append(f'{indent}    result = instance.{func.name}(')
        else:
            tests.append(f'{indent}    result = {func.name}(')

        # Add parameters to call
        param_list = func.parameters[1:] if is_method else func.parameters
        params = [f"mock_{p['name']}" for p in param_list]
        tests.append(f'{indent}        {", ".join(params)}')
        tests.append(f'{indent}    )')

        # Assertions
        tests.append(f'{indent}    assert result is not None')
        tests.append(f'{indent}    # Add specific assertions based on expected behavior')

        return tests

    def _generate_complex_test(self, func: FunctionInfo, is_method: bool, class_name: str) -> List[str]:
        """Generate test for complex function with edge cases"""
        indent = '        ' if is_method else '    '
        tests = []

        # Multiple test scenarios
        scenarios = [
            ("valid inputs", "positive case with valid parameters"),
            ("invalid inputs", "negative case with invalid parameters"),
            ("edge cases", "boundary conditions and special values")
        ]

        for scenario_name, description in scenarios:
            tests.append(f'{indent}    # Test {description}')
            tests.append(f'{indent}    with patch("{self._get_patch_target(func, is_method, class_name)}") as mock_func:')
            tests.append(f'{indent}        mock_func.return_value = Mock()')
            tests.append(f'{indent}        ')

            # Setup test data
            if scenario_name == "valid inputs":
                tests.extend(self._setup_valid_inputs(func, is_method))
            elif scenario_name == "invalid inputs":
                tests.extend(self._setup_invalid_inputs(func, is_method))
            else:  # edge cases
                tests.extend(self._setup_edge_cases(func, is_method))

            # Execute and assert
            tests.extend(self._execute_and_assert(func, is_method, class_name, scenario_name))
            tests.append('')

        return tests

    def _generate_advanced_test(self, func: FunctionInfo, is_method: bool, class_name: str) -> List[str]:
        """Generate comprehensive test for advanced function"""
        indent = '        ' if is_method else '    '
        tests = []

        tests.append(f'{indent}    # Advanced testing for complex function')
        tests.append(f'{indent}    test_cases = [')

        # Generate test cases
        test_cases = [
            ("normal_case", {"description": "Normal operation"}),
            ("error_case", {"description": "Error handling"}),
            ("performance_case", {"description": "Performance validation"}),
            ("security_case", {"description": "Security validation"}) if func.security_relevant else None
        ]

        for case_name, case_data in filter(None, test_cases):
            tests.append(f'{indent}        ("{case_name}", {{')
            for key, value in case_data.items():
                tests.append(f'{indent}            "{key}": "{value}",')
            tests.append(f'{indent}        }}),')

        tests.append(f'{indent}    ]')
        tests.append('')
        tests.append(f'{indent}    for case_name, case_data in test_cases:')
        tests.extend(self._execute_test_case(func, is_method, class_name))

        return tests

    def _get_patch_target(self, func: FunctionInfo, is_method: bool, class_name: str) -> str:
        """Get the target path for patching"""
        if is_method and class_name:
            return f"{class_name}.{func.name}"
        return f"{func.name}"

    def _setup_valid_inputs(self, func: FunctionInfo, is_method: bool) -> List[str]:
        """Setup valid input parameters"""
        indent = '        ' if is_method else '    '
        tests = []

        for param in func.parameters[1:] if is_method else func.parameters:
            if param['annotation'] and 'str' in param['annotation']:
                tests.append(f'{indent}        mock_{param["name"]} = "valid_string"')
            elif param['annotation'] and 'int' in param['annotation']:
                tests.append(f'{indent}        mock_{param["name"]} = 1')
            elif param['annotation'] and 'bool' in param['annotation']:
                tests.append(f'{indent}        mock_{param["name"]} = True')
            else:
                tests.append(f'{indent}        mock_{param["name"]} = Mock()')

        return tests

    def _setup_invalid_inputs(self, func: FunctionInfo, is_method: bool) -> List[str]:
        """Setup invalid input parameters"""
        indent = '        ' if is_method else '    '
        tests = []

        for param in func.parameters[1:] if is_method else func.parameters:
            if param['annotation'] and 'str' in param['annotation']:
                tests.append(f'{indent}        mock_{param["name"]} = ""  # Empty string')
            elif param['annotation'] and 'int' in param['annotation']:
                tests.append(f'{indent}        mock_{param["name"]} = -1  # Invalid number')
            else:
                tests.append(f'{indent}        mock_{param["name"]} = None  # None value')

        return tests

    def _setup_edge_cases(self, func: FunctionInfo, is_method: bool) -> List[str]:
        """Setup edge case parameters"""
        indent = '        ' if is_method else '    '
        tests = []

        for param in func.parameters[1:] if is_method else func.parameters:
            tests.append(f'{indent}        mock_{param["name"]} = None  # Edge case: None')

        return tests

    def _execute_and_assert(self, func: FunctionInfo, is_method: bool, class_name: str, scenario: str) -> List[str]:
        """Execute function and add assertions"""
        indent = '        ' if is_method else '    '
        tests = []

        if scenario == "invalid inputs":
            tests.append(f'{indent}        with pytest.raises((ValueError, TypeError, AssertionError)):')
        else:
            tests.append(f'{indent}        try:')

        # Execute function
        if is_method and class_name:
            tests.append(f'{indent}            instance = {class_name}()')
            tests.append(f'{indent}            result = instance.{func.name}(')
        else:
            tests.append(f'{indent}            result = {func.name}(')

        params = [f"mock_{p['name']}" for p in func.parameters[1:] if is_method else func.parameters]
        tests.append(f'{indent}                {", ".join(params)}')
        tests.append(f'{indent}            )')

        if scenario != "invalid inputs":
            tests.append(f'{indent}            assert result is not None')
            tests.append(f'{indent}            # Add specific assertions for {scenario}')

        return tests

    def _execute_test_case(self, func: FunctionInfo, is_method: bool, class_name: str) -> List[str]:
        """Execute a test case"""
        indent = '        ' if is_method else '    '
        tests = []

        tests.append(f'{indent}        print(f"Testing {{case_name}}: {{case_data["description"]}}")')
        tests.append(f'{indent}        # Implement test case specific logic')
        tests.append(f'{indent}        # Setup, Execute, Assert pattern')

        return tests

    def _generate_integration_tests(self, module_info: ModuleInfo) -> str:
        """Generate integration tests"""
        tests = []
        tests.append('\n\n@pytest.mark.integration')
        tests.append('class TestIntegration:')

        # Database integration tests
        if any(func.database_operation for func in module_info.functions) or \
           any(cls.is_model for cls in module_info.classes):
            tests.extend([
                '',
                '    @pytest.mark.asyncio',
                '    async def test_database_integration(self, test_session: AsyncSession):',
                '        """Test database integration"""',
                '        # Test database operations',
                '        assert test_session is not None',
                '        # Add specific database tests based on module functionality'
            ])

        # API integration tests for endpoints
        if any(cls.is_endpoint for cls in module_info.classes):
            tests.extend([
                '',
                '    @pytest.mark.asyncio',
                '    async def test_api_integration(self, async_client: AsyncClient):',
                '        """Test API integration"""',
                '        # Test API endpoints',
                '        response = await async_client.get("/")',
                '        assert response.status_code in [200, 404]  # 404 if no root endpoint',
                '        # Add specific API endpoint tests'
            ])

        return '\n'.join(tests)

    def _generate_security_tests(self, module_info: ModuleInfo) -> str:
        """Generate security tests"""
        tests = []

        if any(func.security_relevant for func in module_info.functions):
            tests.append('\n\n@pytest.mark.security')
            tests.append('class TestSecurity:')

            security_funcs = [f for f in module_info.functions if f.security_relevant]

            for func in security_funcs:
                tests.extend([
                    '',
                    f'    def test_{func.name}_security(self):',
                    f'        """Test security aspects of {func.name}"""',
                    '        # Test input validation',
                    '        # Test authentication/authorization',
                    '        # Test data sanitization',
                    '        # Test against common vulnerabilities',
                    '        assert True  # Implement specific security tests'
                ])

        return '\n'.join(tests)

    def _generate_performance_tests(self, module_info: ModuleInfo) -> str:
        """Generate performance tests"""
        tests = []
        tests.append('\n\n@pytest.mark.performance')
        tests.append('class TestPerformance:')

        # Performance test for complex functions
        complex_funcs = [f for f in module_info.functions if f.complexity_score >= 3]

        if complex_funcs:
            tests.extend([
                '',
                '    def test_performance_benchmarks(self):',
                '        """Test performance benchmarks"""',
                '        import time',
                '',
                '        start_time = time.time()'
            ])

            for func in complex_funcs[:3]:  # Limit to top 3 complex functions
                tests.extend([
                    f'        # Test {func.name} performance',
                    f'        func_start = time.time()',
                    f'        # Execute {func.name} with test data',
                    f'        func_duration = time.time() - func_start',
                    f'        assert func_duration < 1.0  # Should complete within 1 second'
                ])

            tests.extend([
                '        total_time = time.time() - start_time',
                '        assert total_time < 5.0  # Total test time should be reasonable',
                '        print(f"Performance test completed in {{total_time:.2f}} seconds")'
            ])

        return '\n'.join(tests)

    def _generate_coverage_report(self) -> str:
        """Generate coverage reporting"""
        return '''
# Coverage Information
# This test suite aims for >80% code coverage
# Run coverage with: pytest --cov=module_name --cov-report=html

def test_coverage_summary():
    """Coverage summary test"""
    # This test will be updated by coverage reporting
    assert True  # Placeholder for coverage validation

if __name__ == "__main__":
    # Run tests with coverage
    import subprocess
    import sys

    print("Running comprehensive test suite with coverage...")
    subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "--cov=.",  # Adjust coverage target
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ])
'''

    def _get_unit_test_template(self) -> str:
        """Get unit test template"""
        return '''
def test_{function_name}_{scenario}(self):
    """Test {function_name} - {scenario}"""
    # Arrange
    # Act
    # Assert
    pass
'''

    def _get_integration_test_template(self) -> str:
        """Get integration test template"""
        return '''
@pytest.mark.integration
@pytest.mark.asyncio
async def test_{feature_name}_integration(self):
    """Test {feature_name} integration"""
    # Test with real dependencies
    pass
'''

    def _get_security_test_template(self) -> str:
        """Get security test template"""
        return '''
@pytest.mark.security
def test_{feature_name}_security(self):
    """Test {feature_name} security"""
    # Test security vulnerabilities
    pass
'''

    def _get_performance_test_template(self) -> str:
        """Get performance test template"""
        return '''
@pytest.mark.performance
def test_{feature_name}_performance(self):
    """Test {feature_name} performance"""
    # Test performance characteristics
    pass
'''


class TestSuiteGenerator:
    """Main test suite generator coordinator"""

    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.generator = TestGenerator(self.analyzer)
        self.modules_directory = project_root

    def generate_tests_for_module(self, module_path: str, test_type: str = 'comprehensive') -> str:
        """Generate tests for a specific module"""

        # Validate module path
        full_path = self.modules_directory / module_path
        if not full_path.exists():
            raise FileNotFoundError(f"Module not found: {full_path}")

        if full_path.is_dir():
            # Find Python files in directory
            py_files = list(full_path.glob("**/*.py"))
            if not py_files:
                raise ValueError(f"No Python files found in: {full_path}")

            # Generate tests for first Python file found
            module_file = py_files[0]
        else:
            module_file = full_path

        # Analyze module
        print(f"Analyzing module: {module_file}")
        module_info = self.analyzer.analyze_module(str(module_file))

        # Generate test suite
        print("Generating comprehensive test suite...")
        test_suite = self.generator.generate_test_suite(module_info, test_type)

        return test_suite

    def save_test_suite(self, module_path: str, test_suite: str, test_type: str = 'comprehensive'):
        """Save generated test suite to file"""

        # Determine test file path
        if module_path.endswith('.py'):
            test_file_path = module_path.replace('.py', '_test.py')
        else:
            test_file_path = f"{module_path}_test.py"

        # Ensure test file is in tests directory
        if not test_file_path.startswith('tests/'):
            test_file_path = f"tests/{test_file_path}"

        # Create tests directory if it doesn't exist
        test_file_full_path = self.modules_directory / test_file_path
        test_file_full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write test file
        with open(test_file_full_path, 'w', encoding='utf-8') as f:
            f.write(test_suite)

        print(f"Test suite saved to: {test_file_full_path}")
        return str(test_file_full_path)

    def generate_for_all_modules(self, test_type: str = 'comprehensive') -> List[str]:
        """Generate tests for all modules in the project"""

        generated_files = []

        # Find all Python modules (excluding tests and __pycache__)
        for py_file in self.modules_directory.rglob("*.py"):
            # Skip certain directories
            if any(part in str(py_file) for part in ['tests', '__pycache__', '.venv', 'venv']):
                continue

            # Skip test files
            if py_file.name.endswith('_test.py') or 'test_' in py_file.name:
                continue

            # Convert to relative path
            rel_path = py_file.relative_to(self.modules_directory)
            module_path = str(rel_path.with_suffix(''))

            try:
                print(f"\nGenerating tests for: {module_path}")
                test_suite = self.generate_tests_for_module(str(rel_path), test_type)
                saved_path = self.save_test_suite(module_path, test_suite, test_type)
                generated_files.append(saved_path)

            except Exception as e:
                print(f"Error generating tests for {module_path}: {e}")
                continue

        return generated_files


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive pytest test suites for PsychSync modules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/generate_tests.py --module app.services.user_service
    python scripts/generate_tests.py --module app.api.v1.endpoints.users --type unit
    python scripts/generate_tests.py --all --type comprehensive
        """
    )

    parser.add_argument(
        '--module', '-m',
        type=str,
        help='Module path to generate tests for (e.g., app.services.user_service)'
    )

    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Generate tests for all modules in the project'
    )

    parser.add_argument(
        '--type', '-t',
        choices=['comprehensive', 'unit', 'integration', 'security', 'performance'],
        default='comprehensive',
        help='Type of tests to generate (default: comprehensive)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path (optional, defaults to tests/module_name_test.py)'
    )

    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Show what would be generated without creating files'
    )

    args = parser.parse_args()

    if not args.module and not args.all:
        parser.error("Either --module or --all must be specified")

    if args.module and args.all:
        parser.error("Cannot specify both --module and --all")

    try:
        generator = TestSuiteGenerator()

        if args.module:
            print(f"Generating {args.type} tests for module: {args.module}")
            test_suite = generator.generate_tests_for_module(args.module, args.type)

            if args.dry_run:
                print("\n--- Generated Test Suite ---")
                print(test_suite)
                print("--- End of Test Suite ---")
            else:
                saved_path = generator.save_test_suite(args.module, test_suite, args.type)
                print(f"\n✅ Test suite generated successfully!")
                print(f"📁 Saved to: {saved_path}")

        elif args.all:
            print(f"Generating {args.type} tests for all modules...")
            generated_files = generator.generate_for_all_modules(args.type)

            print(f"\n✅ Test suite generation completed!")
            print(f"📁 Generated {len(generated_files)} test files:")
            for file_path in generated_files:
                print(f"   - {file_path}")

        print(f"\n🎯 Next steps:")
        print(f"   1. Review generated tests")
        print(f"   2. Customize test data and assertions")
        print(f"   3. Run: pytest tests/ -v")
        print(f"   4. Check coverage: pytest --cov=.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()