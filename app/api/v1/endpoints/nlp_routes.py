# ============================================================================
# FILE 2: app/api/routes/nlp_routes.py
# FastAPI routes for NLP services
# ============================================================================

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from app.services.nlp_service import NLPService

router = APIRouter(prefix="/api/v1/nlp", tags=["NLP"])

# Pydantic models
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    include_entities: bool = Field(default=True, description="Include named entity recognition")
    
    @validator("text")
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
    return v

class TextAnalysisResponse(BaseModel):
    sentiment: dict
    emotions: dict
    linguistic_features: dict
    psycholinguistic_markers: dict
    entities: Optional[List[dict]]
    metadata: dict

class TrendAnalysisRequest(BaseModel):
    texts: List[str] = Field(..., min_items=2, max_items=50)
    timestamps: List[datetime]
    
    @validator("timestamps")
    def validate_timestamps(cls, v, values):
        if "texts" in values and len(v) != len(values["texts"]):
            raise ValueError("timestamps must match texts length")
    return v

class WordCloudRequest(BaseModel):
    text: str = Field(..., min_length=10)
    max_words: int = Field(default=100, ge=10, le=500)

class BatchAnalysisRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=50)

# Dependency
def get_nlp_service() -> NLPService:
    """Get NLP service instance"""
    return NLPService()

# Routes
@router.post("/analyze", response_model=TextAnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Analyze text for sentiment, emotions, and linguistic features
    
    - **text**: Text to analyze (1-10000 characters)
    - **include_entities**: Whether to include named entity recognition
    """
    try:
        result = nlp_service.analyze_text(request.text)
        
        if not request.include_entities:
            result.pop("entities", None)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/analyze/trend")
async def analyze_trend(
    request: TrendAnalysisRequest,
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Analyze sentiment trend across multiple texts
    
    - **texts**: List of texts (2-50 items)
    - **timestamps**: Corresponding timestamps for each text
    """
    try:
        result = nlp_service.analyze_trend(request.texts, request.timestamps)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend analysis failed: {str(e)}"
        )

@router.post("/wordcloud")
async def generate_wordcloud(
    request: WordCloudRequest,
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Generate word frequency data for wordcloud visualization
    
    - **text**: Text to process
    - **max_words**: Maximum words to return (10-500)
    """
    try:
        result = nlp_service.generate_wordcloud_data(request.text, request.max_words)
        return {"words": result, "total_unique_words": len(result)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wordcloud generation failed: {str(e)}"
        )

@router.post("/analyze/batch")
async def batch_analyze(
    request: BatchAnalysisRequest,
    nlp_service: NLPService = Depends(get_nlp_service)
):
    """
    Batch analyze multiple texts
    
    - **texts**: List of texts to analyze (1-50 items)
    """
    try:
        results = []
        for idx, text in enumerate(request.texts):
            analysis = nlp_service.analyze_text(text)
            analysis["index"] = idx
            results.append(analysis)
        
        return {
            "analyses": results,
            "count": len(results),
            "summary": {
                "avg_sentiment": sum(r["sentiment"]["overall_score"] for r in results) / len(results),
                "dominant_emotions": _get_dominant_emotions(results)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Check NLP service health"""
    try:
        nlp_service = NLPService()
        return {
            "status": "healthy",
            "models_loaded": all([
                nlp_service.nlp is not None,
                nlp_service.sentiment_analyzer is not None,
                nlp_service.emotion_classifier is not None
            ])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@router.get("/metrics")
async def get_metrics():
    """Get NLP service configuration and limits"""
    return {
        "max_text_length": 10000,
        "max_batch_size": 50,
        "max_trend_items": 50,
        "max_wordcloud_words": 500,
        "supported_languages": ["en"],
        "available_emotions": [
            "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"
        ]
    }

def _get_dominant_emotions(results: List[dict]) -> dict:
    """Get dominant emotions across all analyses"""
    emotion_counts = {}
    for result in results:
        emotion = result["emotions"]["dominant_emotion"]
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    return emotion_counts

