"""
Automated UI Testing Service
Provides comprehensive automated UI testing integration with multiple testing frameworks
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from pathlib import Path
import subprocess
import traceback
from typing import Any
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class TestFramework(Enum):
    """Supported automated testing frameworks"""

    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    CYPRESS = "cypress"
    TESTCAFE = "testcafe"
    PUPPETEER = "puppeteer"
    WEBDRIVERIO = "webdriverio"


class TestType(Enum):
    """Types of UI tests"""

    SMOKE = "smoke"
    REGRESSION = "regression"
    E2E = "e2e"
    VISUAL = "visual"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    RESPONSIVE = "responsive"
    INTEGRATION = "integration"


class BrowserType(Enum):
    """Supported browsers for testing"""

    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"
    HEADLESS = "headless"


class TestStatus(Enum):
    """Test execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"


class PriorityLevel(Enum):
    """Test priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestSuite:
    """Test suite configuration and metadata"""

    id: str
    name: str
    description: str
    framework: TestFramework
    test_type: TestType
    target_browsers: list[BrowserType]
    test_files: list[str]
    setup_commands: list[str] = field(default_factory=list)
    teardown_commands: list[str] = field(default_factory=list)
    environment_config: dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # 5 minutes default
    retry_count: int = 0
    parallel_execution: bool = True
    max_parallel_tests: int = 4
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestCase:
    """Individual test case definition"""

    id: str
    suite_id: str
    name: str
    description: str
    file_path: str
    test_type: TestType
    priority: PriorityLevel
    estimated_duration: int  # seconds
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    expected_results: dict[str, Any] = field(default_factory=dict)
    test_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestExecution:
    """Test execution record"""

    id: str
    test_suite_id: str
    test_case_id: str | None
    framework: TestFramework
    browser: BrowserType
    environment: str
    status: TestStatus
    start_time: datetime
    end_time: datetime | None = None
    duration: float | None = None
    error_message: str | None = None
    stack_trace: str | None = None
    screenshots: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    retry_count: int = 0
    execution_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Complete test execution results"""

    execution_id: str
    test_suite: TestSuite
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    success_rate: float
    browser_coverage: dict[str, int]
    framework_version: str
    environment_info: dict[str, Any]
    detailed_results: list[TestExecution] = field(default_factory=list)
    artifacts: dict[str, list[str]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class VisualTestComparison:
    """Visual regression test comparison result"""

    test_id: str
    baseline_image: str
    current_image: str
    diff_image: str
    pixel_difference: int
    percentage_difference: float
    passed_threshold: bool
    threshold: float = 0.1  # 10% difference threshold


class AutomatedUITestingService:
    """Comprehensive automated UI testing service"""

    def __init__(self):
        self.test_suites: dict[str, TestSuite] = {}
        self.test_cases: dict[str, TestCase] = {}
        self.test_executions: dict[str, TestExecution] = {}
        self.test_results: dict[str, TestResult] = {}
        self.framework_configs: dict[TestFramework, dict[str, Any]] = {}

        # Initialize framework configurations
        self._initialize_framework_configs()

        # Initialize default test suites
        self._initialize_default_suites()

    def _initialize_framework_configs(self):
        """Initialize configurations for different testing frameworks"""
        self.framework_configs[TestFramework.SELENIUM] = {
            "driver_path": "/usr/local/bin/chromedriver",
            "default_timeout": 30,
            "page_load_timeout": 60,
            "implicit_wait": 10,
            "screenshot_format": "png",
            "video_recording": True,
            "capabilities": {
                "chrome": {
                    "browserName": "chrome",
                    "chromeOptions": {
                        "args": ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]
                    },
                },
                "firefox": {
                    "browserName": "firefox",
                    "moz:firefoxOptions": {"args": ["-headless"]},
                },
            },
        }

        self.framework_configs[TestFramework.PLAYWRIGHT] = {
            "timeout": 30000,
            "expect_timeout": 5000,
            "trace": "on-first-retry",
            "screenshot": "only-on-failure",
            "video": "retain-on-failure",
            "devices": [
                "Desktop Chrome",
                "Desktop Firefox",
                "Desktop Safari",
                "iPhone 12",
                "iPad Pro",
            ],
        }

        self.framework_configs[TestFramework.CYPRESS] = {
            "defaultCommandTimeout": 10000,
            "requestTimeout": 10000,
            "responseTimeout": 10000,
            "viewportWidth": 1280,
            "viewportHeight": 720,
            "video": true,
            "screenshotOnRunFailure": True,
            "chromeWebSecurity": False,
            "projectId": "psychsync-uitests",
        }

    def _initialize_default_suites(self):
        """Initialize default test suites"""
        # Smoke test suite
        smoke_suite = TestSuite(
            id="smoke_tests",
            name="Smoke Tests",
            description="Critical functionality tests to verify basic system operation",
            framework=TestFramework.PLAYWRIGHT,
            test_type=TestType.SMOKE,
            target_browsers=[BrowserType.CHROME, BrowserType.FIREFOX],
            test_files=["tests/ui/smoke/login.test.js", "tests/ui/smoke/dashboard.test.js"],
            priority=["critical"],
            timeout=300,
            retry_count=1,
        )
        self.test_suites[smoke_suite.id] = smoke_suite

        # Regression test suite
        regression_suite = TestSuite(
            id="regression_tests",
            name="Regression Tests",
            description="Comprehensive regression tests for existing functionality",
            framework=TestFramework.SELENIUM,
            test_type=TestType.REGRESSION,
            target_browsers=[BrowserType.CHROME, BrowserType.FIREFOX, BrowserType.EDGE],
            test_files=[
                "tests/ui/auth/auth_flow.test.js",
                "tests/ui/assessments/assessment_workflow.test.js",
                "tests/ui/team_management/team_features.test.js",
                "tests/ui/reports/report_generation.test.js",
            ],
            timeout=600,
            retry_count=2,
            parallel_execution=True,
            max_parallel_tests=3,
        )
        self.test_suites[regression_suite.id] = regression_suite

        # Visual regression test suite
        visual_suite = TestSuite(
            id="visual_regression_tests",
            name="Visual Regression Tests",
            description="Visual regression tests to detect UI changes",
            framework=TestFramework.PLAYWRIGHT,
            test_type=TestType.VISUAL,
            target_browsers=[BrowserType.CHROME],
            test_files=[
                "tests/ui/visual/dashboard_visual.test.js",
                "tests/ui/visual/forms_visual.test.js",
            ],
            timeout=400,
            retry_count=1,
            parallel_execution=False,  # Visual tests typically run sequentially
        )
        self.test_suites[visual_suite.id] = visual_suite

        # Accessibility test suite
        accessibility_suite = TestSuite(
            id="accessibility_tests",
            name="Accessibility Tests",
            description="Automated accessibility compliance tests",
            framework=TestFramework.PLAYWRIGHT,
            test_type=TestType.ACCESSIBILITY,
            target_browsers=[BrowserType.CHROME],
            test_files=["tests/ui/accessibility/a11y_compliance.test.js"],
            timeout=300,
            retry_count=1,
            environment_config={"axe-core": True, "wcag": "2.1AA"},
        )
        self.test_suites[accessibility_suite.id] = accessibility_suite

    async def create_test_suite(
        self,
        name: str,
        description: str,
        framework: TestFramework,
        test_type: TestType,
        test_files: list[str],
        target_browsers: list[BrowserType],
        **kwargs,
    ) -> TestSuite:
        """Create a new test suite"""
        suite = TestSuite(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            framework=framework,
            test_type=test_type,
            target_browsers=target_browsers,
            test_files=test_files,
            **kwargs,
        )

        self.test_suites[suite.id] = suite
        logger.info(f"Created test suite: {suite.id} - {name}")

        return suite

    async def add_test_case(
        self,
        suite_id: str,
        name: str,
        description: str,
        file_path: str,
        test_type: TestType,
        priority: PriorityLevel,
        **kwargs,
    ) -> TestCase | None:
        """Add a test case to a test suite"""
        if suite_id not in self.test_suites:
            logger.error(f"Test suite not found: {suite_id}")
            return None

        test_case = TestCase(
            id=str(uuid.uuid4()),
            suite_id=suite_id,
            name=name,
            description=description,
            file_path=file_path,
            test_type=test_type,
            priority=priority,
            **kwargs,
        )

        self.test_cases[test_case.id] = test_case
        logger.info(f"Added test case: {test_case.id} to suite {suite_id}")

        return test_case

    async def execute_test_suite(
        self,
        suite_id: str,
        browsers: list[BrowserType] | None = None,
        environment: str = "test",
        parallel: bool | None = None,
    ) -> TestResult:
        """Execute a complete test suite"""
        if suite_id not in self.test_suites:
            raise ValueError(f"Test suite not found: {suite_id}")

        suite = self.test_suites[suite_id]
        browsers = browsers or suite.target_browsers
        parallel = parallel if parallel is not None else suite.parallel_execution

        logger.info(
            f"Starting test suite execution: {suite.name} on browsers {[b.value for b in browsers]}"
        )

        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())

        # Prepare execution environment
        await self._prepare_execution_environment(suite, environment)

        # Execute tests
        test_executions = []

        if parallel:
            test_executions = await self._execute_tests_parallel(
                suite, browsers, environment, execution_id
            )
        else:
            test_executions = await self._execute_tests_sequential(
                suite, browsers, environment, execution_id
            )

        # Calculate results
        total_tests = len(test_executions)
        passed_tests = len([t for t in test_executions if t.status == TestStatus.PASSED])
        failed_tests = len([t for t in test_executions if t.status == TestStatus.FAILED])
        skipped_tests = len([t for t in test_executions if t.status == TestStatus.SKIPPED])
        error_tests = len([t for t in test_executions if t.status == TestStatus.ERROR])

        total_duration = sum(t.duration or 0 for t in test_executions)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        browser_coverage = {}
        for execution in test_executions:
            browser = execution.browser.value
            browser_coverage[browser] = browser_coverage.get(browser, 0) + 1

        # Generate recommendations
        recommendations = await self._generate_test_recommendations(test_executions)

        # Collect artifacts
        artifacts = await self._collect_test_artifacts(test_executions)

        result = TestResult(
            execution_id=execution_id,
            test_suite=suite,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            total_duration=total_duration,
            success_rate=success_rate,
            browser_coverage=browser_coverage,
            framework_version=await self._get_framework_version(suite.framework),
            environment_info=await self._get_environment_info(environment),
            detailed_results=test_executions,
            artifacts=artifacts,
            recommendations=recommendations,
        )

        self.test_results[execution_id] = result

        logger.info(
            f"Test suite execution completed: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)"
        )
        return result

    async def _prepare_execution_environment(self, suite: TestSuite, environment: str):
        """Prepare the test execution environment"""
        # Create test directories
        test_dirs = ["test-results", "screenshots", "videos", "logs"]
        for test_dir in test_dirs:
            Path(test_dir).mkdir(parents=True, exist_ok=True)

        # Setup environment variables
        env_vars = {
            "TEST_ENVIRONMENT": environment,
            "TEST_SUITE_ID": suite.id,
            "TEST_FRAMEWORK": suite.framework.value,
        }

        # Merge suite environment config
        env_vars.update(suite.environment_config)

        # Run setup commands
        for command in suite.setup_commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    env={**env_vars},
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command)
            except subprocess.CalledProcessError as e:
                logger.error(f"Setup command failed: {command} - {e!s}")
                raise

    async def _execute_tests_parallel(
        self, suite: TestSuite, browsers: list[BrowserType], environment: str, execution_id: str
    ) -> list[TestExecution]:
        """Execute tests in parallel across browsers"""
        tasks = []

        for browser in browsers:
            for test_file in suite.test_files:
                task = self._execute_single_test(
                    suite, test_file, browser, environment, execution_id
                )
                tasks.append(task)

                # Limit parallel tasks
                if len(tasks) >= suite.max_parallel_tests:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    tasks = []  # Clear for next batch

        # Execute remaining tasks
        if tasks:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect and return all execution results
        return [
            e
            for e in self.test_executions.values()
            if e.execution_context.get("execution_id") == execution_id
        ]

    async def _execute_tests_sequential(
        self, suite: TestSuite, browsers: list[BrowserType], environment: str, execution_id: str
    ) -> list[TestExecution]:
        """Execute tests sequentially"""
        executions = []

        for browser in browsers:
            for test_file in suite.test_files:
                execution = await self._execute_single_test(
                    suite, test_file, browser, environment, execution_id
                )
                executions.append(execution)

        return executions

    async def _execute_single_test(
        self,
        suite: TestSuite,
        test_file: str,
        browser: BrowserType,
        environment: str,
        execution_id: str,
    ) -> TestExecution:
        """Execute a single test"""
        execution = TestExecution(
            id=str(uuid.uuid4()),
            test_suite_id=suite.id,
            test_case_id=None,
            framework=suite.framework,
            browser=browser,
            environment=environment,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
            execution_context={"execution_id": execution_id, "test_file": test_file},
        )

        self.test_executions[execution.id] = execution

        try:
            # Build test command based on framework
            command = await self._build_test_command(suite, test_file, browser, environment)

            # Execute test
            result = await self._run_test_command(command, suite.timeout)

            # Process results
            execution.end_time = datetime.utcnow()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()

            if result["exit_code"] == 0:
                execution.status = TestStatus.PASSED
            else:
                execution.status = TestStatus.FAILED
                execution.error_message = result.get("stderr", "")[-500:]  # Last 500 chars
                execution.stack_trace = result.get("stderr", "")

            # Collect artifacts
            execution.screenshots = await self._find_screenshots(execution.id)
            execution.videos = await self._find_videos(execution.id)
            execution.logs = await self._find_logs(execution.id)

            # Extract performance metrics if available
            execution.performance_metrics = await self._extract_performance_metrics(result)

        except TimeoutError:
            execution.status = TestStatus.TIMEOUT
            execution.end_time = datetime.utcnow()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.error_message = f"Test timed out after {suite.timeout} seconds"

        except Exception as e:
            execution.status = TestStatus.ERROR
            execution.end_time = datetime.utcnow()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.error_message = str(e)
            execution.stack_trace = traceback.format_exc()

        logger.info(f"Test execution completed: {execution.id} - {execution.status.value}")
        return execution

    async def _build_test_command(
        self, suite: TestSuite, test_file: str, browser: BrowserType, environment: str
    ) -> str:
        """Build test execution command based on framework"""
        config = self.framework_configs[suite.framework]

        if suite.framework == TestFramework.PLAYWRIGHT:
            command = f"npx playwright test {test_file}"
            command += f" --project={browser.value}"
            command += f" --output-dir=test-results/{suite.id}"
            if config.get("trace"):
                command += f" --trace={config['trace']}"
            if config.get("screenshot"):
                command += f" --screenshot={config['screenshot']}"
            if config.get("video"):
                command += f" --video={config['video']}"

        elif suite.framework == TestFramework.SELENIUM:
            command = f"python -m pytest {test_file}"
            command += f" --browser={browser.value}"
            command += f" --html=test-results/{suite.id}/report.html"
            command += " --self-contained-html"
            command += " --tb=short"

        elif suite.framework == TestFramework.CYPRESS:
            command = f"npx cypress run --spec {test_file}"
            command += f" --browser {browser.value}"
            command += " --config video=true,screenshotOnRunFailure=true"

        else:
            # Default command
            command = f"npm test -- {test_file}"

        # Add environment variables
        env_vars = f"TEST_ENV={environment} TEST_BROWSER={browser.value} TEST_SUITE={suite.id}"

        return f"{env_vars} {command}"

    async def _run_test_command(self, command: str, timeout: int) -> dict[str, Any]:
        """Execute test command and return results"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=settings.PROJECT_ROOT,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
            }

        except TimeoutError:
            # Kill the process if it times out
            if "process" in locals():
                process.kill()
                await process.wait()
            raise

    async def _find_screenshots(self, execution_id: str) -> list[str]:
        """Find screenshot files for execution"""
        screenshot_dir = Path("test-results") / execution_id / "screenshots"
        if not screenshot_dir.exists():
            return []

        return [
            str(f)
            for f in screenshot_dir.glob("**/*")
            if f.suffix.lower() in [".png", ".jpg", ".jpeg"]
        ]

    async def _find_videos(self, execution_id: str) -> list[str]:
        """Find video files for execution"""
        video_dir = Path("test-results") / execution_id / "videos"
        if not video_dir.exists():
            return []

        return [str(f) for f in video_dir.glob("**/*") if f.suffix.lower() in [".mp4", ".webm"]]

    async def _find_logs(self, execution_id: str) -> list[str]:
        """Find log files for execution"""
        log_dir = Path("test-results") / execution_id / "logs"
        if not log_dir.exists():
            return []

        return [str(f) for f in log_dir.glob("**/*") if f.suffix.lower() in [".log", ".txt"]]

    async def _extract_performance_metrics(self, test_result: dict[str, Any]) -> dict[str, float]:
        """Extract performance metrics from test results"""
        metrics = {}
        stdout = test_result.get("stdout", "")

        # Extract common performance metrics
        if "page_load_time:" in stdout:
            try:
                metrics["page_load_time"] = float(stdout.split("page_load_time:")[1].split()[0])
            except (IndexError, ValueError):
                pass

        if "time_to_interactive:" in stdout:
            try:
                metrics["time_to_interactive"] = float(
                    stdout.split("time_to_interactive:")[1].split()[0]
                )
            except (IndexError, ValueError):
                pass

        return metrics

    async def _generate_test_recommendations(
        self, test_executions: list[TestExecution]
    ) -> list[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        failed_tests = [t for t in test_executions if t.status == TestStatus.FAILED]
        slow_tests = [t for t in test_executions if t.duration and t.duration > 300]  # > 5 minutes

        if len(failed_tests) > len(test_executions) * 0.3:  # More than 30% failure rate
            recommendations.append(
                "High failure rate detected. Consider reviewing test environment and application stability."
            )

        if slow_tests:
            recommendations.append(
                f"{len(slow_tests)} tests exceeded 5 minutes. Consider optimizing test performance or breaking down large tests."
            )

        # Check for browser-specific issues
        browser_failures = {}
        for execution in failed_tests:
            browser = execution.browser.value
            browser_failures[browser] = browser_failures.get(browser, 0) + 1

        for browser, count in browser_failures.items():
            if count > 2:  # More than 2 failures in same browser
                recommendations.append(
                    f"Multiple test failures detected in {browser}. Check for browser-specific compatibility issues."
                )

        return recommendations

    async def _collect_test_artifacts(
        self, test_executions: list[TestExecution]
    ) -> dict[str, list[str]]:
        """Collect all test artifacts"""
        artifacts = {"screenshots": [], "videos": [], "logs": [], "reports": []}

        for execution in test_executions:
            artifacts["screenshots"].extend(execution.screenshots)
            artifacts["videos"].extend(execution.videos)
            artifacts["logs"].extend(execution.logs)

        # Find report files
        report_dir = Path("test-results")
        if report_dir.exists():
            artifacts["reports"] = [str(f) for f in report_dir.glob("**/*.html")]

        return artifacts

    async def _get_framework_version(self, framework: TestFramework) -> str:
        """Get version of testing framework"""
        try:
            if framework == TestFramework.PLAYWRIGHT:
                result = await asyncio.create_subprocess_shell(
                    "npx playwright --version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await result.communicate()
                return stdout.decode("utf-8").strip()

            if framework == TestFramework.SELENIUM:
                result = await asyncio.create_subprocess_shell(
                    "pip show selenium",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await result.communicate()
                for line in stdout.decode("utf-8").split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":")[1].strip()

            elif framework == TestFramework.CYPRESS:
                result = await asyncio.create_subprocess_shell(
                    "npx cypress --version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await result.communicate()
                return stdout.decode("utf-8").strip()

        except Exception as e:
            logger.error(f"Failed to get framework version: {e!s}")

        return "Unknown"

    async def _get_environment_info(self, environment: str) -> dict[str, Any]:
        """Get environment information"""
        return {
            "name": environment,
            "os": "Linux",  # Would detect actual OS
            "python_version": "3.9+",  # Would detect actual version
            "node_version": "16+",  # Would detect actual version
            "browser_versions": {
                "chrome": "Latest",
                "firefox": "Latest",
                "safari": "Latest",
                "edge": "Latest",
            },
        }

    async def run_visual_regression_tests(
        self, baseline_dir: str, current_dir: str, output_dir: str, threshold: float = 0.1
    ) -> list[VisualTestComparison]:
        """Run visual regression tests"""
        comparisons = []

        baseline_path = Path(baseline_dir)
        current_path = Path(current_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find all baseline images
        for baseline_file in baseline_path.glob("**/*"):
            if baseline_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                # Find corresponding current image
                relative_path = baseline_file.relative_to(baseline_path)
                current_file = current_path / relative_path

                if current_file.exists():
                    comparison = await self._compare_images(
                        str(baseline_file),
                        str(current_file),
                        str(output_path / relative_path),
                        threshold,
                    )
                    comparisons.append(comparison)

        return comparisons

    async def _compare_images(
        self, baseline_path: str, current_path: str, output_path: str, threshold: float
    ) -> VisualTestComparison:
        """Compare two images and generate diff"""
        # This would integrate with an image comparison library like Pillow or ImageMagick
        # For now, returning a placeholder comparison

        comparison_id = str(uuid.uuid4())
        diff_path = output_path.replace(".", "_diff.")

        return VisualTestComparison(
            test_id=comparison_id,
            baseline_image=baseline_path,
            current_image=current_path,
            diff_image=diff_path,
            pixel_difference=0,  # Would calculate actual difference
            percentage_difference=0.0,  # Would calculate actual percentage
            passed_threshold=True,
            threshold=threshold,
        )

    async def get_test_execution_history(
        self, suite_id: str | None = None, days: int = 30, status: TestStatus | None = None
    ) -> list[TestExecution]:
        """Get test execution history"""
        executions = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        for execution in self.test_executions.values():
            if execution.start_time < cutoff_date:
                continue

            if suite_id and execution.test_suite_id != suite_id:
                continue

            if status and execution.status != status:
                continue

            executions.append(execution)

        return sorted(executions, key=lambda x: x.start_time, reverse=True)

    async def generate_test_report(self, execution_id: str, report_format: str = "html") -> str:
        """Generate comprehensive test report"""
        if execution_id not in self.test_results:
            raise ValueError(f"Test result not found: {execution_id}")

        result = self.test_results[execution_id]

        if report_format == "html":
            return await self._generate_html_report(result)
        if report_format == "json":
            return await self._generate_json_report(result)
        raise ValueError(f"Unsupported report format: {report_format}")

    async def _generate_html_report(self, result: TestResult) -> str:
        """Generate HTML test report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {suite_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
                .passed {{ background: #d4edda; }}
                .failed {{ background: #f8d7da; }}
                .skipped {{ background: #fff3cd; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Execution Report</h1>
                <h2>{suite_name}</h2>
                <p>Execution ID: {execution_id}</p>
                <p>Generated: {timestamp}</p>
            </div>

            <div class="summary">
                <div class="metric">
                    <h3>{total_tests}</h3>
                    <p>Total Tests</p>
                </div>
                <div class="metric passed">
                    <h3>{passed_tests}</h3>
                    <p>Passed</p>
                </div>
                <div class="metric failed">
                    <h3>{failed_tests}</h3>
                    <p>Failed</p>
                </div>
                <div class="metric skipped">
                    <h3>{skipped_tests}</h3>
                    <p>Skipped</p>
                </div>
                <div class="metric">
                    <h3>{success_rate:.1f}%</h3>
                    <p>Success Rate</p>
                </div>
            </div>

            <h3>Test Details</h3>
            <table>
                <tr>
                    <th>Test ID</th>
                    <th>Browser</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Error Message</th>
                </tr>
                {test_rows}
            </table>

            <h3>Recommendations</h3>
            <ul>
                {recommendations}
            </ul>
        </body>
        </html>
        """

        # Generate table rows
        test_rows = ""
        for execution in result.detailed_results:
            status_class = execution.status.value
            error_msg = (
                execution.error_message[:100] + "..."
                if execution.error_message and len(execution.error_message) > 100
                else execution.error_message or ""
            )

            test_rows += f"""
            <tr>
                <td>{execution.id[:8]}</td>
                <td>{execution.browser.value}</td>
                <td class="{status_class}">{execution.status.value}</td>
                <td>{execution.duration or 0:.2f}</td>
                <td>{error_msg}</td>
            </tr>
            """

        # Generate recommendations
        recommendations = "\n".join([f"<li>{rec}</li>" for rec in result.recommendations])

        return html_template.format(
            suite_name=result.test_suite.name,
            execution_id=result.execution_id,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_tests=result.total_tests,
            passed_tests=result.passed_tests,
            failed_tests=result.failed_tests,
            skipped_tests=result.skipped_tests,
            success_rate=result.success_rate,
            test_rows=test_rows,
            recommendations=recommendations,
        )

    async def _generate_json_report(self, result: TestResult) -> str:
        """Generate JSON test report"""
        report_data = {
            "execution_id": result.execution_id,
            "test_suite": {
                "id": result.test_suite.id,
                "name": result.test_suite.name,
                "framework": result.test_suite.framework.value,
                "test_type": result.test_suite.test_type.value,
            },
            "summary": {
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "skipped_tests": result.skipped_tests,
                "error_tests": result.error_tests,
                "success_rate": result.success_rate,
                "total_duration": result.total_duration,
            },
            "environment": result.environment_info,
            "browser_coverage": result.browser_coverage,
            "framework_version": result.framework_version,
            "recommendations": result.recommendations,
            "detailed_results": [
                {
                    "id": execution.id,
                    "browser": execution.browser.value,
                    "status": execution.status.value,
                    "duration": execution.duration,
                    "error_message": execution.error_message,
                    "screenshots": execution.screenshots,
                    "performance_metrics": execution.performance_metrics,
                }
                for execution in result.detailed_results
            ],
            "artifacts": result.artifacts,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return json.dumps(report_data, indent=2)


# Initialize the automated UI testing service
automated_ui_testing_service = AutomatedUITestingService()
