#!/usr/bin/env python3
"""
Comprehensive Bug Reproduction and Analysis Tools
===============================================

Tools for generating minimal reproduction steps, analyzing root causes,
processing stack traces, formatting bug reports, and assessing severity/priority.

Author: Claude Code Assistant
Date: December 13, 2025
Version: 1.0
"""

import datetime
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class SeverityLevel(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    COSMETIC = "Cosmetic"


class PriorityLevel(Enum):
    IMMEDIATE = "Immediate"
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class BugCategory(Enum):
    UI_CRASH = "UI Crash"
    FUNCTIONAL = "Functional"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
    COMPATIBILITY = "Compatibility"
    USABILITY = "Usability"
    DATA_CORRUPTION = "Data Corruption"
    INTEGRATION = "Integration"
    CONFIGURATION = "Configuration"
    UNKNOWN = "Unknown"


@dataclass
class ReproductionStep:
    """Individual step in bug reproduction"""

    step_number: int
    action: str
    expected_result: str
    actual_result: str
    additional_notes: str = ""
    screenshot_needed: bool = False
    test_data: Dict[str, Any] = None


@dataclass
class RootCause:
    """Potential root cause of a bug"""

    cause_id: str
    category: str
    likelihood: str  # HIGH, MEDIUM, LOW
    description: str
    evidence: List[str]
    suggested_fix: str
    components_involved: List[str]


@dataclass
class StackTraceAnalysis:
    """Analysis of a stack trace"""

    thread_name: str
    exception_type: str
    exception_message: str
    failure_points: List[Dict[str, Any]]
    potential_causes: List[str]
    debugging_suggestions: List[str]
    affected_modules: List[str]


@dataclass
class BugReport:
    """Professional bug report"""

    report_id: str
    title: str
    severity: SeverityLevel
    priority: PriorityLevel
    category: BugCategory
    description: str
    reproduction_steps: List[ReproductionStep]
    environment: Dict[str, str]
    expected_behavior: str
    actual_behavior: str
    attachments: List[str]
    reporter: str
    assignee: Optional[str]
    created_date: str
    affected_versions: List[str]


class BugReproductionTool:
    """Comprehensive bug reproduction and analysis tool"""

    def __init__(self):
        self.bug_patterns = {
            "ui_crash": [
                r"Application crashed",
                r"Window closed unexpectedly",
                r"Interface became unresponsive",
                r"Screen frozen",
                r"Button not working",
                r"Page not loading",
            ],
            "performance": [
                r"slow",
                r"lag",
                r"timeout",
                r"loading.*time",
                r"performance.*issue",
                r"memory.*leak",
            ],
            "functional": [
                r"not working",
                r"incorrect.*behavior",
                r"wrong.*result",
                r"feature.*broken",
                r"functionality.*missing",
            ],
            "data_corruption": [
                r"data.*lost",
                r"corruption",
                r"incorrect.*data",
                r"missing.*data",
                r"invalid.*format",
            ],
        }

    def generate_minimal_reproduction_steps(
        self, bug_report: str
    ) -> List[ReproductionStep]:
        """Generate minimal reproduction steps from bug report"""

        # Extract key information from bug report
        actions = self._extract_actions(bug_report)
        expected = self._extract_expected_behavior(bug_report)
        actual = self._extract_actual_behavior(bug_report)

        # Generate reproduction steps
        steps = []

        # Common preliminary steps
        steps.append(
            ReproductionStep(
                step_number=1,
                action="Launch the application and log in with valid credentials",
                expected_result="Application launches successfully and user is logged in",
                actual_result="Application launches and user authentication works",
            )
        )

        # Add context-specific steps
        if any(word in bug_report.lower() for word in ["login", "auth", "signin"]):
            steps.extend(self._generate_login_steps(bug_report))
        elif any(word in bug_report.lower() for word in ["form", "input", "submit"]):
            steps.extend(self._generate_form_steps(bug_report))
        elif any(
            word in bug_report.lower() for word in ["report", "dashboard", "analytics"]
        ):
            steps.extend(self._generate_report_steps(bug_report))
        else:
            steps.extend(self._generate_general_steps(bug_report))

        # Add the specific failure step
        failure_step = ReproductionStep(
            step_number=len(steps) + 1,
            action=self._extract_primary_action(bug_report),
            expected_result=self._extract_expected_from_bug(bug_report),
            actual_result=self._extract_actual_from_bug(bug_report),
            screenshot_needed=True,
        )
        steps.append(failure_step)

        return steps

    def suggest_root_causes(
        self, bug_description: str, context: Dict[str, Any] = None
    ) -> List[RootCause]:
        """Suggest likely root causes of a bug"""

        causes = []

        # Analyze bug patterns
        bug_lower = bug_description.lower()

        # UI/Interface issues
        if any(
            pattern in bug_lower
            for pattern in ["crash", "freeze", "unresponsive", "ui", "interface"]
        ):
            causes.append(
                RootCause(
                    cause_id="UI-001",
                    category="User Interface",
                    likelihood="HIGH",
                    description="UI component failure due to state management issues",
                    evidence=["UI crash described", "Interface unresponsiveness"],
                    suggested_fix="Review component state management and error boundaries",
                    components_involved=[
                        "React Components",
                        "State Management",
                        "Event Handlers",
                    ],
                )
            )

        # Data issues
        if any(
            pattern in bug_lower for pattern in ["data", "null", "undefined", "missing"]
        ):
            causes.append(
                RootCause(
                    cause_id="DATA-001",
                    category="Data Handling",
                    likelihood="HIGH",
                    description="Null/undefined data causing application failure",
                    evidence=[
                        "Data-related error mentioned",
                        "Null reference patterns",
                    ],
                    suggested_fix="Add proper data validation and null checks",
                    components_involved=[
                        "Data Layer",
                        "API Integration",
                        "State Management",
                    ],
                )
            )

        # Performance issues
        if any(
            pattern in bug_lower
            for pattern in ["slow", "performance", "timeout", "lag"]
        ):
            causes.append(
                RootCause(
                    cause_id="PERF-001",
                    category="Performance",
                    likelihood="MEDIUM",
                    description="Performance bottleneck in data processing or rendering",
                    evidence=["Performance degradation described"],
                    suggested_fix="Optimize database queries and implement lazy loading",
                    components_involved=["Database", "API", "Frontend Rendering"],
                )
            )

        # Integration issues
        if any(
            pattern in bug_lower
            for pattern in ["api", "integration", "connection", "server"]
        ):
            causes.append(
                RootCause(
                    cause_id="INT-001",
                    category="Integration",
                    likelihood="HIGH",
                    description="API integration failure or network connectivity issues",
                    evidence=[
                        "API or integration mentioned",
                        "Server-related problems",
                    ],
                    suggested_fix="Verify API endpoints and implement retry logic",
                    components_involved=["API Layer", "Network", "Error Handling"],
                )
            )

        # Authentication issues
        if any(
            pattern in bug_lower
            for pattern in ["login", "auth", "permission", "access"]
        ):
            causes.append(
                RootCause(
                    cause_id="AUTH-001",
                    category="Authentication",
                    likelihood="HIGH",
                    description="Authentication or authorization system failure",
                    evidence=["Auth-related error described"],
                    suggested_fix="Review JWT token handling and permission checks",
                    components_involved=[
                        "Auth Service",
                        "JWT Validation",
                        "Role Management",
                    ],
                )
            )

        # Add a general cause if no specific patterns found
        if not causes:
            causes.append(
                RootCause(
                    cause_id="GEN-001",
                    category="General",
                    likelihood="MEDIUM",
                    description="General application error requiring investigation",
                    evidence=["General error description"],
                    suggested_fix="Review application logs and implement additional logging",
                    components_involved=[
                        "Application Core",
                        "Logging",
                        "Error Handling",
                    ],
                )
            )

        return causes

    def analyze_stack_trace(self, stack_trace: str) -> StackTraceAnalysis:
        """Analyze a stack trace and identify failure points"""

        # Extract thread information
        thread_match = re.search(r'(?:Thread|at)\s+"([^"]+)"', stack_trace)
        thread_name = thread_match.group(1) if thread_match else "Main Thread"

        # Extract exception information
        exception_match = re.search(r"(\w+(?:Exception|Error)):\s*(.+)", stack_trace)
        if exception_match:
            exception_type = exception_match.group(1)
            exception_message = exception_match.group(2)
        else:
            exception_type = "Unknown"
            exception_message = "No clear exception message"

        # Analyze stack frames
        stack_frames = re.findall(r"\s+at\s+([^\(]+)\(([^:]+):(\d+)\)", stack_trace)

        failure_points = []
        affected_modules = set()

        for i, (method, file, line) in enumerate(
            stack_frames[:10]
        ):  # Analyze top 10 frames
            failure_points.append(
                {
                    "frame_number": i + 1,
                    "method": method.strip(),
                    "file": file.strip(),
                    "line_number": int(line),
                    "likely_cause": self._analyze_frame_cause(method, file),
                    "confidence": "HIGH" if i < 3 else "MEDIUM" if i < 6 else "LOW",
                }
            )

            # Extract module/class from method
            module_parts = method.split(".")
            if len(module_parts) > 1:
                affected_modules.add(module_parts[0])

        # Generate potential causes
        potential_causes = []
        if "NullPointerException" in exception_type or "NoneType" in exception_type:
            potential_causes.append("Null reference or missing object initialization")
        if "IndexError" in exception_type or "ArrayIndexOutOfBounds" in exception_type:
            potential_causes.append("Array or list index out of bounds")
        if "KeyError" in exception_type or "KeyNotFound" in exception_type:
            potential_causes.append("Dictionary or map key not found")
        if "TimeoutError" in exception_type or "TimeoutException" in exception_type:
            potential_causes.append(
                "Operation timeout - possible performance or network issue"
            )
        if "MemoryError" in exception_type or "OutOfMemoryError" in exception_type:
            potential_causes.append("Memory exhaustion - possible memory leak")

        # Generate debugging suggestions
        debugging_suggestions = [
            "Review error logs for additional context",
            "Check input data validation at the failure point",
            "Verify environment configuration",
            "Add debug logging around the failing method",
            "Test with different data sets or conditions",
        ]

        return StackTraceAnalysis(
            thread_name=thread_name,
            exception_type=exception_type,
            exception_message=exception_message,
            failure_points=failure_points,
            potential_causes=potential_causes,
            debugging_suggestions=debugging_suggestions,
            affected_modules=list(affected_modules),
        )

    def rewrite_bug_report_professionally(
        self, raw_bug_report: str, additional_context: Dict[str, Any] = None
    ) -> BugReport:
        """Rewrite a bug report in professional format"""

        # Extract key information
        title = self._generate_professional_title(raw_bug_report)
        category = self._categorize_bug(raw_bug_report)

        # Generate professional description
        description = self._generate_professional_description(raw_bug_report)

        # Generate reproduction steps
        repro_steps = self.generate_minimal_reproduction_steps(raw_bug_report)

        # Extract environment information
        context = additional_context or {}
        environment = context.get(
            "environment",
            {
                "browser": "Chrome/Firefox/Safari",
                "os": "Windows/macOS/Linux",
                "version": "Latest",
                "device": "Desktop/Mobile",
            },
        )

        # Determine severity and priority
        severity = self._assess_severity(raw_bug_report)
        priority = self._assess_priority(raw_bug_report, severity)

        return BugReport(
            report_id=f"BUG-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
            title=title,
            severity=severity,
            priority=priority,
            category=category,
            description=description,
            reproduction_steps=repro_steps,
            environment=environment,
            expected_behavior=self._extract_expected_from_bug(raw_bug_report),
            actual_behavior=self._extract_actual_from_bug(raw_bug_report),
            attachments=["screenshot.png", "logs.txt"],
            reporter=context.get("reporter", "QA Team"),
            assignee=None,
            created_date=datetime.datetime.now().isoformat(),
            affected_versions=["v1.0.0", "v1.0.1"],
        )

    def generate_severity_priority_rating(
        self, bug_description: str, affected_users: int = 1, frequency: str = "once"
    ) -> Tuple[SeverityLevel, PriorityLevel]:
        """Generate severity and priority rating for a defect"""

        # Severity assessment (impact on system)
        severity_keywords = {
            SeverityLevel.CRITICAL: [
                "crash",
                "security",
                "data loss",
                "corruption",
                "system down",
                "unrecoverable",
                "production down",
                "security breach",
            ],
            SeverityLevel.HIGH: [
                "major functionality",
                "blocked",
                "cannot use",
                "significant impact",
                "workaround impossible",
                "core feature broken",
            ],
            SeverityLevel.MEDIUM: [
                "minor functionality",
                "workaround available",
                "inconvenience",
                "incorrect behavior",
                "performance issue",
            ],
            SeverityLevel.LOW: [
                "cosmetic",
                "minor issue",
                "spelling",
                "ui improvement",
                "rare occurrence",
                "edge case",
            ],
        }

        bug_lower = bug_description.lower()
        severity = SeverityLevel.MEDIUM  # Default

        for level, keywords in severity_keywords.items():
            if any(keyword in bug_lower for keyword in keywords):
                severity = level
                break

        # Adjust severity based on affected users and frequency
        if affected_users > 100:
            if severity != SeverityLevel.CRITICAL:
                severity = SeverityLevel.HIGH
        elif frequency.lower() in ["always", "frequently", "often"]:
            if severity == SeverityLevel.LOW:
                severity = SeverityLevel.MEDIUM

        # Priority assessment (urgency to fix)
        priority = PriorityLevel.MEDIUM  # Default

        if severity == SeverityLevel.CRITICAL:
            priority = PriorityLevel.IMMEDIATE
        elif severity == SeverityLevel.HIGH:
            priority = PriorityLevel.URGENT
        elif severity == SeverityLevel.MEDIUM:
            priority = (
                PriorityLevel.HIGH
                if frequency.lower() in ["frequently", "often"]
                else PriorityLevel.MEDIUM
            )
        else:
            priority = PriorityLevel.LOW

        return severity, priority

    # Helper methods
    def _extract_actions(self, text: str) -> List[str]:
        """Extract actions from bug description"""
        action_patterns = [
            r"I (?:tried to|attempted to|went to) ([^.]+)",
            r"When I ([^.]+)",
            r"After ([^.]+)",
            r"By ([^.]+)",
        ]

        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            actions.extend(matches)

        return actions

    def _extract_expected_behavior(self, text: str) -> str:
        """Extract expected behavior from bug description"""
        expected_patterns = [
            r"(?:expected|should|supposed to) ([^.]+)",
            r"would ([^.]+)",
            r"should have ([^.]+)",
        ]

        for pattern in expected_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Expected successful operation completion"

    def _extract_actual_behavior(self, text: str) -> str:
        """Extract actual behavior from bug description"""
        actual_patterns = [
            r"(?:instead|but|however) ([^.]+)",
            r"(?:got|received|found) ([^.]+)",
            r"(?:error|crash|fail)[^.]*([^.]+)",
        ]

        for pattern in actual_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Application failed or crashed"

    def _generate_login_steps(self, bug_report: str) -> List[ReproductionStep]:
        """Generate login-related reproduction steps"""
        return [
            ReproductionStep(
                step_number=2,
                action="Navigate to the login page",
                expected_result="Login page loads with username and password fields",
                actual_result="Login page displays correctly",
            ),
            ReproductionStep(
                step_number=3,
                action="Enter valid username and password credentials",
                expected_result="Credentials are accepted and validated",
                actual_result="Authentication process initiated",
            ),
        ]

    def _generate_form_steps(self, bug_report: str) -> List[ReproductionStep]:
        """Generate form-related reproduction steps"""
        return [
            ReproductionStep(
                step_number=2,
                action="Navigate to the form page",
                expected_result="Form loads with all required fields",
                actual_result="Form displays correctly",
            ),
            ReproductionStep(
                step_number=3,
                action="Fill in form fields with valid test data",
                expected_result="All fields accept input and validate correctly",
                actual_result="Data entered into form fields",
            ),
        ]

    def _generate_report_steps(self, bug_report: str) -> List[ReproductionStep]:
        """Generate report-related reproduction steps"""
        return [
            ReproductionStep(
                step_number=2,
                action="Navigate to the reports/analytics section",
                expected_result="Reports page loads with available report options",
                actual_result="Reports page displays",
            ),
            ReproductionStep(
                step_number=3,
                action="Select or configure report parameters",
                expected_result="Report parameters are set and applied",
                actual_result="Report configuration completed",
            ),
        ]

    def _generate_general_steps(self, bug_report: str) -> List[ReproductionStep]:
        """Generate general reproduction steps"""
        return [
            ReproductionStep(
                step_number=2,
                action="Navigate to the feature/section where issue occurs",
                expected_result="Page or feature loads successfully",
                actual_result="Navigation completed successfully",
            )
        ]

    def _extract_primary_action(self, bug_report: str) -> str:
        """Extract the primary action that triggers the bug"""
        actions = self._extract_actions(bug_report)
        if actions:
            return actions[0].strip()

        # Look for other patterns
        if "when i" in bug_report.lower():
            match = re.search(r"when i ([^.]+)", bug_report, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Perform the action that triggers the bug"

    def _extract_expected_from_bug(self, bug_report: str) -> str:
        """Extract expected result from bug report"""
        return self._extract_expected_behavior(bug_report)

    def _extract_actual_from_bug(self, bug_report: str) -> str:
        """Extract actual result from bug report"""
        return self._extract_actual_behavior(bug_report)

    def _analyze_frame_cause(self, method: str, file: str) -> str:
        """Analyze likely cause from stack frame"""
        if "Controller" in method or "controller" in file.lower():
            return "Business logic error in controller layer"
        elif "Service" in method or "service" in file.lower():
            return "Service layer failure"
        elif "Repository" in method or "repository" in file.lower():
            return "Data access layer issue"
        elif "Component" in method or "component" in file.lower():
            return "React component error"
        else:
            return "General application error"

    def _generate_professional_title(self, bug_report: str) -> str:
        """Generate professional bug title"""
        bug_lower = bug_report.lower()

        if "crash" in bug_lower:
            return "Application crashes when performing specific action"
        elif "login" in bug_lower:
            return "Login authentication failure"
        elif "slow" in bug_lower or "performance" in bug_lower:
            return "Performance degradation in specific feature"
        elif "error" in bug_lower:
            return "Error occurs during operation"
        else:
            return "Issue with application functionality"

    def _categorize_bug(self, bug_report: str) -> BugCategory:
        """Categorize the bug type"""
        bug_lower = bug_report.lower()

        if "crash" in bug_lower or "freeze" in bug_lower:
            return BugCategory.UI_CRASH
        elif "slow" in bug_lower or "performance" in bug_lower:
            return BugCategory.PERFORMANCE
        elif "security" in bug_lower or "auth" in bug_lower:
            return BugCategory.SECURITY
        elif "data" in bug_lower and ("lost" in bug_lower or "corrupt" in bug_lower):
            return BugCategory.DATA_CORRUPTION
        elif "integration" in bug_lower or "api" in bug_lower:
            return BugCategory.INTEGRATION
        else:
            return BugCategory.FUNCTIONAL

    def _generate_professional_description(self, bug_report: str) -> str:
        """Generate professional bug description"""
        return f"""
This report documents an issue encountered during normal application usage.
The problem manifests when users attempt to perform standard operations within the system.

Original report: "{bug_report}"

This issue affects user experience and may impact system reliability.
A thorough investigation is required to identify the root cause and implement an appropriate fix.
        """.strip()

    def _assess_severity(self, bug_report: str) -> SeverityLevel:
        """Assess bug severity"""
        severity, _ = self.generate_severity_priority_rating(bug_report)
        return severity

    def _assess_priority(
        self, bug_report: str, severity: SeverityLevel
    ) -> PriorityLevel:
        """Assess bug priority"""
        _, priority = self.generate_severity_priority_rating(bug_report)
        return priority


def main():
    """Demonstrate bug reproduction tools"""

    tool = BugReproductionTool()

    # Example bug report
    example_bug = """
    When I try to login to the application with my valid credentials,
    the page crashes and shows a white screen. I expected to be logged in
    and see the dashboard, but instead the application becomes unresponsive
    and I have to refresh the page. This happens every time I try to login.
    """

    print("🐛 BUG REPRODUCTION TOOLS DEMONSTRATION")
    print("=" * 80)
    print()

    print("📋 ORIGINAL BUG REPORT:")
    print(example_bug)
    print()

    # Generate reproduction steps
    print("🔧 MINIMAL REPRODUCTION STEPS:")
    print("-" * 60)
    repro_steps = tool.generate_minimal_reproduction_steps(example_bug)
    for step in repro_steps:
        print(f"Step {step.step_number}: {step.action}")
        print(f"  Expected: {step.expected_result}")
        print(f"  Actual: {step.actual_result}")
        print()

    # Suggest root causes
    print("🔍 LIKELY ROOT CAUSES:")
    print("-" * 60)
    root_causes = tool.suggest_root_causes(example_bug)
    for cause in root_causes:
        print(f"📌 {cause.category} (Likelihood: {cause.likelihood})")
        print(f"   Description: {cause.description}")
        print(f"   Suggested Fix: {cause.suggested_fix}")
        print(f"   Components: {', '.join(cause.components_involved)}")
        print()

    # Generate severity and priority
    print("📊 SEVERITY & PRIORITY ASSESSMENT:")
    print("-" * 60)
    severity, priority = tool.generate_severity_priority_rating(
        example_bug, affected_users=50, frequency="always"
    )
    print(f"Severity: {severity.value}")
    print(f"Priority: {priority.value}")
    print()

    # Rewrite bug report professionally
    print("📝 PROFESSIONAL BUG REPORT:")
    print("-" * 60)
    professional_report = tool.rewrite_bug_report_professionally(example_bug)
    print(f"Title: {professional_report.title}")
    print(f"Category: {professional_report.category.value}")
    print(f"Severity: {professional_report.severity.value}")
    print(f"Priority: {professional_report.priority.value}")
    print(f"Description: {professional_report.description}")
    print()

    # Example stack trace analysis
    example_stack_trace = """
    Thread "main" Exception in thread "main" java.lang.NullPointerException:
    Cannot invoke "String.length()" because "str" is null
        at com.example.StringUtils.validateString(StringUtils.java:25)
        at com.example.UserService.processUser(UserService.java:42)
        at com.example.MainController.login(MainController.java:18)
        at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    """

    print("📚 STACK TRACE ANALYSIS:")
    print("-" * 60)
    stack_analysis = tool.analyze_stack_trace(example_stack_trace)
    print(f"Exception: {stack_analysis.exception_type}")
    print(f"Message: {stack_analysis.exception_message}")
    print(f"Thread: {stack_analysis.thread_name}")
    print()
    print("Failure Points:")
    for point in stack_analysis.failure_points[:3]:
        print(
            f"  Frame {point['frame_number']}: {point['method']} ({point['file']}:{point['line_number']})"
        )
        print(f"    Likely Cause: {point['likely_cause']}")
    print()

    print("🎯 ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()
