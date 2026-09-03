#!/usr/bin/env python3
"""
HR Tech Go-to-Market Strategy
Mid-market focused GTM strategy for companies 100-1,000 employees
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class CompanySize(Enum):
    LOWER_MID = "lower_mid"  # 100-250 employees
    MID_MID = "mid_mid"      # 251-500 employees
    UPPER_MID = "upper_mid"  # 501-1000 employees

class IndustryFocus(Enum):
    TECHNOLOGY = "technology"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    PROFESSIONAL_SERVICES = "professional_services"
    RETAIL = "retail"

class BuyingPersona(Enum):
    HR_DIRECTOR = "hr_director"
    HR_BUSINESS_PARTNER = "hr_business_partner"
    PEOPLE_OPS_MANAGER = "people_ops_manager"
    TEAM_LEAD = "team_lead"
    DEPARTMENT_HEAD = "department_head"

class SalesMotion(Enum):
    PRODUCT_LED = "product_led"  # Self-service with assisted onboarding
    HYBRID = "hybrid"            # Product-led with sales assistance
    SALES_ASSISTED = "sales_assisted"  # Traditional sales with product demo

@dataclass
class IdealCustomerProfile:
    company_size: CompanySize
    industries: List[IndustryFocus]
    buying_personas: List[BuyingPersona]
    pain_points: List[str]
    budget_range: Dict[str, int]  # min, max annual HR tech budget
    decision_timeline: int  # days
    success_metrics: List[str]

@dataclass
class MarketingChannel:
    name: str
    target_persona: BuyingPersona
    cost_per_lead: float
    lead_to_demo_rate: float
    demo_to_close_rate: float
    ideal_company_size: CompanySize

@dataclass
class SalesPlay:
    name: str
    target_icp: IdealCustomerProfile
    sales_motion: SalesMotion
    average_deal_size: float
    sales_cycle_days: int
    success_rate: float
    key objections: List[str]
    value_proposition: str

class HRTechGTMStrategy:
    """Mid-market HR Tech go-to-market strategy"""

    def __init__(self):
        self.icps = self._define_ideal_customer_profiles()
        self.marketing_channels = self._define_marketing_channels()
        self.sales_plays = self._define_sales_plays()
        self.pricing_strategy = self._define_pricing_strategy()
        self.partnership_strategy = self._define_partnership_strategy()

    def _define_ideal_customer_profiles(self) -> Dict[str, IdealCustomerProfile]:
        """Define ideal customer profiles for mid-market HR Tech"""

        return {
            "growing_tech_company": IdealCustomerProfile(
                company_size=CompanySize.MID_MID,
                industries=[IndustryFocus.TECHNOLOGY],
                buying_personas=[BuyingPersona.HR_DIRECTOR, BuyingPersona.PEOPLE_OPS_MANAGER],
                pain_points=[
                    "Rapid scaling challenges",
                    "Maintaining culture during growth",
                    "Engineering team retention (high turnover risk)",
                    "Cross-functional collaboration issues",
                    "Performance management at scale"
                ],
                budget_range={"min": 50000, "max": 200000},  # $50K-200K annual HR tech budget
                decision_timeline=60,  # 60 days average decision timeline
                success_metrics=[
                    "Reduce engineering turnover by 25%",
                    "Improve team satisfaction scores by 15 points",
                    "Scale onboarding processes efficiently",
                    "Maintain culture quality while growing"
                ]
            ),

            "professional_services_firm": IdealCustomerProfile(
                company_size=CompanySize.UPPER_MID,
                industries=[IndustryFocus.PROFESSIONAL_SERVICES, IndustryFocus.FINANCIAL_SERVICES],
                buying_personas=[BuyingPersona.HR_BUSINESS_PARTNER, BuyingPersona.DEPARTMENT_HEAD],
                pain_points=[
                    "Billable hour utilization optimization",
                    "Team collaboration for client projects",
                    "Talent development and retention",
                    "Succession planning for senior roles",
                    "Cross-team knowledge sharing"
                ],
                budget_range={"min": 75000, "max": 250000},
                decision_timeline=90,
                success_metrics=[
                    "Increase billable utilization by 10%",
                    "Reduce client project delays by 20%",
                    "Improve partner-track retention by 30%",
                    "Accelerate leadership development"
                ]
            ),

            "healthcare_organization": IdealCustomerProfile(
                company_size=CompanySize.UPPER_MID,
                industries=[IndustryFocus.HEALTHCARE],
                buying_personas=[BuyingPersona.HR_DIRECTOR, BuyingPersona.TEAM_LEAD],
                pain_points=[
                    "Care team collaboration and communication",
                    "Staff burnout and retention",
                    "Inter-departmental coordination",
                    "Patient care team optimization",
                    "Leadership development in clinical settings"
                ],
                budget_range={"min": 100000, "max": 300000},
                decision_timeline=120,  # Healthcare has longer cycles
                success_metrics=[
                    "Reduce care team turnover by 40%",
                    "Improve patient satisfaction scores",
                    "Enhance inter-departmental efficiency",
                    "Reduce burnout indicators by 35%"
                ]
            ),

            "manufacturing_company": IdealCustomerProfile(
                company_size=CompanySize.LOWER_MID,
                industries=[IndustryFocus.MANUFACTURING],
                buying_personas=[BuyingPersona.HR_DIRECTOR, BuyingPersona.DEPARTMENT_HEAD],
                pain_points=[
                    "Production team efficiency",
                    "Shift collaboration and handoffs",
                    "Safety culture and compliance",
                    "Skills development and training",
                    "Multi-generational workforce management"
                ],
                budget_range={"min": 30000, "max": 120000},
                decision_timeline=45,  # Faster decisions in manufacturing
                success_metrics=[
                    "Improve production efficiency by 12%",
                    "Reduce safety incidents by 25%",
                    "Increase skills development completion by 40%",
                    "Improve shift handoff efficiency by 30%"
                ]
            )
        }

    def _define_marketing_channels(self) -> List[MarketingChannel]:
        """Define marketing channels optimized for HR Tech mid-market"""

        return [
            MarketingChannel(
                name="HR Technology Conferences",
                target_persona=BuyingPersona.HR_DIRECTOR,
                cost_per_lead=250,
                lead_to_demo_rate=0.35,
                demo_to_close_rate=0.25,
                ideal_company_size=CompanySize.UPPER_MID
            ),
            MarketingChannel(
                name="LinkedIn Thought Leadership",
                target_persona=BuyingPersona.HR_BUSINESS_PARTNER,
                cost_per_lead=85,
                lead_to_demo_rate=0.20,
                demo_to_close_rate=0.18,
                ideal_company_size=CompanySize.MID_MID
            ),
            MarketingChannel(
                name="HR Tech Review Sites",
                target_persona=BuyingPersona.PEOPLE_OPS_MANAGER,
                cost_per_lead=120,
                lead_to_demo_rate=0.28,
                demo_to_close_rate=0.22,
                ideal_company_size=CompanySize.LOWER_MID
            ),
            MarketingChannel(
                name="Webinar Series",
                target_persona=BuyingPersona.DEPARTMENT_HEAD,
                cost_per_lead=65,
                lead_to_demo_rate=0.15,
                demo_to_close_rate=0.20,
                ideal_company_size=CompanySize.MID_MID
            ),
            MarketingChannel(
                name="Content Marketing (Team Science)",
                target_persona=BuyingPersona.HR_DIRECTOR,
                cost_per_lead=95,
                lead_to_demo_rate=0.18,
                demo_to_close_rate=0.25,
                ideal_company_size=CompanySize.UPPER_MID
            ),
            MarketingChannel(
                name="Partner Referrals",
                target_persona=BuyingPersona.HR_BUSINESS_PARTNER,
                cost_per_lead=45,
                lead_to_demo_rate=0.40,
                demo_to_close_rate=0.35,
                ideal_company_size=CompanySize.MID_MID
            )
        ]

    def _define_sales_plays(self) -> List[SalesPlay]:
        """Define sales plays optimized for mid-market HR Tech"""

        return [
            SalesPlay(
                name="Rapid Scale Team Optimization",
                target_icp=self.icps["growing_tech_company"],
                sales_motion=SalesMotion.HYBRID,
                average_deal_size=45000,
                sales_cycle_days=45,
                success_rate=0.30,
                key objections=[
                    "Already using assessment tools (like PI, Gallup)",
                    "Too complex for our current stage",
                    "Need immediate results, not long-term analysis"
                ],
                value_proposition="Reduce engineering turnover by 25% and save $150K+ annually in recruitment costs while maintaining culture during rapid growth"
            ),
            SalesPlay(
                name="Billable Utilization Acceleration",
                target_icp=self.icps["professional_services_firm"],
                sales_motion=SalesMotion.SALES_ASSISTED,
                average_deal_size=75000,
                sales_cycle_days=75,
                success_rate=0.25,
                key objections=[
                    "We track utilization through our practice management system",
                    "Our teams are already highly collaborative",
                    "Concerns about behavioral data privacy in client work"
                ],
                value_proposition="Increase billable utilization by 10% and reduce client project delays by 20%, generating $200K+ additional revenue annually"
            ),
            SalesPlay(
                name="Care Team Retention Optimization",
                target_icp=self.icps["healthcare_organization"],
                sales_motion=SalesMotion.SALES_ASSISTED,
                average_deal_size=90000,
                sales_cycle_days=90,
                success_rate=0.20,
                key objections=[
                    "We have employee wellness programs already",
                    "HIPAA compliance concerns",
                    "Union environment constraints"
                ],
                value_proposition="Reduce care team turnover by 40% and improve patient satisfaction, saving $300K+ annually in recruitment and training costs"
            ),
            SalesPlay(
                name="Production Team Efficiency",
                target_icp=self.icps["manufacturing_company"],
                sales_motion=SalesMotion.PRODUCT_LED,
                average_deal_size=25000,
                sales_cycle_days=30,
                success_rate=0.35,
                key objections=[
                    "We focus on technical skills, not soft skills",
                    "Shift work makes team analysis difficult",
                    "Budget constraints for HR initiatives"
                ],
                value_proposition="Improve production efficiency by 12% and reduce safety incidents by 25%, generating $125K+ annual value"
            )
        ]

    def _define_pricing_strategy(self) -> Dict[str, Any]:
        """Define pricing strategy optimized for mid-market companies"""

        return {
            "pricing_model": "tiered_per_user_plus_success",
            "tiers": {
                "team_starter": {
                    "target_size": "5-50 users",
                    "monthly_price": 399,
                    "annual_price": 4299,  # 10% discount
                    "features": [
                        "Team behavioral assessments",
                        "Basic team optimization insights",
                        "Monthly team reports",
                        "Email support"
                    ],
                    "ideal_for": "Single teams or pilot programs"
                },
                "professional": {
                    "target_size": "51-250 users",
                    "monthly_price": 1299,
                    "annual_price": 13999,  # 10% discount
                    "features": [
                        "All Starter features",
                        "Multi-team analysis",
                        "Advanced behavioral AI insights",
                        "Integration with HRIS systems",
                        "Quarterly strategic reviews",
                        "Priority support"
                    ],
                    "ideal_for": "Growing departments and mid-market companies"
                },
                "enterprise": {
                    "target_size": "251+ users",
                    "monthly_price": 3999,
                    "annual_price": 42999,  # 10% discount
                    "features": [
                        "All Professional features",
                        "Unlimited users and teams",
                        "Custom behavioral frameworks",
                        "Advanced security and compliance",
                        "Dedicated customer success manager",
                        "Executive coaching integration",
                        "API access"
                    ],
                    "ideal_for": "Large organizations and enterprise deployments"
                }
            },
            "value_based_addons": {
                "executive_coaching": {
                    "monthly_price": 2500,
                    "description": "1:1 executive coaching based on behavioral insights"
                },
                "team_building_workshops": {
                    "monthly_price": 1500,
                    "description": "Monthly facilitated team building sessions"
                },
                "custom_analytics": {
                    "monthly_price": 1000,
                    "description": "Custom behavioral analytics and reporting"
                }
            },
            "pricing_principles": {
                "value_based": "Price based on business outcomes delivered",
                "scaling_friendly": "Easy upgrade paths as companies grow",
                "quick_time_to_value": "ROI visible within first 90 days",
                "competitive_positioning": "Premium to survey tools, value vs consulting"
            }
        }

    def _define_partnership_strategy(self) -> Dict[str, Any]:
        """Define partnership strategy for market acceleration"""

        return {
            "hris_partners": {
                "target_partners": ["BambooHR", "Workday", "UKG", "Paychex Flex"],
                "value_proposition": "Enhance HRIS platforms with behavioral intelligence",
                "go_to_market": "Co-marketing and integration partnerships"
            },
            "consulting_partners": {
                "target_partners": ["Deloitte", "Accenture", "Korn Ferry", "Mercer"],
                "value_proposition": "Provide data-driven consulting services",
                "go_to_market": "Referral and implementation partnerships"
            },
            "assessment_partners": {
                "target_partners": ["The Predictive Index", "Gallup", "Hogan Assessments"],
                "value_proposition": "Enhance existing assessments with team optimization",
                "go_to_market": "Integration and complementary offerings"
            },
            "channel_partners": {
                "target_partners": ["HR Technology Vendors", "Benefits Brokers", "PEO Providers"],
                "value_proposition": "Add behavioral intelligence to existing offerings",
                "go_to_market": "Revenue sharing and bundling opportunities"
            }
        }

    def get_target_market_segments(self) -> Dict[str, Any]:
        """Get prioritized target market segments"""

        return {
            "primary_target": {
                "segment": "Technology companies 251-500 employees",
                "reasoning": "High growth, data-driven culture, urgent retention needs",
                "market_size": "2,500 companies in North America",
                "average_deal_size": 45000,
                "win_rate": 0.30
            },
            "secondary_target": {
                "segment": "Professional services 501-1000 employees",
                "reasoning": "High value per employee, clear ROI on utilization",
                "market_size": "1,800 companies in North America",
                "average_deal_size": 75000,
                "win_rate": 0.25
            },
            "tertiary_target": {
                "segment": "Manufacturing 100-250 employees",
                "reasoning": "Untapped market, operational focus, quick decisions",
                "market_size": "3,200 companies in North America",
                "average_deal_size": 25000,
                "win_rate": 0.35
            }
        }

    def generate_acquisition_plan(self, months: int = 12) -> Dict[str, Any]:
        """Generate customer acquisition plan for specified timeframe"""

        total_target_customers = 200  # Target 200 customers in first year
        channel_allocation = {
            "partner_referrals": 0.25,      # 25% from partners
            "linkedin_thought_leadership": 0.20,  # 20% from content
            "hr_conferences": 0.15,         # 15% from events
            "webinars": 0.15,               # 15% from webinars
            "hr_tech_reviews": 0.10,       # 10% from review sites
            "content_marketing": 0.15       # 15% from content marketing
        }

        acquisition_plan = {}
        customers_needed = total_target_customers

        for channel, allocation in channel_allocation.items():
            channel_customers = int(customers_needed * allocation)

            # Calculate leads needed based on conversion rates
            if channel == "partner_referrals":
                leads_needed = int(channel_customers / 0.35)  # 35% close rate
            elif channel in ["hr_conferences", "content_marketing"]:
                leads_needed = int(channel_customers / 0.25)  # 25% close rate
            else:
                leads_needed = int(channel_customers / 0.18)  # 18% average close rate

            acquisition_plan[channel] = {
                "target_customers": channel_customers,
                "leads_needed": leads_needed,
                "budget_allocation": allocation,
                "estimated_cost": self._calculate_channel_cost(channel, leads_needed)
            }

        return {
            "total_target_customers": total_target_customers,
            "total_estimated_cost": sum(plan["estimated_cost"] for plan in acquisition_plan.values()),
            "customer_acquisition_cost": sum(plan["estimated_cost"] for plan in acquisition_plan.values()) / total_target_customers,
            "channel_breakdown": acquisition_plan,
            "monthly_targets": self._generate_monthly_targets(total_target_customers, months)
        }

    def _calculate_channel_cost(self, channel: str, leads_needed: int) -> float:
        """Calculate cost for specific marketing channel"""
        channel_costs = {
            "partner_referrals": 45,
            "linkedin_thought_leadership": 85,
            "hr_conferences": 250,
            "webinars": 65,
            "hr_tech_reviews": 120,
            "content_marketing": 95
        }

        return leads_needed * channel_costs.get(channel, 100)

    def _generate_monthly_targets(self, total_customers: int, months: int) -> List[Dict[str, Any]]:
        """Generate monthly customer acquisition targets"""
        monthly_targets = []

        # Ramp up slowly, then accelerate
        for month in range(1, months + 1):
            if month <= 3:
                # Ramp up period
                monthly_target = max(5, int(total_customers * 0.02 * month / 3))
            elif month <= 9:
                # Growth period
                monthly_target = int(total_customers * 0.12)
            else:
                # Mature period
                monthly_target = int(total_customers * 0.15)

            monthly_targets.append({
                "month": month,
                "target_customers": monthly_target,
                "cumulative_customers": sum(t["target_customers"] for t in monthly_targets)
            })

        return monthly_targets

    def get_success_metrics(self) -> Dict[str, Any]:
        """Define success metrics for GTM strategy"""

        return {
            "acquisition_metrics": {
                "marketing_qualified_leads": 1200,  # Annual target
                "sales_qualified_leads": 360,
                "demos_conducted": 180,
                "new_customers": 200,
                "customer_acquisition_cost": 2500,  # Target CAC
                "lead_to_customer_rate": 0.167  # 16.7% overall conversion
            },
            "revenue_metrics": {
                "annual_recurring_revenue": 2400000,  # $2.4M ARR target
                "average_contract_value": 12000,
                "expansion_revenue_rate": 0.20,  # 20% expansion from existing customers
                "net_revenue_retention": 0.115,  # 115% NRR (includes expansion)
                "sales_cycle_length": 60  # Days
            },
            "customer_success_metrics": {
                "implementation_time": 21,  # Days
                "time_to_value": 45,  # Days to first measurable ROI
                "customer_satisfaction_score": 4.5,  # Out of 5
                "logo_retention_rate": 0.90,  # 90% annual retention
                "expansion_rate": 0.25  # 25% of customers expand in first year
            },
            "operational_metrics": {
                "sales_team_productivity": 1000000,  # $1M ARR per sales rep
                "marketing_spend_efficiency": 3.0,  # 3x LTV:CAC ratio
                "customer_success_load": 1000000,  # $1M ARR per CSM
                "support_ticket_resolution_time": 24  # Hours
            }
        }

    def generate_competitive_positioning(self) -> Dict[str, Any]:
        """Generate competitive positioning strategy"""

        return {
            "primary_competitors": {
                "culture_amp": {
                    "strengths": ["Strong brand", "Large customer base", "Survey expertise"],
                    "weaknesses": ["Survey-focused only", "Lacks team optimization", "Expensive enterprise"],
                    "positioning": "Culture Amp measures culture, PsychSync optimizes it"
                },
                "glint": {
                    "strengths": ["Microsoft backing", "Real-time pulse surveys", "Enterprise features"],
                    "weaknesses": ["Microsoft dependency", "Limited team insights", "Complex implementation"],
                    "positioning": "Glint shows engagement, PsychSync drives performance"
                },
                "15five": {
                    "strengths": ["Performance management", "OKR tracking", "Weekly check-ins"],
                    "weaknesses": ["Manager-focused", "Limited behavioral science", "Basic analytics"],
                    "positioning": "15Five tracks performance, PsychSync improves team dynamics"
                },
                "betterup": {
                    "strengths": ["Coaching platform", "Strong executive presence", "Professional services"],
                    "weaknesses": ["Expensive per-user cost", "Limited team analysis", "Coaching dependency"],
                    "positioning": "BetterUp provides 1:1 coaching, PsychSync optimizes entire teams"
                }
            },
            "differentiation_points": [
                "Scientific behavioral frameworks vs. opinion surveys",
                "Team composition optimization vs. individual measurement",
                "Predictive insights vs. retrospective reporting",
                "Multi-source data integration vs. single platform",
                "Actionable recommendations vs. data reporting",
                "ROI-based pricing vs. per-user licensing"
            ],
            "value_matrix": {
                "psychsync": {"science": 9, "actionability": 9, "roi": 9, "implementation": 8},
                "culture_amp": {"science": 6, "actionability": 6, "roi": 7, "implementation": 7},
                "glint": {"science": 6, "actionability": 5, "roi": 6, "implementation": 5},
                "15five": {"science": 4, "actionability": 7, "roi": 7, "implementation": 8},
                "betterup": {"science": 7, "actionability": 8, "roi": 6, "implementation": 6}
            }
        }

# Initialize GTM strategy service
hr_gtm_service = HRTechGTMStrategy()
