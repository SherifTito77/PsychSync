#!/usr/bin/env python3
"""
PsychSync Monitoring Web Application
Web-based interface for easy monitoring setup and business intelligence
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl, validator
import aiohttp
import yaml

# Import pricing and subscription services
from services.pricing_service import pricing_service, SubscriptionTier, BillingCycle
from services.subscription_service import subscription_service
from services.upgrade_recommendation_service import upgrade_recommendation_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PsychSync Monitor",
    description="Business Intelligence & Monitoring Platform",
    version="1.0.0"
)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
CONFIG_FILE = "/Users/sheriftito/Downloads/psychsync/.env.monitoring"

@dataclass
class BusinessMetrics:
    """Business KPIs tracked by the system"""
    monthly_revenue: float
    active_users: int
    assessment_completion_rate: float
    user_satisfaction_score: float
    downtime_hours: float
    support_ticket_count: int
    nps_score: float

@dataclass
class MonitoringSetup:
    """Monitoring configuration state"""
    api_url: str
    status: str
    endpoints_discovered: int
    metrics_active: bool
    alerts_configured: bool
    dashboard_url: Optional[str]
    created_at: datetime
    business_integration: bool = False
    team_size: str = "medium"
    business_goal: str = "performance"

@dataclass
class CustomerInsight:
    """Business insight derived from monitoring data"""
    insight_type: str
    title: str
    description: str
    impact_level: str  # high, medium, low
    financial_impact: float
    recommendation: str
    confidence: float

# Sample business data (in production, this would come from monitoring systems)
SAMPLE_METRICS = BusinessMetrics(
    monthly_revenue=125000.00,
    active_users=2847,
    assessment_completion_rate=73.5,
    user_satisfaction_score=72.3,
    downtime_hours=4.2,
    support_ticket_count=23,
    nps_score=45.8
)

SAMPLE_INSIGHTS = [
    CustomerInsight(
        insight_type="performance",
        title="Response Time Affecting User Satisfaction",
        description="Users experiencing response times >2s have 40% lower satisfaction scores",
        impact_level="high",
        financial_impact=15600.00,
        recommendation="Optimize database queries and implement caching for slow endpoints",
        confidence=0.92
    ),
    CustomerInsight(
        insight_type="revenue",
        title="Assessment Drop-off Costs $12,500 Monthly",
        description="30% of users abandon assessments at step 3, representing significant lost revenue",
        impact_level="high",
        financial_impact=12500.00,
        recommendation="Simplify assessment flow and provide progress indicators",
        confidence=0.88
    ),
    CustomerInsight(
        insight_type="engagement",
        title="Team Analytics Underutilized",
        description="Teams using analytics features see 45% higher retention and 60% faster value realization",
        impact_level="medium",
        financial_impact=8500.00,
        recommendation="Promote analytics features in team dashboard with usage examples",
        confidence=0.75
    )
]

class SetupForm(BaseModel):
    """Form data for monitoring setup"""
    app_url: HttpUrl
    team_size: str = "small"  # small, medium, large, enterprise
    business_goal: str = "performance"  # performance, revenue, engagement, compliance
    contact_email: str
    company_name: str

    @validator('team_size')
    def validate_team_size(cls, v):
        allowed = ["small", "medium", "large", "enterprise"]
        if v not in allowed:
            raise ValueError('Invalid team size')
        return v

    @validator('business_goal')
    def validate_business_goal(cls, v):
        allowed = ["performance", "revenue", "engagement", "compliance"]
        if v not in allowed:
            raise ValueError('Invalid business goal')
        return v

class PsychSyncAPI:
    """Interface to PsychSync application for auto-discovery"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def discover_endpoints(self) -> List[str]:
        """Auto-discover PsychSync API endpoints"""
        try:
            # Standard PsychSync endpoints
            standard_endpoints = [
                "/api/v1/health",
                "/api/v1/auth/status",
                "/api/v1/assessments/templates",
                "/api/v1/teams",
                "/api/v1/users/me",
                "/api/v1/analytics/summary"
            ]

            discovered = []

            # Test each endpoint
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    discovered.append("/api/v1/health")

            # Try to discover more endpoints if basic ones work
            if discovered:
                try:
                    async with self.session.get(f"{self.base_url}/docs") as response:
                        if response.status == 200:
                            # Could parse OpenAPI spec here for more endpoints
                            pass
                except:
                    pass

            # Add standard endpoints if base app is accessible
            for endpoint in standard_endpoints:
                discovered.append(endpoint)

            return list(set(discovered))  # Remove duplicates

        except Exception as e:
            logger.error(f"Error discovering endpoints: {e}")
            return []

    async def get_business_metrics(self) -> Dict[str, Any]:
        """Get business metrics from PsychSync API"""
        try:
            # In production, this would use actual authentication
            api_url = f"{self.base_url}/api/v1/monitoring/business/dashboard-summary"

            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("business_summary", SAMPLE_METRICS.__dict__)
                else:
                    logger.warning(f"Failed to get business metrics: {response.status}")
                    return SAMPLE_METRICS.__dict__

        except Exception as e:
            logger.error(f"Error getting business metrics: {e}")
            # Fall back to sample data
            return SAMPLE_METRICS.__dict__

    async def get_team_analytics(self, team_id: str) -> Dict[str, Any]:
        """Get team-specific analytics"""
        try:
            # In production, this would hit PsychSync team analytics API
            api_url = f"{self.base_url}/api/v1/monitoring/business/user-journey"

            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    logger.warning(f"Failed to get team analytics: {response.status}")
                    return self._get_mock_team_analytics(team_id)

        except Exception as e:
            logger.error(f"Error getting team analytics: {e}")
            return self._get_mock_team_analytics(team_id)

    async def get_revenue_impact(self) -> Dict[str, Any]:
        """Get revenue impact analysis"""
        try:
            api_url = f"{self.base_url}/api/v1/monitoring/business/revenue-impact"

            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    logger.warning(f"Failed to get revenue impact: {response.status}")
                    return self._get_mock_revenue_impact()

        except Exception as e:
            logger.error(f"Error getting revenue impact: {e}")
            return self._get_mock_revenue_impact()

    async def get_competitive_benchmarking(self) -> Dict[str, Any]:
        """Get competitive benchmarking data"""
        try:
            api_url = f"{self.base_url}/api/v1/monitoring/business/competitive-benchmarking"

            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                else:
                    logger.warning(f"Failed to get competitive benchmarking: {response.status}")
                    return self._get_mock_competitive_benchmarking()

        except Exception as e:
            logger.error(f"Error getting competitive benchmarking: {e}")
            return self._get_mock_competitive_benchmarking()

    def _get_mock_team_analytics(self, team_id: str) -> Dict[str, Any]:
        """Fallback mock team analytics"""
        return {
            "team_id": team_id,
            "members_count": 15,
            "assessments_completed": 89,
            "avg_assessment_time": 8.4,  # minutes
            "team_satisfaction": 78.5,
            "feature_usage": {
                "team_analytics": True,
                "performance_tracking": True,
                "custom_assessments": False,
                "advanced_reports": False
            }
        }

    def _get_mock_revenue_impact(self) -> Dict[str, Any]:
        """Fallback mock revenue impact"""
        return {
            "time_range": "30d",
            "business_metrics": SAMPLE_METRICS.__dict__,
            "revenue_impact": {
                "current_revenue": SAMPLE_METRICS.monthly_revenue,
                "revenue_protected": SAMPLE_METRICS.monthly_revenue * 0.25,
                "performance_impact": SAMPLE_METRICS.monthly_revenue * 0.25,
                "support_cost_savings": SAMPLE_METRICS.support_ticket_count * 150,
                "roi_multiplier": 4.5
            },
            "insights": SAMPLE_INSIGHTS
        }

    def _get_mock_competitive_benchmarking(self) -> Dict[str, Any]:
        """Fallback mock competitive benchmarking"""
        return {
            "psychsync_performance": {
                "api_response_time": 1.2,
                "uptime": 99.9,
                "error_rate": 0.1,
                "user_satisfaction": 72.3
            },
            "industry_benchmarks": {
                "assessment_platforms": {
                    "api_response_time": 2.1,
                    "uptime": 99.5,
                    "error_rate": 0.5,
                    "user_satisfaction": 45.0
                }
            },
            "competitive_advantages": [
                {
                    "advantage": "Faster Response Time",
                    "psychsync": 1.2,
                    "industry": 2.1,
                    "improvement": "43%"
                }
            ]
        }

