import pytest

from app.ai.security.uncertainty_detection import (
    SemanticUncertaintyDetector,
    TaskCategory,
)


@pytest.fixture
def detector():
    return SemanticUncertaintyDetector()


def test_heuristic_pattern_checks(detector):
    # Test semantic inconsistency heuristic
    output = "The patient might have a condition, but it is uncertain."
    report = detector.check_uncertainty(output, TaskCategory.GENERAL_ASSISTANCE)
    assert report.signals.estimated_semantic_inconsistency > 0

    # Test contradiction heuristic
    output = "The patient always has symptoms. The patient never has symptoms."
    report = detector.check_uncertainty(output, TaskCategory.GENERAL_ASSISTANCE)
    assert report.signals.contradiction_heuristic > 0


def test_heuristic_performance_boundary(detector):
    # Test for potential false positives (too many markers)
    clean_output = "The patient shows clear signs of improvement."
    report = detector.check_uncertainty(clean_output, TaskCategory.GENERAL_ASSISTANCE)
    assert report.overall_score < 0.2

    # Test for potential false negatives (too specific/confident)
    uncertain_output = "The patient has exactly 45.2% chance of recovery."
    report = detector.check_uncertainty(
        uncertain_output, TaskCategory.GENERAL_ASSISTANCE
    )
    assert report.signals.specificity_mismatch_heuristic > 0
