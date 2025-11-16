
# ============================================================================
# FILE 8: app/api/routes/psychometrics_routes.py
# FastAPI routes for psychometric services
# ============================================================================

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from ai.psychometrics.sentiment_analysis import PsychometricSentimentAnalyzer
from ai.psychometrics.emotion_detection import EmotionDetector
from ai.psychometrics.personality_insights import PersonalityInsightEngine
from ai.psychometrics.psychometric_scorer import PsychometricScorer
from ai.pattern_recognition import PatternDetector, AnomalyDetector

router = APIRouter(prefix="/api/v1/psychometrics", tags=["Psychometrics"])

# Pydantic models
class TextSampleRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=50)
    user_id: Optional[str] = None

class EmotionHistoryRequest(BaseModel):
    emotion_history: List[Dict] = Field(..., min_items=1)
    user_id: Optional[str] = None

class ComprehensiveProfileRequest(BaseModel):
    texts: List[str] = Field(..., min_items=3, max_items=50)
    emotion_data: Optional[Dict] = None
    linguistic_data: Optional[Dict] = None
    user_id: Optional[str] = None

class AssessmentScoreRequest(BaseModel):
    assessment_type: str = Field(..., regex="^(big_five|mbti|enneagram|disc)$")
    responses: List[Dict] = Field(..., min_items=1)
    framework_config: Dict

class PatternAnalysisRequest(BaseModel):
    data: List[float] = Field(..., min_items=5)
    timestamps: List[datetime]
    user_id: Optional[str] = None

class AnomalyDetectionRequest(BaseModel):
    data_points: List[Dict] = Field(..., min_items=10)
    feature_keys: List[str]

class InterventionAnalysisRequest(BaseModel):
    pre_intervention: List[float] = Field(..., min_items=3)
    post_intervention: List[float] = Field(..., min_items=3)
    intervention_date: datetime
    intervention_type: str

# Dependencies
def get_sentiment_analyzer() -> PsychometricSentimentAnalyzer:
    return PsychometricSentimentAnalyzer()

def get_emotion_detector() -> EmotionDetector:
    return EmotionDetector()

def get_personality_engine() -> PersonalityInsightEngine:
    return PersonalityInsightEngine()

def get_psychometric_scorer() -> PsychometricScorer:
    return PsychometricScorer()

def get_pattern_detector() -> PatternDetector:
    return PatternDetector()

def get_anomaly_detector() -> AnomalyDetector:
    return AnomalyDetector()

# Routes
@router.post("/personality/from-text")
async def analyze_personality_from_text(
    request: TextSampleRequest,
    analyzer: PsychometricSentimentAnalyzer = Depends(get_sentiment_analyzer)
):
    """
    Analyze personality traits from text samples
    
    Estimates Big Five personality traits based on sentiment patterns
    in provided text samples. Requires at least 3 samples for reliable results.
    """
    try:
        result = analyzer.analyze_personality_from_text(request.texts)
        
        if request.user_id:
            result["user_id"] = request.user_id
            result["analyzed_at"] = datetime.utcnow().isoformat()
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Personality analysis failed: {str(e)}"
        )

@router.post("/emotion/analyze-state")
async def analyze_emotional_state(
    request: EmotionHistoryRequest,
    detector: EmotionDetector = Depends(get_emotion_detector)
):
    """
    Analyze emotional state from emotion history
    
    Assesses psychological states including depression risk, anxiety risk,
    and stress indicators based on emotion patterns over time.
    """
    try:
        result = detector.analyze_emotional_state(request.emotion_history)
        
        if request.user_id:
            result["user_id"] = request.user_id
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emotional state analysis failed: {str(e)}"
        )

@router.post("/profile/comprehensive")
async def generate_comprehensive_profile(
    request: ComprehensiveProfileRequest,
    sentiment_analyzer: PsychometricSentimentAnalyzer = Depends(get_sentiment_analyzer),
    emotion_detector: EmotionDetector = Depends(get_emotion_detector),
    personality_engine: PersonalityInsightEngine = Depends(get_personality_engine)
):
    """
    Generate comprehensive psychological profile
    
    Combines sentiment analysis, emotion detection, and linguistic features
    to create a holistic personality and wellbeing profile.
    """
    try:
        # Analyze sentiment
        sentiment_data = sentiment_analyzer.analyze_personality_from_text(request.texts)
        
        # Use provided emotion data or empty
        emotion_data = request.emotion_data or {}
        
        # Use provided linguistic data or empty
        linguistic_data = request.linguistic_data or {}
        
        # Generate comprehensive profile
        profile = personality_engine.generate_comprehensive_profile(
            sentiment_data,
            emotion_data,
            linguistic_data
        )
        
        if request.user_id:
            profile["user_id"] = request.user_id
            profile["generated_at"] = datetime.utcnow().isoformat()
        
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile generation failed: {str(e)}"
        )

