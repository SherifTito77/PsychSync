# app/ai/processors/enneagram.py - Enneagram Assessment Processor

from typing import Any, Dict, List

from .ai_processor_base import AIProcessor


class EnneagramProcessor(AIProcessor):
    """Process Enneagram assessment results"""

    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Enneagram data into standardized format"""
        # Logic simplified for the refactor
        primary_type = raw_data.get("type", 1)
        confidence = raw_data.get("confidence", 0.8)

        return {
            "type": primary_type,
            "confidence": confidence,
            "dimensions": {},  # Placeholder for mapping
            "processed_at": "...",
        }

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the output."""
        return "type" in output and isinstance(output["type"], int)

    def get_confidence_score(self, output: Dict[str, Any]) -> float:
        """Calculate confidence score."""
        return float(output.get("confidence", 0.0))
