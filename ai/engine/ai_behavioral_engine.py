# app/ai/engine/unified_behavioral_engine.py
"""
Unified Behavioral AI Engine for PsychSync

Combines personality profile synthesis with team analysis capabilities to provide:
- Personality-based role recommendations
- Team compatibility analysis
- Behavioral pattern insights
- Optimal team composition suggestions
- Multi-framework personality profile synthesis

Based on:
- Big Five personality traits (OCEAN)
- MBTI types
- Assessment scores
- Team dynamics
- Multiple personality frameworks (Enneagram, Predictive Index, Strengths)
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

# Import with fallbacks for optional ML libraries
try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using simplified models.")

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, Embedding, concatenate
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. Using simplified models.")

logger = logging.getLogger(__name__)


class PersonalityTrait(Enum):
    """Big Five personality traits (OCEAN)"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class TeamRole(Enum):
    """Belbin Team Roles"""
    COORDINATOR = "coordinator"
    SHAPER = "shaper"
    PLANT = "plant"
    RESOURCE_INVESTIGATOR = "resource_investigator"
    MONITOR_EVALUATOR = "monitor_evaluator"
    TEAMWORKER = "teamworker"
    IMPLEMENTER = "implementer"
    COMPLETER_FINISHER = "completer_finisher"
    SPECIALIST = "specialist"


@dataclass
class PersonalityProfile:
    """Individual personality profile"""
    user_id: int
    traits: Dict[PersonalityTrait, float]  # 0-100 scale
    mbti_type: Optional[str] = None
    assessment_scores: Dict[str, float] = field(default_factory=dict)
    unified_profile: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.assessment_scores:
            self.assessment_scores = {}
        if not self.unified_profile:
            self.unified_profile = {}


@dataclass
class RoleRecommendation:
    """Recommended role for a team member"""
    role: TeamRole
    confidence: float  # 0-1
    reasoning: List[str]
    alternative_roles: List[Tuple[TeamRole, float]]


@dataclass
class CompatibilityScore:
    """Compatibility between two team members"""
    user1_id: int
    user2_id: int
    score: float  # 0-1
    strengths: List[str]
    challenges: List[str]
    recommendations: List[str]