@router.post("/assessment/score")
async def score_assessment(
    request: AssessmentScoreRequest,
    scorer: PsychometricScorer = Depends(get_psychometric_scorer)
):
    """
    Score a psychometric assessment
    
    Supports: Big Five, MBTI, Enneagram, DISC
    """
    try:
        result = scorer.score_assessment(
            request.assessment_type,
            request.responses,
            request.framework_config
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment scoring failed: {str(e)}"
        )

@router.post("/patterns/detect-cycles")
async def detect_cyclical_patterns(
    request: PatternAnalysisRequest,
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    Detect cyclical patterns in behavioral data
    
    Identifies recurring cycles in mood, energy, or other behavioral metrics.
    Useful for detecting bipolar patterns or seasonal variations.
    """
    try:
        result = detector.detect_cyclical_patterns(
            request.data,
            request.timestamps
        )
        
        if request.user_id:
            result["user_id"] = request.user_id
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pattern detection failed: {str(e)}"
        )

@router.post("/patterns/analyze-trend")
async def analyze_behavioral_trend(
    request: PatternAnalysisRequest,
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    Analyze trend in behavioral data
    
    Determines if behavior is improving, declining, or stable over time.
    Useful for tracking treatment progress.
    """
    try:
        result = detector.analyze_trend(
            request.data,
            request.timestamps
        )
        
        if request.user_id:
            result["user_id"] = request.user_id
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}"
        )

@router.post("/intervention/analyze-effect")
async def analyze_intervention_effect(
    request: InterventionAnalysisRequest,
    detector: PatternDetector = Depends(get_pattern_detector)
):
    """
    Analyze effect of an intervention
    
    Compares behavioral metrics before and after an intervention
    (e.g., starting therapy, medication change) to assess effectiveness.
    """
    try:
        result = detector.detect_intervention_effect(
            request.pre_intervention,
            request.post_intervention
        )
        
        result["intervention_date"] = request.intervention_date.isoformat()
        result["intervention_type"] = request.intervention_type
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intervention analysis failed: {str(e)}"
        )

@router.post("/anomaly/detect")
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    detector: AnomalyDetector = Depends(get_anomaly_detector)
):
    """
    Detect anomalies in behavioral data
    
    Identifies unusual patterns that may indicate crisis situations,
    significant changes in condition, or data quality issues.
    """
    try:
        result = detector.detect_anomalies(
            request.data_points,
            request.feature_keys
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )

@router.post("/anomaly/detect-sudden-changes")
async def detect_sudden_changes(
    request: PatternAnalysisRequest,
    detector: AnomalyDetector = Depends(get_anomaly_detector)
):
    """
    Detect sudden changes in time-series data
    
    Identifies abrupt shifts that may require immediate attention.
    """
    try:
        result = detector.detect_sudden_changes(
            request.data,
            request.timestamps
        )
        
        if request.user_id:
            result["user_id"] = request.user_id
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change detection failed: {str(e)}"
        )

@router.get("/health")
async def psychometrics_health():
    """Check psychometrics service health"""
    try:
        # Test each service
        services = {
            "sentiment_analyzer": PsychometricSentimentAnalyzer(),
            "emotion_detector": EmotionDetector(),
            "personality_engine": PersonalityInsightEngine(),
            "psychometric_scorer": PsychometricScorer(),
            "pattern_detector": PatternDetector(),
            "anomaly_detector": AnomalyDetector()
        }
        
        return {
            "status": "healthy",
            "services": {name: "operational" for name in services.keys()},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@router.get("/supported-assessments")
async def get_supported_assessments():
    """Get list of supported assessment types and their configurations"""
    return {
        "assessments": [
            {
                "type": "big_five",
                "name": "Big Five Personality Test",
                "dimensions": 5,
                "typical_questions": 44,
                "time_estimate_minutes": 10
            },
            {
                "type": "mbti",
                "name": "Myers-Briggs Type Indicator",
                "dimensions": 4,
                "types": 16,
                "typical_questions": 60,
                "time_estimate_minutes": 15
            },
            {
                "type": "enneagram",
                "name": "Enneagram Personality Test",
                "types": 9,
                "typical_questions": 36,
                "time_estimate_minutes": 12
            },
            {
                "type": "disc",
                "name": "DISC Personality Assessment",
                "dimensions": 4,
                "typical_questions": 24,
                "time_estimate_minutes": 8
            }
        ]
    }

