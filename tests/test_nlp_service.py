# ============================================================================
# FILE 15: tests/test_nlp_service.py
# Tests for NLP service
# ============================================================================

import pytest
from app.services.nlp_service import NLPService

@pytest.fixture
def nlp_service():
    return NLPService()

def test_analyze_text_basic(nlp_service):
    """Test basic text analysis"""
    text = "I am very happy and excited about this opportunity!"
    
    result = nlp_service.analyze_text(text)
    
    assert "sentiment" in result
    assert "emotions" in result
    assert result["sentiment"]["label"] in ["POSITIVE", "NEGATIVE"]
    assert result["sentiment"]["confidence"] > 0

def test_analyze_text_empty(nlp_service):
    """Test with empty text"""
    result = nlp_service.analyze_text("")
    
    assert result["sentiment"]["overall_score"] == 0.0

def test_sentiment_detection(nlp_service):
    """Test sentiment detection accuracy"""
    positive_text = "This is absolutely wonderful and amazing!"
    negative_text = "This is terrible and awful, I hate it."
    
    pos_result = nlp_service.analyze_text(positive_text)
    neg_result = nlp_service.analyze_text(negative_text)
    
    assert pos_result["sentiment"]["overall_score"] > 0
    assert neg_result["sentiment"]["overall_score"] < 0

def test_emotion_detection(nlp_service):
    """Test emotion detection"""
    text = "I am feeling very anxious and worried about tomorrow."
    
    result = nlp_service.analyze_text(text)
    
    assert "emotions" in result
    assert "dominant_emotion" in result["emotions"]
    # Should detect anxiety/fear-related emotions

def test_linguistic_features(nlp_service):
    """Test linguistic feature extraction"""
    text = "The quick brown fox jumps over the lazy dog. This is a simple test sentence."
    
    result = nlp_service.analyze_text(text)
    
    features = result["linguistic_features"]
    assert features["sentence_count"] == 2
    assert features["noun_count"] > 0
    assert features["verb_count"] > 0

def test_trend_analysis(nlp_service):
    """Test sentiment trend analysis"""
    from datetime import datetime, timedelta
    
    texts = [
        "Feeling okay today",
        "Had a great session!",
        "Things are improving",
        "Very positive progress"
    ]
    timestamps = [datetime.now() - timedelta(days=i) for i in range(4)]
    
    result = nlp_service.analyze_trend(texts, timestamps)
    
    assert "trend" in result
    assert result["trend"]["direction"] in ["improving", "declining", "stable"]

