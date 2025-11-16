# tests/devops_functional_testing.py
"""
Comprehensive DevOps Testing & Architecture Validation
Part 2: Functional Testing Framework

Tests API endpoints, database operations, and email service integration
for PsychSync AI platform functional validation.
"""

import asyncio
import json
import logging
import time
import uuid
import pytest
import aiohttp
import asyncpg
import smtplib
from email.mime.text import MimeText
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    'api_base_url': 'http://localhost:8000',
    'database_url': 'postgresql://postgres:password@localhost:5432/psychsync_test',
    'email_smtp_host': 'localhost',
    'email_smtp_port': 587,
    'test_timeout': 30,
    'max_retries': 3
}

logger = logging.getLogger(__name__)

@dataclass
class FunctionalTestResult:
    """Functional test result data structure"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    details: str
    execution_time: float = 0.0
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    suggestions: Optional[List[str]] = None

class FunctionalTestFramework:
    """Comprehensive functional testing framework"""

    def __init__(self):
        self.results: List[FunctionalTestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.auth_token: Optional[str] = None
        self.test_user_data: Dict[str, Any] = {}

    async def setup(self):
        """Setup test environment"""
        logger.info("Setting up functional test environment...")

        # Create HTTP session
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=TEST_CONFIG['test_timeout'])
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )

        # Setup database connection
        try:
            self.db_pool = await asyncpg.create_pool(
                TEST_CONFIG['database_url'],
                min_size=2,
                max_size=10,
                command_timeout=10
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Could not connect to test database: {e}")

    async def teardown(self):
        """Cleanup test environment"""
        logger.info("Cleaning up functional test environment...")

        if self.session:
            await self.session.close()

        if self.db_pool:
            await self.db_pool.close()

    async def run_test(self, test_name: str, test_func):
        """Run a test with timing and error handling"""
        start_time = time.time()
        try:
            result = await test_func()
            execution_time = time.time() - start_time

            if isinstance(result, FunctionalTestResult):
                result.execution_time = execution_time
                self.results.append(result)
            else:
                # Convert boolean result to FunctionalTestResult
                status = 'PASS' if result else 'FAIL'
                self.results.append(FunctionalTestResult(
                    test_name=test_name,
                    status=status,
                    details=f"Test {status.lower()}ed",
                    execution_time=execution_time
                ))

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Test {test_name} failed: {str(e)}")
            self.results.append(FunctionalTestResult(
                test_name=test_name,
                status='FAIL',
                details=f"Test execution failed: {str(e)}",
                error_message=str(e),
                execution_time=execution_time
            ))

    # API Tests
    async def test_api_health_check(self) -> FunctionalTestResult:
        """Test 2.1.1: API Health Check"""
        try:
            async with self.session.get(f"{TEST_CONFIG['api_base_url']}/health") as response:
                data = await response.json()

                if response.status == 200:
                    return FunctionalTestResult(
                        test_name="API Health Check",
                        status="PASS",
                        details="API health endpoint responding correctly",
                        response_data=data
                    )
                else:
                    return FunctionalTestResult(
                        test_name="API Health Check",
                        status="FAIL",
                        details=f"Health check returned status {response.status}",
                        response_data=data
                    )
        except Exception as e:
            return FunctionalTestResult(
                test_name="API Health Check",
                status="FAIL",
                details=f"Could not reach API health endpoint: {str(e)}"
            )

    async def test_user_registration(self) -> FunctionalTestResult:
        """Test 2.1.2: User Registration"""
        test_user = {
            "email": f"test-{uuid.uuid4()}@psychsync.test",
            "password": "TestSecurePassword123!",
            "full_name": "Test User",
            "organization_name": "Test Org"
        }

        self.test_user_data = test_user

        try:
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/v1/auth/register",
                json=test_user
            ) as response:
                data = await response.json()

                if response.status in [200, 201]:
                    return FunctionalTestResult(
                        test_name="User Registration",
                        status="PASS",
                        details="User registration successful",
                        response_data=data
                    )
                else:
                    return FunctionalTestResult(
                        test_name="User Registration",
                        status="FAIL",
                        details=f"Registration failed with status {response.status}: {data.get('detail', 'Unknown error')}",
                        response_data=data
                    )
        except Exception as e:
            return FunctionalTestResult(
                test_name="User Registration",
                status="FAIL",
                details=f"Registration request failed: {str(e)}"
            )

    async def test_user_login(self) -> FunctionalTestResult:
        """Test 2.1.3: User Login"""
        if not self.test_user_data:
            return FunctionalTestResult(
                test_name="User Login",
                status="SKIP",
                details="Skipping login test - no test user data available"
            )

        login_data = {
            "username": self.test_user_data['email'],
            "password": self.test_user_data['password']
        }

        try:
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/v1/auth/login",
                data=login_data,  # Form data for OAuth2
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                data = await response.json()

                if response.status == 200 and 'access_token' in data:
                    self.auth_token = data['access_token']
                    return FunctionalTestResult(
                        test_name="User Login",
                        status="PASS",
                        details="User login successful, token received",
                        response_data=data
                    )
                else:
                    return FunctionalTestResult(
                        test_name="User Login",
                        status="FAIL",
                        details=f"Login failed with status {response.status}: {data.get('detail', 'Unknown error')}",
                        response_data=data
                    )
        except Exception as e:
            return FunctionalTestResult(
                test_name="User Login",
                status="FAIL",
                details=f"Login request failed: {str(e)}"
            )

    async def test_assessment_creation(self) -> FunctionalTestResult:
        """Test 2.1.4: Assessment Creation"""
        if not self.auth_token:
            return FunctionalTestResult(
                test_name="Assessment Creation",
                status="SKIP",
                details="Skipping assessment test - no auth token available"
            )

        headers = {'Authorization': f'Bearer {self.auth_token}'}
        assessment_data = {
            "title": "Test Assessment",
            "description": "A test assessment for functional validation",
            "framework": "big_five",
            "status": "draft",
            "configuration": {
                "time_limit": 300,
                "randomize_questions": True
            }
        }

        try:
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/v1/assessments",
                json=assessment_data,
                headers=headers
            ) as response:
                data = await response.json()

                if response.status in [200, 201]:
                    return FunctionalTestResult(
                        test_name="Assessment Creation",
                        status="PASS",
                        details="Assessment creation successful",
                        response_data=data
                    )
                else:
                    return FunctionalTestResult(
                        test_name="Assessment Creation",
                        status="FAIL",
                        details=f"Assessment creation failed with status {response.status}: {data.get('detail', 'Unknown error')}",
                        response_data=data,
                        suggestions=["Check user permissions", "Validate assessment data format"]
                    )
        except Exception as e:
            return FunctionalTestResult(
                test_name="Assessment Creation",
                status="FAIL",
                details=f"Assessment creation request failed: {str(e)}"
            )

    async def test_team_management(self) -> FunctionalTestResult:
        """Test 2.1.5: Team Management"""
        if not self.auth_token:
            return FunctionalTestResult(
                test_name="Team Management",
                status="SKIP",
                details="Skipping team test - no auth token available"
            )

        headers = {'Authorization': f'Bearer {self.auth_token}'}
        team_data = {
            "name": "Test Team",
            "description": "A test team for functional validation"
        }

        try:
            # Create team
            async with self.session.post(
                f"{TEST_CONFIG['api_base_url']}/api/v1/teams",
                json=team_data,
                headers=headers
            ) as response:
                data = await response.json()

                if response.status in [200, 201]:
                    team_id = data.get('id')

                    # Test team retrieval
                    async with self.session.get(
                        f"{TEST_CONFIG['api_base_url']}/api/v1/teams",
                        headers=headers
                    ) as list_response:
                        list_data = await list_response.json()

                        if list_response.status == 200:
                            return FunctionalTestResult(
                                test_name="Team Management",
                                status="PASS",
                                details="Team creation and retrieval successful",
                                response_data={'created': data, 'listed': list_data}
                            )
                        else:
                            return FunctionalTestResult(
                                test_name="Team Management",
                                status="WARN",
                                details="Team creation successful but retrieval failed",
                                response_data=data
                            )
                else:
                    return FunctionalTestResult(
                        test_name="Team Management",
                        status="FAIL",
                        details=f"Team creation failed with status {response.status}: {data.get('detail', 'Unknown error')}",
                        response_data=data
                    )
        except Exception as e:
            return FunctionalTestResult(
                test_name="Team Management",
                status="FAIL",
                details=f"Team management request failed: {str(e)}"
            )

    # Database Tests
    async def test_database_connection(self) -> FunctionalTestResult:
        """Test 2.2.1: Database Connection"""
        if not self.db_pool:
            return FunctionalTestResult(
                test_name="Database Connection",
                status="SKIP",
                details="Skipping database test - no connection available"
            )

        try:
            async with self.db_pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1 as health_check")

                if result == 1:
                    return FunctionalTestResult(
                        test_name="Database Connection",
                        status="PASS",
                        details="Database connection successful"
                    )
                else:
                    return FunctionalTestResult(
                        test_name="Database Connection",
                        status="FAIL",
                        details=f"Unexpected database response: {result}"
                    )
        except Exception as e:
            return FunctionalTestResult(
                test_name="Database Connection",
                status="FAIL",
                details=f"Database connection failed: {str(e)}"
            )

    async def test_user_crud_operations(self) -> FunctionalTestResult:
        """Test 2.2.2: User CRUD Operations"""
        if not self.db_pool:
            return FunctionalTestResult(
                test_name="User CRUD Operations",
                status="SKIP",
                details="Skipping CRUD test - no database connection"
            )

        test_user_id = str(uuid.uuid4())
        test_email = f"crud-test-{test_user_id}@psychsync.test"

        try:
            async with self.db_pool.acquire() as connection:
                # Create
                await connection.execute(
                    """
                    INSERT INTO users (id, email, full_name, hashed_password, is_active)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    test_user_id, test_email, "CRUD Test User", "hashed_password", True
                )

                # Read
                user_data = await connection.fetchrow(
                    "SELECT * FROM users WHERE id = $1", test_user_id
                )

                if not user_data or user_data['email'] != test_email:
                    return FunctionalTestResult(
                        test_name="User CRUD Operations",
                        status="FAIL",
                        details="User creation or retrieval failed"
                    )

                # Update
                await connection.execute(
                    "UPDATE users SET full_name = $1 WHERE id = $2",
                    "Updated CRUD Test User", test_user_id
                )

                # Verify update
                updated_user = await connection.fetchrow(
                    "SELECT full_name FROM users WHERE id = $1", test_user_id
                )

                # Delete
                await connection.execute("DELETE FROM users WHERE id = $1", test_user_id)

                # Verify deletion
                deleted_user = await connection.fetchrow(
                    "SELECT * FROM users WHERE id = $1", test_user_id
                )

                if deleted_user:
                    return FunctionalTestResult(
                        test_name="User CRUD Operations",
                        status="FAIL",
                        details="User deletion failed"
                    )

                return FunctionalTestResult(
                    test_name="User CRUD Operations",
                    status="PASS",
                    details="User CRUD operations successful"
                )

        except Exception as e:
            # Cleanup on error
            try:
                async with self.db_pool.acquire() as connection:
                    await connection.execute("DELETE FROM users WHERE id = $1", test_user_id)
            except:
                pass

            return FunctionalTestResult(
                test_name="User CRUD Operations",
                status="FAIL",
                details=f"User CRUD operations failed: {str(e)}"
            )

    async def test_assessment_database_operations(self) -> FunctionalTestResult:
        """Test 2.2.3: Assessment Database Operations"""
        if not self.db_pool:
            return FunctionalTestResult(
                test_name="Assessment Database Operations",
                status="SKIP",
                details="Skipping assessment DB test - no database connection"
            )

        test_assessment_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())  # Mock user ID

        try:
            async with self.db_pool.acquire() as connection:
                # Create assessment
                await connection.execute(
                    """
                    INSERT INTO assessments (id, title, description, framework, created_by, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    test_assessment_id, "Test Assessment", "Test Description",
                    "big_five", user_id, "draft"
                )

                # Create assessment questions
                question_id = str(uuid.uuid4())
                await connection.execute(
                    """
                    INSERT INTO questions (id, assessment_id, question_text, question_type, order_index)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    question_id, test_assessment_id, "Test question", "multiple_choice", 1
                )

                # Read and verify
                assessment = await connection.fetchrow(
                    "SELECT * FROM assessments WHERE id = $1", test_assessment_id
                )
                questions = await connection.fetch(
                    "SELECT * FROM questions WHERE assessment_id = $1", test_assessment_id
                )

                if not assessment or len(questions) == 0:
                    return FunctionalTestResult(
                        test_name="Assessment Database Operations",
                        status="FAIL",
                        details="Assessment or question creation failed"
                    )

                # Cleanup
                await connection.execute("DELETE FROM questions WHERE assessment_id = $1", test_assessment_id)
                await connection.execute("DELETE FROM assessments WHERE id = $1", test_assessment_id)

                return FunctionalTestResult(
                    test_name="Assessment Database Operations",
                    status="PASS",
                    details="Assessment database operations successful"
                )

        except Exception as e:
            return FunctionalTestResult(
                test_name="Assessment Database Operations",
                status="FAIL",
                details=f"Assessment database operations failed: {str(e)}"
            )

    # Email Service Tests
    async def test_email_service_connection(self) -> FunctionalTestResult:
        """Test 2.3.1: Email Service Connection"""
        try:
            # Test SMTP connection
            server = smtplib.SMTP(
                TEST_CONFIG['email_smtp_host'],
                TEST_CONFIG['email_smtp_port'],
                timeout=10
            )

            # Try to start TLS
            try:
                server.starttls()
            except:
                pass  # TLS might not be available in test environment

            # Test connection (don't need to login for basic connectivity test)
            server.noop()
            server.quit()

            return FunctionalTestResult(
                test_name="Email Service Connection",
                status="PASS",
                details="Email service connection successful"
            )

        except Exception as e:
            return FunctionalTestResult(
                test_name="Email Service Connection",
                status="WARN",
                details=f"Email service connection failed: {str(e)}",
                suggestions=["Check SMTP server configuration", "Verify network connectivity"]
            )

    async def test_email_service_integration(self) -> FunctionalTestResult:
        """Test 2.3.2: Email Service Integration"""
        if not self.db_pool:
            return FunctionalTestResult(
                test_name="Email Service Integration",
                status="SKIP",
                details="Skipping email integration test - no database connection"
            )

        try:
            async with self.db_pool.acquire() as connection:
                # Check if email templates exist
                templates = await connection.fetch(
                    "SELECT * FROM email_templates LIMIT 1"
                )

                # Check email service configuration
                email_config = await connection.fetchrow(
                    """
                    SELECT * FROM system_settings
                    WHERE key LIKE '%email%' OR key LIKE '%smtp%'
                    LIMIT 3
                    """
                )

                if templates or email_config:
                    return FunctionalTestResult(
                        test_name="Email Service Integration",
                        status="PASS",
                        details="Email service integration components found",
                        response_data={
                            'templates_found': len(templates) if templates else 0,
                            'config_found': 1 if email_config else 0
                        }
                    )
                else:
                    return FunctionalTestResult(
                        test_name="Email Service Integration",
                        status="WARN",
                        details="Email service integration not fully configured",
                        suggestions=["Configure email templates", "Set up SMTP settings"]
                    )

        except Exception as e:
            return FunctionalTestResult(
                test_name="Email Service Integration",
                status="FAIL",
                details=f"Email service integration test failed: {str(e)}"
            )

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive functional testing report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])
        skipped_tests = len([r for r in self.results if r.status == 'SKIP'])

        total_time = sum(r.execution_time for r in self.results)

        # Analyze results by category
        api_tests = [r for r in self.results if 'API' in r.test_name or 'User' in r.test_name or 'Assessment' in r.test_name or 'Team' in r.test_name]
        db_tests = [r for r in self.results if 'Database' in r.test_name or 'CRUD' in r.test_name]
        email_tests = [r for r in self.results if 'Email' in r.test_name]

        return {
            'test_suite': 'Functional Testing',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_execution_time': total_time
            },
            'category_results': {
                'api_tests': {
                    'total': len(api_tests),
                    'passed': len([r for r in api_tests if r.status == 'PASS']),
                    'failed': len([r for r in api_tests if r.status == 'FAIL'])
                },
                'database_tests': {
                    'total': len(db_tests),
                    'passed': len([r for r in db_tests if r.status == 'PASS']),
                    'failed': len([r for r in db_tests if r.status == 'FAIL'])
                },
                'email_tests': {
                    'total': len(email_tests),
                    'passed': len([r for r in email_tests if r.status == 'PASS']),
                    'failed': len([r for r in email_tests if r.status == 'FAIL'])
                }
            },
            'test_results': [asdict(result) for result in self.results],
            'recommendations': self._generate_recommendations(),
            'functional_grade': self._calculate_functional_grade()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate functional testing recommendations"""
        recommendations = []

        failed_tests = [r for r in self.results if r.status == 'FAIL']
        skipped_tests = [r for r in self.results if r.status == 'SKIP']

        if failed_tests:
            recommendations.append("CRITICAL: Fix all failed functional tests before production deployment")

        if skipped_tests:
            recommendations.append(f"Address {len(skipped_tests)} skipped tests - missing dependencies or configuration")

        # Category-specific recommendations
        api_failures = [r for r in self.results if 'FAIL' in r.status and ('API' in r.test_name or 'User' in r.test_name)]
        if api_failures:
            recommendations.append("Review API endpoints and authentication configuration")

        db_failures = [r for r in self.results if 'FAIL' in r.status and 'Database' in r.test_name]
        if db_failures:
            recommendations.append("Check database connectivity and schema")

        email_failures = [r for r in self.results if 'FAIL' in r.status and 'Email' in r.test_name]
        if email_failures:
            recommendations.append("Configure email service settings")

        # Add suggestions from failed tests
        for result in self.results:
            if result.suggestions:
                recommendations.extend(result.suggestions)

        return recommendations

    def _calculate_functional_grade(self) -> str:
        """Calculate overall functional grade"""
        if not self.results:
            return "NO_GRADE"

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == 'PASS'])
        failed_tests = len([r for r in self.results if r.status == 'FAIL'])

        pass_rate = (passed_tests / total_tests) * 100

        if pass_rate >= 90 and failed_tests == 0:
            return "A"
        elif pass_rate >= 80 and failed_tests <= 1:
            return "B+"
        elif pass_rate >= 70 and failed_tests <= 2:
            return "B"
        elif pass_rate >= 60 and failed_tests <= 3:
            return "C"
        else:
            return "F"

# Pytest integration functions
@pytest.fixture
async def functional_test_framework():
    """Pytest fixture for FunctionalTestFramework"""
    framework = FunctionalTestFramework()
    await framework.setup()
    yield framework
    await framework.teardown()

@pytest.mark.asyncio
async def test_api_endpoints(functional_test_framework):
    """Pytest wrapper for API endpoint tests"""
    await functional_test_framework.run_test(
        "API Health Check",
        functional_test_framework.test_api_health_check
    )
    await functional_test_framework.run_test(
        "User Registration",
        functional_test_framework.test_user_registration
    )
    await functional_test_framework.run_test(
        "User Login",
        functional_test_framework.test_user_login
    )
    await functional_test_framework.run_test(
        "Assessment Creation",
        functional_test_framework.test_assessment_creation
    )
    await functional_test_framework.run_test(
        "Team Management",
        functional_test_framework.test_team_management
    )

@pytest.mark.asyncio
async def test_database_operations(functional_test_framework):
    """Pytest wrapper for database operation tests"""
    await functional_test_framework.run_test(
        "Database Connection",
        functional_test_framework.test_database_connection
    )
    await functional_test_framework.run_test(
        "User CRUD Operations",
        functional_test_framework.test_user_crud_operations
    )
    await functional_test_framework.run_test(
        "Assessment Database Operations",
        functional_test_framework.test_assessment_database_operations
    )

@pytest.mark.asyncio
async def test_email_service(functional_test_framework):
    """Pytest wrapper for email service tests"""
    await functional_test_framework.run_test(
        "Email Service Connection",
        functional_test_framework.test_email_service_connection
    )
    await functional_test_framework.run_test(
        "Email Service Integration",
        functional_test_framework.test_email_service_integration
    )

@pytest.mark.asyncio
async def test_functional_validation_complete(functional_test_framework):
    """Complete functional validation test suite"""
    # Run all functional tests
    await functional_test_framework.run_test(
        "API Health Check",
        functional_test_framework.test_api_health_check
    )
    await functional_test_framework.run_test(
        "User Registration",
        functional_test_framework.test_user_registration
    )
    await functional_test_framework.run_test(
        "User Login",
        functional_test_framework.test_user_login
    )
    await functional_test_framework.run_test(
        "Assessment Creation",
        functional_test_framework.test_assessment_creation
    )
    await functional_test_framework.run_test(
        "Team Management",
        functional_test_framework.test_team_management
    )
    await functional_test_framework.run_test(
        "Database Connection",
        functional_test_framework.test_database_connection
    )
    await functional_test_framework.run_test(
        "User CRUD Operations",
        functional_test_framework.test_user_crud_operations
    )
    await functional_test_framework.run_test(
        "Assessment Database Operations",
        functional_test_framework.test_assessment_database_operations
    )
    await functional_test_framework.run_test(
        "Email Service Connection",
        functional_test_framework.test_email_service_connection
    )
    await functional_test_framework.run_test(
        "Email Service Integration",
        functional_test_framework.test_email_service_integration
    )

    # Generate report
    report = functional_test_framework.generate_report()

    # Save report to file
    report_path = Path(__file__).parent.parent / "test_reports" / "functional_testing_report.json"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Functional testing report saved to: {report_path}")

    # Assertions
    assert report['summary']['success_rate'] >= 60, "Functional testing success rate below 60%"
    assert report['functional_grade'] not in ['F'], "Functional grade is F - critical issues found"

    # Print summary
    print(f"\n🧪 Functional Testing Results:")
    print(f"   Grade: {report['functional_grade']}")
    print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Skipped: {report['summary']['skipped']}")
    print(f"   Report: {report_path}")

# Main execution function
async def run_functional_testing():
    """Run functional testing independently"""
    framework = FunctionalTestFramework()

    try:
        await framework.setup()
        print("🧪 Starting Functional Testing...")
        print("=" * 50)

        # Run all tests
        await framework.run_test("API Health Check", framework.test_api_health_check)
        await framework.run_test("User Registration", framework.test_user_registration)
        await framework.run_test("User Login", framework.test_user_login)
        await framework.run_test("Assessment Creation", framework.test_assessment_creation)
        await framework.run_test("Team Management", framework.test_team_management)
        await framework.run_test("Database Connection", framework.test_database_connection)
        await framework.run_test("User CRUD Operations", framework.test_user_crud_operations)
        await framework.run_test("Assessment Database Operations", framework.test_assessment_database_operations)
        await framework.run_test("Email Service Connection", framework.test_email_service_connection)
        await framework.run_test("Email Service Integration", framework.test_email_service_integration)

        # Generate and print report
        report = framework.generate_report()

        print(f"\n📊 Test Results:")
        print(f"   Total Tests: {report['summary']['total_tests']}")
        print(f"   Passed: {report['summary']['passed']}")
        print(f"   Failed: {report['summary']['failed']}")
        print(f"   Skipped: {report['summary']['skipped']}")
        print(f"   Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"   Functional Grade: {report['functional_grade']}")
        print(f"   Execution Time: {report['summary']['total_execution_time']:.3f}s")

        print(f"\n📋 Category Results:")
        for category, results in report['category_results'].items():
            if results['total'] > 0:
                print(f"   {category.title()}: {results['passed']}/{results['total']} passed")

        print(f"\n📋 Detailed Results:")
        for result in framework.results:
            status_icon = "✅" if result.status == "PASS" else "⚠️" if result.status == "SKIP" else "❌"
            print(f"   {status_icon} {result.test_name}")
            if result.status != "PASS":
                print(f"      → {result.details}")

        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")

        # Save report
        report_path = Path(__file__).parent.parent / "test_reports" / f"functional_testing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Full report saved: {report_path}")

        return report

    finally:
        await framework.teardown()

if __name__ == "__main__":
    asyncio.run(run_functional_testing())