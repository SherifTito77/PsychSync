
# app/ai/processors/social_styles.py - Social Styles Processor

from typing import Dict, Any, List
from ai.processors.base import PersonalityFrameworkProcessor


class SocialStylesProcessor(PersonalityFrameworkProcessor):
    """Process Social Styles assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Social Styles data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('social_styles', 'Invalid input data')
        
        try:
            style = self._safe_get(raw_data, 'style', 'Analytical').title()
            assertiveness = self._clamp_value(self._safe_get(raw_data, 'assertiveness', 0.5))
            responsiveness = self._clamp_value(self._safe_get(raw_data, 'responsiveness', 0.5))
            
            return {
                'style': style,
                'assertiveness': assertiveness,
                'responsiveness': responsiveness,
                'confidence': self._safe_get(raw_data, 'confidence', 0.8),
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

