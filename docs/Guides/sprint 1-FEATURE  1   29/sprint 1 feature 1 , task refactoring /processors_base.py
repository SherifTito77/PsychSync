# app/ai/processors/base.py - Base Personality Framework Processor

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PersonalityFrameworkProcessor(ABC):
    """Base class for personality framework processors"""
    
    def _fallback_result(self, framework: str, error: str) -> Dict[str, Any]:
        """Fallback result when processing fails"""
        logger.error(f"Processing error in {framework}: {error}")
        return {
            'error': f"Failed to process {framework}: {error}",
            'confidence': 0.1,
            'dimensions': self._default_dimensions(),
            'framework': framework,
            'processed_at': None
        }
    
    def _ensure_confidence(self, data: Dict[str, Any], default: float = 0.8) -> Dict[str, Any]:
        """Ensure result has confidence score"""
        if 'confidence' not in data:
            data['confidence'] = default
        return data
    
    def _clamp_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to specified range"""
        return max(min_val, min(max_val, float(value)))
    
    def _safe_get(self, data: Dict, key: str, default: Any = None) -> Any:
        """Safely get value from dictionary with default"""
        try:
            return data.get(key, default)
        except (AttributeError, KeyError):
            return default_init__(self):
        self.framework_name = self.__class__.__name__.replace('Processor', '').lower()
    
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw assessment data into standardized format
        
        Args:
            raw_data: Raw assessment results from the framework
            
        Returns:
            Processed and standardized results
        """
        pass
    
    def _validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate input data structure"""
        return isinstance(raw_data, dict) and raw_data
    
    def _default_dimensions(self) -> Dict[str, float]:
        """Default Big Five dimensions when mapping fails"""
        return {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
    
    def _