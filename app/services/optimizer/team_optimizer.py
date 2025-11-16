"""
File Path: app/services/optimizer/team_optimizer.py
Team composition optimizer for organizational assessments
Optimizes team member selection based on personality traits, skills, and compatibility
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from scipy.optimize import linear_sum_assignment
import logging

logger = logging.getLogger(__name__)


# =================================================================
# DATA CLASSES
# =================================================================

@dataclass
class TeamMemberProfile:
    """Individual team member profile for optimization"""
    user_id: int
    name: str
    email: str
    
    # Personality traits (Big Five model)
    openness: float  # 0-100
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    
    # Skills and competencies
    skills: Dict[str, float]  # skill_name: proficiency (0-100)
    
    # Role preferences
    preferred_roles: List[str]
    role_compatibility: Dict[str, float]  # role: compatibility (0-100)
    
    # Availability and constraints
    availability: float  # 0-100 (percentage)
    max_teams: int
    current_teams: int
    
    # Performance metrics
    past_performance: float  # 0-100
    collaboration_score: float  # 0-100
    
    # Additional attributes
    department: str
    seniority_level: str
    tenure_months: int


@dataclass
class TeamRequirements:
    """Team composition requirements and constraints"""
    team_id: int
    team_name: str
    
    # Size requirements
    min_size: int
    max_size: int
    target_size: int
    
    # Role requirements
    required_roles: Dict[str, int]  # role: count
    optional_roles: Dict[str, int]
    
    # Skill requirements
    required_skills: Dict[str, float]  # skill: min_level
    desired_skills: Dict[str, float]
    
    # Diversity requirements
    min_personality_diversity: float  # 0-1
    max_personality_similarity: float  # 0-1
    
    # Department diversity
    max_same_department: Optional[int] = None
    
    # Seniority balance
    min_senior_members: Optional[int] = None
    max_junior_members: Optional[int] = None


@dataclass
class OptimizedTeam:
    """Optimized team composition result"""
    team_id: int
    team_name: str
    members: List[TeamMemberProfile]
    
    # Optimization scores
    overall_score: float  # 0-100
    compatibility_score: float
    skill_coverage_score: float
    diversity_score: float
    balance_score: float
    
    # Team statistics
    avg_performance: float
    avg_collaboration: float
    total_availability: float
    
    # Role distribution
    role_distribution: Dict[str, int]
    skill_coverage: Dict[str, float]
    
    # Personality distribution
    personality_profile: Dict[str, float]
    
    # Recommendations
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]


# =================================================================
# TEAM OPTIMIZATION ENGINE
# =================================================================

class TeamOptimizationEngine:
    """
    Optimizes team composition based on multiple factors:
    - Personality compatibility
    - Skill requirements
    - Role distribution
    - Diversity and balance
    - Performance history
    """
    
    def __init__(self):
        self.weights = {
            'compatibility': 0.25,
            'skills': 0.30,
            'diversity': 0.20,
            'performance': 0.15,
            'balance': 0.10
        }
    
    def optimize_team(
        self,
        candidates: List[TeamMemberProfile],
        requirements: TeamRequirements,
        existing_members: Optional[List[TeamMemberProfile]] = None
    ) -> OptimizedTeam:
        """
        Optimize team composition from candidate pool
        
        Args:
            candidates: Pool of available candidates
            requirements: Team requirements and constraints
            existing_members: Optional existing team members (for expansion)
        
        Returns:
            Optimized team composition
        """
        logger.info(
            f"Optimizing team '{requirements.team_name}' "
            f"from {len(candidates)} candidates"
        )
        
        if existing_members is None:
            existing_members = []
        
        # Filter eligible candidates
        eligible = self._filter_eligible_candidates(
            candidates,
            requirements,
            existing_members
        )
        
        if len(eligible) < requirements.min_size - len(existing_members):
            raise ValueError(
                f"Insufficient eligible candidates: {len(eligible)} available, "
                f"{requirements.min_size - len(existing_members)} required"
            )
        
        # Calculate compatibility matrix
        compatibility_matrix = self._calculate_compatibility_matrix(
            eligible,
            existing_members
        )
        
        # Calculate skill coverage scores
        skill_scores = self._calculate_skill_scores(
            eligible,
            requirements
        )
        
        # Calculate diversity scores
        diversity_scores = self._calculate_diversity_scores(
            eligible,
            existing_members,
            requirements
        )
        
        # Calculate overall scores
        overall_scores = self._calculate_overall_scores(
            compatibility_matrix,
            skill_scores,
            diversity_scores,
            eligible
        )
        
        # Select optimal team members
        selected_indices = self._select_team_members(
            overall_scores,
            requirements.target_size - len(existing_members),
            requirements
        )
        
        selected_members = [eligible[i] for i in selected_indices]
        all_members = existing_members + selected_members
        
        # Create optimized team result
        optimized_team = self._create_team_result(
            all_members,
            requirements,
            overall_scores[selected_indices].mean()
        )
        
        logger.info(
            f"Team optimized: {len(all_members)} members, "
            f"score: {optimized_team.overall_score:.2f}"
        )
        
        return optimized_team
    
    def _filter_eligible_candidates(
        self,
        candidates: List[TeamMemberProfile],
        requirements: TeamRequirements,
        existing_members: List[TeamMemberProfile]
    ) -> List[TeamMemberProfile]:
        """Filter candidates based on basic eligibility"""
        existing_ids = {m.user_id for m in existing_members}
        
        eligible = []
        for candidate in candidates:
            # Skip if already in team
            if candidate.user_id in existing_ids:
                continue
            
            # Check availability
            if candidate.availability < 50:  # Minimum 50% availability
                continue
            
            # Check team capacity
            if candidate.current_teams >= candidate.max_teams:
                continue
            
            # Check required skills
            has_required_skills = True
            for skill, min_level in requirements.required_skills.items():
                if candidate.skills.get(skill, 0) < min_level:
                    has_required_skills = False
                    break
            
            if has_required_skills:
                eligible.append(candidate)
        
        return eligible
    
    def _calculate_compatibility_matrix(
        self,
        candidates: List[TeamMemberProfile],
        existing_members: List[TeamMemberProfile]
    ) -> np.ndarray:
        """Calculate personality compatibility between candidates"""
        n = len(candidates)
        compatibility = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                score = self._calculate_personality_compatibility(
                    candidates[i],
                    candidates[j]
                )
                compatibility[i, j] = score
                compatibility[j, i] = score
        
        # Calculate compatibility with existing members
        if existing_members:
            for i, candidate in enumerate(candidates):
                avg_existing_compat = np.mean([
                    self._calculate_personality_compatibility(
                        candidate,
                        existing
                    )
                    for existing in existing_members
                ])
                compatibility[i, i] = avg_existing_compat
        
        return compatibility
    
    def _calculate_personality_compatibility(
        self,
        member1: TeamMemberProfile,
        member2: TeamMemberProfile
    ) -> float:
        """
        Calculate personality compatibility between two members
        Based on complementary personality traits
        """
        # Complementary traits (opposites attract for work)
        complementary_score = (
            abs(member1.extraversion - member2.extraversion) / 100 * 0.3 +
            abs(member1.openness - member2.openness) / 100 * 0.2
        )
        
        # Similar traits (should be aligned)
        similar_score = (
            (100 - abs(member1.conscientiousness - member2.conscientiousness)) / 100 * 0.3 +
            (100 - abs(member1.agreeableness - member2.agreeableness)) / 100 * 0.2
        )
        
        # Low neuroticism is generally better
        neuroticism_penalty = (
            (member1.neuroticism + member2.neuroticism) / 200 * 0.1
        )
        
        compatibility = (
            complementary_score + similar_score - neuroticism_penalty
        ) * 100
        
        return max(0, min(100, compatibility))
    
    def _calculate_skill_scores(
        self,
        candidates: List[TeamMemberProfile],
        requirements: TeamRequirements
    ) -> np.ndarray:
        """Calculate how well each candidate meets skill requirements"""
        scores = np.zeros(len(candidates))
        
        for i, candidate in enumerate(candidates):
            # Required skills score
            required_score = 0
            for skill, min_level in requirements.required_skills.items():
                level = candidate.skills.get(skill, 0)
                required_score += min(level / min_level, 1.0)
            
            if requirements.required_skills:
                required_score /= len(requirements.required_skills)
            else:
                required_score = 1.0
            
            # Desired skills score
            desired_score = 0
            for skill, desired_level in requirements.desired_skills.items():
                level = candidate.skills.get(skill, 0)
                desired_score += level / desired_level if desired_level > 0 else 0
            
            if requirements.desired_skills:
                desired_score /= len(requirements.desired_skills)
            else:
                desired_score = 1.0
            
            # Combined score
            scores[i] = (required_score * 0.7 + desired_score * 0.3) * 100
        
        return scores
    
    def _calculate_diversity_scores(
        self,
        candidates: List[TeamMemberProfile],
        existing_members: List[TeamMemberProfile],
        requirements: TeamRequirements
    ) -> np.ndarray:
        """Calculate diversity contribution of each candidate"""
        scores = np.zeros(len(candidates))
        
        existing_departments = [m.department for m in existing_members]
        existing_seniority = [m.seniority_level for m in existing_members]
        
        for i, candidate in enumerate(candidates):
            diversity_score = 0
            
            # Department diversity
            dept_count = existing_departments.count(candidate.department)
            if requirements.max_same_department:
                dept_penalty = dept_count / requirements.max_same_department
                diversity_score += (1 - dept_penalty) * 0.3
            else:
                diversity_score += 0.3
            
            # Seniority diversity
            seniority_count = existing_seniority.count(candidate.seniority_level)
            total_existing = len(existing_members) if existing_members else 1
            seniority_balance = 1 - (seniority_count / total_existing)
            diversity_score += seniority_balance * 0.3
            
            # Personality diversity
            if existing_members:
                personality_distances = [
                    self._personality_distance(candidate, existing)
                    for existing in existing_members
                ]
                avg_distance = np.mean(personality_distances)
                diversity_score += (avg_distance / 100) * 0.4
            else:
                diversity_score += 0.4
            
            scores[i] = diversity_score * 100
        
        return scores
    
    def _personality_distance(
        self,
        member1: TeamMemberProfile,
        member2: TeamMemberProfile
    ) -> float:
        """Calculate Euclidean distance between personality profiles"""
        traits1 = np.array([
            member1.openness,
            member1.conscientiousness,
            member1.extraversion,
            member1.agreeableness,
            member1.neuroticism
        ])
        
        traits2 = np.array([
            member2.openness,
            member2.conscientiousness,
            member2.extraversion,
            member2.agreeableness,
            member2.neuroticism
        ])
        
        return np.linalg.norm(traits1 - traits2)
    
    def _calculate_overall_scores(
        self,
        compatibility_matrix: np.ndarray,
        skill_scores: np.ndarray,
        diversity_scores: np.ndarray,
        candidates: List[TeamMemberProfile]
    ) -> np.ndarray:
        """Calculate weighted overall scores for each candidate"""
        n = len(candidates)
        overall_scores = np.zeros(n)
        
        for i in range(n):
            # Compatibility (average with others)
            compat_score = np.mean(compatibility_matrix[i])
            
            # Skills
            skill_score = skill_scores[i]
            
            # Diversity
            diversity_score = diversity_scores[i]
            
            # Performance
            performance_score = candidates[i].past_performance
            
            # Balance (collaboration + availability)
            balance_score = (
                candidates[i].collaboration_score * 0.6 +
                candidates[i].availability * 0.4
            )
            
            # Weighted combination
            overall_scores[i] = (
                compat_score * self.weights['compatibility'] +
                skill_score * self.weights['skills'] +
                diversity_score * self.weights['diversity'] +
                performance_score * self.weights['performance'] +
                balance_score * self.weights['balance']
            )
        
        return overall_scores
    
    def _select_team_members(
        self,
        scores: np.ndarray,
        num_to_select: int,
        requirements: TeamRequirements
    ) -> List[int]:
        """Select team members based on scores and constraints"""
        # Sort by score descending
        sorted_indices = np.argsort(scores)[::-1]
        
        # Select top N candidates
        selected = sorted_indices[:num_to_select].tolist()
        
        return selected
    
    def _create_team_result(
        self,
        members: List[TeamMemberProfile],
        requirements: TeamRequirements,
        overall_score: float
    ) -> OptimizedTeam:
        """Create final optimized team result with analysis"""
        # Calculate team statistics
        avg_performance = np.mean([m.past_performance for m in members])
        avg_collaboration = np.mean([m.collaboration_score for m in members])
        total_availability = np.sum([m.availability for m in members])
        
        # Role distribution
        role_dist = {}
        for member in members:
            for role in member.preferred_roles:
                role_dist[role] = role_dist.get(role, 0) + 1
        
        # Skill coverage
        skill_coverage = {}
        for skill in requirements.required_skills.keys():
            levels = [m.skills.get(skill, 0) for m in members]
            skill_coverage[skill] = max(levels) if levels else 0
        
        # Personality profile (average traits)
        personality_profile = {
            'openness': np.mean([m.openness for m in members]),
            'conscientiousness': np.mean([m.conscientiousness for m in members]),
            'extraversion': np.mean([m.extraversion for m in members]),
            'agreeableness': np.mean([m.agreeableness for m in members]),
            'neuroticism': np.mean([m.neuroticism for m in members])
        }
        
        # Calculate component scores
        compatibility_score = self._calculate_team_compatibility(members)
        skill_coverage_score = self._calculate_skill_coverage_score(
            members,
            requirements
        )
        diversity_score = self._calculate_team_diversity(members)
        balance_score = self._calculate_team_balance(members)
        
        # Generate insights
        strengths, gaps, recommendations = self._generate_team_insights(
            members,
            requirements,
            role_dist,
            skill_coverage
        )
        
        return OptimizedTeam(
            team_id=requirements.team_id,
            team_name=requirements.team_name,
            members=members,
            overall_score=overall_score,
            compatibility_score=compatibility_score,
            skill_coverage_score=skill_coverage_score,
            diversity_score=diversity_score,
            balance_score=balance_score,
            avg_performance=avg_performance,
            avg_collaboration=avg_collaboration,
            total_availability=total_availability,
            role_distribution=role_dist,
            skill_coverage=skill_coverage,
            personality_profile=personality_profile,
            strengths=strengths,
            gaps=gaps,
            recommendations=recommendations
        )
    
    def _calculate_team_compatibility(
        self,
        members: List[TeamMemberProfile]
    ) -> float:
        """Calculate overall team compatibility"""
        if len(members) < 2:
            return 100.0
        
        compatibilities = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                compat = self._calculate_personality_compatibility(
                    members[i],
                    members[j]
                )
                compatibilities.append(compat)
        
        return np.mean(compatibilities) if compatibilities else 100.0
    
    def _calculate_skill_coverage_score(
        self,
        members: List[TeamMemberProfile],
        requirements: TeamRequirements
    ) -> float:
        """Calculate how well team covers required skills"""
        if not requirements.required_skills:
            return 100.0
        
        coverage_scores = []
        for skill, min_level in requirements.required_skills.items():
            max_level = max([m.skills.get(skill, 0) for m in members])
            coverage = min(max_level / min_level, 1.0) if min_level > 0 else 1.0
            coverage_scores.append(coverage)
        
        return np.mean(coverage_scores) * 100
    
    def _calculate_team_diversity(
        self,
        members: List[TeamMemberProfile]
    ) -> float:
        """Calculate team diversity score"""
        if len(members) < 2:
            return 100.0
        
        # Department diversity
        departments = [m.department for m in members]
        dept_diversity = len(set(departments)) / len(departments)
        
        # Seniority diversity
        seniorities = [m.seniority_level for m in members]
        seniority_diversity = len(set(seniorities)) / len(seniorities)
        
        # Personality diversity (variance in traits)
        trait_arrays = np.array([
            [m.openness, m.conscientiousness, m.extraversion, 
             m.agreeableness, m.neuroticism]
            for m in members
        ])
        personality_variance = np.mean(np.var(trait_arrays, axis=0))
        personality_diversity = min(personality_variance / 500, 1.0)  # Normalize
        
        diversity_score = (
            dept_diversity * 0.3 +
            seniority_diversity * 0.3 +
            personality_diversity * 0.4
        ) * 100
        
        return diversity_score
    
    def _calculate_team_balance(
        self,
        members: List[TeamMemberProfile]
    ) -> float:
        """Calculate team balance score"""
        # Availability balance
        availabilities = [m.availability for m in members]
        avg_availability = np.mean(availabilities)
        
        # Collaboration balance
        collaborations = [m.collaboration_score for m in members]
        avg_collaboration = np.mean(collaborations)
        
        # Performance balance
        performances = [m.past_performance for m in members]
        performance_variance = np.var(performances)
        performance_balance = max(0, 1 - (performance_variance / 1000))
        
        balance_score = (
            (avg_availability / 100) * 0.3 +
            (avg_collaboration / 100) * 0.4 +
            performance_balance * 0.3
        ) * 100
        
        return balance_score
    
    def _generate_team_insights(
        self,
        members: List[TeamMemberProfile],
        requirements: TeamRequirements,
        role_dist: Dict[str, int],
        skill_coverage: Dict[str, float]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate team strengths, gaps, and recommendations"""
        strengths = []
        gaps = []
        recommendations = []
        
        # Analyze role coverage
        for role, required_count in requirements.required_roles.items():
            actual_count = role_dist.get(role, 0)
            if actual_count >= required_count:
                strengths.append(
                    f"Good {role} coverage: {actual_count} members"
                )
            else:
                gaps.append(
                    f"Insufficient {role} coverage: {actual_count}/{required_count}"
                )
                recommendations.append(
                    f"Consider adding more {role} members"
                )
        
        # Analyze skill coverage
        for skill, min_level in requirements.required_skills.items():
            coverage = skill_coverage.get(skill, 0)
            if coverage >= min_level:
                strengths.append(
                    f"Strong {skill} capability: {coverage:.1f}%"
                )
            else:
                gaps.append(
                    f"Low {skill} proficiency: {coverage:.1f}%"
                )
                recommendations.append(
                    f"Provide {skill} training or hire specialist"
                )
        
        # Analyze diversity
        departments = list(set(m.department for m in members))
        if len(departments) >= 3:
            strengths.append(
                f"Cross-functional team: {len(departments)} departments"
            )
        elif len(departments) == 1:
            gaps.append("Limited departmental diversity")
            recommendations.append(
                "Consider including members from other departments"
            )
        
        # Analyze personality balance
        avg_extraversion = np.mean([m.extraversion for m in members])
        if 40 <= avg_extraversion <= 60:
            strengths.append("Balanced introvert-extravert mix")
        elif avg_extraversion > 70:
            gaps.append("Team may be too extraverted")
            recommendations.append(
                "Consider adding introverted members for balance"
            )
        elif avg_extraversion < 30:
            gaps.append("Team may be too introverted")
            recommendations.append(
                "Consider adding extraverted members for external engagement"
            )
        
        return strengths, gaps, recommendations