# app/api/v1/endpoints/scoring.py
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.assessment_service as AssessmentService
from app.api.deps import get_current_active_user, get_db
from app.api.v1.deps import get_current_user
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.user import User
from app.services.scoring_service import ScoringService

router = APIRouter()


class ScoringConfigCreate(BaseModel):
    """Scoring configuration creation schema"""

    algorithm: str
    config: Dict[str, Any]


class ScoringConfigUpdate(BaseModel):
    """Scoring configuration update schema"""

    config: Dict[str, Any]


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post(
    "/assessments/{assessment_id}/scoring-config",
    dependencies=[Depends(get_current_user)],
)
def create_scoring_config(
    assessment_id: int,
    config_data: ScoringConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create scoring configuration for an assessment.
    Only assessment creator can configure scoring.
    """
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    if assessment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assessment creator can configure scoring",
        )

    # Check if config already exists
    existing = ScoringService.get_scoring_config(db, assessment_id)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scoring configuration already exists. Use update endpoint.",
        )

    # Validate algorithm
    valid_algorithms = ["mbti", "big_five", "disc", "generic"]
    if config_data.algorithm not in valid_algorithms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid algorithm. Must be one of: {valid_algorithms}",
        )

    config = ScoringService.create_scoring_config(
        db,
        assessment_id=assessment_id,
        algorithm=config_data.algorithm,
        config_data=config_data.config,
    )

    return {
        "id": config.id,
        "assessment_id": config.assessment_id,
        "algorithm": config.algorithm,
        "config": config.config,
    }


@router.get(
    "/assessments/{assessment_id}/scoring-config",
    dependencies=[Depends(get_current_user)],
)
def get_scoring_config(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get scoring configuration for an assessment"""
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    config = ScoringService.get_scoring_config(db, assessment_id)

    if not config:
        return {
            "algorithm": "generic",
            "message": "No specific scoring configuration. Using generic scoring.",
        }

    return {
        "id": config.id
        @ rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW),
        "assessment_id": config.assessment_id,
        "algorithm": config.algorithm,
        "config": config.config,
    }


