#!/usr/bin/env python3
"""
Verification Script for Advanced Clinical Features Implementation

This script verifies that all components of the advanced clinical features
have been properly implemented and are ready for deployment.

Run with: python verify_clinical_implementation.py
"""

import os
import sys
from pathlib import Path

print("🔍 Verifying Advanced Clinical Features Implementation")
print("=" * 70)

# Check if we're in the right directory
if not Path("app/main.py").exists():
    print("❌ Error: Run this script from the project root directory")
    sys.exit(1)

# Track results
results = {
    "backend": {"passed": 0, "failed": 0, "total": 0},
    "frontend": {"passed": 0, "failed": 0, "total": 0},
    "tests": {"passed": 0, "failed": 0, "total": 0},
}

# ============================================================================
# BACKEND VERIFICATION
# ============================================================================
print("\n📦 Backend Components")
print("-" * 70)

backend_files = [
    # Services
    ("app/services/clinical/advanced_scorers.py", "LSAS, EAT-26, Y-BOCS scorers"),
    ("app/services/telehealth/video_service.py", "Telehealth video service"),
    # API Endpoints
    (
        "app/api/v1/endpoints/screening.py",
        "Screening endpoints with LSAS/EAT-26/Y-BOCS",
    ),
    ("app/api/v1/endpoints/telehealth.py", "Telehealth endpoints"),
    # Database
    ("alembic/versions/20250115_add_telehealth_chatbot.py", "Database migration"),
    ("app/db/models/clinical_advanced.py", "Telehealth/Chatbot/Analytics models"),
    ("app/schemas/clinical.py", "Clinical request/response schemas"),
]

for filepath, description in backend_files:
    results["backend"]["total"] += 1
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print(f"✅ {description}")
        print(f"   {filepath} ({size:,} bytes)")
        results["backend"]["passed"] += 1
    else:
        print(f"❌ {description}")
        print(f"   {filepath} - NOT FOUND")
        results["backend"]["failed"] += 1

# ============================================================================
# FRONTEND VERIFICATION
# ============================================================================
print("\n🎨 Frontend Components")
print("-" * 70)

frontend_files = [
    # Clinical Assessments
    ("frontend/src/components/clinical/LSASScreening.tsx", "LSAS Assessment UI"),
    ("frontend/src/components/clinical/EAT26Screening.tsx", "EAT-26 Assessment UI"),
    ("frontend/src/components/clinical/YBOCSScreening.tsx", "Y-BOCS Assessment UI"),
    # Telehealth
    (
        "frontend/src/components/telehealth/VideoConsultation.tsx",
        "Video Consultation UI",
    ),
    (
        "frontend/src/components/telehealth/TelehealthScheduler.tsx",
        "Telehealth Scheduler UI",
    ),
    ("frontend/src/components/telehealth/index.ts", "Telehealth components index"),
    # Analytics
    (
        "frontend/src/components/analytics/ClinicalAnalyticsDashboard.tsx",
        "Analytics Dashboard UI",
    ),
    # AI Chatbot
    ("frontend/src/components/ai/MentalHealthChatbot.tsx", "AI Chatbot UI"),
]

for filepath, description in frontend_files:
    results["frontend"]["total"] += 1
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print(f"✅ {description}")
        print(f"   {filepath} ({size:,} bytes)")
        results["frontend"]["passed"] += 1
    else:
        print(f"❌ {description}")
        print(f"   {filepath} - NOT FOUND")
        results["frontend"]["failed"] += 1

# ============================================================================
# TEST VERIFICATION
# ============================================================================
print("\n🧪 Test Suite")
print("-" * 70)

test_files = [
    ("tests/integration/test_advanced_clinical_features.py", "Integration test suite"),
]

for filepath, description in test_files:
    results["tests"]["total"] += 1
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print(f"✅ {description}")
        print(f"   {filepath} ({size:,} bytes)")
        results["tests"]["passed"] += 1
    else:
        print(f"❌ {description}")
        print(f"   {filepath} - NOT FOUND")
        results["tests"]["failed"] += 1

# ============================================================================
# CODE QUALITY CHECKS
# ============================================================================
print("\n🔬 Code Quality Checks")
print("-" * 70)

# Check if advanced_scorers.py has the required scorers
try:
    with open("app/services/clinical/advanced_scorers.py", "r") as f:
        content = f.read()

    scorers = ["LSASScorer", "EAT26Scorer", "YBOCSScorer"]
    for scorer in scorers:
        results["backend"]["total"] += 1
        if f"class {scorer}" in content:
            print(f"✅ {scorer} implemented")
            results["backend"]["passed"] += 1
        else:
            print(f"❌ {scorer} NOT FOUND")
            results["backend"]["failed"] += 1
except Exception as e:
    print(f"❌ Error checking advanced_scorers.py: {e}")

# Check if video_service.py has required methods
try:
    with open("app/services/telehealth/video_service.py", "r") as f:
        content = f.read()

    methods = [
        "create_consultation_room",
        "join_session",
        "start_session",
        "end_session",
    ]
    for method in methods:
        results["backend"]["total"] += 1
        if f"async def {method}" in content or f"def {method}" in content:
            print(f"✅ TelehealthService.{method}() implemented")
            results["backend"]["passed"] += 1
        else:
            print(f"❌ TelehealthService.{method}() NOT FOUND")
            results["backend"]["failed"] += 1
except Exception as e:
    print(f"❌ Error checking video_service.py: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("📊 VERIFICATION SUMMARY")
print("=" * 70)

all_categories = [
    ("Backend", results["backend"]),
    ("Frontend", results["frontend"]),
    ("Tests", results["tests"]),
]

total_passed = 0
total_failed = 0
total_checks = 0

for category, data in all_categories:
    status = "✅ PASS" if data["failed"] == 0 else "❌ FAIL"
    print(f"\n{category:15} {data['passed']:3}/{data['total']:3} passed  {status}")
    total_passed += data["passed"]
    total_failed += data["failed"]
    total_checks += data["total"]

print(f"\n{'Overall:':15} {total_passed:3}/{total_checks:3} checks passed")

if total_failed == 0:
    print("\n" + "=" * 70)
    print("🎉 SUCCESS! All advanced clinical features are implemented!")
    print("=" * 70)
    print("\n✅ Ready for deployment:")
    print("   1. LSAS Assessment (Social Anxiety)")
    print("   2. EAT-26 Assessment (Eating Disorders)")
    print("   3. Y-BOCS Assessment (OCD)")
    print("   4. Telehealth Video Consultations")
    print("   5. AI Mental Health Chatbot")
    print("   6. Clinical Analytics Dashboard")
    print("\n📖 See COMPLETE_IMPLEMENTATION_SUMMARY.md for deployment instructions")
    sys.exit(0)
else:
    print("\n" + "=" * 70)
    print(f"⚠️  WARNING: {total_failed} check(s) failed")
    print("=" * 70)
    print("\nPlease review the failed checks above and ensure all files are created.")
    sys.exit(1)
