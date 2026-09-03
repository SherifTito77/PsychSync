"""
Test Assessment Endpoints
Endpoints for testing assessment submission functionality
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import get_current_active_user, get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["test-assessment"])


class BigFiveTestSubmitRequest(BaseModel):
    """Request model for Big Five test submission"""

    assessment_type: str
    responses: dict[str, Any]
    raw_type: str | None = None


@rate_limit(limit=20, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post(
    "/big-five-test-submit",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def test_submit_big_five(
    request: BigFiveTestSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Test endpoint for submitting Big Five assessment responses.
    Returns mock results for testing purposes.
    """
    try:
        # Mock scoring - calculate trait scores from responses
        # This is a simplified implementation for testing
        # Real scoring would use the AI processors
        trait_scores = {
            "Openness": 3.5,  # Medium-High
            "Conscientiousness": 3.8,  # High
            "Extraversion": 3.2,  # Medium-High
            "Agreeableness": 4.1,  # High
            "Neuroticism": 2.5,  # Low-Medium
        }

        # Determine levels based on scores (1-5 scale)
        descriptions = {
            "Openness": {
                "level": (
                    "High"
                    if trait_scores["Openness"] > 3.5
                    else "Moderate" if trait_scores["Openness"] > 2.5 else "Low"
                ),
                "description": (
                    "You enjoy creative pursuits, artistic expression, and intellectual exploration"
                    if trait_scores["Openness"] > 3.5
                    else (
                        "You balance practical thinking with creative exploration when needed"
                        if trait_scores["Openness"] > 2.5
                        else "You likely prefer practical, down-to-earth approaches to problem-solving"
                    )
                ),
            },
            "Conscientiousness": {
                "level": (
                    "High"
                    if trait_scores["Conscientiousness"] > 3.5
                    else (
                        "Moderate" if trait_scores["Conscientiousness"] > 2.5 else "Low"
                    )
                ),
                "description": (
                    "You excel at planning, organizing, and following through on commitments"
                    if trait_scores["Conscientiousness"] > 3.5
                    else (
                        "You balance spontaneity and adaptability over strict planning"
                        if trait_scores["Conscientiousness"] > 2.5
                        else "You likely prefer spontaneity and adaptability over strict planning"
                    )
                ),
            },
            "Extraversion": {
                "level": (
                    "High"
                    if trait_scores["Extraversion"] > 3.5
                    else "Moderate" if trait_scores["Extraversion"] > 2.5 else "Low"
                ),
                "description": (
                    "You gain energy from social interaction and external stimulation"
                    if trait_scores["Extraversion"] > 3.5
                    else (
                        "You balance social time with adequate rest and reflection"
                        if trait_scores["Extraversion"] > 2.5
                        else "You likely gain energy from solitude and quiet reflection"
                    )
                ),
            },
            "Agreeableness": {
                "level": (
                    "High"
                    if trait_scores["Agreeableness"] > 3.5
                    else "Moderate" if trait_scores["Agreeableness"] > 2.5 else "Low"
                ),
                "description": (
                    "You prioritize cooperation, harmony, and helping others"
                    if trait_scores["Agreeableness"] > 3.5
                    else (
                        "You balance directness, competition, and objective decision-making"
                        if trait_scores["Agreeableness"] > 2.5
                        else "You likely value directness, competition, and objective decision-making"
                    )
                ),
            },
            "Neuroticism": {
                "level": "Low" if trait_scores["Neuroticism"] < 2.5 else "Moderate",
                "description": (
                    "You remain calm and composed under pressure"
                    if trait_scores["Neuroticism"] < 2.5
                    else "You may experience emotions more intensely and be more sensitive to stress"
                ),
            },
        }

        # Determine personality type based on scores
        personality_type = "Balanced"
        if trait_scores["Extraversion"] > 3.0 and trait_scores["Openness"] > 3.5:
            personality_type = "Creative Explorer"
        elif (
            trait_scores["Conscientiousness"] > 3.5
            and trait_scores["Agreeableness"] > 3.5
        ):
            personality_type = "Organized Supporter"
        elif trait_scores["Openness"] < 2.5 and trait_scores["Conscientiousness"] > 3.5:
            personality_type = "Practical Achiever"

        result = {
            "success": True,
            "result": {
                "personality_type": personality_type,
                "scores": trait_scores,
                "descriptions": descriptions,
                "summary": f"Your Big Five results indicate you're a {personality_type}. You answered {len(request.responses)} questions across {len(request.responses)} questions.",
                "responses_count": len(request.responses),
                "submitted_at": datetime.utcnow().isoformat(),
            },
        }

        logger.info(f"Big Five assessment submitted by user {current_user.id}")
        return result

    except Exception as e:
        logger.error(f"Error processing Big Five assessment: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process assessment"
        ) from e
