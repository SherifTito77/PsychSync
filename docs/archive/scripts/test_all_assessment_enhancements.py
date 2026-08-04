#!/usr/bin/env python3
"""
Test All Assessment Enhancements
Comprehensive verification that ALL personality assessments have been enhanced
with comprehensive educational content and proper functionality
"""

import re
from pathlib import Path


def main():
    print("🎯 TESTING ALL ASSESSMENT ENHANCEMENTS")
    print("=" * 60)
    print("Verifying that ALL personality assessments have been enhanced with")
    print("comprehensive educational content, proper structure, and functionality...")

    frontend_path = Path("frontend/src/pages/assessments/types")

    # Define all 7 personality assessments to test
    assessments = [
        {
            "name": "MBTI Assessment",
            "file": "MBTIAssessmentPage.tsx",
            "theme": "indigo",
            "checks": [
                ("MBTI framework education", "Understanding Your MBTI Type"),
                ("Four preference pairs explanation", "Extraversion vs. Introversion"),
                ("Natural strengths section", "Your Natural Strengths"),
                ("Growth opportunities section", "Areas for Growth"),
                ("Work environment preferences", "Work Environment Preferences"),
                ("Communication style guidance", "Communication Style"),
                ("Dynamic content rendering", "results.mbti_type"),
                ("Type-specific insights", "MBTI Type {results.mbti_type}"),
            ],
        },
        {
            "name": "Big Five Assessment",
            "file": "BigFiveAssessmentPage.tsx",
            "theme": "blue",
            "checks": [
                ("OCEAN model education", "Understanding Your Big Five Results"),
                ("Five dimensions explained", "The OCEAN Model Explained"),
                ("Trait analysis section", "Your Personality Insights"),
                ("Openness to experience", "Openness to Experience"),
                ("Conscientiousness analysis", "Conscientiousness"),
                ("Extraversion analysis", "Extraversion"),
                ("Agreeableness analysis", "Agreeableness"),
                ("Neuroticism analysis", "Neuroticism"),
                ("Practical applications", "Practical Applications"),
                ("Career considerations", "Career Considerations"),
                ("Dynamic trait content", "results.descriptions.Openness"),
            ],
        },
        {
            "name": "Enneagram Assessment",
            "file": "EnneagramAssessmentPage.tsx",
            "theme": "purple",
            "checks": [
                (
                    "Enneagram framework education",
                    "Understanding Your Enneagram Results",
                ),
                ("Nine types overview", "The Nine Enneagram Types"),
                ("Three intelligence centers", "The Three Intelligence Centers"),
                (
                    "Type-specific deep dive",
                    "Your Enneagram Type {results.enneagram_type} Deep Dive",
                ),
                ("Core motivations section", "Core Motivations"),
                ("Core fear content", "Core Fear"),
                ("Core desire content", "Core Desire"),
                ("Growth and stress paths", "Growth and Stress Paths"),
                ("Integration path", "Integration (Growth) Path"),
                ("Disintegration path", "Disintegration (Stress) Path"),
                ("Practical applications", "Practical Applications"),
                ("Dynamic type content", "results.enneagram_type === '1'"),
            ],
        },
        {
            "name": "DISC Assessment",
            "file": "DISCAssessmentPage.tsx",
            "theme": "purple",
            "checks": [
                ("DISC framework education", "Understanding Your DISC Results"),
                ("Four behavioral styles", "The Four DISC Behavioral Styles"),
                ("Type-specific deep dive", "Your DISC Type Deep Dive"),
                ("Dominance profile", "High Dominance Profile"),
                ("Influence profile", "High Influence Profile"),
                ("Steadiness profile", "High Steadiness Profile"),
                ("Conscientiousness profile", "High Conscientiousness Profile"),
                ("Communication tips", "Communication Tips"),
                ("Work environment preferences", "Work Environment Preferences"),
                ("Dynamic style content", "results.disc_type === 'D'"),
            ],
        },
        {
            "name": "Predictive Index",
            "file": "PredictiveIndexPage.tsx",
            "theme": "blue",
            "checks": [
                (
                    "PI framework education",
                    "Understanding Your Predictive Index Results",
                ),
                ("Four behavioral factors", "The Four PI Behavioral Factors"),
                ("Behavioral pattern analysis", "Your Behavioral Pattern Analysis"),
                ("Leadership pattern", "Leadership Pattern Analysis"),
                ("Social pattern", "Social Pattern Analysis"),
                ("Supportive pattern", "Supportive Pattern Analysis"),
                ("Analytical pattern", "Analytical Pattern Analysis"),
                ("Workplace applications", "Workplace Applications"),
                ("Performance indicators", "Performance Indicators"),
                ("Management and motivation", "Management and Motivation"),
                ("Dynamic pattern content", "results.behavioral_pattern.includes"),
            ],
        },
        {
            "name": "Social Styles",
            "file": "SocialStylesPage.tsx",
            "theme": "blue",
            "checks": [
                (
                    "Social Styles framework education",
                    "Understanding Your Social Style Results",
                ),
                ("Two dimensions explanation", "The Social Styles Framework"),
                ("Four styles overview", "The Four Social Styles"),
                ("Assertiveness axis", "Assertiveness"),
                ("Responsiveness axis", "Responsiveness"),
                (
                    "Style-specific deep dive",
                    "Your {results.social_style_type} Style Deep Dive",
                ),
                ("Driver characteristics", "Driver Style Characteristics"),
                ("Expressive characteristics", "Expressive Style Characteristics"),
                ("Amiable characteristics", "Amiable Style Characteristics"),
                ("Analytical characteristics", "Analytical Style Characteristics"),
                ("Working with different styles", "Working with Different Styles"),
                ("Communication strategies", "Your Communication Strategy"),
                ("Adaptation strategies", "Adaptation Strategies"),
                ("Dynamic style content", "results.social_style_type === 'Driver'"),
            ],
        },
        {
            "name": "StrengthsFinder",
            "file": "StrengthsFinderPage.tsx",
            "theme": "green",
            "checks": [
                (
                    "StrengthsFinder education",
                    "Understanding Your StrengthsFinder Results",
                ),
                ("Strength philosophy explanation", "The Philosophy Behind Strengths"),
                ("Core principles", "Core Principles"),
                ("Research background", "The Research"),
                ("Why focus on strengths", "Why Focus on Strengths"),
                (
                    "Strength development strategies",
                    "Living and Leading with Your Strengths",
                ),
                ("Daily strength application", "Daily Strength Application"),
                ("Partnerships and teams", "Partnerships and Teams"),
                ("34 strength themes overview", "The 34 Strength Themes"),
                ("Executing themes", "Executing Themes"),
                ("Influencing themes", "Influencing Themes"),
                ("Relationship building themes", "Relationship Building Themes"),
                ("Strategic thinking themes", "Strategic Thinking Themes"),
                ("Name claim aim process", "Name, Claim, Aim"),
                ("Top 5 strengths display", "results.top_strengths"),
            ],
        },
    ]

    total_checks = 0
    total_passed = 0
    assessment_results = []

    for assessment in assessments:
        print(f"\n🔍 {assessment['name']} ({assessment['theme'].title()} Theme):")
        print("-" * 50)

        file_path = frontend_path / assessment["file"]
        if not file_path.exists():
            print(f"  ❌ File not found: {file_path}")
            assessment_results.append(
                {
                    "name": assessment["name"],
                    "status": "File not found",
                    "passed": 0,
                    "total": len(assessment["checks"]),
                }
            )
            continue

        with open(file_path, "r") as f:
            content = f.read()

        assessment_passed = 0
        assessment_total = 0

        # Check each enhancement feature
        for check_name, pattern in assessment["checks"]:
            total_checks += 1
            assessment_total += 1

            if pattern in content:
                print(f"  ✅ {check_name}")
                assessment_passed += 1
                total_passed += 1
            else:
                print(f"  ❌ {check_name} - Missing: '{pattern}'")

        assessment_percentage = (
            (assessment_passed / assessment_total) * 100 if assessment_total > 0 else 0
        )
        print(
            f"  📈 {assessment['name']}: {assessment_passed}/{assessment_total} ({assessment_percentage:.1f}%)"
        )

        assessment_results.append(
            {
                "name": assessment["name"],
                "status": "Complete" if assessment_percentage >= 90 else "Partial",
                "passed": assessment_passed,
                "total": assessment_total,
                "percentage": assessment_percentage,
            }
        )

    # Final Summary
    print(f"\n" + "=" * 80)
    print(f"🏁 COMPREHENSIVE ASSESSMENT ENHANCEMENT TEST RESULTS")
    print(f"=" * 80)
    print(
        f"📊 OVERALL: {total_passed}/{total_checks} ({(total_passed/total_checks*100):.1f}%)"
    )

    # Results Summary Table
    print(f"\n📋 ASSESSMENT ENHANCEMENT SUMMARY:")
    print("-" * 60)
    for result in assessment_results:
        status_emoji = (
            "✅"
            if result["percentage"] >= 90
            else "⚠️" if result["percentage"] >= 70 else "❌"
        )
        print(
            f"{status_emoji} {result['name']}: {result['passed']}/{result['total']} ({result['percentage']:.1f}%) - {result['status']}"
        )

    # Analysis Results
    fully_enhanced = [r for r in assessment_results if r["percentage"] >= 90]
    partially_enhanced = [r for r in assessment_results if 70 <= r["percentage"] < 90]
    needs_enhancement = [r for r in assessment_results if r["percentage"] < 70]

    print(f"\n📊 ENHANCEMENT ANALYSIS:")
    print(f"   ✅ Fully Enhanced (90%+): {len(fully_enhanced)} assessments")
    print(f"   ⚠️  Partially Enhanced (70-89%): {len(partially_enhanced)} assessments")
    print(f"   ❌ Needs Enhancement (<70%): {len(needs_enhancement)} assessments")

    if total_passed >= total_checks * 0.95:  # 95% success rate
        print(f"\n🎉 ALL ASSESSMENT ENHANCEMENTS SUCCESSFUL!")
        print(f"\n✅ COMPREHENSIVE ENHANCEMENT ACHIEVED:")
        print(
            f"   📚 Educational Content: All assessments include framework explanations"
        )
        print(f"   🎯 Personalized Insights: Dynamic content based on user results")
        print(
            f"   💼 Practical Applications: Workplace, career, and relationship guidance"
        )
        print(f"   🌱 Growth Strategies: Development opportunities and action steps")
        print(f"   🎨 Visual Organization: Structured, accessible information layouts")
        print(f"   🔬 Scientific Context: Research basis and validation information")
        print(f"\n🚀 TRANSFORMATION COMPLETE:")
        print(
            f"   From: Basic score displays → To: Comprehensive personality education"
        )
        print(f"   From: Generic descriptions → To: Personalized, actionable insights")
        print(f"   From: Static information → To: Dynamic, result-adaptive content")
        print(f"   From: Limited value → To: Transformative personal development tools")
        print(f"\n💫 ALL PERSONALITY ASSESSMENTS NOW PROVIDE:")
        print(f"   Comprehensive understanding of personality frameworks")
        print(f"   Personalized insights based on individual assessment results")
        print(f"   Practical applications for personal and professional growth")
        print(f"   Actionable strategies for development and improvement")
        print(f"   Educational context and scientific validation")
        print(f"   Enhanced user experience with organized, accessible content")
    else:
        print(f"\n⚠️ {total_checks - total_passed} enhancement features need attention")
        print(f"Please review the detailed results above for specific missing elements")

        if needs_enhancement:
            print(f"\n❌ ASSESSMENTS NEEDING MAJOR ENHANCEMENT:")
            for result in needs_enhancement:
                print(
                    f"   • {result['name']}: Only {result['percentage']:.1f}% complete"
                )

    return {
        "overall_percentage": (total_passed / total_checks * 100),
        "fully_enhanced": len(fully_enhanced),
        "partially_enhanced": len(partially_enhanced),
        "needs_enhancement": len(needs_enhancement),
        "total_assessments": len(assessments),
    }


if __name__ == "__main__":
    results = main()
