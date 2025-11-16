# app/api/v1/endpoints/communication_analysis.py
"""
Communication Analysis API Endpoints
Provides insights into behavioral patterns and communication analytics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.nlp_analysis_service import nlp_analysis_service
from app.services.communication_pattern_service import communication_pattern_service
from app.services.culture_health_service import culture_health_service
from app.services.coaching_recommendation_service import coaching_recommendation_service
from app.db.models.communication_analysis import CommunicationAnalysis
from app.db.models.communication_patterns import CommunicationPatterns
from app.db.models.culture_metrics import CultureMetrics
from app.db.models.coaching_recommendations import CoachingRecommendation
from app.core.logging_config import logger

router = APIRouter()

# Pydantic models for responses
class SentimentAnalysisResponse(BaseModel):
    score: float
    confidence: float
    label: str

class EmotionAnalysisResponse(BaseModel):
    emotions: Dict[str, float]
    dominant_emotion: str
    emotional_intensity: float

class BehavioralIndicatorsResponse(BaseModel):
    communication_style: str
    response_pattern: str
    leadership_indicators: float
    collaboration_score: float
    conflict_tendency: float
    burnout_risk: float

class CommunicationPatternsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_communications: int
    avg_sentiment_score: Optional[float]
    communication_frequency: float
    leadership_indicators_score: float
    collaboration_score: float
    burnout_risk_score: float
    network_centrality_score: float

class CultureHealthResponse(BaseModel):
    psychological_safety_score: float
    collaboration_score: float
    innovation_score: float
    trust_level: float
    overall_health_score: float
    health_level: str
    risk_factors: List[str]
    strengths: List[str]

class CoachingRecommendationResponse(BaseModel):
    id: str
    recommendation_type: str
    priority: str
    title: str
    description: str
    actionable_steps: List[str]
    resources: List[str]
    confidence_score: float
    created_at: datetime

class InsightsSummaryResponse(BaseModel):
    analysis_period_days: int
    total_emails_analyzed: int
    sentiment_analysis: Dict[str, Any]
    conflict_analysis: Dict[str, Any]
    behavioral_patterns: Dict[str, Any]
    recommendations_count: int

@router.get("/sentiment/summary", response_model=Dict[str, Any])
async def get_sentiment_summary(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sentiment analysis summary for user's communications
    """
    try:
        insights = await nlp_analysis_service.generate_insights_summary(db, current_user.id, days_back)
        return {
            "success": True,
            "data": insights
        }
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate sentiment summary"
        )

@router.get("/patterns/analysis", response_model=CommunicationPatternsResponse)
async def get_communication_patterns(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed communication patterns analysis
    """
    try:
        # Generate current patterns if not available
        patterns = await communication_pattern_service.analyze_user_patterns(db, current_user.id, days_back)

        if not patterns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No communication patterns available"
            )

        return CommunicationPatternsResponse(
            period_start=patterns.period_start,
            period_end=patterns.period_end,
            total_communications=patterns.total_communications,
            avg_sentiment_score=patterns.avg_sentiment_score,
            communication_frequency=patterns.communication_frequency,
            leadership_indicators_score=patterns.leadership_indicators_score,
            collaboration_score=patterns.collaboration_score,
            burnout_risk_score=patterns.burnout_risk_score,
            network_centrality_score=patterns.network_centrality_score
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting communication patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze communication patterns"
        )

@router.get("/patterns/behavioral", response_model=BehavioralIndicatorsResponse)
async def get_behavioral_indicators(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get behavioral indicators based on communication analysis
    """
    try:
        # Get recent email metadata
        emails = await communication_pattern_service.get_user_emails(
            db, current_user.id, days_back
        )

        if not emails:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No email data available for analysis"
            )

        # Analyze patterns
        behavioral_indicators = communication_pattern_service.analyze_communication_patterns(emails)

        return BehavioralIndicatorsResponse(
            communication_style=behavioral_indicators.communication_style,
            response_pattern=behavioral_indicators.response_pattern,
            leadership_indicators=behavioral_indicators.leadership_indicators,
            collaboration_score=behavioral_indicators.collaboration_score,
            conflict_tendency=behavioral_indicators.conflict_tendency,
            burnout_risk=behavioral_indicators.burnout_risk
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting behavioral indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze behavioral indicators"
        )

