"""
Manual QA & Testing Service
Provides comprehensive testing frameworks for manual QA, UAT, and accessibility testing
"""

from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    DEFERRED = "deferred"


class TestPriority(str, Enum):
    """Test priority levels"""

    CRITICAL = "critical"  # Blocks release
    HIGH = "high"  # Important functionality
    MEDIUM = "medium"  # Standard testing
    LOW = "low"  # Nice to have


class TestCategory(str, Enum):
    """Test categories for organization"""

    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    COMPATIBILITY = "compatibility"
    COMPLIANCE = "compliance"
    SMOKE = "smoke"
    SANITY = "sanity"


class TestExecution:
    """Individual test execution result"""

    def __init__(
        self,
        test_id: str,
        title: str,
        category: TestCategory,
        priority: TestPriority,
        description: str,
        steps: list[str],
        expected_result: str,
        actual_result: str = None,
        status: TestStatus = TestStatus.PENDING,
        assigned_to: str = None,
        environment: str = "staging",
        browser: str = "chrome",
        test_data: dict = None,
        screenshots: list[str] = None,
        execution_time: int = 0,
        executed_by: str = None,
        executed_at: datetime = None,
        notes: str = None,
        bugs: list[dict] = None,
        tags: list[str] = None,
    ):
        self.test_id = test_id
        self.title = title
        self.category = category
        self.priority = priority
        self.description = description
        self.steps = steps
        self.expected_result = expected_result
        self.actual_result = actual_result
        self.status = status
        self.assigned_to = assigned_to
        self.environment = environment
        self.browser = browser
        self.test_data = test_data or {}
        self.screenshots = screenshots or []
        self.execution_time = execution_time
        self.executed_by = executed_by
        self.executed_at = executed_at
        self.notes = notes
        self.bugs = bugs or []
        self.tags = tags or []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "test_id": self.test_id,
            "title": self.title,
            "category": self.category.value,
            "priority": self.priority.value,
            "description": self.description,
            "steps": self.steps,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "environment": self.environment,
            "browser": self.browser,
            "test_data": self.test_data,
            "screenshots": self.screenshots,
            "execution_time": self.execution_time,
            "executed_by": self.executed_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "notes": self.notes,
            "bugs": self.bugs,
            "tags": self.tags,
        }


class QATestPlan:
    """Comprehensive QA test plan with structured test cases"""

    def __init__(self, plan_name: str, version: str, description: str):
        self.plan_name = plan_name
        self.version = version
        self.description = description
        self.created_at = datetime.utcnow()
        self.test_cases = []
        self.execution_summary = {}

    def add_test_case(self, test_execution: TestExecution):
        """Add a test case to the plan"""
        self.test_cases.append(test_execution)

    def get_test_cases_by_category(self, category: TestCategory) -> list[TestExecution]:
        """Get test cases filtered by category"""
        return [test for test in self.test_cases if test.category == category]

    def get_test_cases_by_priority(self, priority: TestPriority) -> list[TestExecution]:
        """Get test cases filtered by priority"""
        return [test for test in self.test_cases if test.priority == priority]

    def get_test_cases_by_status(self, status: TestStatus) -> list[TestExecution]:
        """Get test cases filtered by status"""
        return [test for test in self.test_cases if test.status == status]

    def calculate_execution_metrics(self) -> dict[str, Any]:
        """Calculate test execution metrics"""
        total_tests = len(self.test_cases)
        if total_tests == 0:
            return {"total_tests": 0, "pass_rate": 0}

        passed_tests = len(self.get_test_cases_by_status(TestStatus.PASSED))
        failed_tests = len(self.get_test_cases_by_status(TestStatus.FASED))
        blocked_tests = len(self.get_test_cases_by_status(TestStatus.BLOCKED))
        skipped_tests = len(self.get_test_cases_by_status(TestStatus.SKIPPED))

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "blocked": blocked_tests,
            "skipped": skipped_tests,
            "pass_rate": (passed_tests / total_tests) * 100,
            "failure_rate": (failed_tests / total_tests) * 100,
            "execution_rate": ((passed_tests + failed_tests + blocked_tests) / total_tests) * 100,
        }


