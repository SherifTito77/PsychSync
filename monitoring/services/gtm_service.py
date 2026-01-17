#!/usr/bin/env python3
"""
Go-to-Market Strategy Service
Customer acquisition, sales enablement, and revenue growth automation
"""

import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class CustomerSegment(str, Enum):
    STARTUP = "startup"
    SMB = "smb"  # Small & Medium Business
    MID_MARKET = "mid_market"
    ENTERPRISE = "enterprise"

class LeadSource(str, Enum):
    WEBSITE = "website"
    DEMO = "demo"
    REFERRAL = "referral"
    OUTBOUND = "outbound"
    PARTNER = "partner"
    PSYCSYNC_INTEGRATION = "psychsync_integration"

class FunnelStage(str, Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"
    CUSTOMER = "customer"

@dataclass
class GTMCampaign:
    """Marketing campaign configuration"""
    campaign_id: str
    campaign_name: str
    campaign_type: str  # awareness, consideration, conversion, retention
    target_segment: CustomerSegment
    budget: float
    start_date: datetime
    end_date: datetime
    channels: List[str]
    messaging: Dict[str, str]
    kpis: Dict[str, float]
    status: str  # active, paused, completed

@dataclass
class Lead:
    """Sales lead information"""
    lead_id: str
    customer_id: Optional[str]
    email: str
    company_name: str
    job_title: str
    company_size: str
    industry: str
    psychsync_app_url: Optional[str]
    lead_source: LeadSource
    created_at: datetime
    funnel_stage: FunnelStage
    score: float  # 0-100 lead scoring
    contact_info: Dict[str, Any]
    behavioral_data: Dict[str, Any]
    converted_to_customer: bool = False

@dataclass
class SalesPlay:
    """Automated sales playbook"""
    play_id: str
    play_name: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    automation_enabled: bool
    created_at: datetime

@dataclass
class CustomerJourney:
    """Customer journey tracking and optimization"""
    journey_id: str
    customer_id: str
    touchpoints: List[Dict[str, Any]]
    stage_transitions: List[Dict[str, Any]]
    conversion_events: List[Dict[str, Any]]
    optimization_recommendations: List[str]
    created_at: datetime

class GTMService:
    """Go-to-Market strategy and execution service"""

    def __init__(self):
        self.campaigns: Dict[str, GTMCampaign] = {}
        self.leads: Dict[str, Lead] = {}
        self.sales_plays: Dict[str, SalesPlay] = {}
        self.customer_journeys: Dict[str, CustomerJourney] = {}

        self._initialize_default_campaigns()
        self._initialize_sales_plays()

    def _initialize_default_campaigns(self):
        """Initialize default GTM campaigns"""
        campaigns = [
            GTMCampaign(
                campaign_id="awareness_psychsync_integrators",
                campaign_name="PsychSync Integration Awareness",
                campaign_type="awareness",
                target_segment=CustomerSegment.SMB,
                budget=50000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=90),
                channels=["content_marketing", "psychsync_notifications", "partner_outreach"],
                messaging={
                    "headline": "Unlock Business Intelligence for Your PsychSync Platform",
                    "subheadline": "Transform monitoring from cost center to revenue driver",
                    "value_proposition": "See how performance impacts your bottom line",
                    "cta": "Start Free Business Intelligence Setup"
                },
                kpis={
                    "website_visitors": 10000,
                    "demo_signups": 500,
                    "integration_setups": 250,
                    "conversion_rate": 0.025
                },
                status="active"
            ),
            GTMampaign(
                campaign_id="consideration_revenue_protection",
                campaign_name="Revenue Protection Consideration",
                campaign_type="consideration",
                target_segment=CustomerSegment.MID_MARKET,
                budget=75000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=120),
                channels=["email_marketing", "webinars", "case_studies", "competitor_analysis"],
                messaging={
                    "headline": "Protect Your $500K+ Monthly Revenue with Advanced Monitoring",
                    "subheadline": "Our customers save an average of $156K monthly through proactive issue prevention",
                    "value_proposition": "Industry-leading 43% faster response time and 99.9% uptime guarantee",
                    "cta": "See Your Revenue Protection Analysis"
                },
                kpis={
                    "qualified_leads": 200,
                    "demo_requests": 100,
                    "proposals_sent": 50,
                    "conversion_rate": 0.20
                },
                status="active"
            ),
            GTMampaign(
                campaign_id="conversion_growth_upscale",
                campaign_name="Growth & Scale Conversion",
                campaign_type="conversion",
                target_segment=CustomerSegment.ENTERPRISE,
                budget=100000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=180),
                channels=["account_based_marketing", "executive_workshops", "proof_of_concept", "roi_studies"],
                messaging={
                    "headline": "Enterprise Business Intelligence for Scale",
                    "subheadline": "Complete platform visibility with SLA guarantees and dedicated support",
                    "value_proposition": "$1M+ revenue protection with 24/7 dedicated support",
                    "cta": "Schedule Executive Consultation"
                },
                kpis={
                    "enterprise_leads": 100,
                    "executive_meetings": 50,
                    "proofs_concept": 25,
                    "enterprise_deals": 10,
                    "conversion_rate": 0.10
                },
                status="active"
            ),
            GTMCampaign(
                campaign_id="retention_expansion",
                campaign_name="Customer Success & Expansion",
                campaign_type="retention",
                target_segment=CustomerSegment.MID_MARKET,
                budget=30000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=365),
                channels=["customer_success", "automated_insights", "upgrade_triggers", "qbr"],
                messaging={
                    "headline": "Maximize Your Investment with Advanced Features",
                    "subheadline": "Unlock deeper insights and optimize your PsychSync platform performance",
                    "value_proposition": "Advanced customers see 45% higher team productivity and 60% faster value realization",
                    "cta": "Review Your Optimization Opportunities"
                },
                kpis={
                    "upsell_opportunities": 150,
                    "expansion_revenue": 75000,
                    "retention_rate": 0.92,
                    "expansion_rate": 0.15
                },
                status="active"
            )
        ]

        for campaign in campaigns:
            self.campaigns[campaign.campaign_id] = campaign

    def _initialize_sales_plays(self):
        """Initialize automated sales plays"""
        plays = [
            SalesPlay(
                play_id="revenue_risk_high",
                play_name="High Revenue Risk Engagement",
                trigger_conditions={
                    "revenue_at_risk": {"operator": ">", "value": 25000},
                    "critical_incidents": {"operator": ">", "value": 3},
                    "current_tier": "free"
                },
                actions=[
                    {
                        "type": "automated_email",
                        "template": "revenue_protection_urgent",
                        "timing": "immediate"
                    },
                    {
                        "type": "priority_support",
                        "escalation": "high"
                    },
                    {
                        "type": "upgrade_recommendation",
                        "personalized": True,
                        "urgency": "high"
                    }
                ],
                success_criteria={
                    "upgrade_conversion": 0.30,
                    "response_time_hours": 24
                },
                automation_enabled=True,
                created_at=datetime.now()
            ),
            SalesPlay(
                play_id="growth_trajectory_fast",
                play_name="Fast Growth Trajectory",
                trigger_conditions={
                    "revenue_growth_rate": {"operator": ">", "value": 0.20},
                    "team_growth_rate": {"operator": ">", "value": 0.15},
                    "current_tier": ["free", "growth"]
                },
                actions=[
                    {
                        "type": "growth_insights_report",
                        "frequency": "weekly"
                    },
                    {
                        "type": "scalability_consultation",
                        "automated": True
                    },
                    {
                        "type": "future_proofing_proposal",
                        "personalized": True
                    }
                ],
                success_criteria={
                    "upgrade_conversion": 0.25,
                    "expansion_revenue": 0.10
                },
                automation_enabled=True,
                created_at=datetime.now()
            ),
            SalesPlay(
                play_id="feature_adoption_unlock",
                play_name="Feature Adoption Optimization",
                trigger_conditions={
                    "team_analytics_adoption": {"operator": "<", "value": 0.50},
                    "assessment_completion_rate": {"operator": "<", "value": 0.70},
                    "current_tier": "growth"
                },
                actions=[
                    {
                        "type": "adoption_workshop",
                        "automated": False,
                        "priority": "medium"
                    },
                    {
                        "type": "feature_usage_tips",
                        "frequency": "bi_weekly"
                    },
                    {
                        "type": "success_stories",
                        "industry_specific": True
                    }
                ],
                success_criteria={
                    "feature_adoption_increase": 0.20,
                    "engagement_score_improvement": 0.15
                },
                automation_enabled=True,
                created_at=datetime.now()
            )
        ]

        for play in plays:
            self.sales_plays[play.play_id] = play

    def create_lead(
        self,
        email: str,
        company_name: str,
        job_title: str,
        company_size: str,
        industry: str,
        lead_source: LeadSource,
        psychsync_app_url: Optional[str] = None
    ) -> Lead:
        """Create a new sales lead"""
        lead_id = f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        customer_id = f"cust_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{company_name.lower().replace(' ', '_')}"

        # Determine customer segment
        segment = self._determine_customer_segment(company_size)

        lead = Lead(
            lead_id=lead_id,
            customer_id=customer_id,
            email=email,
            company_name=company_name,
            job_title=job_title,
            company_size=company_size,
            industry=industry,
            psychsync_app_url=psychsync_app_url,
            lead_source=lead_source,
            created_at=datetime.now(),
            funnel_stage=FunnelStage.AWARENESS,
            score=0.0,
            contact_info={},
            behavioral_data={},
            converted_to_customer=False
        )

        self.leads[lead_id] = lead

        # Start customer journey tracking
        self._start_customer_journey(customer_id, lead_id)

        # Execute relevant sales plays
        self._execute_sales_plays_for_lead(lead)

        logger.info(f"Created lead: {lead_id} from {lead_source.value}")
        return lead

    def _determine_customer_segment(self, company_size: str) -> CustomerSegment:
        """Determine customer segment from company size"""
        size_lower = company_size.lower()

        if "1-10" in size_lower or "startup" in size_lower or "1-5" in size_lower:
            return CustomerSegment.STARTUP
        elif "11-50" in size_lower or "small" in size_lower:
            return CustomerSegment.SMB
        elif "51-500" in size_lower or "medium" in size_lower:
            return CustomerSegment.MID_MARKET
        else:
            return CustomerSegment.ENTERPRISE

    def _start_customer_journey(self, customer_id: str, lead_id: str):
        """Start tracking customer journey"""
        journey_id = f"journey_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        journey = CustomerJourney(
            journey_id=journey_id,
            customer_id=customer_id,
            touchpoints=[],
            stage_transitions=[],
            conversion_events=[],
            optimization_recommendations=[],
            created_at=datetime.now()
        )

        self.customer_journeys[journey_id] = journey

        # Record first touchpoint
        self._record_touchpoint(journey_id, "lead_created", {
            "lead_id": lead_id,
            "timestamp": datetime.now().isoformat()
        })

    def _record_touchpoint(self, journey_id: str, touchpoint_type: str, data: Dict[str, Any]):
        """Record customer journey touchpoint"""
        if journey_id not in self.customer_journeys:
            return

        journey = self.customer_journeys[journey_id]
        touchpoint = {
            "type": touchpoint_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        journey.touchpoints.append(touchpoint)

    def _execute_sales_plays_for_lead(self, lead: Lead):
        """Execute relevant sales plays for a lead"""
        lead_metrics = self._get_lead_metrics(lead)

        for play_id, play in self.sales_plays.items():
            if self._evaluate_trigger_conditions(play.trigger_conditions, lead_metrics):
                self._execute_sales_play(play_id, lead)
                break  # Only execute highest priority matching play

    def _evaluate_trigger_conditions(self, conditions: Dict[str, Any], metrics: Dict[str, Any]) -> bool:
        """Evaluate if trigger conditions are met"""
        for key, condition in conditions.items():
            if key not in metrics:
                return False

            metric_value = metrics[key]
            condition_value = condition.get("value", 0)
            operator = condition.get("operator", "eq")

            if operator == ">":
                if not metric_value > condition_value:
                    return False
            elif operator == "<":
                if not metric_value < condition_value:
                    return False
            elif operator == "eq":
                if not metric_value == condition_value:
                    return False
            elif operator == "in":
                if isinstance(metric_value, list):
                    if condition_value not in metric_value:
                        return False
                else:
                    if metric_value != condition_value:
                        return False

        return True

    def _execute_sales_play(self, play_id: str, lead: Lead):
        """Execute a sales play for a lead"""
        if play_id not in self.sales_plays:
            return

        play = self.sales_plays[play_id]

        for action in play.actions:
            self._execute_action(action, lead, play)

        logger.info(f"Executed sales play: {play.play_name} for lead: {lead.lead_id}")

    def _execute_action(self, action: Dict[str, Any], lead: Lead, play: SalesPlay):
        """Execute individual action from a sales play"""
        action_type = action.get("type")

        if action_type == "automated_email":
            self._send_automated_email(lead, action)
        elif action_type == "priority_support":
            self._escalate_to_priority_support(lead, action)
        elif action_type == "upgrade_recommendation":
            self._generate_upgrade_recommendation(lead, action)
        elif action_type == "growth_insights_report":
            self._generate_growth_insights(lead, action)
        elif action_type == "scalability_consultation":
            self._schedule_consultation(lead, action)
        elif action_type == "future_proofing_proposal":
            self._create_proposal(lead, action)
        elif action_type == "adoption_workshop":
            self._schedule_workshop(lead, action)
        elif action_type == "feature_usage_tips":
            self._send_feature_tips(lead, action)
        elif action_type == "success_stories":
            self._send_success_stories(lead, action)

    def _send_automated_email(self, lead: Lead, action: Dict[str, Any]):
        """Send automated email to lead"""
        # In production, this would integrate with email service
        template = action.get("template", "general_contact")
        logger.info(f"Sending automated email {template} to lead {lead.lead_id}")

    def _escalate_to_priority_support(self, lead: Lead, action: Dict[str, Any]):
        """Escalate lead to priority support"""
        escalation_level = action.get("escalation", "medium")
        logger.info(f"Escalating lead {lead.lead_id} to {escalation_level} priority support")

    def _generate_upgrade_recommendation(self, lead: Lead, action: Dict[str, Any]):
        """Generate personalized upgrade recommendation"""
        is_personalized = action.get("personalized", False)
        urgency = action.get("urgency", "medium")

        logger.info(f"Generating upgrade recommendation for lead {lead.lead_id} (personalized: {is_personalized}, urgency: {urgency})")

    def _schedule_consultation(self, lead: Lead, action: Dict[str, Any]):
        """Schedule consultation with lead"""
        logger.info(f"Scheduling consultation for lead {lead.lead_id}")

    def _create_proposal(self, lead: Lead, action: Dict[str, Any]):
        """Create personalized proposal for lead"""
        logger.info(f"Creating proposal for lead {lead.lead_id}")

    def _schedule_workshop(self, lead: Lead, action: Dict[str, Any]):
        """Schedule workshop for lead"""
        logger.info(f"Scheduling workshop for lead {lead.lead_id}")

    def _send_feature_tips(self, lead: Lead, action: Dict[str, Any]):
        """Send feature usage tips to lead"""
        frequency = action.get("frequency", "bi_weekly")
        logger.info(f"Scheduling feature tips for lead {lead.lead_id} (frequency: {frequency})")

    def _send_success_stories(self, lead: Lead, action: Dict[str, Any]):
        """Send success stories to lead"""
        industry_specific = action.get("industry_specific", False)
        logger.info(f"Sending success stories to lead {lead.lead_id} (industry_specific: {industry_specific})")

    def _generate_growth_insights(self, lead: Lead, action: Dict[str, Any]):
        """Generate growth insights report for lead"""
        frequency = action.get("frequency", "weekly")
        logger.info(f"Generating growth insights for lead {lead.lead_id} (frequency: {frequency})")

    def _get_lead_metrics(self, lead: Lead) -> Dict[str, Any]:
        """Get metrics for lead evaluation"""
        # Mock metrics - in production, this would come from behavioral tracking
        return {
            "revenue_at_risk": 15000.0,
            "critical_incidents": 2,
            "team_analytics_adoption": 0.35,
            "assessment_completion_rate": 0.68,
            "revenue_growth_rate": 0.25,
            "team_growth_rate": 0.18,
            "current_tier": "free"
        }

    def analyze_campaign_performance(self, campaign_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Analyze campaign performance"""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign = self.campaigns[campaign_id]

        # Calculate performance metrics
        start_date = datetime.now() - timedelta(days=days_back)
        leads_created = sum(1 for lead in self.leads.values()
                          if lead.created_at >= start_date and lead.lead_source == LeadSource.WEBSITE)

        conversions = sum(1 for lead in self.leads.values()
                       if lead.created_at >= start_date and lead.converted_to_customer)

        conversion_rate = conversions / max(1, leads_created) if leads_created > 0 else 0

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.campaign_name,
            "period_days": days_back,
            "leads_generated": leads_created,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "cost_per_lead": campaign.budget / max(1, leads_created),
            "roi": self._calculate_campaign_roi(campaign, conversions),
            "kpis_met": self._calculate_kpis_met(campaign, leads_created, conversions)
        }

    def _calculate_campaign_roi(self, campaign: GTMCampaign, conversions: int) -> float:
        """Calculate campaign ROI"""
        # Average customer value assumptions
        avg_customer_value = {
            CustomerSegment.SMB: 1188,  # $99/month avg, 12 months
            CustomerSegment.MID_MARKET: 5988,  # $499/month avg, 12 months
            CustomerSegment.ENTERPRISE: 5988,  # $499/month avg, 12 months
        }

        segment_value = avg_customer_value.get(campaign.target_segment, 1188)
        total_revenue = conversions * segment_value

        return (total_revenue - campaign.budget) / max(1, campaign.budget)

    def _calculate_kpis_met(self, campaign: GTMCampaign, leads: int, conversions: int) -> Dict[str, float]:
        """Calculate percentage of KPIs met"""
        kpis = campaign.kpis
        met_kpis = {}

        for kpi_name, target_value in kpis.items():
            if kpi_name == "demo_signups":
                actual_value = min(leads * 0.05, target_value)  # Assume 5% demo signup rate
                met_kpis[kpi_name] = (actual_value / target_value) * 100
            elif kpi_name == "conversion_rate":
                actual_value = conversion_rate * 100
                met_kpis[kpi_name] = min(actual_value / target_value, 100) * 100
            else:
                met_kpis[kpi_name] = 0  # Skip unknown KPIs

        return met_kpis

    def get_lead_funnel_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get lead funnel metrics across all stages"""
        start_date = datetime.now() - timedelta(days=days_back)

        funnel_stages = {}
        stage_counts = {}

        for stage in FunnelStage:
            stage_count = sum(1 for lead in self.leads.values()
                             if lead.funnel_stage == stage and lead.created_at >= start_date)
            stage_counts[stage.value] = stage_count

        # Calculate conversion rates between stages
        conversion_rates = {}
        total_leads = stage_counts.get("awareness", 1)

        stages = list(FunnelStage)
        for i in range(len(stages) - 1):
            current_stage = stages[i].value
            next_stage = stages[i + 1].value
            current_count = stage_counts.get(current_stage, 0)
            next_count = stage_counts.get(next_stage, 0)

            if current_count > 0:
                conversion_rates[f"{current_stage}_to_{next_stage}"] = (next_count / current_count) * 100

        return {
            "period_days": days_back,
            "total_leads": total_leads,
            "stage_counts": stage_counts,
            "conversion_rates": conversion_rates,
            "overall_conversion_rate": stage_counts.get("customer", 0) / max(1, total_leads) * 100
        }

# Global GTM service instance
gtm_service = GTMService()
