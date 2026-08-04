#!/usr/bin/env python3
"""
Direct unit tests for clinical screening algorithms
Tests scoring logic without HTTP/auth
"""

import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_phq9_scorer():
    """Test PHQ-9 scoring algorithm"""
    print("\n1. Testing PHQ-9 Scorer...")

    from app.services.clinical.scoring_algorithms import PHQ9Scorer

    scorer = PHQ9Scorer()

    # Test low risk (minimal symptoms)
    responses_low = {1: 1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0}

    result = scorer.score(responses_low)
    print(f"  Low risk test:")
    print(f"    Score: {result.total_score}")
    print(f"    Severity: {result.severity_level}")
    print(f"    Risk: {result.risk_level}")
    print(f"    Crisis Alert: {result.crisis_alert}")

    assert result.total_score == 6, f"Expected score 6, got {result.total_score}"
    assert (
        result.severity_level == "mild"
    ), f"Expected mild, got {result.severity_level}"
    assert result.risk_level == "low", f"Expected low, got {result.risk_level}"
    assert result.crisis_alert == False, "Expected no crisis alert"

    # Test crisis (suicide ideation)
    responses_crisis = {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 2}

    result = scorer.score(responses_crisis)
    print(f"\n  Crisis test:")
    print(f"    Score: {result.total_score}")
    print(f"    Severity: {result.severity_level}")
    print(f"    Risk: {result.risk_level}")
    print(f"    Crisis Alert: {result.crisis_alert}")

    assert result.total_score == 26, f"Expected score 26, got {result.total_score}"
    assert result.crisis_alert == True, "Expected crisis alert"
    assert "suicide" in str(result.risk_flags).lower(), "Expected suicide risk flag"

    print("  ✅ PHQ-9 scorer working correctly")
    return True


def test_gad7_scorer():
    """Test GAD-7 scoring algorithm"""
    print("\n2. Testing GAD-7 Scorer...")

    from app.services.clinical.scoring_algorithms import GAD7Scorer

    scorer = GAD7Scorer()

    # Test minimal anxiety
    responses_minimal = {1: 0, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 0}

    result = scorer.score(responses_minimal)
    print(f"  Minimal anxiety test:")
    print(f"    Score: {result.total_score}")
    print(f"    Severity: {result.severity_level}")
    print(f"    Risk: {result.risk_level}")

    assert result.total_score == 2, f"Expected score 2, got {result.total_score}"
    assert (
        result.severity_level == "minimal"
    ), f"Expected minimal, got {result.severity_level}"

    # Test severe anxiety
    responses_severe = {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3}

    result = scorer.score(responses_severe)
    print(f"\n  Severe anxiety test:")
    print(f"    Score: {result.total_score}")
    print(f"    Severity: {result.severity_level}")
    print(f"    Risk: {result.risk_level}")

    assert result.total_score == 21, f"Expected score 21, got {result.total_score}"
    assert (
        result.severity_level == "severe"
    ), f"Expected severe, got {result.severity_level}"

    print("  ✅ GAD-7 scorer working correctly")
    return True


def test_cssrs_scorer():
    """Test C-SSRS scoring algorithm"""
    print("\n3. Testing C-SSRS Scorer...")

    from app.services.clinical.scoring_algorithms import CSSRSScorer

    scorer = CSSRSScorer()

    # Test low risk (no ideation)
    responses_low = {
        "q1": False,
        "q2": False,
        "q3": False,
        "q4": False,
        "q5": False,
        "q11": False,
        "q12": False,
        "q13": False,
    }

    result = scorer.score(responses_low)
    print(f"  Low risk test:")
    print(f"    Risk Level: {result.risk_level}")
    print(f"    Crisis Alert: {result.crisis_alert}")

    assert result.risk_level == "low", f"Expected low, got {result.risk_level}"
    assert result.crisis_alert == False, "Expected no crisis alert"

    # Test critical risk (recent attempt)
    responses_critical = {
        "q1": True,
        "q2": True,
        "q3": True,
        "q4": True,
        "q5": True,
        "q11": True,  # CRITICAL: Recent attempt
        "q12": True,
        "q13": False,
    }

    result = scorer.score(responses_critical)
    print(f"\n  Critical risk test:")
    print(f"    Risk Level: {result.risk_level}")
    print(f"    Crisis Alert: {result.crisis_alert}")
    print(f"    Risk Flags: {result.risk_flags}")

    assert (
        result.risk_level == "critical"
    ), f"Expected critical, got {result.risk_level}"
    assert result.crisis_alert == True, "Expected crisis alert"

    print("  ✅ C-SSRS scorer working correctly")
    return True


