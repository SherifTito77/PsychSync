"""
Configuration objects for clinical scoring system.

Using dataclasses for type safety, validation, and clear documentation.
"""

from dataclasses import dataclass, field
from enum import Enum


class SeverityLevel(Enum):
    """Standard severity levels for clinical assessments"""

    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


class RiskLevel(Enum):
    """Risk level classifications"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScoringThresholds:
    """
    Threshold configuration for a clinical instrument.

    This encapsulates all scoring thresholds in one place,
    making them easy to test and modify.
    """

    minimal: int
    mild: int
    moderate: int
    moderately_severe: int
    severe: int = float("inf")

    def get_severity(self, score: int) -> SeverityLevel:
        """Map score to severity level"""
        if score <= self.minimal:
            return SeverityLevel.MINIMAL
        if score <= self.mild:
            return SeverityLevel.MILD
        if score <= self.moderate:
            return SeverityLevel.MODERATE
        if score <= self.moderately_severe:
            return SeverityLevel.MODERATELY_SEVERE
        return SeverityLevel.SEVERE

    def validate(self) -> None:
        """Ensure thresholds are in ascending order"""
        thresholds = [self.minimal, self.mild, self.moderate, self.moderately_severe]
        if thresholds != sorted(thresholds):
            raise ValueError("Thresholds must be in ascending order")


@dataclass
class CrisisThresholds:
    """
    Configuration for crisis detection.

    Centralizes crisis detection rules for each instrument.
    """

    suicide_item_number: int
    crisis_threshold: int  # Score on suicide item that triggers crisis
    severe_crisis_threshold: int  # Score that triggers immediate alert
    requires_any_positive: bool = False  # Whether ANY positive response triggers alert

    def is_crisis(self, item_response: int) -> bool:
        """Check if response indicates crisis"""
        if self.requires_any_positive:
            return item_response >= 1
        return item_response >= self.crisis_threshold

    def is_severe_crisis(self, item_response: int) -> bool:
        """Check if response indicates severe crisis"""
        return item_response >= self.severe_crisis_threshold


@dataclass
class InstrumentConfig:
    """
    Complete configuration for a clinical scoring instrument.

    This replaces multiple function parameters and scattered settings.
    """

    name: str
    items: int  # Total number of items
    response_range: tuple[int, int]  # Valid response values (min, max)
    scoring_thresholds: ScoringThresholds
    crisis_thresholds: CrisisThresholds | None = None
    requires_crisis_detection: bool = True
    # Additional metadata
    description: str = ""
    references: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration"""
        if self.items < 1:
            raise ValueError(f"{self.name}: items must be >= 1")
        if self.response_range[0] >= self.response_range[1]:
            raise ValueError(f"{self.name}: invalid response_range")
        self.scoring_thresholds.validate()


# Predefined configurations for common instruments
PHQ9_CONFIG = InstrumentConfig(
    name="PHQ-9",
    items=9,
    response_range=(0, 3),
    scoring_thresholds=ScoringThresholds(
        minimal=4,
        mild=9,
        moderate=14,
        moderately_severe=19,
    ),
    crisis_thresholds=CrisisThresholds(
        suicide_item_number=9,
        crisis_threshold=1,
        severe_crisis_threshold=2,
        requires_any_positive=True,
    ),
    description="Patient Health Questionnaire-9 for depression screening",
    references=["Kroenke et al., 2001", "APA Guidelines"],
)

GAD7_CONFIG = InstrumentConfig(
    name="GAD-7",
    items=7,
    response_range=(0, 3),
    scoring_thresholds=ScoringThresholds(
        minimal=4,
        mild=9,
        moderate=14,
        moderately_severe=14,  # Skip moderately_severe, go straight to severe at 15
    ),
    description="Generalized Anxiety Disorder-7 item scale",
    references=["Spitzer et al., 2006"],
)

ASRS_CONFIG = InstrumentConfig(
    name="ASRS",
    items=18,
    response_range=(0, 4),
    scoring_thresholds=ScoringThresholds(
        minimal=23,
        mild=35,
        moderate=100,  # Not used for ASRS
        moderately_severe=100,  # Not used for ASRS
    ),
    requires_crisis_detection=False,  # ASRS doesn't have crisis items
    description="Adult ADHD Self-Report Scale v1.1 Symptom Checklist",
    references=["Kessler et al., 2005", "DSM-5"],
)

CSSRS_CONFIG = InstrumentConfig(
    name="C-SSRS",
    items=13,
    response_range=(0, 1),
    scoring_thresholds=ScoringThresholds(
        minimal=0,
        mild=0,
        moderate=1,
        moderately_severe=3,
    ),
    crisis_thresholds=CrisisThresholds(
        suicide_item_number=3,
        crisis_threshold=1,
        severe_crisis_threshold=3,
        requires_any_positive=True,
    ),
    description="Columbia-Suicide Severity Rating Scale",
    references=["Posner et al., 2011"],
)
