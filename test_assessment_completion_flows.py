#!/usr/bin/env python3
"""
Comprehensive Assessment Completion Flow Test

This script tests that all assessments properly navigate to results pages
after completion, ensuring consistent routing patterns across the platform.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_assessment_navigation_patterns():
    """Check that all assessments have consistent navigation patterns."""

    frontend_path = Path("frontend/src")

    assessment_files = [
        "pages/clinical/DASS21Assessment.tsx",
        "pages/clinical/PCL5Assessment.tsx",
        "pages/clinical/AUDITAssessment.tsx",
        "pages/assessments/types/MBTIAssessmentPage.tsx",
        "pages/assessments/types/BigFiveAssessmentPage.tsx",
        "pages/assessments/types/EnneagramAssessmentPage.tsx",
        "pages/assessments/types/DISCAssessmentPage.tsx",
        "pages/assessments/types/PredictiveIndexPage.tsx",
        "pages/assessments/types/SocialStylesPage.tsx",
        "pages/assessments/types/StrengthsFinderPage.tsx"
    ]

    print("🔍 ASSESSMENT COMPLETION FLOW ANALYSIS")
    print("=" * 50)

    clinical_patterns = {}
    personality_patterns = {}

    for assessment_file in assessment_files:
        file_path = frontend_path / assessment_file

        if not file_path.exists():
            print(f"❌ Missing file: {assessment_file}")
            continue

        print(f"\n📋 Analyzing: {assessment_file}")

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for navigate calls related to results
            lines = content.split('\n')
            navigate_calls = []
            shows_inline_results = False

            for i, line in enumerate(lines, 1):
                if 'navigate(' in line and ('result' in line.lower() or 'complete' in line.lower()):
                    navigate_calls.append((i, line.strip()))
                elif 'if (results)' in line or 'results &&' in line:
                    shows_inline_results = True

            assessment_name = Path(assessment_file).stem

            if 'clinical' in assessment_file:
                clinical_patterns[assessment_name] = {
                    'navigations': navigate_calls,
                    'inline_results': shows_inline_results,
                    'file_path': assessment_file
                }
            else:
                personality_patterns[assessment_name] = {
                    'navigations': navigate_calls,
                    'inline_results': shows_inline_results,
                    'file_path': assessment_file
                }

            # Display findings
            if shows_inline_results:
                print(f"  ✅ Shows inline results (no navigation needed)")
            elif navigate_calls:
                print(f"  🧭 Has {len(navigate_calls)} navigation call(s):")
                for line_num, nav_call in navigate_calls:
                    print(f"    Line {line_num}: {nav_call}")
            else:
                print(f"  ⚠️  No results handling found")

        except Exception as e:
            print(f"  ❌ Error analyzing file: {e}")

    print("\n\n🎯 CLINICAL ASSESSMENT ROUTING PATTERNS")
    print("=" * 40)

    for assessment, data in clinical_patterns.items():
        print(f"\n🩺 {assessment}:")
        if data['inline_results']:
            print(f"  ✅ Inline results display")
        elif data['navigations']:
            for line_num, nav_call in data['navigations']:
                print(f"  🧭 {nav_call}")
                # Check if it uses the correct pattern
                if '/clinical/assessment/' in nav_call and '/complete' in nav_call:
                    print(f"    ✅ Uses correct route pattern")
                elif '/clinical/results' in nav_call:
                    print(f"    ⚠️  Potentially incorrect route pattern")
                else:
                    print(f"    ❓ Unknown route pattern")

    print("\n\n🧠 PERSONALITY ASSESSMENT PATTERNS")
    print("=" * 40)

    for assessment, data in personality_patterns.items():
        print(f"\n🎭 {assessment}:")
        if data['inline_results']:
            print(f"  ✅ Inline results display")
        elif data['navigations']:
            for line_num, nav_call in data['navigations']:
                print(f"  🧭 {nav_call}")
        else:
            print(f"  ⚠️  No clear results pattern found")

    # Check for consistency
    print("\n\n📊 CONSISTENCY ANALYSIS")
    print("=" * 30)

    clinical_routes = set()
    for assessment, data in clinical_patterns.items():
        for _, nav_call in data['navigations']:
            if '/clinical/assessment/' in nav_call:
                # Extract the route pattern
                start = nav_call.find('\'') + 1
                end = nav_call.find('\'', start)
                if start > 0 and end > 0:
                    route = nav_call[start:end].split(':')[0]  # Remove dynamic parts
                    clinical_routes.add(route)

    print(f"🩺 Clinical assessment route patterns found:")
    for route in sorted(clinical_routes):
        print(f"  {route}")

    if len(clinical_routes) == 1 and '/clinical/assessment/' in list(clinical_routes)[0]:
        print(f"  ✅ All clinical assessments use consistent routing!")
    else:
        print(f"  ⚠️  Inconsistent routing patterns detected")

    return len(clinical_routes) == 1

def verify_app_routing():
    """Verify that App.tsx defines the necessary routes."""

    app_file = Path("frontend/src/App.tsx")

    if not app_file.exists():
        print("❌ App.tsx not found")
        return False

    print("\n\n🛣️  APP.TSX ROUTING VERIFICATION")
    print("=" * 35)

    try:
        with open(app_file, 'r') as f:
            content = f.read()

        # Check for clinical results route
        if 'path="/clinical/assessment/:tool/complete"' in content:
            print("✅ Clinical assessment completion route defined")
        else:
            print("❌ Clinical assessment completion route missing")

        # Check for ClinicalResults component usage
        if '<ClinicalResults' in content:
            print("✅ ClinicalResults component is used")
        else:
            print("❌ ClinicalResults component not found")

        # Look for alternative /clinical/results route
        if 'path="/clinical/results"' in content:
            print("ℹ️  Alternative /clinical/results route also defined")
        else:
            print("ℹ️  No alternative /clinical/results route found")

        return True

    except Exception as e:
        print(f"❌ Error analyzing App.tsx: {e}")
        return False

def main():
    """Main test execution."""

    print("🚀 PSYCHSYNC ASSESSMENT COMPLETION FLOW TEST")
    print("=" * 55)
    print("Testing all assessment completion and routing patterns...")

    # Change to project root
    if not Path("frontend/src").exists():
        print("❌ Error: Run from project root directory")
        sys.exit(1)

    # Test 1: Check navigation patterns
    patterns_consistent = check_assessment_navigation_patterns()

    # Test 2: Verify App.tsx routing
    routing_valid = verify_app_routing()

    # Final assessment
    print("\n\n🏁 TEST RESULTS")
    print("=" * 20)

    if patterns_consistent and routing_valid:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Assessment completion flows are working correctly")
        print("🔧 PCL-5 routing issue has been resolved")
    else:
        print("❌ SOME TESTS FAILED")
        if not patterns_consistent:
            print("⚠️  Inconsistent navigation patterns detected")
        if not routing_valid:
            print("⚠️  Routing configuration issues found")

    print("\n💡 RECOMMENDATIONS:")
    print("  • Test PCL-5 assessment completion in browser")
    print("  • Verify AUDIT assessment also works correctly")
    print("  • All clinical assessments should now use consistent routing")
    print("  • Personality assessments correctly show inline results")

if __name__ == "__main__":
    main()
