"""
ASRS (Adult ADHD Self-Report Scale) Scoring Strategy - Refactored

This module demonstrates the refactored scoring approach using:
- Subscale-specific classifiers (inattention, hyperactivity)
- Separate risk calculator for ADHD types
- Separate recommendation engine
- Clean, single-responsibility functions

Complexity reduced from 150+ lines to ~80 lines through better separation.
"""

import logging
from typing import Dict

from ..config import ASRS_CONFIG, RiskLevel, SeverityLevel
from ..recommendations.recommendation_engine import RecommendationEngine
from .base import BaseScoringStrategy, ScoringResult

logger = logging.getLogger(__name__)


class ADHDClassifier:
    """
    Specialized classifier for ADHD assessment.

    ASRS requires custom classification logic because it has:
    - Two subscales (inattention, hyperactivity)
    - Multiple ADHD types (combined, inattentive, hyperactive)
    - Different thresholds for each type
    """

    # Part A: Inattention items (questions 1-9)
    INATTENTION_ITEMS = list(range(1, 10))
    # Part B: Hyperactivity-Impulsivity items (questions 10-18)
    HYPERACTIVITY_ITEMS = list(range(10, 19))

    # Thresholds for ADHD classification
    INATTENTION_THRESHOLD = 24
    HYPERACTIVITY_THRESHOLD = 24
    SEVERE_INATTENTION_THRESHOLD = 30
    SEVERE_HYPERACTIVITY_THRESHOLD = 30

    def classify(self, responses: Dict[int, int]) -> Dict:
        """
        Classify ADHD type and severity based on subscale scores.

        Args:
            responses: Dict mapping item number to response value (0-4)

        Returns:
            Dict with classification results:
                - inattention_score: Part A total
                - hyperactivity_score: Part B total
                - total_score: Combined score
                - adhd_type: 'combined_type', 'inattentive_type', 'hyperactive_type', or symptom level
                - severity: Classification
                - risk: Risk level
                - risk_flags: List of risk indicators
        """
        # Calculate subscale scores
        inattention_score = sum(
            responses.get(item, 0) for item in self.INATTENTION_ITEMS
        )
        hyperactivity_score = sum(
            responses.get(item, 0) for item in self.HYPERACTIVITY_ITEMS
        )
        total_score = inattention_score + hyperactivity_score

        # Determine ADHD indicators
        inattention_adhd = inattention_score >= self.INATTENTION_THRESHOLD
        hyperactive_adhd = hyperactivity_score >= self.HYPERACTIVITY_THRESHOLD
        combined_adhd = inattention_adhd and hyperactive_adhd

        # Classify ADHD type and severity
        if combined_adhd:
            adhd_type = "combined_type"
            severity = "combined_type"
            risk = RiskLevel.HIGH.value
        elif inattention_adhd:
            adhd_type = "inattentive_type"
            severity = "inattentive_type"
            risk = RiskLevel.HIGH.value
        elif hyperactive_adhd:
            adhd_type = "hyperactive_type"
            severity = "hyperactive_type"
            risk = RiskLevel.HIGH.value
        elif total_score >= 36:
            adhd_type = "symptoms_present"
            severity = "symptoms_present"
            risk = RiskLevel.MODERATE.value
        elif total_score >= 24:
            adhd_type = "some_symptoms"
            severity = "some_symptoms"
            risk = RiskLevel.LOW.value
        else:
            adhd_type = "minimal_symptoms"
            severity = "minimal_symptoms"
            risk = RiskLevel.LOW.value

        # Generate risk flags
        risk_flags = []
        if inattention_adhd:
            risk_flags.append("inattention_adhd_indicators")
        if hyperactive_adhd:
            risk_flags.append("hyperactivity_adhd_indicators")
        if inattention_score >= self.SEVERE_INATTENTION_THRESHOLD:
            risk_flags.append("severe_inattention")
        if hyperactivity_score >= self.SEVERE_HYPERACTIVITY_THRESHOLD:
            risk_flags.append("severe_hyperactivity")

        return {
            "inattention_score": inattention_score,
            "hyperactivity_score": hyperactivity_score,
            "total_score": total_score,
            "adhd_type": adhd_type,
            "severity": severity,
            "risk": risk,
            "risk_flags": risk_flags,
            "combined_adhd": combined_adhd,
            "inattention_adhd": inattention_adhd,
            "hyperactive_adhd": hyperactive_adhd,
        }


class ASRSScorer(BaseScoringStrategy):
    """
    Refactored ASRS scoring strategy.

    Previous implementation: 150+ lines with complex nested conditionals
    Refactored: ~80 lines with clear separation of concerns
    """

    # Interpretation texts - extracted for maintainability
    INTERPRETATIONS = {
        "combined_type": "Screening positive for ADHD Combined Type (both inattention and hyperactivity-impulsivity present). Clinical evaluation recommended for comprehensive assessment and diagnosis.",
        "inattentive_type": "Screening positive for ADHD Predominantly Inattentive Type. Clinical evaluation recommended to confirm diagnosis and explore treatment options.",
        "hyperactive_type": "Screening positive for ADHD Predominantly Hyperactive-Impulsive Type. Clinical evaluation recommended to confirm diagnosis and explore treatment options.",
        "symptoms_present": "Significant ADHD symptoms present across multiple domains. Consider clinical evaluation for comprehensive assessment.",
        "some_symptoms": "Some ADHD symptoms indicated. Further evaluation recommended if symptoms impact daily functioning.",
        "minimal_symptoms": "Minimal ADHD symptoms reported. Current screening does not suggest ADHD, but consider re-evaluation if symptoms change or worsen.",
    }

    def __init__(self):
        super().__init__(ASRS_CONFIG)
        self.adhd_classifier = ADHDClassifier()
        self.recommendation_engine = RecommendationEngine.for_asrs()

    def score(self, responses: Dict[int, int]) -> ScoringResult:
        """
        Score ASRS assessment using refactored components.

        Flow:
        1. Validate input (via base class)
        2. Calculate subscale scores (via ADHDClassifier)
        3. Classify ADHD type and severity
        4. Generate interpretation and recommendations
        5. Return standardized result

        Args:
            responses: Dict mapping item number (1-18) to response value (0-4)

        Returns:
            ScoringResult with complete analysis

        Raises:
            ValueError: If responses are invalid
        """
        # Step 1: Validate
        self.validate_responses(responses)

        # Step 2: Classify using specialized ADHD classifier
        classification = self.adhd_classifier.classify(responses)

        # Step 3: Generate interpretation
        interpretation = self.INTERPRETATIONS.get(
            classification["severity"], self.INTERPRETATIONS["minimal_symptoms"]
        )

        # Step 4: Get recommendations
        recommendations = self.recommendation_engine.generate(
            severity=classification["severity"],
            crisis_alert=False,  # ASRS doesn't have crisis indicators
        )

        # Step 5: Return standardized result
        return ScoringResult(
            total_score=float(classification["total_score"]),
            severity_level=classification["severity"],
            risk_level=classification["risk"],
            subscale_scores={
                "inattention": float(classification["inattention_score"]),
                "hyperactivity_impulsivity": float(
                    classification["hyperactivity_score"]
                ),
            },
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=False,  # ASRS doesn't trigger crisis protocol
            risk_flags=classification["risk_flags"],
            metadata={
                "adhd_type": classification["adhd_type"],
                "inattention_adhd": classification["inattention_adhd"],
                "hyperactive_adhd": classification["hyperactive_adhd"],
                "combined_adhd": classification["combined_adhd"],
            },
        )
