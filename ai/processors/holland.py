# ai/processors/holland.py - Holland Code (RIASEC) Processor

from typing import Any, Dict, List

from ai.processors.processors_base import PersonalityFrameworkProcessor


# Big Five -> RIASEC mapping weights
RIASEC_MAPPINGS: Dict[str, Dict[str, float]] = {
    "realistic": {
        "openness": -0.10,
        "conscientiousness": 0.20,
        "extraversion": -0.10,
        "agreeableness": -0.15,
        "neuroticism": -0.10,
    },
    "investigative": {
        "openness": 0.35,
        "conscientiousness": 0.15,
        "extraversion": -0.20,
        "agreeableness": -0.05,
        "neuroticism": -0.05,
    },
    "artistic": {
        "openness": 0.45,
        "conscientiousness": -0.15,
        "extraversion": 0.05,
        "agreeableness": 0.05,
        "neuroticism": 0.10,
    },
    "social": {
        "openness": 0.10,
        "conscientiousness": 0.05,
        "extraversion": 0.30,
        "agreeableness": 0.35,
        "neuroticism": -0.05,
    },
    "enterprising": {
        "openness": 0.05,
        "conscientiousness": 0.10,
        "extraversion": 0.35,
        "agreeableness": -0.15,
        "neuroticism": -0.15,
    },
    "conventional": {
        "openness": -0.20,
        "conscientiousness": 0.40,
        "extraversion": -0.05,
        "agreeableness": 0.05,
        "neuroticism": -0.05,
    },
}

TYPE_DESCRIPTIONS = {
    "realistic": "Practical, hands-on problem solvers who prefer working with things",
    "investigative": "Analytical thinkers who enjoy research and complex problem solving",
    "artistic": "Creative individuals who value self-expression and originality",
    "social": "Helpers and educators who thrive in cooperative environments",
    "enterprising": "Persuasive leaders who enjoy organizing and directing others",
    "conventional": "Detail-oriented organizers who value structure and accuracy",
}

# Environment fit for each type
ENVIRONMENT_FIT = {
    "realistic": ["engineering", "operations", "devops", "infrastructure", "QA"],
    "investigative": [
        "data_science",
        "research",
        "backend",
        "security",
        "architecture",
    ],
    "artistic": ["design", "UX", "frontend", "content", "branding"],
    "social": ["HR", "people_ops", "coaching", "support", "community"],
    "enterprising": ["management", "sales", "product", "strategy", "leadership"],
    "conventional": [
        "finance",
        "compliance",
        "project_management",
        "admin",
        "analytics",
    ],
}

# Adjacent types on the hexagon have more compatibility
HEXAGON_ORDER = [
    "realistic",
    "investigative",
    "artistic",
    "social",
    "enterprising",
    "conventional",
]


class HollandProcessor(PersonalityFrameworkProcessor):
    """Process assessments into Holland Code (RIASEC) vocational profiles"""

    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._fallback_result("holland", "Invalid input data")

        try:
            if "riasec" in raw_data:
                type_scores = self._process_direct_riasec(raw_data["riasec"])
            else:
                type_scores = self._derive_from_big_five(raw_data)

            sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
            holland_code = "".join(t[0][0].upper() for t in sorted_types[:3])

            return {
                "dimensions": self._map_to_big_five(type_scores),
                "type_scores": {k: round(v, 3) for k, v in type_scores.items()},
                "holland_code": holland_code,
                "dominant_type": sorted_types[0][0],
                "dominant_score": round(sorted_types[0][1], 3),
                "type_profile": self._build_profile(sorted_types),
                "environment_fit": self._get_environment_fit(sorted_types[:3]),
                "consistency": self._compute_consistency(sorted_types),
                "differentiation": self._compute_differentiation(sorted_types),
                "confidence": self._safe_get(raw_data, "confidence", 0.8),
            }

        except Exception as e:
            return self._fallback_result("holland", str(e))

    def _process_direct_riasec(self, riasec: Dict[str, Any]) -> Dict[str, float]:
        result = {}
        for type_name in RIASEC_MAPPINGS:
            value = self._safe_get(riasec, type_name, 0.5)
            result[type_name] = self._clamp_value(float(value))
        return result

    def _derive_from_big_five(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        big_five = {
            "openness": float(self._safe_get(raw_data, "openness", 0.5)),
            "conscientiousness": float(
                self._safe_get(raw_data, "conscientiousness", 0.5)
            ),
            "extraversion": float(self._safe_get(raw_data, "extraversion", 0.5)),
            "agreeableness": float(self._safe_get(raw_data, "agreeableness", 0.5)),
            "neuroticism": float(self._safe_get(raw_data, "neuroticism", 0.5)),
        }

        type_scores = {}
        for type_name, weights in RIASEC_MAPPINGS.items():
            score = 0.5
            for trait, weight in weights.items():
                score += weight * (big_five.get(trait, 0.5) - 0.5)
            type_scores[type_name] = self._clamp_value(score)

        return type_scores

    def _map_to_big_five(self, type_scores: Dict[str, float]) -> Dict[str, float]:
        big_five = {
            t: 0.0
            for t in [
                "openness",
                "conscientiousness",
                "extraversion",
                "agreeableness",
                "neuroticism",
            ]
        }
        total_weight = 0.0
        for type_name, type_val in type_scores.items():
            weights = RIASEC_MAPPINGS.get(type_name, {})
            for trait, w in weights.items():
                if w > 0:
                    big_five[trait] += type_val * abs(w)
                    total_weight += abs(w)

        if total_weight > 0:
            for t in big_five:
                big_five[t] = self._clamp_value(big_five[t] / (total_weight / 5))

        return big_five

    def _build_profile(self, sorted_types: list) -> List[Dict[str, Any]]:
        return [
            {
                "type": name,
                "score": round(score, 3),
                "level": (
                    "dominant"
                    if i < 1
                    else (
                        "strong"
                        if score > 0.6
                        else "moderate" if score > 0.4 else "low"
                    )
                ),
                "description": TYPE_DESCRIPTIONS.get(name, ""),
                "environments": ENVIRONMENT_FIT.get(name, []),
            }
            for i, (name, score) in enumerate(sorted_types)
        ]

    def _get_environment_fit(self, top_types: list) -> List[str]:
        """Get combined environment fit from top 3 types."""
        envs = []
        for type_name, _ in top_types:
            envs.extend(ENVIRONMENT_FIT.get(type_name, []))
        return list(dict.fromkeys(envs))  # dedupe preserving order

    def _compute_consistency(self, sorted_types: list) -> float:
        """Consistency = how adjacent the top 2 types are on the hexagon.
        Adjacent types (distance 1) = high consistency, opposite (distance 3) = low."""
        if len(sorted_types) < 2:
            return 1.0
        t1, t2 = sorted_types[0][0], sorted_types[1][0]
        i1 = HEXAGON_ORDER.index(t1) if t1 in HEXAGON_ORDER else 0
        i2 = HEXAGON_ORDER.index(t2) if t2 in HEXAGON_ORDER else 0
        distance = min(abs(i1 - i2), 6 - abs(i1 - i2))
        return round(max(0, 1.0 - (distance - 1) * 0.3), 3)

    def _compute_differentiation(self, sorted_types: list) -> float:
        """Differentiation = spread between highest and lowest scores.
        Higher = clearer vocational identity."""
        if len(sorted_types) < 2:
            return 0.5
        return round(sorted_types[0][1] - sorted_types[-1][1], 3)

    def _default_dimensions(self) -> Dict[str, float]:
        return {t: 0.5 for t in RIASEC_MAPPINGS}
