"""
GAD-7 Scoring Strategy - Refactored

This module implements the Generalized Anxiety Disorder-7 assessment scoring.
Uses the same refactored architecture as PHQ9Scorer for consistency.

GAD-7 assesses anxiety symptoms over the past 2 weeks.
No suicide/crisis item, but severe anxiety may require clinical attention.
"""

from typing import Dict
import logging
from .base import BaseScoringStrategy, ScoringResult
from ..config import GAD7_CONFIG
from ..classifiers.severity_classifier import SeverityClassifier
from ..detectors.crisis_detector import CrisisDetector

logger = logging.getLogger(__name__)


class GAD7Scorer(BaseScoringStrategy):
    """
    Refactored GAD-7 scoring strategy.

    GAD-7 (Generalized Anxiety Disorder-7 Item Scale)
    Assesses anxiety symptoms across 7 items.

    Previous implementation: ~65 lines with mixed responsibilities
    Refactored: ~45 lines with clear separation of concerns
    """

    # Interpretation texts - anxiety-focused
    INTERPRETATIONS = {
        range(0, 5): "Minimal or no anxiety symptoms detected.",
        range(5, 10): "Mild anxiety symptoms detected. Monitor for changes.",
        range(10, 15): "Moderate anxiety symptoms. Consider clinical evaluation.",
        range(15, 22): "Severe anxiety. Clinical evaluation strongly recommended.",
    }

    RECOMMENDATIONS = {
        "minimal": [
            "Continue regular monitoring of anxiety symptoms",
            "Practice stress management and relaxation techniques",
            "Maintain healthy sleep habits to reduce anxiety",
            "Reassess in 2-4 weeks if anxiety symptoms persist",
        ],
        "mild": [
            "Consider anxiety self-help strategies (relaxation, mindfulness)",
            "Monitor anxiety symptoms for worsening",
            "Reduce caffeine and alcohol intake to manage anxiety",
            "Consult healthcare provider if anxiety persists beyond 2 weeks",
        ],
        "moderate": [
            "Clinical evaluation for anxiety recommended",
            "Consider cognitive-behavioral therapy (CBT) for anxiety",
            "Consider anti-anxiety pharmacotherapy if appropriate",
            "Practice regular relaxation and stress reduction",
        ],
        "moderately_severe": [  # Fallback for threshold classification
            "Clinical evaluation for anxiety strongly recommended",
            "Psychotherapy indicated (CBT preferred for anxiety disorders)",
            "Anti-anxiety medication likely beneficial (SSRIs/SNRIs)",
        ],
        "severe": [
            "Clinical evaluation for severe anxiety strongly recommended",
            "Psychotherapy indicated (CBT preferred for anxiety disorders)",
            "Anti-anxiety medication likely beneficial (SSRIs/SNRIs)",
            "Consider intensive treatment if anxiety impairment is severe",
        ],
    }

    def __init__(self):
        super().__init__(GAD7_CONFIG)
        self.severity_classifier = SeverityClassifier.for_gad7()
        # GAD-7 has no suicide/crisis item, but we still initialize detector
        # for potential future panic symptom monitoring
        self.crisis_detector = CrisisDetector.for_gad7()

    def score(self, responses: Dict[int, int]) -> ScoringResult:
        """
        Score GAD-7 assessment using refactored components.

        Flow:
        1. Validate input (via base class)
        2. Calculate total score
        3. Classify severity (via SeverityClassifier)
        4. Check for severe anxiety indicators
        5. Generate interpretation and recommendations
        6. Return standardized result

        Args:
            responses: Dict mapping item number (1-7) to response value (0-3)

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

        # Step 4: Check for severe anxiety indicators
        # GAD-7 has no dedicated suicide item, but we flag severe cases
        risk_flags = []
        crisis_alert = False

        # Item 6 assesses restlessness/inability to sit still
        # Item 7 assesses fear that something awful might happen
        # High scores on these may indicate panic symptoms
        item_6_response = responses.get(6, 0)
        item_7_response = responses.get(7, 0)

        if item_6_response >= 2 or item_7_response >= 2:
            risk_flags.append("PANIC_SYMPTOMS_DETECTED")
            logger.info("GAD-7: Potential panic symptoms detected (items 6/7)")

        # Severe anxiety may require urgent attention
        if total_score >= 15:
            risk_flags.append("SEVERE_ANXIETY")
            # Note: Not a crisis in the same way as suicidal ideation,
            # but severe anxiety warrants prompt clinical attention
            if total_score >= 18:
                crisis_alert = True
                risk_flags.append("URGENT_CLINICAL_ATTENTION_RECOMMENDED")

        # Step 5: Generate interpretation and recommendations
        interpretation = self._get_interpretation(total_score)
        recommendations = self._get_recommendations(severity, crisis_alert)

        return ScoringResult(
            total_score=float(total_score),
            severity_level=severity,
            risk_level=risk,
            subscale_scores={},  # GAD-7 is unidimensional
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            risk_flags=risk_flags,
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
            # Note: GAD-7 crisis is less urgent than PHQ-9 suicide risk
            # but still warrants prompt attention
            crisis_addendum = [
                "⚠️ SEVERE ANXIETY: Prompt clinical assessment recommended",
                "Consider contacting your healthcare provider within 24-48 hours",
                "If experiencing panic attack, practice grounding techniques",
                "Panic attack helpline available if symptoms are overwhelming",
            ]
            return base_recommendations + crisis_addendum

        return base_recommendations
