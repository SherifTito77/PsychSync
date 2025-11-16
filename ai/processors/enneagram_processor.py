# app/ai/processors/enneagram.py - Enneagram Assessment Processor

from typing import Dict, Any, List
from ai.processors.base import PersonalityFrameworkProcessor


class EnneagramProcessor(PersonalityFrameworkProcessor):
    """Process Enneagram assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Enneagram data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('enneagram', 'Invalid input data')
        
        try:
            # Extract primary type
            primary_type = self._safe_get(raw_data, 'type', 1)
            confidence = self._safe_get(raw_data, 'confidence', 0.8)
            wing = self._safe_get(raw_data, 'wing', None)
            
            # Map to standardized personality dimensions
            type_mapping = self._get_enneagram_mapping()
            
            if primary_type in type_mapping:
                dimensions = type_mapping[primary_type].copy()
            else:
                dimensions = self._default_dimensions()
            
            # Adjust for wing influence if present
            if wing and isinstance(wing, str) and 'w' in wing:
                try:
                    wing_type = int(wing.split('w')[1])
                    if wing_type in type_mapping:
                        wing_dimensions = type_mapping[wing_type]
                        # Blend primary type with wing (30% wing influence)
                        for dim, value in wing_dimensions.items():
                            dimensions[dim] = dimensions[dim] * 0.7 + value * 0.3
                except (ValueError, IndexError):
                    pass  # Invalid wing format, ignore
            
            return {
                'type': primary_type,
                'wing': wing,
                'confidence': confidence,
                'dimensions': dimensions,
                'interpretation': self._get_type_interpretation(primary_type),
                'growth_areas': self._get_growth_areas(primary_type),
                'strengths': self._get_type_strengths(primary_type)
            }
            
        except Exception as e:
            return self._fallback_result('enneagram', str(e))
    
    def _get_enneagram_mapping(self) -> Dict[int, Dict[str, float]]:
        """Map Enneagram types to Big Five dimensions"""
        return {
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
    
    def _get_type_interpretation(self, type_num: int) -> str:
        """Get interpretation for Enneagram type"""
        interpretations = {
            1: "The Perfectionist - Rational, idealistic, principled, purposeful",
            2: "The Helper - Caring, interpersonal, demonstrative, generous",
            3: "The Achiever - Success-oriented, pragmatic, adaptive, driven",
            4: "The Individualist - Sensitive, withdrawn, expressive, dramatic",
            5: "The Investigator - Intense, cerebral, perceptive, innovative",
            6: "The Loyalist - Committed, security-oriented, engaging, responsible",
            7: "The Enthusiast - Spontaneous, versatile, distractible, scattered",
            8: "The Challenger - Self-confident, decisive, willful, confrontational",
            9: "The Peacemaker - Receptive, reassuring, agreeable, complacent"
        }
        return interpretations.get(type_num, "Unknown type")
    
    def _get_growth_areas(self, type_num: int) -> List[str]:
        """Get growth areas for each type"""
        growth_areas = {
            1: ["Perfectionism management", "Flexibility", "Self-compassion"],
            2: ["Self-care", "Boundary setting", "Authentic self-expression"],
            3: ["Work-life balance", "Authentic relationships", "Process over results"],
            4: ["Emotional regulation", "Practical focus", "Resilience building"],
            5: ["Social engagement", "Action orientation", "Emotional expression"],
            6: ["Self-trust", "Independent thinking", "Anxiety management"],
            7: ["Focus and commitment", "Depth over breadth", "Present-moment awareness"],
            8: ["Vulnerability", "Collaborative leadership", "Patience"],
            9: ["Initiative taking", "Conflict engagement", "Self-advocacy"]
        }
        return growth_areas.get(type_num, ["Self-awareness", "Personal growth"])
    
    def _get_type_strengths(self, type_num: int) -> List[str]:
        """Get strengths for each type"""
        strengths = {
            1: ["High standards", "Ethical behavior", "Continuous improvement"],
            2: ["Empathy", "Supportiveness", "Relationship building"],
            3: ["Goal achievement", "Adaptability", "Leadership"],
            4: ["Creativity", "Emotional depth", "Authenticity"],
            5: ["Analytical thinking", "Independence", "Innovation"],
            6: ["Loyalty", "Problem-solving", "Team collaboration"],
            7: ["Enthusiasm", "Versatility", "Optimism"],
            8: ["Leadership", "Decisiveness", "Protection of others"],
            9: ["Harmony creation", "Mediation", "Acceptance"]
        }
        return strengths.get(type_num, ["Unique perspective", "Personal insights"])