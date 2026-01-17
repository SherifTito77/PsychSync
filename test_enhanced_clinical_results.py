#!/usr/bin/env python3
"""
Test Enhanced Clinical Results
Verifies that the enhanced ClinicalResults component provides comprehensive information
"""

import re
from pathlib import Path

def main():
    print("🏥 TESTING ENHANCED CLINICAL RESULTS COMPONENT")
    print("=" * 55)
    print("Verifying comprehensive PTSD and AUDIT content...")

    frontend_path = Path("frontend/src/pages/ClinicalResults.tsx")

    if not frontend_path.exists():
        print("❌ ClinicalResults.tsx not found")
        return

    with open(frontend_path, 'r') as f:
        content = f.read()

    print("\n📋 ENHANCEMENT VERIFICATION:")
    print("-" * 35)

    # Test PCL-5 specific enhancements
    print(f"\n🩺 PCL-5 (PTSD) Specific Content:")

    pcl5_checks = [
        ("PCL-5 section", "tool === 'pcl5'"),
        ("Understanding Your PCL-5 Results", "Understanding Your PCL-5 Results"),
        ("PTSD explanation", "PCL-5 assesses PTSD symptoms across four clusters"),
        ("Evidence-based treatments", "EMDR (Eye Movement Desensitization and Reprocessing)"),
        ("Treatment effectiveness", "significant improvement within 12-16 weeks"),
        ("Why treatment is important", "Untreated PTSD can affect your relationships"),
        ("Severe symptoms warning", "For Severe Symptoms:"),
        ("Grounding techniques", "Name 5 things you see, 4 you can touch"),
        ("Deep breathing", "Inhale for 4 counts, hold for 4, exhale for 6"),
    ]

    pcl5_passed = 0
    for check_name, pattern in pcl5_checks:
        if pattern in content:
            print(f"  ✅ {check_name}")
            pcl5_passed += 1
        else:
            print(f"  ❌ {check_name}")

    # Test enhanced recommendations for PCL-5
    print(f"\n💡 Enhanced PCL-5 Recommendations:")
    pcl5_rec_checks = [
        ("Mild symptoms", "Your symptoms suggest mild PTSD symptoms"),
        ("Moderate symptoms", "Your symptoms suggest moderate PTSD symptoms"),
        ("Severe symptoms", "Your symptoms suggest severe PTSD requiring immediate professional intervention"),
        ("Treatment options", "Consider trauma-focused therapy options like EMDR"),
        ("Avoid substances", "Avoid alcohol and drugs as coping mechanisms"),
        ("Recovery hope", "Treatment works and recovery is possible"),
    ]

    pcl5_rec_passed = 0
    for check_name, pattern in pcl5_rec_checks:
        if pattern in content:
            print(f"  ✅ {check_name}")
            pcl5_rec_passed += 1
        else:
            print(f"  ❌ {check_name}")

    # Test PTSD-specific resources
    print(f"\n📚 PCL-5 Specific Resources:")
    pcl5_resource_checks = [
        ("Crisis resources", "Veterans Crisis Line"),
        ("PTSD treatment info", "PTSD Treatment Options"),
        ("EMDR therapists", "EMDR International Association"),
        ("National Center for PTSD", "National Center for PTSD"),
        ("Support groups", "Trauma-Informed Support Groups"),
        ("Grounding techniques", "Grounding Techniques & Self-Help"),
    ]

    pcl5_resource_passed = 0
    for check_name, pattern in pcl5_resource_checks:
        if pattern in content:
            print(f"  ✅ {check_name}")
            pcl5_resource_passed += 1
        else:
            print(f"  ❌ {check_name}")

    # Test AUDIT enhancements
    print(f"\n🍺 AUDIT (Alcohol) Specific Content:")
    audit_checks = [
        ("AUDIT recommendations", "toolType === 'audit'"),
        ("Minimal risk guidance", "Your drinking pattern appears to be low risk"),
        ("Severe risk warning", "Your drinking pattern indicates high risk requiring immediate attention"),
        ("Treatment resources", "Find local AA meetings"),
        ("SMART Recovery", "SMART Recovery"),
        ("Professional help", "comprehensive treatment including counseling"),
    ]

    audit_passed = 0
    for check_name, pattern in audit_checks:
        if pattern in content:
            print(f"  ✅ {check_name}")
            audit_passed += 1
        else:
            print(f"  ❌ {check_name}")

    # Test general improvements
    print(f"\n🛡️ General Safety Enhancements:")
    safety_checks = [
        ("988 crisis line", "988 Suicide & Crisis Lifeline"),
        ("Crisis Text Line", "Text HOME to 741741"),
        ("SAMHSA helpline", "SAMHSA National Helpline"),
    ]

    safety_passed = 0
    for check_name, pattern in safety_checks:
        if pattern in content:
            print(f"  ✅ {check_name}")
            safety_passed += 1
        else:
            print(f"  ❌ {check_name}")

    # Calculate totals
    total_checks = len(pcl5_checks) + len(pcl5_rec_checks) + len(pcl5_resource_checks) + len(audit_checks) + len(safety_checks)
    total_passed = pcl5_passed + pcl5_rec_passed + pcl5_resource_passed + audit_passed + safety_passed

    print(f"\n🏁 ENHANCEMENT TEST RESULTS:")
    print("=" * 30)
    print(f"✅ PCL-5 Content: {pcl5_passed}/{len(pcl5_checks)} passed")
    print(f"✅ PCL-5 Recommendations: {pcl5_rec_passed}/{len(pcl5_rec_checks)} passed")
    print(f"✅ PCL-5 Resources: {pcl5_resource_passed}/{len(pcl5_resource_checks)} passed")
    print(f"✅ AUDIT Content: {audit_passed}/{len(audit_checks)} passed")
    print(f"✅ Safety Features: {safety_passed}/{len(safety_checks)} passed")
    print(f"\n📊 Overall: {total_passed}/{total_checks} ({(total_passed/total_checks*100):.1f}%)")

    if total_passed == total_checks:
        print("\n🎉 ALL ENHANCEMENTS VERIFIED SUCCESSFULLY!")
        print("\n✅ PCL-5 Results Now Include:")
        print("   • Detailed PTSD explanations and symptom clusters")
        print("   • Evidence-based treatment information (EMDR, CPT, PE)")
        print("   • Why treatment matters and what to expect")
        print("   • Special warnings for severe symptoms")
        print("   • Immediate coping strategies (grounding, breathing)")
        print("   • PTSD-specific resources and crisis lines")
        print("   • Recovery-focused, trauma-informed messaging")
        print("\n✅ AUDIT Results Enhanced:")
        print("   • Alcohol use disorder specific recommendations")
        print("   • Risk-appropriate guidance")
        print("   • Addiction treatment resources")
        print("\n🔧 The enhanced results page now provides comprehensive,")
        print("   actionable information for serious mental health assessments!")
    else:
        print(f"\n⚠️ {total_checks - total_passed} enhancements need attention")

if __name__ == "__main__":
    main()
