
# ai/processors/big_five.py - Big Five Processor

from typing import Dict, Any, List
from ai.processors.processors_base import PersonalityFrameworkProcessor, PsychSyncProcessorError

class BigFiveProcessor(PersonalityFrameworkProcessor):
    """Process Big Five assessment results"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Big Five data into standardized format"""
        if not self._validate_input(raw_data):
            return self._fallback_result('big_five', 'Invalid input data')
        
        try:
            dimensions = {}
            dimension_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            
            for dim in dimension_names:
                value = self._safe_get(raw_data, dim, 0.5)
                dimensions[dim] = self._clamp_value(float(value))
            
            return {
                'dimensions': dimensions,
                'confidence': self._safe_get(raw_data, 'confidence', 0.9),
                'interpretations': self._get_interpretations(dimensions),
                'percentiles': self._convert_to_percentiles(dimensions),
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
        """Identify personality strengths based on high scores"""
        strengths = []
        for dim, value in dimensions.items():
            if value > 0.7:
                strengths.append(f"High {dim.title()}")
        return strengths

    def _identify_development_areas(self, dimensions: Dict[str, float]) -> List[str]:
        """Identify development areas based on low scores"""
        areas = []
        for dim, value in dimensions.items():
            if value < 0.3:
                areas.append(f"Develop {dim.title()}")
        return areas
    