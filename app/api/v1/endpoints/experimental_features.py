"""
Experimental Features Lab API Endpoints

Advanced R&D platform endpoints for A/B testing, gamification, and voice analysis.
"""

from typing import List, Optional, Dict, Any

from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_async_db, get_current_active_user
from app.db.models.user import User
from app.services.experimental_features import (
    ExperimentalFeaturesLab,
    ExperimentConfig,
    ExperimentResults,
    GamificationProfile,
    VoiceAnalysisResult,
    VoiceAnalysisType,
    ExperimentStatus,
    TestType
)
from pydantic import BaseModel, Field

router = APIRouter()

# Request/Response Models
class ExperimentConfigRequest(BaseModel):
    experiment_id: str = Field(..., description="Unique experiment identifier")
    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    test_type: str = Field(..., description="Type of A/B test")
    traffic_split: Dict[str, float] = Field(..., description="Traffic allocation per variant")
    target_audience: Dict[str, Any] = Field(default_factory=dict, description="Target audience criteria")
    success_metrics: List[str] = Field(..., description="Success metrics to track")
    duration_days: int = Field(..., description="Experiment duration in days")
    min_sample_size: int = Field(..., description="Minimum sample size required")
    confidence_level: float = Field(0.95, description="Statistical confidence level")
    variants: Dict[str, Any] = Field(..., description="Variant configurations")

class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    description: str
    status: str
    test_type: str
    start_date: str
    duration_days: int
    participants: int
    variants: Dict[str, Dict[str, float]]
    statistical_significance: bool
    winner: Optional[str]
    business_impact: float

class GamificationProfileResponse(BaseModel):
    current_level: int
    total_points: int
    current_streak: int
    longest_streak: int
    achievements: List[Dict[str, Any]]
    badges: List[Dict[str, Any]]
    leaderboard_rank: Optional[int]
    engagement_score: float
    preferences: Dict[str, Any]

class AchievementRequest(BaseModel):
    achievement_type: str = Field(..., description="Type of achievement to award")
    achievement_data: Dict[str, Any] = Field(default_factory=dict, description="Additional achievement data")

class VoiceAnalysisRequest(BaseModel):
    analysis_types: List[str] = Field(..., description="Types of voice analysis to perform")

class VoiceAnalysisResponse(BaseModel):
    analysis_id: str
    user_id: str
    audio_duration: float
    sentiment_score: Dict[str, float]
    emotions: Dict[str, float]
    speech_metrics: Dict[str, float]
    confidence_score: float
    engagement_level: float
    stress_indicators: List[str]
    recommendations: List[str]
    analysis_date: str

class LabDashboardResponse(BaseModel):
    active_experiments: int
    total_experiments: int
    experiment_results: Dict[str, Any]
    gamification_stats: Dict[str, Any]
    voice_analysis_stats: Dict[str, Any]
    feature_adoption: Dict[str, Any]
    user_engagement: Dict[str, Any]

class LeaderboardResponse(BaseModel):
    leaderboard_type: str
    entries: List[Dict[str, Any]]
    total_entries: int
    user_rank: Optional[int]
    last_updated: str

# API Endpoints