class UnifiedBehavioralEngine:
    """
    Unified AI-powered behavioral analysis engine
    
    Combines personality profile synthesis with team analysis capabilities
    """
    
    def __init__(self):
        """Initialize the unified engine with all necessary components"""
        # Initialize ML components
        self.models = {}
        self.scalers = {}
        self._load_models()
        
        # Initialize role mapping logic
        self.role_trait_requirements = self._initialize_role_requirements()
        self.mbti_role_preferences = self._initialize_mbti_mappings()
        
        logger.info("UnifiedBehavioralEngine initialized successfully")
    
    # ============================================
    # MODEL INITIALIZATION
    # ============================================
    
    def _load_models(self):
        """Load or initialize AI models"""
        try:
            if SKLEARN_AVAILABLE and TENSORFLOW_AVAILABLE:
                self.models['synthesis'] = self._create_synthesis_model()
                self.scalers['behavioral'] = StandardScaler()
                logger.info("Full AI models loaded successfully")
            else:
                self._initialize_simple_models()
                logger.info("Using simplified heuristic models")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            self._initialize_simple_models()
    
    def _create_synthesis_model(self):
        """Create neural network for personality framework synthesis"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        # Multi-input neural network
        enneagram_input = Input(shape=(9,), name='enneagram')
        mbti_input = Input(shape=(16,), name='mbti')
        big_five_input = Input(shape=(5,), name='big_five')
        pi_input = Input(shape=(4,), name='predictive_index')
        strengths_input = Input(shape=(34,), name='strengths')
        
        # Process each framework separately
        enneagram_dense = Dense(16, activation='relu')(enneagram_input)
        mbti_dense = Dense(32, activation='relu')(mbti_input)
        big_five_dense = Dense(8, activation='relu')(big_five_input)
        pi_dense = Dense(8, activation='relu')(pi_input)
        strengths_dense = Dense(16, activation='relu')(strengths_input)
        
        # Concatenate all processed inputs
        combined = concatenate([
            enneagram_dense, mbti_dense, big_five_dense, 
            pi_input, strengths_dense
        ])
        
        # Final synthesis layers
        synthesis = Dense(64, activation='relu')(combined)
        synthesis = Dropout(0.3)(synthesis)
        synthesis = Dense(32, activation='relu')(synthesis)
        output = Dense(20, activation='sigmoid', name='unified_profile')(synthesis)
        
        model = Model(
            inputs=[enneagram_input, mbti_input, big_five_input, pi_input, strengths_input],
            outputs=output
        )
        model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
        return model
    
    def _initialize_simple_models(self):
        """Initialize simplified heuristic models"""
        self.models = {'synthesis': None}
        self.scalers = {'behavioral': None}
    
    # ============================================
    # PERSONALITY PROFILE SYNTHESIS
    # ============================================
    
    def synthesize_personality_profile(self, user_id: int, assessments: Dict[str, Dict]) -> PersonalityProfile:
        """
        Combine insights from multiple personality frameworks into unified profile
        
        Args:
            user_id: Unique identifier for the user
            assessments: Dict with framework names as keys, results as values
            
        Returns:
            PersonalityProfile with synthesized traits and unified profile data
        """
        try:
            if not assessments:
                return self._create_default_profile(user_id)
            
            # Use AI synthesis if model is available, otherwise weighted combination
            if self.models['synthesis'] and len(assessments) >= 3:
                unified_profile = self._ai_synthesis(assessments)
            else:
                unified_profile = self._weighted_synthesis(assessments)
            
            # Add confidence and metadata
            unified_profile.update({
                'confidence': self._calculate_synthesis_confidence(assessments),
                'synthesis_method': 'ai_model' if self.models['synthesis'] else 'heuristic',
                'frameworks_used': list(assessments.keys()),
                'generated_at': datetime.utcnow().isoformat()
            })
            
            # Extract Big Five traits for the profile
            traits = {
                PersonalityTrait.OPENNESS: unified_profile.get('openness', 0.5) * 100,
                PersonalityTrait.CONSCIENTIOUSNESS: unified_profile.get('conscientiousness', 0.5) * 100,
                PersonalityTrait.EXTRAVERSION: unified_profile.get('extraversion', 0.5) * 100,
                PersonalityTrait.AGREEABLENESS: unified_profile.get('agreeableness', 0.5) * 100,
                PersonalityTrait.NEUROTICISM: unified_profile.get('neuroticism', 0.5) * 100,
            }
            
            # Extract MBTI type if available
            mbti_type = assessments.get('mbti', {}).get('type')
            
            return PersonalityProfile(
                user_id=user_id,
                traits=traits,
                mbti_type=mbti_type,
                assessment_scores=assessments,
                unified_profile=unified_profile
            )
            
        except Exception as e:
            logger.error(f"Error in personality synthesis: {str(e)}")
            return self._create_default_profile(user_id)
    
    def _weighted_synthesis(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
        """Simplified weighted combination of assessments"""
        # Framework weights based on research validity
        weights = {
            'big_five': 0.3,
            'mbti': 0.25,
            'enneagram': 0.2,
            'predictive_index': 0.15,
            'strengths': 0.1
        }
        
        # Initialize with neutral values
        dimensions = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
        
        total_weight = 0
        
        for framework, results in assessments.items():
            if framework not in weights or not results:
                continue
            
            weight = weights[framework]
            
            if framework == 'big_five':
                for dim in dimensions.keys():
                    if dim in results:
                        dimensions[dim] = dimensions[dim] * (1 - weight) + results[dim] * weight
                total_weight += weight
            elif framework == 'mbti' and 'type' in results:
                # Map MBTI to Big Five approximations
                big_five_approx = self._mbti_to_big_five(results['type'])
                for dim, value in big_five_approx.items():
                    dimensions[dim] = dimensions[dim] * (1 - weight) + value * weight
                total_weight += weight
        
        # Add derived metrics
        profile = dimensions.copy()
        profile.update({
            'leadership_potential': self._calculate_leadership_potential(dimensions),
            'collaboration_index': self._calculate_collaboration_index(dimensions),
            'stress_tolerance': self._calculate_stress_tolerance(dimensions),
            'adaptability': self._calculate_adaptability(dimensions),
            'communication_style': self._determine_communication_style(dimensions),
            'work_preferences': self._determine_work_preferences(dimensions)
        })
        
        return profile
    
    def _ai_synthesis(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
        """Use AI model to synthesize personality frameworks (placeholder for now)"""
        # This would use the neural network model for synthesis
        # For now, fall back to weighted synthesis
        return self._weighted_synthesis(assessments)
    
    def _create_default_profile(self, user_id: int) -> PersonalityProfile:
        """Create a default profile when synthesis fails"""
        default_traits = {
            PersonalityTrait.OPENNESS: 50.0,
            PersonalityTrait.CONSCIENTIOUSNESS: 50.0,
            PersonalityTrait.EXTRAVERSION: 50.0,
            PersonalityTrait.AGREEABLENESS: 50.0,
            PersonalityTrait.NEUROTICISM: 50.0
        }
        
        default_unified = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5,
            'leadership_potential': 0.5,
            'collaboration_index': 0.5,
            'stress_tolerance': 0.5,
            'adaptability': 0.5,
            'communication_style': 'analytical',
            'work_preferences': ['balanced_approach'],
            'confidence': 0.3,
            'synthesis_method': 'default',
            'frameworks_used': []
        }
        
        return PersonalityProfile(
            user_id=user_id,
            traits=default_traits,
            unified_profile=default_unified
        )
    
    # ============================================
    # ROLE RECOMMENDATIONS
    # ============================================
    
    def recommend_role(self, profile: PersonalityProfile) -> RoleRecommendation:
        """
        Recommend optimal team role based on personality profile
        
        Uses Big Five traits, MBTI, and assessment scores to determine
        best fit for Belbin team roles
        
        Args:
            profile: User's personality profile
            
        Returns:
            RoleRecommendation with confidence and reasoning
        """
        role_scores = {}
        
        # Score each role based on trait alignment
        for role in TeamRole:
            score = self._calculate_role_fit(profile, role)
            role_scores[role] = score
        
        # Sort roles by score
        sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get top recommendation
        best_role, best_score = sorted_roles[0]
        
        # Generate reasoning
        reasoning = self._generate_role_reasoning(profile, best_role)
        
        # Get alternative roles
        alternatives = [(role, score) for role, score in sorted_roles[1:4]]
        
        return RoleRecommendation(
            role=best_role,
            confidence=best_score,
            reasoning=reasoning,
            alternative_roles=alternatives
        )
    
    def _calculate_role_fit(self, profile: PersonalityProfile, role: TeamRole) -> float:
        """
        Calculate how well a profile fits a specific role
        
        Returns score from 0 to 1
        """
        requirements = self.role_trait_requirements.get(role, {})
        
        # Calculate trait alignment
        trait_score = 0.0
        trait_count = 0
        
        for trait, (required_min, required_max) in requirements.items():
            if trait in profile.traits:
                user_value = profile.traits[trait]
                
                # Check if within optimal range
                if required_min <= user_value <= required_max:
                    trait_score += 1.0
                else:
                    # Partial score based on distance from range
                    if user_value < required_min:
                        distance = required_min - user_value
                    else:
                        distance = user_value - required_max
                    
                    # Penalize based on distance
                    trait_score += max(0, 1.0 - (distance / 50.0))
                
                trait_count += 1
        
        if trait_count == 0:
            return 0.5  # Default score if no traits available
        
        base_score = trait_score / trait_count
        
        # Adjust based on MBTI if available
        if profile.mbti_type:
            mbti_adjustment = self._get_mbti_role_affinity(profile.mbti_type, role)
            base_score = (base_score * 0.7) + (mbti_adjustment * 0.3)
        
        # Adjust based on unified profile metrics if available
        if profile.unified_profile:
            leadership = profile.unified_profile.get('leadership_potential', 0.5)
            collaboration = profile.unified_profile.get('collaboration_index', 0.5)
            
            # Boost score for leadership roles if high leadership potential
            if role in [TeamRole.COORDINATOR, TeamRole.SHAPER] and leadership > 0.7:
                base_score = min(1.0, base_score + 0.1)
            
            # Boost score for collaborative roles if high collaboration index
            if role in [TeamRole.TEAMWORKER, TeamRole.COORDINATOR] and collaboration > 0.7:
                base_score = min(1.0, base_score + 0.1)
        
        return base_score
    
    def _generate_role_reasoning(
        self,
        profile: PersonalityProfile,
        role: TeamRole
    ) -> List[str]:
        """Generate human-readable reasoning for role recommendation"""
        reasoning = []
        
        # Trait-based reasoning
        requirements = self.role_trait_requirements.get(role, {})
        
        for trait, (req_min, req_max) in requirements.items():
            if trait in profile.traits:
                value = profile.traits[trait]
                
                if req_min <= value <= req_max:
                    reasoning.append(
                        f"Your {trait.value} level ({value:.0f}/100) is ideal for this role"
                    )
        
        # MBTI-based reasoning
        if profile.mbti_type:
            mbti_roles = self.mbti_role_preferences.get(profile.mbti_type, [])
            if role in mbti_roles:
                reasoning.append(
                    f"Your MBTI type ({profile.mbti_type}) naturally excels in this role"
                )
        
        # Unified profile-based reasoning
        if profile.unified_profile:
            leadership = profile.unified_profile.get('leadership_potential', 0.5)
            collaboration = profile.unified_profile.get('collaboration_index', 0.5)
            
            if role in [TeamRole.COORDINATOR, TeamRole.SHAPER] and leadership > 0.7:
                reasoning.append("High leadership potential indicates strong fit for this role")
            
            if role in [TeamRole.TEAMWORKER, TeamRole.COORDINATOR] and collaboration > 0.7:
                reasoning.append("High collaboration index suggests effectiveness in this role")
        
        # Assessment-based reasoning
        if profile.assessment_scores:
            avg_score = np.mean(list(profile.assessment_scores.values()))
            if avg_score > 70:
                reasoning.append("Your overall assessment scores indicate strong team performance")
        
        return reasoning[:3]  # Return top 3 reasons
    
    # ============================================
    # COMPATIBILITY ANALYSIS
    # ============================================
    
    def analyze_compatibility(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> CompatibilityScore:
        """
        Analyze compatibility between two team members
        
        Considers:
        - Trait complementarity
        - MBTI compatibility
        - Work style alignment
        
        Args:
            profile1: First user's profile
            profile2: Second user's profile
            
        Returns:
            CompatibilityScore with insights
        """
        # Calculate trait similarity/complementarity
        trait_score = self._calculate_trait_compatibility(profile1, profile2)
        
        # Calculate MBTI compatibility if available
        mbti_score = 0.5  # Default
        if profile1.mbti_type and profile2.mbti_type:
            mbti_score = self._calculate_mbti_compatibility(
                profile1.mbti_type,
                profile2.mbti_type
            )
        
        # Calculate unified profile compatibility if available
        unified_score = 0.5  # Default
        if profile1.unified_profile and profile2.unified_profile:
            unified_score = self._calculate_unified_profile_compatibility(
                profile1.unified_profile,
                profile2.unified_profile
            )
        
        # Combine scores
        overall_score = (trait_score * 0.4) + (mbti_score * 0.3) + (unified_score * 0.3)
        
        # Generate insights
        strengths = self._identify_compatibility_strengths(profile1, profile2)
        challenges = self._identify_compatibility_challenges(profile1, profile2)
        recommendations = self._generate_compatibility_recommendations(
            profile1, profile2, strengths, challenges
        )
        
        return CompatibilityScore(
            user1_id=profile1.user_id,
            user2_id=profile2.user_id,
            score=overall_score,
            strengths=strengths,
            challenges=challenges,
            recommendations=recommendations
        )
    
    def _calculate_trait_compatibility(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> float:
        """
        Calculate Big Five trait compatibility
        
        Some traits benefit from similarity (Conscientiousness)
        Others from complementarity (Extraversion/Introversion)
        """
        compatibility = 0.0
        count = 0
        
        for trait in PersonalityTrait:
            if trait in profile1.traits and trait in profile2.traits:
                value1 = profile1.traits[trait]
                value2 = profile2.traits[trait]
                
                difference = abs(value1 - value2)
                
                # Traits that benefit from similarity
                if trait in [PersonalityTrait.CONSCIENTIOUSNESS, PersonalityTrait.AGREEABLENESS]:
                    # Lower difference = better compatibility
                    trait_compat = 1.0 - (difference / 100.0)
                
                # Traits that benefit from balance
                elif trait == PersonalityTrait.EXTRAVERSION:
                    # Moderate difference is good (one extrovert, one introvert)
                    if 20 <= difference <= 50:
                        trait_compat = 1.0
                    else:
                        trait_compat = 0.7
                
                # Neuroticism: both low is best
                elif trait == PersonalityTrait.NEUROTICISM:
                    avg_neuroticism = (value1 + value2) / 2
                    trait_compat = 1.0 - (avg_neuroticism / 100.0)
                
                # Openness: diversity is good
                else:
                    trait_compat = 0.8  # Neutral
                
                compatibility += trait_compat
                count += 1
        
        return compatibility / count if count > 0 else 0.5
    
    def _calculate_unified_profile_compatibility(
        self,
        profile1: Dict[str, Any],
        profile2: Dict[str, Any]
    ) -> float:
        """Calculate compatibility based on unified profile metrics"""
        compatibility = 0.0
        count = 0
        
        # Compare communication styles
        style1 = profile1.get('communication_style', '')
        style2 = profile2.get('communication_style', '')
        
        if style1 and style2:
            # Some styles work well together
            compatible_pairs = [
                ('collaborative', 'supportive'),
                ('assertive', 'analytical'),
                ('supportive', 'collaborative'),
                ('analytical', 'assertive')
            ]
            
            if (style1, style2) in compatible_pairs or (style2, style1) in compatible_pairs:
                compatibility += 0.8
            elif style1 == style2:
                compatibility += 0.6  # Same style is moderately compatible
            else:
                compatibility += 0.4  # Different styles are less compatible
            
            count += 1
        
        # Compare work preferences
        prefs1 = set(profile1.get('work_preferences', []))
        prefs2 = set(profile2.get('work_preferences', []))
        
        if prefs1 and prefs2:
            overlap = len(prefs1.intersection(prefs2))
            total = len(prefs1.union(prefs2))
            
            if total > 0:
                pref_compat = overlap / total
                compatibility += pref_compat
                count += 1
        
        # Compare leadership and collaboration styles
        leadership1 = profile1.get('leadership_potential', 0.5)
        leadership2 = profile2.get('leadership_potential', 0.5)
        
        # One high leader and one moderate collaborator is ideal
        if (leadership1 > 0.7 and 0.4 < leadership2 < 0.7) or (leadership2 > 0.7 and 0.4 < leadership1 < 0.7):
            compatibility += 0.8
        # Both high leaders might conflict
        elif leadership1 > 0.7 and leadership2 > 0.7:
            compatibility += 0.4
        # Both low leaders might lack direction
        elif leadership1 < 0.4 and leadership2 < 0.4:
            compatibility += 0.5
        else:
            compatibility += 0.7
        
        count += 1
        
        return compatibility / count if count > 0 else 0.5
    
    # ============================================
    # TEAM COMPOSITION ANALYSIS
    # ============================================
    
    def analyze_team_composition(
        self,
        profiles: List[PersonalityProfile]
    ) -> Dict[str, Any]:
        """
        Analyze overall team composition and suggest improvements
        
        Args:
            profiles: List of all team member profiles
            
        Returns:
            Analysis with role distribution, gaps, and recommendations
        """
        # Get role recommendations for each member
        role_assignments = {}
        for profile in profiles:
            recommendation = self.recommend_role(profile)
            role_assignments[profile.user_id] = recommendation.role
        
        # Analyze role distribution
        role_counts = {}
        for role in role_assignments.values():
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Identify gaps and overlaps
        gaps = self._identify_role_gaps(role_counts)
        overlaps = self._identify_role_overlaps(role_counts)
        
        # Calculate team diversity
        diversity_score = self._calculate_team_diversity(profiles)
        
        # Calculate team dynamics based on unified profiles
        team_dynamics = self._calculate_team_dynamics(profiles)
        
        # Generate recommendations
        recommendations = self._generate_team_recommendations(
            profiles, role_counts, gaps, overlaps, team_dynamics
        )
        
        return {
            'role_distribution': dict(role_counts),
            'gaps': gaps,
            'overlaps': overlaps,
            'diversity_score': diversity_score,
            'team_dynamics': team_dynamics,
            'recommendations': recommendations,
            'optimal_size': self._suggest_optimal_team_size(len(profiles))
        }
    
    def _calculate_team_dynamics(self, profiles: List[PersonalityProfile]) -> Dict[str, Any]:
        """Calculate team dynamics based on unified profiles"""
        dynamics = {
            'leadership_distribution': {},
            'communication_styles': {},
            'work_preference_alignment': {},
            'overall_collaboration': 0.0,
            'adaptability': 0.0,
            'stress_resilience': 0.0
        }
        
        # Count leadership levels
        leadership_levels = {'high': 0, 'medium': 0, 'low': 0}
        for profile in profiles:
            if profile.unified_profile:
                leadership = profile.unified_profile.get('leadership_potential', 0.5)
                if leadership > 0.7:
                    leadership_levels['high'] += 1
                elif leadership > 0.4:
                    leadership_levels['medium'] += 1
                else:
                    leadership_levels['low'] += 1
        
        dynamics['leadership_distribution'] = leadership_levels
        
        # Count communication styles
        comm_styles = {}
        for profile in profiles:
            if profile.unified_profile:
                style = profile.unified_profile.get('communication_style', 'unknown')
                comm_styles[style] = comm_styles.get(style, 0) + 1
        
        dynamics['communication_styles'] = comm_styles
        
        # Calculate average metrics
        total_collaboration = 0.0
        total_adaptability = 0.0
        total_stress_tolerance = 0.0
        count = 0
        
        for profile in profiles:
            if profile.unified_profile:
                total_collaboration += profile.unified_profile.get('collaboration_index', 0.5)
                total_adaptability += profile.unified_profile.get('adaptability', 0.5)
                total_stress_tolerance += profile.unified_profile.get('stress_tolerance', 0.5)
                count += 1
        
        if count > 0:
            dynamics['overall_collaboration'] = total_collaboration / count
            dynamics['adaptability'] = total_adaptability / count
            dynamics['stress_resilience'] = total_stress_tolerance / count
        
        return dynamics
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _mbti_to_big_five(self, mbti_type: str) -> Dict[str, float]:
        """Approximate MBTI type to Big Five dimensions"""
        result = {
            'openness': 0.5, 
            'conscientiousness': 0.5, 
            'extraversion': 0.5, 
            'agreeableness': 0.5, 
            'neuroticism': 0.5
        }
        
        if 'E' in mbti_type:
            result['extraversion'] = 0.75
        elif 'I' in mbti_type:
            result['extraversion'] = 0.25
        
        if 'N' in mbti_type:
            result['openness'] = 0.7
        elif 'S' in mbti_type:
            result['openness'] = 0.3
        
        if 'F' in mbti_type:
            result['agreeableness'] = 0.7
        elif 'T' in mbti_type:
            result['agreeableness'] = 0.3
        
        if 'J' in mbti_type:
            result['conscientiousness'] = 0.7
        elif 'P' in mbti_type:
            result['conscientiousness'] = 0.3
        
        return result
    
    def _calculate_synthesis_confidence(self, assessments: Dict[str, Dict]) -> float:
        """Calculate confidence in synthesis based on data quality"""
        base_confidence = 0.4
        framework_bonus = len(assessments) * 0.1
        
        # Bonus for high-quality frameworks
        quality_bonus = 0
        for framework in assessments:
            if framework in ['big_five', 'mbti', 'predictive_index']:
                quality_bonus += 0.1
        
        # Penalty for missing key frameworks
        if 'big_five' not in assessments and 'mbti' not in assessments:
            quality_bonus -= 0.2
        
        confidence = min(0.95, base_confidence + framework_bonus + quality_bonus)
        return max(0.1, confidence)
    
    def _calculate_leadership_potential(self, dimensions: Dict[str, float]) -> float:
        """Calculate leadership potential from personality dimensions"""
        return (
            dimensions.get('extraversion', 0.5) * 0.3 +
            dimensions.get('conscientiousness', 0.5) * 0.25 +
            dimensions.get('openness', 0.5) * 0.2 +
            dimensions.get('agreeableness', 0.5) * 0.15 +
            (1 - dimensions.get('neuroticism', 0.5)) * 0.1
        )
    
    def _calculate_collaboration_index(self, dimensions: Dict[str, float]) -> float:
        """Calculate collaboration effectiveness"""
        return (
            dimensions.get('agreeableness', 0.5) * 0.4 +
            dimensions.get('extraversion', 0.5) * 0.3 +
            dimensions.get('openness', 0.5) * 0.2 +
            (1 - dimensions.get('neuroticism', 0.5)) * 0.1
        )
    
    def _calculate_stress_tolerance(self, dimensions: Dict[str, float]) -> float:
        """Calculate stress tolerance"""
        return (
            (1 - dimensions.get('neuroticism', 0.5)) * 0.5 +
            dimensions.get('conscientiousness', 0.5) * 0.3 +
            dimensions.get('extraversion', 0.5) * 0.2
        )
    
    def _calculate_adaptability(self, dimensions: Dict[str, float]) -> float:
        """Calculate adaptability to change"""
        return (
            dimensions.get('openness', 0.5) * 0.4 +
            (1 - dimensions.get('neuroticism', 0.5)) * 0.3 +
            dimensions.get('extraversion', 0.5) * 0.2 +
            (1 - dimensions.get('conscientiousness', 0.5)) * 0.1
        )
    
    def _determine_communication_style(self, dimensions: Dict[str, float]) -> str:
        """Determine primary communication style"""
        extraversion = dimensions.get('extraversion', 0.5)
        agreeableness = dimensions.get('agreeableness', 0.5)
        
        if extraversion > 0.6 and agreeableness > 0.6:
            return "collaborative"
        elif extraversion > 0.6 and agreeableness < 0.4:
            return "assertive"
        elif extraversion < 0.4 and agreeableness > 0.6:
            return "supportive"
        else:
            return "analytical"
    
    def _determine_work_preferences(self, dimensions: Dict[str, float]) -> List[str]:
        """Determine work environment preferences"""
        preferences = []
        
        if dimensions.get('openness', 0.5) > 0.6:
            preferences.extend(["creative_projects", "innovation"])
        if dimensions.get('conscientiousness', 0.5) > 0.6:
            preferences.extend(["structured_environment", "clear_deadlines"])
        if dimensions.get('extraversion', 0.5) > 0.6:
            preferences.extend(["team_collaboration", "public_speaking"])
        else:
            preferences.extend(["focused_work", "minimal_interruptions"])
        
        return preferences
    
    def _calculate_mbti_compatibility(self, type1: str, type2: str) -> float:
        """
        Calculate MBTI compatibility
        
        Based on cognitive function theory and typical interactions
        """
        # MBTI compatibility matrix (simplified)
        compatibility_map = {
            'INTJ': {'ENFP': 0.9, 'ENTP': 0.9, 'INFJ': 0.8},
            'INTP': {'ENTJ': 0.9, 'ENFJ': 0.8, 'INFP': 0.8},
            'ENTJ': {'INTP': 0.9, 'INFP': 0.8, 'INTJ': 0.8},
            'ENTP': {'INFJ': 0.9, 'INTJ': 0.9, 'ENFJ': 0.8},
            'INFJ': {'ENTP': 0.9, 'ENFP': 0.9, 'INTJ': 0.8},
            'INFP': {'ENFJ': 0.9, 'ENTJ': 0.8, 'INTP': 0.8},
            'ENFJ': {'INFP': 0.9, 'ISFP': 0.8, 'INTP': 0.8},
            'ENFP': {'INTJ': 0.9, 'INFJ': 0.9, 'ENTJ': 0.8},
            'ISTJ': {'ESFP': 0.8, 'ESTP': 0.8, 'ISFJ': 0.7},
            'ISFJ': {'ESFP': 0.8, 'ESTP': 0.8, 'ISTJ': 0.7},
            'ESTJ': {'ISFP': 0.8, 'ISTP': 0.8, 'ISTJ': 0.7},
            'ESFJ': {'ISFP': 0.8, 'ISTP': 0.8, 'ISFJ': 0.7},
            'ISTP': {'ESTJ': 0.8, 'ESFJ': 0.8, 'ESTP': 0.7},
            'ISFP': {'ESTJ': 0.8, 'ESFJ': 0.8, 'ENFJ': 0.8},
            'ESTP': {'ISFJ': 0.8, 'ISTJ': 0.8, 'ISTP': 0.7},
            'ESFP': {'ISTJ': 0.8, 'ISFJ': 0.8, 'ESFJ': 0.7}
        }
        
        # Check both directions
        score1 = compatibility_map.get(type1, {}).get(type2, 0.6)
        score2 = compatibility_map.get(type2, {}).get(type1, 0.6)
        
        return (score1 + score2) / 2
    
    def _identify_compatibility_strengths(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> List[str]:
        """Identify compatibility strengths"""
        strengths = []
        
        # Check trait complementarity
        for trait in PersonalityTrait:
            if trait in profile1.traits and trait in profile2.traits:
                v1, v2 = profile1.traits[trait], profile2.traits[trait]
                
                if trait == PersonalityTrait.CONSCIENTIOUSNESS:
                    if abs(v1 - v2) < 20 and v1 > 60:
                        strengths.append("Both highly organized and reliable")
                
                elif trait == PersonalityTrait.AGREEABLENESS:
                    if abs(v1 - v2) < 20 and v1 > 60:
                        strengths.append("Strong collaborative potential")
                
                elif trait == PersonalityTrait.EXTRAVERSION:
                    if abs(v1 - v2) > 30:
                        strengths.append("Balanced energy dynamics (one leads, one supports)")
        
        # Check unified profile compatibility
        if profile1.unified_profile and profile2.unified_profile:
            style1 = profile1.unified_profile.get('communication_style', '')
            style2 = profile2.unified_profile.get('communication_style', '')
            
            if style1 and style2:
                if (style1 == 'collaborative' and style2 == 'supportive') or (style1 == 'supportive' and style2 == 'collaborative'):
                    strengths.append("Complementary communication styles")
                elif style1 == style2:
                    strengths.append(f"Shared {style1} communication approach")
            
            # Check work preference alignment
            prefs1 = set(profile1.unified_profile.get('work_preferences', []))
            prefs2 = set(profile2.unified_profile.get('work_preferences', []))
            
            if prefs1 and prefs2:
                overlap = prefs1.intersection(prefs2)
                if overlap:
                    strengths.append(f"Shared work preferences: {', '.join(list(overlap)[:2])}")
        
        return strengths[:3]
    
    def _identify_compatibility_challenges(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile
    ) -> List[str]:
        """Identify potential compatibility challenges"""
        challenges = []
        
        for trait in PersonalityTrait:
            if trait in profile1.traits and trait in profile2.traits:
                v1, v2 = profile1.traits[trait], profile2.traits[trait]
                
                if trait == PersonalityTrait.NEUROTICISM:
                    if v1 > 70 or v2 > 70:
                        challenges.append("May need stress management strategies")
                
                elif trait == PersonalityTrait.CONSCIENTIOUSNESS:
                    if abs(v1 - v2) > 40:
                        challenges.append("Different approaches to organization and deadlines")
        
        # Check unified profile challenges
        if profile1.unified_profile and profile2.unified_profile:
            leadership1 = profile1.unified_profile.get('leadership_potential', 0.5)
            leadership2 = profile2.unified_profile.get('leadership_potential', 0.5)
            
            if leadership1 > 0.7 and leadership2 > 0.7:
                challenges.append("Potential leadership conflicts - clarify decision-making hierarchy")
            
            style1 = profile1.unified_profile.get('communication_style', '')
            style2 = profile2.unified_profile.get('communication_style', '')
            
            if style1 and style2:
                if (style1 == 'assertive' and style2 == 'supportive') or (style1 == 'supportive' and style2 == 'assertive'):
                    challenges.append("Different communication approaches may require mutual understanding")
        
        return challenges[:3]
    
    def _generate_compatibility_recommendations(
        self,
        profile1: PersonalityProfile,
        profile2: PersonalityProfile,
        strengths: List[str],
        challenges: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if challenges:
            recommendations.append("Schedule regular check-ins to align on work styles")
        
        if strengths:
            recommendations.append("Leverage complementary strengths on complex projects")
        
        # Add specific recommendations based on unified profiles
        if profile1.unified_profile and profile2.unified_profile:
            leadership1 = profile1.unified_profile.get('leadership_potential', 0.5)
            leadership2 = profile2.unified_profile.get('leadership_potential', 0.5)
            
            if leadership1 > 0.7 and leadership2 > 0.7:
                recommendations.append("Establish clear decision-making protocols to avoid conflicts")
            elif leadership1 < 0.4 and leadership2 < 0.4:
                recommendations.append("Consider designating a project lead for direction")
            
            style1 = profile1.unified_profile.get('communication_style', '')
            style2 = profile2.unified_profile.get('communication_style', '')
            
            if style1 != style2:
                recommendations.append(f"Acknowledge different communication styles ({style1} vs {style2})")
        
        recommendations.append("Use clear communication protocols to minimize misunderstandings")
        
        return recommendations[:3]
    
    def _identify_role_gaps(self, role_counts: Dict[TeamRole, int]) -> List[TeamRole]:
        """Identify missing critical roles"""
        critical_roles = [
            TeamRole.COORDINATOR,
            TeamRole.IMPLEMENTER,
            TeamRole.PLANT
        ]
        
        return [role for role in critical_roles if role_counts.get(role, 0) == 0]
    
    def _identify_role_overlaps(self, role_counts: Dict[TeamRole, int]) -> List[TeamRole]:
        """Identify over-represented roles"""
        return [role for role, count in role_counts.items() if count > 2]
    
    def _calculate_team_diversity(self, profiles: List[PersonalityProfile]) -> float:
        """Calculate team personality diversity (0-1)"""
        if len(profiles) < 2:
            return 0.0
        
        # Calculate variance in traits
        trait_variances = []
        
        for trait in PersonalityTrait:
            values = [p.traits.get(trait, 50) for p in profiles if trait in p.traits]
            if values:
                variance = np.var(values)
                trait_variances.append(variance)
        
        if not trait_variances:
            return 0.5
        
        # Higher variance = more diversity
        avg_variance = np.mean(trait_variances)
        
        # Normalize to 0-1 scale (assuming max variance is ~400 for 0-100 scale)
        return min(1.0, avg_variance / 400.0)
    
    def _generate_team_recommendations(
        self,
        profiles: List[PersonalityProfile],
        role_counts: Dict[TeamRole, int],
        gaps: List[TeamRole],
        overlaps: List[TeamRole],
        team_dynamics: Dict[str, Any]
    ) -> List[str]:
        """Generate team improvement recommendations"""
        recommendations = []
        
        if gaps:
            gap_names = [role.value.replace('_', ' ').title() for role in gaps]
            recommendations.append(
                f"Consider recruiting for these roles: {', '.join(gap_names)}"
            )
        
        if overlaps:
            overlap_names = [role.value.replace('_', ' ').title() for role in overlaps]
            recommendations.append(
                f"Multiple members in these roles: {', '.join(overlap_names)}. "
                "Consider sub-teams or role rotation."
            )
        
        diversity_score = self._calculate_team_diversity(profiles)
        if diversity_score < 0.3:
            recommendations.append(
                "Team shows low personality diversity. "
                "Consider adding members with different traits for better balance."
            )
        
        # Add recommendations based on team dynamics
        leadership_dist = team_dynamics.get('leadership_distribution', {})
        if leadership_dist.get('high', 0) > 2:
            recommendations.append(
                "Multiple strong leaders may create conflicts. "
                "Establish clear decision-making hierarchy."
            )
        elif leadership_dist.get('high', 0) == 0 and leadership_dist.get('medium', 0) < 2:
            recommendations.append(
                "Team lacks clear leadership. Consider designating a project lead."
            )
        
        comm_styles = team_dynamics.get('communication_styles', {})
        if len(comm_styles) == 1:
            style = list(comm_styles.keys())[0]
            recommendations.append(
                f"Team has uniform {style} communication style. "
                "Consider adding diverse perspectives."
            )
        
        if team_dynamics.get('overall_collaboration', 0.5) < 0.5:
            recommendations.append(
                "Team shows low collaboration potential. "
                "Consider team-building activities and clarifying roles."
            )
        
        if team_dynamics.get('stress_resilience', 0.5) < 0.5:
            recommendations.append(
                "Team may struggle under pressure. "
                "Implement stress management strategies and regular check-ins."
            )
        
        return recommendations
    
    def _suggest_optimal_team_size(self, current_size: int) -> str:
        """Suggest optimal team size based on research"""
        if current_size < 5:
            return "Consider expanding (optimal: 5-9 members)"
        elif current_size > 12:
            return "Consider splitting into sub-teams (optimal: 5-9 members)"
        else:
            return "Team size is optimal"
    
    # ============================================
    # INITIALIZATION
    # ============================================
    
    def _initialize_role_requirements(self) -> Dict[TeamRole, Dict[PersonalityTrait, Tuple[float, float]]]:
        """
        Initialize optimal trait ranges for each Belbin role
        
        Returns dict mapping roles to trait requirements (min, max)
        """
        return {
            TeamRole.COORDINATOR: {
                PersonalityTrait.EXTRAVERSION: (60, 90),
                PersonalityTrait.AGREEABLENESS: (70, 95),
                PersonalityTrait.CONSCIENTIOUSNESS: (60, 85),
            },
            TeamRole.SHAPER: {
                PersonalityTrait.EXTRAVERSION: (70, 95),
                PersonalityTrait.CONSCIENTIOUSNESS: (65, 90),
                PersonalityTrait.NEUROTICISM: (20, 50),
            },
            TeamRole.PLANT: {
                PersonalityTrait.OPENNESS: (75, 100),
                PersonalityTrait.EXTRAVERSION: (30, 60),
                PersonalityTrait.CONSCIENTIOUSNESS: (50, 75),
            },
            TeamRole.RESOURCE_INVESTIGATOR: {
                PersonalityTrait.EXTRAVERSION: (75, 100),
                PersonalityTrait.OPENNESS: (65, 90),
                PersonalityTrait.AGREEABLENESS: (60, 85),
            },
            TeamRole.MONITOR_EVALUATOR: {
                PersonalityTrait.OPENNESS: (60, 85),
                PersonalityTrait.EXTRAVERSION: (40, 70),
                PersonalityTrait.CONSCIENTIOUSNESS: (70, 95),
            },
            TeamRole.TEAMWORKER: {
                PersonalityTrait.AGREEABLENESS: (75, 100),
                PersonalityTrait.EXTRAVERSION: (50, 80),
                PersonalityTrait.NEUROTICISM: (20, 50),
            },
            TeamRole.IMPLEMENTER: {
                PersonalityTrait.CONSCIENTIOUSNESS: (80, 100),
                PersonalityTrait.AGREEABLENESS: (60, 85),
                PersonalityTrait.NEUROTICISM: (20, 50),
            },
            TeamRole.COMPLETER_FINISHER: {
                PersonalityTrait.CONSCIENTIOUSNESS: (85, 100),
                PersonalityTrait.NEUROTICISM: (40, 70),
                PersonalityTrait.EXTRAVERSION: (30, 60),
            },
            TeamRole.SPECIALIST: {
                PersonalityTrait.OPENNESS: (70, 95),
                PersonalityTrait.CONSCIENTIOUSNESS: (75, 95),
                PersonalityTrait.EXTRAVERSION: (30, 60),
            }
        }
    
    def _initialize_mbti_mappings(self) -> Dict[str, List[TeamRole]]:
        """Map MBTI types to preferred roles"""
        return {
            'INTJ': [TeamRole.MONITOR_EVALUATOR, TeamRole.SPECIALIST],
            'INTP': [TeamRole.PLANT, TeamRole.SPECIALIST],
            'ENTJ': [TeamRole.SHAPER, TeamRole.COORDINATOR],
            'ENTP': [TeamRole.RESOURCE_INVESTIGATOR, TeamRole.PLANT],
            'INFJ': [TeamRole.TEAMWORKER, TeamRole.COORDINATOR],
            'INFP': [TeamRole.PLANT, TeamRole.TEAMWORKER],
            'ENFJ': [TeamRole.COORDINATOR, TeamRole.TEAMWORKER],
            'ENFP': [TeamRole.RESOURCE_INVESTIGATOR, TeamRole.PLANT],
            'ISTJ': [TeamRole.IMPLEMENTER, TeamRole.COMPLETER_FINISHER],
            'ISFJ': [TeamRole.TEAMWORKER, TeamRole.IMPLEMENTER],
            'ESTJ': [TeamRole.COORDINATOR, TeamRole.IMPLEMENTER],
            'ESFJ': [TeamRole.COORDINATOR, TeamRole.TEAMWORKER],
            'ISTP': [TeamRole.SPECIALIST, TeamRole.IMPLEMENTER],
            'ISFP': [TeamRole.TEAMWORKER, TeamRole.SPECIALIST],
            'ESTP': [TeamRole.SHAPER, TeamRole.RESOURCE_INVESTIGATOR],
            'ESFP': [TeamRole.RESOURCE_INVESTIGATOR, TeamRole.TEAMWORKER]
        }
    
    def _get_mbti_role_affinity(self, mbti_type: str, role: TeamRole) -> float:
        """Get affinity score for MBTI type and role"""
        preferred_roles = self.mbti_role_preferences.get(mbti_type, [])
        
        if role in preferred_roles:
            # Primary or secondary preferred role
            index = preferred_roles.index(role)
            return 1.0 if index == 0 else 0.8
        
        return 0.5  # Neutral affinity


# Global instance
unified_engine = UnifiedBehavioralEngine()
