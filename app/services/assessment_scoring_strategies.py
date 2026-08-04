"""
Assessment Scoring Strategies - Strategy Pattern Implementation

Open/Closed Principle (OCP): Open for extension, closed for modification

This module implements the Strategy Pattern for assessment scoring, allowing new
assessment frameworks to be added without modifying existing code (OCP compliance).

Architecture:
    - ScoringStrategy: Abstract base class
    - MBTIScoringStrategy: MBTI assessment scoring
    - BigFiveScoringStrategy: Big Five assessment scoring
    - EnneagramScoringStrategy: Enneagram assessment scoring
    - ScoringStrategyRegistry: Register and retrieve strategies

Usage:
    # Register strategies at startup
    registry = ScoringStrategyRegistry()
    registry.register("MBTI", MBTIScoringStrategy())
    registry.register("BIG_FIVE", BigFiveScoringStrategy())

    # Use in service
    strategy = registry.get_strategy("MBTI")
    scores = strategy.calculate(responses)

Author: Development Team
Version: 1.0 (SOLID OCP Fix)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from app.db.models.response import Response

# =============================================================================
# Data Classes & Enums
# =============================================================================


class FrameworkCode(Enum):
    """Standard assessment framework codes"""

    MBTI = "MBTI"
    BIG_FIVE = "BIG_FIVE"
    ENNEAGRAM = "ENNEAGRAM"
    DISC = "DISC"
    PREDICTIVE_INDEX = "PREDICTIVE_INDEX"
    CLIFTON_STRENGTHS = "CLIFTON_STRENGTHS"
    SOCIAL_STYLES = "SOCIAL_STYLES"
    ASRS = "ASRS"  # ADHD Self-Report Scale
    LSAS = "LSAS"  # Liebowitz Social Anxiety Scale
    ISI = "ISI"  # Insomnia Severity Index


@dataclass
class ScoringResult:
    """Result of assessment scoring"""

    framework_code: str
    scores: Dict[str, float]
    normalized: bool
    calculated_at: datetime
    metadata: Dict[str, Any] | None = None
    interpretation: str | None = None
    severity: str | None = None  # For clinical assessments


# =============================================================================
# Abstract Strategy Interface
# =============================================================================


class ScoringStrategy(ABC):
    """
    Abstract base class for assessment scoring strategies.

    All assessment scoring strategies must inherit from this class and
    implement the calculate() method.

    This follows the Open/Closed Principle:
    - Open for extension: Create new strategies by inheriting from this class
    - Closed for modification: No need to modify existing strategies
    """

    @abstractmethod
    def calculate(self, responses: List[Response]) -> ScoringResult:
        """
        Calculate assessment scores from responses.

        Args:
            responses: List of assessment responses

        Returns:
            ScoringResult with calculated scores

        Raises:
            ValueError: If responses are invalid for this framework
        """
        pass

    @abstractmethod
    def validate_responses(self, responses: List[Response]) -> bool:
        """
        Validate that responses are appropriate for this framework.

        Args:
            responses: List of assessment responses

        Returns:
            True if responses are valid, False otherwise
        """
        pass

    def get_framework_code(self) -> str:
        """Get the framework code for this strategy."""
        return self.__class__.__name__.replace("ScoringStrategy", "").upper()


# =============================================================================
# Concrete Strategy Implementations
# =============================================================================


class MBTIScoringStrategy(ScoringStrategy):
    """
    MBTI (Myers-Briggs Type Indicator) scoring strategy.

    MBTI measures personality across 4 dichotomies:
    - E (Extraversion) vs I (Introversion)
    - S (Sensing) vs N (Intuition)
    - T (Thinking) vs F (Feeling)
    - J (Judging) vs P (Perceiving)
    """

    def validate_responses(self, responses: List[Response]) -> bool:
        """Validate MBTI responses."""
        if not responses:
            return False

        # MBTI typically has ~93 questions
        # For now, just check we have responses
        return len(responses) > 0

    def calculate(self, responses: List[Response]) -> ScoringResult:
        """
        Calculate MBTI scores from responses.

        Returns scores for each dichotomy as a float between -1 and 1:
        - Positive value = first letter (E, S, T, J)
        - Negative value = second letter (I, N, F, P)
        """
        # Initialize scores
        e_i_score = 0.0  # Extraversion vs Introversion
        s_n_score = 0.0  # Sensing vs Intuition
        t_f_score = 0.0  # Thinking vs Feeling
        j_p_score = 0.0  # Judging vs Perceiving

        # Count responses for each dimension
        # This is a simplified placeholder - real MBTI scoring is complex
        for response in responses:
            if hasattr(response, "question_id") and hasattr(response, "score"):
                # Placeholder: Use response score
                # In production, this would map questions to dimensions
                e_i_score += response.score if response.score else 0

        # Normalize scores to -1 to 1 range
        total_responses = len(responses) if responses else 1

        return ScoringResult(
            framework_code=FrameworkCode.MBTI.value,
            scores={
                "E_I": e_i_score / total_responses,
                "S_N": s_n_score / total_responses,
                "T_F": t_f_score / total_responses,
                "J_P": j_p_score / total_responses,
            },
            normalized=True,
            calculated_at=datetime.utcnow(),
            metadata={
                "response_count": len(responses),
                "dimensions": ["E_I", "S_N", "T_F", "J_P"],
            },
            interpretation=self._interpret_mbti_type(
                e_i_score, s_n_score, t_f_score, j_p_score
            ),
        )

    def _interpret_mbti_type(
        self, e_i: float, s_n: float, t_f: float, j_p: float
    ) -> str:
        """Determine MBTI type from scores."""
        type_str = ""

        # Extraversion vs Introversion
        type_str += "E" if e_i > 0 else "I"

        # Sensing vs Intuition
        type_str += "S" if s_n > 0 else "N"

        # Thinking vs Feeling
        type_str += "T" if t_f > 0 else "F"

        # Judging vs Perceiving
        type_str += "J" if j_p > 0 else "P"

        return type_str


class BigFiveScoringStrategy(ScoringStrategy):
    """
    Big Five (Ocean Model) scoring strategy.

    Big Five measures 5 personality traits:
    - O (Openness)
    - C (Conscientiousness)
    - E (Extraversion)
    - A (Agreeableness)
    - N (Neuroticism)
    """

    def validate_responses(self, responses: List[Response]) -> bool:
        """Validate Big Five responses."""
        return len(responses) > 0

    def calculate(self, responses: List[Response]) -> ScoringResult:
        """
        Calculate Big Five scores from responses.

        Returns scores for each trait as a float between 0 and 100.
        """
        # Initialize scores
        openness = 0.0
        conscientiousness = 0.0
        extraversion = 0.0
        agreeableness = 0.0
        neuroticism = 0.0

        # Sum up responses
        for response in responses:
            if hasattr(response, "score"):
                score = response.score or 0
                # In production, would map questions to traits
                # For now, evenly distribute
                openness += score / 5
                conscientiousness += score / 5
                extraversion += score / 5
                agreeableness += score / 5
                neuroticism += score / 5

        total_responses = len(responses) if responses else 1

        return ScoringResult(
            framework_code=FrameworkCode.BIG_FIVE.value,
            scores={
                "openness": openness / total_responses * 100,
                "conscientiousness": conscientiousness / total_responses * 100,
                "extraversion": extraversion / total_responses * 100,
                "agreeableness": agreeableness / total_responses * 100,
                "neuroticism": neuroticism / total_responses * 100,
            },
            normalized=True,
            calculated_at=datetime.utcnow(),
            metadata={
                "response_count": len(responses),
                "traits": ["O", "C", "E", "A", "N"],
            },
            interpretation=self._interpret_big_five(
                openness, conscientiousness, extraversion, agreeableness, neuroticism
            ),
        )

    def _interpret_big_five(
        self, o: float, c: float, e: float, a: float, n: float
    ) -> str:
        """Generate Big Five interpretation."""
        interpretations = []

        if o > 70:
            interpretations.append("High openness to experience")
        elif o < 30:
            interpretations.append("Prefers familiarity and routine")

        if c > 70:
            interpretations.append("Highly organized and disciplined")
        elif c < 30:
            interpretations.append("Flexible and spontaneous")

        if e > 70:
            interpretations.append("Very sociable and energetic")
        elif e < 30:
            interpretations.append("Reserved and introspective")

        if a > 70:
            interpretations.append("Very cooperative and compassionate")
        elif a < 30:
            interpretations.append("Competitive and critical")

        if n > 70:
            interpretations.append("Prone to stress and anxiety")
        elif n < 30:
            interpretations.append("Emotionally stable and calm")

        return "; ".join(interpretations) if interpretations else "Balanced personality"


class EnneagramScoringStrategy(ScoringStrategy):
    """
    Enneagram scoring strategy.

    Enneagram measures 9 personality types, each with distinct motivations.
    """

    def validate_responses(self, responses: List[Response]) -> bool:
        """Validate Enneagram responses."""
        return len(responses) > 0

    def calculate(self, responses: List[Response]) -> ScoringResult:
        """
        Calculate Enneagram scores from responses.

        Returns scores for all 9 types as floats between 0 and 100.
        """
        # Initialize scores for all 9 types
        type_scores = {f"type_{i}": 0.0 for i in range(1, 10)}

        # Sum up responses
        for response in responses:
            if hasattr(response, "score"):
                # In production, would map questions to types
                # For now, distribute evenly
                for i in range(1, 10):
                    type_scores[f"type_{i}"] += (
                        response.score / 9 if response.score else 0
                    )

        total_responses = len(responses) if responses else 1

        # Normalize to 0-100 scale
        normalized_scores = {
            f"type_{i}": (type_scores[f"type_{i}"] / total_responses) * 100
            for i in range(1, 10)
        }

        # Determine dominant type
        dominant_type = max(normalized_scores, key=normalized_scores.get)

        return ScoringResult(
            framework_code=FrameworkCode.ENNEAGRAM.value,
            scores=normalized_scores,
            normalized=True,
            calculated_at=datetime.utcnow(),
            metadata={
                "response_count": len(responses),
                "dominant_type": dominant_type,
                "all_types": [f"type_{i}" for i in range(1, 10)],
            },
            interpretation=self._interpret_enneagram(
                dominant_type, normalized_scores[dominant_type]
            ),
        )

    def _interpret_enneagram(self, dominant_type: str, score: float) -> str:
        """Interpret Enneagram type."""
        type_num = dominant_type.replace("type_", "")

        type_descriptions = {
            "1": "The Perfectionist - rational and idealistic",
            "2": "The Helper - caring and interpersonal",
            "3": "The Achiever - success-oriented and pragmatic",
            "4": "The Individualist - sensitive and withdrawn",
            "5": "The Investigator - intense and cerebral",
            "6": "The Loyalist - committed and security-oriented",
            "7": "The Enthusiast - spontaneous and versatile",
            "8": "The Challenger - powerful and dominating",
            "9": "The Peacemaker - easygoing and self-effacing",
        }

        description = type_descriptions.get(type_num, "Unknown type")
        confidence = "Strong" if score > 60 else "Moderate" if score > 40 else "Mild"

        return f"Type {type_num}: {description} ({confidence} match)"


class DISCScoringStrategy(ScoringStrategy):
    """
    DISC assessment scoring strategy.

    DISC measures 4 behavioral styles:
    - D (Dominance)
    - I (Influence)
    - S (Steadiness)
    - C (Compliance)
    """

    def validate_responses(self, responses: List[Response]) -> bool:
        """Validate DISC responses."""
        return len(responses) > 0

    def calculate(self, responses: List[Response]) -> ScoringResult:
        """Calculate DISC scores from responses."""
        # Initialize scores
        d_score = 0.0
        i_score = 0.0
        s_score = 0.0
        c_score = 0.0

        for response in responses:
            if hasattr(response, "score"):
                score = response.score or 0
                # Evenly distribute for now
                d_score += score / 4
                i_score += score / 4
                s_score += score / 4
                c_score += score / 4

        total_responses = len(responses) if responses else 1

        return ScoringResult(
            framework_code=FrameworkCode.DISC.value,
            scores={
                "D": d_score / total_responses * 100,
                "I": i_score / total_responses * 100,
                "S": s_score / total_responses * 100,
                "C": c_score / total_responses * 100,
            },
            normalized=True,
            calculated_at=datetime.utcnow(),
            metadata={
                "response_count": len(responses),
                "styles": ["D", "I", "S", "C"],
            },
            interpretation=self._interpret_disc(d_score, i_score, s_score, c_score),
        )

    def _interpret_disc(self, d: float, i: float, s: float, c: float) -> str:
        """Interpret DISC style."""
        styles = []

        if d > 50:
            styles.append("Dominant - direct and firm")
        if i > 50:
            styles.append("Influential - outgoing and enthusiastic")
        if s > 50:
            styles.append("Steady - patient and predictable")
        if c > 50:
            styles.append("Compliant - analytical and precise")

        return "; ".join(styles) if styles else "Balanced style"


# =============================================================================
# Strategy Registry
# =============================================================================


class ScoringStrategyRegistry:
    """
    Registry for assessment scoring strategies.

    This follows the Open/Closed Principle:
    - New strategies can be registered without modifying existing code
    - Strategies are looked up by framework code

    Usage:
        registry = ScoringStrategyRegistry()
        registry.register("MBTI", MBTIScoringStrategy())
        registry.register("BIG_FIVE", BigFiveScoringStrategy())

        # Get strategy
        strategy = registry.get_strategy("MBTI")
        scores = strategy.calculate(responses)
    """

    def __init__(self):
        """Initialize registry with empty strategy map."""
        self._strategies: Dict[str, ScoringStrategy] = {}
        self._logger = None

    def register(self, framework_code: str, strategy: ScoringStrategy) -> None:
        """
        Register a scoring strategy for a framework.

        Args:
            framework_code: Framework code (e.g., "MBTI", "BIG_FIVE")
            strategy: ScoringStrategy instance

        Raises:
            ValueError: If framework_code is already registered

        Example:
            registry.register("MBTI", MBTIScoringStrategy())
        """
        if framework_code in self._strategies:
            raise ValueError(
                f"Framework {framework_code} already has a registered strategy"
            )

        self._strategies[framework_code] = strategy

        if self._logger:
            self._logger.info(
                f"Registered scoring strategy for framework: {framework_code}"
            )

    def get_strategy(self, framework_code: str) -> ScoringStrategy:
        """
        Get scoring strategy for a framework.

        Args:
            framework_code: Framework code

        Returns:
            ScoringStrategy instance

        Raises:
            ValueError: If framework_code is not registered

        Example:
            strategy = registry.get_strategy("MBTI")
        """
        if framework_code not in self._strategies:
            # Try case-insensitive lookup
            framework_code_upper = framework_code.upper()
            if framework_code_upper in self._strategies:
                return self._strategies[framework_code_upper]

            available = ", ".join(self._strategies.keys())
            raise ValueError(
                f"No scoring strategy for framework: {framework_code}. "
                f"Available frameworks: {available}"
            )

        return self._strategies[framework_code]

    def has_strategy(self, framework_code: str) -> bool:
        """Check if framework has a registered strategy."""
        return framework_code in self._strategies

    def get_registered_frameworks(self) -> List[str]:
        """Get list of registered framework codes."""
        return list(self._strategies.keys())


# =============================================================================
# Default Registry (Singleton Pattern)
# =============================================================================

_default_registry: ScoringStrategyRegistry | None = None


def get_scoring_strategy_registry() -> ScoringStrategyRegistry:
    """Get default scoring strategy registry (singleton pattern)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ScoringStrategyRegistry()
        # Register default strategies
        _default_registry.register(FrameworkCode.MBTI.value, MBTIScoringStrategy())
        _default_registry.register(
            FrameworkCode.BIG_FIVE.value, BigFiveScoringStrategy()
        )
        _default_registry.register(
            FrameworkCode.ENNEAGRAM.value, EnneagramScoringStrategy()
        )
        _default_registry.register(FrameworkCode.DISC.value, DISCScoringStrategy())
    return _default_registry