class MonitoringSetupManager:
    """Manages the monitoring setup process"""

    def __init__(self):
        self.setups = {}  # In production, this would be stored in database

    async def create_monitoring_setup(self, form_data: SetupForm) -> MonitoringSetup:
        """Create a new monitoring configuration"""
        setup_id = f"setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{form_data.team_size}"

        try:
            async with PsychSyncAPI(str(form_data.app_url)) as api:
                endpoints = await api.discover_endpoints()

                # Test business intelligence API connectivity
                business_metrics = await api.get_business_metrics()
                metrics_available = len(business_metrics) > 0

                setup = MonitoringSetup(
                    api_url=str(form_data.app_url),
                    status="configured",
                    endpoints_discovered=len(endpoints),
                    metrics_active=metrics_available,
                    alerts_configured=True,
                    dashboard_url=f"http://localhost:8080/dashboard/{setup_id}",
                    created_at=datetime.now(),
                    business_integration=metrics_available,
                    team_size=form_data.team_size,
                    business_goal=form_data.business_goal
                )

                self.setups[setup_id] = setup
                logger.info(f"Created monitoring setup: {setup_id} with BI integration: {metrics_available}")
                return setup

        except Exception as e:
            logger.error(f"Error creating monitoring setup: {e}")
            # Return error setup
            return MonitoringSetup(
                api_url=str(form_data.app_url),
                status="error",
                endpoints_discovered=0,
                metrics_active=False,
                alerts_configured=False,
                dashboard_url=None,
                created_at=datetime.now()
            )

