"""
Relationship Analysis Service
Analyzes interpersonal dynamics and compatibility between team members using
advanced psychometric principles and behavioral analytics.

Key Features:
- Pairwise compatibility analysis using Big Five traits
- Communication style matching based on personality profiles
- Team network metrics and cohesion analysis
- Conflict prediction and mitigation strategies
- Relationship strength scoring with multiple dimensions
- Synergy identification for high-performing pairs
- Diversity assessment for optimal team composition
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

class RelationshipType(Enum):
    """Types of relationship dynamics to analyze."""
    COMPATIBILITY = "compatibility"
    COMMUNICATION = "communication"
    COLLABORATION = "collaboration"
    CONFLICT = "conflict"
    SYNERGY = "synergy"
    MENTORSHIP = "mentorship"

class CompatibilityLevel(Enum):
    """Compatibility classification levels."""
    EXCELLENT = "excellent"      # 0.8 - 1.0
    GOOD = "good"               # 0.6 - 0.8
    MODERATE = "moderate"         # 0.4 - 0.6
    CHALLENGING = "challenging"   # 0.2 - 0.4
    POOR = "poor"               # 0.0 - 0.2

@dataclass
class PersonalityProfile:
    """Standardized personality profile for analysis."""
    user_id: str
    name: str
    traits: dict[str, float] = field(default_factory=dict)
    communication_style: str = "balanced"
    work_preferences: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    role: str = ""
    big_five: dict[str, float] | None = None

@dataclass
class RelationshipAnalysis:
    """Results of pairwise relationship analysis."""
    member_a_id: str
    member_b_id: str
    member_a_name: str
    member_b_name: str
    compatibility_score: float
    component_scores: dict[str, float]
    strengths: list[str]
    challenges: list[str]
    collaboration_potential: str
    conflict_probability: float
    synergy_score: float
    mentorship_potential: str
    communication_match: float
    work_style_compatibility: float

class RelationshipAnalyzer:
    """
    Advanced relationship analysis engine for team dynamics optimization.
    """

    def __init__(self):
        self.compatibility_weights = {
            "personality": 0.35,
            "communication_style": 0.25,
            "work_preferences": 0.20,
            "experience_level": 0.10,
            "skills_overlap": 0.10
        }
        self.communication_compatibility_matrix = self._initialize_communication_matrix()

    def _initialize_communication_matrix(self) -> dict[str, dict[str, float]]:
        """Initialize communication style compatibility matrix."""
        return {
            ("analytical", "analytical"): 0.85,
            ("analytical", "assertive"): 0.70,
            ("analytical", "collaborative"): 0.75,
            ("analytical", "supportive"): 0.80,
            ("assertive", "assertive"): 0.65,
            ("assertive", "collaborative"): 0.70,
            ("assertive", "supportive"): 0.55,
            ("collaborative", "collaborative"): 0.90,
            ("collaborative", "supportive"): 0.85,
            ("supportive", "supportive"): 0.80
        }

    def analyze_relationships(
        self,
        members: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Perform comprehensive relationship analysis

        Args:
            members: List of team member profiles

        Returns:
            Complete relationship analysis with scores and insights
        """
        if len(members) < 2:
            return self._empty_analysis()

        # Calculate pairwise relationships
        relationships = []
        conflict_pairs = []
        synergy_pairs = []

        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                analysis = self._analyze_pair(members[i], members[j])
                relationships.append(analysis)

                if analysis["compatibility_score"] < 0.4:
                    conflict_pairs.append(analysis)
                elif analysis["compatibility_score"] > 0.8:
                    synergy_pairs.append(analysis)

        # Calculate network metrics
        network_metrics = self._calculate_network_metrics(relationships)

        # Generate insights
        insights = self._generate_relationship_insights(
            relationships,
            conflict_pairs,
            synergy_pairs
        )

        return {
            "total_relationships": len(relationships),
            "relationships": relationships,
            "conflict_pairs": conflict_pairs,
            "synergy_pairs": synergy_pairs,
            "network_metrics": network_metrics,
            "insights": insights,
            "recommendations": self._generate_recommendations(
                conflict_pairs,
                network_metrics
            )
        }

    def _analyze_pair(
        self,
        member_a: dict[str, Any],
        member_b: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze relationship between two members"""

        # Personality compatibility
        personality_score = self._calculate_personality_compatibility(
            member_a.get("traits", {}),
            member_b.get("traits", {})
        )

        # Communication style compatibility
        comm_score = self._calculate_communication_compatibility(
            member_a.get("communication_style", "analytical"),
            member_b.get("communication_style", "analytical")
        )

        # Work preference alignment
        work_score = self._calculate_work_preference_alignment(
            member_a.get("work_preferences", []),
            member_b.get("work_preferences", [])
        )

        # Experience level compatibility
        exp_score = self._calculate_experience_compatibility(
            member_a.get("experience_years", 0),
            member_b.get("experience_years", 0)
        )

        # Skills overlap
        skills_score = self._calculate_skills_overlap(
            member_a.get("skills", []),
            member_b.get("skills", [])
        )

        # Weighted overall compatibility
        overall_compatibility = (
            personality_score * self.compatibility_weights["personality"] +
            comm_score * self.compatibility_weights["communication_style"] +
            work_score * self.compatibility_weights["work_preferences"] +
            exp_score * self.compatibility_weights["experience_level"] +
            skills_score * self.compatibility_weights["skills_overlap"]
        )

        # Identify strengths and challenges
        strengths = []
        challenges = []

        if personality_score > 0.7:
            strengths.append("Strong personality compatibility")
        elif personality_score < 0.4:
            challenges.append("Personality differences may cause friction")

        if comm_score > 0.7:
            strengths.append("Compatible communication styles")
        elif comm_score < 0.4:
            challenges.append("Different communication preferences")

        if skills_score > 0.5:
            strengths.append("Complementary skills for collaboration")
        elif skills_score < 0.2:
            challenges.append("Limited overlap in expertise")

        return {
            "member_a_id": member_a.get("id"),
            "member_a_name": member_a.get("name", "Unknown"),
            "member_b_id": member_b.get("id"),
            "member_b_name": member_b.get("name", "Unknown"),
            "compatibility_score": round(overall_compatibility, 3),
            "component_scores": {
                "personality": round(personality_score, 3),
                "communication": round(comm_score, 3),
                "work_preferences": round(work_score, 3),
                "experience": round(exp_score, 3),
                "skills": round(skills_score, 3)
            },
            "strengths": strengths,
            "challenges": challenges,
            "collaboration_potential": self._assess_collaboration_potential(
                overall_compatibility,
                skills_score
            )
        }

    def _calculate_personality_compatibility(
        self,
        traits_a: dict[str, float],
        traits_b: dict[str, float]
    ) -> float:
        """Calculate personality trait compatibility"""
        if not traits_a or not traits_b:
            return 0.5

        dimensions = ["openness", "conscientiousness", "extraversion",
                      "agreeableness", "neuroticism"]

        scores = []
        for dim in dimensions:
            val_a = traits_a.get(dim, 0.5)
            val_b = traits_b.get(dim, 0.5)

            # Different dimensions have different compatibility patterns
            if dim == "agreeableness":
                # High agreeableness in both is good
                score = (val_a + val_b) / 2
            elif dim == "neuroticism":
                # Low neuroticism in both is better
                score = 1.0 - ((val_a + val_b) / 2)
            elif dim == "conscientiousness":
                # Similar levels work well
                score = 1.0 - abs(val_a - val_b)
            else:
                # Moderate similarity for other traits
                similarity = 1.0 - abs(val_a - val_b)
                avg_level = (val_a + val_b) / 2
                score = (similarity * 0.6) + (avg_level * 0.4)

            scores.append(max(0.0, min(1.0, score)))

        return np.mean(scores)

    def _calculate_communication_compatibility(
        self,
        style_a: str,
        style_b: str
    ) -> float:
        """Calculate communication style compatibility"""
        # Make lookup symmetric
        pair = tuple(sorted([style_a, style_b]))
        return self.communication_compatibility_matrix.get(pair, 0.60)

    def _calculate_work_preference_alignment(
        self,
        prefs_a: list[str],
        prefs_b: list[str]
    ) -> float:
        """Calculate work preference alignment"""
        if not prefs_a or not prefs_b:
            return 0.5

        # Calculate Jaccard similarity
        set_a = set(prefs_a)
        set_b = set(prefs_b)

        intersection = len(set_a & set_b)
        union = len(set_a | set_b)

        if union == 0:
            return 0.5

        return intersection / union

    def _calculate_experience_compatibility(
        self,
        exp_a: float,
        exp_b: float
    ) -> float:
        """Calculate experience level compatibility"""
        # Some experience gap is beneficial (mentoring)
        # But too large a gap can be problematic
        gap = abs(exp_a - exp_b)

        if gap <= 2:
            return 1.0  # Very compatible
        if gap <= 5:
            return 0.8  # Good (mentoring opportunity)
        if gap <= 10:
            return 0.6  # Moderate
        return 0.4  # May have communication challenges

    def _calculate_skills_overlap(
        self,
        skills_a: list[str],
        skills_b: list[str]
    ) -> float:
        """Calculate skills overlap (for collaboration potential)"""
        if not skills_a or not skills_b:
            return 0.5

        # Some overlap is good, but complementary skills are also valuable
        set_a = set(skills_a)
        set_b = set(skills_b)

        overlap = len(set_a & set_b)
        total = len(set_a | set_b)

        if total == 0:
            return 0.5

        overlap_ratio = overlap / total

        # Optimal is moderate overlap (0.3-0.5)
        if 0.3 <= overlap_ratio <= 0.5:
            return 1.0
        if overlap_ratio < 0.3:
            return 0.5 + overlap_ratio  # Complementary skills
        return 1.5 - overlap_ratio  # Too much overlap

    def _assess_collaboration_potential(
        self,
        compatibility: float,
        skills_overlap: float
    ) -> str:
        """Assess overall collaboration potential"""
        if compatibility > 0.75 and skills_overlap > 0.4:
            return "Excellent collaboration potential"
        if compatibility > 0.6:
            return "Good collaboration potential"
        if compatibility > 0.4:
            return "Moderate collaboration potential with support"
        return "Challenging collaboration - requires structured support"

    def _calculate_network_metrics(
        self,
        relationships: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate team network metrics"""
        if not relationships:
            return {}

        compatibility_scores = [r["compatibility_score"] for r in relationships]

        return {
            "average_compatibility": np.mean(compatibility_scores),
            "median_compatibility": np.median(compatibility_scores),
            "min_compatibility": np.min(compatibility_scores),
            "max_compatibility": np.max(compatibility_scores),
            "std_compatibility": np.std(compatibility_scores),
            "cohesion_index": np.mean([s for s in compatibility_scores if s > 0.6]),
            "conflict_risk": len([s for s in compatibility_scores if s < 0.4]) / len(compatibility_scores)
        }

    def _generate_relationship_insights(
        self,
        relationships: list[dict],
        conflict_pairs: list[dict],
        synergy_pairs: list[dict]
    ) -> list[str]:
        """Generate actionable insights from relationship analysis"""
        insights = []

        if synergy_pairs:
            insights.append(
                f"Found {len(synergy_pairs)} high-synergy pairs - leverage these "
                "for critical project work and mentoring"
            )

        if conflict_pairs:
            insights.append(
                f"Identified {len(conflict_pairs)} potential conflict pairs - "
                "implement structured communication and regular check-ins"
            )

        # Analyze communication patterns
        comm_styles = {}
        for rel in relationships:
            for key in ["member_a_name", "member_b_name"]:
                # This is simplified - in production, track actual styles
                pass

        avg_compat = np.mean([r["compatibility_score"] for r in relationships])
        if avg_compat > 0.7:
            insights.append(
                "Team shows strong overall compatibility - focus on leveraging "
                "this for innovation and experimentation"
            )
        elif avg_compat < 0.5:
            insights.append(
                "Team compatibility is below optimal - consider team building "
                "activities and clearer communication protocols"
            )

        return insights

    def _generate_recommendations(
        self,
        conflict_pairs: list[dict],
        network_metrics: dict[str, float]
    ) -> list[dict[str, str]]:
        """Generate recommendations for improving team dynamics"""
        recommendations = []

        if conflict_pairs:
            recommendations.append({
                "type": "conflict_management",
                "priority": "high",
                "title": "Address Potential Conflicts",
                "description": f"Detected {len(conflict_pairs)} pairs with low compatibility",
                "actions": [
                    "Establish clear communication channels",
                    "Set explicit team norms and expectations",
                    "Implement regular team retrospectives",
                    "Consider conflict resolution training"
                ]
            })

        conflict_risk = network_metrics.get("conflict_risk", 0)
        if conflict_risk > 0.3:
            recommendations.append({
                "type": "team_structure",
                "priority": "medium",
                "title": "Optimize Team Structure",
                "description": "High conflict risk detected in current composition",
                "actions": [
                    "Consider sub-team restructuring",
                    "Rotate pair programming partners",
                    "Implement buddy system for support"
                ]
            })

        avg_compat = network_metrics.get("average_compatibility", 0.5)
        if avg_compat < 0.6:
            recommendations.append({
                "type": "team_building",
                "priority": "medium",
                "title": "Improve Team Cohesion",
                "description": "Team compatibility below optimal threshold",
                "actions": [
                    "Schedule regular team building activities",
                    "Create opportunities for informal interaction",
                    "Implement peer recognition programs"
                ]
            })

        return recommendations

    def _empty_analysis(self) -> dict[str, Any]:
        """Return empty analysis structure"""
        return {
            "total_relationships": 0,
            "relationships": [],
            "conflict_pairs": [],
            "synergy_pairs": [],
            "network_metrics": {},
            "insights": ["Insufficient data for relationship analysis"],
            "recommendations": []
        }
