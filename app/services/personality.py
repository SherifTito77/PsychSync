"""
Personality Trait Mapping and Normalization Service
Converts between different personality frameworks and standardizes traits.
"""

from typing import Dict, Any, Optional, List
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PersonalityMapper:
    """Map and normalize personality traits across frameworks"""

    # MBTI to Big Five conversion coefficients based on research
    MBTI_TO_BIG_FIVE = {
        'E': {'extraversion': 0.75, 'openness': 0.1, 'conscientiousness': 0.0, 'agreeableness': 0.0, 'neuroticism': -0.2},
        'I': {'extraversion': 0.25, 'openness': 0.1, 'conscientiousness': 0.0, 'agreeableness': 0.0, 'neuroticism': 0.2},
        'S': {'extraversion': 0.0, 'openness': 0.30, 'conscientiousness': 0.60, 'agreeableness': 0.0, 'neuroticism': 0.0},
        'N': {'extraversion': 0.0, 'openness': 0.70, 'conscientiousness': 0.40, 'agreeableness': 0.0, 'neuroticism': 0.0},
        'T': {'extraversion': 0.0, 'openness': 0.0, 'conscientiousness': 0.0, 'agreeableness': 0.30, 'neuroticism': 0.0},
        'F': {'extraversion': 0.0, 'openness': 0.0, 'conscientiousness': 0.0, 'agreeableness': 0.70, 'neuroticism': 0.0},
        'J': {'extraversion': 0.0, 'openness': 0.0, 'conscientiousness': 0.70, 'agreeableness': 0.0, 'neuroticism': 0.0},
        'P': {'extraversion': 0.0, 'openness': 0.60, 'conscientiousness': 0.30, 'agreeableness': 0.0, 'neuroticism': 0.0}
    }

    # Enneagram to Big Five conversion
    ENNEAGRAM_TO_BIG_FIVE = {
        1: {'openness': 0.3, 'conscientiousness': 0.9, 'extraversion': 0.4, 'agreeableness': 0.3, 'neuroticism': 0.6},
        2: {'openness': 0.5, 'conscientiousness': 0.6, 'extraversion': 0.8, 'agreeableness': 0.9, 'neuroticism': 0.5},
        3: {'openness': 0.6, 'conscientiousness': 0.8, 'extraversion': 0.9, 'agreeableness': 0.5, 'neuroticism': 0.4},
        4: {'openness': 0.9, 'conscientiousness': 0.4, 'extraversion': 0.3, 'agreeableness': 0.5, 'neuroticism': 0.8},
        5: {'openness': 0.8, 'conscientiousness': 0.5, 'extraversion': 0.2, 'agreeableness': 0.3, 'neuroticism': 0.6},
        6: {'openness': 0.4, 'conscientiousness': 0.7, 'extraversion': 0.5, 'agreeableness': 0.7, 'neuroticism': 0.8},
        7: {'openness': 0.9, 'conscientiousness': 0.3, 'extraversion': 0.9, 'agreeableness': 0.6, 'neuroticism': 0.3},
        8: {'openness': 0.5, 'conscientiousness': 0.6, 'extraversion': 0.8, 'agreeableness': 0.2, 'neuroticism': 0.3},
        9: {'openness': 0.4, 'conscientiousness': 0.4, 'extraversion': 0.3, 'agreeableness': 0.9, 'neuroticism': 0.4}
    }

    # DISC to Big Five conversion
    DISC_TO_BIG_FIVE = {
        'D': {'openness': 0.6, 'conscientiousness': 0.5, 'extraversion': 0.8, 'agreeableness': 0.3, 'neuroticism': 0.4},
        'I': {'openness': 0.7, 'conscientiousness': 0.4, 'extraversion': 0.9, 'agreeableness': 0.8, 'neuroticism': 0.5},
        'S': {'openness': 0.4, 'conscientiousness': 0.8, 'extraversion': 0.3, 'agreeableness': 0.9, 'neuroticism': 0.3},
        'C': {'openness': 0.5, 'conscientiousness': 0.9, 'extraversion': 0.2, 'agreeableness': 0.5, 'neuroticism': 0.6}
    }

    def __init__(self):
        self.cache = {}

    def map_traits(self, raw_traits: Dict[str, Any], framework: str = "raw") -> Dict[str, float]:
        """
        Normalize and map traits to standardized Big Five format

        Args:
            raw_traits: Raw trait data from assessment
            framework: Source framework (mbti, enneagram, disc, big_five, raw)

        Returns:
            Normalized traits in Big Five format (0-1 scale)
        """
        try:
            cache_key = f"{framework}:{hash(str(sorted(raw_traits.items())))}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            framework = framework.lower()

            if framework == "big_five" or framework == "ocean":
                result = self._normalize_big_five(raw_traits)
            elif framework == "mbti":
                result = self._mbti_to_big_five(raw_traits)
            elif framework == "enneagram":
                result = self._enneagram_to_big_five(raw_traits)
            elif framework == "disc":
                result = self._disc_to_big_five(raw_traits)
            elif framework == "predictive_index":
                result = self._predictive_index_to_big_five(raw_traits)
            elif framework == "clifton_strengths":
                result = self._strengths_to_big_five(raw_traits)
            else:
                result = self._normalize_raw(raw_traits)

            # Ensure all values are in 0-1 range
            result = self._ensure_range(result)

            # Cache result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error mapping traits from framework {framework}: {str(e)}")
            return self._get_default_traits()

    def _normalize_big_five(self, traits: Dict) -> Dict[str, float]:
        """Normalize Big Five traits to 0-1 scale"""
        dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        normalized = {}

        for dim in dimensions:
            value = traits.get(dim, 0.5)

            # Handle different input scales
            if isinstance(value, (int, float)):
                if value > 10:  # 1-100 scale
                    normalized[dim] = min(max(value / 100, 0.0), 1.0)
                elif value > 5:  # 1-10 scale
                    normalized[dim] = min(max(value / 10, 0.0), 1.0)
                else:  # 1-5 scale
                    normalized[dim] = min(max((value - 1) / 4, 0.0), 1.0)
            else:
                normalized[dim] = 0.5

        return normalized

    def _mbti_to_big_five(self, traits: Dict) -> Dict[str, float]:
        """Convert MBTI type to Big Five approximation"""
        mbti_type = traits.get('type', traits.get('mbti_type', 'INTJ')).upper()

        # Start with neutral scores
        result = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }

        # Apply MBTI trait contributions
        for letter in mbti_type:
            if letter in self.MBTI_TO_BIG_FIVE:
                for dimension, contribution in self.MBTI_TO_BIG_FIVE[letter].items():
                    if contribution > 0:
                        result[dimension] = min(result[dimension] + contribution * 0.3, 1.0)
                    else:
                        result[dimension] = max(result[dimension] + contribution * 0.3, 0.0)

        # Consider confidence scores if provided
        confidence = traits.get('confidence', 0.8)
        if confidence < 0.7:
            # Regress toward mean for low confidence
            for dim in result:
                result[dim] = result[dim] * confidence + 0.5 * (1 - confidence)

        return result

    def _enneagram_to_big_five(self, traits: Dict) -> Dict[str, float]:
        """Convert Enneagram type to Big Five approximation"""
        primary_type = traits.get('type', traits.get('enneagram_type', 5))

        # Handle both integer and string types
        try:
            type_num = int(primary_type)
        except (ValueError, TypeError):
            type_mapping = {
                'reformer': 1, 'perfectionist': 1,
                'helper': 2, 'giver': 2,
                'achiever': 3, 'performer': 3,
                'individualist': 4, 'romantic': 4,
                'investigator': 5, 'observer': 5,
                'loyalist': 6, 'skeptic': 6,
                'enthusiast': 7, 'epicure': 7,
                'challenger': 8, 'protector': 8,
                'peacemaker': 9, 'mediator': 9
            }
            type_num = type_mapping.get(str(primary_type).lower(), 5)

        base_traits = self.ENNEAGRAM_TO_BIG_FIVE.get(type_num, self.ENNEAGRAM_TO_BIG_FIVE[5])

        # Consider wings (adjacent types)
        wings = traits.get('wings', [])
        if wings:
            for wing in wings:
                if isinstance(wing, int) and 1 <= wing <= 9:
                    wing_traits = self.ENNEAGRAM_TO_BIG_FIVE[wing]
                    for dim in base_traits:
                        base_traits[dim] = (base_traits[dim] + wing_traits[dim]) / 2

        # Consider instinctual variants
        instincts = traits.get('instincts', {})
        if instincts:
            if 'social' in instincts:
                base_traits['extraversion'] += 0.1
                base_traits['agreeableness'] += 0.1
            if 'sexual' in instincts:
                base_traits['openness'] += 0.1
                base_traits['neuroticism'] += 0.1
            if 'self_preservation' in instincts:
                base_traits['conscientiousness'] += 0.1

        return base_traits

    def _disc_to_big_five(self, traits: Dict) -> Dict[str, float]:
        """Convert DISC profile to Big Five approximation"""
        disc_profile = traits.get('profile', '').upper()

        # Start with neutral scores
        result = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }

        # Apply DISC trait contributions
        for letter in disc_profile:
            if letter in self.DISC_TO_BIG_FIVE:
                for dimension, contribution in self.DISC_TO_BIG_FIVE[letter].items():
                    result[dimension] = min(result[dimension] + contribution * 0.25, 1.0)

        # Consider intensity scores if provided
        for letter in 'D I S C'.split():
            intensity = traits.get(f'{letter.lower()}_intensity', 0.5)
            if intensity != 0.5 and letter in self.DISC_TO_BIG_FIVE:
                letter_traits = self.DISC_TO_BIG_FIVE[letter]
                for dim, base_value in letter_traits.items():
                    adjustment = (intensity - 0.5) * base_value * 0.3
                    result[dim] = min(max(result[dim] + adjustment, 0.0), 1.0)

        return result

    def _predictive_index_to_big_five(self, traits: Dict) -> Dict[str, float]:
        """Convert Predictive Index to Big Five"""
        # PI has A-Dominance, B-Extraversion, C-Patience, D-Formality
        a = traits.get('A', traits.get('dominance', 0.5))
        b = traits.get('B', traits.get('extraversion', 0.5))
        c = traits.get('C', traits.get('patience', 0.5))
        d = traits.get('D', traits.get('formality', 0.5))

        # Normalize to 0-1
        a_norm = min(max(a / 100, 0.0), 1.0) if a > 10 else a
        b_norm = min(max(b / 100, 0.0), 1.0) if b > 10 else b
        c_norm = min(max(c / 100, 0.0), 1.0) if c > 10 else c
        d_norm = min(max(d / 100, 0.0), 1.0) if d > 10 else d

        return {
            'extraversion': (b_norm + a_norm * 0.3) / 1.3,
            'conscientiousness': (d_norm + (1 - a_norm) * 0.3 + (1 - b_norm) * 0.2) / 1.5,
            'openness': ((1 - c_norm) + d_norm * 0.2) / 1.2,
            'agreeableness': ((1 - a_norm) + c_norm * 0.3 + d_norm * 0.2) / 1.5,
            'neuroticism': (a_norm * 0.3 + b_norm * 0.2) / 0.5
        }

    def _strengths_to_big_five(self, traits: Dict) -> Dict[str, float]:
        """Convert Clifton Strengths to Big Five approximation"""
        strengths = traits.get('strengths', [])

        # Strength categories and their Big Five correlations
        strength_mappings = {
            'executing': {
                'achiever': {'conscientiousness': 0.8, 'extraversion': 0.6},
                'activator': {'extraversion': 0.9, 'conscientiousness': 0.7},
                'adaptability': {'openness': 0.8, 'neuroticism': -0.2},
                'arranger': {'extraversion': 0.7, 'agreeableness': 0.6},
                'belief': {'conscientiousness': 0.9, 'agreeableness': 0.7},
                'consistency': {'conscientiousness': 0.9, 'neuroticism': -0.3},
                'deliberative': {'conscientiousness': 0.8, 'neuroticism': -0.4},
                'discipline': {'conscientiousness': 0.9, 'neuroticism': -0.3},
                'focus': {'conscientiousness': 0.8, 'neuroticism': -0.2},
                'responsibility': {'conscientiousness': 0.9, 'agreeableness': 0.8},
                'restorative': {'conscientiousness': 0.7, 'openness': 0.6}
            },
            'influencing': {
                'command': {'extraversion': 0.9, 'agreeableness': 0.3},
                'communication': {'extraversion': 0.8, 'agreeableness': 0.7},
                'competition': {'extraversion': 0.7, 'agreeableness': 0.4},
                'connectedness': {'agreeableness': 0.8, 'extraversion': 0.6},
                'developer': {'agreeableness': 0.9, 'extraversion': 0.5},
                'empathy': {'agreeableness': 0.9, 'neuroticism': -0.3},
                'harmony': {'agreeableness': 0.9, 'neuroticism': -0.4},
                'ideation': {'openness': 0.9, 'extraversion': 0.6},
                'maximizer': {'openness': 0.8, 'conscientiousness': 0.6},
                'positivity': {'extraversion': 0.8, 'neuroticism': -0.6},
                'relator': {'agreeableness': 0.8, 'extraversion': 0.5},
                'self_assurance': {'extraversion': 0.7, 'neuroticism': -0.5},
                'significance': {'extraversion': 0.6, 'conscientiousness': 0.4},
                'woo': {'extraversion': 0.9, 'agreeableness': 0.7}
            },
            'relationship_building': {
                # Already included above
            },
            'strategic_thinking': {
                'analytical': {'openness': 0.7, 'conscientiousness': 0.7},
                'context': {'openness': 0.8, 'conscientiousness': 0.5},
                'futuristic': {'openness': 0.9, 'conscientiousness': 0.6},
                'ideation': {'openness': 0.9, 'extraversion': 0.6},  # Also in influencing
                'input': {'openness': 0.8, 'conscientiousness': 0.6},
                'intellection': {'openness': 0.9, 'neuroticism': 0.2},
                'learner': {'openness': 0.8, 'conscientiousness': 0.7},
                'strategic': {'openness': 0.8, 'conscientiousness': 0.7}
            }
        }

        # Start with neutral scores
        result = {dim: 0.5 for dim in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']}

        # Apply strength contributions
        for strength in strengths:
            strength_lower = strength.lower()
            for category, strength_traits in strength_mappings.items():
                if strength_lower in strength_traits:
                    for dim, value in strength_traits[strength_lower].items():
                        if value > 0:
                            result[dim] = min(result[dim] + value * 0.1, 1.0)
                        else:
                            result[dim] = max(result[dim] + value * 0.1, 0.0)

        return result

    def _normalize_raw(self, traits: Dict) -> Dict[str, float]:
        """Normalize raw trait data"""
        result = {}

        for key, value in traits.items():
            if isinstance(value, (int, float)):
                # Normalize different scales
                if value > 100:  # Very large scale
                    normalized = 0.5 + (value - 50) / 200
                elif value > 10:  # 1-100 scale
                    normalized = value / 100
                elif value > 5:  # 1-10 scale
                    normalized = value / 10
                elif value >= 0:  # 0-1 or 1-5 scale
                    if value <= 1:
                        normalized = value
                    else:
                        normalized = (value - 1) / 4
                else:  # Negative values
                    normalized = max(0.0, min(1.0, 0.5 + value / 10))

                result[key] = min(max(normalized, 0.0), 1.0)
            else:
                result[key] = 0.5

        return result

    def _ensure_range(self, traits: Dict[str, float]) -> Dict[str, float]:
        """Ensure all trait values are in 0-1 range"""
        return {k: max(0.0, min(1.0, float(v))) for k, v in traits.items()}

    def _get_default_traits(self) -> Dict[str, float]:
        """Return default neutral traits"""
        return {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }

    def calculate_compatibility(self, traits_a: Dict[str, float], traits_b: Dict[str, float]) -> float:
        """
        Calculate personality compatibility between two trait sets

        Args:
            traits_a: First person's traits (Big Five format)
            traits_b: Second person's traits (Big Five format)

        Returns:
            Compatibility score (0-1)
        """
        try:
            big_five_dims = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            compatibility_scores = []

            for dim in big_five_dims:
                a_val = traits_a.get(dim, 0.5)
                b_val = traits_b.get(dim, 0.5)

                if dim == 'neuroticism':
                    # Lower neuroticism is generally better
                    compatibility = 1.0 - abs(a_val - b_val)
                else:
                    # For other traits, moderate similarity is optimal
                    diff = abs(a_val - b_val)
                    if diff < 0.2:  # Very similar
                        compatibility = 0.8
                    elif diff < 0.4:  # Moderately similar
                        compatibility = 1.0
                    else:  # Different (can be complementary)
                        compatibility = max(0.4, 1.0 - diff)

                compatibility_scores.append(compatibility)

            return np.mean(compatibility_scores)

        except Exception as e:
            logger.error(f"Error calculating compatibility: {str(e)}")
            return 0.5

    def get_compatibility_insights(self, traits_a: Dict[str, float], traits_b: Dict[str, float]) -> List[str]:
        """Generate insights about personality compatibility"""
        insights = []

        big_five_labels = {
            'openness': 'Openness to Experience',
            'conscientiousness': 'Conscientiousness',
            'extraversion': 'Extraversion',
            'agreeableness': 'Agreeableness',
            'neuroticism': 'Emotional Stability'
        }

        for dim, label in big_five_labels.items():
            a_val = traits_a.get(dim, 0.5)
            b_val = traits_b.get(dim, 0.5)
            diff = abs(a_val - b_val)

            if dim == 'neuroticism':
                if a_val < 0.3 and b_val < 0.3:
                    insights.append(f"Both are emotionally stable ({label})")
                elif a_val > 0.7 or b_val > 0.7:
                    insights.append(f"One or both may experience emotional challenges")
            else:
                if diff < 0.2:
                    insights.append(f"Similar {label} levels")
                elif diff > 0.6:
                    insights.append(f"Different {label} levels - potential for balance")

        return insights

# Singleton instance
personality_mapper = PersonalityMapper()

def map_traits(raw_traits: dict, framework: str = "raw") -> dict:
    """
    Convenience function for trait mapping

    Args:
        raw_traits: Raw trait data
        framework: Source framework

    Returns:
        Normalized traits in Big Five format
    """
    return personality_mapper.map_traits(raw_traits, framework)