from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProcessor(ABC):
    """
    Standard interface for all AI-based personality and behavioral processors.
    """

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the raw input data and return the structured result."""
        pass

    @abstractmethod
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the output against schema and hallucination checks."""
        pass

    @abstractmethod
    def get_confidence_score(self, output: Dict[str, Any]) -> float:
        """Calculate and return a confidence score (0.0 to 1.0)."""
        pass
