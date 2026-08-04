"""
Base classes for scoring strategies.

This module defines the interfaces that all scoring strategies must implement.
Using the Strategy Pattern allows for:
- Easy addition of new instruments
- Testable, isolated scoring logic
- Clear separation of concerns
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from ..config import InstrumentConfig, RiskLevel, SeverityLevel


@dataclass
class ScoringResult:
    """
    Standardized result object for all scoring strategies.

    This ensures consistent output format across all instruments.
    """

    total_score: float
    severity_level: str
    risk_level: str
    subscale_scores: Dict[str, float]
    interpretation: str
    recommendations: list[str]
    crisis_alert: bool
    risk_flags: list[str]
    metadata: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_score": self.total_score,
            "severity_level": self.severity_level,
            "risk_level": self.risk_level,
            "subscale_scores": self.subscale_scores,
            "interpretation": self.interpretation,
            "recommendations": self.recommendations,
            "crisis_alert": self.crisis_alert,
            "risk_flags": self.risk_flags,
            "metadata": self.metadata or {},
        }


class BaseScoringStrategy(ABC):
    """
    Abstract base class for all scoring strategies.

    Each clinical instrument implements this interface with its specific logic.
    """

    def __init__(self, config: InstrumentConfig):
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration matches strategy requirements"""
        if not isinstance(self.config.items, int) or self.config.items < 1:
            raise ValueError(f"Invalid items count: {self.config.items}")

    @abstractmethod
    def score(self, responses: Dict[int, int]) -> ScoringResult:
        """
        Calculate score from responses.

        Args:
            responses: Dict mapping item number to response value

        Returns:
            ScoringResult with all calculated values

        Raises:
            ValueError: If responses are invalid
        """
        pass

    def validate_responses(self, responses: Dict[int, int]) -> None:
        """
        Validate response format and values.

        Raises:
            ValueError: If responses are invalid
        """
        if len(responses) != self.config.items:
            raise ValueError(
                f"{self.config.name}: requires {self.config.items} responses, "
                f"got {len(responses)}"
            )

        min_val, max_val = self.config.response_range

        for item, value in responses.items():
            if not isinstance(value, int):
                raise ValueError(
                    f"{self.config.name}: Item {item} response must be int, got {type(value)}"
                )

            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"{self.config.name}: Item {item} response must be "
                    f"{min_val}-{max_val}, got {value}"
                )

            if item < 1 or item > self.config.items:
                raise ValueError(
                    f"{self.config.name}: Item number {item} out of range "
                    f"(1-{self.config.items})"
                )