@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/experiments", response_model=str)
async def create_experiment(
    config: ExperimentConfigRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new A/B testing experiment.
    """
    try:
        # Authorization check - require admin or researcher role
        if not (current_user.is_superuser or current_user.role in ["admin", "researcher"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create experiments"
            )

        # Convert to experiment config
        experiment_config = ExperimentConfig(
            experiment_id=config.experiment_id,
            name=config.name,
            description=config.description,
            test_type=TestType(config.test_type),
            traffic_split=config.traffic_split,
            target_audience=config.target_audience,
            success_metrics=config.success_metrics,
            duration_days=config.duration_days,
            min_sample_size=config.min_sample_size,
            confidence_level=config.confidence_level,
            variants=config.variants
        )

        lab = ExperimentalFeaturesLab(db)
        experiment_id = await lab.create_experiment(experiment_config)

        return experiment_id

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/experiments", response_model=List[ExperimentResponse])
async def get_experiments(
    status: Optional[str] = Query(None, description="Filter by experiment status"),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    limit: int = Query(50, description="Maximum number of experiments to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of experiments with optional filtering.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "researcher"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view experiments"
            )

        lab = ExperimentalFeaturesLab(db)
        dashboard = await lab.get_experiment_dashboard()

        # Mock experiment list with filtering
        experiments = [
            ExperimentResponse(
                experiment_id="exp_001",
                name="AI Assessment Algorithm Test",
                description="Testing new personality analysis algorithm vs. current version",
                status="running",
                test_type="algorithm_change",
                start_date="2024-01-15",
                duration_days=21,
                participants=2450,
                variants={
                    "control": {"users": 1225, "conversion_rate": 0.058},
                    "treatment": {"users": 1225, "conversion_rate": 0.067}
                },
                statistical_significance=False,
                winner=None,
                business_impact=15.5
            ),
            ExperimentResponse(
                experiment_id="exp_002",
                name="Gamification Impact Study",
                description="Measuring engagement impact of new achievement system",
                status="completed",
                test_type="ui_variation",
                start_date="2024-01-01",
                duration_days=14,
                participants=1820,
                variants={
                    "control": {"users": 910, "conversion_rate": 0.042},
                    "treatment": {"users": 910, "conversion_rate": 0.068}
                },
                statistical_significance=True,
                winner="treatment",
                business_impact=61.9
            )
        ]

        # Apply filters
        if status:
            experiments = [e for e in experiments if e.status == status]
        if test_type:
            experiments = [e for e in experiments if e.test_typee == test_type
]

        return experiments[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/experiments/{experiment_id}/assign", response_model=Optional[str])
async def assign_user_to_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign current user to an experiment variant.
    """
    try:
        lab = ExperimentalFeaturesLab(db)
        variant = await lab.assign_user_to_variant(current_user.id, experiment_id)

        return variant

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/experiments/{experiment_id}/track")
async def track_experiment_event(
    experiment_id: str,
    event_name: str,
    event_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Track user events for experiment analysis.
    """
    try:
        lab = ExperimentalFeaturesLab(db)
        success = await lab.track_experiment_event(
            current_user.id, experiment_id, event_name, event_data
        )

        if success:
            return {"status": "success", "message": "Event tracked successfully"}
        else:
            return {"status": "failed", "message": "Failed to track event"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed results and analysis for a specific experiment.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "researcher"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view experiment results"
            )

        lab = ExperimentalFeaturesLab(db)
        results = await lab.analyze_experiment_results(experiment_id)

        return {
            "experiment_id": results.experiment_id,
            "status": results.status.value,
            "total_participants": results.total_participants,
            "variant_results": results.variant_results,
            "statistical_significance": results.statistical_significance,
            "winner": results.winner,
            "confidence_intervals": results.confidence_intervals,
            "business_impact": results.business_impact
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/gamification/profile", response_model=GamificationProfileResponse)
async def get_gamification_profile(
    user_id: Optional[str] = Query(None, description="User ID to get profile for (defaults to current user)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get gamification profile for a user.
    """
    try:
        target_user_id = user_id if user_id else current_user.id

        # Authorization check - users can only see their own profile unless admin
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view gamification profile for this user"
            )

        lab = ExperimentalFeaturesLab(db)
        profile = await lab.get_user_gamification_profile(target_user_id)

        return GamificationProfileResponse(
            current_level=profile.current_level,
            total_points=profile.total_points,
            current_streak=profile.current_streak,
            longest_streak=profile.longest_streak,
            achievements=profile.achievements,
            badges=profile.badges,
            leaderboard_rank=profile.leaderboard_rank,
            engagement_score=profile.engagement_score,
            preferences=profile.preferences
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/gamification/achievements", response_model=Dict[str, Any])
async def award_achievement(
    request: AchievementRequest,
    user_id: Optional[str] = Query(None, description="User ID to award achievement to (defaults to current user)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Award an achievement to a user.
    """
    try:
        target_user_id = user_id if user_id else current_user.id

        # Authorization check - users can only award to themselves unless admin
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to award achievements to this user"
            )

        lab = ExperimentalFeaturesLab(db)
        success = await lab.award_achievement(
            target_user_id, request.achievement_type, request.achievement_data
        )

        if success:
            return {
                "status": "success",
                "message": f"Achievement {request.achievement_type} awarded successfully",
                "user_id": target_user_id,
                "achievement_type": request.achievement_type
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to award achievement (possibly already awarded)"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/gamification/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    leaderboard_type: str = Query("points", description="Type of leaderboard"),
    limit: int = Query(50, description="Maximum number of entries to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get gamification leaderboard.
    """
    try:
        lab = ExperimentalFeaturesLab(db)
        leaderboard_data = await lab.get_leaderboard(leaderboard_type, limit)

        # Find current user's rank
        user_rank = None
        for entry in leaderboard_data:
            if entry.get("user_id") == current_user.id:
                user_rank = entry.get("rank")
                break

        return LeaderboardResponse(
            leaderboard_type=leaderboard_type,
            entries=leaderboard_data,
            total_entries=len(leaderboard_data),
            user_rank=user_rank,
            last_updated=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/voice/analyze", response_model=VoiceAnalysisResponse)
async def analyze_voice_response(
    audio_file: UploadFile = File(..., description="Audio file to analyze"),
    analysis_types: List[str] = Query(..., description="Types of analysis to perform"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze voice response for emotional and behavioral insights.
    """
    try:
        # Validate analysis types
        valid_types = [t.value for t in VoiceAnalysisType]
        invalid_types = [t for t in analysis_types if t not in valid_types]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis types: {invalid_types}"
            )

        # Read audio file
        audio_data = await audio_file.read()

        # Convert analysis types
        voice_analysis_types = [VoiceAnalysisType(t) for t in analysis_types]

        lab = ExperimentalFeaturesLab(db)
        result = await lab.analyze_voice_response(audio_data, current_user.id, voice_analysis_types)

        return VoiceAnalysisResponse(
            analysis_id=result.analysis_id,
            user_id=result.user_id,
            audio_duration=result.audio_duration,
            sentiment_score=result.sentiment_score,
            emotions=result.emotions,
            speech_metrics=result.speech_metrics,
            confidence_score=result.confidence_score,
            engagement_level=result.engagement_level,
            stress_indicators=result.stress_indicators,
            recommendations=result.recommendations,
            analysis_date=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/voice/analysis/{analysis_id}")
async def get_voice_analysis_result(
    analysis_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific voice analysis result.
    """
    try:
        # In production, this would retrieve from database
        # For now, return mock data
        return {
            "analysis_id": analysis_id,
            "user_id": current_user.id,
            "status": "completed",
            "created_date": datetime.utcnow().isoformat(),
            "sentiment_score": {
                "positive": 0.65,
                "negative": 0.15,
                "neutral": 0.20
            },
            "emotions": {
                "joy": 0.35,
                "sadness": 0.08,
                "anger": 0.05,
                "fear": 0.12,
                "surprise": 0.18,
                "disgust": 0.02
            },
            "recommendations": [
                "Consider stress management techniques to improve vocal clarity",
                "Try to speak with more enthusiasm and variation in tone"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/voice/stats")
async def get_voice_analysis_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get voice analysis platform statistics.
    """
    try:
        lab = ExperimentalFeaturesLab(db)
        voice_analyzer = lab.voice_analyzer
        stats = await voice_analyzer.get_analysis_stats()

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/dashboard", response_model=LabDashboardResponse)
async def get_experimental_lab_dashboard(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive experimental features lab dashboard.
    """
    try:
        lab = ExperimentalFeaturesLab(db)
        dashboard = await lab.get_experiment_dashboard()

        return LabDashboardResponse(
            active_experiments=dashboard["active_experiments"],
            total_experiments=dashboard["total_experiments"],
            experiment_results=dashboard["experiment_results"],
            gamification_stats=dashboard["gamification_stats"],
            voice_analysis_stats=dashboard["voice_analysis_stats"],
            feature_adoption=dashboard["feature_adoption"],
            user_engagement=dashboard["user_engagement"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/opt-in", response_model=Dict[str, Any])
async def opt_in_experimental_features(
    opt_in: bool = Field(..., description="Whether to opt in to experimental features"),
    feature_types: Optional[List[str]] = Field(None, description="Specific feature types to opt in to"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Opt in or out of experimental features.
    """
    try:
        # In production, this would update user preferences in database
        return {
            "status": "success",
            "message": f"Successfully opted {'in' if opt_in else 'out'} of experimental features",
            "opt_in_status": opt_in,
            "feature_types": feature_types or "all",
            "updated_date": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/available-features")
async def get_available_experimental_features(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available experimental features.
    """
    try:
        return {
            "ab_testing": {
                "name": "A/B Testing Framework",
                "description": "Participate in user experience experiments",
                "status": "available",
                "participation_rate": 0.64,
                "requirements": []
            },
            "gamification": {
                "name": "Gamification System",
                "description": "Earn points, achievements, and climb leaderboards",
                "status": "available",
                "participation_rate": 0.78,
                "requirements": []
            },
            "voice_analysis": {
                "name": "Voice Response Analysis",
                "description": "Get emotional insights from voice responses",
                "status": "beta",
                "participation_rate": 0.42,
                "requirements": ["microphone_access", "audio_upload"]
            },
            "experimental_algorithms": {
                "name": "Experimental AI Algorithms",
                "description": "Try new personality analysis methods",
                "status": "alpha",
                "participation_rate": 0.28,
                "requirements": ["assessment_completion"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/feedback")
async def submit_experimental_feature_feedback(
    feature_type: str = Field(..., description="Type of experimental feature"),
    feedback_data: Dict[str, Any] = Field(..., description="Feedback data"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit feedback for experimental features.
    """
    try:
        # In production, this would save feedback to database
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feature_type": feature_type,
            "feedback_id": f"fb_{current_user.id}_{datetime.utcnow().timestamp()}",
            "submitted_date": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/analytics/experiment-participation")
async def get_experiment_participation_analytics(
    timeframe_days: int = Query(30, description="Timeframe in days"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analytics about experiment participation.
    """
    try:
        # Authorization check - require admin or researcher role
        if not (current_user.is_superuser or current_user.role in ["admin", "researcher"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view experiment analytics"
            )

        # Mock analytics data
        return {
            "timeframe_days": timeframe_days,
            "total_participants": 3450,
            "new_participants": 847,
            "retention_rate": 0.73,
            "participation_by_feature": {
                "ab_testing": 0.64,
                "gamification": 0.78,
                "voice_analysis": 0.42,
                "experimental_algorithms": 0.28
            },
            "completion_rates": {
                "experiment_completion": 0.89,
                "assessment_completion": 0.76,
                "voice_analysis_completion": 0.91
            },
            "user_satisfaction": {
                "overall": 0.84,
                "ab_testing": 0.79,
                "gamification": 0.91,
                "voice_analysis": 0.72
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/analytics/gamification-engagement")
async def get_gamification_engagement_analytics(
    timeframe_days: int = Query(30, description="Timeframe in days"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analytics about gamification engagement.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view gamification analytics"
            )

        # Mock gamification analytics
        return {
            "timeframe_days": timeframe_days,
            "active_players": 15420,
            "daily_active_players": 3250,
            "achievements_unlocked": 1847,
            "total_points_awarded": 245000,
            "engagement_by_level": {
                "beginner": 0.82,
                "intermediate": 0.76,
                "advanced": 0.71,
                "expert": 0.68
            },
            "popular_achievements": [
                {"achievement_id": "first_assessment", "unlocked_count": 892},
                {"achievement_id": "week_streak", "unlocked_count": 447},
                {"achievement_id": "team_leader", "unlocked_count": 234}
            ],
            "leaderboard_activity": {
                "daily_changes": 147,
                "weekly_changes": 892,
                "monthly_changes": 3420
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
