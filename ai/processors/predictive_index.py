
# app/ai/processors/predictive_index.py - Predictive Index Processor

from typing import Dict, Any, List
from ai.processors.base import PersonalityFrameworkProcessor


class PredictiveIndexProcessor(PersonalityFrameworkProcessor):
    """Process Predictive Index assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw PI data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('predictive_index', 'Invalid input data')
        
        try:
            dimensions = {
                'dominance': self._clamp_value(self._safe_get(raw_data, 'dominance', 0.5)),
                'extraversion': self._clamp_value(self._safe_get(raw_data, 'extraversion', 0.5)),
                'patience': self._clamp_value(self._safe_get(raw_data, 'patience', 0.5)),
                'formality': self._clamp_value(self._safe_get(raw_data, 'formality', 0.5))
            }
            
            # Convert to Big Five approximation
            big_five = self._pi_to_big_five(dimensions)
            
            return {
                'pi_dimensions': dimensions,
                'big_five_approximation': big_five,
                'confidence': self._safe_get(raw_data, 'confidence', 0.8),
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



