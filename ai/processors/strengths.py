
# app/ai/processors/strengths.py - StrengthsFinder Processor

from typing import Dict, Any, List
from ai.processors.base import PersonalityFrameworkProcessor


class StrengthsProcessor(PersonalityFrameworkProcessor):
    """Process StrengthsFinder assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw StrengthsFinder data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('strengths', 'Invalid input data')
        
        try:
            top_themes = self._safe_get(raw_data, 'top_themes', [])[:5]  # Top 5 themes
            theme_scores = self._safe_get(raw_data, 'theme_scores', {})
            
            return {
                'top_themes': top_themes,
                'theme_scores': theme_scores,
                'confidence': self._safe_get(raw_data, 'confidence', 0.8),
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
            'Learner': 'A great desire to learn and continuously improve',
            'Communication': 'The ability to put thoughts into words and motivate others',
            'Empathy': 'The ability to sense the feelings of other people',
            'Focus': 'The ability to take direction and follow through',
            'Responsibility': 'Taking psychological ownership for commitments',
            'Relator': 'Enjoying close relationships with others'
        }
        return {theme: descriptions.get(theme, 'Strength theme') for theme in themes}
    
    def _get_domain_distribution(self, themes: List[str]) -> Dict[str, int]:
        """Get distribution across CliftonStrengths domains"""
        domain_mapping = {
            'Achiever': 'Executing', 'Activator': 'Influencing', 'Arranger': 'Executing',
            'Analytical': 'Strategic Thinking', 'Strategic': 'Strategic Thinking',
            'Learner': 'Strategic Thinking', 'Communication': 'Influencing',
            'Empathy': 'Relationship Building', 'Focus': 'Executing',
            'Responsibility': 'Executing', 'Relator': 'Relationship Building'
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
        if 'Communication' in themes:
            contributions.append("Clear communication and motivation")
        if 'Empathy' in themes:
            contributions.append("Understanding team dynamics")
        
        return contributions if contributions else ["Unique perspective and skills"]
    
    def _get_development_suggestions(self, themes: List[str]) -> List[str]:
        """Get development suggestions based on themes"""
        if not themes:
            return ["Complete assessment to get personalized suggestions"]
        
        return [
            f"Develop your {themes[0]} theme further",
            "Find ways to use your strengths in new situations",
            "Partner with others who have complementary strengths"
        ]
