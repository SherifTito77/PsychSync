"""
Severity classification module.

This module is SOLELY responsible for classifying assessment severity
based on total scores. It does NOT perform scoring or crisis detection.

Single Responsibility Principle: Only classify severity levels.
"""

from dataclasses import dataclass
from typing import Dict, List
from ..config import ScoringThresholds, SeverityLevel, RiskLevel


@dataclass
class SeverityClassification:
    """
    Result of severity classification.

    Contains only severity-related information.
    """
    severity: SeverityLevel
    risk: RiskLevel
    score: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "severity": self.severity.value,
            "risk": self.risk.value,
            "score": self.score,
        }


class SeverityClassifier:
    """
    Classifies assessment severity based on total scores.

    Uses instrument-specific thresholds to map raw scores to
    clinically meaningful severity levels.
    """

    # Risk level mappings for different severities
    RISK_MAPPING = {
        SeverityLevel.MINIMAL: RiskLevel.LOW,
        SeverityLevel.MILD: RiskLevel.LOW,
        SeverityLevel.MODERATE: RiskLevel.MODERATE,
        SeverityLevel.MODERATELY_SEVERE: RiskLevel.HIGH,
        SeverityLevel.SEVERE: RiskLevel.CRITICAL,
    }

    def __init__(self, thresholds: ScoringThresholds):
        self.thresholds = thresholds

    def classify(self, total_score: int) -> SeverityClassification:
        """
        Classify severity based on total score.

        Args:
            total_score: Total assessment score

        Returns:
            SeverityClassification with severity and risk level
        """
        severity = self.thresholds.get_severity(total_score)
        risk = self.RISK_MAPPING[severity]

        return SeverityClassification(
            severity=severity,
            risk=risk,
            score=total_score,
        )

    @classmethod
    def for_phq9(cls) -> 'SeverityClassifier':
        """Factory method for PHQ-9 classification"""
        from ..config import PHQ9_CONFIG
        return cls(thresholds=PHQ9_CONFIG.scoring_thresholds)

    @classmethod
    def for_gad7(cls) -> 'SeverityClassifier':
        """Factory method for GAD-7 classification"""
        from ..config import GAD7_CONFIG
        return cls(thresholds=GAD7_CONFIG.scoring_thresholds)
