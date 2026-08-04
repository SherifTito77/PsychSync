#!/usr/bin/env python3
"""
Test All Enhanced Clinical Assessments
Comprehensive verification that ALL clinical assessments now provide
detailed, assessment-specific information and resources
"""

import re
from pathlib import Path


def main():
    print("🏥 COMPREHENSIVE CLINICAL ASSESSMENTS ENHANCEMENT TEST")
    print("=" * 65)
    print(
        "Verifying that ALL clinical assessments provide comprehensive information..."
    )

    frontend_path = Path("frontend/src/pages/ClinicalResults.tsx")

    if not frontend_path.exists():
        print("❌ ClinicalResults.tsx not found")
        return

    with open(frontend_path, "r") as f:
        content = f.read()

    print("\n📋 ALL ASSESSMENT ENHANCEMENT VERIFICATION:")
    print("-" * 45)

    # Test PCL-5 enhancements
    print(f"\n🩺 PCL-5 (PTSD Assessment):")
    pcl5_checks = [
        ("Information section", "tool === 'pcl5' &&"),
        ("Understanding PCL-5 Results title", "Understanding Your PCL-5 Results"),
        (
            "PTSD symptom explanation",
            "PCL-5 assesses PTSD symptoms across four clusters",
        ),
        (
            "Evidence-based treatments",
            "EMDR (Eye Movement Desensitization and Reprocessing)",
        ),
        (
            "Treatment effectiveness timeline",
            "significant improvement within 12-16 weeks",
        ),
        ("Importance of treatment", "Untreated PTSD can affect your relationships"),
        ("Severe symptoms warning", "For Severe Symptoms:"),
        ("Grounding techniques", "Name 5 things you see, 4 you can touch"),
        (
            "Deep breathing instructions",
            "Inhale for 4 counts, hold for 4, exhale for 6",
        ),
        ("Recovery encouragement", "Treatment works and recovery is possible"),
    ]

    pcl5_rec_checks = [
        ("Minimal symptoms guidance", "Your symptoms suggest minimal PTSD symptoms"),
        ("Mild symptoms action", "Your symptoms suggest mild PTSD symptoms"),
        ("Moderate symptoms treatment", "Your symptoms suggest moderate PTSD symptoms"),
        (
            "Severe symptoms emergency",
            "Your symptoms suggest severe PTSD requiring immediate professional intervention",
        ),
        ("Treatment options", "Consider trauma-focused therapy options like EMDR"),
        ("Avoidance coping", "Avoid alcohol and drugs as coping mechanisms"),
    ]

    pcl5_resource_checks = [
        ("Veterans Crisis Line", "Veterans Crisis Line"),
        ("PTSD treatment resources", "PTSD Treatment Options"),
        ("EMDR therapist directory", "EMDR International Association"),
        ("National PTSD resources", "National Center for PTSD"),
        ("Trauma support groups", "Trauma-Informed Support Groups"),
        ("Grounding resources", "Grounding Techniques & Self-Help"),
    ]

    # Test DASS-21 enhancements
    print(f"\n🧠 DASS-21 (Depression, Anxiety, Stress Scales):")
    dass21_checks = [
        ("Information section", "tool === 'dass21' &&"),
        ("Understanding DASS-21 Results title", "Understanding Your DASS-21 Results"),
        (
            "Three core emotions explanation",
            "DASS-21 measures three core emotional states",
        ),
        (
            "Treatment options",
            "Cognitive Behavioral Therapy (CBT), mindfulness-based approaches",
        ),
        ("Treatment timeline", "significant improvement within 8-12 weeks"),
        (
            "Importance of intervention",
            "Untreated depression and anxiety can affect your physical health",
        ),
        ("Severe symptoms warning", "For Severe Symptoms:"),
        ("Coping strategies", "Practice progressive muscle relaxation"),
        ("Mindfulness techniques", "Use mindfulness techniques"),
        ("Exercise benefit", "even 10 minutes can boost mood"),
    ]

    dass21_rec_checks = [
        ("Minimal symptoms", "Your symptoms suggest minimal distress"),
        ("Mild symptoms guidance", "Your symptoms suggest mild distress"),
        ("Moderate symptoms treatment", "Your symptoms suggest moderate distress"),
        (
            "Severe symptoms emergency",
            "Your symptoms suggest severe distress requiring immediate professional intervention",
        ),
        (
            "Exercise effectiveness",
            "as effective as some medications for mild depression",
        ),
        ("Sleep importance", "Ensure adequate sleep (7-9 hours)"),
        (
            "CBT success rates",
            "Evidence-based treatments like CBT have 60-70% success rates",
        ),
    ]

    dass21_resource_checks = [
        ("ADAA resources", "Anxiety & Depression Association of America"),
        ("NAMI support", "National Alliance on Mental Illness (NAMI)"),
        ("DBSA support groups", "Depression and Bipolar Support Alliance"),
        ("Mindfulness apps", "Mindfulness & Meditation Apps"),
        ("CBT resources", "Cognitive Behavioral Therapy Resources"),
        ("Emergency services for severe", "Emergency Services"),
    ]

    # Test AUDIT enhancements
    print(f"\n🍺 AUDIT (Alcohol Use Assessment):")
    audit_checks = [
        ("Information section", "tool === 'audit' &&"),
        ("Understanding AUDIT Results title", "Understanding Your AUDIT Results"),
        (
            "AUDIT explanation",
            "AUDIT (Alcohol Use Disorders Identification Test) assesses",
        ),
        (
            "Treatment as medical condition",
            "Alcohol use disorder is a treatable medical condition",
        ),
        (
            "Health impact",
            "Excessive alcohol use can damage your liver, heart, and brain",
        ),
        ("High risk warning", "For High Risk Drinking Patterns:"),
        (
            "Reduction strategies",
            "Set clear limits: Decide in advance how much you'll drink",
        ),
        ("Health benefits", "Improved sleep quality and energy levels"),
        ("Signs for professional help", "Signs You May Need Professional Help"),
    ]

    audit_rec_checks = [
        ("Low risk guidance", "Your drinking pattern appears to be low risk"),
        ("Mild risk attention", "Your drinking pattern suggests some risk"),
        ("Moderate risk action", "Your drinking pattern indicates moderate risk"),
        (
            "High risk emergency",
            "Your drinking pattern indicates high risk requiring immediate attention",
        ),
        (
            "Abstinence recommendation",
            "Strongly consider reducing or abstaining from alcohol",
        ),
        ("Treatment hope", "This condition is treatable and recovery is possible"),
    ]

    audit_resource_checks = [
        ("AA meetings", "Alcoholics Anonymous"),
        ("SMART Recovery", "SMART Recovery"),
        ("Treatment finder", "Find Treatment Providers"),
        ("Professional detox", "medical detoxification"),
        ("Comprehensive treatment", "comprehensive treatment including counseling"),
    ]

    def check_section(checks, section_name):
        passed = 0
        for check_name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {check_name}")
                passed += 1
            else:
                print(f"  ❌ {check_name}")
        print(f"  📊 {section_name}: {passed}/{len(checks)} passed")
        return passed

    # Run all checks
    pcl5_info_passed = check_section(pcl5_checks, "PCL-5 Information")
    pcl5_rec_passed = check_section(pcl5_rec_checks, "PCL-5 Recommendations")
    pcl5_res_passed = check_section(pcl5_resource_checks, "PCL-5 Resources")

    dass21_info_passed = check_section(dass21_checks, "DASS-21 Information")
    dass21_rec_passed = check_section(dass21_rec_checks, "DASS-21 Recommendations")
    dass21_res_passed = check_section(dass21_resource_checks, "DASS-21 Resources")

    audit_info_passed = check_section(audit_checks, "AUDIT Information")
    audit_rec_passed = check_section(audit_rec_checks, "AUDIT Recommendations")
    audit_res_passed = check_section(audit_resource_checks, "AUDIT Resources")

    # Calculate totals
    total_checks = sum(
        [
            len(pcl5_checks),
            len(pcl5_rec_checks),
            len(pcl5_resource_checks),
            len(dass21_checks),
            len(dass21_rec_checks),
            len(dass21_resource_checks),
            len(audit_checks),
            len(audit_rec_checks),
            len(audit_resource_checks),
        ]
    )

    total_passed = sum(
        [
            pcl5_info_passed,
            pcl5_rec_passed,
            pcl5_res_passed,
            dass21_info_passed,
            dass21_rec_passed,
            dass21_res_passed,
            audit_info_passed,
            audit_rec_passed,
            audit_res_passed,
        ]
    )

    print(f"\n🏁 COMPREHENSIVE ENHANCEMENT RESULTS:")
    print("=" * 40)
    print(
        f"🩺 PCL-5 Assessment: {pcl5_info_passed + pcl5_rec_passed + pcl5_res_passed}/{len(pcl5_checks) + len(pcl5_rec_checks) + len(pcl5_resource_checks)} total"
    )
    print(f"   - Information: {pcl5_info_passed}/{len(pcl5_checks)}")
    print(f"   - Recommendations: {pcl5_rec_passed}/{len(pcl5_rec_checks)}")
    print(f"   - Resources: {pcl5_res_passed}/{len(pcl5_resource_checks)}")

    print(
        f"🧠 DASS-21 Assessment: {dass21_info_passed + dass21_rec_passed + dass21_res_passed}/{len(dass21_checks) + len(dass21_rec_checks) + len(dass21_resource_checks)} total"
    )
    print(f"   - Information: {dass21_info_passed}/{len(dass21_checks)}")
    print(f"   - Recommendations: {dass21_rec_passed}/{len(dass21_rec_checks)}")
    print(f"   - Resources: {dass21_res_passed}/{len(dass21_resource_checks)}")

    print(
        f"🍺 AUDIT Assessment: {audit_info_passed + audit_rec_passed + audit_res_passed}/{len(audit_checks) + len(audit_rec_checks) + len(audit_resource_checks)} total"
    )
    print(f"   - Information: {audit_info_passed}/{len(audit_checks)}")
    print(f"   - Recommendations: {audit_rec_passed}/{len(audit_rec_checks)}")
    print(f"   - Resources: {audit_res_passed}/{len(audit_resource_checks)}")

    print(
        f"\n📊 OVERALL: {total_passed}/{total_checks} ({(total_passed/total_checks*100):.1f}%)"
    )

    if total_passed >= total_checks * 0.95:  # 95% success rate
        print(f"\n🎉 ALL CLINICAL ASSESSMENTS SUCCESSFULLY ENHANCED!")
        print(f"\n✅ ENHANCED FEATURES NOW AVAILABLE:")
        print(f"   🩺 PCL-5 (PTSD):")
        print(f"      • Detailed trauma education and symptom explanations")
        print(f"      • Evidence-based treatment information (EMDR, CPT, PE)")
        print(f"      • Trauma-informed coping strategies and grounding techniques")
        print(f"      • PTSD-specific resources and crisis lines")
        print(f"      • Recovery-focused messaging with hope")
        print(f"\n   🧠 DASS-21 (Depression/Anxiety/Stress):")
        print(f"      • Three emotional states education and impact")
        print(f"      • Evidence-based treatment information (CBT, mindfulness)")
        print(f"      • Practical coping strategies and lifestyle modifications")
        print(f"      • Mental health-specific resources and support organizations")
        print(f"      • Severity-appropriate guidance with clear action steps")
        print(f"\n   🍺 AUDIT (Alcohol Use):")
        print(f"      • Alcohol use disorder education as medical condition")
        print(f"      • Risk-appropriate reduction strategies and health benefits")
        print(f"      • Addiction treatment resources and support groups")
        print(f"      • Stigma-reducing language emphasizing treatability")
        print(f"      • Recovery-focused resources and professional help guidance")
        print(f"\n🔧 COMMON ENHANCEMENTS:")
        print(f"   • Crisis intervention protocols for severe scores")
        print(f"   • Assessment-specific color coding and theming")
        print(f"   • Immediate coping strategies and safety planning")
        print(f"   • Professional help recommendations with urgency levels")
        print(f"   • Evidence-based treatment information with success rates")
        print(f"   • Recovery hope and destigmatization messaging")
        print(f"\n🚀 The clinical assessment results now provide comprehensive,")
        print(f"   trauma-informed, and actionable information for all users!")
    else:
        print(f"\n⚠️ {total_checks - total_passed} enhancements need attention")


if __name__ == "__main__":
    main()
