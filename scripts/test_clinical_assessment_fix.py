#!/usr/bin/env python3
"""
Test Clinical Assessment Fix
Verifies that PCL-5, AUDIT, and DASS-21 assessments all pass
data in the correct format to the ClinicalResults component
"""

import re
from pathlib import Path


def main():
    print("🔧 CLINICAL ASSESSMENT DATA FORMAT TEST")
    print("=" * 50)

    frontend_path = Path("frontend/src")

    # Test each clinical assessment
    assessments = [
        {
            "name": "PCL-5",
            "file": "pages/clinical/PCL5Assessment.tsx",
            "expected_route": "/clinical/assessment/pcl5/complete",
        },
        {
            "name": "AUDIT",
            "file": "pages/clinical/AUDITAssessment.tsx",
            "expected_route": "/clinical/assessment/audit/complete",
        },
        {
            "name": "DASS-21",
            "file": "pages/clinical/DASS21Assessment.tsx",
            "expected_route": "/clinical/assessment/dass21/complete",
        },
    ]

    all_correct = True

    for assessment in assessments:
        print(f"\n🩺 Testing {assessment['name']} Assessment:")
        print("-" * 30)

        file_path = frontend_path / assessment["file"]

        if not file_path.exists():
            print(f"❌ File not found: {assessment['file']}")
            all_correct = False
            continue

        with open(file_path, "r") as f:
            content = f.read()

        # Check 1: Correct navigation route
        nav_match = re.search(r"navigate\('([^']+)'", content)
        if nav_match:
            actual_route = nav_match.group(1)
            if actual_route == assessment["expected_route"]:
                print(f"✅ Route: {actual_route}")
            else:
                print(
                    f"❌ Route: {actual_route} (expected: {assessment['expected_route']})"
                )
                all_correct = False
        else:
            print("❌ No navigate call found")
            all_correct = False

        # Check 2: State data structure
        state_match = re.search(
            r"state:\s*\{\s*assessmentType:\s*'([^']+)',\s*result:\s*([^}]+)\s*\}",
            content,
        )
        if state_match:
            assessment_type = state_match.group(1)
            print(
                f"✅ State structure: assessmentType: '{assessment_type}', result: object"
            )

            # Check 3: Result object structure
            result_section = content[state_match.end() :]

            # Look for score field
            score_match = re.search(r"score:\s*\w+", result_section)
            if score_match:
                print("✅ Result contains 'score' field")
            else:
                print("❌ Result missing 'score' field")
                all_correct = False

            # Look for severity_level field
            severity_match = re.search(r"severity_level:\s*\w+\(", result_section)
            if severity_match:
                print("✅ Result contains 'severity_level' field")
            else:
                print("❌ Result missing 'severity_level' field")
                all_correct = False

        else:
            print("❌ Incorrect state structure")
            all_correct = False

        # Check 4: Severity level function exists
        severity_func_match = re.search(r"const get\w+SeverityLevel.*=.*=>", content)
        if severity_func_match:
            print("✅ Severity level function exists")
        else:
            print("⚠️  No severity level function found (may use inline calculation)")

    # Check ClinicalResults interface
    print(f"\n📋 ClinicalResults Interface Requirements:")
    print("-" * 35)

    clinical_results_file = frontend_path / "pages/ClinicalResults.tsx"
    with open(clinical_results_file, "r") as f:
        clinical_content = f.read()

    # Check interface requirements
    interface_fields = ["score", "severity_level"]
    for field in interface_fields:
        if f"{field}:" in clinical_content:
            print(f"✅ Interface requires '{field}'")
        else:
            print(f"❌ Interface missing '{field}'")
            all_correct = False

    # Final result
    print(f"\n🏁 TEST RESULT:")
    print("=" * 20)

    if all_correct:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Clinical assessment data format is consistent")
        print("🔧 PCL-5 and AUDIT 'Results not found' issue should be resolved")
        print("📊 All assessments now pass data in the correct format:")
        print("   - score: number")
        print("   - severity_level: string")
        print("   - assessmentType: string")
        print("   - Additional assessment-specific fields")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Data format inconsistencies remain")

    print(f"\n💡 NEXT STEPS:")
    print("1. Test PCL-5 assessment completion in browser")
    print("2. Test AUDIT assessment completion in browser")
    print("3. Verify DASS-21 still works correctly")
    print("4. All should now display results instead of 'Results not found'")


if __name__ == "__main__":
    main()
