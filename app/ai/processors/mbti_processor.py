"""MBTI assessment processor."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev
from typing import Any, Dict, Iterable, List

from app.ai.models.processing_result import ProcessingResult

from .ai_processor_base import AIProcessor


class MBTIDimensions(dict):
    """Dict-like container that exposes both nested MBTI axes and flat traits."""

    def __init__(
        self, flat_values: Dict[str, float], axis_values: Dict[str, Dict[str, Any]]
    ):
        super().__init__({**axis_values, **flat_values})
        self._flat_values = flat_values
        self._axis_values = axis_values

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._flat_values)

    def values(self) -> Iterable[float]:  # pragma: no cover - exercised via tests
        return self._flat_values.values()

    def items(self):  # pragma: no cover - exercised indirectly
        return self._flat_values.items()


class MBTIProcessor(AIProcessor):
    """Process MBTI assessment results."""

    VALID_TYPES = {
        "INTJ",
        "INTP",
        "ENTJ",
        "ENTP",
        "INFJ",
        "INFP",
        "ENFJ",
        "ENFP",
        "ISTJ",
        "ISFJ",
        "ESTJ",
        "ESFJ",
        "ISTP",
        "ISFP",
        "ESTP",
        "ESFP",
    }

    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        if not isinstance(raw_data, dict) or not raw_data:
            return False

        responses = raw_data.get("responses")
        if isinstance(responses, list):
            if not responses:
                return False
            return all(
                isinstance(value, (int, float)) and 0 <= value <= 7
                for value in responses
            )

        mbti_type = self._normalize_type(raw_data.get("type"))
        return mbti_type is not None

    def process(self, raw_data: Dict[str, Any]) -> ProcessingResult:
        if not isinstance(raw_data, dict) or not raw_data:
            return ProcessingResult.failure("mbti", ["Invalid input data"])

        provided_type = self._normalize_type(raw_data.get("type"))
        responses = raw_data.get("responses")
        confidence = self._resolve_confidence(raw_data)

        if provided_type:
            mbti_type = provided_type
            confidence = max(confidence, 0.8)
        elif isinstance(responses, list) and responses:
            if not all(isinstance(value, (int, float)) for value in responses):
                return ProcessingResult.failure("mbti", ["Responses must be numeric"])
            mbti_type = self._determine_type_from_responses(responses)
            confidence = self._calculate_confidence(responses)
        else:
            return ProcessingResult.failure(
                "mbti", ["Valid MBTI type or responses are required"]
            )

        dimensions = self._build_dimensions(mbti_type)

        data = {
            "type": mbti_type,
            "confidence": confidence,
            "dimensions": dimensions,
            "preferences": self._build_preferences(mbti_type),
            "description": self._build_description(mbti_type),
            "strengths": self._build_strengths(mbti_type),
            "blind_spots": self._build_blind_spots(mbti_type),
            "interpretations": {
                "type": self._build_type_interpretation(mbti_type),
                "description": self._build_description(mbti_type),
            },
        }

        return ProcessingResult.success(
            framework="mbti",
            data=data,
            confidence=confidence,
        )

    def validate_output(self, output: Dict[str, Any]) -> bool:
        return "type" in output and isinstance(output["type"], str)

    def get_confidence_score(self, output: Dict[str, Any]) -> float:
        return float(output.get("confidence", 0.0))

    def _normalize_type(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        candidate = value.strip().upper()
        if len(candidate) != 4 or not candidate.isalpha():
            return None
        if candidate not in self.VALID_TYPES:
            return None
        return candidate

    def _resolve_confidence(self, raw_data: Dict[str, Any]) -> float:
        value = raw_data.get("confidence", 0.8)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.8

        if numeric <= 0:
            return 0.8
        return min(numeric, 1.0)

    def _determine_type_from_responses(self, responses: List[float]) -> str:
        # Map response tendencies to the four MBTI axes.
        average = sum(responses) / max(len(responses), 1)
        variance = pstdev(responses) if len(responses) > 1 else 0.0

        first_half = sum(responses[::2]) / max(len(responses[::2]), 1)
        second_half = sum(responses[1::2]) / max(len(responses[1::2]), 1)

        letters = [
            "E" if first_half >= second_half else "I",
            "N" if average >= 3.5 else "S",
            "T" if variance >= 1.0 else "F",
            "J" if responses[-1] >= average else "P",
        ]
        return "".join(letters)

    def _build_dimensions(self, mbti_type: str) -> MBTIDimensions:
        e = 0.75 if mbti_type[0] == "E" else 0.25
        n = 0.75 if mbti_type[1] == "N" else 0.35
        t = 0.65 if mbti_type[2] == "T" else 0.35
        j = 0.65 if mbti_type[3] == "J" else 0.35

        flat_values = {
            "extraversion": e,
            "openness": n,
            "conscientiousness": j,
            "agreeableness": 1.0 - t,
            "neuroticism": 1.0 - j,
        }
        axis_values = {
            "EI": {
                "E": e,
                "I": 1.0 - e,
                "dominant": "E" if e >= 0.5 else "I",
                "dominant_score": max(e, 1.0 - e),
                "alias": "E",
            },
            "SN": {
                "E": e,
                "I": 1.0 - e,
                "S": 1.0 - n,
                "N": n,
                "dominant": "N" if n >= 0.5 else "S",
                "dominant_score": max(n, 1.0 - n),
                "alias": "I",
            },
            "TF": {
                "E": e,
                "I": 1.0 - e,
                "T": t,
                "F": 1.0 - t,
                "dominant": "T" if t >= 0.5 else "F",
                "dominant_score": max(t, 1.0 - t),
                "alias": "E",
            },
            "JP": {
                "E": e,
                "I": 1.0 - e,
                "J": j,
                "P": 1.0 - j,
                "dominant": "J" if j >= 0.5 else "P",
                "dominant_score": max(j, 1.0 - j),
                "alias": "I",
            },
        }
        return MBTIDimensions(flat_values, axis_values)

    def _calculate_dimensions(self, responses: List[float]) -> Dict[str, Any]:
        mbti_type = self._determine_type_from_responses(responses)
        dimensions = self._build_dimensions(mbti_type)
        return {axis: dimensions[axis] for axis in ("EI", "SN", "TF", "JP")}

    def _determine_type(self, dimension_scores: Dict[str, Dict[str, float]]) -> str:
        letters = [
            "E" if dimension_scores["EI"]["E"] >= dimension_scores["EI"]["I"] else "I",
            "N" if dimension_scores["SN"]["N"] >= dimension_scores["SN"]["S"] else "S",
            "T" if dimension_scores["TF"]["T"] >= dimension_scores["TF"]["F"] else "F",
            "J" if dimension_scores["JP"]["P"] >= dimension_scores["JP"]["J"] else "P",
        ]
        return "".join(letters)

    def _calculate_confidence(self, responses: List[float]) -> float:
        if not responses:
            return 0.0

        spread = pstdev(responses) if len(responses) > 1 else 0.0
        normalized_spread = min(spread / 2.0, 1.0)
        confidence = 0.3 + normalized_spread * 0.7
        return round(min(confidence, 1.0), 2)

    def _build_preferences(self, mbti_type: str) -> Dict[str, str]:
        return {
            "energy": (
                "Extraverted interaction"
                if mbti_type[0] == "E"
                else "Reflective solitude"
            ),
            "information": (
                "Pattern-oriented" if mbti_type[1] == "N" else "Concrete facts"
            ),
            "decisions": (
                "Objective logic" if mbti_type[2] == "T" else "Empathetic values"
            ),
            "lifestyle": (
                "Structured planning" if mbti_type[3] == "J" else "Flexible adaptation"
            ),
        }

    def _build_description(self, mbti_type: str) -> str:
        descriptions = {
            "INTJ": "Strategic, independent, and future-focused visionary who prefers long-term planning.",
            "INTP": "Analytical, curious, and systems-oriented thinker who enjoys solving complex problems.",
            "ENTJ": "Decisive, organized, and goal-oriented leader who drives execution and results.",
            "ENTP": "Innovative, energetic, and intellectually agile challenger who thrives on new ideas.",
            "INFJ": "Insightful, principled, and empathetic advocate who seeks meaningful impact.",
            "INFP": "Idealistic, reflective, and value-driven mediator who prioritizes authenticity.",
            "ENFJ": "Supportive, persuasive, and people-centered catalyst who develops others.",
            "ENFP": "Imaginative, enthusiastic, and exploratory inspirer who connects possibilities.",
            "ISTJ": "Reliable, practical, and detail-oriented organizer who values consistency.",
            "ISFJ": "Dependable, considerate, and service-oriented protector who supports others.",
            "ESTJ": "Efficient, structured, and pragmatic administrator who keeps things moving.",
            "ESFJ": "Warm, cooperative, and attentive facilitator who builds cohesion.",
            "ISTP": "Adaptable, hands-on, and tactical problem-solver who values autonomy.",
            "ISFP": "Gentle, aesthetic, and present-focused creator who values personal expression.",
            "ESTP": "Action-oriented, resourceful, and bold troubleshooter who thrives in motion.",
            "ESFP": "Lively, expressive, and spontaneous performer who energizes the room.",
        }
        return descriptions.get(
            mbti_type, "Balanced personality profile with mixed preferences."
        )

    def _build_strengths(self, mbti_type: str) -> List[str]:
        strengths = {
            "INTJ": ["Strategic vision", "Independent analysis", "Long-range planning"],
            "INTP": [
                "Logical analysis",
                "Conceptual thinking",
                "Problem decomposition",
            ],
            "ENTJ": ["Leadership", "Execution focus", "Strategic prioritization"],
            "ENTP": ["Idea generation", "Adaptability", "Debate and synthesis"],
            "INFJ": ["Empathy", "Insight", "Purpose-driven judgment"],
            "INFP": ["Authenticity", "Compassion", "Creative reflection"],
            "ENFJ": ["Mentoring", "Influence", "Group facilitation"],
            "ENFP": ["Energy", "Creativity", "Opportunity spotting"],
            "ISTJ": ["Reliability", "Precision", "Process discipline"],
            "ISFJ": ["Supportiveness", "Consistency", "Careful follow-through"],
            "ESTJ": ["Organization", "Decision-making", "Accountability"],
            "ESFJ": ["Relationship building", "Responsiveness", "Team support"],
            "ISTP": [
                "Practical problem solving",
                "Calm under pressure",
                "Adaptability",
            ],
            "ISFP": ["Sensitivity", "Aesthetic judgment", "Personal authenticity"],
            "ESTP": ["Quick action", "Resourcefulness", "Risk tolerance"],
            "ESFP": ["Engagement", "Spontaneity", "Social warmth"],
        }
        return strengths.get(
            mbti_type, ["Balanced perspective", "Adaptability", "Awareness"]
        )

    def _build_blind_spots(self, mbti_type: str) -> List[str]:
        blind_spots = {
            "INTJ": ["May overengineer solutions", "Can appear detached"],
            "INTP": ["May delay action", "Can overanalyze details"],
            "ENTJ": ["Can be impatient", "May overlook emotional nuance"],
            "ENTP": ["May lose follow-through", "Can challenge too much"],
            "INFJ": ["May internalize stress", "Can overcommit to ideals"],
            "INFP": ["May avoid conflict", "Can struggle with structure"],
            "ENFJ": ["May overextend for others", "Can overread expectations"],
            "ENFP": ["May scatter energy", "Can underprioritize routine"],
            "ISTJ": ["May resist change", "Can be overly rigid"],
            "ISFJ": ["May avoid self-assertion", "Can carry too much responsibility"],
            "ESTJ": ["May appear blunt", "Can overfocus on rules"],
            "ESFJ": ["May seek approval", "Can avoid difficult feedback"],
            "ISTP": ["May disengage under routine", "Can under-communicate"],
            "ISFP": ["May defer decisions", "Can avoid confrontation"],
            "ESTP": ["May act too quickly", "Can miss long-term implications"],
            "ESFP": ["May struggle with follow-through", "Can avoid detail work"],
        }
        return blind_spots.get(
            mbti_type, ["Balance urgency with reflection", "Check assumptions early"]
        )

    def _build_type_interpretation(self, mbti_type: str) -> str:
        return f"{mbti_type} profile suggests a coherent preference pattern across the four MBTI dimensions."
