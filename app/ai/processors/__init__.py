"""Processor registry for the canonical `app.ai.processors` package."""

from typing import List

from .big_five import BigFiveProcessor
from .enneagram_processor import EnneagramProcessor
from .mbti_processor import MBTIProcessor
from .predictive_index import PredictiveIndexProcessor
from .processors_base import PersonalityFrameworkProcessor
from .social_styles import SocialStylesProcessor
from .strengths import StrengthsProcessor

# Processor registry for dynamic loading
PROCESSOR_REGISTRY = {
    "enneagram": EnneagramProcessor,
    "mbti": MBTIProcessor,
    "big_five": BigFiveProcessor,
    "predictive_index": PredictiveIndexProcessor,
    "strengths": StrengthsProcessor,
    "social_styles": SocialStylesProcessor,
}


def get_processor(framework: str) -> PersonalityFrameworkProcessor:
    """Get processor instance for specified framework"""
    if framework not in PROCESSOR_REGISTRY:
        raise ValueError(f"Unknown framework: {framework}")

    processor_class = PROCESSOR_REGISTRY[framework]
    return processor_class()


def get_available_frameworks() -> List[str]:
    """Get list of supported frameworks"""
    return list(PROCESSOR_REGISTRY.keys())


__all__ = [
    "PersonalityFrameworkProcessor",
    "EnneagramProcessor",
    "MBTIProcessor",
    "BigFiveProcessor",
    "PredictiveIndexProcessor",
    "StrengthsProcessor",
    "SocialStylesProcessor",
    "PROCESSOR_REGISTRY",
    "get_processor",
    "get_available_frameworks",
]
