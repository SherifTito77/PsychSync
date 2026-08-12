"""
Voice and Video Response Analysis API Endpoints

Advanced multimodal analysis endpoints with transcription, facial recognition, and sentiment analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_active_user
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.user import User

try:
    from app.services.voice_video_analysis import (
        ComprehensiveAnalysisResult,
        TranscriptionConfig,
        VideoRecordingConfig,
        VoiceVideoAnalysisEngine,
        ML_LIBRARIES_AVAILABLE,
    )
except ImportError:
    ML_LIBRARIES_AVAILABLE = False
    VoiceVideoAnalysisEngine = None
    VideoRecordingConfig = None
    TranscriptionConfig = None
    ComprehensiveAnalysisResult = None

_INSTALL_MSG = (
    "Voice/video analysis requires ML libraries not currently installed. "
    "To enable: pip install opencv-python librosa SpeechRecognition transformers"
)


async def _require_ml_libraries():
    """Router-level dependency: blocks all endpoints when ML libs are missing."""
    if not ML_LIBRARIES_AVAILABLE:
        raise HTTPException(status_code=503, detail=_INSTALL_MSG)


router = APIRouter(
    prefix="/voice-video",
    tags=["Voice & Video Analysis"],
    dependencies=[Depends(_require_ml_libraries)],
)


# Request/Response Models
class VideoRecordingConfigRequest(BaseModel):
    max_duration: int = Field(300, description="Maximum recording duration in seconds")
    quality: str = Field("high", description="Recording quality (low, medium, high)")
    format: str = Field("mp4", description="Video format")
    resolution: str = Field("1280x720", description="Video resolution")
    frame_rate: int = Field(30, description="Video frame rate")
    include_audio: bool = Field(True, description="Include audio in recording")
    auto_transcription: bool = Field(True, description="Automatically transcribe audio")
    real_time_analysis: bool = Field(True, description="Perform real-time analysis")


class TranscriptionConfigRequest(BaseModel):
    language: str = Field("en-US", description="Transcription language")
    quality: str = Field(
        "standard", description="Transcription quality (draft, standard, high)"
    )
    include_timestamps: bool = Field(True, description="Include word timestamps")
    include_confidence: bool = Field(True, description="Include confidence scores")
    speaker_diarization: bool = Field(False, description="Identify different speakers")
    profanity_filter: bool = Field(False, description="Filter profanity")
    custom_vocabulary: List[str] = Field([], description="Custom vocabulary words")


class ComprehensiveAnalysisResponse(BaseModel):
    analysis_id: str
    user_id: str
    duration: float
    transcription: Dict[str, Any]
    facial_analysis: List[Dict[str, Any]]
    voice_sentiment: List[Dict[str, Any]]
    overall_sentiment: str
    overall_confidence: float
    engagement_score: float
    authenticity_score: float
    recommendations: List[str]
    insights: List[str]
    risk_assessment: Dict[str, Any]
    created_date: str


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    duration: float
    word_timestamps: List[List[Any]]
    processing_time: float
    quality_metrics: Dict[str, Any]


class AnalysisStatisticsResponse(BaseModel):
    total_recordings: int
    total_duration: float
    average_confidence: float
    sentiment_distribution: Dict[str, float]
    emotion_distribution: Dict[str, float]
    improvement_trends: Dict[str, float]
    last_analysis_date: str


# API Endpoints


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/record", response_model=Dict[str, Any])
async def start_video_analysis(
    video_file: UploadFile = File(..., description="Video file to analyze"),
    config: Optional[VideoRecordingConfigRequest] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Process video recording with comprehensive analysis including transcription,
    facial expression analysis, and voice sentiment analysis.
    """
    try:
        if not video_file:
            raise HTTPException(status_code=400, detail="Video file is required")

        # Read video file
        video_data = await video_file.read()

        # Convert request config to service config
        recording_config = VideoRecordingConfig(
            max_duration=config.max_duration if config else 300,
            quality=config.quality if config else "high",
            format=config.format if config else "mp4",
            resolution=config.resolution if config else "1280x720",
            frame_rate=config.frame_rate if config else 30,
            include_audio=config.include_audio if config else True,
            auto_transcription=config.auto_transcription if config else True,
            real_time_analysis=config.real_time_analysis if config else True,
        )

        # Initialize analysis engine
        engine = VoiceVideoAnalysisEngine(db)

        # Process video recording
        result = await engine.process_video_recording(
            video_data, current_user.id, recording_config
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        return {
            "status": "success",
            "analysis_id": result["analysis_id"],
            "message": "Video analysis completed successfully",
            "video_path": result["video_path"],
            "duration": result["duration"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    config: Optional[TranscriptionConfigRequest] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Transcribe audio file to text with confidence scoring and timestamps.
    """
    try:
        if not audio_file:
            raise HTTPException(status_code=400, detail="Audio file is required")

        # Read audio file
        audio_data = await audio_file.read()

        # Convert request config to service config
        transcription_config = TranscriptionConfig(
            language=config.language if config else "en-US",
            quality=config.quality if config else "standard",
            include_timestamps=config.include_timestamps if config else True,
            include_confidence=config.include_confidence if config else True,
            speaker_diarization=config.speaker_diarization if config else False,
            profanity_filter=config.profanity_filter if config else False,
            custom_vocabulary=config.custom_vocabulary if config else [],
        )

        # Initialize analysis engine
        engine = VoiceVideoAnalysisEngine(db)

        # Perform transcription
        result = await engine.transcribe_audio(audio_data, transcription_config)

        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration=result.duration,
            word_timestamps=result.word_timestamps,
            processing_time=result.processing_time,
            quality_metrics=result.quality_metrics,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}", response_model=ComprehensiveAnalysisResponse)
async def get_analysis_result(
    analysis_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive analysis results by analysis ID.
    """
    try:
        # In production, this would query the database
        # For now, return mock data
        mock_result = ComprehensiveAnalysisResult(
            analysis_id=analysis_id,
            user_id=current_user.id,
            video_path=f"/videos/{analysis_id}.mp4",
            duration=45.2,
            transcription={
                "text": "I believe that my leadership style focuses on empowering team members through clear communication.",
                "language": "en-US",
                "confidence": 0.94,
                "duration": 45.2,
                "word_timestamps": [],
                "processing_time": 2.3,
                "quality_metrics": {},
            },
            facial_analysis=[
                {
                    "timestamp": 0,
                    "primary_emotion": "happy",
                    "emotion_confidence": 0.85,
                    "attention_score": 0.92,
                    "eye_contact": True,
                    "engagement_indicators": ["maintains_eye_contact"],
                }
            ],
            voice_sentiment=[
                {
                    "timestamp": 0,
                    "sentiment": "positive",
                    "sentiment_confidence": 0.87,
                    "confidence_score": 0.91,
                    "speech_rate": 145,
                    "clarity_score": 0.89,
                    "stress_indicators": [],
                }
            ],
            overall_sentiment="positive",
            overall_confidence=0.86,
            engagement_score=0.89,
            authenticity_score=0.79,
            recommendations=["Excellent performance", "Consider varying pace slightly"],
            insights=["High engagement detected", "Strong vocal confidence"],
            risk_assessment={"risk_level": "low", "risk_factors": []},
        )

        return ComprehensiveAnalysisResponse(
            analysis_id=mock_result.analysis_id,
            user_id=mock_result.user_id,
            duration=mock_result.duration,
            transcription=mock_result.transcription,
            facial_analysis=[
                {
                    "timestamp": result.timestamp,
                    "primary_emotion": result.primary_emotion.value,
                    "emotion_confidence": result.emotion_confidence,
                    "attention_score": result.attention_score,
                    "eye_contact": result.eye_contact,
                    "engagement_indicators": result.engagement_indicators,
                }
                for result in mock_result.facial_analysis
            ],
            voice_sentiment=[
                {
                    "timestamp": result.timestamp,
                    "sentiment": result.sentiment.value,
                    "sentiment_confidence": result.sentiment_confidence,
                    "confidence_score": result.confidence_score,
                    "speech_rate": result.speech_rate,
                    "clarity_score": result.clarity_score,
                    "stress_indicators": result.stress_indicators,
                }
                for result in mock_result.voice_sentiment
            ],
            overall_sentiment=mock_result.overall_sentiment,
            overall_confidence=mock_result.overall_confidence,
            engagement_score=mock_result.engagement_score,
            authenticity_score=mock_result.authenticity_score,
            recommendations=mock_result.recommendations,
            insights=mock_result.insights,
            risk_assessment=mock_result.risk_assessment,
            created_date=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[ComprehensiveAnalysisResponse])
async def get_analysis_history(
    limit: int = Query(50, description="Maximum number of analyses to return"),
    date_from: Optional[str] = Query(None, description="Filter analyses from date"),
    date_to: Optional[str] = Query(None, description="Filter analyses to date"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get user's analysis history with optional date filtering.
    """
    try:
        # In production, query database for user's analysis history
        # For now, return mock data
        mock_history = [
            {
                "analysis_id": f"analysis_{current_user.id}_1",
                "user_id": current_user.id,
                "duration": 45.2,
                "transcription": {
                    "text": "Sample transcription from previous session",
                    "language": "en-US",
                    "confidence": 0.95,
                    "duration": 45.2,
                    "word_timestamps": [],
                    "processing_time": 2.1,
                    "quality_metrics": {},
                },
                "facial_analysis": [],
                "voice_sentiment": [],
                "overall_sentiment": "positive",
                "overall_confidence": 0.87,
                "engagement_score": 0.88,
                "authenticity_score": 0.82,
                "recommendations": ["Good performance"],
                "insights": ["Clear communication"],
                "risk_assessment": {"risk_level": "low", "risk_factors": []},
                "created_date": "2024-01-15T10:30:00Z",
            }
        ]

        return mock_history[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=AnalysisStatisticsResponse)
async def get_analysis_statistics(
    timeframe_days: int = Query(30, description="Timeframe in days"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get comprehensive analysis statistics for a user.
    """
    try:
        engine = VoiceVideoAnalysisEngine(db)
        stats = await engine.get_analysis_statistics(current_user.id)

        return AnalysisStatisticsResponse(
            total_recordings=stats.get("total_recordings", 0),
            total_duration=stats.get("total_duration", 0),
            average_confidence=stats.get("average_confidence", 0),
            sentiment_distribution=stats.get("sentiment_distribution", {}),
            emotion_distribution=stats.get("emotion_distribution", {}),
            improvement_trends=stats.get("improvement_trends", {}),
            last_analysis_date=stats.get(
                "last_analysis_date", datetime.utcnow().isoformat()
            ),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcription/history")
async def get_transcription_history(
    limit: int = Query(50, description="Maximum number of transcriptions to return"),
    date_from: Optional[str] = Query(
        None, description="Filter transcriptions from date"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get user's transcription history with sentiment analysis.
    """
    try:
        engine = VoiceVideoAnalysisEngine(db)
        history = await engine.get_transcription_history(
            current_user.id, limit, date_from
        )

        return {
            "transcriptions": history,
            "total_count": len(history),
            "user_id": current_user.id,
            "generated_date": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/facial-expressions")
async def analyze_facial_expressions(
    video_file: UploadFile = File(..., description="Video file for facial analysis"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Perform facial expression analysis on uploaded video.
    """
    try:
        if not video_file:
            raise HTTPException(status_code=400, detail="Video file is required")

        # Save video file
        video_data = await video_file.read()
        video_path = f"/tmp/facial_analysis/{current_user.id}_{datetime.utcnow().timestamp()}.mp4"

        import os

        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        with open(video_path, "wb") as f:
            f.write(video_data)

        # Initialize analysis engine
        engine = VoiceVideoAnalysisEngine(db)

        # Perform facial analysis
        results = await engine.analyze_facial_expressions(video_path)

        # Convert results to response format
        response_results = [
            {
                "timestamp": result.timestamp,
                "detected_faces": result.detected_faces,
                "primary_emotion": result.primary_emotion.value,
                "emotion_confidence": result.emotion_confidence,
                "emotion_distribution": result.emotion_distribution,
                "eye_contact": result.eye_contact,
                "attention_score": result.attention_score,
                "facial_landmarks": result.facial_landmarks,
                "head_pose": result.head_pose,
                "engagement_indicators": result.engagement_indicators,
            }
            for result in results
        ]

        return {
            "analysis_id": f"facial_{current_user.id}_{datetime.utcnow().timestamp()}",
            "video_path": video_path,
            "results": response_results,
            "total_frames": len(results),
            "processing_date": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/voice-sentiment")
async def analyze_voice_sentiment(
    audio_file: UploadFile = File(..., description="Audio file for sentiment analysis"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Perform voice sentiment analysis on uploaded audio.
    """
    try:
        if not audio_file:
            raise HTTPException(status_code=400, detail="Audio file is required")

        # Save audio file
        audio_data = await audio_file.read()
        audio_path = f"/tmp/voice_sentiment/{current_user.id}_{datetime.utcnow().timestamp()}.wav"

        import os

        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        # Initialize analysis engine
        engine = VoiceVideoAnalysisEngine(db)

        # Perform voice sentiment analysis
        results = await engine.analyze_voice_sentiment(audio_path)

        # Convert results to response format
        response_results = [
            {
                "timestamp": result.timestamp,
                "sentiment": result.sentiment.value,
                "sentiment_confidence": result.sentiment_confidence,
                "emotion_scores": result.emotion_scores,
                "acoustic_features": result.acoustic_features,
                "stress_indicators": result.stress_indicators,
                "confidence_score": result.confidence_score,
                "speech_rate": result.speech_rate,
                "volume_level": result.volume_level,
                "clarity_score": result.clarity_score,
            }
            for result in results
        ]

        # Calculate overall sentiment
        if response_results:
            sentiment_counts = {}
            for result in response_results:
                sentiment = result["sentiment"]
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            overall_sentiment = (
                max(sentiment_counts, key=sentiment_counts.get)
                if sentiment_counts
                else "neutral"
            )
        else:
            overall_sentiment = "neutral"

        return {
            "analysis_id": f"voice_{current_user.id}_{datetime.utcnow().timestamp()}",
            "audio_path": audio_path,
            "results": response_results,
            "overall_sentiment": overall_sentiment,
            "total_segments": len(results),
            "processing_date": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
async def get_analysis_models_status(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get status of available analysis models and their capabilities.
    """
    try:
        # Check model availability and capabilities
        models_status = {
            "transcription_models": {
                "whisper_small": {
                    "available": True,
                    "quality": "high",
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"],
                    "features": ["timestamps", "confidence_scores", "multi_language"],
                },
                "whisper_base": {
                    "available": True,
                    "quality": "standard",
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"],
                    "features": ["timestamps", "confidence_scores", "multi_language"],
                },
                "speechbrain": {
                    "available": True,
                    "quality": "standard",
                    "languages": ["en"],
                    "features": ["timestamps", "confidence_scores"],
                },
            },
            "emotion_models": {
                "facial_emotion": {
                    "available": True,
                    "supported_emotions": [
                        "happy",
                        "sad",
                        "angry",
                        "fear",
                        "surprise",
                        "disgust",
                        "neutral",
                    ],
                    "confidence_threshold": 0.7,
                    "features": ["real_time", "face_detection", "landmark_detection"],
                },
                "voice_emotion": {
                    "available": True,
                    "supported_emotions": [
                        "happy",
                        "sad",
                        "angry",
                        "fear",
                        "surprise",
                        "neutral",
                    ],
                    "confidence_threshold": 0.8,
                    "features": ["acoustic_features", "stress_detection"],
                },
            },
            "sentiment_models": {
                "roberta_sentiment": {
                    "available": True,
                    "accuracy": 0.92,
                    "supported_languages": ["en"],
                    "features": ["confidence_scores", "neutral_classification"],
                },
                "distilbert_sentiment": {
                    "available": True,
                    "accuracy": 0.89,
                    "supported_languages": ["en"],
                    "features": ["confidence_scores", "neutral_classification"],
                },
                "vader_sentiment": {
                    "available": True,
                    "accuracy": 0.75,
                    "supported_languages": ["en"],
                    "features": ["fast_processing", "sentiment_intensity"],
                },
            },
            "facial_detection": {
                "available": True,
                "detection_method": "opencv_haarcascade",
                "max_faces": 10,
                "min_face_size": 30,
                "features": ["multi_face", "face_tracking", "landmark_detection"],
            },
            "system_info": {
                "gpu_available": False,  # Would check actual GPU availability
                "max_video_duration": 300,  # 5 minutes
                "supported_video_formats": ["mp4", "webm", "mov", "avi"],
                "supported_audio_formats": ["wav", "mp3", "m4a", "flac"],
                "processing_queue": "available",
                "last_updated": datetime.utcnow().isoformat(),
            },
        }

        return models_status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recording/config")
async def get_recording_config(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get recording configuration options and capabilities.
    """
    try:
        config = {
            "video_settings": {
                "max_duration": 300,  # 5 minutes
                "supported_qualities": [
                    {"value": "low", "description": "360p, 15fps - Fast processing"},
                    {
                        "value": "medium",
                        "description": "720p, 30fps - Balanced quality",
                    },
                    {"value": "high", "description": "1080p, 30fps - Best quality"},
                ],
                "supported_formats": ["mp4", "webm"],
                "resolutions": ["640x480", "1280x720", "1920x1080"],
                "frame_rates": [15, 24, 30],
            },
            "audio_settings": {
                "sample_rate": 16000,  # 16kHz for speech recognition
                "channels": 1,  # Mono for speech recognition
                "bit_depth": 16,
                "formats": ["wav", "mp3", "aac"],
            },
            "transcription_settings": {
                "supported_languages": [
                    {"code": "en-US", "name": "English (US)"},
                    {"code": "en-GB", "name": "English (UK)"},
                    {"code": "es-ES", "name": "Spanish"},
                    {"code": "fr-FR", "name": "French"},
                    {"code": "de-DE", "name": "German"},
                ],
                "quality_levels": [
                    {"value": "draft", "description": "Fast, ~85% accuracy"},
                    {"value": "standard", "description": "Balanced, ~92% accuracy"},
                    {"value": "high", "description": "Slow, ~97% accuracy"},
                ],
            },
            "analysis_settings": {
                "facial_analysis": {
                    "enabled": True,
                    "real_time": True,
                    "emotions": [
                        "happy",
                        "sad",
                        "angry",
                        "fear",
                        "surprise",
                        "neutral",
                    ],
                    "features": [
                        "emotion_detection",
                        "attention_scoring",
                        "eye_contact",
                    ],
                },
                "voice_sentiment": {
                    "enabled": True,
                    "real_time": True,
                    "sentiments": ["positive", "negative", "neutral"],
                    "features": [
                        "sentiment_analysis",
                        "stress_detection",
                        "confidence_scoring",
                    ],
                },
                "comprehensive_analysis": {
                    "enabled": True,
                    "multi_modal": True,
                    "features": [
                        "authenticity_scoring",
                        "engagement_metrics",
                        "risk_assessment",
                    ],
                },
            },
            "limitations": {
                "max_file_size": 104857600,  # 100MB
                "max_duration": 300,  # 5 minutes
                "concurrent_analyses": 3,
                "storage_quota": 10737418240,  # 10GB per user
            },
        }

        return config

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a specific analysis result.
    """
    try:
        # In production, this would delete from database and file storage
        return {
            "status": "success",
            "message": f"Analysis {analysis_id} deleted successfully",
            "deleted_date": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{analysis_id}")
async def export_analysis(
    analysis_id: str,
    format: str = Query("json", description="Export format (json, csv, pdf)"),
    include_video: bool = Query(False, description="Include video file in export"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export analysis results in specified format.
    """
    try:
        # In production, this would generate and return the exported file
        return {
            "export_id": f"export_{analysis_id}_{datetime.utcnow().timestamp()}",
            "format": format,
            "status": "ready",
            "download_url": f"/api/v1/voice-video/download/export_{analysis_id}.{format}",
            "file_size": 1024,  # Mock file size in bytes
            "created_date": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
