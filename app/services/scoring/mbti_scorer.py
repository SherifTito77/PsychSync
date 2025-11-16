# app/services/scoring/mbti_scorer.py
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.models.assessment import AssessmentResponse
from app.db.models.scoring import AssessmentScoringConfig


class MBTIScorer:
    """
    MBTI (Myers-Briggs Type Indicator) Scoring
    
    Four dimensions:
    - E (Extraversion) vs I (Introversion)
    - S (Sensing) vs N (Intuition)
    - T (Thinking) vs F (Feeling)
    - J (Judging) vs P (Perceiving)
    
    Each dimension scored 0-100, type determined by >50
    """
    
    DIMENSIONS = {
        "E-I": {"positive": "E", "negative": "I", "name": "Extraversion-Introversion"},
        "S-N": {"positive": "S", "negative": "N", "name": "Sensing-Intuition"},
        "T-F": {"positive": "T", "negative": "F", "name": "Thinking-Feeling"},
        "J-P": {"positive": "J", "negative": "P", "name": "Judging-Perceiving"}
    }
    
    TYPE_DESCRIPTIONS = {
        "INTJ": "The Architect - Strategic, analytical, independent thinkers",
        "INTP": "The Logician - Innovative inventors with endless curiosity",
        "ENTJ": "The Commander - Bold, imaginative, strong-willed leaders",
        "ENTP": "The Debater - Smart, curious thinkers who love intellectual challenges",
        "INFJ": "The Advocate - Quiet, mystical, inspiring idealists",
        "INFP": "The Mediator - Poetic, kind, altruistic individuals",
        "ENFJ": "The Protagonist - Charismatic, inspiring leaders",
        "ENFP": "The Campaigner - Enthusiastic, creative, sociable free spirits",
        "ISTJ": "The Logistician - Practical, fact-minded, reliable individuals",
        "ISFJ": "The Defender - Dedicated, warm protectors",
        "ESTJ": "The Executive - Excellent administrators, managing people and things",
        "ESFJ": "The Consul - Caring, social, popular individuals",
        "ISTP": "The Virtuoso - Bold, practical experimenters",
        "ISFP": "The Adventurer - Flexible, charming artists",
        "ESTP": "The Entrepreneur - Smart, energetic, perceptive individuals",
        "ESFP": "The Entertainer - Spontaneous, energetic, enthusiastic entertainers"
    }
    
    @staticmethod
    def calculate_scores(
        response: AssessmentResponse,
        config: AssessmentScoringConfig
    ) -> Dict[str, Any]:
        """
        Calculate MBTI scores from response
        
        Args:
            response: AssessmentResponse object
            config: Scoring configuration
            
        Returns:
            Dict with dimension scores and type
        """
        scoring_config = config.config
        responses_data = response.responses
        
        dimension_scores = {}
        
        # Calculate each dimension
        for dimension, question_ids in scoring_config.get("dimensions", {}).items():
            score = MBTIScorer._calculate_dimension_score(
                dimension,
                question_ids,
                responses_data,
                scoring_config.get("reverse_scored", {}).get(dimension, [])
            )
            dimension_scores[dimension] = score
        
        # Determine type
        mbti_type = MBTIScorer._determine_type(dimension_scores)
        
        # Get interpretation
        interpretation = MBTIScorer._get_interpretation(mbti_type, dimension_scores)
        
        return {
            "algorithm": "mbti",
            "dimension_scores": dimension_scores,
            "mbti_type": mbti_type,
            "type_description": MBTIScorer.TYPE_DESCRIPTIONS.get(mbti_type, ""),
            "interpretation": interpretation,
            "subscale_scores": dimension_scores
        }
    
    @staticmethod
    def _calculate_dimension_score(
        dimension: str,
        question_ids: List[int],
        responses: Dict[str, Any],
        reverse_scored: List[int]
    ) -> float:
        """Calculate score for a single dimension (0-100)"""
        if not question_ids:
            return 50.0
        
        total_score = 0
        valid_responses = 0
        
        for q_id in question_ids:
            q_key = str(q_id)
            if q_key in responses and responses[q_key] is not None:
                value = responses[q_key]
                
                # Handle different response types
                if isinstance(value, bool):
                    value = 5 if value else 1
                elif isinstance(value, str):
                    try:
                        value = float(value)
                    except:
                        continue
                
                # Reverse score if needed
                if q_id in reverse_scored:
                    value = 6 - value  # Assuming 1-5 scale
                
                total_score += value
                valid_responses += 1
        
        if valid_responses == 0:
            return 50.0
        
        # Convert to 0-100 scale
        # Assuming original scale is 1-5
        avg_score = total_score / valid_responses
        normalized_score = ((avg_score - 1) / 4) * 100
        
        return round(normalized_score, 2)
    
    @staticmethod
    def _determine_type(dimension_scores: Dict[str, float]) -> str:
        """Determine MBTI type from dimension scores"""
        type_letters = []
        
        for dimension, score in dimension_scores.items():
            dim_info = MBTIScorer.DIMENSIONS.get(dimension, {})
            if score >= 50:
                type_letters.append(dim_info.get("positive", ""))
            else:
                type_letters.append(dim_info.get("negative", ""))
        
        return "".join(type_letters)
    
    @staticmethod
    def _get_interpretation(mbti_type: str, scores: Dict[str, float]) -> str:
        """Generate detailed interpretation"""
        interpretation = []
        
        interpretation.append(f"Your MBTI type is: {mbti_type}")
        interpretation.append(MBTIScorer.TYPE_DESCRIPTIONS.get(mbti_type, ""))
        interpretation.append("\nDimension Breakdown:")
        
        for dimension, score in scores.items():
            dim_info = MBTIScorer.DIMENSIONS.get(dimension, {})
            if score >= 50:
                pref = f"{dim_info['positive']} ({dim_info['name'].split('-')[0]})"
                strength = "Strong" if score >= 70 else "Moderate" if score >= 55 else "Slight"
            else:
                pref = f"{dim_info['negative']} ({dim_info['name'].split('-')[1]})"
                strength = "Strong" if score <= 30 else "Moderate" if score <= 45 else "Slight"
            
            interpretation.append(f"- {pref}: {strength} preference ({score:.1f}%)")
        
        return "\n".join(interpretation)
    
    @staticmethod
    def create_default_config(assessment_id: int, question_mapping: Dict[str, List[int]]) -> Dict[str, Any]:
        """
        Create default MBTI scoring configuration
        
        Args:
            assessment_id: Assessment ID
            question_mapping: Dict mapping dimensions to question IDs
                Example: {
                    "E-I": [1, 5, 9, 13],
                    "S-N": [2, 6, 10, 14],
                    "T-F": [3, 7, 11, 15],
                    "J-P": [4, 8, 12, 16]
                }
        """
        return {
            "algorithm": "mbti",
            "dimensions": question_mapping,
            "reverse_scored": {},  # Add question IDs that should be reverse scored
            "interpretation_rules": {
                "strong_preference": 70,
                "moderate_preference": 55,
                "slight_preference": 50
            }
        }
        