def test_database_schema():
    """Test database models are accessible"""
    print("\n4. Testing Database Models...")

    from app.db.models.clinical_screening import (
        ClinicalAlert,
        ClinicalAuditLog,
        ClinicalConsent,
        ClinicalReferral,
        ClinicalScreening,
    )

    print(f"  ✅ ClinicalScreening: {ClinicalScreening.__name__}")
    print(f"  ✅ ClinicalAlert: {ClinicalAlert.__name__}")
    print(f"  ✅ ClinicalReferral: {ClinicalReferral.__name__}")
    print(f"  ✅ ClinicalAuditLog: {ClinicalAuditLog.__name__}")
    print(f"  ✅ ClinicalConsent: {ClinicalConsent.__name__}")

    return True


def test_schemas():
    """Test Pydantic schemas"""
    print("\n5. Testing Pydantic Schemas...")

    from datetime import datetime
    from uuid import uuid4

    from app.schemas.clinical import (
        CSSRSRequest,
        GAD7Request,
        PHQ9Request,
        ScreeningResponse,
    )

    # Test PHQ9Request
    phq9_data = {
        "q1_interest": 2,
        "q2_depressed": 1,
        "q3_sleep": 2,
        "q4_energy": 1,
        "q5_appetite": 0,
        "q6_self_worth": 1,
        "q7_concentration": 2,
        "q8_motor": 1,
        "q9_suicide": 0,
    }
    phq9 = PHQ9Request(**phq9_data)
    print(f"  ✅ PHQ9Request validated")

    # Test GAD7Request
    gad7_data = {
        "q1_nervous": 2,
        "q2_control_worry": 2,
        "q3_worry_too_much": 2,
        "q4_trouble_relaxing": 1,
        "q5_restless": 1,
        "q6_irritable": 1,
        "q7_afraid": 0,
    }
    gad7 = GAD7Request(**gad7_data)
    print(f"  ✅ GAD7Request validated")

    # Test CSSRSRequest
    cssrs_data = {
        "q1_wish_dead": False,
        "q2_nonspecific_thoughts": False,
        "q3_active_ideation": False,
        "q4_intent": False,
        "q5_plan": False,
        "q11_actual_attempt": False,
        "q12_preparatory_acts": False,
        "q13_aborted_attempt": False,
    }
    cssrs = CSSRSRequest(**cssrs_data)
    print(f"  ✅ CSSRSRequest validated")

    # Test ScreeningResponse
    response_data = {
        "id": uuid4(),
        "screening_type": "PHQ9",
        "total_score": 12.0,
        "severity_level": "moderate",
        "risk_level": "moderate",
        "interpretation": "Moderate depression",
        "recommendations": ["Seek help"],
        "crisis_alert": False,
        "risk_flags": [],
        "completed_at": datetime.now(),
    }
    response = ScreeningResponse(**response_data)
    print(f"  ✅ ScreeningResponse validated")

    return True


def main():
    print("=" * 60)
    print("Clinical Screening Core Tests")
    print("=" * 60)

    tests = [
        ("PHQ-9 Scorer", test_phq9_scorer),
        ("GAD-7 Scorer", test_gad7_scorer),
        ("C-SSRS Scorer", test_cssrs_scorer),
        ("Database Models", test_database_schema),
        ("Pydantic Schemas", test_schemas),
    ]

    results = {}
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")
            import traceback

            traceback.print_exc()
            results[name] = False

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    all_ok = all(results.values())

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All core tests passed!")
        print("\nThe clinical screening system is ready for integration testing.")
    else:
        print("⚠️ Some tests failed.")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
