#!/usr/bin/env python3
"""
Mobile Improvements Verification Script
Verifies that all mobile usability improvements have been properly implemented

Usage: python mobile_improvements_verification.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


def verify_mobile_improvements() -> Dict:
    """Verify all mobile improvements have been implemented correctly"""

    improvements = {
        "button_component": {"status": "not_checked", "issues": [], "fixes": []},
        "mobile_utilities": {"status": "not_checked", "issues": [], "fixes": []},
        "login_page": {"status": "not_checked", "issues": [], "fixes": []},
        "dashboard_page": {"status": "not_checked", "issues": [], "fixes": []},
        "assessments_page": {"status": "not_checked", "issues": [], "fixes": []},
        "dashboard_layout": {"status": "not_checked", "issues": [], "fixes": []},
    }

    print("🔍 Verifying Mobile Usability Improvements...")
    print("=" * 50)

    # 1. Verify Button Component Improvements
    print("\n📱 Checking Button Component...")
    button_file = Path("frontend/src/components/common/Button.tsx")

    if button_file.exists():
        content = button_file.read_text()

        # Check for mobile touch targets
        if "min-h-[44px]" in content:
            improvements["button_component"]["fixes"].append(
                "✅ 44px minimum touch targets implemented"
            )
        else:
            improvements["button_component"]["issues"].append(
                "❌ Missing 44px minimum touch targets"
            )

        # Check for mobile props
        if "fullWidth" in content:
            improvements["button_component"]["fixes"].append(
                "✅ fullWidth prop for mobile-friendly buttons"
            )
        else:
            improvements["button_component"]["issues"].append(
                "❌ Missing fullWidth prop"
            )

        if "mobileLarge" in content:
            improvements["button_component"]["fixes"].append(
                "✅ mobileLarge prop for enhanced mobile targets"
            )
        else:
            improvements["button_component"]["issues"].append(
                "❌ Missing mobileLarge prop"
            )

        # Check for proper padding
        if "px-4 py-3" in content:
            improvements["button_component"]["fixes"].append(
                "✅ Enhanced padding for mobile"
            )
        else:
            improvements["button_component"]["issues"].append(
                "❌ Insufficient mobile padding"
            )

        improvements["button_component"]["status"] = (
            "complete"
            if len(improvements["button_component"]["issues"]) == 0
            else "partial"
        )

    # 2. Verify Mobile Utilities
    print("\n🛠️ Checking Mobile Utility Classes...")
    utils_file = Path("frontend/src/styles/mobile-utils.css")

    if utils_file.exists():
        content = utils_file.read_text()

        # Check for key mobile utilities
        mobile_classes = [
            ".mobile-container",
            ".mobile-touch-target",
            ".mobile-input",
            ".mobile-card",
            ".mobile-text-responsive",
            ".mobile-nav-item",
        ]

        for cls in mobile_classes:
            if cls in content:
                improvements["mobile_utilities"]["fixes"].append(
                    f"✅ {cls} utility available"
                )
            else:
                improvements["mobile_utilities"]["issues"].append(
                    f"❌ Missing {cls} utility"
                )

        # Check for mobile breakpoints
        if "@media (max-width: 640px)" in content:
            improvements["mobile_utilities"]["fixes"].append(
                "✅ Mobile breakpoints defined"
            )
        else:
            improvements["mobile_utilities"]["issues"].append(
                "❌ Missing mobile breakpoints"
            )

        improvements["mobile_utilities"]["status"] = (
            "complete"
            if len(improvements["mobile_utilities"]["issues"]) == 0
            else "partial"
        )

    # 3. Verify Login Page
    print("\n🔐 Checking Login Page...")
    login_file = Path("frontend/src/pages/Login.tsx")

    if login_file.exists():
        content = login_file.read_text()

        # Check for mobile utilities import
        if "mobile-utils.css" in content:
            improvements["login_page"]["fixes"].append("✅ Mobile utilities imported")
        else:
            improvements["login_page"]["issues"].append(
                "❌ Missing mobile utilities import"
            )

        # Check for mobile input classes
        if "mobile-input" in content:
            improvements["login_page"]["fixes"].append(
                "✅ Mobile-friendly inputs implemented"
            )
        else:
            improvements["login_page"]["issues"].append(
                "❌ Missing mobile input classes"
            )

        # Check for mobile touch targets
        if "mobile-touch-target" in content:
            improvements["login_page"]["fixes"].append("✅ Touch targets optimized")
        else:
            improvements["login_page"]["issues"].append(
                "❌ Missing touch target optimization"
            )

        # Check for full-width buttons
        if "fullWidth" in content and "mobileLarge" in content:
            improvements["login_page"]["fixes"].append("✅ Full-width mobile buttons")
        else:
            improvements["login_page"]["issues"].append(
                "❌ Missing full-width mobile buttons"
            )

        improvements["login_page"]["status"] = (
            "complete" if len(improvements["login_page"]["issues"]) == 0 else "partial"
        )

    # 4. Verify Dashboard Page
    print("\n📊 Checking Dashboard Page...")
    dashboard_file = Path("frontend/src/pages/Dashboard.tsx")

    if dashboard_file.exists():
        content = dashboard_file.read_text()

        if "mobile-utils.css" in content:
            improvements["dashboard_page"]["fixes"].append(
                "✅ Mobile utilities imported"
            )
        else:
            improvements["dashboard_page"]["issues"].append(
                "❌ Missing mobile utilities import"
            )

        # Check for mobile responsive classes
        if "mobile-text-responsive" in content:
            improvements["dashboard_page"]["fixes"].append("✅ Mobile responsive text")
        else:
            improvements["dashboard_page"]["issues"].append(
                "❌ Missing mobile text optimization"
            )

        if "mobile-card" in content:
            improvements["dashboard_page"]["fixes"].append("✅ Mobile card layouts")
        else:
            improvements["dashboard_page"]["issues"].append(
                "❌ Missing mobile card optimization"
            )

        if "mobile-touch-target" in content:
            improvements["dashboard_page"]["fixes"].append("✅ Touch targets optimized")
        else:
            improvements["dashboard_page"]["issues"].append(
                "❌ Missing touch target optimization"
            )

        # Check for responsive grids
        if "sm:grid-cols-2" in content:
            improvements["dashboard_page"]["fixes"].append("✅ Responsive grid layouts")
        else:
            improvements["dashboard_page"]["issues"].append(
                "❌ Missing responsive grid patterns"
            )

        improvements["dashboard_page"]["status"] = (
            "complete"
            if len(improvements["dashboard_page"]["issues"]) == 0
            else "partial"
        )

    # 5. Verify Assessments Page
    print("\n📋 Checking Assessments Page...")
    assessments_file = Path("frontend/src/pages/Assessments.tsx")

    if assessments_file.exists():
        content = assessments_file.read_text()

        if "mobile-utils.css" in content:
            improvements["assessments_page"]["fixes"].append(
                "✅ Mobile utilities imported"
            )
        else:
            improvements["assessments_page"]["issues"].append(
                "❌ Missing mobile utilities import"
            )

        # Check for mobile responsive layouts
        if "mobile-container" in content:
            improvements["assessments_page"]["fixes"].append(
                "✅ Mobile container implemented"
            )
        else:
            improvements["assessments_page"]["issues"].append(
                "❌ Missing mobile container"
            )

        if "mobile-text-responsive" in content:
            improvements["assessments_page"]["fixes"].append(
                "✅ Mobile responsive text"
            )
        else:
            improvements["assessments_page"]["issues"].append(
                "❌ Missing mobile text optimization"
            )

        # Check for responsive button layouts
        if "flex-col sm:flex-row" in content:
            improvements["assessments_page"]["fixes"].append(
                "✅ Responsive button layouts"
            )
        else:
            improvements["assessments_page"]["issues"].append(
                "❌ Missing responsive button layouts"
            )

        if "mobileLarge" in content:
            improvements["assessments_page"]["fixes"].append(
                "✅ Enhanced mobile button targets"
            )
        else:
            improvements["assessments_page"]["issues"].append(
                "❌ Missing enhanced mobile targets"
            )

        improvements["assessments_page"]["status"] = (
            "complete"
            if len(improvements["assessments_page"]["issues"]) == 0
            else "partial"
        )

    # 6. Verify Dashboard Layout (Navigation)
    print("\n🧭 Checking Dashboard Layout Navigation...")
    layout_file = Path("frontend/src/components/layout/DashboardLayout.tsx")

    if layout_file.exists():
        content = layout_file.read_text()

        if "mobile-utils.css" in content:
            improvements["dashboard_layout"]["fixes"].append(
                "✅ Mobile utilities imported"
            )
        else:
            improvements["dashboard_layout"]["issues"].append(
                "❌ Missing mobile utilities import"
            )

        # Check for enhanced mobile navigation
        if "mobile-nav-item" in content:
            improvements["dashboard_layout"]["fixes"].append(
                "✅ Mobile navigation items optimized"
            )
        else:
            improvements["dashboard_layout"]["issues"].append(
                "❌ Missing mobile navigation optimization"
            )

        # Check for improved mobile menu button
        if "p-3 mobile-touch-target" in content:
            improvements["dashboard_layout"]["fixes"].append(
                "✅ Enhanced mobile menu button"
            )
        else:
            improvements["dashboard_layout"]["issues"].append(
                "❌ Mobile menu button needs improvement"
            )

        # Check for additional navigation items
        if "Settings" in content and "My Responses" in content:
            improvements["dashboard_layout"]["fixes"].append(
                "✅ Additional mobile navigation items"
            )
        else:
            improvements["dashboard_layout"]["issues"].append(
                "❌ Limited mobile navigation options"
            )

        # Check for proper mobile menu spacing
        if "px-4 py-3" in content and "space-y-2" in content:
            improvements["dashboard_layout"]["fixes"].append(
                "✅ Proper mobile menu spacing"
            )
        else:
            improvements["dashboard_layout"]["issues"].append(
                "❌ Insufficient mobile menu spacing"
            )

        improvements["dashboard_layout"]["status"] = (
            "complete"
            if len(improvements["dashboard_layout"]["issues"]) == 0
            else "partial"
        )

    return improvements


def generate_improvement_report(improvements: Dict) -> Dict:
    """Generate comprehensive improvement report"""

    total_components = len(improvements)
    completed_components = sum(
        1 for comp in improvements.values() if comp["status"] == "complete"
    )
    partial_components = sum(
        1 for comp in improvements.values() if comp["status"] == "partial"
    )

    total_fixes = sum(len(comp["fixes"]) for comp in improvements.values())
    total_issues = sum(len(comp["issues"]) for comp in improvements.values())

    # Calculate completion percentage
    if total_fixes + total_issues > 0:
        completion_percentage = round(
            (total_fixes / (total_fixes + total_issues)) * 100, 1
        )
    else:
        completion_percentage = 0

    return {
        "summary": {
            "total_components": total_components,
            "completed_components": completed_components,
            "partial_components": partial_components,
            "completion_percentage": completion_percentage,
            "total_fixes": total_fixes,
            "total_issues": total_issues,
        },
        "details": improvements,
        "recommendations": generate_recommendations(improvements),
    }


def generate_recommendations(improvements: Dict) -> List[str]:
    """Generate recommendations based on verification results"""
    recommendations = []

    # Check for common patterns in issues
    all_issues = []
    for comp in improvements.values():
        all_issues.extend(comp["issues"])

    # Analyze issues and generate recommendations
    if "Missing mobile utilities import" in all_issues:
        recommendations.append(
            "🔧 Add mobile utilities import to components missing it"
        )

    if any("touch target" in issue for issue in all_issues):
        recommendations.append(
            "📱 Ensure all interactive elements have proper touch targets"
        )

    if any("responsive" in issue.lower() for issue in all_issues):
        recommendations.append(
            "📐 Implement responsive design patterns across components"
        )

    if any("mobile text" in issue.lower() for issue in all_issues):
        recommendations.append("📝 Optimize text sizing and readability for mobile")

    # Component-specific recommendations
    if improvements["dashboard_layout"]["issues"]:
        recommendations.append("🧭 Complete mobile navigation enhancements")

    if any(comp["status"] != "complete" for comp in improvements.values()):
        recommendations.append("⚠️ Address remaining partial implementations")

    # Positive recommendations if doing well
    if all(comp["status"] == "complete" for comp in improvements.values()):
        recommendations.append(
            "🎉 Excellent! All mobile improvements successfully implemented"
        )
        recommendations.append("📊 Consider setting up automated mobile testing")

    return recommendations


def main():
    """Main verification function"""
    print("🚀 MOBILE USABILITY IMPROVEMENTS VERIFICATION")
    print("=" * 55)
    print("Checking implementation status of all mobile improvements...")

    # Run verification
    improvements = verify_mobile_improvements()

    # Generate report
    report = generate_improvement_report(improvements)

    # Print results
    print(f"\n📊 VERIFICATION SUMMARY")
    print("-" * 30)
    print(
        f"✅ Components Completed: {report['summary']['completed_components']}/{report['summary']['total_components']}"
    )
    print(f"⚠️  Components Partial: {report['summary']['partial_components']}")
    print(f"📈 Completion Rate: {report['summary']['completion_percentage']}%")
    print(f"🔧 Total Fixes: {report['summary']['total_fixes']}")
    print(f"❌ Total Issues: {report['summary']['total_issues']}")

    # Detailed component status
    print(f"\n📱 COMPONENT STATUS")
    print("-" * 20)

    for component, details in improvements.items():
        status_emoji = {"complete": "✅", "partial": "⚠️", "not_checked": "❓"}.get(
            details["status"], "❓"
        )

        print(
            f"{status_emoji} {component.replace('_', ' ').title()}: {details['status'].upper()}"
        )

        if details["fixes"]:
            for fix in details["fixes"][:2]:  # Show first 2 fixes
                print(f"    {fix}")

        if details["issues"]:
            for issue in details["issues"][:2]:  # Show first 2 issues
                print(f"    {issue}")

    # Recommendations
    if report["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 18)
        for rec in report["recommendations"]:
            print(f"   {rec}")

    # Overall assessment
    completion_rate = report["summary"]["completion_percentage"]

    print(f"\n🎯 OVERALL ASSESSMENT")
    print("-" * 22)

    if completion_rate >= 90:
        print("🟢 EXCELLENT: Mobile improvements successfully implemented")
        print("   Ready for production deployment")
    elif completion_rate >= 75:
        print("🟡 GOOD: Most mobile improvements complete")
        print("   Minor items need attention")
    elif completion_rate >= 50:
        print("🟠 MODERATE: Half of improvements implemented")
        print("   Continue with remaining components")
    else:
        print("🔴 NEEDS WORK: More improvements required")
        print("   Focus on core mobile usability first")

    # Save detailed report
    report_file = Path("mobile_improvements_verification_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    return completion_rate >= 75


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
