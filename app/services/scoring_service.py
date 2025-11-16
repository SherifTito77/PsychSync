# app/services/scoring_service.py
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.assessment import AssessmentResponse
from app.db.models.scoring import AssessmentScoringConfig, ScoringAlgorithm
from app.db.models.user import User
from app.services.scoring.mbti_scorer import MBTIScorer
from app.services.scoring.big_five_scorer import BigFiveScorer
from app.services.scoring.disc_scorer import DISCScorer


class ScoringService:
    """Unified scoring service that routes to appropriate algorithm"""
    
    @staticmethod
    def calculate_score(
        db: Session,
        response: AssessmentResponse
    ) -> Dict[str, Any]:
        """
        Calculate score using configured algorithm
        
        Args:
            db: Database session
            response: AssessmentResponse object
            
        Returns:
            Dictionary with scores and interpretation
        """
        # Get scoring configuration for assessment
        config = result = await db.execute(query)
        return result.scalars().all()
        
        if not config:
            # Fall back to generic scoring
            return ScoringService._generic_scoring(response)
        
        # Route to appropriate scorer
        algorithm = config.algorithm
        
        if algorithm == "mbti":
            return MBTIScorer.calculate_scores(response, config)
        elif algorithm == "big_five":
            return BigFiveScorer.calculate_scores(response, config)
        elif algorithm == "disc":
            return DISCScorer.calculate_scores(response, config)
        elif algorithm == "generic":
            return ScoringService._generic_scoring(response)
        else:
            raise ValueError(f"Unknown scoring algorithm: {algorithm}")
    
    @staticmethod
    def _generic_scoring(response: AssessmentResponse) -> Dict[str, Any]:
        """Generic scoring for assessments without specific algorithm"""
        # Implementation from previous generic scorer
        responses = response.responses
        
        total_score = 0
        max_score = 0
        
        for q_id, answer in responses.items():
            if answer is not None:
                if isinstance(answer, bool):
                    value = 1 if answer else 0
                    max_val = 1
                elif isinstance(answer, (int, float)):
                    value = float(answer)
                    max_val = 5  # Assuming 1-5 scale
                else:
                    continue
                
                total_score += value
                max_score += max_val
        
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            "algorithm": "generic",
            "total_score": round(total_score, 2),
            "max_possible_score": round(max_score, 2),
            "percentage_score": round(percentage, 2),
            "interpretation": ScoringService._get_generic_interpretation(percentage)
        }
    
    @staticmethod
    def get_scoring_config(
        db: Session,
        assessment_id: int
    ) -> Optional[AssessmentScoringConfig]:
        """Get scoring configuration for an assessment"""
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    def get_scoring_config_by_id(
        db: Session,
        config_id: int
    ) -> Optional[AssessmentScoringConfig]:
        """Get scoring configuration by ID"""
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    def _get_generic_interpretation(percentage: float) -> str:
        """Generate interpretation for generic scoring"""
        if percentage >= 80:
            return "High score range - Strong performance across assessment areas"
        elif percentage >= 60:
            return "Above average range - Good performance in most areas"
        elif percentage >= 40:
            return "Average range - Typical performance level"
        elif percentage >= 20:
            return "Below average range - Consider areas for development"
        else:
            return "Low score range - Significant opportunity for growth"
    
    @staticmethod
    def create_scoring_config(
        db: Session,
        assessment_id: int,
        algorithm: str,
        config_data: Dict[str, Any]
    ) -> AssessmentScoringConfig:
        """Create scoring configuration for an assessment"""
        config = AssessmentScoringConfig(
            assessment_id=assessment_id,
            algorithm=algorithm,
            config=config_data
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config
    
    @staticmethod
    def update_scoring_config(
        db: Session,
        config_id: int,
        config_data: Dict[str, Any]
    ) -> AssessmentScoringConfig:
        """Update existing scoring configuration"""
        config = result = await db.execute(query)
        return result.scalars().all()
        
        if not config:
            raise ValueError("Scoring configuration not found")
        
        config.config = config_data
        await db.commit()
        await db.refresh(config)
        return config

    # =============================================================================
    # PSYCHOLOGICAL ASSESSMENT SCORING METHODS
    # =============================================================================

    @staticmethod
    async def calculate_psychological_score(
        db: AsyncSession,
        assessment_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive psychological wellness score
        """
        # Placeholder implementation for psychological scoring
        return {
            "user_id": user_id,
            "assessment_id": assessment_id,
            "overall_score": 78.5,
            "category_scores": {
                "cognitive": 82.0,
                "emotional": 75.0,
                "social": 80.0,
                "behavioral": 76.0,
                "professional": 79.0,
                "physical": 74.0
            },
            "insights": [
                "Strong analytical thinking demonstrated",
                "Consider stress management techniques",
                "Excellent team collaboration patterns"
            ],
            "recommendations": [
                "Practice mindfulness exercises",
                "Schedule regular breaks during work",
                "Continue developing leadership skills"
            ],
            "assessment_date": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
                    