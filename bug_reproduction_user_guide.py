#!/usr/bin/env python3
"""
Bug Reproduction Tools - Interactive User Guide
=============================================

Interactive guide and demonstration of all bug reproduction prompts and tools.

Author: Claude Code Assistant
Date: December 13, 2025
Version: 1.0
"""

import json
import datetime
from typing import Dict, List, Any
from bug_reproduction_tools import BugReproductionTool

class BugReproductionUserGuide:
    """Interactive user guide for bug reproduction tools"""

    def __init__(self):
        self.tool = BugReproductionTool()
        self.example_bugs = {
            "ui_crash": """
The application crashes when I click on the "Generate Report" button in the analytics dashboard.
I expected to see a loading spinner and then the report, but instead the entire browser tab
crashes and shows a "Aw, Snap!" error page. This happens every time I click the button
and I lose all my work in the application.
            """,

            "performance_issue": """
The team dashboard takes forever to load, sometimes up to 30 seconds.
When I navigate to the dashboard, I can see the loading icon spinning for a long time
before the data finally appears. This is making it difficult to use the application
efficiently. Other pages seem to load normally.
            """,

            "functional_error": """
When I try to create a new assessment, the form won't submit.
I fill out all the required fields - title, description, questions, and scoring
criteria - but when I click the "Save Assessment" button, nothing happens.
The button highlights but the form doesn't save and no error message appears.
            """,

            "data_corruption": """
Some of my assessment data is missing or showing incorrect values.
When I view previously created assessments, some of the questions are showing up
as blank fields, and the scores are displaying as "null" instead of the actual numbers.
This worked fine last week but now the data seems corrupted.
            """,

            "authentication_issue": """
Users are getting logged out randomly during their sessions.
Several team members have reported that they're working in the application
and suddenly get redirected to the login page without any warning.
They have to log back in and lose any unsaved work.
            """
        }

    def demonstrate_minimal_reproduction_steps(self):
        """Demonstrate minimal reproduction steps generation"""

        print("🔧 MINIMAL REPRODUCTION STEPS GENERATION")
        print("=" * 80)
        print("This feature converts user bug reports into step-by-step reproduction guides.")
        print()

        for bug_name, bug_text in self.example_bugs.items():
            print(f"🐛 Example: {bug_name.replace('_', ' ').title()}")
            print("-" * 60)
            print("Original Report:")
            print(bug_text.strip())
            print()

            steps = self.tool.generate_minimal_reproduction_steps(bug_text)
            print("Generated Reproduction Steps:")
            for step in steps:
                print(f"  {step.step_number}. {step.action}")
                print(f"     Expected: {step.expected_result}")
                print(f"     Actual: {step.actual_result}")
                if step.screenshot_needed:
                    print(f"     📸 Screenshot Required: Yes")
                print()

            print("✅ Reproduction steps generated successfully!")
            print("=" * 80)
            print()

    def demonstrate_root_cause_analysis(self):
        """Demonstrate root cause analysis"""

        print("🔍 ROOT CAUSE ANALYSIS")
        print("=" * 80)
        print("This feature analyzes bug descriptions to identify likely root causes.")
        print()

        for bug_name, bug_text in self.example_bugs.items():
            print(f"🔍 Analyzing: {bug_name.replace('_', ' ').title()}")
            print("-" * 60)

            root_causes = self.tool.suggest_root_causes(bug_text)
            print("Likely Root Causes:")
            for i, cause in enumerate(root_causes, 1):
                print(f"  {i}. {cause.category} (Likelihood: {cause.likelihood})")
                print(f"     Description: {cause.description}")
                print(f"     Suggested Fix: {cause.suggested_fix}")
                print(f"     Components: {', '.join(cause.components_involved)}")
                print()

            print("✅ Root cause analysis completed!")
            print("=" * 80)
            print()

    def demonstrate_stack_trace_analysis(self):
        """Demonstrate stack trace analysis"""

        print("📚 STACK TRACE ANALYSIS")
        print("=" * 80)
        print("This feature analyzes stack traces to identify failure points and debugging suggestions.")
        print()

        stack_traces = {
            "null_pointer": """
Exception in thread "main" java.lang.NullPointerException:
Cannot invoke "String.length()" because "str" is null
    at com.example.StringUtils.validateString(StringUtils.java:25)
    at com.example.UserService.processUser(UserService.java:42)
    at com.example.MainController.login(MainController.java:18)
    at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
            """,

            "index_error": """
Traceback (most recent call last):
  File "app.py", line 156, in generate_report
    user_data = dataset[requested_index]
IndexError: list index out of range
    File "views.py", line 89, in dashboard_view
    report = generate_report(user_id)
    File "routes.py", line 45, in dashboard
    return dashboard_view()
            """,

            "timeout": """
TimeoutError: [Errno 110] Connection timed out
  File "api_client.py", line 78, in fetch_data
    response = requests.get(url, timeout=30)
  File "data_service.py", line 123, in load_user_assessments
    assessments = fetch_data(api_endpoint)
  File "dashboard.py", line 234, in get_dashboard_data
    data = load_user_assessments(user_id)
            """
        }

        for trace_name, trace_text in stack_traces.items():
            print(f"📚 Analyzing Stack Trace: {trace_name.replace('_', ' ').title()}")
            print("-" * 60)
            print("Stack Trace:")
            print(trace_text.strip())
            print()

            analysis = self.tool.analyze_stack_trace(trace_text)
            print("Analysis Results:")
            print(f"  Exception Type: {analysis.exception_type}")
            print(f"  Exception Message: {analysis.exception_message}")
            print(f"  Thread: {analysis.thread_name}")
            print()

            print("Top Failure Points:")
            for point in analysis.failure_points[:3]:
                print(f"    {point['method']} ({point['file']}:{point['line_number']})")
                print(f"    Likely Cause: {point['likely_cause']}")
                print(f"    Confidence: {point['confidence']}")
                print()

            print("Potential Causes:")
            for cause in analysis.potential_causes:
                print(f"    • {cause}")
            print()

            print("Debugging Suggestions:")
            for suggestion in analysis.debugging_suggestions:
                print(f"    • {suggestion}")
            print()

            print("✅ Stack trace analysis completed!")
            print("=" * 80)
            print()

    def demonstrate_professional_bug_report(self):
        """Demonstrate professional bug report generation"""

        print("📝 PROFESSIONAL BUG REPORT WRITER")
        print("=" * 80)
        print("This feature converts raw bug reports into professional, actionable bug reports.")
        print()

        for bug_name, bug_text in list(self.example_bugs.items())[:2]:  # Show first 2 examples
            print(f"📝 Processing: {bug_name.replace('_', ' ').title()}")
            print("-" * 60)
            print("Original Report:")
            print(bug_text.strip())
            print()

            professional_report = self.tool.rewrite_bug_report_professionally(
                bug_text,
                {
                    "reporter": "QA Team",
                    "environment": {
                        "browser": "Chrome 119.0",
                        "os": "Windows 11",
                        "version": "v2.1.0",
                        "device": "Desktop"
                    }
                }
            )

            print("Professional Bug Report:")
            print(f"  📋 Report ID: {professional_report.report_id}")
            print(f"  📝 Title: {professional_report.title}")
            print(f"  🏷️  Category: {professional_report.category.value}")
            print(f"  🚨 Severity: {professional_report.severity.value}")
            print(f"  ⏱️  Priority: {professional_report.priority.value}")
            print(f"  👤 Reporter: {professional_report.reporter}")
            print(f"  📅 Created: {professional_report.created_date}")
            print()

            print("  📄 Description:")
            print("  " + professional_report.description.replace('\n', '\n  '))
            print()

            print("  🔄 Reproduction Steps:")
            for step in professional_report.reproduction_steps:
                print(f"    {step.step_number}. {step.action}")
            print()

            print("  ✅ Expected Behavior:")
            print(f"    {professional_report.expected_behavior}")
            print()

            print("  ❌ Actual Behavior:")
            print(f"    {professional_report.actual_behavior}")
            print()

            print("  🖥️  Environment:")
            for key, value in professional_report.environment.items():
                print(f"    {key.title()}: {value}")
            print()

            print("✅ Professional bug report generated!")
            print("=" * 80)
            print()

    def demonstrate_severity_priority_rating(self):
        """Demonstrate severity and priority rating"""

        print("📊 SEVERITY & PRIORITY RATING")
        print("=" * 80)
        print("This feature analyzes bug impact to assign appropriate severity and priority levels.")
        print()

        test_cases = [
            {
                "description": "Application crashes when user tries to save assessment data",
                "affected_users": 500,
                "frequency": "always"
            },
            {
                "description": "Minor UI formatting issue on the settings page",
                "affected_users": 10,
                "frequency": "sometimes"
            },
            {
                "description": "Performance degradation when loading large datasets",
                "affected_users": 200,
                "frequency": "frequently"
            },
            {
                "description": "Spelling mistake in the help documentation",
                "affected_users": 5,
                "frequency": "once"
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"📊 Test Case {i}:")
            print("-" * 40)
            print(f"Description: {test_case['description']}")
            print(f"Affected Users: {test_case['affected_users']}")
            print(f"Frequency: {test_case['frequency']}")
            print()

            severity, priority = self.tool.generate_severity_priority_rating(
                test_case['description'],
                test_case['affected_users'],
                test_case['frequency']
            )

            print(f"🚨 Severity: {severity.value}")
            print(f"⏱️  Priority: {priority.value}")
            print()

            # Add rationale
            if severity.value == "Critical":
                print("💡 Rationale: Critical impact on system functionality affecting many users")
            elif severity.value == "High":
                print("💡 Rationale: Significant impact on user experience")
            elif severity.value == "Medium":
                print("💡 Rationale: Moderate impact with workarounds available")
            else:
                print("💡 Rationale: Minor impact on system functionality")
            print()

            print("✅ Severity and priority assigned!")
            print("=" * 80)
            print()

    def interactive_demo(self):
        """Run interactive demonstration"""

        print("🎯 BUG REPRODUCTION TOOLS - INTERACTIVE DEMO")
        print("=" * 100)
        print("Welcome to the comprehensive bug reproduction and analysis tool!")
        print("This demo will show you how to use all available features.")
        print("=" * 100)
        print()

        # Run all demonstrations
        self.demonstrate_minimal_reproduction_steps()
        self.demonstrate_root_cause_analysis()
        self.demonstrate_stack_trace_analysis()
        self.demonstrate_professional_bug_report()
        self.demonstrate_severity_priority_rating()

        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 100)
        print("Features demonstrated:")
        print("✅ Minimal reproduction steps generation")
        print("✅ Root cause analysis")
        print("✅ Stack trace analysis")
        print("✅ Professional bug report writing")
        print("✅ Severity and priority rating")
        print()
        print("These tools help improve bug reporting quality and accelerate resolution!")
        print("=" * 100)

def main():
    """Main execution function"""
    guide = BugReproductionUserGuide()
    guide.interactive_demo()

if __name__ == "__main__":
    main()