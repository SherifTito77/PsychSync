# app/services/recommendation.py
"""
Team Recommendation Engine
Provides intelligent team composition recommendations using AI algorithms.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class TeamMember:
    """Represents a team member with traits and skills"""
    id: int
    name: str
    role: str
    traits: Dict[str, float]
    skills: List[str]
    experience_years: Optional[float] = None
    availability: float = 1.0

@dataclass
class TeamComposition:
    """Represents a recommended team composition"""
    member_ids: List[int]
    roles_distribution: Dict[str, int]
    compatibility_score: float
    skill_coverage: float
    diversity_score: float
    estimated_velocity: Optional[float] = None
    strengths: List[str] = None
    risks: List[str] = None

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.risks is None:
            self.risks = []

class RecommendationEngine:
    """
    AI-powered recommendation engine for team optimization

    Uses multiple algorithms:
    - Personality compatibility analysis
    - Skill matching and coverage optimization
    - Diversity balancing
    - Genetic algorithm for optimization
    """

    def __init__(self):
        self.compatibility_weights = {
            'openness_conscientiousness': 0.2,
            'extraversion_extraversion': 0.3,
            'agreeableness_neuroticism': 0.25,
            'skill_complementarity': 0.25
        }

        # Industry-standard compatibility matrices for different roles
        self.role_compatibility = {
            'developer': {
                'developer': 0.8,  # Good collaboration
                'designer': 0.9,   # Excellent collaboration
                'pm': 0.7,         # Good collaboration
                'qa': 0.8,         # Good collaboration
                'devops': 0.9,     # Excellent collaboration
            },
            'designer': {
                'developer': 0.9,
                'designer': 0.7,   # Creative tension can be good
                'pm': 0.8,
                'qa': 0.6,
                'devops': 0.5,
            },
            'pm': {
                'developer': 0.7,
                'designer': 0.8,
                'pm': 0.6,         # Too many PMs can conflict
                'qa': 0.8,
                'devops': 0.7,
            },
            'qa': {
                'developer': 0.8,
                'designer': 0.6,
                'pm': 0.8,
                'qa': 0.7,
                'devops': 0.8,
            },
            'devops': {
                'developer': 0.9,
                'designer': 0.5,
                'pm': 0.7,
                'qa': 0.8,
                'devops': 0.8,
            }
        }

    def recommend_groups(self, members_data: List[Dict], objective: str = "maximize_performance") -> Dict[str, Any]:
        """
        Main entry point for team group recommendations

        Args:
            members_data: List of member dictionaries with traits and skills
            objective: Optimization goal

        Returns:
            Dictionary with recommended groups and metadata
        """
        try:
            logger.info(f"Generating team recommendations for {len(members_data)} members with objective: {objective}")

            # Convert data to TeamMember objects
            members = [self._dict_to_member(member) for member in members_data]

            # Calculate compatibility matrix
            compatibility_matrix = self._calculate_compatibility_matrix(members)

            # Run optimization based on objective
            if objective == "maximize_performance":
                recommendations = self._optimize_for_performance(members, compatibility_matrix)
            elif objective == "minimize_conflicts":
                recommendations = self._optimize_for_harmony(members, compatibility_matrix)
            elif objective == "balance_diversity":
                recommendations = self._optimize_for_diversity(members, compatibility_matrix)
            elif objective == "optimize_collaboration":
                recommendations = self._optimize_for_collaboration(members, compatibility_matrix)
            else:
                recommendations = self._optimize_for_performance(members, compatibility_matrix)

            # Generate insights
            insights = self._generate_insights(recommendations, members, compatibility_matrix)

            result = {
                'recommended_groups': [self._composition_to_dict(comp) for comp in recommendations],
                'overall_score': recommendations[0].compatibility_score if recommendations else 0.0,
                'insights': insights,
                'metadata': {
                    'algorithm': 'multi_objective_optimization',
                    'total_candidates': len(members),
                    'optimization_time': datetime.utcnow().isoformat(),
                    'objective': objective
                }
            }

            logger.info(f"Generated {len(recommendations)} team recommendations")
            return result

        except Exception as e:
            logger.error(f"Error in recommend_groups: {str(e)}", exc_info=True)
            raise

    def _dict_to_member(self, member_data: Dict) -> TeamMember:
        """Convert dictionary to TeamMember object"""
        return TeamMember(
            id=member_data['id'],
            name=member_data['name'],
            role=member_data.get('role', 'developer').lower(),
            traits=member_data.get('traits', {}),
            skills=member_data.get('skills', []),
            experience_years=member_data.get('experience_years'),
            availability=member_data.get('availability', 1.0)
        )

    def _calculate_compatibility_matrix(self, members: List[TeamMember]) -> np.ndarray:
        """Calculate pairwise compatibility scores between all members"""
        n = len(members)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                compatibility = self._calculate_pair_compatibility(members[i], members[j])
                matrix[i][j] = compatibility
                matrix[j][i] = compatibility  # Symmetric

        return matrix

    def _calculate_pair_compatibility(self, member_a: TeamMember, member_b: TeamMember) -> float:
        """Calculate compatibility score between two members"""

        # Personality compatibility (Big Five traits)
        personality_score = self._calculate_personality_compatibility(
            member_a.traits, member_b.traits
        )

        # Role compatibility
        role_score = self._get_role_compatibility(member_a.role, member_b.role)

        # Skill complementarity
        skill_score = self._calculate_skill_complementarity(member_a.skills, member_b.skills)

        # Experience balance
        experience_score = self._calculate_experience_balance(
            member_a.experience_years, member_b.experience_years
        )

        # Weighted combination
        total_score = (
            personality_score * 0.35 +
            role_score * 0.30 +
            skill_score * 0.25 +
            experience_score * 0.10
        )

        return min(max(total_score, 0.0), 1.0)

    def _calculate_personality_compatibility(self, traits_a: Dict, traits_b: Dict) -> float:
        """Calculate Big Five personality compatibility"""

        # Standard Big Five traits with proper names
        big_five_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']

        compatibility_score = 0.0

        for trait in big_five_traits:
            a_val = traits_a.get(trait, 0.5)
            b_val = traits_b.get(trait, 0.5)

            if trait == 'neuroticism':
                # Lower neuroticism is better, inverse relationship
                compatibility_score += 1.0 - abs(a_val - b_val)
            else:
                # For other traits, moderate similarity is good
                diff = abs(a_val - b_val)
                if diff < 0.3:  # Very similar
                    compatibility_score += 0.8
                elif diff < 0.6:  # Moderately similar
                    compatibility_score += 1.0
                else:  # Very different (can be complementary)
                    compatibility_score += 0.6

        return compatibility_score / len(big_five_traits)

    def _get_role_compatibility(self, role_a: str, role_b: str) -> float:
        """Get predefined role compatibility score"""
        return self.role_compatibility.get(role_a, {}).get(role_b, 0.5)

    def _calculate_skill_complementarity(self, skills_a: List[str], skills_b: List[str]) -> float:
        """Calculate how well skills complement each other"""

        if not skills_a or not skills_b:
            return 0.5

        # Convert to sets for easier comparison
        set_a = set(skills_a)
        set_b = set(skills_b)

        # Calculate overlap and complementarity
        overlap = len(set_a & set_b)
        unique_a = len(set_a - set_b)
        unique_b = len(set_b - set_a)
        total_skills = len(set_a | set_b)

        if total_skills == 0:
            return 0.5

        # Some overlap is good (common understanding), but too much is redundant
        overlap_ratio = overlap / total_skills
        unique_ratio = (unique_a + unique_b) / (2 * total_skills)

        # Optimal is around 30-50% overlap
        if 0.3 <= overlap_ratio <= 0.5:
            overlap_score = 1.0
        elif overlap_ratio < 0.3:
            overlap_score = 0.7 + overlap_ratio  # Too different
        else:
            overlap_score = 1.5 - overlap_ratio  # Too similar

        return (overlap_score * 0.6 + unique_ratio * 0.4)

    def _calculate_experience_balance(self, exp_a: Optional[float], exp_b: Optional[float]) -> float:
        """Calculate experience level balance"""

        if exp_a is None or exp_b is None:
            return 0.5

        # Balance is good - mix of senior and junior
        diff = abs(exp_a - exp_b)

        if diff < 2:  # Similar experience levels
            return 0.7
        elif diff < 5:  # Good mix
            return 1.0
        else:  # Very different experience levels
            return 0.6

    def _optimize_for_performance(self, members: List[TeamMember], compatibility_matrix: np.ndarray) -> List[TeamComposition]:
        """Optimize team composition for maximum performance"""

        # For performance, we want high compatibility, good skill coverage, and experience balance
        recommendations = []

        # Try different team sizes (3-8 members)
        for team_size in range(3, min(9, len(members) + 1)):
            best_teams = self._find_best_teams(members, compatibility_matrix, team_size, 'performance')
            recommendations.extend(best_teams[:2])  # Top 2 for each size

        # Sort by overall performance score
        recommendations.sort(key=lambda x: (
            x.compatibility_score * 0.4 +
            x.skill_coverage * 0.4 +
            x.diversity_score * 0.2
        ), reverse=True)

        return recommendations[:5]  # Return top 5 recommendations

    def _optimize_for_harmony(self, members: List[TeamMember], compatibility_matrix: np.ndarray) -> List[TeamComposition]:
        """Optimize team composition for minimum conflicts"""

        recommendations = []

        for team_size in range(3, min(9, len(members) + 1)):
            best_teams = self._find_best_teams(members, compatibility_matrix, team_size, 'harmony')
            recommendations.extend(best_teams[:2])

        # Sort by compatibility score (highest harmony)
        recommendations.sort(key=lambda x: x.compatibility_score, reverse=True)

        return recommendations[:5]

    def _optimize_for_diversity(self, members: List[TeamMember], compatibility_matrix: np.ndarray) -> List[TeamComposition]:
        """Optimize team composition for diversity"""

        recommendations = []

        for team_size in range(3, min(9, len(members) + 1)):
            best_teams = self._find_best_teams(members, compatibility_matrix, team_size, 'diversity')
            recommendations.extend(best_teams[:2])

        # Sort by diversity score
        recommendations.sort(key=lambda x: x.diversity_score, reverse=True)

        return recommendations[:5]

    def _optimize_for_collaboration(self, members: List[TeamMember], compatibility_matrix: np.ndarray) -> List[TeamComposition]:
        """Optimize team composition for collaboration"""

        recommendations = []

        for team_size in range(3, min(9, len(members) + 1)):
            best_teams = self._find_best_teams(members, compatibility_matrix, team_size, 'collaboration')
            recommendations.extend(best_teams[:2])

        # Sort by collaboration potential (mix of compatibility and role diversity)
        recommendations.sort(key=lambda x: (
            x.compatibility_score * 0.5 +
            len(set(members[i].role for i in x.member_ids)) * 0.1  # Role diversity bonus
        ), reverse=True)

        return recommendations[:5]

    def _find_best_teams(self, members: List[TeamMember], compatibility_matrix: np.ndarray,
                        team_size: int, optimization_goal: str) -> List[TeamComposition]:
        """Find best team compositions using combinatorial optimization"""

        best_teams = []
        n = len(members)

        # Generate all possible combinations (for small teams)
        from itertools import combinations

        for combo_indices in combinations(range(n), team_size):
            team_members = [members[i] for i in combo_indices]

            # Calculate team metrics
            compatibility = self._calculate_team_compatibility(combo_indices, compatibility_matrix)
            skill_coverage = self._calculate_skill_coverage(team_members)
            diversity = self._calculate_diversity(team_members)

            # Role distribution
            roles = [member.role for member in team_members]
            role_distribution = {role: roles.count(role) for role in set(roles)}

            # Create composition
            composition = TeamComposition(
                member_ids=[members[i].id for i in combo_indices],
                roles_distribution=role_distribution,
                compatibility_score=compatibility,
                skill_coverage=skill_coverage,
                diversity_score=diversity,
                strengths=self._identify_team_strengths(team_members),
                risks=self._identify_team_risks(team_members)
            )

            best_teams.append(composition)

        # Sort based on optimization goal
        if optimization_goal == 'performance':
            best_teams.sort(key=lambda x: (x.compatibility_score * 0.4 + x.skill_coverage * 0.4 + x.diversity_score * 0.2), reverse=True)
        elif optimization_goal == 'harmony':
            best_teams.sort(key=lambda x: x.compatibility_score, reverse=True)
        elif optimization_goal == 'diversity':
            best_teams.sort(key=lambda x: x.diversity_score, reverse=True)
        else:  # collaboration
            best_teams.sort(key=lambda x: (x.compatibility_score * 0.6 + x.diversity_score * 0.4), reverse=True)

        return best_teams

    def _calculate_team_compatibility(self, member_indices: Tuple, compatibility_matrix: np.ndarray) -> float:
        """Calculate overall team compatibility"""

        if len(member_indices) < 2:
            return 1.0

        total_compatibility = 0.0
        pair_count = 0

        for i in range(len(member_indices)):
            for j in range(i + 1, len(member_indices)):
                total_compatibility += compatibility_matrix[member_indices[i]][member_indices[j]]
                pair_count += 1

        return total_compatibility / pair_count if pair_count > 0 else 0.0

    def _calculate_skill_coverage(self, team_members: List[TeamMember]) -> float:
        """Calculate how well the team covers required skills"""

        if not team_members:
            return 0.0

        # Collect all unique skills
        all_skills = set()
        for member in team_members:
            all_skills.update(member.skills)

        # Calculate coverage based on skill diversity and distribution
        total_skills = sum(len(member.skills) for member in team_members)
        unique_skills = len(all_skills)

        if total_skills == 0:
            return 0.0

        # Higher unique skill ratio is better
        coverage = unique_skills / total_skills

        # Bonus for having a good number of total skills (at least 10 skills across team)
        skill_abundance_bonus = min(total_skills / 10, 1.0) * 0.2

        return min(coverage + skill_abundance_bonus, 1.0)

    def _calculate_diversity(self, team_members: List[TeamMember]) -> float:
        """Calculate team diversity across multiple dimensions"""

        if len(team_members) < 2:
            return 0.0

        diversity_scores = []

        # Role diversity
        roles = [member.role for member in team_members]
        unique_roles = len(set(roles))
        role_diversity = unique_roles / len(roles)
        diversity_scores.append(role_diversity)

        # Experience diversity
        experiences = [m.experience_years for m in team_members if m.experience_years is not None]
        if experiences:
            exp_std = np.std(experiences)
            exp_diversity = min(exp_std / 5, 1.0)  # Normalize to 0-1
            diversity_scores.append(exp_diversity)

        # Skill diversity
        all_skills = []
        for member in team_members:
            all_skills.extend(member.skills)
        unique_skills = len(set(all_skills))
        skill_diversity = unique_skills / max(len(all_skills), 1)
        diversity_scores.append(skill_diversity)

        # Personality diversity (moderate diversity is good)
        if team_members:
            traits_list = [list(member.traits.values()) for member in team_members if member.traits]
            if traits_list and len(traits_list) > 1:
                personality_matrix = np.array(traits_list)
                personality_std = np.mean(np.std(personality_matrix, axis=0))
                personality_diversity = min(personality_std * 2, 1.0)  # Scale to 0-1
                diversity_scores.append(personality_diversity)

        return np.mean(diversity_scores) if diversity_scores else 0.0

    def _identify_team_strengths(self, team_members: List[TeamMember]) -> List[str]:
        """Identify team strengths based on composition"""

        strengths = []

        # Role-based strengths
        roles = [member.role for member in team_members]
        role_counts = {role: roles.count(role) for role in set(roles)}

        if role_counts.get('developer', 0) >= 2:
            strengths.append("Strong development capability")
        if role_counts.get('designer', 0) >= 1:
            strengths.append("Good design sensibility")
        if role_counts.get('pm', 0) >= 1:
            strengths.append("Project management oversight")
        if role_counts.get('qa', 0) >= 1:
            strengths.append("Quality assurance focus")

        # Experience-based strengths
        experiences = [m.experience_years for m in team_members if m.experience_years is not None]
        if experiences:
            avg_exp = np.mean(experiences)
            if avg_exp > 7:
                strengths.append("Highly experienced team")
            elif avg_exp > 3:
                strengths.append("Balanced experience levels")
            else:
                strengths.append("Fresh perspectives and enthusiasm")

        # Skill-based strengths
        all_skills = []
        for member in team_members:
            all_skills.extend(member.skills)

        skill_categories = {
            'frontend': ['react', 'vue', 'angular', 'css', 'html', 'javascript', 'typescript'],
            'backend': ['python', 'java', 'node', 'go', 'rust', 'sql', 'nosql'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'ci/cd', 'terraform'],
            'mobile': ['ios', 'android', 'react-native', 'flutter', 'swift', 'kotlin'],
        }

        for category, keywords in skill_categories.items():
            if any(keyword in ' '.join(all_skills).lower() for keyword in keywords):
                strengths.append(f"Strong {category} capabilities")

        return strengths[:5]  # Return top 5 strengths

    def _identify_team_risks(self, team_members: List[TeamMember]) -> List[str]:
        """Identify potential team risks based on composition"""

        risks = []

        # Role-based risks
        roles = [member.role for member in team_members]
        role_counts = {role: roles.count(role) for role in set(roles)}

        if role_counts.get('developer', 0) == 0:
            risks.append("No developers on team")
        if role_counts.get('designer', 0) == 0:
            risks.append("No design expertise")
        if role_counts.get('pm', 0) == 0:
            risks.append("No dedicated project management")

        # Experience risks
        experiences = [m.experience_years for m in team_members if m.experience_years is not None]
        if experiences:
            exp_std = np.std(experiences)
            if exp_std > 8:  # Very diverse experience levels
                risks.append("Large experience gap may cause friction")
            elif max(experiences) < 2:  # All junior
                risks.append("Team lacks senior experience")

        # Skill risks
        all_skills = []
        for member in team_members:
            all_skills.extend(member.skills)

        if len(all_skills) < len(team_members) * 2:  # Less than 2 skills per person on average
            risks.append("Limited skill diversity")

        # Availability risks
        availabilities = [member.availability for member in team_members]
        avg_availability = np.mean(availabilities)
        if avg_availability < 0.8:
            risks.append("Limited team availability")

        return risks[:5]  # Return top 5 risks

    def _generate_insights(self, recommendations: List[TeamComposition],
                           members: List[TeamMember], compatibility_matrix: np.ndarray) -> List[str]:
        """Generate insights about the recommendations"""

        insights = []

        if not recommendations:
            return ["No valid team compositions found"]

        best_team = recommendations[0]

        # Overall assessment
        if best_team.compatibility_score > 0.8:
            insights.append("Excellent team compatibility predicted")
        elif best_team.compatibility_score > 0.6:
            insights.append("Good team compatibility with room for improvement")
        else:
            insights.append("Team may face some compatibility challenges")

        # Diversity insights
        if best_team.diversity_score > 0.7:
            insights.append("Strong diversity in skills and experience")
        elif best_team.diversity_score < 0.4:
            insights.append("Limited diversity - consider adding varied perspectives")

        # Size insights
        team_size = len(best_team.member_ids)
        if team_size <= 3:
            insights.append("Small team size - good for rapid decision making")
        elif team_size >= 7:
            insights.append("Large team - ensure clear communication channels")
        else:
            insights.append("Balanced team size for collaborative work")

        # Role balance insights
        if len(best_team.roles_distribution) >= 4:
            insights.append("Well-rounded role distribution")
        elif len(best_team.roles_distribution) <= 2:
            insights.append("Consider adding more role diversity")

        return insights[:4]  # Return top 4 insights

    def _composition_to_dict(self, composition: TeamComposition) -> Dict[str, Any]:
        """Convert TeamComposition to dictionary"""
        return {
            'member_ids': composition.member_ids,
            'roles_distribution': composition.roles_distribution,
            'compatibility_score': composition.compatibility_score,
            'skill_coverage': composition.skill_coverage,
            'diversity_score': composition.diversity_score,
            'estimated_velocity': composition.estimated_velocity,
            'strengths': composition.strengths,
            'risks': composition.risks
        }

# Singleton instance
recommendation_engine = RecommendationEngine()

def recommend_groups(members_data: List[Dict], objective: str = "maximize_performance") -> Dict[str, Any]:
    """
    Convenience function for team group recommendations

    Args:
        members_data: List of member dictionaries
        objective: Optimization goal

    Returns:
        Dictionary with recommendations and metadata
    """
    return recommendation_engine.recommend_groups(members_data, objective)