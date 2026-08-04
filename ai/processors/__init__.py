# app/ai/processors/__init__.py - Processor Registry

from typing import List

from ai.processors.enneagram_processor import EnneagramProcessor
from ai.processors.mbti_processor import MBTIProcessor

# from ai.processors.big_five_processor import BigFiveProcessor  # TODO: Create this file
from ai.processors.predictive_index import PredictiveIndexProcessor
from ai.processors.processors_base import PersonalityFrameworkProcessor
from ai.processors.social_styles import SocialStylesProcessor
from ai.processors.strengths import StrengthsProcessor

# Processor registry for dynamic loading
PROCESSOR_REGISTRY = {
    "enneagram": EnneagramProcessor,
    "mbti": MBTIProcessor,
    # 'big_five': BigFiveProcessor,  # TODO: Create this file
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
    # 'BigFiveProcessor',  # TODO: Create this file
    "PredictiveIndexProcessor",
    "StrengthsProcessor",
    "SocialStylesProcessor",
    "PROCESSOR_REGISTRY",
    "get_processor",
    "get_available_frameworks",
]
