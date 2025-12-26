"""
Growth Marketing API Endpoints
Enterprise-grade user acquisition, retention, and growth automation
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.middleware.rate_limiter import check_rate_limit
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.services.growth_marketing_service import (
    GrowthMarketingService,
    CampaignType,
    TriggerType,
    UserJourneyStage,
    growth_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/growth", tags=["Growth Marketing"])


@check_rate_limit(identifier="public", endpoint_type="public")
@router.post("/campaigns/trigger")
async def trigger_growth_campaign(
    campaign_id: str,
    trigger_type: TriggerType,
    user_id: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger a growth marketing campaign
    """
    try:
        # Use authenticated user if no specific user_id provided
        target_user_id = user_id or str(current_user.id)

        success = await growth_service.trigger_campaign(
            campaign_id=campaign_id,
            trigger_type=trigger_type,
            user_id=target_user_id,
            context_data=context_data
        )

        if success:
            return {
                "success": True,
                "campaign_id": campaign_id,
                "trigger_type": trigger_type.value,
                "user_id": target_user_id,
                "executed_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign trigger failed - check criteria and conditions"
            )

    except Exception as e:
        logger.error(f"Failed to trigger campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      
@check_rate_limit(identifier="public", endpoint_type="public")
      detail=f"Failed to trigger campaign: {str(e)}"
        )

@router.get("/campaigns", dependencies=[Depends(get_current_user)])
async def list_campaigns():
    """
    List all available growth marketing campaigns
    """
    try:
        campaigns = []

        for campaign_id, campaign in growth_service.campaigns.items():
            campaigns.append({
                "id": campaign.id,
                "name": campaign.name,
                "campaign_type": campaign.campaign_type.value,
                "description": campaign.description,
                "is_active": campaign.is_active,
                "trigger_events": [event.value for event in campaign.trigger_events],
                "target_segments": campaign.target_segments,
                "created_at": campaign.created_at.isoformat()
            })

        return {
            "campaigns": campaigns,
            "total_count": len(campaigns)
        }

    except Exception as e:
        logger.error(f"Failed to list campaigns: {str(e)}")
        raise HTTPExcepti
@check_rate_limit(identifier="public", endpoint_type="public")
on(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaigns"
        )

@router.get("/segments")
async def list_user_segments():
    """
    List all user segments for targeting
    """
    try:
        segments = []

        for segment_id, segment in growth_service.segments.items():
            segments.append({
                "id": segment.id,
                "name": segment.name,
                "description": segment.description,
                "estimated_size": segment.estimated_size,
                "growth_rate": segment.growth_rate,
                "created_at": segment.created_at.isoformat()
            })

        return {
            "segments": segments,
            "total_count": len(segments)
        }

    except Exception as e:
        logger.error(f"Failed to list user segments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user segments"
        )