class ManualQAService:
    """Manual QA testing management service"""

    def __init__(self):
        self.test_plans = {}
        self.current_sprint = "Sprint 1.2"
        self.test_environments = ["development", "staging", "production"]
        self.supported_browsers = ["chrome", "firefox", "safari", "edge"]

    def create_comprehensive_test_plan(self) -> QATestPlan:
        """Create comprehensive test plan for PsychSync platform"""

        plan = QATestPlan(
            plan_name="PsychSync Comprehensive QA Test Plan",
            version="1.2",
            description="Complete manual testing plan covering all platform features and requirements",
        )

        # Authentication & Authorization Tests
        self._add_auth_tests(plan)

        # User Management Tests
        self._add_user_management_tests(plan)

        # Assessment System Tests
        self._add_assessment_tests(plan)

        # Team Optimization Tests
        self._add_team_optimization_tests(plan)

        # Analytics & Reporting Tests
        self._add_analytics_tests(plan)

        # GDPR & Compliance Tests
        self._add_compliance_tests(plan)

        # Integration Tests
        self._add_integration_tests(plan)

        # UI/UX Tests
        self._add_ui_ux_tests(plan)

        # Performance Tests
        self._add_performance_tests(plan)

        # Security Tests
        self._add_security_tests(plan)

        # Accessibility Tests
        self._add_accessibility_tests(plan)

        # Cross-browser Tests
        self._add_browser_compatibility_tests(plan)

        # Mobile Responsiveness Tests
        self._add_mobile_tests(plan)

        self.test_plans[plan.plan_name] = plan
        return plan

    def _add_auth_tests(self, plan: QATestPlan):
        """Add authentication and authorization tests"""

        auth_tests = [
            TestExecution(
                test_id="AUTH_001",
                title="User Registration - Valid Data",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.CRITICAL,
                description="Verify users can register with valid information",
                steps=[
                    "Navigate to registration page",
                    "Enter valid email, password, and full name",
                    "Click 'Create Account'",
                    "Verify confirmation email is sent",
                    "Click verification link in email",
                    "Verify user is logged in after verification",
                ],
                expected_result="User successfully registers, receives verification email, and can log in after verification",
                tags=["authentication", "registration", "email-verification"],
            ),
            TestExecution(
                test_id="AUTH_002",
                title="User Login - Valid Credentials",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.CRITICAL,
                description="Verify users can login with correct credentials",
                steps=[
                    "Navigate to login page",
                    "Enter registered email and password",
                    "Click 'Login'",
                    "Verify user is redirected to dashboard",
                ],
                expected_result="User successfully logs in and is redirected to dashboard",
                tags=["authentication", "login", "dashboard"],
            ),
            TestExecution(
                test_id="AUTH_003",
                title="User Login - Invalid Credentials",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify login fails with incorrect credentials",
                steps=[
                    "Navigate to login page",
                    "Enter incorrect email or password",
                    "Click 'Login'",
                    "Verify error message is displayed",
                ],
                expected_result="Login fails and appropriate error message is shown",
                tags=["authentication", "login", "error-handling"],
            ),
            TestExecution(
                test_id="AUTH_004",
                title="Password Reset Flow",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify password reset functionality",
                steps=[
                    "Click 'Forgot Password' on login page",
                    "Enter registered email",
                    "Submit password reset request",
                    "Check email for reset link",
                    "Click reset link",
                    "Enter new password",
                    "Confirm new password",
                    "Verify password is updated",
                ],
                expected_result="Password reset email is sent, user can reset password successfully",
                tags=["authentication", "password-reset", "email"],
            ),
            TestExecution(
                test_id="AUTH_005",
                title="Session Management - Logout",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify session is properly terminated on logout",
                steps=[
                    "Login with valid credentials",
                    "Navigate to different pages",
                    "Click 'Logout'",
                    "Verify user is logged out",
                    "Try to access protected page",
                    "Verify user is redirected to login",
                ],
                expected_result="Session properly terminated, protected pages redirect to login",
                tags=["authentication", "logout", "session-management"],
            ),
            TestExecution(
                test_id="AUTH_006",
                title="Token Refresh - Automatic",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify JWT token refresh works automatically",
                steps=[
                    "Login and note initial JWT token",
                    "Wait for token to approach expiry",
                    "Make an API request",
                    "Verify token is refreshed automatically",
                    "Verify user remains logged in",
                ],
                expected_result="Token refreshes seamlessly without user interruption",
                tags=["authentication", "jwt", "token-refresh"],
            ),
        ]

        for test in auth_tests:
            plan.add_test_case(test)

    def _add_user_management_tests(self, plan: QATestPlan):
        """Add user management tests"""

        user_tests = [
            TestExecution(
                test_id="USER_001",
                title="Profile Update - Valid Data",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify users can update their profile information",
                steps=[
                    "Login as registered user",
                    "Navigate to profile settings",
                    "Update full name",
                    "Update timezone",
                    "Update language preference",
                    "Save changes",
                    "Verify profile is updated",
                    "Logout and login again",
                    "Verify changes persist",
                ],
                expected_result="Profile updates successfully and persists across sessions",
                tags=["user-management", "profile", "settings"],
            ),
            TestExecution(
                test_id="USER_002",
                title="Avatar Upload - Valid Image",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify users can upload profile avatar",
                steps=[
                    "Navigate to profile settings",
                    "Click 'Upload Avatar'",
                    "Select valid image file (JPG, PNG)",
                    "Click upload",
                    "Verify image preview",
                    "Save changes",
                    "Verify avatar displays in profile",
                ],
                expected_result="Avatar uploads successfully and displays correctly",
                tags=["user-management", "avatar", "file-upload"],
            ),
            TestExecution(
                test_id="USER_003",
                title="Email Change - Verification Required",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify email change requires verification",
                steps=[
                    "Navigate to profile settings",
                    "Update email address",
                    "Save changes",
                    "Verify verification email is sent to new address",
                    "Click verification link",
                    "Verify email is updated",
                ],
                expected_result="Email change requires verification before taking effect",
                tags=["user-management", "email", "verification"],
            ),
            TestExecution(
                test_id="USER_004",
                title="Account Deactivation",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify users can deactivate their account",
                steps=[
                    "Navigate to account settings",
                    "Click 'Deactivate Account'",
                    "Confirm deactivation",
                    "Verify account is deactivated",
                    "Verify login fails with deactivated account",
                ],
                expected_result="Account deactivates successfully, login is blocked",
                tags=["user-management", "account-deactivation", "security"],
            ),
        ]

        for test in user_tests:
            plan.add_test_case(test)

    def _add_assessment_tests(self, plan: QATestPlan):
        """Add assessment system tests"""

        assessment_tests = [
            TestExecution(
                test_id="ASSESS_001",
                title="Big Five Assessment - Complete Flow",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.CRITICAL,
                description="Verify complete Big Five assessment workflow",
                steps=[
                    "Navigate to assessments page",
                    "Select Big Five assessment",
                    "Start assessment",
                    "Answer all questions honestly",
                    "Complete all questions",
                    "Submit assessment",
                    "Verify results are generated",
                    "View personality profile",
                    "Verify trait scores are displayed",
                ],
                expected_result="Assessment completes successfully, results show accurate personality traits",
                tags=["assessment", "big-five", "personality"],
            ),
            TestExecution(
                test_id="ASSESS_002",
                title="MBTI Assessment - Type Assignment",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify MBTI assessment correctly assigns personality types",
                steps=[
                    "Select MBTI assessment",
                    "Answer preference-based questions",
                    "Complete assessment",
                    "Verify MBTI type is calculated",
                    "View type description",
                    "Verify type matches responses",
                ],
                expected_result="MBTI type is correctly calculated based on responses",
                tags=["assessment", "mbti", "personality-type"],
            ),
            TestExecution(
                test_id="ASSESS_003",
                title="Assessment Progress Saving",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify assessment progress can be saved and resumed",
                steps=[
                    "Start any assessment",
                    "Answer first 5 questions",
                    "Click 'Save Progress'",
                    "Logout",
                    "Login again",
                    "Navigate to assessments",
                    "Click 'Resume Assessment'",
                    "Verify progress is restored",
                    "Continue and complete assessment",
                ],
                expected_result="Progress saves correctly and can be resumed later",
                tags=["assessment", "progress-saving", "resume"],
            ),
            TestExecution(
                test_id="ASSESS_004",
                title="Assessment Results Accuracy",
                category=TestCategory.REGRESSION,
                priority=TestPriority.HIGH,
                description="Verify assessment results are accurate and consistent",
                steps=[
                    "Take same assessment multiple times",
                    "Compare results for consistency",
                    "Verify scoring algorithm works correctly",
                    "Check for calculation errors",
                    "Validate personality type assignments",
                ],
                expected_result="Results are consistent and mathematically correct",
                tags=["assessment", "accuracy", "scoring"],
            ),
            TestExecution(
                test_id="ASSESS_005",
                title="Assessment Time Limit Enforcement",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify time limits are enforced for timed assessments",
                steps=[
                    "Start timed assessment",
                    "Wait beyond time limit",
                    "Verify assessment auto-submits",
                    "Check results are based on completed questions",
                    "Verify timeout message is shown",
                ],
                expected_result="Time limits are enforced, partial results are used",
                tags=["assessment", "time-limits", "auto-submit"],
            ),
        ]

        for test in assessment_tests:
            plan.add_test_case(test)

    def _add_team_optimization_tests(self, plan: QATestPlan):
        """Add team optimization tests"""

        team_tests = [
            TestExecution(
                test_id="TEAM_001",
                title="Team Creation - Basic Flow",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.CRITICAL,
                description="Verify team creation workflow",
                steps=[
                    "Navigate to teams page",
                    "Click 'Create Team'",
                    "Enter team name",
                    "Enter team description",
                    "Select team type",
                    "Save team",
                    "Verify team appears in dashboard",
                    "Verify team member can be added",
                ],
                expected_result="Team creates successfully with correct information",
                tags=["team-optimization", "team-creation", "management"],
            ),
            TestExecution(
                test_id="TEAM_002",
                title="Team Member Addition",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify team members can be added to teams",
                steps=[
                    "Open existing team",
                    "Click 'Add Member'",
                    "Search for user by email",
                    "Select user from search results",
                    "Assign role (member/admin/owner)",
                    "Send invitation",
                    "Verify invitation email is sent",
                    "Accept invitation as invited user",
                ],
                expected_result="Team member added successfully with correct role",
                tags=["team-optimization", "team-members", "invitations"],
            ),
            TestExecution(
                test_id="TEAM_003",
                title="Team Optimization Analysis",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.CRITICAL,
                description="Verify team optimization generates recommendations",
                steps=[
                    "Select team with 3+ members",
                    "Click 'Optimize Team'",
                    "Select optimization objective",
                    "Wait for analysis to complete",
                    "Review generated recommendations",
                    "Verify compatibility scores",
                    "Check suggested team configurations",
                ],
                expected_result="Optimization analysis completes with valid recommendations",
                tags=["team-optimization", "ai-analysis", "recommendations"],
            ),
            TestExecution(
                test_id="TEAM_004",
                title="Team Compatibility Scoring",
                category=TestCategory.REGRESSION,
                priority=TestPriority.HIGH,
                description="Verify team compatibility scores are accurate",
                steps=[
                    "Create test team with known personalities",
                    "Run optimization analysis",
                    "Check compatibility scores manually",
                    "Verify algorithm calculations",
                    "Validate score ranges (0-1)",
                ],
                expected_result="Compatibility scores are mathematically accurate",
                tags=["team-optimization", "compatibility", "scoring"],
            ),
            TestExecution(
                test_id="TEAM_005",
                title="Team Performance Metrics",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify team performance metrics are calculated",
                steps=[
                    "Select optimized team",
                    "View performance dashboard",
                    "Check key metrics displayed",
                    "Verify metric calculations",
                    "Validate historical tracking",
                ],
                expected_result="Performance metrics are accurate and comprehensive",
                tags=["team-optimization", "performance", "metrics"],
            ),
        ]

        for test in team_tests:
            plan.add_test_case(test)

    def _add_analytics_tests(self, plan: QATestPlan):
        """Add analytics and reporting tests"""

        analytics_tests = [
            TestExecution(
                test_id="ANALYTICS_001",
                title="Dashboard Data Accuracy",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.HIGH,
                description="Verify dashboard displays accurate analytics data",
                steps=[
                    "Navigate to analytics dashboard",
                    "Check user count metrics",
                    "Verify assessment completion rates",
                    "Check team optimization usage",
                    "Validate performance indicators",
                    "Verify data freshness",
                ],
                expected_result="All dashboard metrics are accurate and up-to-date",
                tags=["analytics", "dashboard", "metrics"],
            ),
            TestExecution(
                test_id="ANALYTICS_002",
                title="Report Generation",
                category=TestCategory.FUNCTIONAL,
                priority=TestPriority.MEDIUM,
                description="Verify reports can be generated and exported",
                steps=[
                    "Navigate to reports section",
                    "Select report type",
                    "Set date range",
                    "Generate report",
                    "Verify report contents",
                    "Export to PDF/CSV",
                    "Check exported file format",
                ],
                expected_result="Reports generate correctly with accurate data",
                tags=["analytics", "reports", "export"],
            ),
        ]

        for test in analytics_tests:
            plan.add_test_case(test)

    def _add_compliance_tests(self, plan: QATestPlan):
        """Add GDPR and compliance tests"""

        compliance_tests = [
            TestExecution(
                test_id="COMPLIANCE_001",
                title="GDPR Data Export - Complete Flow",
                category=TestCategory.COMPLIANCE,
                priority=TestPriority.CRITICAL,
                description="Verify GDPR-compliant data export functionality",
                steps=[
                    "Navigate to privacy settings",
                    "Request data export",
                    "Select export format (JSON/CSV/ZIP)",
                    "Submit export request",
                    "Download exported data",
                    "Verify all user data is included",
                    "Check data format compliance",
                    "Verify export link expires after 7 days",
                ],
                expected_result="Data export complies with GDPR requirements",
                tags=["compliance", "gdpr", "data-export"],
            ),
            TestExecution(
                test_id="COMPLIANCE_002",
                title="Data Deletion Request",
                category=TestCategory.COMPLIANCE,
                priority=TestPriority.CRITICAL,
                description="Verify right to be forgotten request",
                steps=[
                    "Request data deletion",
                    "Confirm password",
                    "Verify 30-day grace period",
                    "Check account deactivation",
                    "Verify data deletion after grace period",
                ],
                expected_result="Data deletion process complies with GDPR Article 17",
                tags=["compliance", "gdpr", "data-deletion"],
            ),
            TestExecution(
                test_id="COMPLIANCE_003",
                title="Consent Management",
                category=TestCategory.COMPLIANCE,
                priority=TestPriority.HIGH,
                description="Verify granular consent management",
                steps=[
                    "Review current consent status",
                    "Withdraw analytics consent",
                    "Grant marketing consent",
                    "Verify consent changes are recorded",
                    "Check consent history",
                    "Verify audit trail",
                ],
                expected_result="Consent management meets GDPR requirements",
                tags=["compliance", "gdpr", "consent"],
            ),
        ]

        for test in compliance_tests:
            plan.add_test_case(test)

    def _add_ui_ux_tests(self, plan: QATestPlan):
        """Add UI/UX usability tests"""

        ui_tests = [
            TestExecution(
                test_id="UI_001",
                title="Navigation Flow - Intuitive",
                category=TestCategory.USABILITY,
                priority=TestPriority.HIGH,
                description="Verify navigation is intuitive and user-friendly",
                steps=[
                    "Test main navigation menu",
                    "Check breadcrumb navigation",
                    "Verify consistent button placement",
                    "Test responsive navigation on mobile",
                    "Check keyboard navigation support",
                ],
                expected_result="Navigation is intuitive and easy to use",
                tags=["ui", "ux", "navigation"],
            ),
            TestExecution(
                test_id="UI_002",
                title="Form Validation - User Friendly",
                category=TestCategory.USABILITY,
                priority=TestPriority.HIGH,
                description="Verify form validation is helpful and clear",
                steps=[
                    "Submit form with empty required fields",
                    "Test invalid email format validation",
                    "Check password strength indicators",
                    "Verify real-time validation feedback",
                    "Test error message clarity",
                ],
                expected_result="Form validation provides clear, helpful feedback",
                tags=["ui", "ux", "forms", "validation"],
            ),
        ]

        for test in ui_tests:
            plan.add_test_case(test)

    def _add_accessibility_tests(self, plan: QATestPlan):
        """Add accessibility compliance tests"""

        accessibility_tests = [
            TestExecution(
                test_id="A11Y_001",
                title="Keyboard Navigation - Full Site",
                category=TestCategory.ACCESSIBILITY,
                priority=TestPriority.CRITICAL,
                description="Verify entire site is keyboard navigable",
                steps=[
                    "Tab through all pages",
                    "Verify focus indicators are visible",
                    "Check all interactive elements reachable",
                    "Test skip navigation links",
                    "Verify focus trap in modals",
                ],
                expected_result="Site fully navigable via keyboard",
                tags=["accessibility", "wcag", "keyboard"],
            ),
            TestExecution(
                test_id="A11Y_002",
                title="Screen Reader Compatibility",
                category=TestCategory.ACCESSIBILITY,
                priority=TestPriority.HIGH,
                description="Verify screen reader compatibility",
                steps=[
                    "Test with screen reader enabled",
                    "Check alt text on images",
                    "Verify form labels are announced",
                    "Test ARIA landmarks",
                    "Check page structure clarity",
                ],
                expected_result="Site works well with screen readers",
                tags=["accessibility", "wcag", "screen-reader"],
            ),
            TestExecution(
                test_id="A11Y_003",
                title="Color Contrast Compliance",
                category=TestCategory.ACCESSIBILITY,
                priority=TestPriority.HIGH,
                description="Verify color contrast meets WCAG standards",
                steps=[
                    "Check text contrast ratios",
                    "Test color combinations",
                    "Verify sufficient contrast",
                    "Check with contrast checking tools",
                ],
                expected_result="All text meets WCAG AA contrast standards",
                tags=["accessibility", "wcag", "color-contrast"],
            ),
            TestExecution(
                test_id="A11Y_004",
                title="Focus Management",
                category=TestCategory.ACCESSIBILITY,
                priority=TestPriority.HIGH,
                description="Verify focus management is accessible",
                steps=[
                    "Test focus in modals and dialogs",
                    "Verify focus returns correctly",
                    "Check focus indicators are visible",
                    "Test focus trap in overlays",
                ],
                expected_result="Focus management is accessible and predictable",
                tags=["accessibility", "wcag", "focus-management"],
            ),
        ]

        for test in accessibility_tests:
            plan.add_test_case(test)

    def _add_mobile_tests(self, plan: QATestPlan):
        """Add mobile responsiveness tests"""

        mobile_tests = [
            TestExecution(
                test_id="MOBILE_001",
                title="Mobile Responsiveness - iPhone",
                category=TestCategory.COMPATIBILITY,
                priority=TestPriority.HIGH,
                description="Verify site works correctly on iPhone",
                steps=[
                    "Test on iPhone viewport",
                    "Check layout adaptation",
                    "Test touch interactions",
                    "Verify menu functionality",
                    "Check form usability",
                ],
                expected_result="Site works well on iPhone devices",
                tags=["mobile", "responsive", "ios"],
            ),
            TestExecution(
                test_id="MOBILE_002",
                title="Mobile Responsiveness - Android",
                category=TestCategory.COMPATIBILITY,
                priority=TestPriority.HIGH,
                description="Verify site works correctly on Android",
                steps=[
                    "Test on Android viewport",
                    "Check layout adaptation",
                    "Test touch interactions",
                    "Verify menu functionality",
                    "Check form usability",
                ],
                expected_result="Site works well on Android devices",
                tags=["mobile", "responsive", "android"],
            ),
        ]

        for test in mobile_tests:
            plan.add_test_case(test)

    def get_test_execution_summary(self, plan_name: str) -> dict[str, Any]:
        """Get comprehensive test execution summary"""

        plan = self.test_plans.get(plan_name)
        if not plan:
            return {"error": f"Test plan '{plan_name}' not found"}

        metrics = plan.calculate_execution_metrics()

        # Additional breakdowns
        category_breakdown = {}
        for category in TestCategory:
            category_tests = plan.get_test_cases_by_category(category)
            if category_tests:
                passed = len([t for t in category_tests if t.status == TestStatus.PASSED])
                total = len(category_tests)
                category_breakdown[category.value] = {
                    "total": total,
                    "passed": passed,
                    "pass_rate": (passed / total) * 100 if total > 0 else 0,
                }

        priority_breakdown = {}
        for priority in TestPriority:
            priority_tests = plan.get_test_cases_by_priority(priority)
            if priority_tests:
                status_counts = {}
                for test in priority_tests:
                    status_counts[test.status.value] = status_counts.get(test.status.value, 0) + 1
                priority_breakdown[priority.value] = {
                    "total": len(priority_tests),
                    "status_counts": status_counts,
                }

        return {
            "plan_name": plan.plan_name,
            "version": plan.version,
            "description": plan.description,
            "created_at": plan.created_at.isoformat(),
            "test_metrics": metrics,
            "category_breakdown": category_breakdown,
            "priority_breakdown": priority_breakdown,
            "total_test_cases": len(plan.test_cases),
        }

    def generate_test_report(self, plan_name: str, format: str = "json") -> str:
        """Generate comprehensive test report"""

        plan = self.test_plans.get(plan_name)
        if not plan:
            return "Test plan not found"

        summary = self.get_test_execution_summary(plan_name)

        report_data = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "plan_name": plan.plan_name,
                "version": plan.version,
                "generator": "PsychSync QA Service",
            },
            "test_summary": summary,
            "test_cases": [test.to_dict() for test in plan.test_cases],
        }

        if format == "json":
            return json.dumps(report_data, indent=2, default=str)
        return str(report_data)
