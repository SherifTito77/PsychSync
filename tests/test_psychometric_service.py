# ============================================================================
# FILE 16: tests/test_psychometric_service.py
# Tests for psychometric service
# ============================================================================

import pytest
from app.services.psychometric_service import PsychometricService
from datetime import datetime

@pytest.fixture
def psychometric_service():
    return PsychometricService()

@pytest.mark.asyncio
async def test_analyze_session(psychometric_service):
    """Test session analysis"""
    session_text = """
    Client expressed feeling much better this week. 
    Reported improved sleep and reduced anxiety.
    Talked about positive interactions with family.
    """
    
    result = await psychometric_service.analyze_client_session(
        session_text=session_text,
        client_id="test_client_123",
        session_id="session_456",
        session_date=datetime.now()
    )
    
    assert "sentiment_analysis" in result
    assert "emotion_analysis" in result
    assert "key_insights" in result
    assert result["client_id"] == "test_client_123"

@pytest.mark.asyncio
async def test_progress_report(psychometric_service):
    """Test progress report generation"""
    # Mock session analyses
    session_analyses = [
        {
            "session_date": (datetime.now() - timedelta(days=i)).isoformat(),
            "sentiment_analysis": {"overall_score": 0.5 + i*0.1},
            "emotion_analysis": {"dominant_emotion": "joy"}
        }
        for i in range(5)
    ]
    
    result = await psychometric_service.generate_client_progress_report(
        client_id="test_client",
        session_analyses=session_analyses,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    
    assert "trend_analysis" in result
    assert "progress_level" in result
    assert "recommendations" in result