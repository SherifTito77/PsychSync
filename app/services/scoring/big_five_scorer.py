# app/services/scoring/big_five_scorer.py
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import AssessmentResponse
from app.db.models.scoring import AssessmentScoringConfig


class BigFiveScorer:
    """
    Big Five (OCEAN) Scoring
    
    Five factors:
    - O: Openness to Experience
    - C: Conscientiousness
    - E: Extraversion
    - A: Agreeableness
    - N: Neuroticism (Emotional Stability)
    
    Each factor scored 0-100
    """
    
    FACTORS = {
        "openness": {
            "name": "Openness to Experience",
            "description": "Imagination, curiosity, and willingness to try new things",
            "facets": ["Fantasy", "Aesthetics", "Feelings", "Actions", "Ideas", "Values"]
        },
        "conscientiousness": {
            "name": "Conscientiousness",
            "description": "Organization, responsibility, and reliability",
            "facets": ["Competence", "Order", "Dutifulness", "Achievement", "Self-Discipline", "Deliberation"]
        },
        "extraversion": {
            "name": "Extraversion",
            "description": "Sociability, assertiveness, and energy level",
            "facets": ["Warmth", "Gregariousness", "Assertiveness", "Activity", "Excitement-Seeking", "Positive Emotions"]
        },
        "agreeableness": {
            "name": "Agreeableness",
            "description": "Compassion, cooperativeness, and trust in others",
            "facets": ["Trust", "Straightforwardness", "Altruism", "Compliance", "Modesty", "Tender-Mindedness"]
        },
        "neuroticism": {
            "name": "Neuroticism",
            "description": "Emotional stability and tendency toward negative emotions",
            "facets": ["Anxiety", "Angry Hostility", "Depression", "Self-Consciousness", "Impulsiveness", "Vulnerability"]
        }
    }
    
    @staticmethod
    def calculate_scores(
        response: AssessmentResponse,
        config: AssessmentScoringConfig
    ) -> Dict[str, Any]:
        """Calculate Big Five scores from response"""
        scoring_config = config.config
        responses_data = response.responses
        
        factor_scores = {}
        percentile_scores = {}
        
        # Calculate each factor
        for factor, question_ids in scoring_config.get("factors", {}).items():
            score = BigFiveScorer._calculate_factor_score(
                factor,
                question_ids,
                responses_data,
                scoring_config.get("reverse_scored", {}).get(factor, [])
            )
            factor_scores[factor] = score
            percentile_scores[factor] = BigFiveScorer._score_to_percentile(score)
        
        # Get interpretation
        interpretation = BigFiveScorer._get_interpretation(factor_scores)
        
        # Calculate profile
        profile = BigFiveScorer._determine_profile(factor_scores)
        
        return {
            "algorithm": "big_five",
            "factor_scores": factor_scores,
            "percentile_scores": percentile_scores,
            "profile": profile,
            "interpretation": interpretation,
            "subscale_scores": factor_scores
        }
    
    @staticmethod
    def _calculate_factor_score(
        factor: str,
        question_ids: List[int],
        responses: Dict[str, Any],
        reverse_scored: List[int]
    ) -> float:
        """Calculate score for a single factor (0-100)"""
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
        avg_score = total_score / valid_responses
        normalized_score = ((avg_score - 1) / 4) * 100
        
        return round(normalized_score, 2)
    
    @staticmethod
    def _score_to_percentile(score: float) -> int:
        """Convert raw score to percentile (approximate)"""
        # Simplified percentile conversion
        # In production, use normative data
        if score >= 90:
            return 98
        elif score >= 80:
            return 90
        elif score >= 70:
            return 75
        elif score >= 60:
            return 60
        elif score >= 50:
            return 50
        elif score >= 40:
            return 40
        elif score >= 30:
            return 25
        elif score >= 20:
            return 10
        else:
            return 2
    
    @staticmethod
    def _get_interpretation(factor_scores: Dict[str, float]) -> str:
        """Generate detailed interpretation"""
        interpretation = []
        
        interpretation.append("Big Five Personality Profile:\n")
        
        for factor, score in factor_scores.items():
            factor_info = BigFiveScorer.FACTORS.get(factor, {})
            name = factor_info.get("name", factor.title())
            description = factor_info.get("description", "")
            
            # Determine level
            if score >= 70:
                level = "Very High"
                qualifier = "significantly above average"
            elif score >= 55:
                level = "High"
                qualifier = "above average"
            elif score >= 45:
                level = "Average"
                qualifier = "typical"
            elif score >= 30:
                level = "Low"
                qualifier = "below average"
            else:
                level = "Very Low"
                qualifier = "significantly below average"
            
            interpretation.append(f"\n{name}: {level} ({score:.1f}/100)")
            interpretation.append(f"  {description}")
            interpretation.append(f"  Your score is {qualifier} for this trait.")
        
        return "\n".join(interpretation)
    
    @staticmethod
    def _determine_profile(factor_scores: Dict[str, float]) -> str:
        """Determine overall personality profile"""
        # Simplified profile determination
        high_factors = [f for f, s in factor_scores.items() if s >= 60]
        low_factors = [f for f, s in factor_scores.items() if s <= 40]
        
        if len(high_factors) >= 3:
            return "Well-adjusted with multiple strong traits"
        elif "neuroticism" in low_factors and len(high_factors) >= 2:
            return "Emotionally stable with positive traits"
        elif "openness" in high_factors and "conscientiousness" in high_factors:
            return "Creative and organized achiever"
        elif "extraversion" in high_factors and "agreeableness" in high_factors:
            return "Socially engaged and cooperative"
        else:
            return "Balanced personality profile"
    
    @staticmethod
    def create_default_config(assessment_id: int, question_mapping: Dict[str, List[int]]) -> Dict[str, Any]:
        """
        Create default Big Five scoring configuration
        
        Args:
            assessment_id: Assessment ID
            question_mapping: Dict mapping factors to question IDs
                Example: {
                    "openness": [1, 6, 11, 16, 21, 26],
                    "conscientiousness": [2, 7, 12, 17, 22, 27],
                    "extraversion": [3, 8, 13, 18, 23, 28],
                    "agreeableness": [4, 9, 14, 19, 24, 29],
                    "neuroticism": [5, 10, 15, 20, 25, 30]
                }
        """
        return {
            "algorithm": "big_five",
            "factors": question_mapping,
            "reverse_scored": {},
            "interpretation_rules": {
                "very_high": 70,
                "high": 55,
                "average_low": 45,
                "low": 30
            }
        }
        