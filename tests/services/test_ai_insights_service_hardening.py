import os
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai_insights_service import AIInsightsService


@pytest.mark.asyncio
async def test_generate_team_insights_fallback_no_key():
    # Test that it returns rule-based insights when no key is provided
    with patch.dict(os.environ, {}, clear=True):
        team_data = {"team_id": 1, "openness": {"avg": 3.0}}
        insights = await AIInsightsService.generate_team_insights(
            team_data, use_cache=False
        )
        assert len(insights) >= 3


@pytest.mark.asyncio
async def test_generate_team_insights_invalid_json():
    # Test fallback to rule-based on invalid JSON from AI
    with patch(
        "app.services.ai_insights_service.AIInsightsService._generate_with_openai",
        new_callable=AsyncMock,
    ) as mock_openai:
        mock_openai.return_value = None  # Explicitly trigger fallback

        team_data = {"team_id": 1, "openness": {"avg": 3.0}}
        insights = await AIInsightsService.generate_team_insights(
            team_data, use_cache=False
        )
        assert len(insights) >= 3


@pytest.mark.asyncio
async def test_generate_team_insights_api_failure():
    # Mock OpenAI client to fail
    with patch("openai.AsyncOpenAI") as mock_openai_client:
        mock_openai_client.return_value.chat.completions.create = AsyncMock(
            side_effect=Exception("API failure")
        )

        team_data = {"team_id": 1, "openness": {"avg": 3.0}}
        # We need the API key for _generate_with_openai to proceed to the API call
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
            insights = await AIInsightsService.generate_team_insights(
                team_data, use_cache=False
            )
            # The API call will fail, but the service should catch it and return rule-based insights
            assert len(insights) >= 3