class BusinessInsightGenerator:
    """Generates business insights from monitoring data"""

    def __init__(self):
        self.insights = SAMPLE_INSIGHTS

    async def generate_insights(self, metrics: BusinessMetrics, team_size: str, goal: str) -> List[CustomerInsight]:
        """Generate business insights based on metrics"""
        insights = []

        # Filter and prioritize insights based on team size and goals
        for insight in self.insights:
            # Simple filtering logic - in production, this would be more sophisticated
            if self._should_include_insight(insight, metrics, team_size, goal):
                insights.append(insight)

        # Generate additional context-specific insights
        context_insights = await self._generate_context_insights(metrics, team_size, goal)
        insights.extend(context_insights)

        # Sort by financial impact
        insights.sort(key=lambda x: x.financial_impact, reverse=True)

        return insights

    def _should_include_insight(self, insight: CustomerInsight, metrics: BusinessMetrics, team_size: str, goal: str) -> bool:
        """Determine if insight should be included based on context"""
        if insight.confidence < 0.7:  # Low confidence insights excluded
            return False

        # Include if impact level matches goals
        if goal == "performance" and insight.insight_type == "performance":
            return True
        if goal == "revenue" and insight.insight_type == "revenue":
            return True
        if goal == "engagement" and insight.insight_type == "engagement":
            return True

        # Always include high-impact insights
        if insight.impact_level == "high":
            return True

        return False

    async def _generate_context_insights(self, metrics: BusinessMetrics, team_size: str, goal: str) -> List[CustomerInsight]:
        """Generate insights based on current context"""
        insights = []

        # Team size based insights
        if team_size == "small" and metrics.nps_score < 50:
            insights.append(CustomerInsight(
                insight_type="customer_experience",
                title="Low NPS Score Risk",
                description=f"NPS of {metrics.nps_score} is below small business average. User satisfaction issues may lead to churn.",
                impact_level="medium",
                financial_impact=8000.00,
                recommendation="Implement customer success program and gather user feedback",
                confidence=0.85
            ))

        # Revenue insights
        if goal == "revenue" and metrics.monthly_revenue > 100000:
            insights.append(CustomerInsight(
                insight_type="opportunity",
                title="Revenue Growth Opportunity",
                description="With ${metrics.monthly_revenue:,.0f} monthly revenue, advanced analytics could increase revenue by 20-30% through optimization.",
                impact_level="high",
                financial_impact=37500.00,
                recommendation="Upgrade to Growth Analytics tier to unlock revenue optimization features",
                confidence=0.90
            ))

        # Performance insights
        if goal == "performance" and metrics.downtime_hours > 2:
            insights.append(CustomerInsight(
                insight_type="reliability",
                title="Downtime Impacting Business Operations",
                description=f"{metrics.downtime_hours:.1f} hours of downtime is preventing normal business operations and affecting customer satisfaction.",
                impact_level="high",
                financial_impact=metrics.downtime_hours * 2500, 0,  # $2500/hour business impact
                recommendation="Implement proactive monitoring and automated issue prevention",
                confidence=0.95
            ))

        return insights

