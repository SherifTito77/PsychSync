#!/usr/bin/env python3
"""
Go-to-Market Analytics Dashboard
Comprehensive GTM performance tracking, ROI analysis, and business intelligence
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from services.customer_success_service import customer_success_service
from services.email_marketing_service import email_marketing_service
from services.gtm_service import gtm_service
from services.pricing_service import pricing_service
from services.sales_enablement_service import sales_enablement_service
from services.subscription_service import subscription_service

logger = logging.getLogger(__name__)

# Initialize FastAPI app for GTM dashboard
app = FastAPI(
    title="PsychSync Monitor - GTM Analytics Dashboard",
    description="Go-to-Market performance analytics and business intelligence",
    version="1.0.0",
)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Pydantic models for API requests
class DateRangeRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    comparison_period: Optional[str] = "previous_period"


class MetricFilterRequest(BaseModel):
    metrics: List[str]
    segments: List[str]
    channels: List[str]


class GTMOverviewResponse(BaseModel):
    total_revenue: float
    revenue_growth: float
    customer_count: int
    customer_growth: float
    conversion_rates: Dict[str, float]
    channel_performance: Dict[str, Any]
    top_campaigns: List[Dict[str, Any]]
    forecast_accuracy: float


class FunnelAnalyticsResponse(BaseModel):
    funnel_stages: Dict[str, int]
    conversion_rates: Dict[str, float]
    bottleneck_stages: List[str]
    optimization_opportunities: List[str]
    cohort_analysis: Dict[str, Any]


@app.get("/", response_class=HTMLResponse)
async def gtm_dashboard(request: Request):
    """Main GTM analytics dashboard"""
    return templates.TemplateResponse(
        "gtm_dashboard.html", {"request": request, "title": "GTM Analytics Dashboard"}
    )


@app.get("/api/overview")
async def get_gtm_overview(date_range: DateRangeRequest) -> GTMOverviewResponse:
    """Get comprehensive GTM overview metrics"""
    try:
        # Get revenue metrics
        revenue_metrics = subscription_service.get_revenue_metrics("month")
        total_revenue = revenue_metrics.get("total_revenue", 0)
        revenue_growth = revenue_metrics.get("growth_rate", 0)

        # Get customer metrics
        customer_metrics = gtm_service.get_customer_metrics()
        total_customers = len(gtm_service.leads)
        customer_growth = customer_metrics.get("growth_rate", 0)

        # Get conversion rates
        conversion_rates = {
            "visitor_to_lead": 0.12,  # 12% visitor to lead conversion
            "lead_to_qualified": 0.45,  # 45% lead to qualified conversion
            "qualified_to_demo": 0.65,  # 65% qualified to demo conversion
            "demo_to_close": 0.35,  # 35% demo to close conversion
            "free_to_paid": 0.18,  # 18% free to paid conversion
        }

        # Get channel performance
        channel_performance = gtm_service.analyze_channel_performance(
            date_range.start_date, date_range.end_date
        )

        # Get top performing campaigns
        top_campaigns = gtm_service.get_top_campaigns(10)

        # Calculate forecast accuracy
        forecast_accuracy = gtm_service.calculate_forecast_accuracy()

        return GTMOverviewResponse(
            total_revenue=total_revenue,
            revenue_growth=revenue_growth,
            customer_count=total_customers,
            customer_growth=customer_growth,
            conversion_rates=conversion_rates,
            channel_performance=channel_performance,
            top_campaigns=top_campaigns,
            forecast_accuracy=forecast_accuracy,
        )

    except Exception as e:
        logger.error(f"Error getting GTM overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get GTM overview")


@app.get("/api/funnel-analytics")
async def get_funnel_analytics(date_range: DateRangeRequest) -> FunnelAnalyticsResponse:
    """Get detailed funnel analytics and conversion analysis"""
    try:
        # Get funnel metrics
        funnel_metrics = gtm_service.get_lead_funnel_metrics(30)

        # Define funnel stages with sample data
        funnel_stages = {
            "visitors": 10000,
            "leads": 1200,
            "qualified_leads": 540,
            "demo_scheduled": 351,
            "demo_completed": 280,
            "proposals_sent": 98,
            "closed_won": 34,
        }

        # Calculate stage-to-stage conversion rates
        conversion_rates = {
            "visitor_to_lead": funnel_stages["leads"] / funnel_stages["visitors"],
            "lead_to_qualified": funnel_stages["qualified_leads"]
            / funnel_stages["leads"],
            "qualified_to_demo": funnel_stages["demo_scheduled"]
            / funnel_stages["qualified_leads"],
            "demo_to_proposal": funnel_stages["proposals_sent"]
            / funnel_stages["demo_completed"],
            "proposal_to_close": funnel_stages["closed_won"]
            / funnel_stages["proposals_sent"],
        }

        # Identify bottlenecks (conversion rates below 30%)
        bottleneck_stages = [
            stage for stage, rate in conversion_rates.items() if rate < 0.3
        ]

        # Generate optimization opportunities
        optimization_opportunities = []
        if conversion_rates["visitor_to_lead"] < 0.15:
            optimization_opportunities.append(
                "Improve landing page conversion with better value proposition"
            )
        if conversion_rates["lead_to_qualified"] < 0.5:
            optimization_opportunities.append(
                "Enhance lead scoring and qualification criteria"
            )
        if conversion_rates["qualified_to_demo"] < 0.7:
            optimization_opportunities.append(
                "Optimize demo scheduling process and follow-up"
            )
        if conversion_rates["demo_to_proposal"] < 0.4:
            optimization_opportunities.append(
                "Improve demo quality and value demonstration"
            )
        if conversion_rates["proposal_to_close"] < 0.5:
            optimization_opportunities.append(
                "Streamline proposal process and address objections proactively"
            )

        # Cohort analysis by acquisition month
        cohort_analysis = {
            "current_month": {
                "leads_generated": 180,
                "conversion_to_demo": 0.68,
                "conversion_to_close": 0.32,
                "average_deal_size": 2800,
            },
            "previous_month": {
                "leads_generated": 165,
                "conversion_to_demo": 0.62,
                "conversion_to_close": 0.28,
                "average_deal_size": 2500,
            },
            "three_months_ago": {
                "leads_generated": 140,
                "conversion_to_demo": 0.58,
                "conversion_to_close": 0.25,
                "average_deal_size": 2200,
            },
        }

        return FunnelAnalyticsResponse(
            funnel_stages=funnel_stages,
            conversion_rates=conversion_rates,
            bottleneck_stages=bottleneck_stages,
            optimization_opportunities=optimization_opportunities,
            cohort_analysis=cohort_analysis,
        )

    except Exception as e:
        logger.error(f"Error getting funnel analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get funnel analytics")


@app.get("/api/revenue-analytics")
async def get_revenue_analytics(date_range: DateRangeRequest) -> Dict[str, Any]:
    """Get detailed revenue analytics and forecasting"""
    try:
        # Get revenue metrics
        revenue_metrics = subscription_service.get_revenue_metrics("month")

        # Monthly recurring revenue breakdown
        mrr_breakdown = {
            "growth_tier": revenue_metrics.get("growth_tier_mrr", 0),
            "enterprise_tier": revenue_metrics.get("enterprise_tier_mrr", 0),
            "professional_services": revenue_metrics.get(
                "professional_services_revenue", 0
            ),
        }

        # Revenue growth trend
        revenue_growth_trend = [
            {"month": "Jan", "revenue": 45000},
            {"month": "Feb", "revenue": 52000},
            {"month": "Mar", "revenue": 61000},
            {"month": "Apr", "revenue": 73000},
            {"month": "May", "revenue": 85000},
            {"month": "Jun", "revenue": 98000},
        ]

        # Customer acquisition cost (CAC)
        cac_metrics = {
            "marketing_spend": 25000,
            "sales_spend": 35000,
            "new_customers": 45,
            "cac": 1333,  # (25000 + 35000) / 45
            "cac_ratio": 0.12,  # CAC as percentage of annual contract value
        }

        # Customer lifetime value (LTV)
        ltv_metrics = {
            "average_contract_value": 1500,
            "customer_tenure_months": 18,
            "gross_margin": 0.85,
            "ltv": 22950,  # 1500 * 18 * 0.85
            "ltv_cac_ratio": 17.2,  # 22950 / 1333
        }

        # Revenue forecasting
        forecast_revenue = gtm_service.forecast_revenue(90)  # 90-day forecast
        forecast_confidence = gtm_service.calculate_forecast_confidence()

        return {
            "mrr_breakdown": mrr_breakdown,
            "revenue_growth_trend": revenue_growth_trend,
            "cac_metrics": cac_metrics,
            "ltv_metrics": ltv_metrics,
            "forecast": {
                "next_30_days": forecast_revenue.get("next_30_days", 0),
                "next_90_days": forecast_revenue.get("next_90_days", 0),
                "confidence_score": forecast_confidence,
            },
            "key_insights": [
                "LTV:CAC ratio of 17.2x indicates healthy business model",
                "Growth tier represents 68% of MRR, showing successful free-to-paid conversion",
                "Customer acquisition efficiency improving month over month",
                "Revenue growth averaging 25% month-over-month",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get revenue analytics")


@app.get("/api/campaign-performance")
async def get_campaign_performance(date_range: DateRangeRequest) -> Dict[str, Any]:
    """Get detailed campaign performance analytics"""
    try:
        # Get email marketing analytics
        email_analytics = email_marketing_service.get_campaign_analytics(30)

        # Get GTM campaign performance
        gtm_campaigns = []
        for campaign_id, campaign in gtm_service.campaigns.items():
            performance = gtm_service.analyze_campaign_performance(campaign_id, 30)
            gtm_campaigns.append(
                {
                    "id": campaign_id,
                    "name": campaign.name,
                    "status": campaign.status,
                    "budget": campaign.budget,
                    "spend": campaign.spend,
                    "leads_generated": performance.get("leads_generated", 0),
                    "conversion_rate": performance.get("conversion_rate", 0),
                    "cost_per_lead": campaign.spend
                    / max(1, performance.get("leads_generated", 1)),
                    "roi": performance.get("roi", 0),
                }
            )

        # Sort by ROI
        gtm_campaigns.sort(key=lambda x: x["roi"], reverse=True)

        # Channel performance comparison
        channel_performance = {
            "email_marketing": {
                "leads": 320,
                "conversion_rate": 0.18,
                "cost_per_lead": 15,
                "roi": 8.5,
            },
            "content_marketing": {
                "leads": 180,
                "conversion_rate": 0.22,
                "cost_per_lead": 85,
                "roi": 4.2,
            },
            "paid_search": {
                "leads": 240,
                "conversion_rate": 0.15,
                "cost_per_lead": 120,
                "roi": 3.8,
            },
            "social_media": {
                "leads": 95,
                "conversion_rate": 0.12,
                "cost_per_lead": 45,
                "roi": 2.9,
            },
            "direct_sales": {
                "leads": 45,
                "conversion_rate": 0.35,
                "cost_per_lead": 280,
                "roi": 6.2,
            },
        }

        # Best performing content
        top_content = [
            {
                "type": "case_study",
                "title": "SaaS Company Increases Revenue 25%",
                "leads": 85,
                "conversion_rate": 0.28,
            },
            {
                "type": "webinar",
                "title": "Business Intelligence for Competitive Advantage",
                "leads": 120,
                "conversion_rate": 0.32,
            },
            {
                "type": "blog_post",
                "title": "ROI of Business Intelligence Monitoring",
                "leads": 65,
                "conversion_rate": 0.19,
            },
        ]

        return {
            "email_campaigns": email_analytics,
            "gtm_campaigns": gtm_campaigns[:10],  # Top 10 campaigns
            "channel_performance": channel_performance,
            "top_content": top_content,
            "optimization_recommendations": [
                "Increase budget for high-ROI email campaigns",
                "Optimize paid search keywords for better conversion",
                "Develop more webinar content based on success",
                "Scale case study development across industries",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting campaign performance: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get campaign performance"
        )


@app.get("/api/customer-segmentation")
async def get_customer_segmentation() -> Dict[str, Any]:
    """Get customer segmentation and cohort analysis"""
    try:
        # Get customer success portfolio overview
        portfolio_health = customer_success_service.get_portfolio_health_overview()

        # Segment customers by various dimensions
        customer_segments = {
            "by_tier": {
                "free": {
                    "count": 1200,
                    "avg_health": 0.75,
                    "upgrade_potential": 180,
                    "at_risk": 120,
                },
                "growth": {
                    "count": 85,
                    "avg_health": 0.85,
                    "upgrade_potential": 15,
                    "at_risk": 8,
                },
                "enterprise": {
                    "count": 12,
                    "avg_health": 0.92,
                    "upgrade_potential": 0,
                    "at_risk": 1,
                },
            },
            "by_industry": {
                "technology": {
                    "count": 450,
                    "avg_deal_size": 2200,
                    "retention_rate": 0.92,
                },
                "financial_services": {
                    "count": 320,
                    "avg_deal_size": 3500,
                    "retention_rate": 0.95,
                },
                "healthcare": {
                    "count": 180,
                    "avg_deal_size": 2800,
                    "retention_rate": 0.88,
                },
                "professional_services": {
                    "count": 347,
                    "avg_deal_size": 1900,
                    "retention_rate": 0.90,
                },
            },
            "by_company_size": {
                "startup": {"count": 650, "avg_revenue": 750000, "growth_rate": 0.45},
                "smb": {"count": 520, "avg_revenue": 15000000, "growth_rate": 0.32},
                "mid_market": {
                    "count": 110,
                    "avg_revenue": 125000000,
                    "growth_rate": 0.28,
                },
                "enterprise": {
                    "count": 17,
                    "avg_revenue": 2500000000,
                    "growth_rate": 0.15,
                },
            },
        }

        # Behavioral segmentation
        behavioral_segments = {
            "power_users": {
                "count": 95,
                "characteristics": [
                    "Daily login",
                    "Multiple features",
                    "Team collaboration",
                ],
                "retention_rate": 0.98,
                "expansion_potential": 0.75,
            },
            "casual_users": {
                "count": 850,
                "characteristics": ["Weekly login", "Basic features", "Individual use"],
                "retention_rate": 0.82,
                "expansion_potential": 0.35,
            },
            "at_risk_users": {
                "count": 180,
                "characteristics": [
                    "Infrequent login",
                    "Limited feature adoption",
                    "Low engagement",
                ],
                "retention_rate": 0.45,
                "expansion_potential": 0.10,
            },
            "new_users": {
                "count": 172,
                "characteristics": [
                    "Recent signup",
                    "Onboarding phase",
                    "Discovery mode",
                ],
                "retention_rate": 0.78,
                "expansion_potential": 0.60,
            },
        }

        # Cohort analysis by acquisition month
        cohort_analysis = {
            "current_quarter": {
                "customers": 145,
                "mrr": 28000,
                "retention_rate": 0.95,
                "expansion_rate": 0.12,
            },
            "previous_quarter": {
                "customers": 138,
                "mrr": 32000,
                "retention_rate": 0.92,
                "expansion_rate": 0.18,
            },
            "two_quarters_ago": {
                "customers": 125,
                "mrr": 35000,
                "retention_rate": 0.89,
                "expansion_rate": 0.22,
            },
            "three_quarters_ago": {
                "customers": 110,
                "mrr": 38000,
                "retention_rate": 0.85,
                "expansion_rate": 0.25,
            },
        }

        return {
            "portfolio_health": portfolio_health,
            "customer_segments": customer_segments,
            "behavioral_segments": behavioral_segments,
            "cohort_analysis": cohort_analysis,
            "key_insights": [
                "Enterprise customers show highest retention (95%) and lowest at-risk rates",
                "Technology and financial services are most profitable segments",
                "Power users represent best expansion opportunities (75% potential)",
                "New user onboarding improvements could increase 30-day retention by 15%",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting customer segmentation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get customer segmentation"
        )


@app.get("/api/sales-performance")
async def get_sales_performance(date_range: DateRangeRequest) -> Dict[str, Any]:
    """Get sales team performance analytics"""
    try:
        # Sales funnel metrics
        sales_metrics = gtm_service.get_sales_metrics()

        # Rep performance (sample data)
        rep_performance = [
            {
                "rep_name": "Sarah Johnson",
                "deals_closed": 12,
                "revenue_generated": 36000,
                "conversion_rate": 0.38,
                "average_deal_size": 3000,
                "sales_cycle_days": 18,
            },
            {
                "rep_name": "Michael Chen",
                "deals_closed": 8,
                "revenue_generated": 28000,
                "conversion_rate": 0.42,
                "average_deal_size": 3500,
                "sales_cycle_days": 22,
            },
            {
                "rep_name": "Emily Rodriguez",
                "deals_closed": 10,
                "revenue_generated": 45000,
                "conversion_rate": 0.45,
                "average_deal_size": 4500,
                "sales_cycle_days": 15,
            },
        ]

        # Sales playbook performance
        playbook_performance = {}
        for playbook_id, playbook in sales_enablement_service.playbooks.items():
            # Simulate playbook performance data
            conversion_rate = sum(playbook.conversion_rates.values()) / len(
                playbook.conversion_rates
            )
            playbook_performance[playbook_id] = {
                "name": playbook.name,
                "average_deal_size": playbook.average_deal_size,
                "conversion_rate": conversion_rate,
                "sales_cycle_days": playbook.sales_cycle_days,
                "usage_count": 25,
                "success_rate": 0.78,
            }

        # Competitive win rates
        competitive_wins = {
            "vs_new_relic": {
                "deals": 15,
                "wins": 11,
                "win_rate": 0.73,
                "average_deal_size": 4200,
            },
            "vs_datadog": {
                "deals": 22,
                "wins": 14,
                "win_rate": 0.64,
                "average_deal_size": 3800,
            },
            "vs_generic_bi": {
                "deals": 18,
                "wins": 16,
                "win_rate": 0.89,
                "average_deal_size": 3200,
            },
        }

        # Sales pipeline health
        pipeline_health = {
            "total_pipeline_value": 850000,
            "qualified_pipeline": 420000,
            "forecast_confidence": 0.75,
            "coverage_ratio": 3.2,  # Pipeline / quarterly quota
            "average_deal_age": 45,
            "stalled_deals": 8,
        }

        return {
            "rep_performance": rep_performance,
            "playbook_performance": playbook_performance,
            "competitive_wins": competitive_wins,
            "pipeline_health": pipeline_health,
            "performance_trends": {
                "conversion_rate_trend": [
                    {"month": "Jan", "rate": 0.32},
                    {"month": "Feb", "rate": 0.35},
                    {"month": "Mar", "rate": 0.38},
                    {"month": "Apr", "rate": 0.42},
                    {"month": "May", "rate": 0.45},
                ],
                "deal_size_trend": [
                    {"month": "Jan", "size": 2200},
                    {"month": "Feb", "size": 2450},
                    {"month": "Mar", "size": 2800},
                    {"month": "Apr", "size": 3100},
                    {"month": "May", "size": 3400},
                ],
            },
            "optimization_opportunities": [
                "Focus on displacing generic BI tools (89% win rate)",
                "Reduce sales cycle for deals over 60 days old",
                "Increase average deal size by 15% through value selling",
                "Improve conversion rates for middle-of-funnel stages",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting sales performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sales performance")


@app.get("/api/market-intelligence")
async def get_market_intelligence() -> Dict[str, Any]:
    """Get market intelligence and competitive analysis"""
    try:
        # Market share analysis
        market_share = {
            "psychsync_monitor": 0.08,  # 8% market share
            "new_relic": 0.32,
            "datadog": 0.28,
            "generic_bi": 0.22,
            "others": 0.10,
        }

        # Market growth trends
        market_trends = {
            "total_addressable_market": 2500000000,  # $2.5B
            "market_growth_rate": 0.18,  # 18% annual growth
            "psychsync_growth_rate": 0.45,  # 45% growth (faster than market)
            "market_share_trend": [
                {"year": 2022, "psychsync_share": 0.03},
                {"year": 2023, "psychsync_share": 0.05},
                {"year": 2024, "psychsync_share": 0.08},
            ],
        }

        # Competitive positioning
        competitive_positioning = {
            "price_advantage": "87% lower than New Relic",
            "setup_time_advantage": "95% faster than traditional BI",
            "roi_advantage": "3x better than industry average",
            "specialization": "Business intelligence vs technical monitoring",
        }

        # Industry opportunities
        industry_opportunities = [
            {
                "industry": "Healthcare",
                "market_size": 450000000,
                "growth_rate": 0.22,
                "psychsync_penetration": 0.05,
                "opportunity_size": 427500000,
            },
            {
                "industry": "Financial Services",
                "market_size": 680000000,
                "growth_rate": 0.18,
                "psychsync_penetration": 0.12,
                "opportunity_size": 598400000,
            },
            {
                "industry": "Manufacturing",
                "market_size": 380000000,
                "growth_rate": 0.15,
                "psychsync_penetration": 0.04,
                "opportunity_size": 364800000,
            },
        ]

        # Voice of customer insights
        customer_insights = {
            "top_buying_triggers": [
                "Competitive pressure (32% of deals)",
                "Revenue protection concerns (28%)",
                "Efficiency improvement needs (22%)",
                "Executive reporting requirements (18%)",
            ],
            "common_objections": [
                "Already have monitoring tools (45%)",
                "Budget constraints (32%)",
                "Implementation complexity (18%)",
                "Team training requirements (5%)",
            ],
            "success_factors": [
                "Clear ROI demonstration (89% of closed deals)",
                "Executive sponsorship (76%)",
                "Competitive differentiation (68%)",
                "Quick implementation timeline (62%)",
            ],
        }

        return {
            "market_share": market_share,
            "market_trends": market_trends,
            "competitive_positioning": competitive_positioning,
            "industry_opportunities": industry_opportunities,
            "customer_insights": customer_insights,
            "strategic_recommendations": [
                "Focus on healthcare and financial services expansion",
                "Emphasize ROI and speed-to-value in messaging",
                "Develop executive-targeted content and case studies",
                "Build partnerships with system integrators in target industries",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting market intelligence: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market intelligence")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
