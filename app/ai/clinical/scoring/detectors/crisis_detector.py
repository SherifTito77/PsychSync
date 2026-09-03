"""
Crisis detection module.

This module is SOLELY responsible for detecting crisis indicators
in assessment responses. It does NOT perform scoring or interpretation.

Single Responsibility Principle: Only detect crisis signals.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List

from ..config import CrisisThresholds

logger = logging.getLogger(__name__)


@dataclass
class CrisisInfo:
    """
    Result of crisis detection analysis.

    Contains only crisis-related information, nothing else.
    """

    is_crisis: bool
    is_severe: bool
    risk_flags: List[str]
    crisis_items: Dict[int, int]  # Item numbers and responses that triggered crisis

    def add_flag(self, flag: str) -> None:
        """Add a risk flag"""
        if flag not in self.risk_flags:
            self.risk_flags.append(flag)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "is_crisis": self.is_crisis,
            "is_severe": self.is_severe,
            "risk_flags": self.risk_flags,
            "crisis_items": self.crisis_items,
        }


class CrisisDetector:
    """
    Detects crisis indicators in assessment responses.

    This detector can handle multiple clinical instruments with different
    crisis detection rules, configured via CrisisThresholds.
    """

    def __init__(self, thresholds: CrisisThresholds):
        self.thresholds = thresholds

    def detect(self, responses: Dict[int, int]) -> CrisisInfo:
        """
        Detect crisis indicators in responses.

        Args:
            responses: All assessment responses

        Returns:
            CrisisInfo with detected crisis information
        """
        crisis_info = CrisisInfo(
            is_crisis=False, is_severe=False, risk_flags=[], crisis_items={}
        )

        # Check suicide/crisis item if configured
        if self.thresholds:
            suicide_item = self.thresholds.suicide_item_number
            suicide_response = responses.get(suicide_item, 0)

            if suicide_response > 0:
                crisis_info.crisis_items[suicide_item] = suicide_response

                # Preserve the current public contract:
                # 1 = mild, 2 = moderate, 3+ = severe
                if suicide_response >= 3:
                    crisis_info.is_severe = True
                    crisis_info.is_crisis = True
                    crisis_info.add_flag("SUICIDE_IDEATION_SEVERE")
                    logger.warning(
                        f"Severe suicide ideation detected: "
                        f"Item {suicide_item} = {suicide_response}"
                    )
                elif suicide_response == 2:
                    crisis_info.is_crisis = True
                    crisis_info.add_flag("SUICIDE_IDEATION_MODERATE")
                    logger.info(
                        f"Moderate suicide ideation detected: "
                        f"Item {suicide_item} = {suicide_response}"
                    )
                else:
                    crisis_info.is_crisis = True
                    crisis_info.add_flag("SUICIDE_IDEATION_MILD")

        return crisis_info

    @classmethod
    def for_phq9(cls) -> "CrisisDetector":
        """Factory method for PHQ-9 crisis detection"""
        from ..config import PHQ9_CONFIG

        return cls(thresholds=PHQ9_CONFIG.crisis_thresholds)

    @classmethod
    def for_gad7(cls) -> "CrisisDetector":
        """Factory method for GAD-7 crisis detection (no crisis item)"""
        return cls(thresholds=None)
