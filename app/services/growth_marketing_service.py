"""
Customer Acquisition and Growth Marketing Service
Enterprise-grade user acquisition, retention, and growth automation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any
import uuid

from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class CampaignType(Enum):
    """Types of marketing campaigns"""

    ONBOARDING = "onboarding"
    RETENTION = "retention"
    REACTIVATION = "reactivation"
    REFERRAL = "referral"
    PROMOTION = "promotion"
    FEATURE_ADOPTION = "feature_adoption"
    ASSESSMENT_REMINDER = "assessment_reminder"


class UserJourneyStage(Enum):
    """User journey stages for targeted messaging"""

    NEW_USER = "new_user"  # 0-1 days
    ACTIVATING = "activating"  # 1-7 days
    ENGAGED = "engaged"  # 7-30 days
    ACTIVE = "active"  # 30-90 days
    LOYAL = "loyal"  # 90+ days
    AT_RISK = "at_risk"  # Inactive 14-30 days
    DORMANT = "dormant"  # Inactive 30+ days


class TriggerType(Enum):
    """Types of triggers for automated campaigns"""

    USER_SIGNUP = "user_signup"
    FIRST_LOGIN = "first_login"
    ASSESSMENT_COMPLETED = "assessment_completed"
    TEAM_CREATED = "team_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    PAYMENT_FAILED = "payment_failed"
    TRIAL_EXPIRING = "trial_expiring"
    FEATURE_USED = "feature_used"
    INACTIVITY_DETECTED = "inactivity_detected"


@dataclass
class Campaign:
    """Marketing campaign configuration"""

    id: str
    name: str
    campaign_type: CampaignType
    description: str
    is_active: bool = True
    trigger_events: list[TriggerType] = field(default_factory=list)
    target_segments: list[str] = field(default_factory=list)
    email_templates: dict[str, str] = field(default_factory=dict)
    timing_rules: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserSegment:
    """User segment for targeted marketing"""

    id: str
    name: str
    description: str
    criteria: dict[str, Any]  # SQL-like conditions
    estimated_size: int = 0
    growth_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GrowthMetric:
    """Growth metric for tracking"""

    name: str
    description: str
    calculation_method: str
    target_value: float
    current_value: float
    period: str  # daily, weekly, monthly
    trend: str  # up, down, stable
    last_updated: datetime = field(default_factory=datetime.utcnow)


class GrowthMarketingService:
    """
    Comprehensive growth marketing service
    Handles user acquisition, retention, and growth automation
    """

    def __init__(self):
        self.email_service = EmailService()
        self.campaigns = self._initialize_campaigns()
        self.segments = self._initialize_segments()
        self.metrics = self._initialize_metrics()

    def _initialize_campaigns(self) -> dict[str, Campaign]:
        """Initialize predefined marketing campaigns"""
        return {
            "welcome_series": Campaign(
                id="welcome_series",
                name="Welcome Email Series",
                campaign_type=CampaignType.ONBOARDING,
                description="Multi-day onboarding sequence for new users",
                trigger_events=[TriggerType.USER_SIGNUP, TriggerType.FIRST_LOGIN],
                target_segments=["new_users"],
                email_templates={
                    "day1_welcome": "welcome_day1",
                    "day3_assessment_prompt": "assessment_prompt_day3",
                    "day7_tips": "tips_day7",
                    "day14_check_in": "check_in_day14",
                },
                timing_rules={
                    "immediate": ["day1_welcome"],
                    "delay_2_days": ["day3_assessment_prompt"],
                    "delay_6_days": ["day7_tips"],
                    "delay_13_days": ["day14_check_in"],
                },
                conditions={"not_completed_assessment": True, "not_created_team": True},
            ),
            "assessment_reminder": Campaign(
                id="assessment_reminder",
                name="Assessment Reminder",
                campaign_type=CampaignType.FEATURE_ADOPTION,
                description="Remind users to complete assessments",
                trigger_events=[TriggerType.INACTIVITY_DETECTED],
                target_segments=["engaged_users", "new_users"],
                email_templates={
                    "reminder_3_days": "assessment_reminder_3_days",
                    "reminder_7_days": "assessment_reminder_7_days",
                },
                timing_rules={
                    "inactivity_3_days": ["reminder_3_days"],
                    "inactivity_7_days": ["reminder_7_days"],
                },
                conditions={"no_assessment_in_period": True},
            ),
            "trial_expiration": Campaign(
                id="trial_expiration",
                name="Trial Expiration Warning",
                campaign_type=CampaignType.RETENTION,
                description="Warn users about trial expiration",
                trigger_events=[TriggerType.TRIAL_EXPIRING],
                target_segments=["trial_users"],
                email_templates={
                    "warning_3_days": "trial_warning_3_days",
                    "warning_1_day": "trial_warning_1_day",
                    "expired": "trial_expired",
                },
                timing_rules={
                    "3_days_before": ["warning_3_days"],
                    "1_day_before": ["warning_1_day"],
                    "on_expiry": ["expired"],
                },
                conditions={"trial_active": True},
            ),
            "feature_adoption": Campaign(
                id="feature_adoption",
                name="Feature Adoption",
                campaign_type=CampaignType.FEATURE_ADOPTION,
                description="Educate users about advanced features",
                trigger_events=[TriggerType.ASSESSMENT_COMPLETED],
                target_segments=["engaged_users", "active_users"],
                email_templates={
                    "advanced_analytics": "feature_advanced_analytics",
                    "team_insights": "feature_team_insights",
                    "api_access": "feature_api_access",
                },
                timing_rules={
                    "delay_1_day": ["advanced_analytics"],
                    "delay_3_days": ["team_insights"],
                    "delay_7_days": ["api_access"],
                },
                conditions={"has_assessment": True, "feature_not_used": True},
            ),
            "win_back": Campaign(
                id="win_back",
                name="Win Back Campaign",
                campaign_type=CampaignType.REACTIVATION,
                description="Re-engagement for dormant users",
                trigger_events=[TriggerType.INACTIVITY_DETECTED],
                target_segments=["at_risk_users", "dormant_users"],
                email_templates={
                    "missed_you": "win_back_missed_you",
                    "new_features": "win_back_new_features",
                    "special_offer": "win_back_special_offer",
                },
                timing_rules={
                    "dormancy_30_days": ["missed_you"],
                    "dormancy_60_days": ["new_features"],
                    "dormancy_90_days": ["special_offer"],
                },
                conditions={"inactive_period_days": 30},
            ),
            "referral_program": Campaign(
                id="referral_program",
                name="Referral Program",
                campaign_type=CampaignType.REFERRAL,
                description="Encourage user referrals",
                trigger_events=[TriggerType.TEAM_CREATED],
                target_segments=["active_users", "loyal_users"],
                email_templates={
                    "referral_invite": "referral_invite",
                    "referral_reminder": "referral_reminder",
                },
                timing_rules={
                    "immediate": ["referral_invite"],
                    "delay_7_days": ["referral_reminder"],
                },
                conditions={"has_referral_code": True},
            ),
        }

    def _initialize_segments(self) -> dict[str, UserSegment]:
        """Initialize predefined user segments"""
        return {
            "new_users": UserSegment(
                id="new_users",
                name="New Users",
                description="Users who joined in the last 7 days",
                criteria={
                    "created_at": {"operator": ">=", "value": datetime.utcnow() - timedelta(days=7)}
                },
            ),
            "trial_users": UserSegment(
                id="trial_users",
                name="Trial Users",
                description="Users on free trial",
                criteria={
                    "subscription_tier": "free",
                    "created_at": {
                        "operator": ">=",
                        "value": datetime.utcnow() - timedelta(days=14),
                    },
                },
            ),
            "engaged_users": UserSegment(
                id="engaged_users",
                name="Engaged Users",
                description="Users with recent activity",
                criteria={
                    "last_login": {
                        "operator": ">=",
                        "value": datetime.utcnow() - timedelta(days=7),
                    },
                    "assessment_count": {"operator": ">", "value": 0},
                },
            ),
            "at_risk_users": UserSegment(
                id="at_risk_users",
                name="At Risk Users",
                description="Users inactive for 14-30 days",
                criteria={
                    "last_login": {
                        "operator": "<",
                        "value": datetime.utcnow() - timedelta(days=14),
                    },
                    "last_login": {
                        "operator": ">=",
                        "value": datetime.utcnow() - timedelta(days=30),
                    },
                },
            ),
            "dormant_users": UserSegment(
                id="dormant_users",
                name="Dormant Users",
                description="Users inactive for 30+ days",
                criteria={
                    "last_login": {"operator": "<", "value": datetime.utcnow() - timedelta(days=30)}
                },
            ),
            "loyal_users": UserSegment(
                id="loyal_users",
                name="Loyal Users",
                description="Users active for 90+ days",
                criteria={
                    "created_at": {
                        "operator": "<=",
                        "value": datetime.utcnow() - timedelta(days=90),
                    },
                    "last_login": {
                        "operator": ">=",
                        "value": datetime.utcnow() - timedelta(days=14),
                    },
                },
            ),
        }

    def _initialize_metrics(self) -> dict[str, GrowthMetric]:
        """Initialize growth metrics"""
        return {
            "user_acquisition_rate": GrowthMetric(
                name="User Acquisition Rate",
                description="New users per day/week/month",
                calculation_method="new_users / time_period",
                target_value=50.0,
                current_value=0.0,
                period="daily",
            ),
            "activation_rate": GrowthMetric(
                name="Activation Rate",
                description="Percentage of users who complete onboarding",
                calculation_method="activated_users / new_users",
                target_value=0.8,
                current_value=0.0,
                period="monthly",
            ),
            "retention_rate": GrowthMetric(
                name="Retention Rate",
                description="Percentage of users retained after 30 days",
                calculation_method="users_after_30_days / users_at_signup",
                target_value=0.85,
                current_value=0.0,
                period="monthly",
            ),
            "churn_rate": GrowthMetric(
                name="Churn Rate",
                description="Percentage of users who cancel",
                calculation_method="canceled_users / total_users",
                target_value=0.05,
                current_value=0.0,
                period="monthly",
            ),
            "free_to_paid_conversion": GrowthMetric(
                name="Free to Paid Conversion",
                description="Percentage of free users who upgrade",
                calculation_method="paid_upgrades / free_users",
                target_value=0.05,
                current_value=0.0,
                period="monthly",
            ),
            "referral_rate": GrowthMetric(
                name="Referral Rate",
                description="Percentage of users who refer others",
                calculation_method="referring_users / active_users",
                target_value=0.15,
                current_value=0.0,
                period="monthly",
            ),
        }

    async def trigger_campaign(
        self,
        campaign_id: str,
        trigger_type: TriggerType,
        user_id: str,
        context_data: dict[str, Any] | None = None,
    ) -> bool:
        """Trigger a marketing campaign for a specific user"""
        try:
            if campaign_id not in self.campaigns:
                logger.error(f"Campaign {campaign_id} not found")
                return False

            campaign = self.campaigns[campaign_id]

            if not campaign.is_active:
                logger.info(f"Campaign {campaign_id} is inactive")
                return False

            if trigger_type not in campaign.trigger_events:
                logger.info(f"Trigger {trigger_type} not configured for campaign {campaign_id}")
                return False

            # Get user data (this would query your database)
            user_data = await self._get_user_data(user_id)

            # Check if user matches target segments
            if not await self._user_matches_segments(user_data, campaign.target_segments):
                logger.info(
                    f"User {user_id} does not match target segments for campaign {campaign_id}"
                )
                return False

            # Check campaign conditions
            if not await self._check_campaign_conditions(user_data, campaign.conditions):
                logger.info(f"User {user_id} does not meet conditions for campaign {campaign_id}")
                return False

            # Execute campaign timing rules
            await self._execute_campaign_timing(user_id, campaign, context_data)

            logger.info(f"Triggered campaign {campaign_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger campaign {campaign_id} for user {user_id}: {e!s}")
            return False

    async def _get_user_data(self, user_id: str) -> dict[str, Any]:
        """Get user data for campaign targeting"""
        try:
            # This would query your database for user information
            # For now, return a basic structure

            return {
                "user_id": user_id,
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "created_at": datetime.utcnow() - timedelta(days=5),
                "last_login": datetime.utcnow() - timedelta(hours=2),
                "subscription_tier": "free",
                "assessment_count": 0,
                "team_count": 0,
                "has_referral_code": False,
                "trial_expires": None,
            }

        except Exception as e:
            logger.error(f"Failed to get user data for {user_id}: {e!s}")
            return {}

    async def _user_matches_segments(
        self, user_data: dict[str, Any], target_segments: list[str]
    ) -> bool:
        """Check if user matches any target segments"""
        try:
            if not target_segments:
                return True

            user_stage = self._determine_user_stage(user_data)

            # Map segments to stages
            segment_stage_mapping = {
                "new_users": [UserJourneyStage.NEW_USER, UserJourneyStage.ACTIVATING],
                "trial_users": [UserJourneyStage.ACTIVATING, UserJourneyStage.ENGAGED],
                "engaged_users": [UserJourneyStage.ENGAGED, UserJourneyStage.ACTIVE],
                "at_risk_users": [UserJourneyStage.AT_RISK],
                "dormant_users": [UserJourneyStage.DORMANT],
                "loyal_users": [UserJourneyStage.LOYAL],
            }

            for segment in target_segments:
                if segment in segment_stage_mapping:
                    if user_stage in segment_stage_mapping[segment]:
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to check user segments: {e!s}")
            return False

    def _determine_user_stage(self, user_data: dict[str, Any]) -> UserJourneyStage:
        """Determine user's journey stage"""
        try:
            now = datetime.utcnow()
            created_at = user_data.get("created_at", now)
            last_login = user_data.get("last_login", now)

            days_since_creation = (now - created_at).days
            days_since_last_login = (now - last_login).days

            if days_since_creation <= 1:
                return UserJourneyStage.NEW_USER
            if days_since_creation <= 7:
                return UserJourneyStage.ACTIVATING
            if days_since_last_login <= 7:
                if days_since_creation <= 30:
                    return UserJourneyStage.ENGAGED
                return UserJourneyStage.ACTIVE
            if days_since_last_login <= 30:
                return UserJourneyStage.AT_RISK
            if days_since_creation >= 90:
                return UserJourneyStage.LOYAL
            return UserJourneyStage.DORMANT

        except Exception as e:
            logger.error(f"Failed to determine user stage: {e!s}")
            return UserJourneyStage.DORMANT

    async def _check_campaign_conditions(
        self, user_data: dict[str, Any], conditions: dict[str, Any]
    ) -> bool:
        """Check if user meets campaign conditions"""
        try:
            for condition_key, condition_value in conditions.items():
                if condition_key == "not_completed_assessment":
                    assessment_count = user_data.get("assessment_count", 0)
                    if assessment_count > 0:
                        return False

                elif condition_key == "not_created_team":
                    team_count = user_data.get("team_count", 0)
                    if team_count > 0:
                        return False

                elif condition_key == "no_assessment_in_period":
                    # This would require more complex logic
                    pass

                elif condition_key == "trial_active":
                    subscription_tier = user_data.get("subscription_tier", "free")
                    if subscription_tier != "free":
                        return False

                elif condition_key == "has_assessment":
                    assessment_count = user_data.get("assessment_count", 0)
                    if assessment_count == 0:
                        return False

                elif condition_key == "feature_not_used":
                    # This would require feature usage tracking
                    pass

                elif condition_key == "has_referral_code":
                    has_referral = user_data.get("has_referral_code", False)
                    if not has_referral:
                        return False

                elif condition_key == "inactive_period_days":
                    days_inactive = condition_value
                    last_login = user_data.get("last_login", datetime.utcnow())
                    if (datetime.utcnow() - last_login).days < days_inactive:
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to check campaign conditions: {e!s}")
            return False

    async def _execute_campaign_timing(
        self, user_id: str, campaign: Campaign, context_data: dict[str, Any] | None = None
    ):
        """Execute campaign timing rules and send emails"""
        try:
            for timing_rule, template_keys in campaign.timing_rules.items():
                if timing_rule == "immediate":
                    for template_key in template_keys:
                        await self._send_campaign_email(
                            user_id, template_key, campaign, context_data
                        )

                elif timing_rule.startswith("delay_"):
                    # Parse delay period
                    delay_parts = timing_rule.split("_")
                    if len(delay_parts) == 3 and delay_parts[1].isdigit():
                        delay_days = int(delay_parts[1])

                        # Schedule delayed email (this would use a task queue)
                        await self._schedule_delayed_email(
                            user_id=user_id,
                            template_keys=template_keys,
                            campaign=campaign,
                            delay_days=delay_days,
                            context_data=context_data,
                        )

        except Exception as e:
            logger.error(f"Failed to execute campaign timing: {e!s}")

    async def _send_campaign_email(
        self,
        user_id: str,
        template_key: str,
        campaign: Campaign,
        context_data: dict[str, Any] | None = None,
    ):
        """Send campaign email"""
        try:
            # Get user data for email personalization
            user_data = await self._get_user_data(user_id)

            # Build email context
            email_context = {
                "user": user_data,
                "campaign": {
                    "id": campaign.id,
                    "name": campaign.name,
                    "description": campaign.description,
                },
                "template_key": template_key,
                "personalization_data": context_data or {},
            }

            # Send email using your email service
            await self.email_service.send_campaign_email(
                template_name=campaign.email_templates.get(template_key),
                recipient=user_data["email"],
                context=email_context,
            )

            # Log email sent for analytics
            await self._log_campaign_email(user_id, campaign.id, template_key)

        except Exception as e:
            logger.error(f"Failed to send campaign email {template_key} to {user_id}: {e!s}")

    async def _schedule_delayed_email(
        self,
        user_id: str,
        template_keys: list[str],
        campaign: Campaign,
        delay_days: int,
        context_data: dict[str, Any] | None = None,
    ):
        """Schedule delayed campaign emails"""
        try:
            # This would integrate with your task queue (Celery, etc.)
            # For now, we'll just log the scheduling

            scheduled_date = datetime.utcnow() + timedelta(days=delay_days)

            logger.info(f"Scheduled email for user {user_id} on {scheduled_date}")

            # In a real implementation, you would:
            # 1. Create a task in your task queue
            # 2. Store the task with execution date
            # 3. Your task processor would handle the actual email sending

        except Exception as e:
            logger.error(f"Failed to schedule delayed email: {e!s}")

    async def _log_campaign_email(self, user_id: str, campaign_id: str, template_key: str):
        """Log campaign email for analytics"""
        try:
            # This would save to your analytics database
            # For now, we'll just log

            log_entry = {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "template_key": template_key,
                "sent_at": datetime.utcnow().isoformat(),
                "event_id": str(uuid.uuid4()),
            }

            logger.info(f"Campaign email logged: {log_entry}")

        except Exception as e:
            logger.error(f"Failed to log campaign email: {e!s}")

    async def get_user_journey_stage(self, user_id: str) -> UserJourneyStage:
        """Get user's current journey stage"""
        try:
            user_data = await self._get_user_data(user_id)
            return self._determine_user_stage(user_data)

        except Exception as e:
            logger.error(f"Failed to get user journey stage for {user_id}: {e!s}")
            return UserJourneyStage.DORMANT

    async def generate_referral_code(self, user_id: str) -> str:
        """Generate unique referral code for user"""
        try:
            # Generate unique code
            referral_code = f"PSYC{str(uuid.uuid4())[:8].upper()}"

            # Store referral code in database
            # Note: This would require updating your user model

            return referral_code

        except Exception as e:
            logger.error(f"Failed to generate referral code for {user_id}: {e!s}")
            raise

    async def track_referral_conversion(
        self, referral_code: str, referring_user_id: str, new_user_id: str
    ):
        """Track successful referral conversion"""
        try:
            # Verify referral code exists and is valid
            # Award referral credits
            # Update referral analytics

            conversion_data = {
                "referral_code": referral_code,
                "referring_user_id": referring_user_id,
                "new_user_id": new_user_id,
                "conversion_date": datetime.utcnow().isoformat(),
                "reward_amount": 10.00,  # Could be configurable
            }

            logger.info(f"Referral conversion tracked: {conversion_data}")

            # Send notification to referring user
            await self._send_referral_notification(referring_user_id, new_user_id)

        except Exception as e:
            logger.error(f"Failed to track referral conversion: {e!s}")
            raise

    async def _send_referral_notification(self, referring_user_id: str, new_user_id: str):
        """Send notification about successful referral"""
        try:
            # Get user data for personalization
            referring_user = await self._get_user_data(referring_user_id)
            new_user = await self._get_user_data(new_user_id)

            notification_context = {
                "referring_user": referring_user,
                "new_user": new_user,
                "reward_amount": 10.00,
            }

            # Send notification email
            await self.email_service.send_referral_notification(
                recipient=referring_user["email"], context=notification_context
            )

        except Exception as e:
            logger.error(f"Failed to send referral notification: {e!s}")

    async def get_growth_analytics(
        self, date_range_start: datetime, date_range_end: datetime
    ) -> dict[str, Any]:
        """Generate comprehensive growth analytics"""
        try:
            analytics = {
                "period": {
                    "start": date_range_start.isoformat(),
                    "end": date_range_end.isoformat(),
                },
                "metrics": {},
                "campaign_performance": {},
                "user_journey_stages": {},
                "referral_analytics": {},
                "conversion_funnels": {},
            }

            # Calculate metrics
            for metric_name, metric in self.metrics.items():
                analytics["metrics"][metric_name] = {
                    "name": metric.name,
                    "current_value": metric.current_value,
                    "target_value": metric.target_value,
                    "trend": metric.trend,
                    "achievement_rate": (metric.current_value / metric.target_value) * 100
                    if metric.target_value > 0
                    else 0,
                }

            # Campaign performance
            for campaign_id, campaign in self.campaigns.items():
                if campaign.is_active:
                    analytics["campaign_performance"][campaign_id] = {
                        "name": campaign.name,
                        "type": campaign.campaign_type.value,
                        "emails_sent": 0,  # Would query database
                        "open_rate": 0.0,
                        "click_rate": 0.0,
                        "conversion_rate": 0.0,
                    }

            # User journey stages distribution
            stage_counts = {}
            for stage in UserJourneyStage:
                stage_counts[stage.value] = 0  # Would query database

            analytics["user_journey_stages"] = stage_counts

            return analytics

        except Exception as e:
            logger.error(f"Failed to generate growth analytics: {e!s}")
            raise

    async def create_a_b_test(
        self,
        test_name: str,
        hypothesis: str,
        variant_a_config: dict[str, Any],
        variant_b_config: dict[str, Any],
        traffic_split: float = 0.5,
    ) -> dict[str, Any]:
        """Create A/B test for marketing campaigns"""
        try:
            test_id = str(uuid.uuid4())

            ab_test = {
                "test_id": test_id,
                "test_name": test_name,
                "hypothesis": hypothesis,
                "variant_a": {
                    "name": "Control",
                    "config": variant_a_config,
                    "traffic_percentage": traffic_split * 100,
                },
                "variant_b": {
                    "name": "Treatment",
                    "config": variant_b_config,
                    "traffic_percentage": (1 - traffic_split) * 100,
                },
                "status": "active",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": None,
                "sample_size_target": 1000,
                "statistical_significance": 0.95,
            }

            logger.info(f"Created A/B test: {test_id}")

            return ab_test

        except Exception as e:
            logger.error(f"Failed to create A/B test: {e!s}")
            raise


# Initialize service instance
growth_service = GrowthMarketingService()
