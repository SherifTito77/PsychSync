"""
Refactored Clinical Scoring System

This package contains the refactored scoring system with improved separation of concerns.
Each module has a single, well-defined responsibility.

Architecture:
- strategies/: Different scoring strategies for each clinical instrument
- detectors/: Crisis detection and risk assessment
- classifiers/: Severity classification logic
- validators/: Input validation
- config/: Configuration objects
"""

from .strategies.base import BaseScoringStrategy
from .detectors.crisis_detector import CrisisDetector
from .classifiers.severity_classifier import SeverityClassifier

__all__ = [
    'BaseScoringStrategy',
    'CrisisDetector',
    'SeverityClassifier',
]
