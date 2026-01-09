"""
Accessibility Compliance Service
Provides WCAG 2.1 compliance testing, audit tools, and accessibility monitoring
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConformanceLevel(Enum):
    """WCAG conformance levels"""

    A = "A"  # Minimum level
    AA = "AA"  # Standard level
    AAA = "AAA"  # Highest level


class SeverityLevel(Enum):
    """Accessibility issue severity levels"""

    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"
    INFO = "info"


@dataclass
class AccessibilityTest:
    """Individual accessibility test definition"""

    id: str
    name: str
    description: str
    wcag_criteria: list[str]  # e.g., ["1.1.1", "1.2.1"]
    conformance_level: ConformanceLevel
    severity: SeverityLevel
    test_type: str  # "automated", "manual", "semi-automated"
    implementation: str  # Test implementation details
    remediation: str  # How to fix issues


@dataclass
class AccessibilityIssue:
    """Accessibility issue discovered during testing"""

    test_id: str
    severity: SeverityLevel
    wcag_criteria: list[str]
    element: str  # Element with issue
    description: str
    remediation: str
    url: str | None = None
    screenshot: str | None = None
    automated: bool = True
    confidence: float = 1.0  # 0-1 confidence score


@dataclass
class AccessibilityAudit:
    """Complete accessibility audit results"""

    timestamp: datetime
    url: str
    conformance_target: ConformanceLevel
    total_tests: int
    passed_tests: int
    failed_tests: int
    issues: list[AccessibilityIssue] = field(default_factory=list)
    score: float = 0.0  # Overall accessibility score
    compliance_percentage: float = 0.0
    remediation_priority: list[str] = field(default_factory=list)


class AccessibilityAuditService:
    """Comprehensive accessibility audit service"""

    def __init__(self):
        self.tests = self._initialize_wcag_tests()
        self.color_contrast_ratios = {
            "AA_normal": 4.5,
            "AA_large": 3.0,
            "AAA_normal": 7.0,
            "AAA_large": 4.5,
        }

    def _initialize_wcag_tests(self) -> dict[str, AccessibilityTest]:
        """Initialize WCAG 2.1 test suite"""
        return {
            # Perceivable
            "text_alternatives": AccessibilityTest(
                id="text_alternatives",
                name="Text Alternatives for Non-Text Content",
                description="All non-text content must have text alternatives",
                wcag_criteria=["1.1.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.CRITICAL,
                test_type="semi-automated",
                implementation="Check for alt text, aria-labels, and descriptive text",
                remediation="Add appropriate alt attributes or ARIA labels to provide text alternatives",
            ),
            "captions_prerecorded": AccessibilityTest(
                id="captions_prerecorded",
                name="Captions for Pre-recorded Audio",
                description="Synchronized captions must be provided for pre-recorded audio content",
                wcag_criteria=["1.2.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.CRITICAL,
                test_type="manual",
                implementation="Verify presence and accuracy of captions in video content",
                remediation="Add synchronized captions using WebVTT or similar technology",
            ),
            "color_reliance": AccessibilityTest(
                id="color_reliance",
                name="Color Not Used as Only Visual Means",
                description="Color should not be used as the only visual means of conveying information",
                wcag_criteria=["1.4.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="automated",
                implementation="Check for color-only indicators and verify alternative indicators exist",
                remediation="Add non-color indicators (icons, text, patterns) alongside color coding",
            ),
            "audio_control": AccessibilityTest(
                id="audio_control",
                name="Audio Control",
                description="Audio that plays automatically must have controls to stop or adjust volume",
                wcag_criteria=["1.4.2"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="automated",
                implementation="Check for auto-playing audio elements and verify controls exist",
                remediation="Add audio controls or prevent auto-play",
            ),
            "contrast_normal": AccessibilityTest(
                id="contrast_normal",
                name="Contrast Ratio (Normal Text)",
                description="Text and images of text must have contrast ratio of at least 4.5:1",
                wcag_criteria=["1.4.3"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="automated",
                implementation="Calculate color contrast ratios for all text elements",
                remediation="Increase contrast between text and background colors",
            ),
            "contrast_large": AccessibilityTest(
                id="contrast_large",
                name="Contrast Ratio (Large Text)",
                description="Large text must have contrast ratio of at least 3:1",
                wcag_criteria=["1.4.3"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="automated",
                implementation="Identify large text (18pt+ or 14pt+ bold) and check contrast ratios",
                remediation="Increase contrast between large text and background colors",
            ),
            "reflow": AccessibilityTest(
                id="reflow",
                name="Reflow (Horizontal Scrolling)",
                description="Content must be presented without loss of information or functionality, and without requiring scrolling in two dimensions",
                wcag_criteria=["1.4.10"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="automated",
                implementation="Check for horizontal scrolling at various viewport sizes",
                remediation="Use responsive design and flexible layouts that adapt to screen size",
            ),
            "non_text_contrast": AccessibilityTest(
                id="non_text_contrast",
                name="Non-text Contrast",
                description="User interface components and graphical objects must have contrast ratio of at least 3:1",
                wcag_criteria=["1.4.11"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="automated",
                implementation="Check contrast of buttons, icons, form controls, and other UI elements",
                remediation="Increase contrast or add outlines/borders to improve visibility",
            ),
            "text_spacing": AccessibilityTest(
                id="text_spacing",
                name="Text Spacing",
                description="Text spacing must be adjustable without loss of content or functionality",
                wcag_criteria=["1.4.12"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.MODERATE,
                test_type="manual",
                implementation="Test text spacing adjustments (line height, letter spacing, word spacing)",
                remediation="Ensure layout adapts to increased text spacing",
            ),
            # Operable
            "keyboard_accessible": AccessibilityTest(
                id="keyboard_accessible",
                name="Keyboard Accessible",
                description="All functionality must be operable through keyboard interface",
                wcag_criteria=["2.1.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.CRITICAL,
                test_type="manual",
                implementation="Navigate entire interface using only keyboard",
                remediation="Ensure all interactive elements are keyboard accessible and properly focused",
            ),
            "keyboard_trap": AccessibilityTest(
                id="keyboard_trap",
                name="No Keyboard Trap",
                description="Keyboard focus must not be trapped in any part of the content",
                wcag_criteria=["2.1.2"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.CRITICAL,
                test_type="manual",
                implementation="Test for keyboard focus traps in modals, menus, and custom components",
                remediation="Implement proper focus management and escape mechanisms",
            ),
            "timeout_customizable": AccessibilityTest(
                id="timeout_customizable",
                name="Timeout Customizable",
                description="Timeouts must be adjustable, disabled, or extended with user warning",
                wcag_criteria=["2.2.1"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test session timeouts and auto-dismissing messages",
                remediation="Provide timeout controls and warnings before session expiration",
            ),
            "pause_stop_hide": AccessibilityTest(
                id="pause_stop_hide",
                name="Pause, Stop, Hide",
                description="Moving, blinking, scrolling, or auto-updating content must be controllable",
                wcag_criteria=["2.2.2"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test for auto-updating content and verify pause/stop controls",
                remediation="Add controls to pause, stop, or hide auto-updating content",
            ),
            "navigation_order": AccessibilityTest(
                id="navigation_order",
                name="Navigable (Focus Order)",
                description="Focus order must preserve meaning and operability",
                wcag_criteria=["2.4.3"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test tab order through all interactive elements",
                remediation="Ensure logical focus order using source order and tabindex management",
            ),
            "link_purpose": AccessibilityTest(
                id="link_purpose",
                name="Link Purpose (Context)",
                description="Link purpose can be determined from link text alone or from context",
                wcag_criteria=["2.4.4"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.MODERATE,
                test_type="automated",
                implementation="Analyze link text for descriptiveness and clarity",
                remediation="Use descriptive link text or add ARIA labels for context",
            ),
            "headings_labels": AccessibilityTest(
                id="headings_labels",
                name="Headings and Labels",
                description="Section headings and labels must describe topic or purpose",
                wcag_criteria=["2.4.6"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.MODERATE,
                test_type="automated",
                implementation="Check headings and form labels for descriptiveness",
                remediation="Use meaningful headings and descriptive form labels",
            ),
            "focus_visible": AccessibilityTest(
                id="focus_visible",
                name="Focus Visible",
                description="Keyboard focus indicator must be visible",
                wcag_criteria=["2.4.7"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test focus visibility on all interactive elements",
                remediation="Add visible focus styles using CSS :focus-visible",
            ),
            "location_purpose": AccessibilityTest(
                id="location_purpose",
                name="Location (Page Titles)",
                description="Page titles must describe topic or purpose",
                wcag_criteria=["2.4.2"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.MODERATE,
                test_type="automated",
                implementation="Check page titles for descriptiveness and uniqueness",
                remediation="Use unique, descriptive page titles",
            ),
            # Understandable
            "language_identified": AccessibilityTest(
                id="language_identified",
                name="Language of Page",
                description="Human language of page must be programmatically determined",
                wcag_criteria=["3.1.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.MODERATE,
                test_type="automated",
                implementation="Check for lang attribute on html element",
                remediation="Add appropriate lang attribute to html element",
            ),
            "language_parts": AccessibilityTest(
                id="language_parts",
                name="Language of Parts",
                description="Changes in language must be programmatically identified",
                wcag_criteria=["3.1.2"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.MODERATE,
                test_type="manual",
                implementation="Check for content in different languages and proper lang attributes",
                remediation="Add lang attributes to content in different languages",
            ),
            "input_purpose": AccessibilityTest(
                id="input_purpose",
                name="Input Purpose",
                description="Input fields should have predictable purpose through autocomplete",
                wcag_criteria=["1.3.5", "1.3.6"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.MODERATE,
                test_type="automated",
                implementation="Check for autocomplete attributes on form inputs",
                remediation="Add appropriate autocomplete attributes to form inputs",
            ),
            "error_identification": AccessibilityTest(
                id="error_identification",
                name="Error Identification",
                description="Errors must be identified and described to user in text",
                wcag_criteria=["3.3.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test form validation and error messages",
                remediation="Provide clear, descriptive error messages",
            ),
            "labels_instructions": AccessibilityTest(
                id="labels_instructions",
                name="Labels or Instructions",
                description="Labels or instructions must be provided when content requires user input",
                wcag_criteria=["3.3.2"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Check form fields for labels and instructions",
                remediation="Add clear labels and instructions for all form inputs",
            ),
            "error_suggestion": AccessibilityTest(
                id="error_suggestion",
                name="Error Suggestion",
                description="When input errors are detected, suggestions for correction must be provided",
                wcag_criteria=["3.3.3"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.MODERATE,
                test_type="manual",
                implementation="Test form error handling and suggestions",
                remediation="Provide helpful suggestions for input corrections",
            ),
            "error_prevention": AccessibilityTest(
                id="error_prevention",
                name="Error Prevention (Legal, Financial, Data)",
                description="Legal, financial, or data submission errors must be reversible or have confirmation",
                wcag_criteria=["3.3.4"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test critical form submissions and error prevention mechanisms",
                remediation="Add confirmation steps or ability to review/edit before submission",
            ),
            # Robust
            "markup_valid": AccessibilityTest(
                id="markup_valid",
                name="Parsing",
                description="Elements must have complete start and end tags, nested correctly",
                wcag_criteria=["4.1.1"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.CRITICAL,
                test_type="automated",
                implementation="Validate HTML markup and DOM structure",
                remediation="Fix HTML markup errors and ensure proper nesting",
            ),
            "name_role_value": AccessibilityTest(
                id="name_role_value",
                name="Name, Role, Value",
                description="Assistive technologies must be able to identify name, role, and value",
                wcag_criteria=["4.1.2"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.SERIOUS,
                test_type="semi-automated",
                implementation="Check ARIA attributes and native semantic elements",
                remediation="Ensure proper ARIA implementation and use of semantic HTML",
            ),
            # WCAG 2.1 additions
            "character_key_shortcuts": AccessibilityTest(
                id="character_key_shortcuts",
                name="Character Key Shortcuts",
                description="Character key shortcuts must be disableable or remappable",
                wcag_criteria=["2.1.4"],
                conformance_level=ConformanceLevel.A,
                severity=SeverityLevel.MODERATE,
                test_type="manual",
                implementation="Test for single-key shortcuts and provide alternatives",
                remediation="Provide multiple-key shortcuts or ability to disable single-key shortcuts",
            ),
            "motion_animation": AccessibilityTest(
                id="motion_animation",
                name="Motion Animation from Users",
                description="Motion animation must be disableable unless essential",
                wcag_criteria=["2.3.3"],
                conformance_level=ConformanceLevel.AAA,
                severity=SeverityLevel.MODERATE,
                test_type="manual",
                implementation="Test for motion animations and provide controls",
                remediation="Add prefers-reduced-motion support and animation controls",
            ),
            "orientation": AccessibilityTest(
                id="orientation",
                name="Orientation",
                description="Content must not be restricted to display orientation",
                wcag_criteria=["1.3.4"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test content in portrait and landscape orientations",
                remediation="Ensure content adapts to both orientations",
            ),
            "reauthentication": AccessibilityTest(
                id="reauthentication",
                name="Re-authentication",
                description="Re-authentication after timeout must not cause data loss",
                wcag_criteria=["2.2.5"],
                conformance_level=ConformanceLevel.AAA,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test timeout and re-authentication workflows",
                remediation="Preserve form data and state through authentication processes",
            ),
            "target_size": AccessibilityTest(
                id="target_size",
                name="Target Size",
                description="Target areas must be at least 24x24 CSS pixels",
                wcag_criteria=["2.5.5"],
                conformance_level=ConformanceLevel.AAA,
                severity=SeverityLevel.MODERATE,
                test_type="automated",
                implementation="Measure target sizes for clickable elements",
                remediation="Increase target size or ensure adequate spacing",
            ),
            "concurrent_input": AccessibilityTest(
                id="concurrent_input",
                name="Concurrent Input Mechanisms",
                description="Content must not restrict use of input modalities",
                wcag_criteria=["2.5.1"],
                conformance_level=ConformanceLevel.AA,
                severity=SeverityLevel.SERIOUS,
                test_type="manual",
                implementation="Test with various input methods (mouse, keyboard, touch, voice)",
                remediation="Ensure content works with all input methods",
            ),
        }

    async def run_accessibility_audit(
        self,
        url: str,
        conformance_target: ConformanceLevel = ConformanceLevel.AA,
        include_automated: bool = True,
        include_manual: bool = False,
    ) -> AccessibilityAudit:
        """Run comprehensive accessibility audit"""
        logger.info(
            f"Starting accessibility audit for {url} targeting {conformance_target.value} compliance"
        )

        audit = AccessibilityAudit(
            timestamp=datetime.utcnow(),
            url=url,
            conformance_target=conformance_target,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
        )

        # Filter tests based on conformance level and test type
        applicable_tests = [
            test
            for test in self.tests.values()
            if self._is_applicable_test(test, conformance_target, include_automated, include_manual)
        ]

        audit.total_tests = len(applicable_tests)

        # Run tests
        for test in applicable_tests:
            try:
                result = await self._run_individual_test(test, url)
                if result:
                    audit.issues.append(result)
                    audit.failed_tests += 1
                else:
                    audit.passed_tests += 1
            except Exception as e:
                logger.error(f"Error running accessibility test {test.id}: {e!s}")
                # Create issue for test failure
                issue = AccessibilityIssue(
                    test_id=test.id,
                    severity=SeverityLevel.CRITICAL,
                    wcag_criteria=test.wcag_criteria,
                    element="Test System",
                    description=f"Test execution failed: {e!s}",
                    remediation="Fix test execution environment or update test implementation",
                    url=url,
                    automated=True,
                    confidence=0.0,
                )
                audit.issues.append(issue)
                audit.failed_tests += 1

        # Calculate scores
        audit.compliance_percentage = (
            (audit.passed_tests / audit.total_tests) * 100 if audit.total_tests > 0 else 0
        )
        audit.score = self._calculate_accessibility_score(audit.issues, audit.total_tests)
        audit.remediation_priority = self._prioritize_remediation(audit.issues)

        logger.info(
            f"Accessibility audit completed: {audit.compliance_percentage:.1f}% compliance, {audit.failed_tests} issues found"
        )
        return audit

    def _is_applicable_test(
        self,
        test: AccessibilityTest,
        conformance_target: ConformanceLevel,
        include_automated: bool,
        include_manual: bool,
    ) -> bool:
        """Check if test is applicable for current audit configuration"""
        # Check conformance level
        if self._conformance_level_priority(
            test.conformance_level
        ) > self._conformance_level_priority(conformance_target):
            return False

        # Check test type
        if (test.test_type == "automated" and not include_automated) or (
            test.test_type == "manual" and not include_manual
        ):
            return False

        return True

    def _conformance_level_priority(self, level: ConformanceLevel) -> int:
        """Get numeric priority for conformance level (higher = stricter)"""
        priorities = {ConformanceLevel.A: 1, ConformanceLevel.AA: 2, ConformanceLevel.AAA: 3}
        return priorities.get(level, 0)

    async def _run_individual_test(
        self, test: AccessibilityTest, url: str
    ) -> AccessibilityIssue | None:
        """Run individual accessibility test"""
        if test.test_type == "automated":
            return await self._run_automated_test(test, url)
        if test.test_type == "manual":
            return None  # Manual tests require human evaluation
        if test.test_type == "semi-automated":
            return await self._run_semi_automated_test(test, url)

        return None

    async def _run_automated_test(
        self, test: AccessibilityTest, url: str
    ) -> AccessibilityIssue | None:
        """Run automated accessibility test"""
        # This would integrate with automated testing tools like axe-core, lighthouse, etc.
        # For now, returning placeholder results

        if test.id == "markup_valid":
            # Simulate HTML validation
            return None  # Assume valid markup for demo

        if test.id == "contrast_normal":
            # Simulate contrast checking
            # In real implementation, this would use color contrast calculation
            return AccessibilityIssue(
                test_id=test.id,
                severity=SeverityLevel.SERIOUS,
                wcag_criteria=test.wcag_criteria,
                element="button.primary",
                description="Contrast ratio of 3.8:1 is below required 4.5:1",
                remediation="Increase text or background color contrast",
                url=url,
                automated=True,
                confidence=0.9,
            )

        if test.id == "focus_visible":
            # Simulate focus visibility check
            return AccessibilityIssue(
                test_id=test.id,
                severity=SeverityLevel.SERIOUS,
                wcag_criteria=test.wcag_criteria,
                element="a.nav-link",
                description="Focus indicator not visible on navigation links",
                remediation="Add visible focus styles using CSS :focus-visible",
                url=url,
                automated=True,
                confidence=0.8,
            )

        # Default: pass test
        return None

    async def _run_semi_automated_test(
        self, test: AccessibilityTest, url: str
    ) -> AccessibilityIssue | None:
        """Run semi-automated accessibility test"""
        # These tests combine automated checks with human verification
        return None  # Placeholder for semi-automated tests

    def _calculate_accessibility_score(
        self, issues: list[AccessibilityIssue], total_tests: int
    ) -> float:
        """Calculate overall accessibility score (0-100)"""
        if total_tests == 0:
            return 0.0

        # Weight issues by severity
        severity_weights = {
            SeverityLevel.CRITICAL: 10.0,
            SeverityLevel.SERIOUS: 5.0,
            SeverityLevel.MODERATE: 2.0,
            SeverityLevel.MINOR: 1.0,
            SeverityLevel.INFO: 0.5,
        }

        total_penalty = sum(severity_weights[issue.severity] for issue in issues)
        max_possible_score = 100.0
        score = max(0.0, max_possible_score - total_penalty)

        return min(100.0, score)

    def _prioritize_remediation(self, issues: list[AccessibilityIssue]) -> list[str]:
        """Prioritize issues for remediation based on severity and impact"""
        severity_priority = {
            SeverityLevel.CRITICAL: 1,
            SeverityLevel.SERIOUS: 2,
            SeverityLevel.MODERATE: 3,
            SeverityLevel.MINOR: 4,
            SeverityLevel.INFO: 5,
        }

        # Sort by severity priority, then by number of affected WCAG criteria
        prioritized_issues = sorted(
            issues, key=lambda x: (severity_priority[x.severity], -len(x.wcag_criteria))
        )

        return [
            f"{issue.severity.value.upper()}: {issue.test_id} - {issue.description[:50]}..."
            for issue in prioritized_issues[:10]  # Top 10 priorities
        ]

    def generate_accessibility_report(self, audit: AccessibilityAudit) -> dict[str, Any]:
        """Generate comprehensive accessibility audit report"""
        return {
            "executive_summary": {
                "overall_score": audit.score,
                "compliance_percentage": audit.compliance_percentage,
                "conformance_target": audit.conformance_target.value,
                "total_issues": len(audit.issues),
                "critical_issues": len(
                    [i for i in audit.issues if i.severity == SeverityLevel.CRITICAL]
                ),
                "audit_date": audit.timestamp.isoformat(),
                "url_audited": audit.url,
            },
            "test_summary": {
                "total_tests": audit.total_tests,
                "passed_tests": audit.passed_tests,
                "failed_tests": audit.failed_tests,
                "automated_tests": len(
                    [t for t in self.tests.values() if t.test_type == "automated"]
                ),
                "manual_tests": len([t for t in self.tests.values() if t.test_type == "manual"]),
                "semi_automated_tests": len(
                    [t for t in self.tests.values() if t.test_type == "semi-automated"]
                ),
            },
            "issues_by_severity": self._group_issues_by_severity(audit.issues),
            "issues_by_wcag": self._group_issues_by_wcag(audit.issues),
            "top_remediation_priorities": audit.remediation_priority,
            "detailed_issues": [
                {
                    "test_id": issue.test_id,
                    "severity": issue.severity.value,
                    "wcag_criteria": issue.wcag_criteria,
                    "element": issue.element,
                    "description": issue.description,
                    "remediation": issue.remediation,
                    "url": issue.url,
                    "automated": issue.automated,
                    "confidence": issue.confidence,
                }
                for issue in audit.issues
            ],
            "recommendations": self._generate_recommendations(audit),
        }

    def _group_issues_by_severity(self, issues: list[AccessibilityIssue]) -> dict[str, int]:
        """Group issues by severity level"""
        severity_counts = {level.value: 0 for level in SeverityLevel}
        for issue in issues:
            severity_counts[issue.severity.value] += 1
        return severity_counts

    def _group_issues_by_wcag(self, issues: list[AccessibilityIssue]) -> dict[str, int]:
        """Group issues by WCAG criteria"""
        wcag_counts = {}
        for issue in issues:
            for criterion in issue.wcag_criteria:
                wcag_counts[criterion] = wcag_counts.get(criterion, 0) + 1
        return wcag_counts

    def _generate_recommendations(self, audit: AccessibilityAudit) -> list[str]:
        """Generate specific recommendations based on audit results"""
        recommendations = []

        # Check for critical issues
        critical_issues = [i for i in audit.issues if i.severity == SeverityLevel.CRITICAL]
        if critical_issues:
            recommendations.append(
                f"URGENT: Address {len(critical_issues)} critical accessibility issues immediately "
                "as they prevent users with disabilities from using the application"
            )

        # Check conformance level
        if audit.compliance_percentage < 80:
            recommendations.append(
                f"Current compliance ({audit.compliance_percentage:.1f}%) is below target. "
                f"Focus on high-impact fixes to reach {audit.conformance_target.value} conformance"
            )

        # Specific issue type recommendations
        if any("contrast" in issue.test_id for issue in audit.issues):
            recommendations.append(
                "Implement a color contrast testing process in design system to prevent future contrast issues"
            )

        if any("keyboard" in issue.test_id for issue in audit.issues):
            recommendations.append(
                "Establish keyboard accessibility testing as part of regular QA process"
            )

        if any(
            "alt" in str(issue).lower() or "aria" in str(issue).lower() for issue in audit.issues
        ):
            recommendations.append(
                "Create guidelines and training for content authors on accessible media and ARIA usage"
            )

        return recommendations

    def create_accessibility_checklist(
        self, conformance_target: ConformanceLevel = ConformanceLevel.AA
    ) -> dict[str, Any]:
        """Create accessibility testing checklist for developers and testers"""
        applicable_tests = [
            test
            for test in self.tests.values()
            if self._conformance_level_priority(test.conformance_level)
            <= self._conformance_level_priority(conformance_target)
        ]

        checklist = {
            "conformance_target": conformance_target.value,
            "created_date": datetime.utcnow().isoformat(),
            "sections": {},
        }

        # Group tests by WCAG principle
        principles = {"Perceivable": [], "Operable": [], "Understandable": [], "Robust": []}

        for test in applicable_tests:
            # Determine principle based on WCAG criteria first digit
            if test.wcag_criteria:
                first_digit = test.wcag_criteria[0].split(".")[0]
                if first_digit == "1":
                    principles["Perceivable"].append(
                        {
                            "test_id": test.id,
                            "description": test.description,
                            "wcag_criteria": test.wcag_criteria,
                            "test_type": test.test_type,
                            "how_to_test": test.implementation,
                            "pass_criteria": f"{test.wcag_criteria[0]} - {test.description}",
                        }
                    )
                elif first_digit == "2":
                    principles["Operable"].append(
                        {
                            "test_id": test.id,
                            "description": test.description,
                            "wcag_criteria": test.wcag_criteria,
                            "test_type": test.test_type,
                            "how_to_test": test.implementation,
                            "pass_criteria": f"{test.wcag_criteria[0]} - {test.description}",
                        }
                    )
                elif first_digit == "3":
                    principles["Understandable"].append(
                        {
                            "test_id": test.id,
                            "description": test.description,
                            "wcag_criteria": test.wcag_criteria,
                            "test_type": test.test_type,
                            "how_to_test": test.implementation,
                            "pass_criteria": f"{test.wcag_criteria[0]} - {test.description}",
                        }
                    )
                elif first_digit == "4":
                    principles["Robust"].append(
                        {
                            "test_id": test.id,
                            "description": test.description,
                            "wcag_criteria": test.wcag_criteria,
                            "test_type": test.test_type,
                            "how_to_test": test.implementation,
                            "pass_criteria": f"{test.wcag_criteria[0]} - {test.description}",
                        }
                    )

        checklist["sections"] = principles

        # Add testing tools and resources
        checklist["testing_tools"] = {
            "automated": [
                "axe-core browser extension",
                "Google Lighthouse",
                "WAVE Web Accessibility Evaluation Tool",
                "Color Contrast Analyzer",
                "Screen reader simulators",
            ],
            "manual": [
                "Keyboard-only navigation testing",
                "Screen reader testing (NVDA, JAWS, VoiceOver)",
                "Zoom testing (200% and 400%)",
                "Voice recognition software testing",
                "Mobile accessibility testing",
            ],
            "user_testing": [
                "Testing with assistive technology users",
                "Testing with users with disabilities",
                "Usability testing with accessibility focus",
            ],
        }

        # Add common accessibility patterns
        checklist["best_practices"] = {
            "semantic_html": "Use semantic HTML elements (header, nav, main, section, article, footer)",
            "aria_usage": "Use ARIA only when necessary, prefer native HTML semantics",
            "keyboard_navigation": "Ensure all interactive elements are keyboard accessible",
            "focus_management": "Manage focus properly in dynamic content and modals",
            "color_contrast": "Test color contrast ratios for all text and UI elements",
            "responsive_design": "Test content reflow at different viewport sizes",
            "form_labels": "Associate labels with form inputs and provide clear instructions",
            "error_handling": "Provide clear error messages and suggestions for correction",
        }

        return checklist


# Initialize the accessibility audit service
accessibility_service = AccessibilityAuditService()
