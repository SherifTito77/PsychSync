#!/usr/bin/env python3
"""
Email Marketing Automation Service
Behavioral email campaigns with personalized content and automated triggers
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CampaignType(Enum):
    ONBOARDING = "onboarding"
    ACTIVATION = "activation"
    UPGRADE_NUDGE = "upgrade_nudge"
    WINBACK = "winback"
    FEATURE_ADOPTION = "feature_adoption"
    COMPETITIVE_INSIGHT = "competitive_insight"
    ROI_FOLLOWUP = "roi_followup"


class TriggerType(Enum):
    SIGNUP = "signup"
    DASHBOARD_CREATED = "dashboard_created"
    INSIGHT_VIEWED = "insight_viewed"
    UPGRADE_RECOMMENDATION = "upgrade_recommendation"
    USAGE_MILESTONE = "usage_milestone"
    INACTIVITY = "inactivity"
    COMPETITIVE_BENCHMARK = "competitive_benchmark"


@dataclass
class EmailTemplate:
    id: str
    name: str
    campaign_type: CampaignType
    trigger_type: TriggerType
    subject_template: str
    html_template: str
    variables: List[str]
    personalization_tokens: Dict[str, str]


@dataclass
class Campaign:
    id: str
    name: str
    campaign_type: CampaignType
    description: str
    emails: List[EmailTemplate]
    triggers: List[TriggerType]
    delay_rules: Dict[str, int]  # hours to wait after trigger
    conditions: Dict[str, Any]  # conditions for campaign execution


@dataclass
class CustomerBehavior:
    customer_id: str
    email: str
    company_name: str
    current_tier: str
    signup_date: datetime
    last_active: datetime
    dashboard_created: bool
    insights_viewed: int
    upgrade_recommendations_received: int
    usage_metrics: Dict[str, Any]
    psychsync_app_url: Optional[str] = None
    support_interactions: int = 0
    nps_score: Optional[float] = None


@dataclass
class EmailSend:
    id: str
    customer_id: str
    template_id: str
    campaign_id: str
    subject: str
    content: str
    sent_at: datetime
    opened: bool = False
    clicked: bool = False
    converted: bool = False
    revenue_impact: float = 0.0


class EmailMarketingService:
    """Automated email marketing with behavioral triggers and personalization"""

    def __init__(self):
        self.campaigns = self._initialize_campaigns()
        self.customer_behaviors = {}
        self.email_sends = []
        self.template_cache = {}

    def _initialize_campaigns(self) -> Dict[str, Campaign]:
        """Initialize all email marketing campaigns"""
        campaigns = {}

        # Onboarding Campaign
        campaigns["onboarding_welcome"] = Campaign(
            id="onboarding_welcome",
            name="PsychSync Monitor Welcome Series",
            campaign_type=CampaignType.ONBOARDING,
            description="Welcome series for new customers highlighting business value",
            emails=[
                EmailTemplate(
                    id="welcome_immediate_value",
                    name="Immediate Business Value",
                    campaign_type=CampaignType.ONBOARDING,
                    trigger_type=TriggerType.SIGNUP,
                    subject_template="Your Business Intelligence Dashboard is Ready - {company_name}",
                    html_template=self._get_welcome_template(),
                    variables=[
                        "company_name",
                        "dashboard_url",
                        "setup_completion_time",
                    ],
                    personalization_tokens={
                        "company_name": "Customer company name",
                        "dashboard_url": "Direct link to their dashboard",
                        "setup_completion_time": "Time to complete setup",
                    },
                ),
                EmailTemplate(
                    id="onboarding_first_insight",
                    name="First Insight Notification",
                    campaign_type=CampaignType.ONBOARDING,
                    trigger_type=TriggerType.DASHBOARD_CREATED,
                    subject_template="🎯 Your First Competitive Advantage is Ready",
                    html_template=self._get_first_insight_template(),
                    variables=["company_name", "insight_type", "competitive_advantage"],
                    personalization_tokens={
                        "insight_type": "Type of insight discovered",
                        "competitive_advantage": "Specific advantage metrics",
                    },
                ),
                EmailTemplate(
                    id="onboarding_feature_discovery",
                    name="Feature Discovery",
                    campaign_type=CampaignType.ONBOARDING,
                    trigger_type=TriggerType.INSIGHT_VIEWED,
                    subject_template="3 Ways to Turn {company_name} Data Into Revenue",
                    html_template=self._get_feature_discovery_template(),
                    variables=[
                        "company_name",
                        "revenue_opportunity",
                        "upgrade_potential",
                    ],
                    personalization_tokens={
                        "revenue_opportunity": "Calculated revenue impact",
                        "upgrade_potential": "Potential value from upgrade",
                    },
                ),
            ],
            triggers=[
                TriggerType.SIGNUP,
                TriggerType.DASHBOARD_CREATED,
                TriggerType.INSIGHT_VIEWED,
            ],
            delay_rules={"signup": 0, "dashboard_created": 2, "insight_viewed": 24},
            conditions={"min_tier": "free", "max_tier": "enterprise"},
        )

        # Upgrade Nudge Campaign
        campaigns["upgrade_intelligent"] = Campaign(
            id="upgrade_intelligent",
            name="Intelligent Upgrade Recommendations",
            campaign_type=CampaignType.UPGRADE_NUDGE,
            description="Personalized upgrade recommendations based on usage patterns",
            emails=[
                EmailTemplate(
                    id="upgrade_usage_spike",
                    name="Usage Spike Upgrade",
                    campaign_type=CampaignType.UPGRADE_NUDGE,
                    trigger_type=TriggerType.USAGE_MILESTONE,
                    subject_template="📈 {company_name} is Outgrowing Free Tier - Next Steps?",
                    html_template=self._get_upgrade_usage_template(),
                    variables=[
                        "company_name",
                        "usage_percentage",
                        "upgrade_benefits",
                        "roi_calculation",
                    ],
                    personalization_tokens={
                        "usage_percentage": "Current tier usage percentage",
                        "upgrade_benefits": "Specific benefits for upgrade",
                        "roi_calculation": "Personalized ROI calculation",
                    },
                ),
                EmailTemplate(
                    id="upgrade_competitive_insight",
                    name="Competitive Insight Upgrade",
                    campaign_type=CampaignType.UPGRADE_NUDGE,
                    trigger_type=TriggerType.COMPETITIVE_BENCHMARK,
                    subject_template="🏆 {company_name} vs Industry Leaders - Upgrade to See Full Analysis",
                    html_template=self._get_competitive_upgrade_template(),
                    variables=[
                        "company_name",
                        "industry_ranking",
                        "competitive_gap",
                        "enterprise_benefits",
                    ],
                    personalization_tokens={
                        "industry_ranking": "Current industry ranking",
                        "competitive_gap": "Gap vs industry leaders",
                        "enterprise_benefits": "Enterprise-tier specific benefits",
                    },
                ),
            ],
            triggers=[TriggerType.USAGE_MILESTONE, TriggerType.COMPETITIVE_BENCHMARK],
            delay_rules={"usage_milestone": 0, "competitive_benchmark": 4},
            conditions={"current_tier": "free", "upgrade_eligible": True},
        )

        # Winback Campaign
        campaigns["winback_re_engage"] = Campaign(
            id="winback_re_engage",
            name="Customer Winback Campaign",
            campaign_type=CampaignType.WINBACK,
            description="Re-engage inactive customers with new insights and value",
            emails=[
                EmailTemplate(
                    id="winback_new_insights",
                    name="New Insights Available",
                    campaign_type=CampaignType.WINBACK,
                    trigger_type=TriggerType.INACTIVITY,
                    subject_template="🔍 {company_name} - New Business Insights Waiting for You",
                    html_template=self._get_winback_insights_template(),
                    variables=[
                        "company_name",
                        "days_inactive",
                        "new_insights_count",
                        "missed_value",
                    ],
                    personalization_tokens={
                        "days_inactive": "Days since last activity",
                        "new_insights_count": "Number of new insights available",
                        "missed_value": "Estimated value they missed",
                    },
                ),
                EmailTemplate(
                    id="winback_roi_reminder",
                    name="ROI Reminder",
                    campaign_type=CampaignType.WINBACK,
                    trigger_type=TriggerType.INACTIVITY,
                    subject_template="💰 {company_name} - {missed_revenue} in Revenue Protection Waiting",
                    html_template=self._get_winback_roi_template(),
                    variables=[
                        "company_name",
                        "missed_revenue",
                        "reactivation_bonus",
                        "urgent_insights",
                    ],
                    personalization_tokens={
                        "missed_revenue": "Revenue they could have protected",
                        "reactivation_bonus": "Special offer for reactivation",
                        "urgent_insights": "Critical insights requiring attention",
                    },
                ),
            ],
            triggers=[TriggerType.INACTIVITY],
            delay_rules={"inactivity": 168},  # 1 week
            conditions={
                "days_inactive_min": 7,
                "previous_tier": ["growth", "enterprise"],
            },
        )

        # Feature Adoption Campaign
        campaigns["feature_adoption"] = Campaign(
            id="feature_adoption",
            name="Advanced Feature Adoption",
            campaign_type=CampaignType.FEATURE_ADOPTION,
            description="Encourage adoption of advanced features and integrations",
            emails=[
                EmailTemplate(
                    id="feature_slack_integration",
                    name="Slack Integration",
                    campaign_type=CampaignType.FEATURE_ADOPTION,
                    trigger_type=TriggerType.USAGE_MILESTONE,
                    subject_template="🚀 Get {company_name} Insights in Slack - Real-Time Business Intelligence",
                    html_template=self._get_slack_integration_template(),
                    variables=[
                        "company_name",
                        "integration_benefits",
                        "setup_time",
                        "productivity_gain",
                    ],
                    personalization_tokens={
                        "integration_benefits": "Benefits of Slack integration",
                        "setup_time": "Time to set up integration",
                        "productivity_gain": "Expected productivity improvement",
                    },
                ),
                EmailTemplate(
                    id="feature_custom_metrics",
                    name="Custom Metrics",
                    campaign_type=CampaignType.FEATURE_ADOPTION,
                    trigger_type=TriggerType.INSIGHT_VIEWED,
                    subject_template="📊 Create {company_name}-Specific Metrics That Drive Revenue",
                    html_template=self._get_custom_metrics_template(),
                    variables=[
                        "company_name",
                        "metric_examples",
                        "revenue_impact",
                        "setup_guide",
                    ],
                    personalization_tokens={
                        "metric_examples": "Relevant metric examples",
                        "revenue_impact": "Revenue impact of custom metrics",
                        "setup_guide": "Quick setup guide",
                    },
                ),
            ],
            triggers=[TriggerType.USAGE_MILESTONE, TriggerType.INSIGHT_VIEWED],
            delay_rules={"usage_milestone": 48, "insight_viewed": 72},
            conditions={"current_tier": ["growth", "enterprise"]},
        )

        return campaigns

    def _get_welcome_template(self) -> str:
        """Welcome email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your Business Intelligence Dashboard is Ready</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .cta { background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }
                .metrics { background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .metric { text-align: center; padding: 10px; }
                .value { font-size: 2em; font-weight: bold; color: #10b981; }
                .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 0.9em; color: #6b7280; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Your Business Intelligence Dashboard is Ready</h1>
                <p>Transform {company_name} data into competitive advantages in minutes</p>
            </div>

            <div class="content">
                <h2>Welcome to PsychSync Monitor!</h2>
                <p>Your personalized business intelligence dashboard has been automatically created and is already analyzing {company_name} performance.</p>

                <div class="metrics">
                    <div style="display: flex; justify-content: space-around;">
                        <div class="metric">
                            <div class="value">43%</div>
                            <div>Faster Response Time Than Industry</div>
                        </div>
                        <div class="metric">
                            <div class="value">27.3</div>
                            <div>Point NPS Advantage</div>
                        </div>
                        <div class="metric">
                            <div class="value">$125K</div>
                            <div>Monthly Revenue Protected</div>
                        </div>
                    </div>
                </div>

                <h3>What Your Dashboard Shows Right Now:</h3>
                <ul>
                    <li>📈 <strong>Real-time Revenue Impact</strong> - See how performance affects your bottom line</li>
                    <li>🎯 <strong>Competitive Benchmarking</strong> - Compare against industry leaders</li>
                    <li>🚀 <strong>User Journey Analytics</strong> - Identify conversion opportunities</li>
                    <li>⚡ <strong>Performance Optimization</strong> - Automated recommendations for growth</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" class="cta">View Your Dashboard →</a>
                    <p><small>Setup completed in {setup_completion_time} - 95% faster than industry average</small></p>
                </div>

                <h3>Ready for Deeper Insights?</h3>
                <p>Our Growth tier customers see <strong>189x ROI</strong> with an average <strong>1-day payback period</strong>. Upgrade to unlock:</p>
                <ul>
                    <li>Predictive analytics and forecasting</li>
                    <li>Custom metrics and reporting</li>
                    <li>Slack integration for real-time alerts</li>
                    <li>Enterprise-grade support and SLA</li>
                </ul>
            </div>

            <div class="footer">
                <p>PsychSync Monitor - Transform Technical Data into Business Intelligence</p>
                <p>You received this email because you signed up for PsychSync Monitor at {company_name}</p>
            </div>
        </body>
        </html>
        """

    def _get_upgrade_usage_template(self) -> str:
        """Upgrade usage spike template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{company_name} is Outgrowing Free Tier</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .warning { background: #fef2f2; border: 2px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .upgrade-cta { background: #10b981; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
                .roi-box { background: #f0fdf4; border: 2px solid #86efac; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .pricing { display: flex; justify-content: space-around; text-align: center; margin: 30px 0; }
                .tier { padding: 20px; border: 2px solid #e5e7eb; border-radius: 8px; }
                .enterprise { border-color: #10b981; background: #f0fdf4; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📈 Great News! {company_name} is Growing Fast</h1>
                <p>Your business intelligence usage indicates it's time to upgrade</p>
            </div>

            <div class="content">
                <div class="warning">
                    <h3>⚠️ You're at {usage_percentage}% of Free Tier Limits</h3>
                    <p>Your team is getting tremendous value from PsychSync Monitor! Based on your usage patterns, you'll hit limits soon.</p>
                </div>

                <h2>Here's What You're Risking by Staying on Free Tier:</h2>
                <ul>
                    <li>📊 <strong>Lost Insights</strong> - Only 30 days of data retention (vs 1 year in Growth)</li>
                    <li>🚫 <strong>Usage Caps</strong> - Team size and tracking limits will restrict growth</li>
                    <li>⚠️ <strong>No SLA</strong> - Revenue protection without service guarantees</li>
                    <li>📈 <strong>Missed Optimizations</strong> - Advanced analytics could save $50K+ monthly</li>
                </ul>

                <div class="roi-box">
                    <h3>💰 Your Personalized Upgrade ROI</h3>
                    <div style="font-size: 1.5em; font-weight: bold; color: #10b981; text-align: center; margin: 20px 0;">
                        {roi_calculation}
                    </div>
                    <p>Based on your current usage and industry benchmarks, upgrading to Growth tier should pay for itself in <strong>under 24 hours</strong>.</p>
                </div>

                <h3>{upgrade_benefits}</h3>

                <div class="pricing">
                    <div class="tier">
                        <h4>Current: Free Tier</h4>
                        <p>$0/month<br>Limited features<br>30-day retention</p>
                    </div>
                    <div class="tier enterprise">
                        <h4>Growth: $99/month</h4>
                        <p><strong>Unlimited insights</strong><br>90-day retention<br>Predictive analytics<br>Slack integration<br Priority support</p>
                    </div>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/upgrade?customer_id={customer_id}" class="upgrade-cta">
                        Upgrade Now - Protect Your Revenue →
                    </a>
                    <p><strong>Limited Time:</strong> First month free with code GROWTH2024</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_competitive_upgrade_template(self) -> str:
        """Competitive insight upgrade template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{company_name} vs Industry Leaders</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .ranking { background: #f0f9ff; border: 2px solid #93c5fd; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }
                .gap { background: #fef2f2; border: 2px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .enterprise-cta { background: #6366f1; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
                .competitive-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0; }
                .insight { background: #f8fafc; padding: 15px; border-radius: 6px; border-left: 4px solid #6366f1; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏆 How {company_name} Compares to Industry Leaders</h1>
                <p>Your competitive intelligence analysis is ready</p>
            </div>

            <div class="content">
                <div class="ranking">
                    <h2>Your Industry Ranking</h2>
                    <div style="font-size: 3em; font-weight: bold; color: #6366f1;">{industry_ranking}</div>
                    <p>Out of 500+ companies in your industry segment</p>
                </div>

                <div class="gap">
                    <h3>🎯 The Opportunity Gap</h3>
                    <p>Top-performing companies in your industry are achieving <strong>{competitive_gap}</strong> better results than {company_name}.</p>
                    <p>The gap represents <strong>$250K+</strong> in annual revenue opportunity.</p>
                </div>

                <h2>What Industry Leaders Do Differently:</h2>
                <div class="competitive-grid">
                    <div class="insight">
                        <h4>📊 Real-Time Decision Making</h4>
                        <p>Leaders respond to performance issues in <strong>15 minutes</strong> vs your <strong>2 hours</strong></p>
                    </div>
                    <div class="insight">
                        <h4>🎯 User Experience Optimization</h4>
                        <p>Industry leaders maintain <strong>94%</strong> user satisfaction vs your <strong>87%</strong></p>
                    </div>
                    <div class="insight">
                        <h4>⚡ Proactive Issue Prevention</h4>
                        <p>Top companies prevent <strong>78%</strong> of issues before impact vs your <strong>45%</strong></p>
                    </div>
                    <div class="insight">
                        <h4>💰 Revenue Protection</h4>
                        <p>Leaders protect <strong>$500K+</strong> monthly vs your current <strong>$125K</strong></p>
                    </div>
                </div>

                <h3>{enterprise_benefits}</h3>

                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 30px 0;">
                    <h4>🔒 Enterprise Competitive Intelligence Includes:</h4>
                    <ul>
                        <li>Detailed competitor analysis and tracking</li>
                        <li>Industry trend forecasting and predictions</li>
                        <li>Custom benchmarking against specific competitors</li>
                        <li>Quarterly competitive strategy consultations</li>
                        <li>API access for custom competitive dashboards</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/enterprise-intelligence?customer_id={customer_id}" class="enterprise-cta">
                        Unlock Competitive Intelligence →
                    </a>
                    <p><strong>Enterprise Tier:</strong> $499/month for unlimited competitive intelligence</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_winback_insights_template(self) -> str:
        """Winback insights template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Business Insights Waiting for You</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .insights-summary { background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .missed-value { background: #fef2f2; border: 2px solid #fecaca; padding: 15px; border-radius: 6px; margin: 15px 0; }
                .reactivation-cta { background: #06b6d4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 15px 0; }
                .insight-item { background: #f8fafc; padding: 10px; margin: 10px 0; border-left: 3px solid #06b6d4; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 {company_name} - We've Found Something Important</h1>
                <p>New business insights that require your attention</p>
            </div>

            <div class="content">
                <h2>While You Were Away ({days_inactive} days)</h2>

                <div class="insights-summary">
                    <h3>📊 New Insights Discovered</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #06b6d4; text-align: center;">
                        {new_insights_count} Critical Insights
                    </div>
                </div>

                <h3>What You've Missed:</h3>
                <div class="insight-item">
                    <strong>Revenue Protection Alert</strong> - Potential $15K monthly revenue at risk due to performance trends
                </div>
                <div class="insight-item">
                    <strong>Competitive Movement</strong> - 3 competitors made significant improvements that affect your market position
                </div>
                <div class="insight-item">
                    <strong>User Experience Drop</strong> - 12% decrease in user satisfaction requiring immediate attention
                </div>
                <div class="insight-item">
                    <strong>Growth Opportunity</strong> - New market segment showing 40% higher conversion rates
                </div>

                <div class="missed-value">
                    <h4>💰 Estimated Value Missed</h4>
                    <p style="font-size: 1.5em; font-weight: bold; color: #dc2626;">{missed_value}</p>
                    <p>These insights could have generated significant value if addressed earlier.</p>
                </div>

                <h3>Why This Matters Now:</h3>
                <ul>
                    <li>⚡ <strong>Time-Sensitive Opportunities</strong> - Some insights have expiration dates</li>
                    <li>📈 <strong>Trend Acceleration</strong> - Performance trends are accelerating rapidly</li>
                    <li>🏆 <strong>Competitive Response</strong> - Competitors are acting on similar intelligence</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/dashboard?customer_id={customer_id}&welcome_back=true" class="reactivation-cta">
                        Review Your Insights Now →
                    </a>
                    <p><small>Your dashboard has been updated with all new analysis</small></p>
                </div>

                <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h4>🎯 Quick Start (2 minutes)</h4>
                    <ol>
                        <li>Review the 3 starred insights (highest impact)</li>
                        <li>Check your competitive ranking changes</li>
                        <li>Set up alerts for critical metrics</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_slack_integration_template(self) -> str:
        """Slack integration template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Get {company_name} Insights in Slack</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .integration-preview { background: #f0fdf4; border: 2px solid #86efac; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .setup-steps { background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .slack-cta { background: #10b981; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
                .benefit { background: #f0f9ff; padding: 10px; margin: 10px 0; border-radius: 6px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Real-Time Business Intelligence in Slack</h1>
                <p>Get {company_name} insights where your team already works</p>
            </div>

            <div class="content">
                <h2>Slack Integration: {integration_benefits}</h2>

                <div class="integration-preview">
                    <h3>📱 What You'll See in Slack:</h3>
                    <div style="background: #ffffff; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 0.9em;">
                        <div><strong>🔔 PsychSync Monitor Alert</strong></div>
                        <div>{company_name} performance improved by 15% this week</div>
                        <div>Competitive ranking: #3 → #2 in industry segment</div>
                        <div>Revenue protection: $142K this month (↑$17K)</div>
                        <div><a href="#">View Dashboard →</a></div>
                    </div>
                </div>

                <h3>Key Benefits for {company_name}:</h3>
                <div class="benefit">
                    <strong>⚡ Instant Response Time</strong> - React to issues in minutes, not hours
                </div>
                <div class="benefit">
                    <strong>📊 Team Visibility</strong> - Everyone sees the same business intelligence
                </div>
                <div class="benefit">
                    <strong>🎯 Targeted Alerts</strong> - Only important insights, no noise
                </div>
                <div class="benefit">
                    <strong>📈 Trend Tracking</strong> - Daily/weekly summaries of key metrics
                </div>

                <h3>Setup in {setup_time} (3 steps):</h3>
                <div class="setup-steps">
                    <ol>
                        <li><strong>Connect Slack</strong> - Authorize PsychSync Monitor in your Slack workspace</li>
                        <li><strong>Choose Channel</strong> - Select #business-intelligence or create a dedicated channel</li>
                        <li><strong>Configure Alerts</strong> - Pick which insights to share (revenue, competitive, user experience)</li>
                    </ol>
                </div>

                <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 30px 0;">
                    <h3>📈 Expected Productivity Gain</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #10b981; text-align: center;">
                        {productivity_gain}
                    </div>
                    <p style="text-align: center;">Teams with Slack integration respond 4x faster to business opportunities</p>
                </div>

                <h3>Popular Alert Types:</h3>
                <ul>
                    <li>💰 <strong>Revenue Impact</strong> - When performance changes affect revenue</li>
                    <li>🏆 <strong>Competitive Moves</strong> - When competitors gain/lose market position</li>
                    <li>📉 <strong>User Experience</strong> - When customer satisfaction drops significantly</li>
                    <li>🎯 <strong>Growth Opportunities</strong> - When new optimization opportunities appear</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/integrations/slack?customer_id={customer_id}" class="slack-cta">
                        Connect Slack Now →
                    </a>
                    <p><strong>Growth & Enterprise Feature:</strong> Included in your current plan</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_custom_metrics_template(self) -> str:
        """Custom metrics template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Create {company_name}-Specific Metrics</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .metric-examples { background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .revenue-impact { background: #f0fdf4; border: 2px solid #86efac; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .setup-cta { background: #8b5cf6; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
                .example { background: #fef2f2; padding: 10px; margin: 10px 0; border-radius: 6px; border-left: 3px solid #8b5cf6; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Metrics That Matter to {company_name}</h1>
                <p>Create custom business intelligence tailored to your specific goals</p>
            </div>

            <div class="content">
                <h2>Why Custom Metrics Drive {revenue_impact} in Revenue</h2>

                <div class="revenue-impact">
                    <h3>💰 The Custom Metrics Advantage</h3>
                    <p>Companies using custom metrics see <strong>40% higher revenue growth</strong> because they:</p>
                    <ul>
                        <li>Track what actually matters to their business model</li>
                        <li>Identify opportunities specific to their industry</li>
                        <li>Align team goals with revenue outcomes</li>
                        <li>Predict issues before standard metrics detect them</li>
                    </ul>
                </div>

                <h3>Custom Metrics for {company_name} Industry:</h3>
                <div class="metric-examples">
                    <div class="example">
                        <strong>🎯 Assessment Completion Funnel Velocity</strong><br>
                        Track how quickly users move from assessment start to completion and identify drop-off points
                    </div>
                    <div class="example">
                        <strong>💼 Team Performance Score</strong><br>
                        Combine individual assessment results into team effectiveness metrics
                    </div>
                    <div class="example">
                        <strong>📈 Revenue per Assessment</strong><br>
                        Calculate the direct revenue impact of each assessment completed
                    </div>
                    <div class="example">
                        <strong>🔄 User Engagement Quality</strong><br>
                        Measure not just if users engage, but the quality and business impact of that engagement
                    </div>
                </div>

                <h3>Popular Custom Metric Categories:</h3>
                <ul>
                    <li>📊 <strong>Business Impact Metrics</strong> - Revenue, cost savings, efficiency gains</li>
                    <li>👥 <strong>Team Performance</strong> - Collaboration, productivity, satisfaction scores</li>
                    <li>🎯 <strong>Conversion Metrics</strong> - Assessment completion, upgrade rates, retention</li>
                    <li>⚡ <strong>Operational Efficiency</strong> - Support ticket reduction, time savings, automation</li>
                </ul>

                <h3>Quick Setup Guide ({setup_guide}):</h3>
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <ol>
                        <li><strong>Define Your KPIs</strong> - Choose 3-5 metrics that drive your revenue</li>
                        <li><strong>Connect Data Sources</strong> - Link PsychSync, CRM, financial systems</li>
                        <li><strong>Set Calculations</strong> - Define how metrics are calculated and weighted</li>
                        <li><strong>Configure Alerts</strong> - Set thresholds for important changes</li>
                        <li><strong>Create Dashboards</strong> - Build views for different teams and stakeholders</li>
                    </ol>
                </div>

                <h3>Success Stories:</h3>
                <ul>
                    <li><strong>SaaS Company:</strong> 25% revenue increase by tracking "Qualified Lead per Assessment"</li>
                    <li><strong>Consulting Firm:</strong> 40% efficiency gain by monitoring "Project Profitability per Team"</li>
                    <li><strong>Enterprise:</strong> $2M cost savings through "Process Automation Impact" metrics</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/custom-metrics?customer_id={customer_id}" class="setup-cta">
                        Create Your Custom Metrics →
                    </a>
                    <p><strong>Enterprise Feature:</strong> Unlimited custom metrics included in your plan</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_first_insight_template(self) -> str:
        """First insight notification template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your First Competitive Advantage is Ready</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .insight-box { background: #eff6ff; border: 2px solid #93c5fd; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .advantage { background: #f0fdf4; border: 2px solid #86efac; padding: 15px; border-radius: 6px; margin: 15px 0; }
                .dashboard-cta { background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Congratulations! Your First Insight is Ready</h1>
                <p>We've discovered your initial competitive advantage</p>
            </div>

            <div class="content">
                <h2>Your First Business Intelligence: {insight_type}</h2>

                <div class="insight-box">
                    <h3>🏆 Competitive Advantage Identified</h3>
                    <div style="font-size: 1.5em; font-weight: bold; color: #3b82f6; text-align: center; margin: 20px 0;">
                        {competitive_advantage}
                    </div>
                    <p>This represents a significant advantage over 70% of companies in your industry segment.</p>
                </div>

                <div class="advantage">
                    <h4>What This Means for {company_name}:</h4>
                    <p>Your performance in this area is driving better business outcomes than most competitors. This specific advantage is likely contributing to higher user satisfaction and revenue retention.</p>
                </div>

                <h3>What's Next:</h3>
                <ul>
                    <li>📊 <strong>Explore More Insights</strong> - Your dashboard has 5+ additional advantages identified</li>
                    <li>🎯 <strong>Set Up Alerts</strong> - Get notified when this advantage changes</li>
                    <li>📈 <strong>Track Progress</strong> - Monitor how this advantage evolves over time</li>
                    <li>💰 <strong>Calculate Impact</strong> - See the revenue impact of this advantage</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}?insight=first" class="dashboard-cta">
                        View All Your Insights →
                    </a>
                    <p><small>This is just the beginning - your competitive intelligence grows richer over time</small></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_feature_discovery_template(self) -> str:
        """Feature discovery template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Turn {company_name} Data Into Revenue</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .revenue-box { background: #fef3c7; border: 2px solid #fcd34d; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .feature { background: #f8fafc; padding: 15px; margin: 15px 0; border-radius: 6px; border-left: 3px solid #f59e0b; }
                .explore-cta { background: #f59e0b; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>💰 3 Ways to Turn {company_name} Data Into Revenue</h1>
                <p>You've got insights - here's how to monetize them</p>
            </div>

            <div class="content">
                <h2>Your Revenue Opportunity</h2>

                <div class="revenue-box">
                    <h3>📈 Monthly Revenue Opportunity Identified</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #d97706; text-align: center;">
                        {revenue_opportunity}
                    </div>
                    <p>Based on your current insights and industry benchmarks</p>
                </div>

                <h3>3 Revenue-Driving Strategies:</h3>

                <div class="feature">
                    <h4>1. 🎯 Optimize User Experience</h4>
                    <p><strong>Impact:</strong> $15K-$25K monthly revenue increase</p>
                    <p>Your insights show specific user experience improvements that could increase conversion rates by 12%. Focus on the assessment completion funnel where drop-offs are highest.</p>
                </div>

                <div class="feature">
                    <h4>2. 🏆 Leverage Competitive Advantages</h4>
                    <p><strong>Impact:</strong> $20K-$35K monthly revenue protection</p>
                    <p>You have 3 identified competitive advantages. Marketing these differentiators could increase market share and justifying premium pricing.</p>
                </div>

                <div class="feature">
                    <h4>3. 📊 Predictive Resource Allocation</h4>
                    <p><strong>Impact:</strong> $10K-$20K monthly cost savings</p>
                    <p>Your usage patterns predict optimal resource allocation. Redirect resources from low-impact areas to high-ROI opportunities identified in your insights.</p>
                </div>

                <h3>Upgrade Potential</h3>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p><strong>{upgrade_potential}</strong> with Growth tier features:</p>
                    <ul>
                        <li>Predictive analytics for revenue forecasting</li>
                        <li>Advanced segmentation for targeted optimization</li>
                        <li>Automated recommendations for revenue optimization</li>
                        <li>Custom revenue impact metrics</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/revenue-optimization?customer_id={customer_id}" class="explore-cta">
                        Explore Revenue Features →
                    </a>
                    <p><small>Free customers who upgrade see 3x faster revenue growth</small></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_winback_roi_template(self) -> str:
        """Winback ROI reminder template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{missed_revenue} in Revenue Protection Waiting</title>
            <style>
                body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #1f2937; }
                .header { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 40px 20px; text-align: center; }
                .content { padding: 40px 20px; max-width: 600px; margin: 0 auto; }
                .urgent-alert { background: #fef2f2; border: 2px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .bonus-offer { background: #f0fdf4; border: 2px solid #86efac; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .reactivation-cta { background: #dc2626; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
                .urgent-item { background: #fef3c7; padding: 10px; margin: 10px 0; border-radius: 6px; border-left: 3px solid #dc2626; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>💰 Urgent: {missed_revenue} at Risk for {company_name}</h1>
                <p>Critical revenue protection insights need your immediate attention</p>
            </div>

            <div class="content">
                <div class="urgent-alert">
                    <h3>🚨 CRITICAL: Revenue Protection at Risk</h3>
                    <p>You haven't checked your business intelligence in {days_inactive} days. During this time, <strong>{missed_revenue}</strong> in potential revenue protection has been missed.</p>
                </div>

                <h3>🔥 Urgent Insights Requiring Immediate Action:</h3>
                <div class="urgent-item">
                    <strong>Performance Degradation Detected</strong><br>
                    Response times have increased by 35%, affecting customer satisfaction and potentially causing $8K monthly revenue loss
                </div>
                <div class="urgent-item">
                    <strong>Competitive Threat Identified</strong><br>
                    2 competitors have made improvements that put them ahead of {company_name} in key performance areas
                </div>
                <div class="urgent-item">
                    <strong>User Experience Alert</strong><br>
                    Customer satisfaction scores have dropped below critical threshold, risking churn and revenue
                </div>

                <div class="bonus-offer">
                    <h3>🎁 Special Reactivation Bonus</h3>
                    <p>Come back now and we'll add <strong>{reactivation_bonus}</strong> in premium features free for 3 months:</p>
                    <ul>
                        <li>Advanced predictive analytics</li>
                        <li>Custom competitive intelligence</li>
                        <li>Priority support and monitoring</li>
                        <li>Quarterly business reviews</li>
                    </ul>
                </div>

                <h3>Why This Can't Wait:</h3>
                <ul>
                    <li>⏰ <strong>Time-Sensitive</strong> - Performance issues compound daily without intervention</li>
                    <li>💸 <strong>Revenue Impact</strong> - Every day costs {company_name} money in lost optimization opportunities</li>
                    <li>🏆 <strong>Competitive Risk</strong> - Competitors are actively using similar intelligence to gain market share</li>
                    <li>👥 <strong>Customer Impact</strong> - User experience issues directly affect retention and revenue</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://monitor.psychsync.com/urgent-dashboard?customer_id={customer_id}&reactivation=true" class="reactivation-cta">
                        Protect Your Revenue Now →
                    </a>
                    <p><strong>Limited Time:</strong> Reactivation bonus expires in 48 hours</p>
                </div>

                <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h4>🚀 Immediate Action Plan (5 minutes):</h4>
                    <ol>
                        <li>Review urgent alerts (highlighted in red)</li>
                        <li>Check revenue protection dashboard</li>
                        <li>Compare vs competitors (updated rankings)</li>
                        <li>Set up critical alerts to prevent future issues</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """

    def track_customer_behavior(
        self, customer_data: Dict[str, Any]
    ) -> CustomerBehavior:
        """Track customer behavior for campaign triggers"""
        customer_id = customer_data.get("customer_id")

        if customer_id not in self.customer_behaviors:
            self.customer_behaviors[customer_id] = CustomerBehavior(
                customer_id=customer_id,
                email=customer_data.get("email"),
                company_name=customer_data.get("company_name"),
                current_tier=customer_data.get("tier", "free"),
                signup_date=customer_data.get("signup_date", datetime.now()),
                last_active=customer_data.get("last_active", datetime.now()),
                dashboard_created=customer_data.get("dashboard_created", False),
                insights_viewed=customer_data.get("insights_viewed", 0),
                upgrade_recommendations_received=customer_data.get(
                    "upgrade_recommendations_received", 0
                ),
                usage_metrics=customer_data.get("usage_metrics", {}),
                psychsync_app_url=customer_data.get("psychsync_app_url"),
                support_interactions=customer_data.get("support_interactions", 0),
                nps_score=customer_data.get("nps_score"),
            )

        return self.customer_behaviors[customer_id]

    def trigger_campaign(
        self,
        customer_id: str,
        trigger_type: TriggerType,
        trigger_data: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Trigger email campaigns based on customer behavior"""
        triggered_emails = []

        if customer_id not in self.customer_behaviors:
            logger.warning(f"Customer {customer_id} not found in behavior tracking")
            return triggered_emails

        behavior = self.customer_behaviors[customer_id]

        for campaign_id, campaign in self.campaigns.items():
            if trigger_type in campaign.triggers:
                if self._check_campaign_conditions(campaign, behavior, trigger_data):
                    emails = self._execute_campaign(campaign, behavior, trigger_data)
                    triggered_emails.extend(emails)

        return triggered_emails

    def _check_campaign_conditions(
        self,
        campaign: Campaign,
        behavior: CustomerBehavior,
        trigger_data: Optional[Dict[str, Any]],
    ) -> bool:
        """Check if campaign conditions are met"""
        conditions = campaign.conditions

        # Check tier conditions
        if "current_tier" in conditions:
            if isinstance(conditions["current_tier"], list):
                if behavior.current_tier not in conditions["current_tier"]:
                    return False
            elif behavior.current_tier != conditions["current_tier"]:
                return False

        # Check min/max tier conditions
        if "min_tier" in conditions:
            tier_hierarchy = {"free": 1, "growth": 2, "enterprise": 3}
            if tier_hierarchy.get(behavior.current_tier, 0) < tier_hierarchy.get(
                conditions["min_tier"], 0
            ):
                return False

        if "max_tier" in conditions:
            tier_hierarchy = {"free": 1, "growth": 2, "enterprise": 3}
            if tier_hierarchy.get(behavior.current_tier, 0) > tier_hierarchy.get(
                conditions["max_tier"], 0
            ):
                return False

        # Check usage conditions
        if "upgrade_eligible" in conditions and conditions["upgrade_eligible"]:
            # Simple heuristic: if they're using >80% of tier limits
            usage_percentage = (
                trigger_data.get("usage_percentage", 0) if trigger_data else 0
            )
            if usage_percentage < 80:
                return False

        # Check inactivity conditions
        if "days_inactive_min" in conditions:
            days_inactive = (datetime.now() - behavior.last_active).days
            if days_inactive < conditions["days_inactive_min"]:
                return False

        return True

    def _execute_campaign(
        self,
        campaign: Campaign,
        behavior: CustomerBehavior,
        trigger_data: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Execute campaign and send relevant emails"""
        sent_emails = []

        for email_template in campaign.emails:
            if email_template.trigger_type in [t for t in campaign.triggers]:
                # Check delay rules
                delay_hours = campaign.delay_rules.get(
                    email_template.trigger_type.value, 0
                )
                if delay_hours > 0:
                    # In production, this would schedule the email for later
                    # For now, we'll simulate immediate sending
                    pass

                # Personalize and send email
                email_id = self._send_personalized_email(
                    email_template, behavior, trigger_data
                )
                sent_emails.append(email_id)

        return sent_emails

    def _send_personalized_email(
        self,
        template: EmailTemplate,
        behavior: CustomerBehavior,
        trigger_data: Optional[Dict[str, Any]],
    ) -> str:
        """Send personalized email using template"""
        # Personalization variables
        variables = {
            "company_name": behavior.company_name,
            "customer_id": behavior.customer_id,
            "dashboard_url": f"https://monitor.psychsync.com/dashboard?customer_id={behavior.customer_id}",
            "setup_completion_time": "2 minutes",
            "insight_type": "Performance Advantage",
            "competitive_advantage": "43% faster response time than industry",
            "revenue_opportunity": "$25K-$50K monthly",
            "upgrade_potential": "3x revenue acceleration",
            "usage_percentage": (
                trigger_data.get("usage_percentage", 85) if trigger_data else 85
            ),
            "roi_calculation": "189x ROI with 1-day payback period",
            "industry_ranking": "#12 in industry segment",
            "competitive_gap": "25% better user satisfaction",
            "enterprise_benefits": "Unlimited competitive intelligence and custom metrics",
            "days_inactive": (datetime.now() - behavior.last_active).days,
            "new_insights_count": "7 critical insights",
            "missed_value": "$15K in optimization opportunities",
            "missed_revenue": "$50K monthly",
            "reactivation_bonus": "3 months free Enterprise features",
            "urgent_insights": "Performance degradation and competitive threats",
            "integration_benefits": "Real-time alerts where your team works",
            "setup_time": "2 minutes",
            "productivity_gain": "4x faster response time",
            "revenue_impact": "40% higher revenue growth",
            "metric_examples": "Assessment velocity, team performance, revenue per assessment",
            "setup_guide": "5-minute quick start",
        }

        # Add trigger-specific variables
        if trigger_data:
            variables.update(trigger_data)

        # Personalize subject and content
        subject = template.subject_template.format(**variables)
        content = template.html_template.format(**variables)

        # Create email send record
        email_send = EmailSend(
            id=f"email_{len(self.email_sends) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            customer_id=behavior.customer_id,
            template_id=template.id,
            campaign_id=template.campaign_type.value,
            subject=subject,
            content=content,
            sent_at=datetime.now(),
        )

        self.email_sends.append(email_send)

        # In production, this would send via email service provider
        logger.info(f"Email sent: {subject} to {behavior.email}")

        return email_send.id

    def get_campaign_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get campaign performance analytics"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_sends = [s for s in self.email_sends if s.sent_at >= cutoff_date]

        analytics = {
            "total_emails_sent": len(recent_sends),
            "campaigns_sent": {},
            "performance_metrics": {
                "open_rate": 0.35,  # Simulated
                "click_rate": 0.12,
                "conversion_rate": 0.04,
                "revenue_generated": 125000,
            },
            "top_performing_campaigns": [],
        }

        # Group by campaign
        for send in recent_sends:
            campaign_id = send.campaign_id
            if campaign_id not in analytics["campaigns_sent"]:
                analytics["campaigns_sent"][campaign_id] = {
                    "emails_sent": 0,
                    "opens": 0,
                    "clicks": 0,
                    "conversions": 0,
                    "revenue": 0,
                }

            analytics["campaigns_sent"][campaign_id]["emails_sent"] += 1
            if send.opened:
                analytics["campaigns_sent"][campaign_id]["opens"] += 1
            if send.clicked:
                analytics["campaigns_sent"][campaign_id]["clicks"] += 1
            if send.converted:
                analytics["campaigns_sent"][campaign_id]["conversions"] += 1

        return analytics

    def get_customer_email_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get email history for a specific customer"""
        customer_emails = [s for s in self.email_sends if s.customer_id == customer_id]

        return [
            {
                "email_id": s.id,
                "campaign": s.campaign_id,
                "subject": s.subject,
                "sent_at": s.sent_at.isoformat(),
                "opened": s.opened,
                "clicked": s.clicked,
                "converted": s.converted,
                "revenue_impact": s.revenue_impact,
            }
            for s in sorted(customer_emails, key=lambda x: x.sent_at, reverse=True)
        ]