@router.get("/culture/team", response_model=CultureHealthResponse)
async def get_team_culture_health(
    team_id: Optional[str] = Query(None, description="Team ID (optional, uses user's team if not provided)"),
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get culture health analysis for team
    """
    try:
        # Determine team ID
        target_team_id = team_id
        if not target_team_id and hasattr(current_user, 'team_id'):
            target_team_id = current_user.team_id

        if not target_team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team ID required for culture analysis"
            )

        # Generate or get culture metrics
        culture_metrics = await culture_health_service.analyze_team_culture(db, target_team_id, days_back)

        if not culture_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No culture data available for team"
            )

        return CultureHealthResponse(
            psychological_safety_score=culture_metrics.psychological_safety_score,
            collaboration_score=culture_metrics.collaboration_score,
            innovation_score=culture_metrics.innovation_score,
            trust_level=culture_metrics.trust_level,
            overall_health_score=culture_metrics.overall_health_score,
            health_level=culture_metrics.health_level.value if hasattr(culture_metrics.health_level, 'value') else str(culture_metrics.health_level),
            risk_factors=culture_metrics.risk_factors_identified,
            strengths=culture_metrics.strength_indicators
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team culture health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze team culture"
        )

@router.get("/culture/organization", response_model=CultureHealthResponse)
async def get_organization_culture_health(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get culture health analysis for organization
    """
    try:
        if not current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to an organization"
            )

        # Generate or get culture metrics
        culture_metrics = await culture_health_service.analyze_organization_culture(db, current_user.organization_id, days_back)

        if not culture_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No culture data available for organization"
            )

        return CultureHealthResponse(
            psychological_safety_score=culture_metrics.psychological_safety_score,
            collaboration_score=culture_metrics.collaboration_score,
            innovation_score=culture_metrics.innovation_score,
            trust_level=culture_metrics.trust_level,
            overall_health_score=culture_metrics.overall_health_score,
            health_level=culture_metrics.health_level.value if hasattr(culture_metrics.health_level, 'value') else str(culture_metrics.health_level),
            risk_factors=culture_metrics.risk_factors_identified,
            strengths=culture_metrics.strength_indicators
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization culture health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze organization culture"
        )

