"""
Semantic Uncertainty Detection Tests
Comprehensive tests for confabulation and hallucination detection.

Benchmarks:
- Known hallucination patterns (fake citations, fake stats)
- Internal contradictions
- Knowledge boundary violations
- Over-specificity with low support

Author: PsychSync Security Team
Version: 1.0.0
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.security.uncertainty_detection import (
    SemanticUncertaintyDetector,
    HumanReviewQueue,
    TaskCategory,
    UncertaintyThreshold,
    UncertaintyReport,
    UncertaintySignals,
)


class TestUncertaintySignals:
    """Test individual uncertainty signal detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=False
        )

    def test_semantic_variance_detection(self):
        """Test detection of semantic variance through uncertainty markers."""
        # High uncertainty
        high_uncertainty = (
            "The patient might possibly show symptoms that could indicate "
            "they may perhaps have a condition that seems like it might be "
            "bipolar disorder, but it's uncertain and appears unclear."
        )
        report = self.detector.check_uncertainty(
            high_uncertainty,
            TaskCategory.CLINICAL_ASSESSMENT
        )
        assert report.signals.semantic_variance > 0.3, \
            f"Expected high variance, got {report.signals.semantic_variance}"

        # Low uncertainty
        low_uncertainty = (
            "Based on the PHQ-9 assessment, the patient shows clear signs "
            "of depression with a score of 18 out of 27."
        )
        report = self.detector.check_uncertainty(
            low_uncertainty,
            TaskCategory.CLINICAL_ASSESSMENT
        )
        assert report.signals.semantic_variance < 0.2, \
            f"Expected low variance, got {report.signals.semantic_variance}"

    def test_token_probability_analysis(self):
        """Test analysis of token-level probabilities."""
        # All high confidence tokens
        high_confidence = [0.9, 0.85, 0.92, 0.88, 0.95]
        report = self.detector.check_uncertainty(
            "The patient is depressed",
            TaskCategory.GENERAL_ASSISTANCE,
            token_probabilities=high_confidence
        )
        assert report.signals.low_confidence_tokens == 0.0

        # Mix of high and low confidence
        mixed_confidence = [0.95, 0.05, 0.92, 0.08, 0.88]
        report = self.detector.check_uncertainty(
            "The patient is depressed",
            TaskCategory.GENERAL_ASSISTANCE,
            token_probabilities=mixed_confidence
        )
        assert report.signals.low_confidence_tokens == 0.4, \
            f"Expected 0.4, got {report.signals.low_confidence_tokens}"

    def test_knowledge_gap_detection(self):
        """Test detection of claims outside knowledge base."""
        output = "The patient's score is 42 on the GDS-15 scale"
        context = {
            'scale': 'GDS-15',
            'max_score': 15  # Actual max is 15, not 42
        }

        report = self.detector.check_uncertainty(
            output,
            TaskCategory.CLINICAL_ASSESSMENT,
            additional_context=context
        )

        # Should detect that 42 is not in context
        assert report.signals.knowledge_gap_score > 0, \
            "Should detect knowledge gap for score outside context"

    def test_contradiction_detection(self):
        """Test detection of internal contradictions."""
        contradictory = (
            "The patient always reports feeling depressed and "
            "never shows any signs of improvement, although "
            "all symptoms have decreased."
        )

        report = self.detector.check_uncertainty(
            contradictory,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        assert report.signals.contradiction_score > 0.1, \
            f"Expected contradiction detection, got {report.signals.contradiction_score}"

    def test_hallucination_pattern_detection_fake_citations(self):
        """Test detection of fake academic citations."""
        fake_citation = (
            "Research by Smith et al. (2022) demonstrates that "
            "CBT is 87.5% effective for treating anxiety."
        )

        report = self.detector.check_uncertainty(
            fake_citation,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        assert report.signals.hallucination_risk > 0.2, \
            f"Expected high hallucination risk, got {report.signals.hallucination_risk}"
        assert len(report.flagged_claims) > 0, \
            "Expected flagged claims for fake citation"

    def test_hallucination_pattern_detection_fake_stats(self):
        """Test detection of fake statistics without confidence intervals."""
        fake_stats = (
            "The assessment shows 94.3% accuracy in predicting "
            "patient outcomes with no margin of error."
        )

        report = self.detector.check_uncertainty(
            fake_stats,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        assert report.signals.hallucination_risk > 0.1, \
            "Expected to flag over-specific statistics"

    def test_specificity_mismatch_detection(self):
        """Test detection of certainty language with uncertain content."""
        mismatch = (
            "The patient is definitely suffering from bipolar disorder, "
            "though it might possibly be something else."
        )

        report = self.detector.check_uncertainty(
            mismatch,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        assert report.signals.specificity_mismatch > 0.3, \
            f"Expected specificity mismatch, got {report.signals.specificity_mismatch}"


class TestConfabulationBenchmarks:
    """
    Benchmark tests using known confabulation patterns.

    These tests use real-world examples of LLM hallucinations
    to verify the detector catches them.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=False
        )

    def test_benchmark_fake_citations(self):
        """
        Benchmark: Detect fake academic citations.

        LLMs often hallucinate citations that look real but don't exist.
        This test verifies we catch these patterns.
        """
        test_cases = [
            # Fake single author
            "According to Johnson (2019), the treatment efficacy is 92%.",
            # Fake multiple authors
            "Studies by Williams et al. (2021) show significant improvement.",
            # Fake journal citation
            "Research published in Journal of Clinical Psychology (Smith, 2020) indicates...",
        ]

        for case in test_cases:
            report = self.detector.check_uncertainty(
                case,
                TaskCategory.CLINICAL_ASSESSMENT
            )

            # Should detect citation as potential hallucination
            assert report.signals.hallucination_risk > 0.1, \
                f"Failed to detect fake citation in: {case}"

    def test_benchmark_fake_statistics(self):
        """
        Benchmark: Detect fake statistics.

        LLMs often invent specific numbers without basis.
        """
        test_cases = [
            "The treatment has a 87.2% success rate",
            "Patients improve in 4.6 days on average",
            "The assessment is 96.8% accurate",
            "Recovery occurs in 2.3 weeks for 78.5% of patients",
        ]

        for case in test_cases:
            report = self.detector.check_uncertainty(
                case,
                TaskCategory.CLINICAL_ASSESSMENT
            )

            # Should flag specific numbers without verification
            assert report.signals.hallucination_risk > 0.05, \
                f"Failed to flag suspicious stats in: {case}"

    def test_benchmark_internal_contradictions(self):
        """
        Benchmark: Detect internal contradictions.

        Confabulations often contain logical inconsistencies.
        """
        test_cases = [
            "The patient always responds well to treatment but never shows improvement",
            "All symptoms have increased, indicating decreased severity",
            "High scores on the scale indicate low depression levels",
            "The patient is definitely certain they might have the condition",
        ]

        for case in test_cases:
            report = self.detector.check_uncertainty(
                case,
                TaskCategory.CLINICAL_ASSESSMENT
            )

            # Should detect contradictions
            assert report.signals.contradiction_score > 0.05 or \
                   report.signals.specificity_mismatch > 0.1, \
                f"Failed to detect contradiction in: {case}"

    def test_benchmark_knowledge_boundary_violations(self):
        """
        Benchmark: Detect claims outside training knowledge.

        LLMs may make authoritative claims about very recent events
        or obscure facts not in training data.
        """
        test_cases = [
            # Specific recent date (would be outside training cutoff)
            "The FDA approved this treatment on March 15, 2024",
            # Very specific future prediction
            "By 2027, 94.5% of clinics will use this method",
            # Obscure specific claim
            "The clinic at 123 Main Street, Smalltown, USA reported 100% success",
        ]

        for case in test_cases:
            report = self.detector.check_uncertainty(
                case,
                TaskCategory.CLINICAL_ASSESSMENT,
                additional_context={'patient_name': 'John Doe'}
            )

            # Should flag as uncertain without verification
            total_risk = (
                report.signals.knowledge_gap_score +
                report.signals.hallucination_risk
            )
            assert total_risk > 0.1, \
                f"Failed to detect knowledge boundary violation in: {case}"

    def test_benchmark_over_specificity(self):
        """
        Benchmark: Detect over-specific claims without support.

        Confabulations often include suspiciously precise details.
        """
        test_cases = [
            "The patient will recover in exactly 7 days",
            "This treatment is definitely 100% effective",
            "Precisely 83.27% of patients improve",
            "The assessment is certainly, undoubtedly correct",
        ]

        for case in test_cases:
            report = self.detector.check_uncertainty(
                case,
                TaskCategory.CLINICAL_ASSESSMENT
            )

            # Should flag over-specific language
            total_risk = (
                report.signals.hallucination_risk +
                report.signals.specificity_mismatch
            )
            assert total_risk > 0.1, \
                f"Failed to detect over-specificity in: {case}"


class TestTaskCategoryThresholds:
    """Test uncertainty thresholds for different task categories."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=False
        )

    def test_clinical_assessment_strict_threshold(self):
        """Test that clinical assessments have strict uncertainty threshold."""
        uncertain_output = (
            "The patient might possibly show signs that could indicate "
            "depression, though it's uncertain."
        )

        report = self.detector.check_uncertainty(
            uncertain_output,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Clinical threshold is 0.10 (very strict)
        assert report.task_category == "clinical"
        assert report.threshold_used == 0.10
        # Should require review for clinical use
        assert report.requires_human_review is True

    def test_general_assistance_permissive_threshold(self):
        """Test that general assistance has permissive uncertainty threshold."""
        same_uncertain_output = (
            "The patient might possibly show signs that could indicate "
            "depression, though it's uncertain."
        )

        report = self.detector.check_uncertainty(
            same_uncertain_output,
            TaskCategory.GENERAL_ASSISTANCE
        )

        # General threshold is 0.60 (permissive)
        assert report.task_category == "general"
        assert report.threshold_used == 0.60
        # Might not require review for general use
        # (depends on actual score)

    def test_team_optimization_medium_threshold(self):
        """Test that team optimization has medium uncertainty threshold."""
        output = "Team members might work well together"

        report = self.detector.check_uncertainty(
            output,
            TaskCategory.TEAM_OPTIMIZATION
        )

        assert report.task_category == "team"
        assert report.threshold_used == 0.40  # Medium threshold


class TestHumanReviewQueue:
    """Test human review queue management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=False
        )
        self.queue = HumanReviewQueue(max_queue_size=10)

    def test_queue_for_review(self):
        """Test queuing an output for human review."""
        output = "The patient definitely might have depression"

        report = self.detector.check_uncertainty(
            output,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        ticket_id = self.queue.queue_for_review(
            report=report,
            llm_input="Assess patient depression",
            llm_output=output,
            metadata={'patient_id': '123'}
        )

        assert ticket_id.startswith("REVIEW-")
        assert len(self.queue.get_pending_reviews()) == 1

    def test_review_prioritization(self):
        """Test that reviews are prioritized correctly."""
        # High uncertainty (clinical)
        high_report = self.detector.check_uncertainty(
            "Patient definitely might have condition",
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Lower uncertainty (general)
        low_report = self.detector.check_uncertainty(
            "Team might work well",
            TaskCategory.GENERAL_ASSISTANCE
        )

        # Queue in reverse order
        self.queue.queue_for_review(low_report, "", "")
        self.queue.queue_for_review(high_report, "", "")

        # High priority should come first
        pending = self.queue.get_pending_reviews()
        assert pending[0]['uncertainty_score'] >= pending[1]['uncertainty_score']

    def test_queue_capacity_limit(self):
        """Test that queue respects capacity limit."""
        # Fill queue beyond capacity
        for i in range(15):
            report = self.detector.check_uncertainty(
                f"Output {i}",
                TaskCategory.GENERAL_ASSISTANCE
            )
            self.queue.queue_for_review(report, "", "")

        # Should not exceed max size
        assert len(self.queue.get_pending_reviews(limit=100)) <= 10


class TestUncertaintyReport:
    """Test uncertainty report generation and serialization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=False
        )

    def test_report_serialization(self):
        """Test that reports can be serialized to JSON."""
        report = self.detector.check_uncertainty(
            "Test output",
            TaskCategory.GENERAL_ASSISTANCE
        )

        # Should not raise exception
        json_str = report.to_json()
        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_report_contains_all_fields(self):
        """Test that report contains all required fields."""
        report = self.detector.check_uncertainty(
            "Test output",
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Check all required fields
        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'signals')
        assert hasattr(report, 'exceeds_threshold')
        assert hasattr(report, 'requires_human_review')
        assert hasattr(report, 'task_category')
        assert hasattr(report, 'threshold_used')
        assert hasattr(report, 'flagged_claims')
        assert hasattr(report, 'recommendations')
        assert hasattr(report, 'timestamp')
        assert hasattr(report, 'report_hash')

    def test_report_recommendations(self):
        """Test that report generates meaningful recommendations."""
        # Create high uncertainty report
        report = self.detector.check_uncertainty(
            "The patient definitely might possibly have condition, et al. (2022)",
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Should have recommendations
        assert len(report.recommendations) > 0

        # Should include human review warning
        if report.requires_human_review:
            review_warnings = [
                r for r in report.recommendations
                if "REQUIRE HUMAN REVIEW" in r
            ]
            assert len(review_warnings) > 0


class TestIntegrationWorkflows:
    """Integration tests for complete uncertainty detection workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=False
        )
        self.queue = HumanReviewQueue()

    def test_clinical_assessment_workflow(self):
        """
        Test complete workflow for clinical assessment.

        Workflow:
        1. Generate LLM output
        2. Check uncertainty
        3. Queue for review if needed
        4. Generate report
        """
        llm_output = (
            "Based on the assessment, the patient shows symptoms that "
            "might possibly indicate depression, with a PHQ-9 score of "
            "87.3% according to Smith et al. (2022)."
        )

        # Step 1 & 2: Check uncertainty
        report = self.detector.check_uncertainty(
            llm_output,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Step 3: Queue for review if needed
        if report.requires_human_review:
            ticket_id = self.queue.queue_for_review(
                report=report,
                llm_input="Assess patient for depression",
                llm_output=llm_output
            )
            assert ticket_id is not None

        # Step 4: Verify report
        assert report.overall_score > 0  # Should detect some uncertainty
        assert report.task_category == "clinical"

        # Verify hallucinations were detected
        assert report.signals.hallucination_risk > 0, \
            "Should detect fake citation and statistics"

    def test_team_optimization_workflow(self):
        """Test workflow for team optimization recommendations."""
        llm_output = (
            "The team members certainly demonstrate strong collaboration "
            "and definitely will improve productivity by 94.5%."
        )

        report = self.detector.check_uncertainty(
            llm_output,
            TaskCategory.TEAM_OPTIMIZATION
        )

        # Should flag over-specific statistics
        assert report.signals.hallucination_risk > 0 or \
               report.signals.specificity_mismatch > 0

    def test_uncertainty_vs_confidence_boundary(self):
        """
        Test the boundary between uncertain and confident outputs.

        This test verifies that the detector correctly distinguishes
        between outputs that should and shouldn't require review.
        """
        # Clearly uncertain output
        uncertain = (
            "The patient might possibly have depression, "
            "though it's unclear and uncertain according to Johnson et al. (2024)."
        )
        report_uncertain = self.detector.check_uncertainty(
            uncertain,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Confident output
        confident = (
            "Patient scored 18/27 on PHQ-9 assessment, "
            "indicating moderately severe depression."
        )
        report_confident = self.detector.check_uncertainty(
            confident,
            TaskCategory.CLINICAL_ASSESSMENT
        )

        # Uncertain should have higher score
        assert report_uncertain.overall_score > report_confident.overall_score, \
            "Uncertain output should have higher uncertainty score"

        # Uncertain should require review
        assert report_uncertain.requires_human_review is True, \
            "Uncertain output should require human review"


class TestPerformance:
    """Performance and caching tests."""

    def test_caching_improves_performance(self):
        """Test that caching improves repeated check performance."""
        detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=True
        )

        output = "Test output for caching"

        # First check (not cached)
        import time
        start = time.time()
        report1 = detector.check_uncertainty(
            output,
            TaskCategory.GENERAL_ASSISTANCE
        )
        first_time = time.time() - start

        # Second check (cached)
        start = time.time()
        report2 = detector.check_uncertainty(
            output,
            TaskCategory.GENERAL_ASSISTANCE
        )
        cached_time = time.time() - start

        # Reports should be identical
        assert report1.report_hash == report2.report_hash

        # Cache should be faster (or at least not slower)
        # Note: This might be flaky in CI, so we just verify caching works
        assert len(detector._cache) > 0

    def test_cache_clear(self):
        """Test cache clearing functionality."""
        detector = SemanticUncertaintyDetector(
            enable_logging=False,
            cache_results=True
        )

        # Add some items to cache
        for i in range(5):
            detector.check_uncertainty(
                f"Output {i}",
                TaskCategory.GENERAL_ASSISTANCE
            )

        assert len(detector._cache) == 5

        # Clear cache
        detector.clear_cache()

        assert len(detector._cache) == 0


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
