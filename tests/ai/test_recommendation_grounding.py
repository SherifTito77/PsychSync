import pytest

from app.services.ai_insights_service import AIInsightsService


@pytest.mark.recommendation
@pytest.mark.asyncio
async def test_recommendation_grounding_present():
    team_data = {
        "team_id": 1,
        "team_size": 5,
        "openness": {"avg": 4.5},
        "conscientiousness": {"avg": 2.0},
        "extraversion": {"avg": 3.0},
        "agreeableness": {"avg": 3.0},
        "neuroticism": {"avg": 3.0},
        "diversity_score": 0.2,
        "internal_compatibility": 0.5,
        "strengths": ["Innovation"],
        "gaps": ["Organization"],
    }
    insights = await AIInsightsService.generate_team_insights(
        team_data, use_cache=False
    )
    for insight in insights:
        assert "grounding" in insight
        assert all(
            k in insight["grounding"]
            for k in ["framework", "dimension", "score", "threshold", "confidence"]
        )
