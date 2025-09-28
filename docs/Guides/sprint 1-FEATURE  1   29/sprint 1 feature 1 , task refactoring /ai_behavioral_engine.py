# app/ai/engine/behavioral_ai.py - Main Behavioral AI Engine

import numpy as np
from typing import Dict, List, Any, Optional
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


class BehavioralAIEngine:
    """Main AI engine for behavioral analysis and synthesis"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self._load_models()
    
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
        self.models = {'synthesis': None}
        self.scalers = {'behavioral': None}
    
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
    
    def _ai_synthesis(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
        """Use AI model to synthesize personality frameworks (placeholder for now)"""
        # This would use the neural network model for synthesis
        # For now, fall back to weighted synthesis
        return self._weighted_synthesis(assessments)
    
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