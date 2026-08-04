"""Big Five assessment processor."""

from __future__ import annotations

from typing import Any, Dict, List

from app.ai.models.processing_result import ProcessingResult

from .ai_processor_base import AIProcessor


class BigFiveProcessor(AIProcessor):
    """Process Big Five assessment results."""

    TRAITS = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
    ]

    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        if not isinstance(raw_data, dict) or not raw_data:
            return False

        responses = raw_data.get("responses", raw_data)
        if not isinstance(responses, dict):
            return False

        for trait in self.TRAITS:
            if trait not in responses:
                return False
            try:
                value = float(responses[trait])
            except (TypeError, ValueError):
                return False
            if not 0.0 <= value <= 1.0:
                return False

        return True

    def process(self, raw_data: Dict[str, Any]) -> ProcessingResult:
        if not isinstance(raw_data, dict) or not raw_data:
            return ProcessingResult.failure("big_five", ["Invalid input data"])

        responses = raw_data.get("responses", raw_data)
        if not isinstance(responses, dict):
            return ProcessingResult.failure("big_five", ["Responses must be a mapping"])

        if not self.validate_input(raw_data):
            return ProcessingResult.failure(
                "big_five", ["Missing or invalid Big Five traits"]
            )

        dimensions = {
            trait: self._clamp_value(float(responses[trait])) for trait in self.TRAITS
        }
        percentiles = {
            trait: round(value * 100, 1) for trait, value in dimensions.items()
        }
        strengths = self._identify_strengths(dimensions)
        development_areas = self._identify_development_areas(dimensions)

        data = {
            "dimensions": dimensions,
            "percentiles": percentiles,
            "interpretations": self._build_interpretations(dimensions),
            "strengths": strengths,
            "development_areas": development_areas,
        }

        return ProcessingResult.success(
            framework="big_five",
            data=data,
            confidence=self._calculate_confidence(dimensions),
        )

    def validate_output(self, output: Dict[str, Any]) -> bool:
        return "dimensions" in output and isinstance(output["dimensions"], dict)

    def get_confidence_score(self, output: Dict[str, Any]) -> float:
        return float(output.get("confidence", 0.0))

    def _clamp_value(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _calculate_confidence(self, dimensions: Dict[str, float]) -> float:
        spread = max(dimensions.values()) - min(dimensions.values())
        confidence = 0.55 + (1.0 - spread) * 0.4
        return round(min(confidence, 1.0), 2)

    def _identify_strengths(self, dimensions: Dict[str, float]) -> List[str]:
        strengths = []
        if dimensions["openness"] >= 0.7:
            strengths.append("openness for new ideas")
        if dimensions["conscientiousness"] >= 0.7:
            strengths.append("conscientiousness and follow-through")
        if dimensions["extraversion"] >= 0.7:
            strengths.append("extraversion and social energy")
        if dimensions["agreeableness"] >= 0.7:
            strengths.append("agreeableness and collaboration")
        if dimensions["neuroticism"] <= 0.3:
            strengths.append("emotional stability under pressure")
        return strengths or ["balanced personality profile"]

    def _identify_development_areas(self, dimensions: Dict[str, float]) -> List[str]:
        development = []
        if dimensions["openness"] <= 0.3:
            development.append("openness and experimentation")
        if dimensions["conscientiousness"] <= 0.3:
            development.append("organization and consistency")
        if dimensions["extraversion"] <= 0.3:
            development.append("social engagement and visibility")
        if dimensions["agreeableness"] <= 0.3:
            development.append("cooperation and empathy")
        if dimensions["neuroticism"] >= 0.7:
            development.append("emotional regulation and stress tolerance")
        return development or ["maintaining balanced trait expression"]

    def _build_interpretations(self, dimensions: Dict[str, float]) -> Dict[str, str]:
        return {
            "openness": (
                "High openness suggests creativity and curiosity."
                if dimensions["openness"] >= 0.7
                else "Lower openness suggests preference for familiar routines."
            ),
            "conscientiousness": (
                "High conscientiousness indicates strong organization and discipline."
                if dimensions["conscientiousness"] >= 0.7
                else "Lower conscientiousness indicates flexibility over structure."
            ),
            "extraversion": (
                "High extraversion indicates outgoing, energetic behavior."
                if dimensions["extraversion"] >= 0.7
                else "Lower extraversion indicates a quieter, more reserved style."
            ),
            "agreeableness": (
                "High agreeableness indicates trust and cooperation."
                if dimensions["agreeableness"] >= 0.7
                else "Lower agreeableness may indicate more direct or skeptical interaction."
            ),
            "neuroticism": (
                "Low neuroticism indicates emotional stability."
                if dimensions["neuroticism"] <= 0.3
                else "Higher neuroticism may indicate sensitivity to stress."
            ),
        }
