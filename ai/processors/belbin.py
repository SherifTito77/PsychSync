# ai/processors/belbin.py - Belbin Team Roles Processor

from typing import Any, Dict, List

from ai.processors.processors_base import PersonalityFrameworkProcessor


# Big Five -> Belbin role affinity weights
# Each role maps to a weighted combination of OCEAN traits
ROLE_MAPPINGS: Dict[str, Dict[str, float]] = {
    # Action-Oriented Roles
    "shaper": {
        "openness": 0.1,
        "conscientiousness": 0.15,
        "extraversion": 0.35,
        "agreeableness": -0.25,
        "neuroticism": -0.15,
    },
    "implementer": {
        "openness": -0.15,
        "conscientiousness": 0.40,
        "extraversion": 0.05,
        "agreeableness": 0.10,
        "neuroticism": -0.10,
    },
    "completer_finisher": {
        "openness": -0.10,
        "conscientiousness": 0.35,
        "extraversion": -0.15,
        "agreeableness": 0.05,
        "neuroticism": 0.15,
    },
    # People-Oriented Roles
    "coordinator": {
        "openness": 0.10,
        "conscientiousness": 0.15,
        "extraversion": 0.30,
        "agreeableness": 0.20,
        "neuroticism": -0.15,
    },
    "teamworker": {
        "openness": 0.05,
        "conscientiousness": 0.10,
        "extraversion": 0.15,
        "agreeableness": 0.40,
        "neuroticism": -0.10,
    },
    "resource_investigator": {
        "openness": 0.25,
        "conscientiousness": -0.05,
        "extraversion": 0.40,
        "agreeableness": 0.10,
        "neuroticism": -0.10,
    },
    # Thought-Oriented Roles
    "plant": {
        "openness": 0.45,
        "conscientiousness": -0.10,
        "extraversion": -0.10,
        "agreeableness": -0.05,
        "neuroticism": 0.10,
    },
    "monitor_evaluator": {
        "openness": 0.10,
        "conscientiousness": 0.20,
        "extraversion": -0.20,
        "agreeableness": -0.05,
        "neuroticism": -0.15,
    },
    "specialist": {
        "openness": 0.05,
        "conscientiousness": 0.30,
        "extraversion": -0.20,
        "agreeableness": 0.00,
        "neuroticism": 0.05,
    },
}

ROLE_CLUSTERS = {
    "action": ["shaper", "implementer", "completer_finisher"],
    "people": ["coordinator", "teamworker", "resource_investigator"],
    "thought": ["plant", "monitor_evaluator", "specialist"],
}

ROLE_DESCRIPTIONS = {
    "shaper": "Drives the team forward, challenges complacency",
    "implementer": "Turns concepts and plans into practical actions",
    "completer_finisher": "Ensures thoroughness and attention to detail",
    "coordinator": "Clarifies goals, delegates effectively",
    "teamworker": "Builds cooperation, diffuses friction",
    "resource_investigator": "Explores opportunities, develops contacts",
    "plant": "Generates creative ideas and novel solutions",
    "monitor_evaluator": "Provides logical, impartial judgments",
    "specialist": "Provides in-depth knowledge in key areas",
}


class BelbinProcessor(PersonalityFrameworkProcessor):
    """Process assessments into Belbin Team Role profiles"""

    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._fallback_result("belbin", "Invalid input data")

        try:
            # Accept either direct role scores or Big Five traits to derive roles
            if "roles" in raw_data:
                role_scores = self._process_direct_roles(raw_data["roles"])
            else:
                role_scores = self._derive_from_big_five(raw_data)

            sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
            dominant = sorted_roles[0]
            secondary = sorted_roles[1] if len(sorted_roles) > 1 else None

            cluster_scores = {}
            for cluster_name, cluster_roles in ROLE_CLUSTERS.items():
                cluster_scores[cluster_name] = round(
                    sum(role_scores.get(r, 0) for r in cluster_roles)
                    / len(cluster_roles),
                    3,
                )

            return {
                "dimensions": self._map_to_big_five(role_scores),
                "role_scores": {k: round(v, 3) for k, v in role_scores.items()},
                "dominant_role": dominant[0],
                "dominant_score": round(dominant[1], 3),
                "secondary_role": secondary[0] if secondary else None,
                "secondary_score": round(secondary[1], 3) if secondary else None,
                "cluster_scores": cluster_scores,
                "role_profile": self._build_profile(sorted_roles),
                "team_contribution": ROLE_DESCRIPTIONS.get(dominant[0], ""),
                "confidence": self._safe_get(raw_data, "confidence", 0.8),
            }

        except Exception as e:
            return self._fallback_result("belbin", str(e))

    def _process_direct_roles(self, roles: Dict[str, Any]) -> Dict[str, float]:
        result = {}
        for role_name in ROLE_MAPPINGS:
            value = self._safe_get(roles, role_name, 0.5)
            result[role_name] = self._clamp_value(float(value))
        return result

    def _derive_from_big_five(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Derive Belbin role scores from Big Five traits."""
        big_five = {
            "openness": float(self._safe_get(raw_data, "openness", 0.5)),
            "conscientiousness": float(
                self._safe_get(raw_data, "conscientiousness", 0.5)
            ),
            "extraversion": float(self._safe_get(raw_data, "extraversion", 0.5)),
            "agreeableness": float(self._safe_get(raw_data, "agreeableness", 0.5)),
            "neuroticism": float(self._safe_get(raw_data, "neuroticism", 0.5)),
        }

        role_scores = {}
        for role_name, weights in ROLE_MAPPINGS.items():
            score = 0.5  # base
            for trait, weight in weights.items():
                trait_val = big_five.get(trait, 0.5)
                score += weight * (trait_val - 0.5)
            role_scores[role_name] = self._clamp_value(score)

        return role_scores

    def _map_to_big_five(self, role_scores: Dict[str, float]) -> Dict[str, float]:
        """Reverse-map Belbin roles back to Big Five for cross-framework synthesis."""
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
        for role_name, role_val in role_scores.items():
            weights = ROLE_MAPPINGS.get(role_name, {})
            for trait, w in weights.items():
                if w > 0:
                    big_five[trait] += role_val * abs(w)
                    total_weight += abs(w)

        if total_weight > 0:
            for t in big_five:
                big_five[t] = self._clamp_value(big_five[t] / (total_weight / 5))

        return big_five

    def _build_profile(self, sorted_roles: list) -> List[Dict[str, Any]]:
        return [
            {
                "role": name,
                "score": round(score, 3),
                "level": (
                    "dominant"
                    if i == 0
                    else (
                        "strong"
                        if score > 0.6
                        else "moderate" if score > 0.4 else "low"
                    )
                ),
                "cluster": next(
                    (c for c, roles in ROLE_CLUSTERS.items() if name in roles),
                    "unknown",
                ),
                "description": ROLE_DESCRIPTIONS.get(name, ""),
            }
            for i, (name, score) in enumerate(sorted_roles)
        ]

    def _default_dimensions(self) -> Dict[str, float]:
        return {r: 0.5 for r in ROLE_MAPPINGS}
