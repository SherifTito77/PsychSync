"""
C-SSRS (Columbia-Suicide Severity Rating Scale) Scoring Strategy.
Refactored into the modular architecture.
"""

import logging
from typing import Dict

from ..config import CSSRS_CONFIG
from ..detectors.crisis_detector import CrisisDetector
from .base import BaseScoringStrategy, ScoringResult

logger = logging.getLogger(__name__)


class CSSRSScorer(BaseScoringStrategy):
    """Refactored C-SSRS scoring strategy."""

    def __init__(self):
        super().__init__(CSSRS_CONFIG)
        self.crisis_detector = CrisisDetector(thresholds=CSSRS_CONFIG.crisis_thresholds)

    def score(self, responses: Dict[int, int]) -> ScoringResult:
        """Score C-SSRS based on crisis indicators."""
        self.validate_responses(responses)

        # C-SSRS logic: mapping items to specific risk indicators
        recent_attempt = bool(responses.get(11, False))
        active_ideation = any(responses.get(i, False) for i in [3, 4, 5])
        passive_ideation = any(responses.get(i, False) for i in [1, 2])

        if recent_attempt:
            risk = "critical"
            severity = "recent_attempt"
            crisis_alert = True
            risk_flags = ["recent_attempt"]
        elif active_ideation:
            risk = "high"
            severity = "active_ideation"
            crisis_alert = True
            risk_flags = ["active_ideation"]
        elif passive_ideation:
            risk = "moderate"
            severity = "passive_ideation"
            crisis_alert = True
            risk_flags = ["passive_ideation"]
        else:
            risk = "low"
            severity = "no_ideation"
            crisis_alert = False
            risk_flags = []

        total_score = float(
            5
            if recent_attempt
            else (3 if active_ideation else (1 if passive_ideation else 0))
        )

        return ScoringResult(
            total_score=total_score,
            severity_level=severity,
            risk_level=risk,
            subscale_scores={"ideation_level": total_score},
            interpretation=self._get_interpretation(int(total_score), recent_attempt),
            recommendations=self._get_recommendations(risk),
            crisis_alert=crisis_alert,
            risk_flags=risk_flags,
        )

    def _get_interpretation(self, ideation_level: int, attempt: bool) -> str:
        if attempt:
            return "🚨 CRITICAL: Recent suicide attempt reported. IMMEDIATE intervention required."
        elif ideation_level >= 3:
            return "⚠️ HIGH RISK: Active suicidal ideation. Urgent mental health evaluation required."
        elif ideation_level >= 1:
            return "⚠️ MODERATE RISK: Suicidal thoughts present. Mental health evaluation recommended."
        return "No current suicidal ideation reported."

    def _get_recommendations(self, risk_level: str) -> list[str]:
        if risk_level == "critical":
            return ["🚨 CALL 911/988 IMMEDIATELY", "DO NOT leave person alone"]
        elif risk_level == "high":
            return [
                "URGENT: Contact crisis line (988)",
                "Seek emergency psychiatric evaluation",
            ]
        elif risk_level == "moderate":
            return ["Contact professional within 24-48 hours", "Call 988 for support"]
        return ["Continue self-monitoring", "Use 988 if symptoms worsen"]