@router.get("/journey/stage/{user_id}")
async def get_user_journey_stage(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current journey stage
    """
    try:
        # Users can only check their own journey stage unless admin
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        stage = await growth_service.get_user_journey_stage(user_id)

        return {
            "user_id": user_id,
            "stage": stage.value,
            "stage_description": self._get_stage_description(stage),
            "stage_color": self._get_stage_color(stage),
            "next_stage": self._get_next_stage(stage)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user journey stage for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user journey stage: {str(e)}"
        )

def _get_stage_description(stage: UserJourneyStage) -> str:
    """Get human-readable description of journey stage"""
    descriptions = {
        UserJourneyStage.NEW_USER: "Just joined the platform - needs onboarding guidance",
        UserJourneyStage.ACTIVATING: "Starting to explore features - needs engagement",
        UserJourneyStage.ENGAGED: "Using platform regularly - ready for advanced features",
        UserJourneyStage.ACTIVE: "Consistent user - ready for optimization",
        UserJourneyStage.LOYAL: "Long-term power user - brand advocate potential",
        UserJourneyStage.AT_RISK: "Recently inactive - needs re-engagement",
        UserJourneyStage.DORMANT: "Inactive for extended period - requires win-back campaign"
    }
    return descriptions.get(stage, "Unknown stage")

def _get_stage_color(stage: UserJourneyStage) -> str:
    """Get color for journey stage visualization"""
    colors = {
        UserJourneyStage.NEW_USER: "#3b82f6",  # Blue
        UserJourneyStage.ACTIVATING: "#10b981",  # Green
        UserJourneyStage.ENGAGED: "#f59e0b",  # Yellow
        UserJourneyStage.ACTIVE: "#06b6d4",  # Cyan
        UserJourneyStage.LOYAL: "#8b5cf6",  # Purple
        UserJourneyStage.AT_RISK: "#f97316",  # Orange
        UserJourneyStage.DORMANT: "#ef4444"   # Red
    }
    return colors.get(stage, "#6b7280")

def _get_next_stage(stage: UserJourneyStage) -> Optional[str]:
    """Get next logical stage in user journey"""
    progression = {
        UserJourneyStage.NEW_USER: UserJourneyStage.ACTIVATING,
        UserJourneyStage.ACTIVATING: UserJourneyStage.ENGAGED,
        UserJourneyStage.ENGAGED: UserJourneyStage.ACTIVE,
        UserJourneyStage.ACTIVE: UserJourneyStage.LOYAL,
        UserJourneyStage.AT_RISK: UserJourneyStage.DORMANT,
        UserJourneyStage.DORMANT: None,
        UserJourneyStage.LOYAL: UserJourneyStage.LOYAL
    }
    next_stage = progression.get(stage)
    return next_stage.value if next_stage else None

@router.post("/referrals/generate")
async def generate_referral_code(
    current_user: User = Depends(get_current_user)
):
    """
    Generate unique referral code for user
    """
    try:
        referral_code = await growth_service.generate_referral_code(str(current_user.id))

        return {
            "success": True,
            "referral_code": referral_code,
            "referral_url": f"https://psychsync.app/signup?ref={referral_code}",
            "user_id": str(current_user.id),
            "created_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate referral code for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate referral code: {str(e)}"
        )

@router.post("/referrals/convert")
async def track_referral_conversion(
    referral_code: str,
    new_user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Track successful referral conversion
    """
    try:
        # Get referring user from referral code (this would query your database)
        # For now, assume current user is the referrer

        referring_user_id = str(current_user.id)

        await growth_service.track_referral_conversion(
            referral_code=referral_code,
            referring_user_id=referring_user_id,
            new_user_id=new_user_id
        )

        return {
            "success": True,
            "referral_code": referral_code,
            "referring_user_id": referring_user_id,
            "new_user_id": new_user_id,
            "reward_amount": 10.00,
            "converted_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to track referral conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track referral conversion: {str(e)}"
        )

@router.get("/analytics")
async def get_growth_analytics(
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive growth analytics
    """
    try:
        # Only admins can access full analytics
        if not current_user.is_admin:
            # Return user-specific analytics instead
            return await self._get_user_specific_growth_analytics(str(current_user.id))

        # Parse date range
        if date_range_start:
            start_date = datetime.fromisoformat(date_range_start.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow() - timedelta(days=30)

        if date_range_end:
            end_date = datetime.fromisoformat(date_range_end.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()

        analytics = await growth_service.get_growth_analytics(start_date, end_date)

        return analytics

    except Exception as e:
        logger.error(f"Failed to get growth analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve growth analytics: {str(e)}"
        )

async def _get_user_specific_growth_analytics(user_id: str) -> Dict[str, Any]:
    """Get growth analytics specific to a user"""
    try:
        # Get user's journey stage and personalized recommendations
        stage = await growth_service.get_user_journey_stage(user_id)
        user_data = await growth_service._get_user_data(user_id)

        return {
            "user_id": user_id,
            "personalized_analytics": {
                "current_stage": stage.value,
                "stage_progress": self._calculate_stage_progress(stage),
                "recommended_actions": self._get_recommended_actions(stage),
                "next_milestones": self._get_next_milestones(stage)
            },
            "engagement_metrics": {
                "days_since_signup": (datetime.utcnow() - user_data["created_at"]).days,
                "last_login": user_data.get("last_login"),
                "assessment_count": user_data.get("assessment_count", 0),
                "team_count": user_data.get("team_count", 0),
                "subscription_tier": user_data.get("subscription_tier", "free")
            }
        }

    except Exception as e:
        logger.error(f"Failed to get user-specific analytics: {str(e)}")
        raise

def _calculate_stage_progress(stage: UserJourneyStage) -> float:
    """Calculate progress percentage within current stage"""
    # This would calculate how far along the user is in their current stage
    progress_map = {
        UserJourneyStage.NEW_USER: 0.5,      # Just started
        UserJourneyStage.ACTIVATING: 0.7,  # Some activity
        UserJourneyStage.ENGAGED: 0.8,     # Regular activity
        UserJourneyStage.ACTIVE: 0.9,        # Consistent activity
        UserJourneyStage.LOYAL: 1.0,         # Maximum engagement
        UserJourneyStage.AT_RISK: 0.3,      # Inactivity detected
        UserJourneyStage.DORMANT: 0.1        # Extended inactivity
    }
    return progress_map.get(stage, 0.0)

def _get_recommended_actions(stage: UserJourneyStage) -> List[str]:
    """Get recommended actions for user based on journey stage"""
    actions_map = {
        UserJourneyStage.NEW_USER: [
            "Complete your first assessment",
            "Create a team to collaborate",
            "Explore the analytics dashboard",
            "Set up your profile"
        ],
        UserJourneyStage.ACTIVATING: [
            "Try different assessment types",
            "Invite team members",
            "Review your first results",
            "Set up regular assessments"
        ],
        UserJourneyStage.ENGAGED: [
            "Upgrade to advanced analytics",
            "Create custom assessments",
            "Set up team insights",
            "Explore API access"
        ],
        UserJourneyStage.ACTIVE: [
            "Optimize team dynamics",
            "Use advanced reporting",
            "Implement automated workflows",
            "Consider clinical assessment features"
        ],
        UserJourneyStage.LOYAL: [
            "Become a brand advocate",
            "Refer other organizations",
            "Join our partner program",
            "Share success stories"
        ],
        UserJourneyStage.AT_RISK: [
            "Re-engage with a new assessment",
            "Review team insights",
            "Contact customer success",
            "Check out new features"
        ],
        UserJourneyStage.DORMANT: [
            "See what's new since your last visit",
            "Try our reactivation campaign",
            "Consider if features still meet your needs",
            "Schedule a consultation"
        ]
    }
    return actions_map.get(stage, [])

def _get_next_milestones(stage: UserJourneyStage) -> List[str]:
    """Get next milestones for user to achieve"""
    milestones_map = {
        UserJourneyStage.NEW_USER: [
            "Complete first assessment",
            "Create team",
            "Invite 3+ members"
        ],
        UserJourneyStage.ACTIVATING: [
            "Complete 3 assessments",
            "Achieve 50% team participation",
            "Review team insights"
        ],
        UserJourneyStage.ENGAGED: [
            "Upgrade subscription",
            "Use advanced features",
            "Create custom assessment"
        ],
        UserJourneyStage.ACTIVE: [
            "Optimize team performance",
            "Implement workflows",
            "Achieve 90% team engagement"
        ],
        UserJourneyStage.LOYAL: [
            "Refer 5+ new users",
            "Achieve power user status",
            "Join community program"
        ],
        UserJourneyStage.AT_RISK: [
            "Return to active usage",
            "Re-engage team",
            "Complete assessment"
        ],
        UserJourneyStage.DORMANT: [
            "Re-evaluate platform fit",
            "Consider account changes",
            "Contact support"
        ]
    }
    return milestones_map.get(stage, [])

@router.post("/ab-tests")
async def create_a_b_test(
    test_name: str,
    hypothesis: str,
    variant_a_config: Dict[str, Any],
    variant_b_config: Dict[str, Any],
    traffic_split: float = 0.5,
    current_user: User = Depends(get_current_user)
):
    """
    Create A/B test for marketing campaigns
    """
    try:
        # Only admins can create A/B tests
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        ab_test = await growth_service.create_a_b_test(
            test_name=test_name,
            hypothesis=hypothesis,
            variant_a_config=variant_a_config,
            variant_b_config=variant_b_config,
            traffic_split=traffic_split
        )

        return {
            "success": True,
            "test_id": ab_test["test_id"],
            "test_name": test_name,
            "hypothesis": hypothesis,
            "variant_a": ab_test["variant_a"],
            "variant_b": ab_test["variant_b"],
            "traffic_split": traffic_split,
            "status": ab_test["status"],
            "created_at": ab_test["start_date"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create A/B test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}"
        )

@router.get("/triggers", dependencies=[Depends(get_current_user)])
async def list_available_triggers():
    """
    List all available campaign triggers
    """
    try:
        triggers = []

        for trigger in TriggerType:
            triggers.append({
                "value": trigger.value,
                "name": trigger.value.replace("_", " ").title(),
                "description": self._get_trigger_description(trigger)
            })

        return {
            "triggers": triggers,
            "total_count": len(triggers)
        }

    except Exception as e:
        logger.error(f"Failed to list triggers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve triggers"
        )

def _get_trigger_description(trigger: TriggerType) -> str:
    """Get description for campaign trigger"""
    descriptions = {
        TriggerType.USER_SIGNUP: "User creates an account",
        TriggerType.FIRST_LOGIN: "User logs in for the first time",
        TriggerType.ASSESSMENT_COMPLETED: "User completes an assessment",
        TriggerType.TEAM_CREATED: "User creates their first team",
        TriggerType.SUBSCRIPTION_UPGRADED: "User upgrades subscription",
        TriggerType.PAYMENT_FAILED: "Payment method fails",
        TriggerType.TRIAL_EXPIRING: "Trial period is ending",
        TriggerType.FEATURE_USED: "User uses a specific feature",
        TriggerType.INACTIVITY_DETECTED: "User becomes inactive"
    }
    return descriptions.get(trigger, "Unknown trigger")

@router.get("/metrics")
async def list_growth_metrics():
    """
    List all available growth metrics
    """
    try:
        metrics = []

        for metric_name, metric in growth_service.metrics.items():
            metrics.append({
                "name": metric_name,
                "description": metric.description,
                "current_value": metric.current_value,
                "target_value": metric.target_value,
                "period": metric.period,
                "trend": metric.trend,
                "achievement_rate": (metric.current_value / metric.target_value * 100) if metric.target_value > 0 else 0
            })

        return {
            "metrics": metrics,
            "total_count": len(metrics)
        }

    except Exception as e:
        logger.error(f"Failed to list growth metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve growth metrics"
        )

# Webhook endpoints for external integrations
@router.post("/webhooks/user-signup", dependencies=[Depends(get_current_user)])
async def handle_user_signup_webhook(
    user_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Handle user signup webhook for immediate campaign triggering
    """
    try:
        # Extract user information
        user_id = user_data.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )

        # Trigger welcome series campaign
        background_tasks.add_task(
            growth_service.trigger_campaign(
                campaign_id="welcome_series",
                trigger_type=TriggerType.USER_SIGNUP,
                user_id=user_id,
                context_data=user_data
            )
        )

        return {
            "success": True,
            "message": "User signup webhook processed",
            "user_id": user_id,
            "campaigns_triggered": ["welcome_series"]
        }

    except Exception as e:
        logger.error(f"Failed to handle user signup webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )