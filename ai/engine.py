
#ai/engine.py

# ai/engine.py - Core AI and Machine Learning Components
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json

# Import ML libraries with fallbacks
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
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

class BehavioralAIEngine:
    """Main AI engine for behavioral analysis and synthesis"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.load_pretrained_models()
        
    def load_pretrained_models(self):
        """Load pre-trained models or initialize new ones"""
        try:
            if SKLEARN_AVAILABLE and TENSORFLOW_AVAILABLE:
                # Load full ML models
                self.models['compatibility'] = self._create_compatibility_model()
                self.models['performance'] = self._create_performance_model()
                self.models['conflict'] = self._create_conflict_model()
                self.models['synthesis'] = self._create_synthesis_model()
                self.scalers['behavioral'] = StandardScaler()
            else:
                # Use simplified heuristic models
                self._initialize_simple_models()
            
            logger.info("AI models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            self._initialize_simple_models()
    
    def _create_compatibility_model(self):
        """Create neural network for team compatibility prediction"""
        if not TENSORFLOW_AVAILABLE:
            return None
            
        model = Sequential([
            Dense(128, activation='relu', input_shape=(50,)),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
        return model
    
    def _create_performance_model(self):
        """Create LSTM model for team performance prediction"""
        if not TENSORFLOW_AVAILABLE:
            return None
            
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(10, 20)),
            Dropout(0.3),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')
        ])
        model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
        return model
    
    def _create_conflict_model(self):
        """Create conflict prediction classifier"""
        if not SKLEARN_AVAILABLE:
            return None
            
        return GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
    
    def _create_synthesis_model(self):
        """Create model for synthesizing multiple personality frameworks"""
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
            pi_dense, strengths_dense
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
        self.models = {
            'compatibility': None,
            'performance': None,
            'conflict': None,
            'synthesis': None
        }
        self.scalers = {'behavioral': None}
        logger.info("Using simplified heuristic models")
    
    def synthesize_personality_profile(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Combine insights from multiple personality frameworks into unified profile
        
        Args:
            assessments: Dict with framework names as keys, results as values
            
        Returns:
            Unified personality profile with standardized metrics
        """
        try:
            if not assessments:
                return self._default_profile()
                
            # Use simplified weighted synthesis
            unified_profile = self._weighted_synthesis(assessments)
            
            # Add confidence score based on data completeness
            confidence = self._calculate_synthesis_confidence(assessments)
            unified_profile['confidence'] = confidence
            unified_profile['synthesis_method'] = 'heuristic'
            unified_profile['frameworks_used'] = list(assessments.keys())
            
            return unified_profile
            
        except Exception as e:
            logger.error(f"Error in personality synthesis: {str(e)}")
            return self._default_profile()
    
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
        
        # Start with neutral values
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
    
    def _mbti_to_big_five(self, mbti_type: str) -> Dict[str, float]:
        """Approximate MBTI type to Big Five dimensions"""
        # Simplified mapping based on research correlations
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
    
    def _default_profile(self) -> Dict[str, Any]:
        """Default profile when synthesis fails"""
        return {
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


class TeamOptimizer:
    """Optimize team composition and dynamics"""
    
    def __init__(self):
        self.compatibility_calculator = CompatibilityCalculator()
        
    def optimize_team_composition(
        self,
        team_profiles: List[Dict],
        project_requirements: Dict[str, Any],
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize team composition for maximum effectiveness
        """
        try:
            if not team_profiles:
                return self._empty_team_result()
            
            # Calculate pairwise compatibility matrix
            compatibility_matrix = self._calculate_team_compatibility_matrix(team_profiles)
            
            # Analyze current team composition
            current_metrics = self._analyze_current_composition(team_profiles, compatibility_matrix)
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(
                team_profiles, compatibility_matrix, project_requirements, optimization_goals
            )
            
            # Predict team performance
            performance_prediction = self._predict_team_performance(
                team_profiles, compatibility_matrix, project_requirements
            )
            
            return {
                'current_metrics': current_metrics,
                'compatibility_matrix': compatibility_matrix,
                'recommendations': recommendations,
                'performance_prediction': performance_prediction,
                'optimization_score': current_metrics['overall_score'],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in team optimization: {str(e)}")
            return self._fallback_optimization_result(team_profiles)
    
    def _calculate_team_compatibility_matrix(self, team_profiles: List[Dict]) -> List[List[float]]:
        """Calculate compatibility between all team member pairs"""
        n = len(team_profiles)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                compatibility = self.compatibility_calculator.calculate_compatibility(
                    team_profiles[i]['profile'],
                    team_profiles[j]['profile']
                )
                matrix[i][j] = matrix[j][i] = compatibility
                
        # Self-compatibility is always 1.0
        for i in range(n):
            matrix[i][i] = 1.0
            
        return matrix
    
    def _analyze_current_composition(self, team_profiles: List[Dict], compatibility_matrix: List[List[float]]) -> Dict[str, Any]:
        """Analyze current team composition metrics"""
        n = len(team_profiles)
        
        if n == 0:
            return self._empty_metrics()
        
        # Calculate overall compatibility
        total_compatibility = 0
        pair_count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                total_compatibility += compatibility_matrix[i][j]
                pair_count += 1
        
        avg_compatibility = total_compatibility / pair_count if pair_count > 0 else 1.0
        
        # Analyze personality diversity
        diversity_score = self._calculate_personality_diversity(team_profiles)
        
        # Identify potential conflicts
        conflict_pairs = self._identify_conflict_pairs(compatibility_matrix, threshold=0.3)
        
        # Calculate team balance
        balance_score = self._calculate_team_balance(team_profiles)
        
        # Overall team score
        overall_score = (avg_compatibility * 0.4 + diversity_score * 0.3 + balance_score * 0.3)
        
        return {
            'overall_score': overall_score,
            'average_compatibility': avg_compatibility,
            'diversity_score': diversity_score,
            'balance_score': balance_score,
            'conflict_pairs': conflict_pairs,
            'team_size': n,
            'strengths': self._identify_team_strengths(team_profiles),
            'weaknesses': self._identify_team_weaknesses(team_profiles)
        }
    
    def _calculate_personality_diversity(self, team_profiles: List[Dict]) -> float:
        """Calculate personality diversity within the team"""
        if len(team_profiles) < 2:
            return 0.0
            
        dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        diversity_scores = []
        
        for dimension in dimensions:
            values = [profile['profile'].get(dimension, 0.5) for profile in team_profiles]
            if values:
                diversity = np.std(values) if np.std(values) is not None else 0.0
                diversity_scores.append(diversity)
        
        return float(np.mean(diversity_scores)) if diversity_scores else 0.0
    
    def _identify_conflict_pairs(self, compatibility_matrix: List[List[float]], threshold: float = 0.3) -> List[Dict]:
        """Identify pairs with potential conflicts"""
        conflicts = []
        n = len(compatibility_matrix)
        
        for i in range(n):
            for j in range(i + 1, n):
                if compatibility_matrix[i][j] < threshold:
                    conflicts.append({
                        'member_a': i,
                        'member_b': j,
                        'compatibility_score': compatibility_matrix[i][j],
                        'risk_level': 'high' if compatibility_matrix[i][j] < 0.2 else 'medium'
                    })
        
        return conflicts
    
    def _calculate_team_balance(self, team_profiles: List[Dict]) -> float:
        """Calculate how well-balanced the team is across different dimensions"""
        if len(team_profiles) < 2:
            return 0.0
        
        balance_factors = []
        
        # Leadership balance
        leadership_scores = [profile['profile'].get('leadership_potential', 0.5) for profile in team_profiles]
        leadership_balance = max(0.0, 1.0 - abs(np.mean(leadership_scores) - 0.6))
        balance_factors.append(leadership_balance)
        
        # Collaboration balance
        collaboration_scores = [profile['profile'].get('collaboration_index', 0.5) for profile in team_profiles]
        collaboration_balance = max(0.0, 1.0 - abs(np.mean(collaboration_scores) - 0.7))
        balance_factors.append(collaboration_balance)
        
        return float(np.mean(balance_factors)) if balance_factors else 0.0
    
    def _identify_team_strengths(self, team_profiles: List[Dict]) -> List[str]:
        """Identify team's collective strengths"""
        if not team_profiles:
            return []
            
        strengths = []
        avg_leadership = np.mean([p['profile'].get('leadership_potential', 0.5) for p in team_profiles])
        avg_collaboration = np.mean([p['profile'].get('collaboration_index', 0.5) for p in team_profiles])
        avg_adaptability = np.mean([p['profile'].get('adaptability', 0.5) for p in team_profiles])
        
        if avg_leadership > 0.7:
            strengths.append("Strong leadership capabilities")
        if avg_collaboration > 0.7:
            strengths.append("Excellent collaboration potential")
        if avg_adaptability > 0.7:
            strengths.append("High adaptability to change")
            
        return strengths if strengths else ["Balanced team composition"]
    
    def _identify_team_weaknesses(self, team_profiles: List[Dict]) -> List[str]:
        """Identify potential team weaknesses"""
        if not team_profiles:
            return []
            
        weaknesses = []
        avg_stress_tolerance = np.mean([p['profile'].get('stress_tolerance', 0.5) for p in team_profiles])
        
        if avg_stress_tolerance < 0.4:
            weaknesses.append("May struggle under high pressure")
            
        return weaknesses
    
    def _generate_optimization_recommendations(
        self, team_profiles: List[Dict], compatibility_matrix: List[List[float]],
        project_requirements: Dict[str, Any], optimization_goals: List[str]
    ) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        conflicts = self._identify_conflict_pairs(compatibility_matrix)
        if conflicts:
            recommendations.append({
                'type': 'conflict_resolution',
                'priority': 'high',
                'title': 'Address Potential Conflicts',
                'description': f'Detected {len(conflicts)} potential compatibility issues',
                'action': 'Implement structured communication protocols'
            })
        
        return recommendations
    
    def _predict_team_performance(
        self, team_profiles: List[Dict], compatibility_matrix: List[List[float]],
        project_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict team performance metrics"""
        if not team_profiles:
            return {'predicted_velocity': 0, 'satisfaction_score': 0, 'conflict_probability': 1.0}
            
        avg_compatibility = np.mean([np.mean(row) for row in compatibility_matrix]) if compatibility_matrix else 0.5
        
        base_velocity = 20
        predicted_velocity = base_velocity * avg_compatibility
        
        return {
            'predicted_velocity': round(predicted_velocity, 1),
            'satisfaction_score': round(avg_compatibility, 2),
            'conflict_probability': round(1 - avg_compatibility, 2),
            'performance_trend': 'increasing' if avg_compatibility > 0.6 else 'stable'
        }
    
    def _empty_team_result(self) -> Dict[str, Any]:
        """Result for empty team"""
        return {
            'current_metrics': self._empty_metrics(),
            'compatibility_matrix': [],
            'recommendations': [],
            'performance_prediction': {'predicted_velocity': 0, 'satisfaction_score': 0, 'conflict_probability': 1.0},
            'optimization_score': 0.0,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Empty metrics for empty team"""
        return {
            'overall_score': 0.0,
            'average_compatibility': 0.0,
            'diversity_score': 0.0,
            'balance_score': 0.0,
            'conflict_pairs': [],
            'team_size': 0,
            'strengths': [],
            'weaknesses': []
        }
    
    def _fallback_optimization_result(self, team_profiles: List[Dict]) -> Dict[str, Any]:
        """Fallback result when optimization fails"""
        return {
            'current_metrics': {
                'overall_score': 0.6,
                'average_compatibility': 0.6,
                'diversity_score': 0.5,
                'balance_score': 0.6,
                'conflict_pairs': [],
                'team_size': len(team_profiles)
            },
            'compatibility_matrix': [[0.6 for _ in range(len(team_profiles))] for _ in range(len(team_profiles))],
            'recommendations': [{
                'type': 'general',
                'priority': 'low',
                'title': 'Assessment Needed',
                'description': 'Complete team assessments for detailed optimization',
                'action': 'Ensure all team members complete their personality assessments'
            }],
            'performance_prediction': {
                'predicted_velocity': 18.0,
                'satisfaction_score': 0.6,
                'conflict_probability': 0.3,
                'performance_trend': 'stable'
            },
            'optimization_score': 0.6,
            'generated_at': datetime.utcnow().isoformat()
        }


class CompatibilityCalculator:
    """Calculate compatibility between team members"""
    
    def calculate_compatibility(self, profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> float:
        """
        Calculate compatibility score between two personality profiles
        """
        try:
            # Calculate compatibility across different dimensions
            big_five_compatibility = self._calculate_big_five_compatibility(profile_a, profile_b)
            work_style_compatibility = self._calculate_work_style_compatibility(profile_a, profile_b)
            communication_compatibility = self._calculate_communication_compatibility(profile_a, profile_b)
            
            # Weighted combination
            overall_compatibility = (
                big_five_compatibility * 0.5 +
                work_style_compatibility * 0.3 +
                communication_compatibility * 0.2
            )
            
            return min(1.0, max(0.0, overall_compatibility))
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {str(e)}")
            return 0.5  # Neutral compatibility as fallback
    
    def _calculate_big_five_compatibility(self, profile_a: Dict, profile_b: Dict) -> float:
        """Calculate compatibility based on Big Five personality dimensions"""
        dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
        compatibility_scores = []
        
        for dimension in dimensions:
            value_a = profile_a.get(dimension, 0.5)
            value_b = profile_b.get(dimension, 0.5)
            
            # Different dimensions have different compatibility patterns
            if dimension == 'agreeableness':
                # High agreeableness in both is good
                score = (value_a + value_b) / 2
            elif dimension == 'neuroticism':
                # Low neuroticism in both is better
                score = 1.0 - ((value_a + value_b) / 2)
            elif dimension == 'conscientiousness':
                # Similar conscientiousness levels work well
                score = 1.0 - abs(value_a - value_b)
            else:  # openness, extraversion
                # Complementary levels can work well
                avg_level = (value_a + value_b) / 2
                difference_penalty = abs(value_a - value_b) * 0.3
                score = avg_level - difference_penalty
            
            compatibility_scores.append(max(0.0, min(1.0, score)))
        
        return float(np.mean(compatibility_scores))
    
    def _calculate_work_style_compatibility(self, profile_a: Dict, profile_b: Dict) -> float:
        """Calculate work style compatibility"""
        prefs_a = profile_a.get('work_preferences', [])
        prefs_b = profile_b.get('work_preferences', [])
        
        if not prefs_a or not prefs_b:
            return 0.6  # Neutral score if preferences unknown
        
        # Calculate overlap in preferences
        common_prefs = set(prefs_a).intersection(set(prefs_b))
        total_prefs = set(prefs_a).union(set(prefs_b))
        
        if not total_prefs:
            return 0.6
        
        overlap_score = len(common_prefs) / len(total_prefs)
        return min(1.0, overlap_score * 1.5)  # Boost the score slightly
    
    def _calculate_communication_compatibility(self, profile_a: Dict, profile_b: Dict) -> float:
        """Calculate communication style compatibility"""
        style_a = profile_a.get('communication_style', 'analytical')
        style_b = profile_b.get('communication_style', 'analytical')
        
        # Compatibility matrix for communication styles
        compatibility_scores = {
            ('collaborative', 'collaborative'): 0.9,
            ('collaborative', 'supportive'): 0.8,
            ('collaborative', 'assertive'): 0.6,
            ('collaborative', 'analytical'): 0.7,
            ('supportive', 'supportive'): 0.8,
            ('supportive', 'assertive'): 0.5,
            ('supportive', 'analytical'): 0.7,
            ('assertive', 'assertive'): 0.6,
            ('assertive', 'analytical'): 0.7,
            ('analytical', 'analytical'): 0.8
        }
        
        # Make lookup symmetric
        pair = tuple(sorted([style_a, style_b]))
        return compatibility_scores.get(pair, 0.6)


class PredictiveAnalytics:
    """Generate predictions about team performance and dynamics"""
    
    def __init__(self):
        self.performance_model = None
        self.conflict_model = None
        self.satisfaction_model = None
    
    def generate_team_predictions(
        self,
        behavioral_data: List[Dict],
        prediction_type: str = "all"
    ) -> List[Dict]:
        """
        Generate various predictions about team performance
        """
        predictions = []
        
        try:
            if not behavioral_data:
                return [self._fallback_prediction()]
            
            if prediction_type in ["all", "performance"]:
                perf_prediction = self._predict_performance(behavioral_data)
                predictions.append(perf_prediction)
            
            if prediction_type in ["all", "conflict"]:
                conflict_prediction = self._predict_conflicts(behavioral_data)
                predictions.append(conflict_prediction)
            
            if prediction_type in ["all", "satisfaction"]:
                satisfaction_prediction = self._predict_satisfaction(behavioral_data)
                predictions.append(satisfaction_prediction)
            
            if prediction_type in ["all", "velocity"]:
                velocity_prediction = self._predict_velocity(behavioral_data)
                predictions.append(velocity_prediction)
                
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            predictions.append(self._fallback_prediction())
        
        return predictions
    
    def _predict_performance(self, behavioral_data: List[Dict]) -> Dict:
        """Predict overall team performance"""
        features = self._extract_performance_features(behavioral_data)
        
        # Simple heuristic-based prediction
        avg_collaboration = np.mean([f.get('collaboration_index', 0.5) for f in features])
        avg_leadership = np.mean([f.get('leadership_potential', 0.5) for f in features])
        avg_stress_tolerance = np.mean([f.get('stress_tolerance', 0.5) for f in features])
        
        performance_score = (avg_collaboration * 0.4 + avg_leadership * 0.3 + avg_stress_tolerance * 0.3)
        
        if performance_score > 0.75:
            performance_level = "exceptional"
            confidence = 0.8
        elif performance_score > 0.6:
            performance_level = "good"
            confidence = 0.75
        elif performance_score > 0.4:
            performance_level = "average"
            confidence = 0.7
        else:
            performance_level = "needs_improvement"
            confidence = 0.65
        
        return {
            'type': 'performance',
            'data': {
                'performance_score': round(performance_score, 2),
                'performance_level': performance_level,
                'key_drivers': ["Team collaboration", "Leadership presence"],
                'improvement_areas': ["Stress management"] if avg_stress_tolerance < 0.5 else []
            },
            'confidence': confidence,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _predict_conflicts(self, behavioral_data: List[Dict]) -> Dict:
        """Predict potential team conflicts"""
        features = self._extract_performance_features(behavioral_data)
        
        # Simple conflict risk calculation
        avg_agreeableness = np.mean([f.get('agreeableness', 0.5) for f in features])
        avg_neuroticism = np.mean([f.get('neuroticism', 0.5) for f in features])
        
        conflict_probability = (1 - avg_agreeableness) * 0.6 + avg_neuroticism * 0.4
        
        risk_level = "high" if conflict_probability > 0.6 else "medium" if conflict_probability > 0.3 else "low"
        
        return {
            'type': 'conflict',
            'data': {
                'conflict_probability': round(conflict_probability, 2),
                'risk_level': risk_level,
                'personality_clashes': [],
                'communication_barriers': [],
                'mitigation_strategies': ["Regular team check-ins", "Clear communication protocols"]
            },
            'confidence': 0.72,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _predict_satisfaction(self, behavioral_data: List[Dict]) -> Dict:
        """Predict team satisfaction levels"""
        features = self._extract_performance_features(behavioral_data)
        
        # Simple satisfaction calculation
        avg_agreeableness = np.mean([f.get('agreeableness', 0.5) for f in features])
        avg_neuroticism = np.mean([f.get('neuroticism', 0.5) for f in features])
        
        satisfaction_score = avg_agreeableness * 0.6 + (1 - avg_neuroticism) * 0.4
        
        satisfaction_level = "very_satisfied" if satisfaction_score > 0.8 else \
                           "satisfied" if satisfaction_score > 0.6 else \
                           "neutral" if satisfaction_score > 0.4 else "dissatisfied"
        
        return {
            'type': 'satisfaction',
            'data': {
                'satisfaction_score': round(satisfaction_score, 2),
                'satisfaction_level': satisfaction_level,
                'role_fit_score': 0.7,
                'team_harmony_score': round(satisfaction_score, 2),
                'satisfaction_drivers': ["Team harmony", "Role alignment"],
                'improvement_recommendations': ["Provide growth opportunities"] if satisfaction_score < 0.6 else []
            },
            'confidence': 0.68,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _predict_velocity(self, behavioral_data: List[Dict]) -> Dict:
        """Predict team velocity (story points per sprint)"""
        features = self._extract_performance_features(behavioral_data)
        
        team_size = len(behavioral_data)
        base_velocity_per_person = 4
        
        # Simple efficiency calculation
        avg_conscientiousness = np.mean([f.get('conscientiousness', 0.5) for f in features])
        efficiency_modifier = 0.7 + (avg_conscientiousness * 0.6)
        
        predicted_velocity = team_size * base_velocity_per_person * efficiency_modifier
        
        velocity_range = [
            round(predicted_velocity * 0.8, 1),
            round(predicted_velocity * 1.2, 1)
        ]
        
        return {
            'type': 'velocity',
            'data': {
                'predicted_velocity': round(predicted_velocity, 1),
                'velocity_range': velocity_range,
                'team_size': team_size,
                'efficiency_factors': {
                    'efficiency_modifier': round(efficiency_modifier, 2),
                    'collaboration_modifier': 1.0,
                    'focus_modifier': 1.0
                },
                'velocity_drivers': ["Team conscientiousness", "Collaboration"],
                'optimization_suggestions': ["Focus on process improvement"] if efficiency_modifier < 1.0 else []
            },
            'confidence': 0.71,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _extract_performance_features(self, behavioral_data: List[Dict]) -> List[Dict]:
        """Extract features relevant to performance prediction"""
        features = []
        for member_data in behavioral_data:
            assessments = member_data.get('assessments', {})
            feature = {}
            
            # Extract from unified profile or individual assessments
            if 'unified_profile' in assessments:
                feature.update(assessments['unified_profile'])
            else:
                # Extract from individual frameworks
                for framework, results in assessments.items():
                    if framework == 'big_five':
                        feature.update(results)
            
            # Set defaults for missing values
            defaults = {
                'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5,
                'agreeableness': 0.5, 'neuroticism': 0.5, 'leadership_potential': 0.5,
                'collaboration_index': 0.5, 'stress_tolerance': 0.5, 'adaptability': 0.5
            }
            
            for key, default_value in defaults.items():
                if key not in feature:
                    feature[key] = default_value
                    
            features.append(feature)
        
        return features
    
    def _fallback_prediction(self) -> Dict:
        """Fallback prediction when generation fails"""
        return {
            'type': 'general',
            'data': {
                'message': 'Complete team assessments for detailed predictions',
                'baseline_performance': 'average'
            },
            'confidence': 0.3,
            'generated_at': datetime.utcnow().isoformat()
        }


class PersonalityFrameworkProcessor:
    """Base class for personality framework processors"""
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw assessment data into standardized format"""
        raise NotImplementedError("Subclasses must implement process method")

#         # Calculate team balance
#         balance_score = self._calculate_team_balance(team_profiles)
        
#         # Overall team score
#         overall_score = (avg_compatibility * 0.4 + diversity_score * 0.3 + balance_score * 0.3)
        
#         return {
#             'overall_score': overall_score,
#             'average_compatibility': avg_compatibility,
#             'diversity_score': diversity_score,
#             'balance_score': balance_score,
#             'conflict_pairs': conflict_pairs,
#             'team_size': n,
#             'strengths': self._identify_team_strengths(team_profiles),
#             'weaknesses': self._identify_team_weaknesses(team_profiles)
#         }
    
#     def _calculate_personality_diversity(self, team_profiles: List[Dict]) -> float:
#         """Calculate personality diversity within the team"""
#         if len(team_profiles) < 2:
#             return 0.0
            
#         # Extract personality dimensions
#         dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
#         diversity_scores = []
        
#         for dimension in dimensions:
#             values = [profile['profile'].get(dimension, 0.5) for profile in team_profiles]
#             diversity = np.std(values)  # Standard deviation as diversity measure
#             diversity_scores.append(diversity)
        
#         return np.mean(diversity_scores)
    
#     def _identify_conflict_pairs(self, compatibility_matrix: List[List[float]], threshold: float = 0.3) -> List[Dict]:
#         """Identify pairs with potential conflicts"""
#         conflicts = []
#         n = len(compatibility_matrix)
        
#         for i in range(n):
#             for j in range(i + 1, n):
#                 if compatibility_matrix[i][j] < threshold:
#                     conflicts.append({
#                         'member_a': i,
#                         'member_b': j,
#                         'compatibility_score': compatibility_matrix[i][j],
#                         'risk_level': 'high' if compatibility_matrix[i][j] < 0.2 else 'medium'
#                     })
        
#         return conflicts
    
#     def _calculate_team_balance(self, team_profiles: List[Dict]) -> float:
#         """Calculate how well-balanced the team is across different dimensions"""
#         if len(team_profiles) < 2:
#             return 0.0
        
#         # Check balance across key dimensions
#         balance_factors = []
        
#         # Leadership balance
#         leadership_scores = [profile['profile'].get('leadership_potential', 0.5) for profile in team_profiles]
#         leadership_balance = 1.0 - abs(np.mean(leadership_scores) - 0.6)  # Slightly favor leadership
#         balance_factors.append(leadership_balance)
        
#         # Collaboration balance
#         collaboration_scores = [profile['profile'].get('collaboration_index', 0.5) for profile in team_profiles]
#         collaboration_balance = 1.0 - abs(np.mean(collaboration_scores) - 0.7)  # Favor collaboration
#         balance_factors.append(collaboration_balance)
        
#         # Stress tolerance balance
#         stress_scores = [profile['profile'].get('stress_tolerance', 0.5) for profile in team_profiles]
#         stress_balance = 1.0 - abs(np.mean(stress_scores) - 0.6)  # Slightly favor stress tolerance
#         balance_factors.append(stress_balance)
        
#         return np.mean(balance_factors)
    
#     def _identify_team_strengths(self, team_profiles: List[Dict]) -> List[str]:
#         """Identify team's collective strengths"""
#         strengths = []
        
#         # Calculate team averages
#         avg_leadership = np.mean([p['profile'].get('leadership_potential', 0.5) for p in team_profiles])
#         avg_collaboration = np.mean([p['profile'].get('collaboration_index', 0.5) for p in team_profiles])
#         avg_adaptability = np.mean([p['profile'].get('adaptability', 0.5) for p in team_profiles])
#         avg_openness = np.mean([p['profile'].get('openness', 0.5) for p in team_profiles])
        
#         if avg_leadership > 0.7:
#             strengths.append("Strong leadership capabilities")
#         if avg_collaboration > 0.7:
#             strengths.append("Excellent collaboration potential")
#         if avg_adaptability > 0.7:
#             strengths.append("High adaptability to change")
#         if avg_openness > 0.7:
#             strengths.append("Creative and innovative thinking")
            
#         return strengths if strengths else ["Balanced team composition"]
    
#     def _identify_team_weaknesses(self, team_profiles: List[Dict]) -> List[str]:
#         """Identify potential team weaknesses"""
#         weaknesses = []
        
#         # Calculate team averages
#         avg_stress_tolerance = np.mean([p['profile'].get('stress_tolerance', 0.5) for p in team_profiles])
#         avg_conscientiousness = np.mean([p['profile'].get('conscientiousness', 0.5) for p in team_profiles])
        
#         if avg_stress_tolerance < 0.4:
#             weaknesses.append("May struggle under high pressure")
#         if avg_conscientiousness < 0.4:
#             weaknesses.append("May need additional structure and oversight")
            
#         # Check for diversity issues
#         diversity = self._calculate_personality_diversity(team_profiles)
#         if diversity < 0.2:
#             weaknesses.append("Limited personality diversity may reduce creativity")
            
#         return weaknesses if weaknesses else []
    
#     def _generate_optimization_recommendations(
#         self,
#         team_profiles: List[Dict],
#         compatibility_matrix: List[List[float]],
#         project_requirements: Dict[str, Any],
#         optimization_goals: List[str]
#     ) -> List[Dict]:
#         """Generate specific recommendations for team optimization"""
#         recommendations = []
        
#         # Role assignment recommendations
#         role_recommendations = self._recommend_role_assignments(team_profiles, project_requirements)
#         if role_recommendations:
#             recommendations.extend(role_recommendations)
        
#         # Conflict resolution recommendations
#         conflicts = self._identify_conflict_pairs(compatibility_matrix)
#         if conflicts:
#             conflict_recommendations = self._recommend_conflict_resolutions(conflicts, team_profiles)
#             recommendations.extend(conflict_recommendations)
        
#         # Communication strategy recommendations
#         comm_recommendations = self._recommend_communication_strategies(team_profiles)
#         recommendations.extend(comm_recommendations)
        
#         # Meeting structure recommendations
#         meeting_recommendations = self._recommend_meeting_structures(team_profiles)
#         recommendations.extend(meeting_recommendations)
        
#         return recommendations
    
#     def _recommend_role_assignments(self, team_profiles: List[Dict], project_requirements: Dict) -> List[Dict]:
#         """Recommend optimal role assignments"""
#         recommendations = []
        
#         # Find best candidates for key roles
#         leadership_scores = [(i, p['profile'].get('leadership_potential', 0.5)) for i, p in enumerate(team_profiles)]
#         leadership_scores.sort(key=lambda x: x[1], reverse=True)
        
#         if leadership_scores[0][1] > 0.7:
#             recommendations.append({
#                 'type': 'role_assignment',
#                 'priority': 'high',
#                 'title': 'Optimal Team Lead Identified',
#                 'description': f'Team member {leadership_scores[0][0]} shows strong leadership potential',
#                 'action': f'Consider assigning leadership responsibilities to member {leadership_scores[0][0]}'
#             })
        
#         return recommendations
    
#     def _recommend_conflict_resolutions(self, conflicts: List[Dict], team_profiles: List[Dict]) -> List[Dict]:
#         """Recommend strategies to resolve potential conflicts"""
#         recommendations = []
        
#         for conflict in conflicts:
#             if conflict['risk_level'] == 'high':
#                 recommendations.append({
#                     'type': 'conflict_resolution',
#                     'priority': 'high',
#                     'title': 'High Conflict Risk Detected',
#                     'description': f'Members {conflict["member_a"]} and {conflict["member_b"]} may experience communication challenges',
#                     'action': 'Implement structured communication protocols and regular check-ins'
#                 })
        
#         return recommendations
    
#     def _recommend_communication_strategies(self, team_profiles: List[Dict]) -> List[Dict]:
#         """Recommend communication strategies based on team composition"""
#         recommendations = []
        
#         # Analyze communication styles
#         styles = [p['profile'].get('communication_style', 'analytical') for p in team_profiles]
#         style_counts = {style: styles.count(style) for style in set(styles)}
        
#         if len(style_counts) > 2:
#             recommendations.append({
#                 'type': 'communication',
#                 'priority': 'medium',
#                 'title': 'Diverse Communication Styles',
#                 'description': 'Team has diverse communication preferences',
#                 'action': 'Establish multiple communication channels to accommodate different styles'
#             })
        
#         return recommendations
    
#     def _recommend_meeting_structures(self, team_profiles: List[Dict]) -> List[Dict]:
#         """Recommend meeting structures based on team personality"""
#         recommendations = []
        
#         avg_extraversion = np.mean([p['profile'].get('extraversion', 0.5) for p in team_profiles])
        
#         if avg_extraversion < 0.4:
#             recommendations.append({
#                 'type': 'meeting_structure',
#                 'priority': 'medium',
#                 'title': 'Introverted Team Composition',
#                 'description': 'Team has many introverted members',
#                 'action': 'Use structured agendas and allow processing time before decisions'
#             })
#         elif avg_extraversion > 0.7:
#             recommendations.append({
#                 'type': 'meeting_structure',
#                 'priority': 'medium',
#                 'title': 'Extraverted Team Composition',
#                 'description': 'Team has many extraverted members',
#                 'action': 'Facilitate balanced participation and manage discussion flow'
#             })
        
#         return recommendations
    
#     def _predict_team_performance(
#         self,
#         team_profiles: List[Dict],
#         compatibility_matrix: List[List[float]],
#         project_requirements: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """Predict team performance metrics"""
        
#         # Calculate base performance score
#         avg_compatibility = np.mean([np.mean(row) for row in compatibility_matrix])
#         diversity_score = self._calculate_personality_diversity(team_profiles)
#         balance_score = self._calculate_team_balance(team_profiles)
        
#         # Predict velocity (story points per sprint)
#         base_velocity = 20  # Base velocity for average team
#         velocity_modifier = (avg_compatibility * 0.4 + diversity_score * 0.3 + balance_score * 0.3)
#         predicted_velocity = base_velocity * (0.7 + velocity_modifier * 0.6)
        
#         # Predict satisfaction score
#         satisfaction_score = avg_compatibility * 0.6 + balance_score * 0.4
        
#         # Predict conflict probability
#         conflicts = self._identify_conflict_pairs(compatibility_matrix)
#         conflict_probability = min(0.9, len(conflicts) * 0.15)
        
#         return {
#             'predicted_velocity': round(predicted_velocity, 1),
#             'satisfaction_score': round(satisfaction_score, 2),
#             'conflict_probability': round(conflict_probability, 2),
#             'performance_trend': 'increasing' if velocity_modifier > 0.6 else 'stable',
#             'confidence_interval': [
#                 round(predicted_velocity * 0.85, 1),
#                 round(predicted_velocity * 1.15, 1)
#             ]
#         }
    
#     def _fallback_optimization_result(self, team_profiles: List[Dict]) -> Dict[str, Any]:
#         """Fallback result when optimization fails"""
#         return {
#             'current_metrics': {
#                 'overall_score': 0.6,
#                 'average_compatibility': 0.6,
#                 'diversity_score': 0.5,
#                 'balance_score': 0.6,
#                 'conflict_pairs': [],
#                 'team_size': len(team_profiles)
#             },
#             'compatibility_matrix': [[0.6 for _ in range(len(team_profiles))] for _ in range(len(team_profiles))],
#             'recommendations': [{
#                 'type': 'general',
#                 'priority': 'low',
#                 'title': 'Assessment Needed',
#                 'description': 'Complete team assessments for detailed optimization',
#                 'action': 'Ensure all team members complete their personality assessments'
#             }],
#             'performance_prediction': {
#                 'predicted_velocity': 18.0,
#                 'satisfaction_score': 0.6,
#                 'conflict_probability': 0.3,
#                 'performance_trend': 'stable'
#             },
#             'optimization_score': 0.6,
#             'generated_at': datetime.utcnow().isoformat()
#         }


# class CompatibilityCalculator:
#     """Calculate compatibility between team members"""
    
#     def calculate_compatibility(self, profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> float:
#         """
#         Calculate compatibility score between two personality profiles
        
#         Args:
#             profile_a: First person's personality profile
#             profile_b: Second person's personality profile
            
#         Returns:
#             Compatibility score between 0.0 and 1.0
#         """
#         try:
#             # Calculate compatibility across different dimensions
#             big_five_compatibility = self._calculate_big_five_compatibility(profile_a, profile_b)
#             work_style_compatibility = self._calculate_work_style_compatibility(profile_a, profile_b)
#             communication_compatibility = self._calculate_communication_compatibility(profile_a, profile_b)
            
#             # Weighted combination
#             overall_compatibility = (
#                 big_five_compatibility * 0.5 +
#                 work_style_compatibility * 0.3 +
#                 communication_compatibility * 0.2
#             )
            
#             return min(1.0, max(0.0, overall_compatibility))
            
#         except Exception as e:
#             logger.error(f"Error calculating compatibility: {str(e)}")
#             return 0.5  # Neutral compatibility as fallback
    
#     def _calculate_big_five_compatibility(self, profile_a: Dict, profile_b: Dict) -> float:
#         """Calculate compatibility based on Big Five personality dimensions"""
#         dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
#         compatibility_scores = []
        
#         for dimension in dimensions:
#             value_a = profile_a.get(dimension, 0.5)
#             value_b = profile_b.get(dimension, 0.5)
            
#             # Different dimensions have different compatibility patterns
#             if dimension == 'agreeableness':
#                 # High agreeableness in both is good
#                 score = (value_a + value_b) / 2
#             elif dimension == 'neuroticism':
#                 # Low neuroticism in both is better
#                 score = 1.0 - ((value_a + value_b) / 2)
#             elif dimension == 'conscientiousness':
#                 # Similar conscientiousness levels work well
#                 score = 1.0 - abs(value_a - value_b)
#             else:  # openness, extraversion
#                 # Complementary levels can work well
#                 avg_level = (value_a + value_b) / 2
#                 difference_penalty = abs(value_a - value_b) * 0.3
#                 score = avg_level - difference_penalty
            
#             compatibility_scores.append(max(0.0, min(1.0, score)))
        
#         return np.mean(compatibility_scores)
    
#     def _calculate_work_style_compatibility(self, profile_a: Dict, profile_b: Dict) -> float:
#         """Calculate work style compatibility"""
        
#         # Compare work preferences
#         prefs_a = profile_a.get('work_preferences', [])
#         prefs_b = profile_b.get('work_preferences', [])
        
#         if not prefs_a or not prefs_b:
#             return 0.6  # Neutral score if preferences unknown
        
#         # Calculate overlap in preferences
#         common_prefs = set(prefs_a).intersection(set(prefs_b))
#         total_prefs = set(prefs_a).union(set(prefs_b))
        
#         if not total_prefs:
#             return 0.6
        
#         overlap_score = len(common_prefs) / len(total_prefs)
        
#         # Bonus for complementary preferences
#         complementary_pairs = [
#             ('creative_projects', 'structured_environment'),
#             ('team_collaboration', 'focused_work'),
#             ('innovation', 'clear_deadlines')
#         ]
        
#         complementary_bonus = 0
#         for pref_a, pref_b in complementary_pairs:
#             if (pref_a in prefs_a and pref_b in prefs_b) or (pref_b in prefs_a and pref_a in prefs_b):
#                 complementary_bonus += 0.1
        
#         return min(1.0, overlap_score + complementary_bonus)
    
#     def _calculate_communication_compatibility(self, profile_a: Dict, profile_b: Dict) -> float:
#         """Calculate communication style compatibility"""
        
#         style_a = profile_a.get('communication_style', 'analytical')
#         style_b = profile_b.get('communication_style', 'analytical')
        
#         # Compatibility matrix for communication styles
#         compatibility_matrix = {
#             ('collaborative', 'collaborative'): 0.9,
#             ('collaborative', 'supportive'): 0.8,
#             ('collaborative', 'assertive'): 0.6,
#             ('collaborative', 'analytical'): 0.7,
#             ('supportive', 'supportive'): 0.8,
#             ('supportive', 'assertive'): 0.5,
#             ('supportive', 'analytical'): 0.7,
#             ('assertive', 'assertive'): 0.6,
#             ('assertive', 'analytical'): 0.7,
#             ('analytical', 'analytical'): 0.8
#         }
        
#         # Make lookup symmetric
#         pair = tuple(sorted([style_a, style_b]))
#         return compatibility_matrix.get(pair, 0.6)


# class PredictiveAnalytics:
#     """Generate predictions about team performance and dynamics"""
    
#     def __init__(self):
#         self.performance_model = None
#         self.conflict_model = None
#         self.satisfaction_model = None
#         self._load_models()
    
#     def _load_models(self):
#         """Load or initialize predictive models"""
#         try:
#             # In production, these would be loaded from saved model files
#             self.performance_model = RandomForestRegressor(n_estimators=100, random_state=42)
#             self.conflict_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
#             self.satisfaction_model = RandomForestRegressor(n_estimators=100, random_state=42)
#             logger.info("Predictive models loaded successfully")
#         except Exception as e:
#             logger.error(f"Error loading predictive models: {str(e)}")
    
#     def generate_team_predictions(
#         self,
#         behavioral_data: List[Dict],
#         prediction_type: str = "all"
#     ) -> List[Dict]:
#         """
#         Generate various predictions about team performance
        
#         Args:
#             behavioral_data: Team behavioral data
#             prediction_type: Type of predictions to generate
            
#         Returns:
#             List of prediction objects
#         """
#         predictions = []
        
#         try:
#             if prediction_type in ["all", "performance"]:
#                 perf_prediction = self._predict_performance(behavioral_data)
#                 predictions.append(perf_prediction)
            
#             if prediction_type in ["all", "conflict"]:
#                 conflict_prediction = self._predict_conflicts(behavioral_data)
#                 predictions.append(conflict_prediction)
            
#             if prediction_type in ["all", "satisfaction"]:
#                 satisfaction_prediction = self._predict_satisfaction(behavioral_data)
#                 predictions.append(satisfaction_prediction)
            
#             if prediction_type in ["all", "velocity"]:
#                 velocity_prediction = self._predict_velocity(behavioral_data)
#                 predictions.append(velocity_prediction)
                
#         except Exception as e:
#             logger.error(f"Error generating predictions: {str(e)}")
#             predictions.append(self._fallback_prediction())
        
#         return predictions
    
#     def _predict_performance(self, behavioral_data: List[Dict]) -> Dict:
#         """Predict overall team performance"""
        
#         # Extract features from behavioral data
#         features = self._extract_performance_features(behavioral_data)
        
#         # Simple heuristic-based prediction (would be ML model in production)
#         avg_collaboration = np.mean([f.get('collaboration_index', 0.5) for f in features])
#         avg_leadership = np.mean([f.get('leadership_potential', 0.5) for f in features])
#         avg_stress_tolerance = np.mean([f.get('stress_tolerance', 0.5) for f in features])
        
#         performance_score = (avg_collaboration * 0.4 + avg_leadership * 0.3 + avg_stress_tolerance * 0.3)
        
#         # Determine performance level
#         if performance_score > 0.75:
#             performance_level = "exceptional"
#             confidence = 0.8
#         elif performance_score > 0.6:
#             performance_level = "good"
#             confidence = 0.75
#         elif performance_score > 0.4:
#             performance_level = "average"
#             confidence = 0.7
#         else:
#             performance_level = "needs_improvement"
#             confidence = 0.65
        
#         return {
#             'type': 'performance',
#             'data': {
#                 'performance_score': round(performance_score, 2),
#                 'performance_level': performance_level,
#                 'key_drivers': self._identify_performance_drivers(features),
#                 'improvement_areas': self._identify_improvement_areas(features)
#             },
#             'confidence': confidence,
#             'generated_at': datetime.utcnow().isoformat()
#         }
    
#     def _predict_conflicts(self, behavioral_data: List[Dict]) -> Dict:
#         """Predict potential team conflicts"""
        
#         features = self._extract_conflict_features(behavioral_data)
        
#         # Calculate conflict risk factors
#         personality_clashes = self._identify_personality_clashes(features)
#         communication_barriers = self._identify_communication_barriers(features)
#         stress_factors = self._identify_stress_factors(features)
        
#         # Overall conflict probability
#         conflict_probability = (
#             len(personality_clashes) * 0.2 +
#             len(communication_barriers) * 0.15 +
#             stress_factors * 0.1
#         )
#         conflict_probability = min(0.9, conflict_probability)
        
#         risk_level = "high" if conflict_probability > 0.6 else "medium" if conflict_probability > 0.3 else "low"
        
#         return {
#             'type': 'conflict',
#             'data': {
#                 'conflict_probability': round(conflict_probability, 2),
#                 'risk_level': risk_level,
#                 'personality_clashes': personality_clashes,
#                 'communication_barriers': communication_barriers,
#                 'mitigation_strategies': self._suggest_conflict_mitigation(personality_clashes, communication_barriers)
#             },
#             'confidence': 0.72,
#             'generated_at': datetime.utcnow().isoformat()
#         }
    
#     def _predict_satisfaction(self, behavioral_data: List[Dict]) -> Dict:
#         """Predict team satisfaction levels"""
        
#         features = self._extract_satisfaction_features(behavioral_data)
        
#         # Calculate satisfaction factors
#         role_fit_score = self._calculate_role_fit(features)
#         team_harmony_score = self._calculate_team_harmony(features)
#         work_environment_fit = self._calculate_environment_fit(features)
        
#         overall_satisfaction = (role_fit_score * 0.4 + team_harmony_score * 0.4 + work_environment_fit * 0.2)
        
#         satisfaction_level = "very_satisfied" if overall_satisfaction > 0.8 else \
#                            "satisfied" if overall_satisfaction > 0.6 else \
#                            "neutral" if overall_satisfaction > 0.4 else "dissatisfied"
        
#         return {
#             'type': 'satisfaction',
#             'data': {
#                 'satisfaction_score': round(overall_satisfaction, 2),
#                 'satisfaction_level': satisfaction_level,
#                 'role_fit_score': round(role_fit_score, 2),
#                 'team_harmony_score': round(team_harmony_score, 2),
#                 'satisfaction_drivers': self._identify_satisfaction_drivers(features),
#                 'improvement_recommendations': self._suggest_satisfaction_improvements(features)
#             },
#             'confidence': 0.68,
#             'generated_at': datetime.utcnow().isoformat()
#         }
    
#     def _predict_velocity(self, behavioral_data: List[Dict]) -> Dict:
#         """Predict team velocity (story points per sprint)"""
        
#         features = self._extract_velocity_features(behavioral_data)
        
#         # Base velocity calculation
#         team_size = len(behavioral_data)
#         base_velocity_per_person = 4  # Average story points per person per sprint
        
#         # Modifiers based on personality
#         efficiency_modifier = self._calculate_efficiency_modifier(features)
#         collaboration_modifier = self._calculate_collaboration_modifier(features)
#         focus_modifier = self._calculate_focus_modifier(features)
        
#         total_modifier = efficiency_modifier * collaboration_modifier * focus_modifier
#         predicted_velocity = team_size * base_velocity_per_person * total_modifier
        
#         # Add confidence intervals
#         velocity_range = [
#             round(predicted_velocity * 0.8, 1),
#             round(predicted_velocity * 1.2, 1)
#         ]
        
#         return {
#             'type': 'velocity',
#             'data': {
#                 'predicted_velocity': round(predicted_velocity, 1),
#                 'velocity_range': velocity_range,
#                 'team_size': team_size,
#                 'efficiency_factors': {
#                     'efficiency_modifier': round(efficiency_modifier, 2),
#                     'collaboration_modifier': round(collaboration_modifier, 2),
#                     'focus_modifier': round(focus_modifier, 2)
#                 },
#                 'velocity_drivers': self._identify_velocity_drivers(features),
#                 'optimization_suggestions': self._suggest_velocity_optimizations(features)
#             },
#             'confidence': 0.71,
#             'generated_at': datetime.utcnow().isoformat()
#         }
    
#     # Helper methods for feature extraction and calculations
#     def _extract_performance_features(self, behavioral_data: List[Dict]) -> List[Dict]:
#         """Extract features relevant to performance prediction"""
#         features = []
#         for member_data in behavioral_data:
#             assessments = member_data.get('assessments', {})
#             feature = {}
            
#             # Extract key personality traits
#             for framework, results in assessments.items():
#                 if framework == 'big_five':
#                     feature.update(results)
#                 elif framework == 'predictive_index':
#                     feature.update({f'pi_{k}': v for k, v in results.items()})
            
#             # Add derived metrics if available
#             if 'collaboration_index' in assessments.get('unified_profile', {}):
#                 feature.update(assessments['unified_profile'])
                
#             features.append(feature)
        
#         return features
    
#     def _extract_conflict_features(self, behavioral_data: List[Dict]) -> List[Dict]:
#         """Extract features for conflict prediction"""
#         return self._extract_performance_features(behavioral_data)  # Same features for now
    
#     def _extract_satisfaction_features(self, behavioral_data: List[Dict]) -> List[Dict]:
#         """Extract features for satisfaction prediction"""
#         return self._extract_performance_features(behavioral_data)
    
#     def _extract_velocity_features(self, behavioral_data: List[Dict]) -> List[Dict]:
#         """Extract features for velocity prediction"""
#         return self._extract_performance_features(behavioral_data)
    
#     def _identify_performance_drivers(self, features: List[Dict]) -> List[str]:
#         """Identify key performance drivers for the team"""
#         drivers = []
        
#         avg_collaboration = np.mean([f.get('collaboration_index', 0.5) for f in features])
#         avg_conscientiousness = np.mean([f.get('conscientiousness', 0.5) for f in features])
#         avg_openness = np.mean([f.get('openness', 0.5) for f in features])
        
#         if avg_collaboration > 0.7:
#             drivers.append("High team collaboration")
#         if avg_conscientiousness > 0.7:
#             drivers.append("Strong work ethic and reliability")
#         if avg_openness > 0.7:
#             drivers.append("Innovation and creative problem-solving")
            
#         return drivers if drivers else ["Balanced team capabilities"]
    
#     def _identify_improvement_areas(self, features: List[Dict]) -> List[str]:
#         """Identify areas for performance improvement"""
#         areas = []
        
#         avg_stress_tolerance = np.mean([f.get('stress_tolerance', 0.5) for f in features])
#         avg_adaptability = np.mean([f.get('adaptability', 0.5) for f in features])
        
#         if avg_stress_tolerance < 0.4:
#             areas.append("Stress management and resilience")
#         if avg_adaptability < 0.4:
#             areas.append("Adaptability to changing requirements")
            
#         return areas
    
#     def _identify_personality_clashes(self, features: List[Dict]) -> List[Dict]:
#         """Identify potential personality clashes"""
#         clashes = []
        
#         # Simple heuristic: high dominance + low agreeableness combinations
#         high_dominance = [i for i, f in enumerate(features) if f.get('pi_dominance', 0.5) > 0.7]
#         low_agreeableness = [i for i, f in enumerate(features) if f.get('agreeableness', 0.5) < 0.3]
        
#         if len(high_dominance) > 1:
#             clashes.append({
#                 'type': 'dominance_conflict',
#                 'description': 'Multiple highly dominant personalities may compete for control',
#                 'members': high_dominance
#             })
        
#         return clashes
    
#     def _identify_communication_barriers(self, features: List[Dict]) -> List[Dict]:
#         """Identify communication barriers"""
#         barriers = []
        
#         # Check for extreme introversion/extraversion mix
#         extraversion_scores = [f.get('extraversion', 0.5) for f in features]
#         if max(extraversion_scores) - min(extraversion_scores) > 0.6:
#             barriers.append({
#                 'type': 'introversion_extraversion_gap',
#                 'description': 'Significant differences in communication preferences'
#             })
        
#         return barriers
    
#     def _identify_stress_factors(self, features: List[Dict]) -> float:
#         """Calculate overall team stress factors"""
#         avg_neuroticism = np.mean([f.get('neuroticism', 0.5) for f in features])
#         avg_stress_tolerance = np.mean([f.get('stress_tolerance', 0.5) for f in features])
        
#         return avg_neuroticism + (1 - avg_stress_tolerance)
    
#     def _calculate_role_fit(self, features: List[Dict]) -> float:
#         """Calculate how well team members fit their roles"""
#         # Simplified calculation - in production would consider actual role assignments
#         avg_leadership = np.mean([f.get('leadership_potential', 0.5) for f in features])
#         avg_collaboration = np.mean([f.get('collaboration_index', 0.5) for f in features])
#         return (avg_leadership + avg_collaboration) / 2
    
#     def _calculate_team_harmony(self, features: List[Dict]) -> float:
#         """Calculate team harmony score"""
#         avg_agreeableness = np.mean([f.get('agreeableness', 0.5) for f in features])
#         avg_neuroticism = np.mean([f.get('neuroticism', 0.5) for f in features])
#         return avg_agreeableness * (1 - avg_neuroticism)
    
#     def _calculate_environment_fit(self, features: List[Dict]) -> float:
#         """Calculate how well team fits the work environment"""
#         # Assume agile environment benefits from certain traits
#         avg_adaptability = np.mean([f.get('adaptability', 0.5) for f in features])
#         avg_openness = np.mean([f.get('openness', 0.5) for f in features])
#         return (avg_adaptability + avg_openness) / 2
    
#     def _calculate_efficiency_modifier(self, features: List[Dict]) -> float:
#         """Calculate efficiency modifier based on conscientiousness and focus"""
#         avg_conscientiousness = np.mean([f.get('conscientiousness', 0.5) for f in features])
#         return 0.7 + (avg_conscientiousness * 0.6)  # Range: 0.7 to 1.3
    
#     def _calculate_collaboration_modifier(self, features: List[Dict]) -> float:
#         """Calculate collaboration modifier"""
#         avg_collaboration = np.mean([f.get('collaboration_index', 0.5) for f in features])
#         avg_agreeableness = np.mean([f.get('agreeableness', 0.5) for f in features])
#         collaboration_score = (avg_collaboration + avg_agreeableness) / 2
#         return 0.8 + (collaboration_score * 0.4)  # Range: 0.8 to 1.2
    
#     def _calculate_focus_modifier(self, features: List[Dict]) -> float:
#         """Calculate focus modifier based on distractibility"""
#         avg_neuroticism = np.mean([f.get('neuroticism', 0.5) for f in features])
#         # Lower neuroticism = better focus
#         focus_score = 1 - avg_neuroticism
#         return 0.8 + (focus_score * 0.4)  # Range: 0.8 to 1.2
    
#     def _suggest_conflict_mitigation(self, personality_clashes: List[Dict], communication_barriers: List[Dict]) -> List[str]:
#         """Suggest strategies to mitigate conflicts"""
#         strategies = []
        
#         if personality_clashes:
#             strategies.append("Establish clear role boundaries and decision-making processes")
#             strategies.append("Implement structured conflict resolution protocols")
        
#         if communication_barriers:
#             strategies.append("Use multiple communication channels to accommodate different preferences")
#             strategies.append("Schedule regular one-on-one check-ins between team members")
        
#         return strategies if strategies else ["Monitor team dynamics and provide coaching as needed"]
    
#     def _identify_satisfaction_drivers(self, features: List[Dict]) -> List[str]:
#         """Identify key satisfaction drivers"""
#         drivers = []
        
#         avg_autonomy_need = np.mean([f.get('openness', 0.5) for f in features])
#         avg_structure_need = np.mean([f.get('conscientiousness', 0.5) for f in features])
        
#         if avg_autonomy_need > 0.6:
#             drivers.append("Creative freedom and autonomy")
#         if avg_structure_need > 0.6:
#             drivers.append("Clear processes and expectations")
        
#         return drivers if drivers else ["Balanced work environment"]
    
#     def _suggest_satisfaction_improvements(self, features: List[Dict]) -> List[str]:
#         """Suggest improvements to increase satisfaction"""
#         improvements = []
        
#         avg_recognition_need = np.mean([f.get('extraversion', 0.5) for f in features])
#         avg_growth_need = np.mean([f.get('openness', 0.5) for f in features])
        
#         if avg_recognition_need > 0.6:
#             improvements.append("Implement regular recognition and feedback systems")
#         if avg_growth_need > 0.6:
#             improvements.append("Provide learning and development opportunities")
        
#         return improvements if improvements else ["Maintain current positive team dynamics"]
    
#     def _identify_velocity_drivers(self, features: List[Dict]) -> List[str]:
#         """Identify key velocity drivers"""
#         drivers = []
        
#         avg_efficiency = self._calculate_efficiency_modifier(features)
#         avg_collaboration = self._calculate_collaboration_modifier(features)
        
#         if avg_efficiency > 1.1:
#             drivers.append("High individual productivity and work ethic")
#         if avg_collaboration > 1.1:
#             drivers.append("Excellent team collaboration and knowledge sharing")
        
#         return drivers if drivers else ["Standard team productivity patterns"]
    
#     def _suggest_velocity_optimizations(self, features: List[Dict]) -> List[str]:
#         """Suggest optimizations to improve velocity"""
#         optimizations = []
        
#         efficiency_modifier = self._calculate_efficiency_modifier(features)
#         collaboration_modifier = self._calculate_collaboration_modifier(features)
        
#         if efficiency_modifier < 0.9:
#             optimizations.append("Implement productivity tools and time management training")
#         if collaboration_modifier < 0.9:
#             optimizations.append("Facilitate better knowledge sharing and pair programming")
        
#         return optimizations if optimizations else ["Team is performing at optimal velocity"]
    
#     def _fallback_prediction(self) -> Dict:
#         """Fallback prediction when generation fails"""
#         return {
#             'type': 'general',
#             'data': {
#                 'message': 'Complete team assessments for detailed predictions',
#                 'baseline_performance': 'average'
#             },
#             'confidence': 0.3,
#             'generated_at': datetime.utcnow().isoformat()
#         }


# class GeneticAlgorithmOptimizer:
#     """Genetic algorithm for team composition optimization"""
    
#     def __init__(self, population_size: int = 50, generations: int = 100):
#         self.population_size = population_size
#         self.generations = generations
#         self.mutation_rate = 0.1
#         self.elite_size = 10
    
#     def optimize_team_composition(
#         self,
#         available_people: List[Dict],
#         team_size: int,
#         objectives: List[str],
#         constraints: Dict[str, Any] = None
#     ) -> Dict[str, Any]:
#         """
#         Use genetic algorithm to find optimal team composition
        
#         Args:
#             available_people: Pool of available team members
#             team_size: Desired team size
#             objectives: Optimization objectives
#             constraints: Additional constraints
            
#         Returns:
#             Optimization result with best team composition
#         """
#         if len(available_people) < team_size:
#             raise ValueError("Not enough people available for desired team size")
        
#         try:
#             # Initialize population
#             population = self._initialize_population(available_people, team_size)
            
#             best_fitness = -1
#             best_team = None
            
#             for generation in range(self.generations):
#                 # Evaluate fitness
#                 fitness_scores = [
#                     self._evaluate_fitness(team, objectives, constraints)
#                     for team in population
#                 ]
                
#                 # Track best solution
#                 max_fitness_idx = np.argmax(fitness_scores)
#                 if fitness_scores[max_fitness_idx] > best_fitness:
#                     best_fitness = fitness_scores[max_fitness_idx]
#                     best_team = population[max_fitness_idx].copy()
                
#                 # Selection and reproduction
#                 population = self._evolve_population(population, fitness_scores)
                
#                 # Early stopping if we find a very good solution
#                 if best_fitness > 0.95:
#                     break
            
#             return {
#                 'best_team': best_team,
#                 'fitness_score': best_fitness,
#                 'generations_run': generation + 1,
#                 'optimization_objectives': objectives
#             }
            
#         except Exception as e:
#             logger.error(f"Error in genetic algorithm optimization: {str(e)}")
#             # Return random team as fallback
#             random_team = np.random.choice(len(available_people), team_size, replace=False).tolist()
#             return {
#                 'best_team': random_team,
#                 'fitness_score': 0.5,
#                 'generations_run': 0,
#                 'optimization_objectives': objectives
#             }
    
#     def _initialize_population(self, available_people: List[Dict], team_size: int) -> List[List[int]]:
#         """Initialize random population of team compositions"""
#         population = []
        
#         for _ in range(self.population_size):
#             team = np.random.choice(len(available_people), team_size, replace=False).tolist()
#             population.append(team)
        
#         return population
    
#     def _evaluate_fitness(
#         self,
#         team_indices: List[int],
#         objectives: List[str],
#         constraints: Dict[str, Any] = None
#     ) -> float:
#         """Evaluate fitness of a team composition"""
        
#         # For now, use a simplified fitness function
#         # In production, this would use the full compatibility and performance models
        
#         base_fitness = 0.5
        
#         # Diversity bonus
#         if len(set(team_indices)) == len(team_indices):  # No duplicates
#             base_fitness += 0.2
        
#         # Size penalty/bonus
#         if constraints and 'preferred_size' in constraints:
#             size_diff = abs(len(team_indices) - constraints['preferred_size'])
#             base_fitness -= size_diff * 0.1
        
#         # Random variation to simulate personality compatibility
#         compatibility_score = np.random.beta(2, 2)  # Skewed toward middle values
#         fitness = base_fitness * 0.3 + compatibility_score * 0.7
        
#         return max(0.0, min(1.0, fitness))
    
#     def _evolve_population(self, population: List[List[int]], fitness_scores: List[float]) -> List[List[int]]:
#         """Evolve population through selection, crossover, and mutation"""
        
#         # Sort by fitness
#         sorted_indices = np.argsort(fitness_scores)[::-1]  # Descending order
        
#         new_population = []
        
#         # Elite preservation
#         for i in range(self.elite_size):
#             new_population.append(population[sorted_indices[i]].copy())
        
#         # Generate rest of population through crossover and mutation
#         while len(new_population) < self.population_size:
#             # Tournament selection
#             parent1 = self._tournament_selection(population, fitness_scores)
#             parent2 = self._tournament_selection(population, fitness_scores)
            
#             # Crossover
#             child1, child2 = self._crossover(parent1, parent2)
            
#             # Mutation
#             if np.random.random() < self.mutation_rate:
#                 child1 = self._mutate(child1, len(population[0]))
#             if np.random.random() < self.mutation_rate:
#                 child2 = self._mutate(child2, len(population[0]))
            
#             new_population.extend([child1, child2])
        
#         return new_population[:self.population_size]
    
#     def _tournament_selection(self, population: List[List[int]], fitness_scores: List[float]) -> List[int]:
#         """Tournament selection for parent selection"""
#         tournament_size = 3
#         tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
#         tournament_fitness = [fitness_scores[i] for i in tournament_indices]
#         winner_idx = tournament_indices[np.argmax(tournament_fitness)]
#         return population[winner_idx].copy()
    
#     def _crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
#         """Single-point crossover"""
#         if len(parent1) != len(parent2):
#             return parent1.copy(), parent2.copy()
        
#         crossover_point = np.random.randint(1, len(parent1))
        
#         child1 = parent1[:crossover_point] + parent2[crossover_point:]
#         child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
#         # Ensure no duplicates (simplified approach)
#         child1 = list(dict.fromkeys(child1))  # Remove duplicates while preserving order
#         child2 = list(dict.fromkeys(child2))
        
#         return child1, child2
    
#     def _mutate(self, individual: List[int], max_person_index: int) -> List[int]:
#         """Mutate an individual by replacing one member"""
#         mutated = individual.copy()
        
#         if len(mutated) > 0:
#             # Replace random team member with random person
#             replace_idx = np.random.randint(len(mutated))
#             new_person = np.random.randint(max_person_index)
            
#             # Ensure we don't create duplicates
#             while new_person in mutated:
#                 new_person = np.random.randint(max_person_index)
            
#             mutated[replace_idx] = new_person
        
#         return mutated
#         # ai_engine.py - Core AI and Machine Learning Components
# import numpy as np
# import pandas as pd
# from typing import Dict, List, Any, Optional, Tuple
# from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
# from sklearn.preprocessing import StandardScaler
# from sklearn.cluster import DBSCAN
# from sklearn.metrics.pairwise import cosine_similarity
# import tensorflow as tf
# from tensorflow.keras.models import Sequential, Model
# from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, Embedding, concatenate
# from tensorflow.keras.optimizers import Adam
# import joblib
# import logging
# from datetime import datetime, timedelta
# import json

# logger = logging.getLogger(__name__)

# class BehavioralAIEngine:
#     """Main AI engine for behavioral analysis and synthesis"""
    
#     def __init__(self):
#         self.models = {}
#         self.scalers = {}
#         self.load_pretrained_models()
        
#     def load_pretrained_models(self):
#         """Load pre-trained models or initialize new ones"""
#         try:
#             # In production, these would be loaded from model storage
#             self.models['compatibility'] = self._create_compatibility_model()
#             self.models['performance'] = self._create_performance_model()
#             self.models['conflict'] = self._create_conflict_model()
#             self.models['synthesis'] = self._create_synthesis_model()
#             self.scalers['behavioral'] = StandardScaler()
#             logger.info("AI models loaded successfully")
#         except Exception as e:
#             logger.error(f"Error loading models: {str(e)}")
#             self._initialize_default_models()
    
#     def _create_compatibility_model(self):
#         """Create neural network for team compatibility prediction"""
#         model = Sequential([
#             Dense(128, activation='relu', input_shape=(50,)),
#             Dropout(0.3),
#             Dense(64, activation='relu'),
#             Dropout(0.2),
#             Dense(32, activation='relu'),
#             Dense(1, activation='sigmoid')
#         ])
#         model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
#         return model
    
#     def _create_performance_model(self):
#         """Create LSTM model for team performance prediction"""
#         model = Sequential([
#             LSTM(64, return_sequences=True, input_shape=(10, 20)),
#             Dropout(0.3),
#             LSTM(32, return_sequences=False),
#             Dropout(0.2),
#             Dense(16, activation='relu'),
#             Dense(1, activation='linear')
#         ])
#         model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
#         return model
    
#     def _create_conflict_model(self):
#         """Create conflict prediction classifier"""
#         return GradientBoostingClassifier(
#             n_estimators=100,
#             learning_rate=0.1,
#             max_depth=6,
#             random_state=42
#         )
    
#     def _create_synthesis_model(self):
#         """Create model for synthesizing multiple personality frameworks"""
#         # Multi-input neural network
#         enneagram_input = Input(shape=(9,), name='enneagram')
#         mbti_input = Input(shape=(16,), name='mbti')
#         big_five_input = Input(shape=(5,), name='big_five')
#         pi_input = Input(shape=(4,), name='predictive_index')
#         strengths_input = Input(shape=(34,), name='strengths')
        
#         # Process each framework separately
#         enneagram_dense = Dense(16, activation='relu')(enneagram_input)
#         mbti_dense = Dense(32, activation='relu')(mbti_input)
#         big_five_dense = Dense(8, activation='relu')(big_five_input)
#         pi_dense = Dense(8, activation='relu')(pi_input)
#         strengths_dense = Dense(16, activation='relu')(strengths_input)
        
#         # Concatenate all processed inputs
#         combined = concatenate([
#             enneagram_dense, mbti_dense, big_five_dense, 
#             pi_dense, strengths_dense
#         ])
        
#         # Final synthesis layers
#         synthesis = Dense(64, activation='relu')(combined)
#         synthesis = Dropout(0.3)(synthesis)
#         synthesis = Dense(32, activation='relu')(synthesis)
#         output = Dense(20, activation='sigmoid', name='unified_profile')(synthesis)
        
#         model = Model(
#             inputs=[enneagram_input, mbti_input, big_five_input, pi_input, strengths_input],
#             outputs=output
#         )
#         model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])
#         return model
    
#     def _initialize_default_models(self):
#         """Initialize default models if loading fails"""
#         self.models = {
#             'compatibility': self._create_compatibility_model(),
#             'performance': self._create_performance_model(),
#             'conflict': self._create_conflict_model(),
#             'synthesis': self._create_synthesis_model()
#         }
#         self.scalers = {'behavioral': StandardScaler()}
    
#     def synthesize_personality_profile(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
#         """
#         Combine insights from multiple personality frameworks into unified profile
        
#         Args:
#             assessments: Dict with framework names as keys, results as values
            
#         Returns:
#             Unified personality profile with standardized metrics
#         """
#         try:
#             # Convert assessments to feature vectors
#             feature_vectors = self._convert_assessments_to_features(assessments)
            
#             # Use synthesis model if available, otherwise use weighted combination
#             if 'synthesis' in self.models and len(feature_vectors) >= 3:
#                 unified_profile = self._ai_synthesis(feature_vectors)
#             else:
#                 unified_profile = self._weighted_synthesis(assessments)
            
#             # Add confidence score based on data completeness
#             confidence = self._calculate_synthesis_confidence(assessments)
#             unified_profile['confidence'] = confidence
#             unified_profile['synthesis_method'] = 'ai_model' if len(feature_vectors) >= 3 else 'weighted'
#             unified_profile['frameworks_used'] = list(assessments.keys())
            
#             return unified_profile
            
#         except Exception as e:
#             logger.error(f"Error in personality synthesis: {str(e)}")
#             return self._fallback_synthesis(assessments)
    
#     def _convert_assessments_to_features(self, assessments: Dict[str, Dict]) -> Dict[str, np.ndarray]:
#         """Convert assessment results to standardized feature vectors"""
#         feature_vectors = {}
        
#         for framework, results in assessments.items():
#             if framework == 'enneagram':
#                 vector = self._enneagram_to_vector(results)
#             elif framework == 'mbti':
#                 vector = self._mbti_to_vector(results)
#             elif framework == 'big_five':
#                 vector = self._big_five_to_vector(results)
#             elif framework == 'predictive_index':
#                 vector = self._pi_to_vector(results)
#             elif framework == 'strengths':
#                 vector = self._strengths_to_vector(results)
#             else:
#                 continue
                
#             feature_vectors[framework] = vector
            
#         return feature_vectors
    
#     def _enneagram_to_vector(self, results: Dict) -> np.ndarray:
#         """Convert Enneagram results to feature vector"""
#         vector = np.zeros(9)
#         primary_type = results.get('type', 1) - 1  # Convert to 0-indexed
#         if 0 <= primary_type < 9:
#             vector[primary_type] = results.get('confidence', 0.8)
            
#         # Add wing influence if present
#         wing = results.get('wing')
#         if wing:
#             wing_index = int(wing.split('w')[1]) - 1
#             if 0 <= wing_index < 9:
#                 vector[wing_index] += 0.3
                
#         return vector
    
#     def _mbti_to_vector(self, results: Dict) -> np.ndarray:
#         """Convert MBTI results to feature vector"""
#         type_mapping = {
#             'INTJ': 0, 'INTP': 1, 'ENTJ': 2, 'ENTP': 3,
#             'INFJ': 4, 'INFP': 5, 'ENFJ': 6, 'ENFP': 7,
#             'ISTJ': 8, 'ISFJ': 9, 'ESTJ': 10, 'ESFJ': 11,
#             'ISTP': 12, 'ISFP': 13, 'ESTP': 14, 'ESFP': 15
#         }
        
#         vector = np.zeros(16)
#         mbti_type = results.get('type', 'INTJ')
#         if mbti_type in type_mapping:
#             vector[type_mapping[mbti_type]] = results.get('confidence', 0.8)
            
#         return vector
    
#     def _big_five_to_vector(self, results: Dict) -> np.ndarray:
#         """Convert Big Five results to feature vector"""
#         dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
#         vector = np.array([results.get(dim, 0.5) for dim in dimensions])
#         return vector
    
#     def _pi_to_vector(self, results: Dict) -> np.ndarray:
#         """Convert Predictive Index results to feature vector"""
#         dimensions = ['dominance', 'extraversion', 'patience', 'formality']
#         vector = np.array([results.get(dim, 0.5) for dim in dimensions])
#         return vector
    
#     def _strengths_to_vector(self, results: Dict) -> np.ndarray:
#         """Convert StrengthsFinder results to feature vector"""
#         all_themes = [
#             'Achiever', 'Activator', 'Adaptability', 'Analytical', 'Arranger', 'Belief',
#             'Command', 'Communication', 'Competition', 'Connectedness', 'Consistency',
#             'Context', 'Deliberative', 'Developer', 'Discipline', 'Empathy', 'Focus',
#             'Futuristic', 'Harmony', 'Ideation', 'Includer', 'Individualization',
#             'Input', 'Intellection', 'Learner', 'Maximizer', 'Positivity', 'Relator',
#             'Responsibility', 'Restorative', 'Self-Assurance', 'Significance', 'Strategic', 'Woo'
#         ]
        
#         vector = np.zeros(34)
#         top_themes = results.get('top_themes', [])
        
#         for i, theme in enumerate(top_themes[:5]):  # Top 5 themes
#             if theme in all_themes:
#                 theme_index = all_themes.index(theme)
#                 vector[theme_index] = (5 - i) / 5  # Weight by ranking
                
#         return vector
    
#     def _ai_synthesis(self, feature_vectors: Dict[str, np.ndarray]) -> Dict[str, Any]:
#         """Use AI model to synthesize personality frameworks"""
#         try:
#             # Prepare inputs for the synthesis model
#             inputs = {}
#             for framework in ['enneagram', 'mbti', 'big_five', 'predictive_index', 'strengths']:
#                 if framework in feature_vectors:
#                     inputs[framework] = feature_vectors[framework].reshape(1, -1)
#                 else:
#                     # Use neutral/average values for missing frameworks
#                     if framework == 'enneagram':
#                         inputs[framework] = np.full((1, 9), 1/9)
#                     elif framework == 'mbti':
#                         inputs[framework] = np.full((1, 16), 1/16)
#                     elif framework == 'big_five':
#                         inputs[framework] = np.full((1, 5), 0.5)
#                     elif framework == 'predictive_index':
#                         inputs[framework] = np.full((1, 4), 0.5)
#                     elif framework == 'strengths':
#                         inputs[framework] = np.full((1, 34), 0.1)
            
#             # Generate unified profile
#             unified_vector = self.models['synthesis'].predict([
#                 inputs['enneagram'], inputs['mbti'], inputs['big_five'],
#                 inputs['predictive_index'], inputs['strengths']
#             ])[0]
            
#             # Convert to interpretable profile
#             profile = self._vector_to_profile(unified_vector)
#             return profile
            
#         except Exception as e:
#             logger.error(f"Error in AI synthesis: {str(e)}")
#             return self._fallback_synthesis(feature_vectors)
    
#     def _weighted_synthesis(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
#         """Fallback weighted combination of assessments"""
#         # Framework weights based on research validity
#         weights = {
#             'big_five': 0.3,
#             'mbti': 0.25,
#             'enneagram': 0.2,
#             'predictive_index': 0.15,
#             'strengths': 0.1
#         }
        
#         # Synthesize Big Five dimensions
#         dimensions = {}
#         total_weight = 0
        
#         for framework, results in assessments.items():
#             if framework not in weights:
#                 continue
                
#             weight = weights[framework]
#             total_weight += weight
            
#             if framework == 'big_five':
#                 for dim in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
#                     if dim not in dimensions:
#                         dimensions[dim] = 0
#                     dimensions[dim] += results.get(dim, 0.5) * weight
                    
#             elif framework == 'mbti':
#                 # Map MBTI to Big Five approximations
#                 mbti_type = results.get('type', 'INTJ')
#                 big_five_approx = self._mbti_to_big_five(mbti_type)
#                 for dim, value in big_five_approx.items():
#                     if dim not in dimensions:
#                         dimensions[dim] = 0
#                     dimensions[dim] += value * weight
        
#         # Normalize by total weight
#         if total_weight > 0:
#             for dim in dimensions:
#                 dimensions[dim] /= total_weight
        
#         # Add derived metrics
#         profile = dimensions.copy()
#         profile.update({
#             'leadership_potential': self._calculate_leadership_potential(dimensions),
#             'collaboration_index': self._calculate_collaboration_index(dimensions),
#             'stress_tolerance': self._calculate_stress_tolerance(dimensions),
#             'adaptability': self._calculate_adaptability(dimensions)
#         })
        
#         return profile
    
#     def _mbti_to_big_five(self, mbti_type: str) -> Dict[str, float]:
#         """Approximate MBTI type to Big Five dimensions"""
#         # Simplified mapping based on research correlations
#         mappings = {
#             'E': {'extraversion': 0.75},
#             'I': {'extraversion': 0.25},
#             'S': {'openness': 0.3, 'conscientiousness': 0.6},
#             'N': {'openness': 0.7, 'conscientiousness': 0.4},
#             'T': {'agreeableness': 0.3},
#             'F': {'agreeableness': 0.7},
#             'J': {'conscientiousness': 0.7},
#             'P': {'conscientiousness': 0.3, 'openness': 0.6}
#         }
        
#         result = {'openness': 0.5, 'conscientiousness': 0.5, 'extraversion': 0.5, 'agreeableness': 0.5, 'neuroticism': 0.5}
        
#         for letter in mbti_type:
#             if letter in mappings:
#                 for dimension, value in mappings[letter].items():
#                     result[dimension] = value
                    
#         return result
    
#     def _vector_to_profile(self, vector: np.ndarray) -> Dict[str, Any]:
#         """Convert unified vector back to interpretable profile"""
#         # This is a simplified version - in production, this would be more sophisticated
#         profile = {
#             'openness': float(vector[0]),
#             'conscientiousness': float(vector[1]),
#             'extraversion': float(vector[2]),
#             'agreeableness': float(vector[3]),
#             'neuroticism': float(vector[4]),
#             'leadership_potential': float(vector[5]),
#             'collaboration_index': float(vector[6]),
#             'stress_tolerance': float(vector[7]),
#             'adaptability': float(vector[8]),
#             'communication_style': self._determine_communication_style(vector),
#             'work_preferences': self._determine_work_preferences(vector),
#             'team_roles': self._suggest_team_roles(vector)
#         }
        
#         return profile
    
#     def _calculate_synthesis_confidence(self, assessments: Dict[str, Dict]) -> float:
#         """Calculate confidence in synthesis based on data quality"""
#         base_confidence = 0.4
#         framework_bonus = len(assessments) * 0.1
        
#         # Bonus for high-quality frameworks
#         quality_bonus = 0
#         for framework in assessments:
#             if framework in ['big_five', 'mbti', 'predictive_index']:
#                 quality_bonus += 0.1
                
#         # Penalty for missing key frameworks
#         if 'big_five' not in assessments and 'mbti' not in assessments:
#             quality_bonus -= 0.2
            
#         confidence = min(0.95, base_confidence + framework_bonus + quality_bonus)
#         return max(0.1, confidence)
    
#     def _calculate_leadership_potential(self, dimensions: Dict[str, float]) -> float:
#         """Calculate leadership potential from personality dimensions"""
#         return (
#             dimensions.get('extraversion', 0.5) * 0.3 +
#             dimensions.get('conscientiousness', 0.5) * 0.25 +
#             dimensions.get('openness', 0.5) * 0.2 +
#             dimensions.get('agreeableness', 0.5) * 0.15 +
#             (1 - dimensions.get('neuroticism', 0.5)) * 0.1
#         )
    
#     def _calculate_collaboration_index(self, dimensions: Dict[str, float]) -> float:
#         """Calculate collaboration effectiveness"""
#         return (
#             dimensions.get('agreeableness', 0.5) * 0.4 +
#             dimensions.get('extraversion', 0.5) * 0.3 +
#             dimensions.get('openness', 0.5) * 0.2 +
#             (1 - dimensions.get('neuroticism', 0.5)) * 0.1
#         )
    
#     def _calculate_stress_tolerance(self, dimensions: Dict[str, float]) -> float:
#         """Calculate stress tolerance"""
#         return (
#             (1 - dimensions.get('neuroticism', 0.5)) * 0.5 +
#             dimensions.get('conscientiousness', 0.5) * 0.3 +
#             dimensions.get('extraversion', 0.5) * 0.2
#         )
    
#     def _calculate_adaptability(self, dimensions: Dict[str, float]) -> float:
#         """Calculate adaptability to change"""
#         return (
#             dimensions.get('openness', 0.5) * 0.4 +
#             (1 - dimensions.get('neuroticism', 0.5)) * 0.3 +
#             dimensions.get('extraversion', 0.5) * 0.2 +
#             (1 - dimensions.get('conscientiousness', 0.5)) * 0.1  # Less rigid structure preference
#         )
    
#     def _determine_communication_style(self, vector: np.ndarray) -> str:
#         """Determine primary communication style"""
#         extraversion = vector[2] if len(vector) > 2 else 0.5
#         agreeableness = vector[3] if len(vector) > 3 else 0.5
        
#         if extraversion > 0.6 and agreeableness > 0.6:
#             return "collaborative"
#         elif extraversion > 0.6 and agreeableness < 0.4:
#             return "assertive"
#         elif extraversion < 0.4 and agreeableness > 0.6:
#             return "supportive"
#         else:
#             return "analytical"
    
#     def _determine_work_preferences(self, vector: np.ndarray) -> List[str]:
#         """Determine work environment preferences"""
#         preferences = []
        
#         openness = vector[0] if len(vector) > 0 else 0.5
#         conscientiousness = vector[1] if len(vector) > 1 else 0.5
#         extraversion = vector[2] if len(vector) > 2 else 0.5
        
#         if openness > 0.6:
#             preferences.extend(["creative_projects", "innovation"])
#         if conscientiousness > 0.6:
#             preferences.extend(["structured_environment", "clear_deadlines"])
#         if extraversion > 0.6:
#             preferences.extend(["team_collaboration", "public_speaking"])
#         else:
#             preferences.extend(["focused_work", "minimal_interruptions"])
            
#         return preferences
    
#     def _suggest_team_roles(self, vector: np.ndarray) -> List[str]:
#         """Suggest optimal team roles"""
#         roles = []
        
#         leadership_potential = vector[5] if len(vector) > 5 else 0.5
#         collaboration_index = vector[6] if len(vector) > 6 else 0.5
        
#         if leadership_potential > 0.7:
#             roles.append("team_lead")
#         if collaboration_index > 0.7:
#             roles.extend(["scrum_master", "facilitator"])
#         if vector[0] > 0.7:  # High openness
#             roles.extend(["architect", "innovator"])
#         if vector[1] > 0.7:  # High conscientiousness
#             roles.extend(["quality_assurance", "project_coordinator"])
            
#         return roles if roles else ["team_member"]
    
#     def _fallback_synthesis(self, assessments: Dict) -> Dict[str, Any]:
#         """Simple fallback when AI synthesis fails"""
#         return {
#             'openness': 0.5,
#             'conscientiousness': 0.5,
#             'extraversion': 0.5,
#             'agreeableness': 0.5,
#             'neuroticism': 0.5,
#             'leadership_potential': 0.5,
#             'collaboration_index': 0.5,
#             'stress_tolerance': 0.5,
#             'adaptability': 0.5,
#             'confidence': 0.3,
#             'synthesis_method': 'fallback',
#             'frameworks_used': list(assessments.keys()) if isinstance(assessments, dict) else []
#         }


# class TeamOptimizer:
#     """Optimize team composition and dynamics"""
    
#     def __init__(self):
#         self.compatibility_calculator = CompatibilityCalculator()
#         self.genetic_algorithm = GeneticAlgorithmOptimizer()
        
#     def optimize_team_composition(
#         self,
#         team_profiles: List[Dict],
#         project_requirements: Dict[str, Any],
#         optimization_goals: List[str]
#     ) -> Dict[str, Any]:
#         """
#         Optimize team composition for maximum effectiveness
        
#         Args:
#             team_profiles: List of team member profiles with personality data
#             project_requirements: Requirements and constraints for the project
#             optimization_goals: List of optimization objectives
            
#         Returns:
#             Optimization results with recommendations
#         """
#         try:
#             # Calculate pairwise compatibility matrix
#             compatibility_matrix = self._calculate_team_compatibility_matrix(team_profiles)
            
#             # Analyze current team composition
#             current_metrics = self._analyze_current_composition(team_profiles, compatibility_matrix)
            
#             # Generate optimization recommendations
#             recommendations = self._generate_optimization_recommendations(
#                 team_profiles,
#                 compatibility_matrix,
#                 project_requirements,
#                 optimization_goals
#             )
            
#             # Predict team performance
#             performance_prediction = self._predict_team_performance(
#                 team_profiles,
#                 compatibility_matrix,
#                 project_requirements
#             )
            
#             return {
#                 'current_metrics': current_metrics,
#                 'compatibility_matrix': compatibility_matrix,
#                 'recommendations': recommendations,
#                 'performance_prediction': performance_prediction,
#                 'optimization_score': current_metrics['overall_score'],
#                 'generated_at': datetime.utcnow().isoformat()
#             }
            
#         except Exception as e:
#             logger.error(f"Error in team optimization: {str(e)}")
#             return self._fallback_optimization_result(team_profiles)
    
#     def _calculate_team_compatibility_matrix(self, team_profiles: List[Dict]) -> List[List[float]]:
#         """Calculate compatibility between all team member pairs"""
#         n = len(team_profiles)
#         matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
#         for i in range(n):
#             for j in range(i + 1, n):
#                 compatibility = self.compatibility_calculator.calculate_compatibility(
#                     team_profiles[i]['profile'],
#                     team_profiles[j]['profile']
#                 )
#                 matrix[i][j] = matrix[j][i] = compatibility
                
#         # Self-compatibility is always 1.0
#         for i in range(n):
#             matrix[i][i] = 1.0
            
#         return matrix
    
#     def _analyze_current_composition(self, team_profiles: List[Dict], compatibility_matrix: List[List[float]]) -> Dict[str, Any]:
#         """Analyze current team composition metrics"""
#         n = len(team_profiles)
        
#         # Calculate overall compatibility
#         total_compatibility = 0
#         pair_count = 0
        
#         for i in range(n):
#             for j in range(i + 1, n):
#                 total_compatibility += compatibility_matrix[i][j]
#                 pair_count += 1
        
#         avg_compatibility = total_compatibility / pair_count if pair_count > 0 else 0
        
#         # Analyze personality diversity
#         diversity_score = self._calculate_personality_diversity(team_profiles)
        
#         # Identify potential conflicts
#         conflict_pairs = self._identify_conflict_pairs(compatibility_matrix, threshold=0.3)
        
#         # Calculate team balance
#         balance_score = self._calculate_team_balance(team_profiles)
        