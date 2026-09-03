"""
Team Compatibility Analysis Service
Advanced algorithms for analyzing team member compatibility and optimization
"""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models.responses import UserAssessmentResponse
from app.db.models.team import Team
from app.db.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityScore:
    """Compatibility score between two team members"""

    user1_id: UUID
    user2_id: UUID
    overall_score: float
    personality_fit: float
    skills_complement: float
    work_style_match: float
    communication_match: float
    potential_conflicts: list[str]
    strengths: list[str]
    recommendations: list[str]


@dataclass
class TeamCompatibilityReport:
    """Comprehensive team compatibility analysis"""

    team_id: UUID
    overall_compatibility: float
    compatibility_matrix: dict[str, dict[str, float]]
    role_fit_scores: dict[str, float]
    team_balance_score: float
    diversity_metrics: dict[str, float]
    optimization_suggestions: list[str]
    risk_factors: list[str]


class TeamCompatibilityAnalysisService:
    """Advanced team compatibility analysis and optimization service"""

    def __init__(self, db: Session):
        self.db = db

        # Analysis weights
        self.weights = {
            "personality_fit": 0.3,
            "skills_complement": 0.25,
            "work_style_match": 0.2,
            "communication_match": 0.15,
            "cognitive_diversity": 0.1,
        }

        # Compatibility thresholds
        self.thresholds = {
            "high_compatibility": 0.8,
            "moderate_compatibility": 0.6,
            "low_compatibility": 0.4,
        }

    async def analyze_team_compatibility(
        self, team_id: UUID
    ) -> TeamCompatibilityReport:
        """Perform comprehensive team compatibility analysis"""
        try:
            # Get team members
            team = self.db.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team {team_id} not found")

            team_members = team.members
            if len(team_members) < 2:
                raise ValueError(
                    "Team must have at least 2 members for compatibility analysis"
                )

            # Get assessment data for all team members
            member_profiles = await self._get_member_profiles(team_members)

            # Calculate pairwise compatibility
            compatibility_matrix = await self._calculate_compatibility_matrix(
                member_profiles
            )

            # Calculate team-level metrics
            overall_compatibility = await self._calculate_overall_compatibility(
                compatibility_matrix
            )
            team_balance_score = await self._calculate_team_balance(member_profiles)
            diversity_metrics = await self._calculate_diversity_metrics(member_profiles)
            role_fit_scores = await self._analyze_role_fits(team, member_profiles)

            # Generate insights and recommendations
            optimization_suggestions = await self._generate_optimization_suggestions(
                compatibility_matrix, member_profiles, diversity_metrics
            )
            risk_factors = await self._identify_risk_factors(
                compatibility_matrix, member_profiles
            )

            return TeamCompatibilityReport(
                team_id=team_id,
                overall_compatibility=overall_compatibility,
                compatibility_matrix=compatibility_matrix,
                role_fit_scores=role_fit_scores,
                team_balance_score=team_balance_score,
                diversity_metrics=diversity_metrics,
                optimization_suggestions=optimization_suggestions,
                risk_factors=risk_factors,
            )

        except Exception as e:
            logger.error(f"Error analyzing team compatibility: {e!s}")
            raise

    async def analyze_member_compatibility(
        self, user1_id: UUID, user2_id: UUID
    ) -> CompatibilityScore:
        """Analyze compatibility between two specific team members"""
        try:
            # Get user profiles
            user1_profile = await self._get_member_profiles([user1_id])
            user2_profile = await self._get_member_profiles([user2_id])

            if not user1_profile or not user2_profile:
                raise ValueError(
                    "One or both users not found or have no assessment data"
                )

            profile1 = user1_profile[0]
            profile2 = user2_profile[0]

            # Calculate individual compatibility components
            personality_fit = await self._calculate_personality_compatibility(
                profile1, profile2
            )
            skills_complement = await self._calculate_skills_complementarity(
                profile1, profile2
            )
            work_style_match = await self._calculate_work_style_compatibility(
                profile1, profile2
            )
            communication_match = await self._calculate_communication_compatibility(
                profile1, profile2
            )

            # Calculate weighted overall score
            overall_score = (
                personality_fit * self.weights["personality_fit"]
                + skills_complement * self.weights["skills_complement"]
                + work_style_match * self.weights["work_style_match"]
                + communication_match * self.weights["communication_match"]
            )

            # Generate insights
            potential_conflicts = await self._identify_potential_conflicts(
                profile1, profile2
            )
            strengths = await self._identify_compatibility_strengths(profile1, profile2)
            recommendations = await self._generate_compatibility_recommendations(
                profile1, profile2
            )

            return CompatibilityScore(
                user1_id=user1_id,
                user2_id=user2_id,
                overall_score=overall_score,
                personality_fit=personality_fit,
                skills_complement=skills_complement,
                work_style_match=work_style_match,
                communication_match=communication_match,
                potential_conflicts=potential_conflicts,
                strengths=strengths,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error analyzing member compatibility: {e!s}")
            raise

    async def suggest_team_composition(
        self, team_id: UUID, required_skills: list[str], team_size: int
    ) -> dict[str, Any]:
        """Suggest optimal team composition for specific requirements"""
        try:
            team = self.db.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team {team_id} not found")

            # Get all potential candidates from organization
            current_member_ids = [member.id for member in team.members]
            candidates = (
                self.db.query(User)
                .filter(
                    and_(
                        User.organization_id == team.organization_id,
                        User.id.notin_(current_member_ids),
                    )
                )
                .all()
            )

            # Get profiles for candidates
            candidate_profiles = await self._get_member_profiles(candidates)
            current_profiles = await self._get_member_profiles(team.members)

            # Analyze current team gaps
            current_skills = await self._extract_team_skills(current_profiles)
            skill_gaps = set(required_skills) - set(current_skills)

            # Score candidates based on multiple factors
            candidate_scores = []
            for candidate in candidate_profiles:
                score = await self._score_candidate_for_team(
                    candidate, current_profiles, required_skills, skill_gaps
                )
                candidate_scores.append(
                    {
                        "user_id": candidate["user_id"],
                        "name": candidate["name"],
                        "score": score,
                        "skills": candidate.get("skills", []),
                        "role_fit": score.get("role_fit", 0),
                    }
                )

            # Sort and return top recommendations
            candidate_scores.sort(key=lambda x: x["score"], reverse=True)
            top_candidates = candidate_scores[: min(10, len(candidate_scores))]

            return {
                "team_id": team_id,
                "required_skills": required_skills,
                "current_skills": list(current_skills),
                "skill_gaps": list(skill_gaps),
                "recommendations": top_candidates,
                "composition_analysis": {
                    "current_size": len(team.members),
                    "target_size": team_size,
                    "openings": max(0, team_size - len(team.members)),
                },
            }

        except Exception as e:
            logger.error(f"Error suggesting team composition: {e!s}")
            raise

    async def _get_member_profiles(self, members: list[Any]) -> list[dict[str, Any]]:
        """Extract comprehensive profiles for team members from assessment data"""
        profiles = []

        for member in members:
            user_id = member.id if isinstance(member, User) else member

            # Get latest assessment responses
            responses = (
                self.db.query(UserAssessmentResponse)
                .filter(UserAssessmentResponse.user_id == user_id)
                .all()
            )

            if not responses:
                continue

            # Extract personality traits (Big Five, MBTI, etc.)
            personality_scores = await self._extract_personality_scores(responses)

            # Extract skills and competencies
            skills = await self._extract_skills(responses)

            # Extract work style preferences
            work_style = await self._extract_work_style(responses)

            # Extract communication style
            communication_style = await self._extract_communication_style(responses)

            profile = {
                "user_id": user_id,
                "name": (
                    member.full_name
                    if hasattr(member, "full_name")
                    else f"User {user_id}"
                ),
                "personality": personality_scores,
                "skills": skills,
                "work_style": work_style,
                "communication": communication_style,
                "response_count": len(responses),
                "last_assessment": (
                    max([r.created_at for r in responses]) if responses else None
                ),
            }

            profiles.append(profile)

        return profiles

    async def _extract_personality_scores(
        self, responses: list[Any]
    ) -> dict[str, float]:
        """Extract personality trait scores from assessment responses"""
        personality_scores = {
            "openness": 0.5,  # Big Five traits
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
            "mbti_type": None,  # Will be filled if available
        }

        for response in responses:
            if hasattr(response.assessment, "scoring_config"):
                config = response.assessment.scoring_config
                if config and "personality_traits" in config:
                    traits = config["personality_traits"]
                    for trait, value in traits.items():
                        if trait in personality_scores:
                            personality_scores[trait] = float(value)

        return personality_scores

    async def _extract_skills(self, responses: list[Any]) -> list[str]:
        """Extract skills from assessment responses"""
        skills = set()

        for response in responses:
            if response.answers:
                for answer in response.answers:
                    if isinstance(answer, dict) and "skill" in answer:
                        skills.add(answer["skill"])
                    elif isinstance(answer, str) and "skill" in answer.lower():
                        skills.add(answer)

        return list(skills)

    async def _extract_work_style(self, responses: list[Any]) -> dict[str, Any]:
        """Extract work style preferences"""
        work_style = {
            "preferred_environment": "collaborative",
            "decision_making_style": "analytical",
            "task_preference": "structured",
            "leadership_style": "democratic",
        }

        # Analyze response patterns to determine work style
        for response in responses:
            if hasattr(response, "answers") and response.answers:
                # Simple heuristic-based classification
                collaborative_responses = sum(
                    1
                    for ans in response.answers
                    if "team" in str(ans).lower() or "collabor" in str(ans).lower()
                )
                analytical_responses = sum(
                    1
                    for ans in response.answers
                    if "analy" in str(ans).lower() or "data" in str(ans).lower()
                )

                if collaborative_responses > len(response.answers) * 0.6:
                    work_style["preferred_environment"] = "collaborative"
                elif collaborative_responses < len(response.answers) * 0.3:
                    work_style["preferred_environment"] = "independent"

                if analytical_responses > len(response.answers) * 0.5:
                    work_style["decision_making_style"] = "analytical"
                else:
                    work_style["decision_making_style"] = "intuitive"

        return work_style

    async def _extract_communication_style(
        self, responses: list[Any]
    ) -> dict[str, Any]:
        """Extract communication style preferences"""
        communication_style = {
            "formality_level": "moderate",
            "frequency_preference": "regular",
            "channel_preference": "mixed",
            "clarity_focus": True,
        }

        # Analyze text responses for communication patterns
        for response in responses:
            if hasattr(response, "text_responses"):
                text_responses = " ".join(response.text_responses or [])
                formal_indicators = ["please", "thank you", "regarding", "concerning"]
                informal_indicators = ["hey", "gonna", "wanna", "cool", "awesome"]

                formal_count = sum(
                    1
                    for indicator in formal_indicators
                    if indicator in text_responses.lower()
                )
                informal_count = sum(
                    1
                    for indicator in informal_indicators
                    if indicator in text_responses.lower()
                )

                if formal_count > informal_count:
                    communication_style["formality_level"] = "formal"
                elif informal_count > formal_count:
                    communication_style["formality_level"] = "informal"

        return communication_style

    async def _calculate_compatibility_matrix(
        self, profiles: list[dict[str, Any]]
    ) -> dict[str, dict[str, float]]:
        """Calculate pairwise compatibility matrix for all team members"""
        compatibility_matrix = {}

        for i, profile1 in enumerate(profiles):
            user1_id = str(profile1["user_id"])
            compatibility_matrix[user1_id] = {}

            for j, profile2 in enumerate(profiles):
                if i != j:
                    user2_id = str(profile2["user_id"])

                    # Calculate compatibility scores
                    personality_fit = await self._calculate_personality_compatibility(
                        profile1, profile2
                    )
                    skills_complement = await self._calculate_skills_complementarity(
                        profile1, profile2
                    )
                    work_style_match = await self._calculate_work_style_compatibility(
                        profile1, profile2
                    )
                    communication_match = (
                        await self._calculate_communication_compatibility(
                            profile1, profile2
                        )
                    )

                    # Calculate weighted overall compatibility
                    overall_score = (
                        personality_fit * self.weights["personality_fit"]
                        + skills_complement * self.weights["skills_complement"]
                        + work_style_match * self.weights["work_style_match"]
                        + communication_match * self.weights["communication_match"]
                    )

                    compatibility_matrix[user1_id][user2_id] = overall_score

        return compatibility_matrix

    async def _calculate_personality_compatibility(
        self, profile1: dict, profile2: dict
    ) -> float:
        """Calculate personality compatibility between two profiles"""
        p1 = profile1.get("personality", {})
        p2 = profile2.get("personality", {})

        # Use Big Five traits for calculation
        traits = [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ]

        if not all(trait in p1 and trait in p2 for trait in traits):
            return 0.5  # Default compatibility if data missing

        # Calculate trait differences (lower is better)
        differences = []
        for trait in traits:
            diff = abs(p1[trait] - p2[trait])
            differences.append(diff)

        # Convert differences to compatibility (1 - normalized difference)
        avg_difference = np.mean(differences)
        compatibility = max(0, 1 - avg_difference)

        # Bonus for complementary extraversion levels (one introvert, one extrovert)
        if (p1["extraversion"] < 0.5 and p2["extraversion"] > 0.5) or (
            p1["extraversion"] > 0.5 and p2["extraversion"] < 0.5
        ):
            compatibility += 0.1

        return min(1.0, compatibility)

    async def _calculate_skills_complementarity(
        self, profile1: dict, profile2: dict
    ) -> float:
        """Calculate skills complementarity between two profiles"""
        skills1 = set(profile1.get("skills", []))
        skills2 = set(profile2.get("skills", []))

        if not skills1 and not skills2:
            return 0.5

        # Calculate overlap and uniqueness
        common_skills = skills1.intersection(skills2)
        unique_skills1 = skills1 - skills2
        unique_skills2 = skills2 - skills1

        total_unique_skills = len(skills1.union(skills2))

        if total_unique_skills == 0:
            return 0.5

        # Balance between shared understanding and diverse skill sets
        overlap_ratio = len(common_skills) / total_unique_skills
        diversity_ratio = (len(unique_skills1) + len(unique_skills2)) / (
            total_unique_skills * 2
        )

        # Optimal balance: some overlap but good diversity
        complementarity = overlap_ratio * 0.4 + diversity_ratio * 0.6

        return complementarity

    async def _calculate_work_style_compatibility(
        self, profile1: dict, profile2: dict
    ) -> float:
        """Calculate work style compatibility"""
        ws1 = profile1.get("work_style", {})
        ws2 = profile2.get("work_style", {})

        compatibility_score = 0.0
        factors = 0

        # Compare decision making styles
        if ws1.get("decision_making_style") == ws2.get("decision_making_style"):
            compatibility_score += 0.3
        elif ws1.get("decision_making_style") in [
            "analytical",
            "data-driven",
        ] and ws2.get("decision_making_style") in ["intuitive", "creative"]:
            compatibility_score += 0.2  # Complementary styles
        factors += 1

        # Compare work environment preferences
        if ws1.get("preferred_environment") == ws2.get("preferred_environment"):
            compatibility_score += 0.4
        elif (
            ws1.get("preferred_environment") == "collaborative"
            and ws2.get("preferred_environment") == "independent"
        ):
            compatibility_score += 0.1  # Can work well together
        factors += 1

        # Compare task preferences
        if ws1.get("task_preference") == ws2.get("task_preference"):
            compatibility_score += 0.3
        factors += 1

        return compatibility_score if factors > 0 else 0.5

    async def _calculate_communication_compatibility(
        self, profile1: dict, profile2: dict
    ) -> float:
        """Calculate communication compatibility"""
        com1 = profile1.get("communication", {})
        com2 = profile2.get("communication", {})

        compatibility_score = 0.0

        # Compare formality levels
        formality1 = com1.get("formality_level", "moderate")
        formality2 = com2.get("formality_level", "moderate")

        if formality1 == formality2:
            compatibility_score += 0.4
        elif (
            abs(
                ["informal", "moderate", "formal"].index(formality1)
                - ["informal", "moderate", "formal"].index(formality2)
            )
            == 1
        ):
            compatibility_score += 0.2  # Close formality levels
        else:
            compatibility_score += 0.0  # Very different formality levels

        # Compare frequency preferences
        freq1 = com1.get("frequency_preference", "regular")
        freq2 = com2.get("frequency_preference", "regular")

        if freq1 == freq2:
            compatibility_score += 0.3
        else:
            compatibility_score += 0.1

        # Both value clarity
        if com1.get("clarity_focus", True) and com2.get("clarity_focus", True):
            compatibility_score += 0.3

        return min(1.0, compatibility_score)

    async def _calculate_overall_compatibility(
        self, compatibility_matrix: dict[str, dict[str, float]]
    ) -> float:
        """Calculate overall team compatibility score"""
        if not compatibility_matrix:
            return 0.0

        total_score = 0.0
        count = 0

        for user1_id, compatibilities in compatibility_matrix.items():
            for user2_id, score in compatibilities.items():
                total_score += score
                count += 1

        return total_score / count if count > 0 else 0.0

    async def _calculate_team_balance(self, profiles: list[dict[str, Any]]) -> float:
        """Calculate team balance across multiple dimensions"""
        if len(profiles) < 2:
            return 1.0

        # Calculate diversity in personality traits
        personality_values = []
        for profile in profiles:
            traits = profile.get("personality", {})
            if traits:
                personality_values.append(
                    [
                        traits.get("openness", 0.5),
                        traits.get("conscientiousness", 0.5),
                        traits.get("extraversion", 0.5),
                        traits.get("agreeableness", 0.5),
                        traits.get("neuroticism", 0.5),
                    ]
                )

        if not personality_values:
            return 0.5

        # Calculate diversity as average standard deviation
        personality_array = np.array(personality_values)
        std_devs = np.std(personality_array, axis=0)
        avg_diversity = np.mean(std_devs)

        # Optimal diversity score (not too similar, not too different)
        optimal_range = (0.2, 0.4)
        if optimal_range[0] <= avg_diversity <= optimal_range[1]:
            diversity_score = 1.0
        elif avg_diversity < optimal_range[0]:
            diversity_score = avg_diversity / optimal_range[0]
        else:
            diversity_score = max(0, 1.0 - (avg_diversity - optimal_range[1]))

        return diversity_score

    async def _calculate_diversity_metrics(
        self, profiles: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate various diversity metrics for the team"""
        diversity_metrics = {}

        # Skill diversity
        all_skills = set()
        total_skills = 0
        for profile in profiles:
            skills = set(profile.get("skills", []))
            all_skills.update(skills)
            total_skills += len(skills)

        skill_diversity = len(all_skills) / max(1, total_skills)
        diversity_metrics["skill_diversity"] = skill_diversity

        # Work style diversity
        work_styles = [profile.get("work_style", {}) for profile in profiles]
        unique_environments = len(
            set(ws.get("preferred_environment") for ws in work_styles)
        )
        diversity_metrics["work_environment_diversity"] = unique_environments / max(
            1, len(work_styles)
        )

        # Communication diversity
        communication_styles = [
            profile.get("communication", {}) for profile in profiles
        ]
        unique_formalities = len(
            set(cs.get("formality_level") for cs in communication_styles)
        )
        diversity_metrics["communication_diversity"] = unique_formalities / max(
            1, len(communication_styles)
        )

        return diversity_metrics

    async def _analyze_role_fits(
        self, team: Team, profiles: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Analyze how well each member fits their current role"""
        role_fits = {}

        for profile in profiles:
            user_id = str(profile["user_id"])

            # Simplified role fit analysis based on skills and work style
            skills = profile.get("skills", [])
            work_style = profile.get("work_style", {})

            # Base score from skill relevance
            skill_score = min(
                1.0, len(skills) / 5.0
            )  # Assuming 5+ relevant skills is good

            # Work style alignment score
            work_style_score = 0.7  # Default score
            if work_style.get("preferred_environment") == "collaborative":
                work_style_score = 0.9  # Team environments usually value collaboration

            # Overall role fit
            role_fit = skill_score * 0.6 + work_style_score * 0.4
            role_fits[user_id] = role_fit

        return role_fits

    async def _generate_optimization_suggestions(
        self,
        compatibility_matrix: dict[str, dict[str, float]],
        profiles: list[dict[str, Any]],
        diversity_metrics: dict[str, float],
    ) -> list[str]:
        """Generate team optimization suggestions"""
        suggestions = []

        # Analyze compatibility patterns
        low_compatibility_pairs = []
        high_compatibility_pairs = []

        for user1_id, compatibilities in compatibility_matrix.items():
            for user2_id, score in compatibilities.items():
                if user1_id < user2_id:  # Avoid duplicates
                    if score < 0.4:
                        low_compatibility_pairs.append((user1_id, user2_id, score))
                    elif score > 0.8:
                        high_compatibility_pairs.append((user1_id, user2_id, score))

        # Generate suggestions based on analysis
        if low_compatibility_pairs:
            suggestions.append(
                f"Consider team building activities for {len(low_compatibility_pairs)} low-compatibility pairs"
            )
            suggestions.append(
                "Facilitate communication workshops to improve understanding"
            )

        if high_compatibility_pairs:
            suggestions.append(
                f"Leverage {len(high_compatibility_pairs)} high-compatibility pairs for mentoring and collaboration"
            )

        # Diversity-based suggestions
        if diversity_metrics.get("skill_diversity", 0) < 0.5:
            suggestions.append("Consider adding members with complementary skill sets")

        if diversity_metrics.get("communication_diversity", 0) < 0.3:
            suggestions.append(
                "Establish clear communication protocols to accommodate different styles"
            )

        return suggestions

    async def _identify_risk_factors(
        self,
        compatibility_matrix: dict[str, dict[str, float]],
        profiles: list[dict[str, Any]],
    ) -> list[str]:
        """Identify potential risk factors in team composition"""
        risk_factors = []

        # Check for very low compatibility pairs
        min_compatibility = 1.0
        for compatibilities in compatibility_matrix.values():
            for score in compatibilities.values():
                min_compatibility = min(min_compatibility, score)

        if min_compatibility < 0.3:
            risk_factors.append(
                "Very low compatibility between some team members may cause conflicts"
            )

        # Check for communication style mismatches
        communication_styles = [p.get("communication", {}) for p in profiles]
        formal_members = sum(
            1 for cs in communication_styles if cs.get("formality_level") == "formal"
        )
        informal_members = sum(
            1 for cs in communication_styles if cs.get("formality_level") == "informal"
        )

        if formal_members > 0 and informal_members > 0:
            if min(formal_members, informal_members) / len(profiles) > 0.3:
                risk_factors.append(
                    "Mixed communication formality levels may cause misunderstandings"
                )

        # Check for extreme work style differences
        collaborative_count = sum(
            1
            for p in profiles
            if p.get("work_style", {}).get("preferred_environment") == "collaborative"
        )
        independent_count = len(profiles) - collaborative_count

        if abs(collaborative_count - independent_count) / len(profiles) > 0.7:
            risk_factors.append(
                "Team may be unbalanced in work environment preferences"
            )

        return risk_factors

    async def _identify_potential_conflicts(
        self, profile1: dict, profile2: dict
    ) -> list[str]:
        """Identify potential conflict areas between two team members"""
        conflicts = []

        # Personality-based conflicts
        p1 = profile1.get("personality", {})
        p2 = profile2.get("personality", {})

        # High neuroticism in both may lead to stress-based conflicts
        if p1.get("neuroticism", 0.5) > 0.7 and p2.get("neuroticism", 0.5) > 0.7:
            conflicts.append(
                "Both may be sensitive to stress - establish clear conflict resolution processes"
            )

        # Very different extraversion levels
        if abs(p1.get("extraversion", 0.5) - p2.get("extraversion", 0.5)) > 0.8:
            conflicts.append("Different energy levels may affect meeting dynamics")

        # Work style conflicts
        ws1 = profile1.get("work_style", {})
        ws2 = profile2.get("work_style", {})

        if (
            ws1.get("task_preference") == "structured"
            and ws2.get("task_preference") == "flexible"
        ):
            conflicts.append(
                "Different approaches to task organization may require compromise"
            )

        return conflicts

    async def _identify_compatibility_strengths(
        self, profile1: dict, profile2: dict
    ) -> list[str]:
        """Identify strengths in the compatibility between two team members"""
        strengths = []

        # Complementary skills
        skills1 = set(profile1.get("skills", []))
        skills2 = set(profile2.get("skills", []))
        unique_skills = skills1.symmetric_difference(skills2)

        if len(unique_skills) >= len(skills1.intersection(skills2)):
            strengths.append(
                "Strong complementary skill sets for comprehensive coverage"
            )

        # Similar work ethics (conscientiousness)
        p1 = profile1.get("personality", {})
        p2 = profile2.get("personality", {})

        if (
            abs(p1.get("conscientiousness", 0.5) - p2.get("conscientiousness", 0.5))
            < 0.2
        ):
            strengths.append("Similar work ethic and reliability levels")

        # Balanced leadership potential
        if p1.get("extraversion", 0.5) > 0.6 and p2.get("agreeableness", 0.5) > 0.6:
            strengths.append(
                "Good balance of leadership initiative and team cooperation"
            )

        return strengths

    async def _generate_compatibility_recommendations(
        self, profile1: dict, profile2: dict
    ) -> list[str]:
        """Generate recommendations for improving compatibility"""
        recommendations = []

        # Communication recommendations
        com1 = profile1.get("communication", {})
        com2 = profile2.get("communication", {})

        if com1.get("formality_level") != com2.get("formality_level"):
            recommendations.append("Establish agreed-upon communication standards")

        # Work collaboration recommendations
        ws1 = profile1.get("work_style", {})
        ws2 = profile2.get("work_style", {})

        if ws1.get("preferred_environment") != ws2.get("preferred_environment"):
            recommendations.append("Balance collaborative and independent work time")

        # Skill development recommendations
        skills1 = set(profile1.get("skills", []))
        skills2 = set(profile2.get("skills", []))

        if skills1 and skills2 and len(skills1.intersection(skills2)) < 2:
            recommendations.append(
                "Consider cross-training to build common knowledge base"
            )

        return recommendations

    async def _extract_team_skills(self, profiles: list[dict[str, Any]]) -> list[str]:
        """Extract all skills present in the team"""
        all_skills = set()
        for profile in profiles:
            all_skills.update(profile.get("skills", []))
        return list(all_skills)

    async def _score_candidate_for_team(
        self,
        candidate: dict[str, Any],
        current_profiles: list[dict[str, Any]],
        required_skills: list[str],
        skill_gaps: list[str],
    ) -> dict[str, float]:
        """Score a candidate for team compatibility and skill fit"""
        score = {
            "skill_fit": 0.0,
            "compatibility": 0.0,
            "diversity_value": 0.0,
            "overall": 0.0,
            "role_fit": 0.0,
        }

        # Skill fit score
        candidate_skills = set(candidate.get("skills", []))
        required_skills_set = set(required_skills)
        skill_gaps_set = set(skill_gaps)

        matching_required = len(candidate_skills.intersection(required_skills_set))
        filling_gaps = len(candidate_skills.intersection(skill_gaps_set))

        score["skill_fit"] = (matching_required + filling_gaps * 1.5) / max(
            1, len(required_skills_set)
        )

        # Compatibility with current team
        if current_profiles:
            compatibility_scores = []
            for current_profile in current_profiles:
                compatibility = await self._calculate_personality_compatibility(
                    candidate, current_profile
                )
                compatibility_scores.append(compatibility)

            score["compatibility"] = np.mean(compatibility_scores)

        # Diversity value (adds unique perspective)
        all_current_skills = set()
        for profile in current_profiles:
            all_current_skills.update(profile.get("skills", []))

        unique_skills = candidate_skills - all_current_skills
        score["diversity_value"] = min(
            1.0, len(unique_skills) / max(1, len(candidate_skills))
        )

        # Role fit assessment
        work_style = candidate.get("work_style", {})
        if work_style.get("preferred_environment") == "collaborative":
            score["role_fit"] = 0.8
        else:
            score["role_fit"] = 0.6

        # Calculate overall score
        score["overall"] = (
            score["skill_fit"] * 0.4
            + score["compatibility"] * 0.3
            + score["diversity_value"] * 0.2
            + score["role_fit"] * 0.1
        )

        return score
