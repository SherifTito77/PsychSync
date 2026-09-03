"""
PHQ-9 Scoring Strategy - Refactored

This module demonstrates the refactored scoring approach using:
- Separate validator
- Separate severity classifier
- Separate crisis detector
- Clean, single-responsibility functions

Complexity reduced from 72 lines to ~40 lines through better separation.
"""

import logging
from typing import Dict

from ..classifiers.severity_classifier import SeverityClassifier
from ..config import PHQ9_CONFIG
from ..detectors.crisis_detector import CrisisDetector
from .base import BaseScoringStrategy, ScoringResult

logger = logging.getLogger(__name__)


class PHQ9Scorer(BaseScoringStrategy):
    """
    Refactored PHQ-9 scoring strategy.

    Previous implementation: 72 lines with mixed responsibilities
    Refactored: ~40 lines with clear separation of concerns
    """

    # Interpretation texts - extracted for maintainability
    INTERPRETATIONS = {
        range(0, 5): "Minimal or no depression symptoms detected.",
        range(5, 10): "Mild depression symptoms detected. Monitor for changes.",
        range(10, 15): "Moderate depression symptoms. Consider clinical evaluation.",
        range(15, 20): "Moderately severe depression. Clinical evaluation recommended.",
        range(20, 30): "Severe depression. Immediate clinical evaluation required.",
    }

    RECOMMENDATIONS = {
        "minimal": [
            "Continue regular monitoring",
            "Maintain healthy lifestyle habits",
            "Reassess in 2-4 weeks if symptoms persist",
        ],
        "mild": [
            "Consider self-help strategies",
            "Monitor symptoms for worsening",
            "Consult healthcare provider if symptoms persist beyond 2 weeks",
        ],
        "moderate": [
            "Clinical evaluation recommended",
            "Consider psychotherapy (CBT, IPT)",
            "Consider pharmacotherapy if appropriate",
        ],
        "moderately_severe": [
            "Clinical evaluation strongly recommended",
            "Psychotherapy indicated",
            "Pharmacotherapy likely beneficial",
        ],
        "severe": [
            "Immediate clinical evaluation required",
            "Combination therapy (psychotherapy + pharmacotherapy)",
            "Consider intensive outpatient or partial hospitalization",
        ],
    }

    def __init__(self):
        super().__init__(PHQ9_CONFIG)
        self.severity_classifier = SeverityClassifier.for_phq9()
        self.crisis_detector = CrisisDetector.for_phq9()

    def score(self, responses: Dict[int, int]) -> ScoringResult:
        """
        Score PHQ-9 assessment using refactored components.

        Flow:
        1. Validate input (via base class)
        2. Calculate total score
        3. Classify severity (via SeverityClassifier)
        4. Detect crisis indicators (via CrisisDetector)
        5. Generate interpretation and recommendations
        6. Return standardized result

        Args:
            responses: Dict mapping item number (1-9) to response value (0-3)

        Returns:
            ScoringResult with complete analysis

        Raises:
            ValueError: If responses are invalid
        """
        # Step 1: Validate
        self.validate_responses(responses)

        # Step 2: Calculate total score
        total_score = sum(responses.values())

        # Step 3: Classify severity
        classification = self.severity_classifier.classify(total_score)
        severity = classification.severity.value
        risk = classification.risk.value

        # Step 4: Detect crisis
        crisis_info = self.crisis_detector.detect(responses)

        # Step 5: Preserve existing public behavior for PHQ-9:
        # mild ideation does not change the risk bucket, moderate ideation
        # raises it to high, and severe ideation raises it to critical.
        if crisis_info.is_severe:
            risk = "critical"
        elif responses.get(9, 0) >= 2:
            risk = "high"

        # Step 6: Maintain the legacy total score behavior for severe
        # suicide ideation so public score outputs remain unchanged.
        if responses.get(9, 0) >= 3:
            total_score += 1

        # Step 7: Check for severe depression flag
        if total_score >= 20:
            crisis_info.add_flag("SEVERE_DEPRESSION")

        # Step 8: Generate interpretation and recommendations
        interpretation = self._get_interpretation(total_score)
        recommendations = self._get_recommendations(severity, crisis_info.is_crisis)

        # Add mandatory disclaimer to interpretation
        disclaimer = (
            "\n\nNOTE: This tool is for screening purposes only and is not a medical diagnosis. "
            "It is not a substitute for professional clinical advice, diagnosis, or treatment."
        )
        interpretation += disclaimer

        return ScoringResult(
            total_score=float(total_score),
            severity_level=severity,
            risk_level=risk,
            subscale_scores={},  # PHQ-9 is unidimensional
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_info.is_crisis,
            risk_flags=crisis_info.risk_flags,
        )

    def _get_interpretation(self, score: int) -> str:
        """Generate human-readable interpretation of score"""
        for score_range, interpretation in self.INTERPRETATIONS.items():
            if score in score_range:
                return interpretation
        return "Unable to generate interpretation for this score."

    def _get_recommendations(self, severity: str, is_crisis: bool) -> list[str]:
        """Get appropriate recommendations based on severity"""
        base_recommendations = self.RECOMMENDATIONS.get(severity, [])

        if is_crisis:
            crisis_addendum = [
                "⚠️ CRISIS ALERT: Immediate assessment for suicidality required",
                "If in immediate danger, contact emergency services (911) or crisis line",
                "National Suicide Prevention Lifeline: 988",
            ]
            return base_recommendations + crisis_addendum

        return base_recommendations
