import pytest

from app.services.ai_insights_service import AIInsightsService


@pytest.mark.asyncio
async def test_generate_rule_based_insights_includes_grounding():
    # Mock team data
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

    insights = AIInsightsService._generate_rule_based_insights(team_data)

    assert len(insights) >= 3
    for insight in insights:
        assert "grounding" in insight
        assert "framework" in insight["grounding"]
        assert "dimension" in insight["grounding"]
        assert "score" in insight["grounding"]
        assert "threshold" in insight["grounding"]
        assert "confidence" in insight["grounding"]