@router.put("/scoring-configs/{config_id}", dependencies=[Depends(get_current_user)])
def update_scoring_config(
    config_id: int,
    config_update: ScoringConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update scoring configuration"""
    config = ScoringService.get_scoring_config_by_id(db, config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scoring configuration not found",
        )

    assessment = AssessmentService.get_by_id(db, assessment_id=config.assessment_id)

    if assessment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assessment creator can update scoring",
        )

    updated_config = ScoringService.update_scoring_config(
        db, config_id=config_id, config_data=config_update.config
    )

    return {
        "id": updated_config.id,
        "assessment_id": updated_config.assessment_id,
        "algorithm": updated_config.algorithm,
        "config": updated_config.config,
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
                "J-P": [4, 8, 12, 16, 20, 24],
            },
            "reverse_scored": {
                "E-I": [5, 13],
                "S-N": [6, 14],
                "T-F": [],
                "J-P": [8, 16],
            },
        },
        "instructions": "Map question IDs to each MBTI dimension. Include reverse-scored questions.",
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
                "neuroticism": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
            },
            "reverse_scored": {
                "openness": [6, 16, 26],
                "conscientiousness": [7, 17, 27],
                "extraversion": [8, 18, 28],
                "agreeableness": [9, 19, 29],
                "neuroticism": [],
            },
        },
        "instructions": "Map question IDs to each Big Five factor. Typically 8-10 questions per factor.",
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
                "C": [4, 8, 12, 16, 20, 24],
            }
        },
        "instructions": "Map question IDs to each DISC dimension. Typically 6-8 questions per dimension.",
    }


@router.post("/submit")
async def submit_assessment(assessment_data: dict):
    """
    Submit assessment responses for scoring

    Accepts assessment responses and returns processed results using appropriate scoring algorithm
    """
    try:
        assessment_id = assessment_data.get("assessment_id")
        assessment_type = assessment_data.get("assessment_type")
        responses = assessment_data.get("responses", {})
        raw_type = assessment_data.get("raw_type")

        if not assessment_type:
            raise HTTPException(status_code=400, detail="assessment_type is required")

        if assessment_type == "mbti":
            # Simple MBTI scoring without complex dependencies
            dimensions = {
                "E-I": {"E": 0, "I": 0},
                "S-N": {"S": 0, "N": 0},
                "T-F": {"T": 0, "F": 0},
                "J-P": {"J": 0, "P": 0},
            }

            # Count responses for each dimension
            for question_id, answer in responses.items():
                if answer in dimensions.get("E-I", {}):
                    dimensions["E-I"][answer] += 1
                elif answer in dimensions.get("S-N", {}):
                    dimensions["S-N"][answer] += 1
                elif answer in dimensions.get("T-F", {}):
                    dimensions["T-F"][answer] += 1
                elif answer in dimensions.get("J-P", {}):
                    dimensions["J-P"][answer] += 1

            # Calculate MBTI type
            calculated_type = [
                "E" if dimensions["E-I"]["E"] > dimensions["E-I"]["I"] else "I",
                "S" if dimensions["S-N"]["S"] > dimensions["S-N"]["N"] else "N",
                "T" if dimensions["T-F"]["T"] > dimensions["T-F"]["F"] else "F",
                "J" if dimensions["J-P"]["J"] > dimensions["J-P"]["P"] else "P",
            ].join("")

            # Use the calculated type or provided raw_type
            final_type = raw_type or calculated_type

            # Calculate confidence based on consistency
            total_questions = len(responses)
            avg_consistency = (
                sum(
                    [
                        (
                            max(dimensions["E-I"].values())
                            / sum(dimensions["E-I"].values())
                            if sum(dimensions["E-I"].values()) > 0
                            else 0
                        ),
                        (
                            max(dimensions["S-N"].values())
                            / sum(dimensions["S-N"].values())
                            if sum(dimensions["S-N"].values()) > 0
                            else 0
                        ),
                        (
                            max(dimensions["T-F"].values())
                            / sum(dimensions["T-F"].values())
                            if sum(dimensions["T-F"].values()) > 0
                            else 0
                        ),
                        (
                            max(dimensions["J-P"].values())
                            / sum(dimensions["J-P"].values())
                            if sum(dimensions["J-P"].values()) > 0
                            else 0
                        ),
                    ]
                )
                / 4
            )

            # MBTI type descriptions
            mbti_descriptions = {
                "INTJ": "The Architect - Imaginative and strategic thinkers, with a plan for everything.",
                "INTP": "The Thinker - Innovative inventors with an unquenchable thirst for knowledge.",
                "ENTJ": "The Commander - Bold, imaginative and strong-willed leaders.",
                "ENTP": "The Debater - Smart and curious thinkers who cannot resist an intellectual challenge.",
                "INFJ": "The Advocate - Quiet and mystical, yet very inspiring and tireless idealists.",
                "INFP": "The Mediator - Poetic, kind and altruistic people, always eager to help a good cause.",
                "ENFJ": "The Protagonist - Charismatic and inspiring leaders, able to mesmerize their listeners.",
                "ENFP": "The Campaigner - Enthusiastic, creative and sociable free spirits.",
                "ISTJ": "The Logistician - Practical and fact-oriented individuals, reliable and dutiful.",
                "ISFJ": "The Defender - Very dedicated and warm protectors, always ready to defend loved ones.",
                "ESTJ": "The Executive - Excellent administrators, unsurpassed at managing things or people.",
                "ESFJ": "The Consul - Extraordinarily caring, social and popular people, always eager to help.",
                "ISTP": "The Virtuoso - Bold and practical experimenters, masters of all kinds of tools.",
                "ISFP": "The Adventurer - Flexible and charming artists, always ready to explore.",
                "ESTP": "The Entrepreneur - Smart, energetic and very perceptive people, who truly enjoy living on the edge.",
                "ESFP": "The Entertainer - Spontaneous, energetic and enthusiastic entertainers.",
            }

            return {
                "type": final_type,
                "confidence": round(avg_consistency, 2),
                "description": mbti_descriptions.get(
                    final_type, f"Your MBTI type is {final_type}"
                ),
                "dimensions": {
                    "extraversion": (
                        avg_consistency if final_type[0] == "E" else 1 - avg_consistency
                    ),
                    "intuition": (
                        avg_consistency if final_type[1] == "N" else 1 - avg_consistency
                    ),
                    "thinking": (
                        avg_consistency if final_type[2] == "T" else 1 - avg_consistency
                    ),
                    "judging": (
                        avg_consistency if final_type[3] == "J" else 1 - avg_consistency
                    ),
                },
                "preferences": [
                    final_type[0] + "x" + final_type[1],
                    final_type[0] + "x" + final_type[2],
                    final_type[0] + "x" + final_type[3],
                    final_type[1] + "x" + final_type[2],
                    final_type[1] + "x" + final_type[3],
                    final_type[2] + "x" + final_type[3],
                ],
                "strengths": [
                    (
                        "Strategic thinking"
                        if final_type[0] in ["N", "T"]
                        else "Practical focus"
                    ),
                    "Decision making" if final_type[2] == "T" else "People orientation",
                    "Planning" if final_type[3] == "J" else "Adaptability",
                    "Social interaction" if final_type[0] == "E" else "Deep thinking",
                ],
                "blind_spots": [
                    (
                        "May overlook practical details"
                        if final_type[0] == "N"
                        else "May miss broader implications"
                    ),
                    (
                        "May seem insensitive"
                        if final_type[2] == "T"
                        else "May struggle with difficult decisions"
                    ),
                    (
                        "May appear rigid"
                        if final_type[3] == "J"
                        else "May struggle with structure"
                    ),
                    (
                        "May need alone time"
                        if final_type[0] == "I"
                        else "May struggle with solitude"
                    ),
                ],
                "submitted_at": "2024-12-02T00:00:00Z",
                "assessment_id": assessment_id,
                "scoring_details": {
                    "algorithm": "mbti",
                    "total_questions": total_questions,
                    "dimension_scores": {
                        "E-I": dimensions["E-I"],
                        "S-N": dimensions["S-N"],
                        "T-F": dimensions["T-F"],
                        "J-P": dimensions["J-P"],
                    },
                },
            }

        else:
            # Fallback for other assessment types
            return {
                "type": raw_type or "UNKNOWN",
                "confidence": 0.7,
                "description": f"Assessment completed for {assessment_type}",
                "submitted_at": "2024-12-02T00:00:00Z",
                "assessment_id": assessment_id,
                "responses_count": len(responses),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}") from e


def get_mbti_dimension_from_response(response_value: str) -> str:
    """Determine MBTI dimension from response value"""
    if response_value in ["E", "I"]:
        return "E-I"
    elif response_value in ["S", "N"]:
        return "S-N"
    elif response_value in ["T", "F"]:
        return "T-F"
    elif response_value in ["J", "P"]:
        return "J-P"
    return "E-I"  # Default fallback