@router.get("/coaching/recommendations", response_model=List[CoachingRecommendationResponse])
async def get_coaching_recommendations(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized coaching recommendations
    """
    try:
        # Generate recommendations if not available
        recommendations = await coaching_recommendation_service.generate_user_recommendations(db, current_user.id, days_back)

        if not recommendations:
            return []

        # Save recommendations to database
        for rec in recommendations:
            db.add(rec)
        await db.commit()

        # Get all recommendations for the user
        all_recommendations = db.query(CoachingRecommendation).filter(
            CoachingRecommendation.user_id == current_user.id,
            CoachingRecommendation.expires_at > datetime.utcnow()
        ).order_by(CoachingRecommendation.created_at.desc()).limit(20).all()

        return [
            CoachingRecommendationResponse(
                id=str(rec.id),
                recommendation_type=rec.recommendation_type.value if hasattr(rec.recommendation_type, 'value') else str(rec.recommendation_type),
                priority=rec.priority.value if hasattr(rec.priority, 'value') else str(rec.priority),
                title=rec.title,
                description=rec.description,
                actionable_steps=rec.actionable_steps,
                resources=rec.resources or [],
                confidence_score=rec.confidence_score,
                created_at=rec.created_at
            )
            for rec in all_recommendations
        ]
    except Exception as e:
        logger.error(f"Error getting coaching recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate coaching recommendations"
        )

@router.get("/insights/summary", response_model=InsightsSummaryResponse)
async def get_insights_summary(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive insights summary combining all analysis types
    """
    try:
        # Get various analyses
        sentiment_insights = await nlp_analysis_service.generate_insights_summary(db, current_user.id, days_back)

        # Get communication patterns
        patterns = db.query(CommunicationPatterns).filter(
            CommunicationPatterns.user_id == current_user.id,
            CommunicationPatterns.period_start >= datetime.utcnow() - timedelta(days=days_back)
        ).all()

        # Get coaching recommendations count
        recommendations_count = db.query(CoachingRecommendation).filter(
            CoachingRecommendation.user_id == current_user.id,
            CoachingRecommendation.created_at >= datetime.utcnow() - timedelta(days=days_back)
        ).count()

        # Build summary
        summary = InsightsSummaryResponse(
            analysis_period_days=days_back,
            total_emails_analyzed=sentiment_insights.get("total_emails_analyzed", 0),
            sentiment_analysis=sentiment_insights.get("sentiment_analysis", {}),
            conflict_analysis=sentiment_insights.get("conflict_analysis", {}),
            behavioral_patterns=sentiment_insights.get("behavioral_patterns", {}),
            recommendations_count=recommendations_count
        )

        return summary
    except Exception as e:
        logger.error(f"Error getting insights summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights summary"
        )

@router.post("/coaching/{recommendation_id}/complete")
async def complete_recommendation(
    recommendation_id: str,
    completion_notes: Optional[str] = Query(None, description="Notes about completion"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a coaching recommendation as completed
    """
    try:
        recommendation = db.query(CoachingRecommendation).filter(
            CoachingRecommendation.id == recommendation_id,
            CoachingRecommendation.user_id == current_user.id
        ).first()

        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommendation not found"
            )

        # Mark as completed
        recommendation.status = "completed"
        recommendation.completed_at = datetime.utcnow()
        recommendation.completion_notes = completion_notes

        await db.commit()

        return {
            "success": True,
            "message": "Recommendation marked as completed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing recommendation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete recommendation"
        )

@router.get("/coaching/effectiveness")
async def get_coaching_effectiveness(
    days_back: int = Query(default=90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis of coaching recommendation effectiveness
    """
    try:
        effectiveness = await coaching_recommendation_service.get_recommendation_effectiveness(db, current_user.id, days_back)
        return {
            "success": True,
            "data": effectiveness
        }
    except Exception as e:
        logger.error(f"Error getting coaching effectiveness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze coaching effectiveness"
        )

@router.post("/analysis/trigger")
async def trigger_analysis(
    analysis_type: str = Query(..., description="Type of analysis to trigger: 'patterns', 'culture', 'recommendations'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger analysis for the user
    """
    try:
        results = {}

        if analysis_type in ["patterns", "all"]:
            # Trigger communication patterns analysis
            patterns = await communication_pattern_service.analyze_user_patterns(db, current_user.id, 30)
            if patterns:
                db.add(patterns)
                await db.commit()
                results["patterns"] = "Analysis completed successfully"
        else:
            results["patterns"] = "Insufficient data for analysis"

        if analysis_type in ["recommendations", "all"]:
            # Generate coaching recommendations
            recommendations = await coaching_recommendation_service.generate_user_recommendations(db, current_user.id, 30)
            for rec in recommendations:
                db.add(rec)
        await db.commit()
            results["recommendations"] = f"Generated {len(recommendations)} recommendations"

        if analysis_type in ["culture", "all"] and current_user.organization_id:
            # Trigger organization culture analysis (admin only)
            if current_user.role == "admin":
                culture_metrics = await culture_health_service.analyze_organization_culture(db, current_user.organization_id, 30)
                if culture_metrics:
                    db.add(culture_metrics)
        await db.commit()
                    results["culture"] = "Culture analysis completed successfully"
                else:
                    results["culture"] = "Insufficient data for culture analysis"
            else:
                results["culture"] = "Admin privileges required for culture analysis"

        return {
            "success": True,
            "message": f"Analysis triggered for {analysis_type}",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger analysis"
        )

@router.get("/dashboard/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get key metrics for dashboard display
    """
    try:
        # Get recent patterns
        recent_patterns = db.query(CommunicationPatterns).filter(
            CommunicationPatterns.user_id == current_user.id,
            CommunicationPatterns.period_end >= datetime.utcnow() - timedelta(days=7)
        ).first()

        # Get active recommendations
        active_recommendations = db.query(CoachingRecommendation).filter(
            CoachingRecommendation.user_id == current_user.id,
            CoachingRecommendation.status != "completed",
            CoachingRecommendation.expires_at > datetime.utcnow()
        ).count()

        # Get recent sentiment trend
        recent_analyses = db.query(CommunicationAnalysis).filter(
            CommunicationAnalysis.user_id == current_user.id,
            CommunicationAnalysis.analysis_timestamp >= datetime.utcnow() - timedelta(days=7)
        ).all()

        sentiment_trend = "stable"
        if recent_analyses:
            sentiment_scores = [float(a.sentiment_score) for a in recent_analyses if a.sentiment_score]
            if len(sentiment_scores) > 5:
                recent_avg = sum(sentiment_scores[-3:]) / 3
                earlier_avg = sum(sentiment_scores[:3]) / 3
                if recent_avg > earlier_avg + 0.1:
                    sentiment_trend = "improving"
                elif recent_avg < earlier_avg - 0.1:
                    sentiment_trend = "declining"

        metrics = {
            "sentiment_score": recent_patterns.avg_sentiment_score if recent_patterns else None,
            "leadership_indicators": recent_patterns.leadership_indicators_score if recent_patterns else None,
            "collaboration_score": recent_patterns.collaboration_score if recent_patterns else None,
            "burnout_risk": recent_patterns.burnout_risk_score if recent_patterns else None,
            "active_recommendations": active_recommendations,
            "sentiment_trend": sentiment_trend,
            "emails_analyzed_this_week": len(recent_analyses),
            "last_analysis_date": recent_patterns.period_end if recent_patterns else None
        }

        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard metrics"
        )