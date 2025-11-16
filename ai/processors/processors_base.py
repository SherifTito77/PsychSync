# ai/processors/processors_base.py - Base Personality Framework Processor

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class PsychSyncProcessorError(Exception):
    """Custom exception for AI processing errors"""

    def __init__(self, message: str, framework: str = None, error_code: str = None):
        self.message = message
        self.framework = framework
        self.error_code = error_code
        super().__init__(message)


class PersonalityFrameworkProcessor(ABC):
    """Base class for personality framework processors"""

    def __init__(self):
        self.framework_name = self.__class__.__name__.replace('Processor', '').lower()
        self.logger = logging.getLogger(f"{__name__}.{self.framework_name}")

    def _fallback_result(self, framework: str, error: str) -> Dict[str, Any]:
        """Fallback result when processing fails"""
        self.logger.error(f"Processing error in {framework}: {error}")
        return {
            'error': f"Failed to process {framework}: {error}",
            'confidence': 0.1,
            'dimensions': self._default_dimensions(),
            'framework': framework,
            'processed_at': datetime.utcnow().isoformat(),
            'fallback': True
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
        except (AttributeError, KeyError, TypeError):
            return default

    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw assessment data into standardized format

        Args:
            raw_data: Raw assessment results from the framework

        Returns:
            Processed and standardized results

        Raises:
            PsychSyncProcessorError: If processing fails
        """
        pass

    def _validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate input data structure"""
        return isinstance(raw_data, dict) and bool(raw_data)

    def _default_dimensions(self) -> Dict[str, float]:
        """Default Big Five dimensions when mapping fails"""
        return {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }

    def get_framework_info(self) -> Dict[str, Any]:
        """Get framework information"""
        return {
            'name': self.framework_name,
            'class_name': self.__class__.__name__,
            'description': self.__doc__ or f"{self.framework_name.title()} personality framework processor",
            'supported_dimensions': list(self._default_dimensions().keys()) if hasattr(self, '_default_dimensions') else []
        }

    def _safe_process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Safe processing with error handling"""
        try:
            if not self._validate_input(raw_data):
                return self._fallback_result(self.framework_name, 'Invalid input data')

            result = self.process(raw_data)
            result['framework'] = self.framework_name
            result['processed_at'] = datetime.utcnow().isoformat()
            result['success'] = True

            return self._ensure_confidence(result)

        except Exception as e:
            self.logger.error(f"Unexpected error in {self.framework_name}: {str(e)}")
            return self._fallback_result(self.framework_name, str(e))