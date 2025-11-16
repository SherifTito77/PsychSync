# app/services/scoring/disc_scorer.py
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import AssessmentResponse
from app.db.models.scoring import AssessmentScoringConfig


class DISCScorer:
    """
    DISC Personality Assessment Scoring
    
    Four dimensions:
    - D: Dominance (direct, results-oriented, decisive)
    - I: Influence (outgoing, enthusiastic, optimistic)
    - S: Steadiness (supportive, cooperative, reliable)
    - C: Conscientiousness (analytical, reserved, precise)
    
    Each dimension scored 0-100
    Primary style determined by highest score
    """
    
    STYLES = {
        "D": {
            "name": "Dominance",
            "description": "Direct, results-oriented, decisive",
            "strengths": ["Problem-solving", "Taking charge", "Quick decisions"],
            "challenges": ["Impatience", "Insensitivity", "Poor listening"],
            "motivators": ["Challenges", "Authority", "Achievement"],
            "fears": ["Being taken advantage of", "Loss of control"]
        },
        "I": {
            "name": "Influence",
            "description": "Outgoing, enthusiastic, optimistic",
            "strengths": ["Enthusiasm", "Persuasion", "Building relationships"],
            "challenges": ["Disorganization", "Impulsiveness", "Lack of follow-through"],
            "motivators": ["Recognition", "Social approval", "Popularity"],
            "fears": ["Rejection", "Disapproval", "Loss of influence"]
        },
        "S": {
            "name": "Steadiness",
            "description": "Supportive, cooperative, reliable",
            "strengths": ["Patience", "Team support", "Consistency"],
            "challenges": ["Resistance to change", "Indecisiveness", "Avoiding conflict"],
            "motivators": ["Stability", "Appreciation", "Cooperation"],
            "fears": ["Loss of stability", "Sudden change", "Confrontation"]
        },
        "C": {
            "name": "Conscientiousness",
            "description": "Analytical, reserved, precise",
            "strengths": ["Accuracy", "Analysis", "Systematic approach"],
            "challenges": ["Perfectionism", "Over-analysis", "Social discomfort"],
            "motivators": ["Quality", "Expertise", "Accuracy"],
            "fears": ["Criticism", "Being wrong", "Loss of standards"]
        }
    }
    
    STYLE_COMBINATIONS = {
        "DI": "Results-oriented leader who inspires others",
        "DC": "Driven perfectionist focused on results and quality",
        "DS": "Balanced leader who values both results and relationships",
        "ID": "Charismatic motivator who drives action",
        "IS": "Enthusiastic team player who builds consensus",
        "IC": "Persuasive analyst who combines charm with data",
        "SD": "Steady achiever who balances support with results",
        "SI": "Warm networker who maintains stable relationships",
        "SC": "Reliable specialist who provides consistent quality",
        "CD": "Determined analyst who ensures precise execution",
        "CI": "Analytical communicator who presents data engagingly",
        "CS": "Meticulous supporter who maintains high standards"
    }
    
    @staticmethod
    def calculate_scores(
        response: AssessmentResponse,
        config: AssessmentScoringConfig
    ) -> Dict[str, Any]:
        """Calculate DISC scores from response"""
        scoring_config = config.config
        responses_data = response.responses
        
        dimension_scores = {}
        
        # Calculate each dimension
        for dimension, question_ids in scoring_config.get("dimensions", {}).items():
            score = DISCScorer._calculate_dimension_score(
                dimension,
                question_ids,
                responses_data
            )
            dimension_scores[dimension] = score
        
        # Determine primary and secondary styles
        primary_style, secondary_style = DISCScorer._determine_styles(dimension_scores)
        
        # Get interpretation
        interpretation = DISCScorer._get_interpretation(
            dimension_scores,
            primary_style,
            secondary_style
        )
        
        # Get behavioral insights
        insights = DISCScorer._get_behavioral_insights(primary_style, secondary_style)
        
        return {
            "algorithm": "disc",
            "dimension_scores": dimension_scores,
            "primary_style": primary_style,
            "secondary_style": secondary_style,
            "style_combination": f"{primary_style}{secondary_style}" if secondary_style else primary_style,
            "interpretation": interpretation,
            "behavioral_insights": insights,
            "subscale_scores": dimension_scores
        }
    
    @staticmethod
    def _calculate_dimension_score(
        dimension: str,
        question_ids: List[int],
        responses: Dict[str, Any]
    ) -> float:
        """Calculate score for a single dimension (0-100)"""
        if not question_ids:
            return 25.0  # Default low score
        
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
                
                total_score += value
                valid_responses += 1
        
        if valid_responses == 0:
            return 25.0
        
        # Convert to 0-100 scale
        avg_score = total_score / valid_responses
        normalized_score = ((avg_score - 1) / 4) * 100
        
        return round(normalized_score, 2)
    
    @staticmethod
    def _determine_styles(dimension_scores: Dict[str, float]) -> tuple:
        """Determine primary and secondary DISC styles"""
        # Sort dimensions by score
        sorted_dimensions = sorted(
            dimension_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_style = sorted_dimensions[0][0] if sorted_dimensions else "D"
        
        # Secondary style only if it's close to primary (within 15 points)
        secondary_style = None
        if len(sorted_dimensions) > 1:
            if sorted_dimensions[1][1] >= (sorted_dimensions[0][1] - 15):
                secondary_style = sorted_dimensions[1][0]
        
        return primary_style, secondary_style
    
    @staticmethod
    def _get_interpretation(
        scores: Dict[str, float],
        primary: str,
        secondary: str = None
    ) -> str:
        """Generate detailed interpretation"""
        interpretation = []
        
        # Primary style
        primary_info = DISCScorer.STYLES.get(primary, {})
        interpretation.append(f"Primary Style: {primary} - {primary_info.get('name')}")
        interpretation.append(f"{primary_info.get('description')}\n")
        
        # Secondary style if exists
        if secondary:
            secondary_info = DISCScorer.STYLES.get(secondary, {})
            combination_key = f"{primary}{secondary}"
            combination_desc = DISCScorer.STYLE_COMBINATIONS.get(
                combination_key,
                f"Blend of {primary} and {secondary} traits"
            )
            interpretation.append(f"Secondary Style: {secondary} - {secondary_info.get('name')}")
            interpretation.append(f"Style Combination: {combination_desc}\n")
        
        # Detailed scores
        interpretation.append("Dimension Scores:")
        for dimension, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            dim_info = DISCScorer.STYLES.get(dimension, {})
            level = "High" if score >= 60 else "Moderate" if score >= 40 else "Low"
            interpretation.append(f"- {dimension} ({dim_info.get('name')}): {score:.1f}/100 ({level})")
        
        return "\n".join(interpretation)
    
    @staticmethod
    def _get_behavioral_insights(primary: str, secondary: str = None) -> Dict[str, List[str]]:
        """Get behavioral insights for the style"""
        primary_info = DISCScorer.STYLES.get(primary, {})
        
        insights = {
            "strengths": primary_info.get("strengths", []),
            "challenges": primary_info.get("challenges", []),
            "motivators": primary_info.get("motivators", []),
            "communication_style": DISCScorer._get_communication_style(primary),
            "ideal_work_environment": DISCScorer._get_ideal_environment(primary),
            "leadership_style": DISCScorer._get_leadership_style(primary)
        }
        
        # Add secondary influences
        if secondary:
            secondary_info = DISCScorer.STYLES.get(secondary, {})
            insights["secondary_strengths"] = secondary_info.get("strengths", [])[:2]
        
        return insights
    
    @staticmethod
    def _get_communication_style(style: str) -> List[str]:
        """Get communication preferences"""
        styles = {
            "D": ["Direct and to the point", "Prefers facts over feelings", "Wants bottom-line information"],
            "I": ["Enthusiastic and expressive", "Enjoys storytelling", "Prefers face-to-face interaction"],
            "S": ["Patient and supportive", "Good listener", "Prefers calm, non-confrontational dialogue"],
            "C": ["Precise and detailed", "Prefers written communication", "Wants data and evidence"]
        }
        return styles.get(style, [])
    
    @staticmethod
    def _get_ideal_environment(style: str) -> List[str]:
        """Get ideal work environment characteristics"""
        environments = {
            "D": ["Fast-paced", "Challenging", "Results-oriented", "Autonomous"],
            "I": ["Collaborative", "Dynamic", "Social", "Creative"],
            "S": ["Stable", "Team-oriented", "Predictable", "Supportive"],
            "C": ["Structured", "Quality-focused", "Detail-oriented", "Analytical"]
        }
        return environments.get(style, [])
    
    @staticmethod
    def _get_leadership_style(style: str) -> List[str]:
        """Get leadership characteristics"""
        styles = {
            "D": ["Decisive leader", "Takes charge quickly", "Focuses on results"],
            "I": ["Inspirational leader", "Motivates through enthusiasm", "Builds team morale"],
            "S": ["Supportive leader", "Develops team members", "Creates stability"],
            "C": ["Expert leader", "Maintains high standards", "Leads through expertise"]
        }
        return styles.get(style, [])
    
    @staticmethod
    def create_default_config(assessment_id: int, question_mapping: Dict[str, List[int]]) -> Dict[str, Any]:
        """
        Create default DISC scoring configuration
        
        Args:
            assessment_id: Assessment ID
            question_mapping: Dict mapping dimensions to question IDs
                Example: {
                    "D": [1, 5, 9, 13, 17, 21],
                    "I": [2, 6, 10, 14, 18, 22],
                    "S": [3, 7, 11, 15, 19, 23],
                    "C": [4, 8, 12, 16, 20, 24]
                }
        """
        return {
            "algorithm": "disc",
            "dimensions": question_mapping,
            "interpretation_rules": {
                "high_threshold": 60,
                "moderate_threshold": 40,
                "secondary_threshold": 15  # How close secondary must be to primary
            }
        }

        