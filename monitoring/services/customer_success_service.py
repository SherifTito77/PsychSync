#!/usr/bin/env python3
"""
Customer Success Automation Service
Automated onboarding flows, health monitoring, and customer success playbooks
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class CustomerHealthStatus(Enum):
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    CHURNED = "churned"
    GROWING = "growing"

class OnboardingStage(Enum):
    SIGNED_UP = "signed_up"
    DASHBOARD_CREATED = "dashboard_created"
    FIRST_INSIGHT_VIEWED = "first_insight_viewed"
    TEAM_INVITED = "team_invited"
    INTEGRATIONS_CONNECTED = "integrations_connected"
    VALUE_REALIZED = "value_realized"
    FULLY_ADOPTED = "fully_adopted"

class SuccessMilestone(Enum):
    SETUP_COMPLETED = "setup_completed"
    FIRST_WEEK_ACTIVE = "first_week_active"
    MONTHLY_VALUE_DEMONSTRATED = "monthly_value_demonstrated"
    TEAM_ADOPTION = "team_adoption"
    UPGRADE_QUALIFIED = "upgrade_qualified"
    EXECUTIVE_BUY_IN = "executive_buy_in"

@dataclass
class CustomerProfile:
    customer_id: str
    email: str
    company_name: str
    tier: str
    signup_date: datetime
    industry: str
    team_size: int
    annual_revenue: float
    use_case: str
    success_metrics: List[str]
    risk_factors: List[str]
    growth_indicators: List[str]
    support_tickets: int = 0
    last_login: Optional[datetime] = None
    health_score: float = 0.0
    health_status: CustomerHealthStatus = CustomerHealthStatus.HEALTHY

@dataclass
class OnboardingFlow:
    id: str
    name: str
    description: str
    stages: List[Dict[str, Any]]
    target_tiers: List[str]
    automated_actions: List[Dict[str, Any]]
    success_criteria: List[str]
    average_completion_days: int

@dataclass
class HealthMetric:
    name: str
    value: float
    threshold_good: float
    threshold_warning: float
    weight: float
    last_updated: datetime

@dataclass
class SuccessPlay:
    id: str
    name: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    expected_outcome: str
    success_metrics: List[str]
    timeline_days: int

class CustomerSuccessService:
    """Automated customer success with health monitoring and proactive engagement"""

    def __init__(self):
        self.customer_profiles = {}
        self.onboarding_flows = self._initialize_onboarding_flows()
        self.health_metrics = self._initialize_health_metrics()
        self.success_plays = self._initialize_success_plays()
        self.engagement_history = []

    def _initialize_onboarding_flows(self) -> Dict[str, OnboardingFlow]:
        """Initialize automated onboarding flows"""
        flows = {}

        # Free Tier Onboarding
        flows["free_tier_onboarding"] = OnboardingFlow(
            id="free_tier_onboarding",
            name="Free Tier Quick Start",
            description="Rapid onboarding focused on immediate value realization",
            stages=[
                {
                    "stage": OnboardingStage.SIGNED_UP.value,
                    "duration_hours": 0,
                    "objectives": ["Welcome email sent", "Account setup confirmation"],
                    "automated_actions": [
                        {"type": "email", "template": "welcome_free_tier", "delay_hours": 0},
                        {"type": "in_app", "message": "Let's create your first dashboard", "delay_hours": 0}
                    ]
                },
                {
                    "stage": OnboardingStage.DASHBOARD_CREATED.value,
                    "duration_hours": 24,
                    "objectives": ["Dashboard setup completed", "Initial insights generated"],
                    "automated_actions": [
                        {"type": "email", "template": "first_insight_ready", "trigger": "dashboard_created"},
                        {"type": "in_app", "message": "Your competitive advantage is ready", "delay_hours": 1}
                    ]
                },
                {
                    "stage": OnboardingStage.FIRST_INSIGHT_VIEWED.value,
                    "duration_hours": 48,
                    "objectives": ["First insight viewed", "Value demonstrated"],
                    "automated_actions": [
                        {"type": "email", "template": "value_realization", "trigger": "insight_viewed"},
                        {"type": "check_in", "message": "How valuable was your first insight?", "delay_hours": 24}
                    ]
                },
                {
                    "stage": OnboardingStage.VALUE_REALIZED.value,
                    "duration_hours": 168,  # 1 week
                    "objectives": ["Customer recognizes value", "Active engagement established"],
                    "automated_actions": [
                        {"type": "email", "template": "weekly_success", "delay_hours": 168},
                        {"type": "upgrade_nudge", "condition": "high_usage", "delay_hours": 144}
                    ]
                }
            ],
            target_tiers=["free"],
            automated_actions=[
                {"type": "progress_tracking", "frequency": "daily"},
                {"type": "health_monitoring", "frequency": "continuous"},
                {"type": "upgrade_eligibility_check", "frequency": "weekly"}
            ],
            success_criteria=[
                "Dashboard created within 48 hours",
                "First insight viewed within 72 hours",
                "Weekly active engagement",
                "Upgrade qualified within 30 days"
            ],
            average_completion_days=7
        )

        # Growth Tier Onboarding
        flows["growth_tier_onboarding"] = OnboardingFlow(
            id="growth_tier_onboarding",
            name="Growth Tier Success Acceleration",
            description="Comprehensive onboarding for paid customers with team features",
            stages=[
                {
                    "stage": OnboardingStage.SIGNED_UP.value,
                    "duration_hours": 0,
                    "objectives": ["Premium features unlocked", "Success manager assigned"],
                    "automated_actions": [
                        {"type": "email", "template": "welcome_growth_tier", "delay_hours": 0},
                        {"type": "human_touch", "action": "assign_success_manager", "delay_hours": 4},
                        {"type": "onboarding_call", "schedule": "automated", "delay_hours": 24}
                    ]
                },
                {
                    "stage": OnboardingStage.DASHBOARD_CREATED.value,
                    "duration_hours": 24,
                    "objectives": ["Advanced dashboard setup", "Custom metrics configured"],
                    "automated_actions": [
                        {"type": "email", "template": "advanced_features_guide", "delay_hours": 2},
                        {"type": "in_app", "message": "Explore premium features", "delay_hours": 4}
                    ]
                },
                {
                    "stage": OnboardingStage.TEAM_INVITED.value,
                    "duration_hours": 72,
                    "objectives": ["Team members invited", "Collaboration features activated"],
                    "automated_actions": [
                        {"type": "email", "template": "team_collaboration_guide", "trigger": "team_invited"},
                        {"type": "team_usage_report", "frequency": "weekly", "delay_hours": 168}
                    ]
                },
                {
                    "stage": OnboardingStage.INTEGRATIONS_CONNECTED.value,
                    "duration_hours": 120,  # 5 days
                    "objectives": ["Key integrations connected", "Automated workflows active"],
                    "automated_actions": [
                        {"type": "email", "template": "integration_success_stories", "trigger": "integration_connected"},
                        {"type": "integration_health_check", "frequency": "daily"}
                    ]
                },
                {
                    "stage": OnboardingStage.FULLY_ADOPTED.value,
                    "duration_hours": 336,  # 14 days
                    "objectives": ["Full feature adoption", "ROI demonstrated", "Expansion identified"],
                    "automated_actions": [
                        {"type": "email", "template": "success_celebration", "delay_hours": 336},
                        {"type": "roi_review", "schedule": "automated", "delay_hours": 384},
                        {"type": "expansion_planning", "schedule": "30_day_review", "delay_hours": 720}
                    ]
                }
            ],
            target_tiers=["growth", "enterprise"],
            automated_actions=[
                {"type": "success_manager_check_in", "frequency": "weekly"},
                {"type": "roi_tracking", "frequency": "continuous"},
                {"type": "expansion_opportunity_detection", "frequency": "weekly"},
                {"type": "executive_reporting", "frequency": "monthly"}
            ],
            success_criteria=[
                "Advanced features used within 7 days",
                "Team adoption >50% within 14 days",
                "Key integrations connected within 30 days",
                "ROI >100x within 60 days"
            ],
            average_completion_days=14
        )

        # Enterprise Onboarding
        flows["enterprise_onboarding"] = OnboardingFlow(
            id="enterprise_onboarding",
            name="Enterprise Strategic Implementation",
            description="White-glove onboarding for enterprise customers with custom requirements",
            stages=[
                {
                    "stage": OnboardingStage.SIGNED_UP.value,
                    "duration_hours": 0,
                    "objectives": ["Executive sponsor confirmed", "Technical requirements gathered"],
                    "automated_actions": [
                        {"type": "email", "template": "enterprise_welcome", "delay_hours": 0},
                        {"type": "human_touch", "action": "assign_enterprise_team", "delay_hours": 2},
                        {"type": "discovery_call", "priority": "high", "delay_hours": 24}
                    ]
                },
                {
                    "stage": OnboardingStage.DASHBOARD_CREATED.value,
                    "duration_hours": 48,
                    "objectives": ["Custom dashboards designed", "Executive reporting configured"],
                    "automated_actions": [
                        {"type": "email", "template": "custom_dashboard_review", "trigger": "dashboard_created"},
                        {"type": "executive_demonstration", "schedule": "automated", "delay_hours": 72}
                    ]
                },
                {
                    "stage": OnboardingStage.TEAM_INVITED.value,
                    "duration_hours": 96,
                    "objectives": ["Enterprise team rollout", "Training sessions conducted"],
                    "automated_actions": [
                        {"type": "email", "template": "enterprise_training_schedule", "trigger": "team_invited"},
                        {"type": "training_session", "type": "webinar", "frequency": "weekly"}
                    ]
                },
                {
                    "stage": OnboardingStage.INTEGRATIONS_CONNECTED.value,
                    "duration_hours": 168,  # 1 week
                    "objectives": ["Enterprise integrations deployed", "SSO configured", "Security approved"],
                    "automated_actions": [
                        {"type": "email", "template": "enterprise_security_confirmation", "trigger": "security_setup"},
                        {"type": "security_audit", "frequency": "monthly"},
                        {"type": "compliance_reporting", "frequency": "quarterly"}
                    ]
                },
                {
                    "stage": OnboardingStage.EXECUTIVE_BUY_IN.value,
                    "duration_hours": 336,  # 14 days
                    "objectives": ["Executive value demonstrated", "Strategic partnership established"],
                    "automated_actions": [
                        {"type": "email", "template": "executive_business_review", "delay_hours": 336},
                        {"type": "quarterly_business_review", "schedule": "automated", "recurring": True},
                        {"type": "strategic_planning", "frequency": "quarterly"}
                    ]
                },
                {
                    "stage": OnboardingStage.FULLY_ADOPTED.value,
                    "duration_hours": 720,  # 30 days
                    "objectives": ["Enterprise-wide adoption", "Custom KPIs tracked", "Strategic value proven"],
                    "automated_actions": [
                        {"type": "email", "template": "enterprise_success_celebration", "delay_hours": 720},
                        {"type": "account_review", "frequency": "monthly"},
                        {"type": "strategic_growth_planning", "frequency": "quarterly"}
                    ]
                }
            ],
            target_tiers=["enterprise"],
            automated_actions=[
                {"type": "dedicated_success_manager", "availability": "24/7"},
                {"type": "executive_sponsor_check_in", "frequency": "monthly"},
                {"type": "strategic_account_review", "frequency": "quarterly"},
                {"type": "custom_success_metrics", "frequency": "continuous"}
            ],
            success_criteria=[
                "Executive dashboards active within 5 days",
                "80% team adoption within 30 days",
                "Custom integrations deployed within 14 days",
                "Strategic value demonstrated within 60 days"
            ],
            average_completion_days=30
        )

        return flows

    def _initialize_health_metrics(self) -> Dict[str, HealthMetric]:
        """Initialize customer health tracking metrics"""
        return {
            "login_frequency": HealthMetric(
                name="Login Frequency",
                value=0.0,
                threshold_good=0.8,  # 80% of expected login frequency
                threshold_warning=0.5,
                weight=0.25,
                last_updated=datetime.now()
            ),
            "feature_adoption": HealthMetric(
                name="Feature Adoption",
                value=0.0,
                threshold_good=0.7,  # 70% of key features used
                threshold_warning=0.4,
                weight=0.2,
                last_updated=datetime.now()
            ),
            "team_engagement": HealthMetric(
                name="Team Engagement",
                value=0.0,
                threshold_good=0.6,  # 60% of team members active
                threshold_warning=0.3,
                weight=0.15,
                last_updated=datetime.now()
            ),
            "roi_realization": HealthMetric(
                name="ROI Realization",
                value=0.0,
                threshold_good=100.0,  # 100x ROI achieved
                threshold_warning=50.0,
                weight=0.2,
                last_updated=datetime.now()
            ),
            "support_sentiment": HealthMetric(
                name="Support Sentiment",
                value=0.0,
                threshold_good=0.9,  # 90% positive sentiment
                threshold_warning=0.7,
                weight=0.1,
                last_updated=datetime.now()
            ),
            "growth_indicators": HealthMetric(
                name="Growth Indicators",
                value=0.0,
                threshold_good=0.5,  # 50% of growth indicators present
                threshold_warning=0.2,
                weight=0.1,
                last_updated=datetime.now()
            )
        }

    def _initialize_success_plays(self) -> Dict[str, SuccessPlay]:
        """Initialize customer success intervention plays"""
        plays = {}

        # At-Risk Intervention
        plays["at_risk_intervention"] = SuccessPlay(
            id="at_risk_intervention",
            name="At-Risk Customer Intervention",
            trigger_conditions={
                "health_score_below": 40,
                "login_frequency_below": 0.3,
                "days_inactive_above": 14,
                "support_tickets_above": 3
            },
            actions=[
                {"type": "priority_support", "action": "assign_dedicated_support"},
                {"type": "outreach", "method": "phone_call", "priority": "high"},
                {"type": "success_plan", "action": "create_recovery_plan"},
                {"type": "executive_escalation", "condition": "high_value_customer"},
                {"type": "value_demonstration", "action": "custom_roi_analysis"}
            ],
            expected_outcome="Recovery to healthy status within 30 days",
            success_metrics=[
                "Health score improves to >60",
                "Login frequency increases to >50%",
                "Customer re-engages with key features",
                "Positive support interactions"
            ],
            timeline_days=30
        )

        # Growth Acceleration
        plays["growth_acceleration"] = SuccessPlay(
            id="growth_acceleration",
            name="High-Potential Growth Acceleration",
            trigger_conditions={
                "health_score_above": 80,
                "usage_growth_rate_above": 0.2,  # 20% month-over-month
                "team_expansion_detected": True,
                "roi_above_threshold": True
            },
            actions=[
                {"type": "success_manager_engagement", "frequency": "bi-weekly"},
                {"type": "expansion_opportunity", "action": "identify_upgrade_triggers"},
                {"type": "advocacy_program", "action": "invite_to_customer_advisory"},
                {"type": "case_study_development", "action": "document_success_story"},
                {"type": "executive_business_review", "schedule": "quarterly"}
            ],
            expected_outcome="Expansion to higher tier within 90 days",
            success_metrics=[
                "Upgrade to next tier completed",
                "Team size increases by >50%",
                "ROI >200x achieved",
                "Customer advocacy activities initiated"
            ],
            timeline_days=90
        )

        # New Customer Success
        plays["new_customer_success"] = SuccessPlay(
            id="new_customer_success",
            name="New Customer Success Acceleration",
            trigger_conditions={
                "customer_age_days": "<=30",
                "onboarding_stage": "in_progress",
                "first_month_active": True
            },
            actions=[
                {"type": "onboarding_support", "frequency": "daily_check_ins"},
                {"type": "best_practice_sharing", "method": "targeted_content"},
                {"type": "peer_connection", "action": "connect_with_similar_customers"},
                {"type": "quick_win_identification", "action": "find_immediate_value_opportunities"},
                {"type": "success_planning", "action": "30_day_success_plan"}
            ],
            expected_outcome="Successful onboarding completion with 90% retention",
            success_metrics=[
                "Onboarding completed on schedule",
                "First month usage targets met",
                "Customer satisfaction score >8/10",
                "Renewal likelihood >90%"
            ],
            timeline_days=30
        )

        # Executive Engagement
        plays["executive_engagement"] = SuccessPlay(
            id="executive_engagement",
            name="Executive Stakeholder Engagement",
            trigger_conditions={
                "account_tier": "enterprise",
                "revenue_impact_above": 100000,
                "strategic_importance": "high",
                "contract_renewal_within": "90_days"
            },
            actions=[
                {"type": "executive_business_review", "schedule": "quarterly"},
                {"type": "strategic_planning", "action": "joint_success_planning"},
                {"type": "industry_intelligence", "action": "custom_market_analysis"},
                {"type": "innovation_workshop", "schedule": "semi_annual"},
                {"type": "executive_sponsor_program", "action": "executive_matchmaking"}
            ],
            expected_outcome="Strategic partnership with multi-year commitment",
            success_metrics=[
                "Executive satisfaction score >9/10",
                "Strategic value documented",
                "Multi-year contract renewal",
                "Joint innovation initiatives launched"
            ],
            timeline_days=180
        )

        return plays

    def create_customer_profile(self, customer_data: Dict[str, Any]) -> CustomerProfile:
        """Create and initialize customer success profile"""
        customer_id = customer_data["customer_id"]

        profile = CustomerProfile(
            customer_id=customer_id,
            email=customer_data["email"],
            company_name=customer_data["company_name"],
            tier=customer_data.get("tier", "free"),
            signup_date=customer_data.get("signup_date", datetime.now()),
            industry=customer_data.get("industry", "technology"),
            team_size=customer_data.get("team_size", 10),
            annual_revenue=customer_data.get("annual_revenue", 1000000),
            use_case=customer_data.get("use_case", "business_intelligence"),
            success_metrics=customer_data.get("success_metrics", [
                "user_satisfaction",
                "revenue_protection",
                "competitive_advantage"
            ]),
            risk_factors=customer_data.get("risk_factors", []),
            growth_indicators=customer_data.get("growth_indicators", [])
        )

        self.customer_profiles[customer_id] = profile
        self._start_onboarding_flow(customer_id)

        return profile

    def _start_onboarding_flow(self, customer_id: str):
        """Start appropriate onboarding flow based on customer profile"""
        profile = self.customer_profiles[customer_id]

        # Select appropriate onboarding flow
        if profile.tier == "free":
            flow_id = "free_tier_onboarding"
        elif profile.tier == "enterprise":
            flow_id = "enterprise_onboarding"
        else:
            flow_id = "growth_tier_onboarding"

        flow = self.onboarding_flows.get(flow_id)
        if flow:
            self._execute_onboarding_stage(customer_id, flow, 0)

    def _execute_onboarding_stage(self, customer_id: str, flow: OnboardingFlow, stage_index: int):
        """Execute current onboarding stage with automated actions"""
        if stage_index >= len(flow.stages):
            return

        stage = flow.stages[stage_index]

        # Execute automated actions for this stage
        for action in stage["automated_actions"]:
            self._execute_automated_action(customer_id, action)

        # Schedule next stage
        next_stage_delay = stage.get("duration_hours", 24)
        # In production, this would schedule the next stage execution
        logger.info(f"Scheduled next onboarding stage for {customer_id} in {next_stage_delay} hours")

    def _execute_automated_action(self, customer_id: str, action: Dict[str, Any]):
        """Execute automated action based on action type"""
        action_type = action.get("type")

        if action_type == "email":
            template = action.get("template")
            delay_hours = action.get("delay_hours", 0)
            self._send_automated_email(customer_id, template, delay_hours)

        elif action_type == "in_app":
            message = action.get("message")
            delay_hours = action.get("delay_hours", 0)
            self._send_in_app_message(customer_id, message, delay_hours)

        elif action_type == "human_touch":
            action_type = action.get("action")
            delay_hours = action.get("delay_hours", 0)
            self._schedule_human_touch(customer_id, action_type, delay_hours)

        elif action_type == "check_in":
            message = action.get("message")
            delay_hours = action.get("delay_hours", 0)
            self._schedule_check_in(customer_id, message, delay_hours)

        # Log action for tracking
        self.engagement_history.append({
            "customer_id": customer_id,
            "action": action,
            "executed_at": datetime.now(),
            "status": "executed"
        })

    def _send_automated_email(self, customer_id: str, template: str, delay_hours: int):
        """Send automated onboarding email"""
        # In production, this would integrate with email marketing service
        logger.info(f"Scheduling email template '{template}' for {customer_id} in {delay_hours} hours")

    def _send_in_app_message(self, customer_id: str, message: str, delay_hours: int):
        """Send in-app notification"""
        # In production, this would integrate with notification system
        logger.info(f"Scheduling in-app message for {customer_id}: '{message}' in {delay_hours} hours")

    def _schedule_human_touch(self, customer_id: str, action_type: str, delay_hours: int):
        """Schedule human touchpoint (success manager, call, etc.)"""
        # In production, this would create tasks for success team
        logger.info(f"Scheduling human touch '{action_type}' for {customer_id} in {delay_hours} hours")

    def _schedule_check_in(self, customer_id: str, message: str, delay_hours: int):
        """Schedule customer check-in"""
        # In production, this would schedule automated check-in
        logger.info(f"Scheduling check-in for {customer_id}: '{message}' in {delay_hours} hours")

    def update_customer_activity(self, customer_id: str, activity_data: Dict[str, Any]):
        """Update customer activity and recalculate health"""
        if customer_id not in self.customer_profiles:
            return

        profile = self.customer_profiles[customer_id]

        # Update activity tracking
        activity_type = activity_data.get("type")

        if activity_type == "login":
            profile.last_login = datetime.now()
            self._update_health_metric(customer_id, "login_frequency", 1.0)

        elif activity_type == "feature_used":
            feature = activity_data.get("feature")
            self._update_health_metric(customer_id, "feature_adoption", 0.1)

        elif activity_type == "team_member_active":
            self._update_health_metric(customer_id, "team_engagement", 0.05)

        elif activity_type == "support_ticket":
            profile.support_tickets += 1
            sentiment = activity_data.get("sentiment", 0.5)
            self._update_health_metric(customer_id, "support_sentiment", sentiment)

        elif activity_type == "roi_milestone":
            roi_value = activity_data.get("roi_value", 0)
            self._update_health_metric(customer_id, "roi_realization", roi_value)

        # Recalculate overall health
        self._recalculate_health_score(customer_id)

        # Check for success play triggers
        self._check_success_play_triggers(customer_id)

    def _update_health_metric(self, customer_id: str, metric_name: str, increment: float):
        """Update specific health metric"""
        if metric_name in self.health_metrics:
            metric = self.health_metrics[metric_name]
            metric.value = min(1.0, metric.value + increment)
            metric.last_updated = datetime.now()

    def _recalculate_health_score(self, customer_id: str):
        """Recalculate overall customer health score"""
        if customer_id not in self.customer_profiles:
            return

        profile = self.customer_profiles[customer_id]

        # Calculate weighted health score
        total_weight = 0
        weighted_score = 0

        for metric in self.health_metrics.values():
            weighted_score += metric.value * metric.weight
            total_weight += metric.weight

        if total_weight > 0:
            profile.health_score = weighted_score / total_weight

        # Determine health status
        if profile.health_score >= 80:
            profile.health_status = CustomerHealthStatus.HEALTHY
        elif profile.health_score >= 60:
            profile.health_status = CustomerHealthStatus.AT_RISK
        elif profile.health_score >= 40:
            profile.health_status = CustomerHealthStatus.CRITICAL
        else:
            profile.health_status = CustomerHealthStatus.CHURNED

    def _check_success_play_triggers(self, customer_id: str):
        """Check if any success plays should be triggered"""
        profile = self.customer_profiles[customer_id]

        for play_id, play in self.success_plays.items():
            if self._should_trigger_success_play(profile, play):
                self._execute_success_play(customer_id, play)

    def _should_trigger_success_play(self, profile: CustomerProfile, play: SuccessPlay) -> bool:
        """Check if success play conditions are met"""
        triggers = play.trigger_conditions

        # Check health score conditions
        if "health_score_below" in triggers and profile.health_score >= triggers["health_score_below"]:
            return False
        if "health_score_above" in triggers and profile.health_score < triggers["health_score_above"]:
            return False

        # Check account age
        if "customer_age_days" in triggers:
            customer_age = (datetime.now() - profile.signup_date).days
            age_condition = triggers["customer_age_days"]
            if age_condition.startswith("<=") and customer_age > int(age_condition[2:]):
                return False
            if age_condition.startswith(">=") and customer_age < int(age_condition[2:]):
                return False

        # Check tier conditions
        if "account_tier" in triggers and profile.tier != triggers["account_tier"]:
            return False

        # Check login frequency
        if "login_frequency_below" in triggers:
            login_metric = self.health_metrics.get("login_frequency")
            if login_metric and login_metric.value >= triggers["login_frequency_below"]:
                return False

        # Check inactivity
        if "days_inactive_above" in triggers:
            if profile.last_login:
                days_inactive = (datetime.now() - profile.last_login).days
                if days_inactive <= triggers["days_inactive_above"]:
                    return False

        # Check support tickets
        if "support_tickets_above" in triggers and profile.support_tickets <= triggers["support_tickets_above"]:
            return False

        # Check revenue impact
        if "revenue_impact_above" in triggers:
            # This would require tracking actual revenue impact
            # For now, use proxy based on health score and tier
            estimated_impact = profile.health_score * profile.annual_revenue * 0.01
            if estimated_impact <= triggers["revenue_impact_above"]:
                return False

        return True

    def _execute_success_play(self, customer_id: str, play: SuccessPlay):
        """Execute success play actions"""
        logger.info(f"Executing success play '{play.name}' for customer {customer_id}")

        for action in play["actions"]:
            self._execute_success_action(customer_id, action, play)

    def _execute_success_action(self, customer_id: str, action: Dict[str, Any], play: SuccessPlay):
        """Execute individual success play action"""
        action_type = action.get("type")

        if action_type == "priority_support":
            # Assign dedicated support resources
            self._assign_priority_support(customer_id)

        elif action_type == "outreach":
            # Schedule high-priority outreach
            method = action.get("method", "email")
            self._schedule_priority_outreach(customer_id, method)

        elif action_type == "success_plan":
            # Create or update success plan
            self._create_success_plan(customer_id, play)

        elif action_type == "executive_escalation":
            # Escalate to executive team if needed
            self._executive_escalation(customer_id)

        elif action_type == "value_demonstration":
            # Prepare custom ROI analysis
            self._prepare_value_demonstration(customer_id)

        elif action_type == "expansion_opportunity":
            # Identify expansion opportunities
            self._identify_expansion_opportunities(customer_id)

        elif action_type == "advocacy_program":
            # Invite to advocacy program
            self._invite_to_advocacy_program(customer_id)

    def _assign_priority_support(self, customer_id: str):
        """Assign priority support to at-risk customer"""
        logger.info(f"Assigning priority support to customer {customer_id}")

    def _schedule_priority_outreach(self, customer_id: str, method: str):
        """Schedule priority outreach to customer"""
        logger.info(f"Scheduling priority {method} outreach for customer {customer_id}")

    def _create_success_plan(self, customer_id: str, play: SuccessPlay):
        """Create customer success plan"""
        logger.info(f"Creating success plan for customer {customer_id} based on play {play.id}")

    def _executive_escalation(self, customer_id: str):
        """Escalate to executive team"""
        logger.info(f"Executive escalation for customer {customer_id}")

    def _prepare_value_demonstration(self, customer_id: str):
        """Prepare custom ROI demonstration"""
        logger.info(f"Preparing value demonstration for customer {customer_id}")

    def _identify_expansion_opportunities(self, customer_id: str):
        """Identify expansion and upgrade opportunities"""
        logger.info(f"Identifying expansion opportunities for customer {customer_id}")

    def _invite_to_advocacy_program(self, customer_id: str):
        """Invite customer to advocacy program"""
        logger.info(f"Inviting customer {customer_id} to advocacy program")

    def get_customer_health_report(self, customer_id: str) -> Dict[str, Any]:
        """Generate comprehensive customer health report"""
        if customer_id not in self.customer_profiles:
            return {}

        profile = self.customer_profiles[customer_id]

        return {
            "customer_id": customer_id,
            "company_name": profile.company_name,
            "tier": profile.tier,
            "health_score": profile.health_score,
            "health_status": profile.health_status.value,
            "health_metrics": {
                name: {
                    "value": metric.value,
                    "status": "good" if metric.value >= metric.threshold_good else
                            "warning" if metric.value >= metric.threshold_warning else "critical",
                    "last_updated": metric.last_updated.isoformat()
                }
                for name, metric in self.health_metrics.items()
            },
            "engagement_summary": {
                "last_login": profile.last_login.isoformat() if profile.last_login else None,
                "support_tickets": profile.support_tickets,
                "risk_factors": profile.risk_factors,
                "growth_indicators": profile.growth_indicators
            },
            "recommendations": self._generate_health_recommendations(profile)
        }

    def _generate_health_recommendations(self, profile: CustomerProfile) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        if profile.health_score < 60:
            recommendations.extend([
                "Schedule immediate check-in with customer",
                "Review and address any support issues",
                "Provide additional training on key features",
                "Demonstrate recent value and ROI"
            ])

        if self.health_metrics["login_frequency"].value < 0.5:
            recommendations.append("Send re-engagement campaign with value reminders")

        if self.health_metrics["feature_adoption"].value < 0.5:
            recommendations.append("Provide feature adoption training and use case examples")

        if self.health_metrics["team_engagement"].value < 0.3:
            recommendations.append("Conduct team training and identify additional users")

        if profile.support_tickets > 3:
            recommendations.append("Review support ticket patterns and address root causes")

        return recommendations

    def get_portfolio_health_overview(self) -> Dict[str, Any]:
        """Get portfolio-wide health overview"""
        if not self.customer_profiles:
            return {"total_customers": 0, "health_distribution": {}, "tier_breakdown": {}}

        total_customers = len(self.customer_profiles)
        health_distribution = {
            "healthy": 0,
            "at_risk": 0,
            "critical": 0,
            "churned": 0,
            "growing": 0
        }

        tier_breakdown = {
            "free": {"count": 0, "avg_health": 0},
            "growth": {"count": 0, "avg_health": 0},
            "enterprise": {"count": 0, "avg_health": 0}
        }

        total_health_by_tier = {
            "free": [],
            "growth": [],
            "enterprise": []
        }

        for profile in self.customer_profiles.values():
            # Count health distribution
            health_distribution[profile.health_status.value] += 1

            # Track by tier
            tier_breakdown[profile.tier]["count"] += 1
            total_health_by_tier[profile.tier].append(profile.health_score)

        # Calculate average health by tier
        for tier in total_health_by_tier:
            if total_health_by_tier[tier]:
                tier_breakdown[tier]["avg_health"] = sum(total_health_by_tier[tier]) / len(total_health_by_tier[tier])

        # Calculate risk and opportunity metrics
        at_risk_customers = [p for p in self.customer_profiles.values() if p.health_status in [CustomerHealthStatus.AT_RISK, CustomerHealthStatus.CRITICAL]]
        growth_opportunities = [p for p in self.customer_profiles.values() if p.health_score > 80 and p.tier != "enterprise"]

        return {
            "total_customers": total_customers,
            "health_distribution": health_distribution,
            "tier_breakdown": tier_breakdown,
            "risk_metrics": {
                "at_risk_count": len(at_risk_customers),
                "at_risk_percentage": len(at_risk_customers) / total_customers * 100,
                "high_value_at_risk": len([p for p in at_risk_customers if p.annual_revenue > 1000000])
            },
            "growth_opportunities": {
                "upgrade_candidates": len(growth_opportunities),
                "expansion_revenue_potential": sum(p.annual_revenue * 0.01 for p in growth_opportunities),  # 1% of revenue
                "advocacy_potential": len([p for p in self.customer_profiles.values() if p.health_score > 90])
            },
            "success_play_activity": {
                "active_plays": len([p for p in self.customer_profiles.values() if p.health_score < 60]),
                "growth_plays": len(growth_opportunities),
                "executive_engagement": len([p for p in self.customer_profiles.values() if p.tier == "enterprise"])
            }
        }
