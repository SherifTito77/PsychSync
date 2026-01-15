# app/schemas/team_personality.py
"""
Schemas for Team Personality Map API
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DimensionStats(BaseModel):
    """Statistics for a single personality dimension"""
    avg: float = Field(..., description="Average score for this dimension")
    min: float = Field(..., description="Minimum score")
    max: float = Field(..., description="Maximum score")
    std_dev: float = Field(..., description="Standard deviation")
    distribution: List[float] = Field(
        ...,
        description="Distribution across quintiles [very low, low, medium, high, very high]"
    )


class TeamCompositionResponse(BaseModel):
    """Team personality composition response"""
    team_id: str = Field(..., description="Team UUID")
    team_size: int = Field(..., description="Number of team members with assessments")
    composition_type: str = Field(..., description="Overall team personality type")
    openness: Optional[DimensionStats] = Field(None, description="Openness dimension statistics")
    conscientiousness: Optional[DimensionStats] = Field(None, description="Conscientiousness dimension statistics")
    extraversion: Optional[DimensionStats] = Field(None, description="Extraversion dimension statistics")
    agreeableness: Optional[DimensionStats] = Field(None, description="Agreeableness dimension statistics")
    neuroticism: Optional[DimensionStats] = Field(None, description="Neuroticism dimension statistics")
    strengths: List[str] = Field(default_factory=list, description="Team strengths based on personality")
    gaps: List[str] = Field(default_factory=list, description="Potential areas for development")
    internal_compatibility: Optional[float] = Field(None, description="How well personalities complement each other (0-1)")
    diversity_score: Optional[float] = Field(None, description="Personality diversity score (0-1)")
    updated_at: str = Field(..., description="When this composition was last calculated")

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        json_schema_extra = {
            "example": {
                "team_id": "123e4567-e89b-12d3-a456-426614174000",
                "team_size": 10,
                "composition_type": "Creative & Social",
                "openness": {
                    "avg": 4.2,
                    "min": 3.0,
                    "max": 5.0,
                    "std_dev": 0.6,
                    "distribution": [0, 10, 20, 40, 30]
                },
                "conscientiousness": {
                    "avg": 3.8,
                    "min": 2.5,
                    "max": 4.8,
                    "std_dev": 0.7,
                    "distribution": [0, 10, 30, 40, 20]
                },
                "extraversion": {
                    "avg": 4.0,
                    "min": 2.8,
                    "max": 5.0,
                    "std_dev": 0.5,
                    "distribution": [0, 0, 20, 50, 30]
                },
                "agreeableness": {
                    "avg": 3.5,
                    "min": 2.0,
                    "max": 4.5,
                    "std_dev": 0.8,
                    "distribution": [0, 20, 30, 30, 20]
                },
                "neuroticism": {
                    "avg": 2.3,
                    "min": 1.5,
                    "max": 3.5,
                    "std_dev": 0.6,
                    "distribution": [20, 40, 30, 10, 0]
                },
                "strengths": [
                    "Creative problem-solving and innovation",
                    "Excellent communication and social engagement",
                    "Emotional stability and stress resilience"
                ],
                "gaps": [
                    "May struggle with organization and follow-through"
                ],
                "internal_compatibility": 0.85,
                "diversity_score": 0.42,
                "updated_at": "2025-01-12T10:30:00Z"
            }
        }


class TeamComparisonResponse(BaseModel):
    """Team comparison response"""
    teams: List[TeamCompositionResponse] = Field(..., description="Team composition data")
    insights: List[str] = Field(default_factory=list, description="Comparative insights")


class TeamCompositionRefreshRequest(BaseModel):
    """Request to force refresh team composition"""
    force_recalculate: bool = Field(
        default=False,
        description="If True, recalculate from scratch instead of using cached data"
    )
