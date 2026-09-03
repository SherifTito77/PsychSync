"""
Compatibility layer for clinical scoring.
Bridges modular scoring strategies with legacy monolith interfaces.
"""

from typing import Any, Dict, List

from .strategies.base import ScoringResult
from .strategies.gad7_scorer import GAD7Scorer
from .strategies.phq9_scorer import PHQ9Scorer


def score_phq9_legacy(responses: Dict[int, int]) -> Dict[str, Any]:
    """Compatibility bridge for PHQ-9"""
    scorer = PHQ9Scorer()
    result = scorer.score(responses)
    return {
        "screening_type": "PHQ9",
        "total_score": result.total_score,
        "severity_level": result.severity_level,
        "risk_level": result.risk_level,
        "interpretation": result.interpretation,
        "recommendations": result.recommendations,
        "crisis_alert": result.crisis_alert,
        "risk_flags": result.risk_flags,
        "subscale_scores": result.subscale_scores,
        "completed_at": "2025-01-15T00:00:00Z",
    }


def score_gad7_legacy(responses: Dict[int, int]) -> Dict[str, Any]:
    """Compatibility bridge for GAD-7"""
    scorer = GAD7Scorer()
    result = scorer.score(responses)
    return {
        "screening_type": "GAD7",
        "total_score": result.total_score,
        "severity_level": result.severity_level,
        "risk_level": result.risk_level,
        "interpretation": result.interpretation,
        "recommendations": result.recommendations,
        "crisis_alert": result.crisis_alert,
        "risk_flags": result.risk_flags,
        "subscale_scores": result.subscale_scores,
        "completed_at": "2025-01-15T00:00:00Z",
    }
