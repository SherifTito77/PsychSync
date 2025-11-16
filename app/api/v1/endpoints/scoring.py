# app/api/v1/endpoints/scoring.py
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.db.models.assessment import Assessment
from app.db.models.scoring import AssessmentScoringConfig
import app.services.assessment_service as AssessmentService
from app.services.scoring_service import ScoringService
from app.services.scoring.mbti_scorer import MBTIScorer
from app.services.scoring.big_five_scorer import BigFiveScorer
from app.services.scoring.disc_scorer import DISCScorer
from pydantic import BaseModel

router = APIRouter()


class ScoringConfigCreate(BaseModel):
    """Scoring configuration creation schema"""
    algorithm: str
    config: Dict[str, Any]


class ScoringConfigUpdate(BaseModel):
    """Scoring configuration update schema"""
    config: Dict[str, Any]


@router.post("/assessments/{assessment_id}/scoring-config")
def create_scoring_config(
    assessment_id: int,
    config_data: ScoringConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create scoring configuration for an assessment.
    Only assessment creator can configure scoring.
    """
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    if assessment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assessment creator can configure scoring"
        )
    
    # Check if config already exists
    existing = ScoringService.get_scoring_config(db, assessment_id)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scoring configuration already exists. Use update endpoint."
        )
    
    # Validate algorithm
    valid_algorithms = ["mbti", "big_five", "disc", "generic"]
    if config_data.algorithm not in valid_algorithms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid algorithm. Must be one of: {valid_algorithms}"
        )
    
    config = ScoringService.create_scoring_config(
        db,
        assessment_id=assessment_id,
        algorithm=config_data.algorithm,
        config_data=config_data.config
    )
    
    return {
        "id": config.id,
        "assessment_id": config.assessment_id,
        "algorithm": config.algorithm,
        "config": config.config
    }


@router.get("/assessments/{assessment_id}/scoring-config")
def get_scoring_config(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get scoring configuration for an assessment"""
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    config = ScoringService.get_scoring_config(db, assessment_id)
    
    if not config:
        return {
            "algorithm": "generic",
            "message": "No specific scoring configuration. Using generic scoring."
        }
    
    return {
        "id": config.id,
        "assessment_id": config.assessment_id,
        "algorithm": config.algorithm,
        "config": config.config
    }


@router.put("/scoring-configs/{config_id}")
def update_scoring_config(
    config_id: int,
    config_update: ScoringConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update scoring configuration"""
    config = ScoringService.get_scoring_config_by_id(db, config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring configuration not found"
        )
    
    assessment = AssessmentService.get_by_id(db, assessment_id=config.assessment_id)
    
    if assessment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assessment creator can update scoring"
        )
    
    updated_config = ScoringService.update_scoring_config(
        db,
        config_id=config_id,
        config_data=config_update.config
    )
    
    return {
        "id": updated_config.id,
        "assessment_id": updated_config.assessment_id,
        "algorithm": updated_config.algorithm,
        "config": updated_config.config
    }


@router.get("/scoring-helpers/mbti-template")
def get_mbti_template():
    """Get template for MBTI scoring configuration"""
    return {
        "algorithm": "mbti",
        "description": "Myers-Briggs Type Indicator configuration template",
        "example_config": {
            "dimensions": {
                "E-I": [1, 5, 9, 13, 17, 21],
                "S-N": [2, 6, 10, 14, 18, 22],
                "T-F": [3, 7, 11, 15, 19, 23],
                "J-P": [4, 8, 12, 16, 20, 24]
            },
            "reverse_scored": {
                "E-I": [5, 13],
                "S-N": [6, 14],
                "T-F": [],
                "J-P": [8, 16]
            }
        },
        "instructions": "Map question IDs to each MBTI dimension. Include reverse-scored questions."
    }


@router.get("/scoring-helpers/big-five-template")
def get_big_five_template():
    """Get template for Big Five scoring configuration"""
    return {
        "algorithm": "big_five",
        "description": "Big Five (OCEAN) personality traits configuration template",
        "example_config": {
            "factors": {
                "openness": [1, 6, 11, 16, 21, 26, 31, 36, 41, 46],
                "conscientiousness": [2, 7, 12, 17, 22, 27, 32, 37, 42, 47],
                "extraversion": [3, 8, 13, 18, 23, 28, 33, 38, 43, 48],
                "agreeableness": [4, 9, 14, 19, 24, 29, 34, 39, 44, 49],
                "neuroticism": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
            },
            "reverse_scored": {
                "openness": [6, 16, 26],
                "conscientiousness": [7, 17, 27],
                "extraversion": [8, 18, 28],
                "agreeableness": [9, 19, 29],
                "neuroticism": []
            }
        },
        "instructions": "Map question IDs to each Big Five factor. Typically 8-10 questions per factor."
    }


@router.get("/scoring-helpers/disc-template")
def get_disc_template():
    """Get template for DISC scoring configuration"""
    return {
        "algorithm": "disc",
        "description": "DISC behavioral assessment configuration template",
        "example_config": {
            "dimensions": {
                "D": [1, 5, 9, 13, 17, 21],
                "I": [2, 6, 10, 14, 18, 22],
                "S": [3, 7, 11, 15, 19, 23],
                "C": [4, 8, 12, 16, 20, 24]
            }
        },
        "instructions": "Map question IDs to each DISC dimension. Typically 6-8 questions per dimension."
    }
    