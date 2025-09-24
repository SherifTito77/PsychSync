
# ai/processors/psychsync_assessment_processors.py

# ai/processors/psychsync_assessment_processors.py
from typing import Dict, Any, List
import numpy as np
from ai.engine import PersonalityFrameworkProcessor

class EnneagramProcessor(PersonalityFrameworkProcessor):
    """Process Enneagram assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Enneagram data into standardized format"""
        try:
            # Extract primary type
            primary_type = raw_data.get('type', 1)
            confidence = raw_data.get('confidence', 0.8)
            wing = raw_data.get('wing', None)
            
            # Map to standardized personality dimensions
            type_mapping = self._get_enneagram_mapping()
            
            if primary_type in type_mapping:
                dimensions = type_mapping[primary_type].copy()
            else:
                dimensions = self._default_dimensions()
            
            # Adjust for wing influence if present
            if wing and isinstance(wing, str) and 'w' in wing:
                wing_type = int(wing.split('w')[1])
                if wing_type in type_mapping:
                    wing_dimensions = type_mapping[wing_type]
                    # Blend primary type with wing (30% wing influence)
                    for dim, value in wing_dimensions.items():
                        dimensions[dim] = dimensions[dim] * 0.7 + value * 0.3
            
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
    
    def _default_dimensions(self) -> Dict[str, float]:
        """Default dimensions when type is unknown"""
        return {'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5, 'agreeableness': 0.5, 'neuroticism': 0.5}
    
    def _fallback_result(self, framework: str, error: str) -> Dict[str, Any]:
        """Fallback result when processing fails"""
        return {
            'error': f"Failed to process {framework}: {error}",
            'confidence': 0.1,
            'dimensions': self._default_dimensions()
        }


class MBTIProcessor(PersonalityFrameworkProcessor):
    """Process MBTI assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw MBTI data into standardized format"""
        try:
            mbti_type = raw_data.get('type', 'INTJ').upper()
            confidence = raw_data.get('confidence', 0.8)
            
            if len(mbti_type) != 4 or not self._is_valid_mbti(mbti_type):
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
        dimensions = {'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5, 'agreeableness': 0.5, 'neuroticism': 0.5}
        
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
        # Simplified - in reality you'd have detailed mappings
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
            'ENTP': ["May jump between projects", "Difficulty with follow-through"]
        }
        return blind_spots.get(mbti_type, ["Areas for development"])


class BigFiveProcessor(PersonalityFrameworkProcessor):
    """Process Big Five assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Big Five data into standardized format"""
        try:
            dimensions = {}
            dimension_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            
            for dim in dimension_names:
                value = raw_data.get(dim, 0.5)
                dimensions[dim] = max(0.0, min(1.0, float(value)))
            
            return {
                'dimensions': dimensions,
                'confidence': raw_data.get('confidence', 0.9),
                'interpretations': self._get_interpretations(dimensions),
                'percentiles': self._convert_to_percentiles(dimensions),
                'facets': raw_data.get('facets', {}),
                'strengths': self._identify_strengths(dimensions),
                'development_areas': self._identify_development_areas(dimensions)
            }
            
        except Exception as e:
            return self._fallback_result('big_five', str(e))
    
    def _get_interpretations(self, dimensions: Dict[str, float]) -> Dict[str, str]:
        """Get interpretations for each dimension"""
        interpretations = {}
        
        for dim, value in dimensions.items():
            if value > 0.7:
                level = "High"
            elif value > 0.3:
                level = "Moderate"
            else:
                level = "Low"
            
            interpretations[dim] = f"{level} {dim.title()}"
        
        return interpretations
    
    def _convert_to_percentiles(self, dimensions: Dict[str, float]) -> Dict[str, int]:
        """Convert raw scores to percentiles"""
        return {dim: int(value * 100) for dim, value in dimensions.items()}
    
    def _identify_strengths(self, dimensions: Dict[str, float]) -> List[str]:
        """Identify strengths based on Big Five scores"""
        strengths = []
        
        if dimensions.get('openness', 0.5) > 0.7:
            strengths.append("Creative and open to new experiences")
        if dimensions.get('conscientiousness', 0.5) > 0.7:
            strengths.append("Organized and goal-oriented")
        if dimensions.get('extraversion', 0.5) > 0.7:
            strengths.append("Energetic and socially confident")
        if dimensions.get('agreeableness', 0.5) > 0.7:
            strengths.append("Cooperative and trustworthy")
        if dimensions.get('neuroticism', 0.5) < 0.3:
            strengths.append("Emotionally stable and resilient")
        
        return strengths if strengths else ["Balanced personality profile"]
    
    def _identify_development_areas(self, dimensions: Dict[str, float]) -> List[str]:
        """Identify development areas based on Big Five scores"""
        areas = []
        
        if dimensions.get('conscientiousness', 0.5) < 0.3:
            areas.append("Organization and self-discipline")
        if dimensions.get('neuroticism', 0.5) > 0.7:
            areas.append("Stress management and emotional regulation")
        if dimensions.get('agreeableness', 0.5) < 0.3:
            areas.append("Collaboration and empathy")
        
        return areas


class PIProcessor(PersonalityFrameworkProcessor):
    """Process Predictive Index assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw PI data into standardized format"""
        try:
            dimensions = {
                'dominance': max(0.0, min(1.0, raw_data.get('dominance', 0.5))),
                'extraversion': max(0.0, min(1.0, raw_data.get('extraversion', 0.5))),
                'patience': max(0.0, min(1.0, raw_data.get('patience', 0.5))),
                'formality': max(0.0, min(1.0, raw_data.get('formality', 0.5)))
            }
            
            # Convert to Big Five approximation
            big_five = self._pi_to_big_five(dimensions)
            
            return {
                'pi_dimensions': dimensions,
                'big_five_approximation': big_five,
                'confidence': raw_data.get('confidence', 0.8),
                'behavioral_pattern': self._determine_pattern(dimensions),
                'work_style': self._determine_work_style(dimensions),
                'management_needs': self._determine_management_needs(dimensions)
            }
            
        except Exception as e:
            return self._fallback_result('predictive_index', str(e))
    
    def _pi_to_big_five(self, pi_dims: Dict[str, float]) -> Dict[str, float]:
        """Convert PI dimensions to Big Five approximation"""
        return {
            'openness': 0.5,  # PI doesn't directly measure this
            'conscientiousness': pi_dims['formality'],
            'extraversion': pi_dims['extraversion'],
            'agreeableness': 1.0 - pi_dims['dominance'],  # Inverse relationship
            'neuroticism': 1.0 - pi_dims['patience']  # Inverse relationship
        }
    
    def _determine_pattern(self, dimensions: Dict[str, float]) -> str:
        """Determine PI behavioral pattern"""
        # Simplified pattern recognition
        if dimensions['dominance'] > 0.7 and dimensions['extraversion'] > 0.7:
            return "Influencer"
        elif dimensions['dominance'] > 0.7 and dimensions['patience'] < 0.3:
            return "Dominant"
        elif dimensions['patience'] > 0.7 and dimensions['formality'] > 0.7:
            return "Steady"
        else:
            return "Balanced"
    
    def _determine_work_style(self, dimensions: Dict[str, float]) -> List[str]:
        """Determine work style preferences"""
        style = []
        
        if dimensions['dominance'] > 0.6:
            style.append("Results-oriented")
        if dimensions['extraversion'] > 0.6:
            style.append("People-focused")
        if dimensions['patience'] > 0.6:
            style.append("Process-oriented")
        if dimensions['formality'] > 0.6:
            style.append("Detail-oriented")
        
        return style if style else ["Adaptable"]
    
    def _determine_management_needs(self, dimensions: Dict[str, float]) -> List[str]:
        """Determine management and motivation needs"""
        needs = []
        
        if dimensions['dominance'] > 0.7:
            needs.append("Autonomy and challenges")
        if dimensions['extraversion'] > 0.7:
            needs.append("Social interaction and recognition")
        if dimensions['patience'] > 0.7:
            needs.append("Stability and clear processes")
        if dimensions['formality'] > 0.7:
            needs.append("Structure and detailed information")
        
        return needs if needs else ["Balanced approach"]


class StrengthsProcessor(PersonalityFrameworkProcessor):
    """Process StrengthsFinder assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw StrengthsFinder data into standardized format"""
        try:
            top_themes = raw_data.get('top_themes', [])[:5]  # Top 5 themes
            theme_scores = raw_data.get('theme_scores', {})
            
            return {
                'top_themes': top_themes,
                'theme_scores': theme_scores,
                'confidence': raw_data.get('confidence', 0.8),
                'theme_descriptions': self._get_theme_descriptions(top_themes),
                'domain_distribution': self._get_domain_distribution(top_themes),
                'team_contribution': self._get_team_contribution(top_themes),
                'development_suggestions': self._get_development_suggestions(top_themes)
            }
            
        except Exception as e:
            return self._fallback_result('strengths', str(e))
    
    def _get_theme_descriptions(self, themes: List[str]) -> Dict[str, str]:
        """Get descriptions for themes"""
        descriptions = {
            'Achiever': 'A constant need for achievement and productivity',
            'Activator': 'The ability to make things happen by turning thoughts into action',
            'Analytical': 'The search for reasons and causes',
            'Strategic': 'The ability to sort through the clutter and find the best route',
            'Learner': 'A great desire to learn and continuously improve'
            # Add more as needed
        }
        return {theme: descriptions.get(theme, 'Strength theme') for theme in themes}
    
    def _get_domain_distribution(self, themes: List[str]) -> Dict[str, int]:
        """Get distribution across CliftonStrengths domains"""
        domain_mapping = {
            'Achiever': 'Executing', 'Activator': 'Influencing',
            'Analytical': 'Strategic Thinking', 'Strategic': 'Strategic Thinking',
            'Learner': 'Strategic Thinking'
            # Add more mappings as needed
        }
        
        domains = {'Executing': 0, 'Influencing': 0, 'Relationship Building': 0, 'Strategic Thinking': 0}
        
        for theme in themes:
            domain = domain_mapping.get(theme, 'Strategic Thinking')
            domains[domain] += 1
        
        return domains
    
    def _get_team_contribution(self, themes: List[str]) -> List[str]:
        """Determine how this person contributes to team"""
        contributions = []
        
        if 'Strategic' in themes:
            contributions.append("Strategic planning and direction")
        if 'Activator' in themes:
            contributions.append("Getting things started and moving")
        if 'Learner' in themes:
            contributions.append("Continuous learning and improvement")
        
        return contributions if contributions else ["Unique perspective and skills"]
    
    def _get_development_suggestions(self, themes: List[str]) -> List[str]:
        """Get development suggestions based on themes"""
        return [
            f"Develop your {themes[0]} theme further",
            "Find ways to use your strengths in new situations",
            "Partner with others who have complementary strengths"
        ]


class SocialStylesProcessor(PersonalityFrameworkProcessor):
    """Process Social Styles assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Social Styles data into standardized format"""
        try:
            style = raw_data.get('style', 'Analytical').title()
            assertiveness = raw_data.get('assertiveness', 0.5)
            responsiveness = raw_data.get('responsiveness', 0.5)
            
            return {
                'style': style,
                'assertiveness': assertiveness,
                'responsiveness': responsiveness,
                'confidence': raw_data.get('confidence', 0.8),
                'description': self._get_style_description(style),
                'communication_preferences': self._get_communication_preferences(style),
                'interaction_tips': self._get_interaction_tips(style),
                'backup_behavior': self._get_backup_behavior(style)
            }
            
        except Exception as e:
            return self._fallback_result('social_styles', str(e))
    
    def _get_style_description(self, style: str) -> str:
        """Get description for social style"""
        descriptions = {
            'Driver': 'Results-oriented, decisive, and direct',
            'Expressive': 'People-oriented, enthusiastic, and spontaneous',
            'Amiable': 'Relationship-focused, supportive, and cooperative',
            'Analytical': 'Task-oriented, methodical, and precise'
        }
        return descriptions.get(style, 'Unknown style')
    
    def _get_communication_preferences(self, style: str) -> List[str]:
        """Get communication preferences for style"""
        preferences = {
            'Driver': ['Direct communication', 'Bottom-line focus', 'Time efficiency'],
            'Expressive': ['Enthusiastic interaction', 'Big picture focus', 'Social connection'],
            'Amiable': ['Supportive tone', 'Personal consideration', 'Consensus building'],
            'Analytical': ['Detailed information', 'Logical structure', 'Data-driven discussion']
        }
        return preferences.get(style, ['Clear communication'])
    
    def _get_interaction_tips(self, style: str) -> List[str]:
        """Get tips for interacting with this style"""
        tips = {
            'Driver': ['Be brief and direct', 'Focus on results', 'Avoid small talk'],
            'Expressive': ['Be enthusiastic', 'Allow for interaction', 'Focus on big picture'],
            'Amiable': ['Be patient and supportive', 'Build relationship first', 'Avoid pressure'],
            'Analytical': ['Provide detailed information', 'Be logical', 'Allow processing time']
        }
        return tips.get(style, ['Adapt communication style'])
    
    def _get_backup_behavior(self, style: str) -> str:
        """Get backup behavior under stress"""
        backups = {
            'Driver': 'Autocratic - becomes controlling and demanding',
            'Expressive': 'Attacking - becomes aggressive and critical',
            'Amiable': 'Acquiescing - becomes overly accommodating',
            'Analytical': 'Avoiding - withdraws and becomes indecisive'
        }
        return backups.get(style, 'Stress response varies')