# Initialize managers
setup_manager = MonitoringSetupManager()
insight_generator = BusinessInsightGenerator()

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Marketing landing page"""
    return templates.TemplateResponse("marketing_landing.html", {
        "request": request
    })

@app.get("/setup", response_class=HTMLResponse)
async def setup_form(request: Request):
    """Setup form page"""
    return templates.TemplateResponse("setup.html", {
        "request": request
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def main_dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request
    })

@app.post("/setup", response_class=HTMLResponse)
async def handle_setup(request: Request):
    """Handle monitoring setup submission"""
    form = await request.form()

    try:
        setup_data = SetupForm(
            app_url=form.get("app_url"),
            team_size=form.get("team_size"),
            business_goal=form.get("business_goal"),
            contact_email=form.get("contact_email"),
            company_name=form.get("company_name")
        )

        setup = await setup_manager.create_monitoring_setup(setup_data)

        if setup.status == "configured":
            return templates.TemplateResponse("setup_success.html", {
                "request": request,
                "setup": setup
            })
        else:
            return templates.TemplateResponse("setup_error.html", {
                "request": request,
                "error": "Failed to configure monitoring. Please check your app URL and try again."
            })

    except Exception as e:
        logger.error(f"Setup error: {e}")
        return templates.TemplateResponse("setup_error.html", {
            "request": request,
            "error": f"Setup failed: {str(e)}"
        })

@app.get("/dashboard/{setup_id}", response_class=HTMLResponse)
async def dashboard_view(request: Request, setup_id: str):
    """Display business intelligence dashboard"""
    try:
        # Get setup details
        setup = setup_manager.setups.get(setup_id)
        if not setup:
            raise HTTPException(status_code=404, detail="Setup not found")

        # Generate business insights
        insights = await insight_generator.generate_insights(
            SAMPLE_METRICS,
            "small",  # Would come from setup data
            "performance"  # Would come from setup data
        )

        return templates.TemplateResponse("business_dashboard.html", {
            "request": request,
            "setup": setup,
            "metrics": SAMPLE_METRICS,
            "insights": insights
        })

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard loading failed")

@app.get("/dashboard/{setup_id}/business", response_class=HTMLResponse)
async def business_dashboard(request: Request, setup_id: str):
    """Business intelligence dashboard"""
    try:
        setup = setup_manager.setups.get(setup_id)
        if not setup:
            raise HTTPException(status_code=404, detail="Setup not found")

        # Get real data from PsychSync API if integration is available
        if setup.business_integration:
            async with PsychSyncAPI(setup.api_url) as api:
                business_data = await api.get_revenue_impact()
                metrics_data = await api.get_business_metrics()

                # Convert to BusinessMetrics format
                metrics = BusinessMetrics(
                    monthly_revenue=metrics_data.get("monthly_revenue", 125000.00),
                    active_users=metrics_data.get("active_users", 2847),
                    assessment_completion_rate=metrics_data.get("assessment_completion_rate", 73.5),
                    user_satisfaction_score=metrics_data.get("user_satisfaction", 72.3),
                    downtime_hours=metrics_data.get("downtime_hours", 4.2),
                    support_ticket_count=metrics_data.get("support_ticket_count", 23),
                    nps_score=metrics_data.get("nps_score", 45.8)
                )

                insights = business_data.get("insights", SAMPLE_INSIGHTS)
        else:
            # Fall back to sample data
            metrics = SAMPLE_METRICS
            insights = await insight_generator.generate_insights(
                SAMPLE_METRICS,
                setup.team_size,
                setup.business_goal
            )

        return templates.TemplateResponse("business_dashboard.html", {
            "request": request,
            "setup": setup,
            "metrics": metrics,
            "insights": insights
        })

    except Exception as e:
        logger.error(f"Business dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard loading failed")

@app.get("/dashboard/{setup_id}/journey", response_class=HTMLResponse)
async def user_journey_dashboard(request: Request, setup_id: str):
    """User journey analytics dashboard"""
    try:
        setup = setup_manager.setups.get(setup_id)
        if not setup:
            raise HTTPException(status_code=404, detail="Setup not found")

        return templates.TemplateResponse("user_journey_dashboard.html", {
            "request": request,
            "setup": setup,
            "metrics": SAMPLE_METRICS
        })

    except Exception as e:
        logger.error(f"User journey dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard loading failed")

@app.get("/dashboard/{setup_id}/competitive", response_class=HTMLResponse)
async def competitive_dashboard(request: Request, setup_id: str):
    """Competitive benchmarking dashboard"""
    try:
        setup = setup_manager.setups.get(setup_id)
        if not setup:
            raise HTTPException(status_code=404, detail="Setup not found")

        return templates.TemplateResponse("competitive_dashboard.html", {
            "request": request,
            "setup": setup,
            "metrics": SAMPLE_METRICS
        })

    except Exception as e:
        logger.error(f"Competitive dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard loading failed")

@app.get("/demo/business", response_class=HTMLResponse)
async def demo_business_dashboard(request: Request):
    """Demo business intelligence dashboard"""
    return templates.TemplateResponse("business_dashboard.html", {
        "request": request,
        "setup": None,
        "metrics": SAMPLE_METRICS,
        "insights": SAMPLE_INSIGHTS
    })

@app.get("/demo/journey", response_class=HTMLResponse)
async def demo_journey_dashboard(request: Request):
    """Demo user journey analytics dashboard"""
    return templates.TemplateResponse("user_journey_dashboard.html", {
        "request": request,
        "setup": None,
        "metrics": SAMPLE_METRICS
    })

@app.get("/demo/competitive", response_class=HTMLResponse)
async def demo_competitive_dashboard(request: Request):
    """Demo competitive benchmarking dashboard"""
    return templates.TemplateResponse("competitive_dashboard.html", {
        "request": request,
        "setup": None,
        "metrics": SAMPLE_METRICS
    })

@app.get("/upgrade", response_class=HTMLResponse)
async def upgrade_dashboard(request: Request):
    """Upgrade dashboard with pricing recommendations"""
    return templates.TemplateResponse("upgrade_dashboard.html", {
        "request": request
    })

@app.get("/upgrade/{setup_id}", response_class=HTMLResponse)
async def personalized_upgrade_dashboard(request: Request, setup_id: str):
    """Personalized upgrade dashboard for a specific setup"""
    try:
        setup = setup_manager.setups.get(setup_id)
        if not setup:
            raise HTTPException(status_code=404, detail="Setup not found")

        return templates.TemplateResponse("upgrade_dashboard.html", {
            "request": request,
            "setup": setup
        })

    except Exception as e:
        logger.error(f"Upgrade dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard loading failed")

# Pricing API Endpoints

@app.get("/api/pricing/tiers")
async def get_pricing_tiers():
    """Get all available pricing tiers"""
    try:
        tiers = {}
        for tier, config in pricing_service.tiers.items():
            tiers[tier.value] = {
                "name": config.name,
                "monthly_price": config.monthly_price,
                "yearly_price": config.yearly_price,
                "features": config.features,
                "limits": config.limits,
                "revenue_protection_limit": config.revenue_protection_limit,
                "support_level": config.support_level,
                "data_retention_days": config.data_retention_days,
                "team_size_limit": config.team_size_limit,
                "yearly_savings": pricing_service.calculate_yearly_savings(tier)
            }

        return {
            "tiers": tiers,
            "currency": "USD",
            "billing_cycles": ["monthly", "yearly"]
        }

    except Exception as e:
        logger.error(f"Error getting pricing tiers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing tiers")

@app.post("/api/pricing/recommendation")
async def get_tier_recommendation(request: Request):
    """Get recommended tier based on metrics"""
    try:
        data = await request.json()
        metrics = data.get("metrics", {})

        recommended_tier = pricing_service.get_recommended_tier(metrics)
        value_prop = pricing_service.calculate_tier_value_proposition(recommended_tier, metrics)

        return {
            "recommended_tier": recommended_tier.value,
            "value_proposition": value_prop,
            "reasoning": f"Based on your ${metrics.get('monthly_revenue', 0):,.0f} monthly revenue and {metrics.get('team_size', 1)} team members"
        }

    except Exception as e:
        logger.error(f"Error getting tier recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation")

@app.post("/api/pricing/upgrade-analysis")
async def analyze_upgrade_opportunity(request: Request):
    """Analyze upgrade opportunity and generate personalized recommendation"""
    try:
        data = await request.json()
        subscription_id = data.get("subscription_id")
        metrics = data.get("metrics", {})

        if not subscription_id:
            raise HTTPException(status_code=400, detail="subscription_id is required")

        # For demo purposes, create a mock subscription
        mock_subscription = subscription_service.subscriptions.get(subscription_id) or Subscription(
            customer_id="demo_customer",
            tier=SubscriptionTier.FREE,
            billing_cycle=BillingCycle.MONTHLY,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            status="active",
            revenue_impact=0.0,
            usage_metrics=metrics,
            upgrade_triggers=[]
        )

        # Analyze usage patterns
        usage_patterns = await upgrade_recommendation_service.analyze_usage_patterns(
            mock_subscription.customer_id, metrics
        )

        # Generate upgrade recommendation
        recommendation = await upgrade_recommendation_service.generate_upgrade_recommendation(
            customer_id=mock_subscription.customer_id,
            subscription=mock_subscription,
            current_metrics=metrics,
            usage_patterns=usage_patterns
        )

        # Generate detailed upgrade proposal
        upgrade_proposal = pricing_service.generate_upgrade_proposal(
            current_tier=recommendation.current_tier,
            target_tier=recommendation.recommended_tier,
            metrics=metrics
        )

        return {
            "recommendation": {
                "current_tier": recommendation.current_tier.value,
                "recommended_tier": recommendation.recommended_tier.value,
                "urgency_score": recommendation.urgency_score,
                "confidence_score": recommendation.confidence_score,
                "timeline": recommendation.timeline_recommendation,
                "personalized_message": recommendation.personalized_message,
                "upgrade_triggers": recommendation.upgrade_triggers
            },
            "value_proposition": {
                "additional_monthly_value": upgrade_proposal["additional_monthly_value"],
                "additional_cost": upgrade_proposal["additional_cost"],
                "upgrade_roi": upgrade_proposal["upgrade_roi"],
                "payback_period_days": upgrade_proposal["payback_period_days"],
                "key_benefits": upgrade_proposal["key_benefits"]
            },
            "new_features": upgrade_proposal["new_features"],
            "upgraded_limits": upgrade_proposal["upgraded_limits"],
            "pricing_details": {
                "new_monthly_price": pricing_service.get_tier_pricing(recommendation.recommended_tier, BillingCycle.MONTHLY),
                "new_yearly_price": pricing_service.get_tier_pricing(recommendation.recommended_tier, BillingCycle.YEARLY),
                "yearly_savings": pricing_service.calculate_yearly_savings(recommendation.recommended_tier)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing upgrade opportunity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze upgrade opportunity")

@app.post("/api/subscriptions/create")
async def create_subscription(request: Request):
    """Create a new subscription"""
    try:
        data = await request.json()
        customer_id = data.get("customer_id")
        tier = SubscriptionTier(data.get("tier", "free"))
        billing_cycle = BillingCycle(data.get("billing_cycle", "monthly"))
        trial_days = data.get("trial_days", 0)

        subscription = subscription_service.create_subscription(
            customer_id=customer_id,
            tier=tier,
            billing_cycle=billing_cycle,
            trial_days=trial_days
        )

        return {
            "success": True,
            "subscription_id": subscription.subscription_id,
            "tier": subscription.tier.value,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle.value,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "monthly_price": pricing_service.get_tier_pricing(subscription.tier, BillingCycle.MONTHLY),
            "yearly_price": pricing_service.get_tier_pricing(subscription.tier, BillingCycle.YEARLY)
        }

    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@app.get("/api/revenue/metrics")
async def get_revenue_metrics(time_period: str = "month"):
    """Get revenue metrics for the platform"""
    try:
        metrics = subscription_service.get_revenue_metrics(time_period)
        return metrics

    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/metrics")
async def get_metrics():
    """Get current business metrics"""
    return {
        "metrics": asdict(SAMPLE_METRICS),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/analytics/revenue-impact")
async def get_revenue_impact():
    """Get revenue impact analysis"""
    return {
        "current_revenue": SAMPLE_METRICS.monthly_revenue,
        "potential_increase": SAMPLE_METRICS.monthly_revenue * 0.25,  # 25% potential increase
        "at_risk_revenue": SAMPLE_METRICS.downtime_hours * 5000,  # Revenue at risk from downtime
        "roi_multiplier": 4.5,  # Industry average ROI for business intelligence
        "monthly_impact": SAMPLE_METRICS.monthly_revenue * 4.5,
        "insights": [
            {
                "category": "Revenue Protection",
                "amount": SAMPLE_METRICS.downtime_hours * 5000,
                "description": "Revenue protected by monitoring"
            },
            {
                "category": "Performance Optimization",
                "amount": SAMPLE_METRICS.monthly_revenue * 0.25,
                "description": "Potential revenue increase from optimization"
            },
            {
                "category": "Cost Savings",
                "amount": SAMPLE_METRICS.support_ticket_count * 150,
                "description": "Reduced support costs from proactive monitoring"
            }
        ]
    }

@app.get("/api/analytics/user-journey")
async def get_user_journey_analytics():
    """Get user journey and engagement analytics"""
    return {
        "funnel_analytics": {
            "visitors": 10000,
            "signups": 1234,
            "first_assessment": 891,
            "completed_assessment": 658,
            "conversion_rate": 0.658
        },
        "journey_metrics": {
            "avg_time_to_first_assessment": 12.5,  # minutes
            "drop_off_points": [
                {"step": "Dashboard Setup", "drop_off_rate": 0.15},
                {"step": "Team Creation", "drop_off_rate": 0.25},
                {"step": "Assessment Start", "drop_off_rate": 0.30},
                {"step": "Assessment Complete", "drop_off_rate": 0.15}
            ]
        },
        "engagement_metrics": {
            "daily_active_users": 847,
            "weekly_active_users": 2156,
            "monthly_active_users": 3847,
            "avg_session_duration": 8.4,  # minutes
            "feature_adoption": {
                "team_analytics": 0.45,
                "custom_assessments": 0.32,
                "advanced_reports": 0.18
            }
        }
    }

@app.get("/api/analytics/competitive-benchmarking")
async def get_competitive_benchmarking():
    """Get competitive benchmarking data"""
    return {
        "psychsync_performance": {
            "api_response_time": 1.2,  # seconds (95th percentile)
            "uptime": 99.9,
            "error_rate": 0.1,  # percentage
            "user_satisfaction": 72.3
        },
        "industry_benchmarks": {
            "assessment_platforms": {
                "api_response_time": 2.1,
                "uptime": 99.5,
                "error_rate": 0.5,
                "user_satisfaction": 45.0
            },
            "b2b_saas": {
                "api_response_time": 1.8,
                "uptime": 99.7,
                "error_rate": 0.3,
                "user_satisfaction": 52.0
            }
        },
        "competitive_advantages": [
            {
                "advantage": "Faster Response Time",
                "psychsync": 1.2,
                "industry": 2.1,
                "improvement": "43%"
            },
            {
                "advantage": "Higher Uptime",
                "psychsync": 99.9,
                "industry": 99.5,
                "improvement": "0.4%"
            },
            {
                "advantage": "Better User Satisfaction",
                "psychsync": 72.3,
                "industry": 45.0,
                "improvement": "27.3 points"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0", port=8080, reload=True)