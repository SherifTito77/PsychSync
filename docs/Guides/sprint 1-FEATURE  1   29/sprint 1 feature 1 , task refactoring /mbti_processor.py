# app/ai/processors/mbti.py - MBTI Assessment Processor

from typing import Dict, Any, List
from app.ai.processors.base import PersonalityFrameworkProcessor


class MBTIProcessor(PersonalityFrameworkProcessor):
    """Process MBTI assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw MBTI data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('mbti', 'Invalid input data')
        
        try:
            mbti_type = self._safe_get(raw_data, 'type', 'INTJ').upper()
            confidence = self._safe_get(raw_data, 'confidence', 0.8)
            
            if not self._is_valid_mbti(mbti_type):
                mbti_type = 'INTJ'  # Default fallback
            
            # Map to Big Five dimensions
            dimensions = self._mbti_to_big_five(mbti_type)
            
            return {
                'type': mbti_type,
                'confidence': confidence,
                'dimensions': dimensions,
                'preferences': self._get_preferences(mbti_type),
                'description': self._get_type_description(mbti_type),
                'strengths': self._get_type_strengths(mbti_type),
                'blind_spots': self._get_blind_spots(mbti_type)
            }
            
        except Exception as e:
            return self._fallback_result('mbti', str(e))
    
    def _is_valid_mbti(self, mbti_type: str) -> bool:
        """Validate MBTI type format"""
        if len(mbti_type) != 4:
            return False
        return (mbti_type[0] in 'EI' and mbti_type[1] in 'SN' and 
                mbti_type[2] in 'TF' and mbti_type[3] in 'JP')
    
    def _mbti_to_big_five(self, mbti_type: str) -> Dict[str, float]:
        """Convert MBTI type to Big Five dimensions"""
        dimensions = self._default_dimensions()
        
        # Extraversion/Introversion
        dimensions['extraversion'] = 0.75 if mbti_type[0] == 'E' else 0.25
        
        # Sensing/Intuition -> Openness
        dimensions['openness'] = 0.75 if mbti_type[1] == 'N' else 0.35
        
        # Thinking/Feeling -> Agreeableness
        dimensions['agreeableness'] = 0.75 if mbti_type[2] == 'F' else 0.35
        
        # Judging/Perceiving -> Conscientiousness
        dimensions['conscientiousness'] = 0.75 if mbti_type[3] == 'J' else 0.35
        
        return dimensions
    
    def _get_preferences(self, mbti_type: str) -> Dict[str, str]:
        """Get preference descriptions"""
        return {
            'energy': 'Extraversion' if mbti_type[0] == 'E' else 'Introversion',
            'information': 'Sensing' if mbti_type[1] == 'S' else 'Intuition',
            'decisions': 'Thinking' if mbti_type[2] == 'T' else 'Feeling',
            'lifestyle': 'Judging' if mbti_type[3] == 'J' else 'Perceiving'
        }
    
    def _get_type_description(self, mbti_type: str) -> str:
        """Get type description"""
        descriptions = {
            'INTJ': "The Architect - Strategic, independent, and innovative",
            'INTP': "The Thinker - Logical, flexible, and adaptable",
            'ENTJ': "The Commander - Bold, imaginative, and strong-willed",
            'ENTP': "The Debater - Smart, curious, and playful",
            'INFJ': "The Advocate - Creative, insightful, and principled",
            'INFP': "The Mediator - Poetic, kind, and altruistic",
            'ENFJ': "The Protagonist - Charismatic, inspiring, and caring",
            'ENFP': "The Campaigner - Enthusiastic, creative, and sociable",
            'ISTJ': "The Logistician - Practical, fact-minded, and reliable",
            'ISFJ': "The Protector - Warm-hearted, conscientious, and cooperative",
            'ESTJ': "The Executive - Organized, practical, and results-oriented",
            'ESFJ': "The Consul - Caring, social, and community-minded",
            'ISTP': "The Virtuoso - Bold, practical, and experimental",
            'ISFP': "The Adventurer - Charming, sensitive, and artistic",
            'ESTP': "The Entrepreneur - Smart, energetic, and perceptive",
            'ESFP': "The Entertainer - Spontaneous, energetic, and enthusiastic"
        }
        return descriptions.get(mbti_type, "Unknown type")
    
    def _get_type_strengths(self, mbti_type: str) -> List[str]:
        """Get strengths for MBTI type"""
        strengths = {
            'INTJ': ["Strategic thinking", "Independence", "Vision"],
            'INTP': ["Logical analysis", "Flexibility", "Innovation"],
            'ENTJ': ["Leadership", "Strategic planning", "Efficiency"],
            'ENTP': ["Innovation", "Adaptability", "Enthusiasm"],
            'INFJ': ["Insight", "Empathy", "Vision"],
            'INFP': ["Authenticity", "Creativity", "Values-driven"],
            'ENFJ': ["Inspiring others", "Communication", "Empathy"],
            'ENFP': ["Enthusiasm", "Creativity", "People skills"],
            'ISTJ': ["Reliability", "Attention to detail", "Consistency"],
            'ISFJ': ["Supportiveness", "Loyalty", "Attention to others"],
            'ESTJ': ["Organization", "Leadership", "Practicality"],
            'ESFJ': ["Cooperation", "Harmony", "Service to others"],
            'ISTP': ["Problem-solving", "Adaptability", "Practicality"],
            'ISFP': ["Creativity", "Compassion", "Flexibility"],
            'ESTP': ["Action-orientation", "Adaptability", "Realism"],
            'ESFP': ["Enthusiasm", "People skills", "Spontaneity"]
        }
        return strengths.get(mbti_type, ["Balanced perspective"])
    
    def _get_blind_spots(self, mbti_type: str) -> List[str]:
        """Get potential blind spots for MBTI type"""
        blind_spots = {
            'INTJ': ["May overlook people factors", "Can be overly critical"],
            'INTP': ["May procrastinate", "Difficulty with routine tasks"],
            'ENTJ': ["May be too direct", "Impatience with inefficiency"],
            'ENTP': ["May jump between projects", "Difficulty with follow-through"],
            'INFJ': ["Perfectionism", "May avoid conflict"],
            'INFP': ["May be overly idealistic", "Difficulty with criticism"],
            'ENFJ': ["May neglect own needs", "Can be overly involved"],
            'ENFP': ["May lack follow-through", "Can be disorganized"],
            'ISTJ': ["Resistance to change", "May be inflexible"],
            'ISFJ': ["Difficulty saying no", "May avoid conflict"],
            'ESTJ': ["May be inflexible", "Can overlook feelings"],
            'ESFJ': ["Oversensitive to criticism", "May neglect own needs"],
            'ISTP': ["May seem detached", "Difficulty expressing emotions"],
            'ISFP': ["May avoid conflict", "Difficulty with deadlines"],
            'ESTP': ["May be impulsive", "Difficulty with long-term planning"],
            'ESFP': ["May avoid difficult conversations", "Can be disorganized"]
        }
        return blind_spots.get(mbti_type, ["Areas for development"])