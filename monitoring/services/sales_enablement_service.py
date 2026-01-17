#!/usr/bin/env python3
"""
Sales Enablement Service
Provides sales teams with tools, content, and playbooks for effective revenue generation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class SalesPlayType(Enum):
    OUTBOUND_PROSPECTING = "outbound_prospecting"
    INBOUND_FOLLOWUP = "inbound_followup"
    UPGRADE_CONVERSATION = "upgrade_conversation"
    ENTERPRISE_DEAL = "enterprise_deal"
    COMPETITIVE_DISPLACEMENT = "competitive_displacement"
    WINBACK_CAMPAIGN = "winback_campaign"
    EXPANSION_RENEWAL = "expansion_renewal"

class CustomerSegment(Enum):
    STARTUP = "startup"  # 1-50 employees, <$1M revenue
    SMB = "smb"  # 50-500 employees, $1M-50M revenue
    MID_MARKET = "mid_market"  # 500-2000 employees, $50M-500M revenue
    ENTERPRISE = "enterprise"  # 2000+ employees, >$500M revenue

class IndustryType(Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    PROFESSIONAL_SERVICES = "professional_services"
    EDUCATION = "education"
    GOVERNMENT = "government"

@dataclass
class SalesPlaybook:
    id: str
    name: str
    play_type: SalesPlayType
    target_segments: List[CustomerSegment]
    target_industries: List[IndustryType]
    description: str
    objectives: List[str]
    key_messages: List[str]
    objection_handling: Dict[str, str]
    success_criteria: List[str]
    average_deal_size: float
    sales_cycle_days: int
    conversion_rates: Dict[str, float]
    required_assets: List[str]

@dataclass
class CompetitiveIntelligence:
    competitor: str
    strengths: List[str]
    weaknesses: List[str]
    positioning: str
    pricing_comparison: Dict[str, str]
    win_themes: List[str]
    loss_themes: List[str]
    displacement_tactics: List[str]

@dataclass
class SalesAsset:
    id: str
    name: str
    asset_type: str  # presentation, one-pager, case_study, roi_calculator, demo_script
    description: str
    target_audience: str
    content: str
    usage_instructions: str
    success_metrics: List[str]
    last_updated: datetime

@dataclass
class SalesConversationGuide:
    id: str
    scenario: str
    conversation_stages: List[Dict[str, Any]]
    key_questions: List[str]
    value_proposition: str
    roi_framework: Dict[str, Any]
    next_steps: List[str]
    success_indicators: List[str]

class SalesEnablementService:
    """Comprehensive sales enablement platform with playbooks, content, and intelligence"""

    def __init__(self):
        self.playbooks = self._initialize_playbooks()
        self.competitive_intelligence = self._initialize_competitive_intelligence()
        self.sales_assets = self._initialize_sales_assets()
        self.conversation_guides = self._initialize_conversation_guides()
        self.performance_tracking = {}

    def _initialize_playbooks(self) -> Dict[str, SalesPlaybook]:
        """Initialize comprehensive sales playbooks"""
        playbooks = {}

        # Outbound Prospecting Playbook
        playbooks["outbound_prospecting"] = SalesPlaybook(
            id="outbound_prospecting",
            name="High-Growth Company Outbound Prospecting",
            play_type=SalesPlayType.OUTBOUND_PROSPECTING,
            target_segments=[CustomerSegment.STARTUP, CustomerSegment.SMB],
            target_industries=[IndustryType.TECHNOLOGY, IndustryType.PROFESSIONAL_SERVICES],
            description="Outbound playbook for prospecting high-growth companies with personalized business intelligence messaging",
            objectives=[
                "Secure initial discovery meeting",
                "Identify specific business pain points",
                "Establish value of business intelligence",
                "Create urgency for competitive insights"
            ],
            key_messages=[
                "Companies using business intelligence grow 40% faster",
                "Your competitors are already using similar insights",
                "We can show you $125K+ in monthly revenue opportunities",
                "Setup takes 2 minutes, value is immediate"
            ],
            objection_handling={
                "Too expensive": "Our Growth tier is $99/month - less than 1 hour of consulting time for insights that save $150K+ annually",
                "No time": "Setup takes 2 minutes. Most customers see value within their first dashboard view",
                "Already have tools": "Do your current tools connect business impact to technical performance in real-time?",
                "Not interested": "I understand - would you be interested in seeing how your competitors are using business intelligence to gain market share?"
            },
            success_criteria=[
                "Booked discovery meeting",
                "Identified 3+ specific pain points",
                "Customer agrees to demo",
                "Technical stakeholder involved"
            ],
            average_deal_size=2500.0,
            sales_cycle_days=14,
            conversion_rates={
                "email_to_meeting": 0.08,
                "meeting_to_demo": 0.65,
                "demo_to_proposal": 0.45,
                "proposal_to_close": 0.70
            },
            required_assets=["personalized_outreach_template", "competitive_intelligence_report", "roi_calculator"]
        )

        # Upgrade Conversation Playbook
        playbooks["upgrade_conversation"] = SalesPlaybook(
            id="upgrade_conversation",
            name="Free-to-Paid Customer Upgrade",
            play_type=SalesPlayType.UPGRADE_CONVERSATION,
            target_segments=[CustomerSegment.STARTUP, CustomerSegment.SMB],
            target_industries=list(IndustryType),
            description="Playbook for converting free tier customers to paid plans using usage data and ROI insights",
            objectives=[
                "Identify upgrade triggers based on usage",
                "Demonstrate clear ROI for upgrade",
                "Remove barriers to upgrade decision",
                "Process upgrade immediately"
            ],
            key_messages=[
                "You're currently at {usage_percentage}% of free tier limits",
                "Growth tier customers see 189x ROI with 1-day payback",
                "You're missing $X in monthly value by staying on free tier",
                "Upgrade takes 30 seconds and benefits are immediate"
            ],
            objection_handling={
                "Happy with free": "I'm glad you're finding value! Based on your usage, you're leaving $X on the table each month",
                "Too expensive": "$99/month is less than 2 hours of employee time for insights that save $10K+ monthly",
                "Don't need features": "It's not about features - it's about the $125K+ in revenue protection you're currently missing",
                "Need to think": "I understand. Can I show you exactly how much revenue you're missing while you decide?"
            },
            success_criteria=[
                "Customer identifies upgrade value",
                "ROI calculation accepted",
                "Payment method provided",
                "Upgrade completed in call"
            ],
            average_deal_size=1188.0,
            sales_cycle_days=3,
            conversion_rates={
                "outreach_to_meeting": 0.25,
                "meeting_to_upgrade": 0.80,
                "upgrade_to_success": 0.90
            },
            required_assets=["usage_report", "roi_analysis", "upgrade_comparison_chart", "competitive_intelligence"]
        )

        # Enterprise Deal Playbook
        playbooks["enterprise_deal"] = SalesPlaybook(
            id="enterprise_deal",
            name="Enterprise Strategic Deal",
            play_type=SalesPlayType.ENTERPRISE_DEAL,
            target_segments=[CustomerSegment.MID_MARKET, CustomerSegment.ENTERPRISE],
            target_industries=[IndustryType.TECHNOLOGY, IndustryType.FINANCIAL_SERVICES, IndustryType.HEALTHCARE],
            description="Enterprise sales playbook for strategic deals with custom requirements and SLA guarantees",
            objectives=[
                "Identify strategic business requirements",
                "Align with executive stakeholders",
                "Demonstrate enterprise-grade capabilities",
                "Secure multi-year commitment"
            ],
            key_messages=[
                "Enterprise-grade business intelligence for competitive advantage",
                "SLA guarantees protecting your revenue streams",
                "Custom metrics aligned with your specific KPIs",
                "ROI of 300%+ with executive reporting included"
            ],
            objection_handling={
                "Too expensive": "At $499/month, we protect enterprise revenue streams worth millions. What's the cost of not having this visibility?",
                "Need custom features": "We can build custom metrics and integrations. What specific capabilities would drive the most value?",
                "Long procurement process": "I understand. Can we start with a 90-day pilot to demonstrate value while procurement runs?",
                "Internal solution": "How long would it take to build this internally? What's the opportunity cost of waiting 6-12 months?"
            },
            success_criteria=[
                "Executive sponsor identified",
                "Technical requirements documented",
                "Pilot or proof of concept approved",
                "Procurement process initiated"
            ],
            average_deal_size=30000.0,
            sales_cycle_days=60,
            conversion_rates={
                "initial_to_discovery": 0.40,
                "discovery_to_proposal": 0.70,
                "proposal_to_pilot": 0.50,
                "pilot_to_close": 0.80
            },
            required_assets=["executive_summary", "technical_architecture", "security_compliance", "custom_proposal"]
        )

        # Competitive Displacement Playbook
        playbooks["competitive_displacement"] = SalesPlaybook(
            id="competitive_displacement",
            name="Competitive Tool Replacement",
            play_type=SalesPlayType.COMPETITIVE_DISPLACEMENT,
            target_segments=[CustomerSegment.SMB, CustomerSegment.MID_MARKET],
            target_industries=list(IndustryType),
            description="Playbook for displacing competitive monitoring tools with superior business intelligence",
            objectives=[
                "Identify gaps in current solution",
                "Demonstrate PsychSync competitive advantages",
                "Create migration plan",
                "Accelerate decision timeline"
            ],
            key_messages=[
                "Your current tool shows technical metrics, we show business impact",
                "Competitive intelligence: you vs industry leaders in real-time",
                "189x better ROI with automated insights vs manual dashboards",
                "Setup in 2 minutes vs months of configuration"
            ],
            objection_handling={
                "Happy with current tool": "Great! Are you happy with the business insights and ROI you're getting from it?",
                "Too disruptive to switch": "We can run in parallel during transition. Most customers see value immediately and switch within weeks",
                "Already paid for year": "We'll credit remaining months toward Growth tier and provide free onboarding",
                "Team knows current tool": "Our tool is designed for business users, not technical teams. Setup is 95% faster"
            },
            success_criteria=[
                "Current tool limitations identified",
                "PsychSync advantages demonstrated",
                "Migration timeline established",
                "Executive approval secured"
            ],
            average_deal_size=15000.0,
            sales_cycle_days=30,
            conversion_rates={
                "discovery_to_demo": 0.75,
                "demo_to_pilot": 0.60,
                "pilot_to_close": 0.70
            },
            required_assets=["competitive_comparison", "migration_guide", "roi_vs_competitor", "executive_case_study"]
        )

        return playbooks

    def _initialize_competitive_intelligence(self) -> Dict[str, CompetitiveIntelligence]:
        """Initialize competitive intelligence data"""
        intelligence = {}

        # New Relic Competition
        intelligence["new_relic"] = CompetitiveIntelligence(
            competitor="New Relic",
            strengths=[
                "Established brand in APM space",
                "Comprehensive technical monitoring",
                "Large ecosystem of integrations",
                "Strong enterprise features"
            ],
            weaknesses=[
                "Business intelligence focus is secondary",
                "Complex setup and configuration",
                "Expensive for business insights",
                "Requires technical expertise to extract value"
            ],
            positioning="New Relic is technical infrastructure monitoring. We're business intelligence that happens to use the same data.",
            pricing_comparison={
                "New Relic": "$500+/month for business insights",
                "PsychSync Monitor": "$99/month for superior business intelligence",
                "Setup Time": "New Relic: weeks, PsychSync: 2 minutes",
                "ROI": "New Relic: 50x, PsychSync: 189x"
            },
            win_themes=[
                "Business impact focus vs technical metrics",
                "Setup time advantage (2 minutes vs weeks)",
                "Industry-specific competitive intelligence",
                "Superior ROI with faster payback"
            ],
            loss_themes=[
                "Already invested in New Relic ecosystem",
                "Need deep technical monitoring capabilities",
                "Enterprise procurement preference for established vendors"
            ],
            displacement_tactics=[
                "Focus on business users vs technical teams",
                "Competitive intelligence as differentiator",
                "ROI comparison highlighting 3x better returns",
                "Setup complexity and time-to-value advantage"
            ]
        )

        # Datadog Competition
        intelligence["datadog"] = CompetitiveIntelligence(
            competitor="Datadog",
            strengths=[
                "Strong brand recognition",
                "Comprehensive monitoring coverage",
                "Good visualization capabilities",
                "Strong technical community"
            ],
            weaknesses=[
                "Overwhelming for business users",
                "Expensive pricing tiers",
                "Business insights require customization",
                "No industry benchmarking"
            ],
            positioning="Datadog shows what's happening. We show what it means for your business.",
            pricing_comparison={
                "Datadog": "$700+/month for business features",
                "PsychSync Monitor": "$99/month for complete business intelligence",
                "Complexity": "Datadog: high, PsychSync: low",
                "Value": "Datadog: technical, PsychSync: business"
            },
            win_themes=[
                "Simplicity and ease of use",
                "Business-focused insights out of the box",
                "Industry competitive intelligence",
                "Better ROI and faster setup"
            ],
            loss_themes=[
                "Need deep technical monitoring",
                "Already standardized on Datadog",
                "Require specific Datadog integrations"
            ],
            displacement_tactics=[
                "Focus on business stakeholder needs",
                "Competitive intelligence as unique value",
                "Cost comparison for business insights",
                "User experience and adoption advantages"
            ]
        )

        # Generic Business Intelligence Competition
        intelligence["generic_bi"] = CompetitiveIntelligence(
            competitor="Generic BI Tools (Tableau, Power BI)",
            strengths=[
                "Powerful visualization capabilities",
                "Flexible data modeling",
                "Strong enterprise adoption",
                "Custom dashboard capabilities"
            ],
            weaknesses=[
                "Requires data engineering setup",
                "No real-time PsychSync integration",
                "Generic, not industry-specific",
                "High implementation and maintenance costs"
            ],
            positioning="Generic BI tools require data engineering. We provide business intelligence instantly.",
            pricing_comparison={
                "Generic BI": "$10K+ implementation + $2K+/month",
                "PsychSync Monitor": "$99/month ready to use",
                "Time to Value": "Generic: months, PsychSync: minutes",
                "Domain Expertise": "Generic: none, PsychSync: built-in"
            },
            win_themes=[
                "Instant value vs implementation projects",
                "PsychSync-specific business intelligence",
                "Industry competitive intelligence",
                "No technical resources required"
            ],
            loss_themes=[
                "Need highly custom dashboards",
                "Already invested in BI platform",
                "Require data warehouse integration"
            ],
            displacement_tactics=[
                "Total cost of ownership comparison",
                "Time-to-value advantage",
                "Business user enablement",
                "Specialized vs generic capabilities"
            ]
        )

        return intelligence

    def _initialize_sales_assets(self) -> Dict[str, SalesAsset]:
        """Initialize sales collateral and assets"""
        assets = {}

        # ROI Calculator
        assets["roi_calculator"] = SalesAsset(
            id="roi_calculator",
            name="Business Intelligence ROI Calculator",
            asset_type="roi_calculator",
            description="Interactive calculator for demonstrating PsychSync Monitor ROI",
            target_audience="Prospects and customers evaluating investment",
            content="""
# PsychSync Monitor ROI Calculator

## Input Parameters
- **Company Size**: Team members and monthly assessments
- **Current Revenue**: Monthly recurring revenue
- **Industry**: For competitive benchmarking
- **Pain Points**: Current monitoring challenges

## Calculations
### Revenue Protection
- **Downtime Cost**: $2,500/hour (industry average)
- **Incident Prevention**: 80% reduction with proactive monitoring
- **Monthly Protection**: $125K average customer value

### Efficiency Gains
- **Manual Monitoring Time Saved**: 40 hours/month
- **Faster Decision Making**: 75% reduction in time-to-insight
- **Team Productivity Gain**: $15K monthly value

### Competitive Advantage
- **Performance Optimization**: 25% potential revenue increase
- **Customer Satisfaction**: 27.3 point NPS advantage
- **Market Positioning**: Real-time competitive intelligence

## Results Format
- **Monthly Value**: $X
- **Annual ROI**: X%
- **Payback Period**: X days
- **Confidence Score**: X%

## Industry Benchmarks
- **Technology**: 189x ROI, 1-day payback
- **Financial Services**: 156x ROI, 2-day payback
- **Healthcare**: 142x ROI, 3-day payback
- **Professional Services**: 178x ROI, 1-day payback
            """,
            usage_instructions="""
1. Gather basic company information (size, revenue, industry)
2. Identify 2-3 current monitoring pain points
3. Walk through calculator with prospect
4. Customize results based on their specific situation
5. Compare results to industry benchmarks
6. Discuss implementation timeline and value realization
            """,
            success_metrics=[
                "Prospect accepts ROI calculation",
                "ROI meets minimum threshold (100x+)",
                "Calculation influences purchase decision",
                "Customer achieves projected ROI within 6 months"
            ],
            last_updated=datetime.now()
        )

        # Executive One-Pager
        assets["executive_one_pager"] = SalesAsset(
            id="executive_one_pager",
            name="Executive Summary One-Pager",
            asset_type="one_pager",
            description="Concise executive summary for C-level stakeholders",
            target_audience="CEOs, CTOs, CROs, and other executives",
            content="""
# Transform Technical Data Into Business Intelligence

## The Problem
Technical monitoring tools show metrics, not business impact. Companies spend $100K+ on tools that don't answer the questions executives care about:
- How does performance affect revenue?
- How do we compare to competitors?
- Where are our biggest optimization opportunities?

## The Solution
PsychSync Monitor translates technical metrics into business intelligence that drives revenue growth.

## Key Benefits
- **$125K Monthly Revenue Protection**: Average customer value from proactive issue prevention
- **43% Performance Advantage**: Faster response time than industry average
- **189x ROI**: With 1-day average payback period
- **2-Minute Setup**: vs months for traditional BI implementations

## Business Impact
### Before PsychSync Monitor
- Reactive problem resolution
- Limited business visibility
- No competitive intelligence
- Manual reporting and analysis

### After PsychSync Monitor
- Proactive revenue protection
- Real-time business insights
- Competitive market positioning
- Automated executive dashboards

## Customer Success
- **SaaS Company**: 25% revenue increase from optimization insights
- **Enterprise**: $2M cost savings through efficiency gains
- **Startup**: 40% faster growth using competitive intelligence

## Pricing & ROI
- **Growth Tier**: $99/month
- **Enterprise Tier**: $499/month
- **Average ROI**: 189x
- **Payback Period**: 1-3 days

## Next Steps
1. 15-minute executive demo
2. Customized ROI analysis
3. 30-day pilot program
4. Full implementation
            """,
            usage_instructions="""
1. Use for initial executive outreach
2. Leave behind after executive meetings
3. Include in proposal packages
4. Share with economic buyers
5. Customize with prospect-specific data
            """,
            success_metrics=[
                "Executive meeting secured",
                "Request for detailed presentation",
                "Inclusion in evaluation process",
                "Executive sponsorship obtained"
            ],
            last_updated=datetime.now()
        )

        # Case Study Template
        assets["case_study_template"] = SalesAsset(
            id="case_study_template",
            name="Customer Success Story Template",
            asset_type="case_study",
            description="Template for creating compelling customer success stories",
            target_audience="Prospects in evaluation phase",
            content="""
# [Customer Name]: [Headline Result]

## Company Overview
- **Industry**: [Industry]
- **Size**: [Employees], [Revenue]
- **Challenge**: [Specific business challenge]

## The Challenge
[Brief description of the specific business problem or opportunity]

## The Solution
[How PsychSync Monitor addressed their specific needs]

## Implementation
- **Setup Time**: [Time to value]
- **Integration**: [How connected to existing systems]
- **User Adoption**: [How quickly team adopted]

## Results
### Quantitative Impact
- **Revenue Protection**: $X monthly
- **Efficiency Gains**: X hours saved monthly
- **Performance Improvement**: X% better than industry
- **ROI**: X with X-day payback

### Qualitative Impact
- **Decision Making**: Faster, data-driven decisions
- **Competitive Positioning**: Improved market position
- **Team Productivity**: More focused on value-added activities

## Customer Quote
"[Powerful testimonial about business impact]"

## Key Success Factors
- [Factor 1: Quick time-to-value]
- [Factor 2: Business-focused insights]
- [Factor 3: Competitive intelligence]
- [Factor 4: User-friendly adoption]

## Next Steps
- [Planned expansion or additional use cases]
- [Recommendations for similar companies]
            """,
            usage_instructions="""
1. Interview successful customers
2. Gather quantitative results and metrics
3. Obtain compelling quotes and testimonials
4. Customize template for each customer story
5. Use in proposals and presentations
6. Publish on website and marketing materials
            """,
            success_metrics=[
                "Influenced prospect decisions",
                "Used in successful proposals",
                "Shared by customers",
                "Improved conversion rates"
            ],
            last_updated=datetime.now()
        )

        # Demo Script
        assets["demo_script"] = SalesAsset(
            id="demo_script",
            name="Business Intelligence Demo Script",
            asset_type="demo_script",
            description="Comprehensive demo script focusing on business value",
            target_audience="Sales team conducting product demonstrations",
            content="""
# PsychSync Monitor Demo Script

## Pre-Demo Preparation (5 minutes)
- Research company and industry
- Identify likely pain points
- Prepare competitive intelligence data
- Set up demo environment with relevant data

## Introduction (5 minutes)
- Welcome and agenda
- Company understanding and challenges
- Value proposition overview
- Demo expectations

## Business Impact Discovery (10 minutes)
### Key Questions:
- "How do you currently track business impact of technical performance?"
- "What are your biggest concerns about downtime or performance issues?"
- "How do you compare to competitors in terms of user experience?"
- "What would it mean to your business to prevent just one major outage per year?"

### Pain Point Identification:
- Current monitoring gaps
- Business impact concerns
- Competitive pressure
- Resource constraints

## Live Demo (20 minutes)

### Section 1: Immediate Business Value (5 minutes)
- **Dashboard Overview**: Show business-focused metrics
- **Revenue Impact**: Real-time revenue protection calculations
- **Key Message**: "This is what's protecting your revenue right now"

### Section 2: Competitive Intelligence (5 minutes)
- **Industry Benchmarking**: How they compare to competitors
- **Market Positioning**: Real-time competitive analysis
- **Key Message**: "This is how you're performing against industry leaders"

### Section 3: User Journey Analytics (5 minutes)
- **Conversion Funnel**: Where revenue opportunities are lost
- **Optimization Opportunities**: Specific areas for improvement
- **Key Message**: "This is where you can increase revenue by 25%"

### Section 4: Executive Reporting (5 minutes)
- **Executive Dashboard**: C-level focused insights
- **ROI Tracking**: Measurable business impact
- **Key Message**: "This is how you report value to executives"

## Value Proposition Discussion (10 minutes)
- **ROI Calculation**: Using their specific numbers
- **Competitive Advantages**: Unique value vs alternatives
- **Implementation Timeline**: Quick path to value
- **Success Stories**: Relevant customer examples

## Objection Handling (5 minutes)
- Address common concerns proactively
- Share competitive intelligence
- Discuss implementation and support
- Reference relevant case studies

## Next Steps (5 minutes)
- **Immediate**: Schedule technical deep dive
- **Short-term**: Start 30-day pilot
- **Long-term**: Full implementation plan
- **Follow-up**: Clear action items and timeline

## Closing Questions:
- "What aspect of this would be most valuable to your business?"
- "What would prevent you from moving forward with this?"
- "Who else needs to be involved in this decision?"
- "What timeline makes sense for your organization?"
            """,
            usage_instructions="""
1. Customize script for each prospect
2. Focus on business value, not technical features
3. Use prospect-specific data and examples
4. Adapt based on real-time feedback
5. Always connect features to business outcomes
6. Prepare for common objections and questions
            """,
            success_metrics=[
                "Demo completion rate",
                "Prospect engagement during demo",
                "Request for next steps",
                "Progression to pilot/proposal stage"
            ],
            last_updated=datetime.now()
        )

        return assets

    def _initialize_conversation_guides(self) -> Dict[str, SalesConversationGuide]:
        """Initialize sales conversation guides"""
        guides = {}

        # Initial Discovery Guide
        guides["initial_discovery"] = SalesConversationGuide(
            id="initial_discovery",
            scenario="First conversation with new prospect",
            conversation_stages=[
                {
                    "stage": "Opening",
                    "duration": "2 minutes",
                    "objectives": ["Build rapport", "Understand their context", "Set agenda"],
                    "key_questions": [
                        "What prompted your interest in business intelligence?",
                        "How familiar are you with PsychSync?",
                        "What are your biggest business challenges right now?"
                    ]
                },
                {
                    "stage": "Business Discovery",
                    "duration": "15 minutes",
                    "objectives": ["Identify pain points", "Understand current solutions", "Quantify impact"],
                    "key_questions": [
                        "How do you currently track business performance?",
                        "What metrics matter most to your executives?",
                        "How do technical issues affect your revenue?",
                        "What's the cost of poor performance or downtime?",
                        "How do you compare to competitors?"
                    ]
                },
                {
                    "stage": "Solution Alignment",
                    "duration": "10 minutes",
                    "objectives": ["Connect solutions to pain", "Demonstrate understanding", "Create urgency"],
                    "key_questions": [
                        "If you could prevent just one major outage per year, what would that be worth?",
                        "How much faster would you grow with better competitive intelligence?",
                        "What would it mean to your team to have insights in minutes vs weeks?"
                    ]
                },
                {
                    "stage": "Next Steps",
                    "duration": "3 minutes",
                    "objectives": ["Define clear actions", "Secure stakeholder involvement", "Set timeline"],
                    "key_questions": [
                        "Who else needs to be involved in this decision?",
                        "What timeline makes sense for evaluation?",
                        "What would you need to see to move forward?"
                    ]
                }
            ],
            key_questions=[
                "What's the business impact of poor performance?",
                "How do you currently measure and optimize user experience?",
                "What competitive insights would be most valuable?",
                "What's your process for making data-driven decisions?"
            ],
            value_proposition="Transform technical monitoring into business intelligence that drives revenue growth and competitive advantage",
            roi_framework={
                "revenue_protection": "Calculate based on potential downtime costs",
                "efficiency_gains": "Quantify time savings and productivity improvements",
                "competitive_advantage": "Value from market positioning and customer experience",
                "growth_acceleration": "Impact of optimized user journey and conversion"
            },
            next_steps=[
                "Schedule personalized demo",
                "Provide customized ROI analysis",
                "Set up 30-day pilot program",
                "Engage technical stakeholders"
            ],
            success_indicators=[
                "Prospect identifies specific business value",
                "Clear understanding of current challenges",
                "Agreement to next steps",
                "Stakeholder identification complete"
            ]
        )

        # Upgrade Conversation Guide
        guides["upgrade_conversation"] = SalesConversationGuide(
            id="upgrade_conversation",
            scenario="Free tier customer upgrade conversation",
            conversation_stages=[
                {
                    "stage": "Value Recognition",
                    "duration": "5 minutes",
                    "objectives": ["Acknowledge current success", "Identify usage patterns", "Recognize value"],
                    "key_questions": [
                        "How has PsychSync Monitor helped your business so far?",
                        "What insights have been most valuable?",
                        "How often are you checking your dashboard?"
                    ]
                },
                {
                    "stage": "Opportunity Identification",
                    "duration": "10 minutes",
                    "objectives": ["Show growth trajectory", "Identify missed opportunities", "Create urgency"],
                    "key_questions": [
                        "Did you know you're at X% of free tier limits?",
                        "What would it mean to get 3x more insights?",
                        "How much is it costing you to miss these optimization opportunities?"
                    ]
                },
                {
                    "stage": "ROI Presentation",
                    "duration": "5 minutes",
                    "objectives": ["Present specific ROI", "Show immediate value", "Remove barriers"],
                    "key_questions": [
                        "If you could protect $X more revenue monthly for just $99, would that make sense?",
                        "What would prevent you from upgrading today?",
                        "How quickly would you like to see these benefits?"
                    ]
                },
                {
                    "stage": "Processing",
                    "duration": "2 minutes",
                    "objectives": ["Complete upgrade", "Confirm value", "Set expectations"],
                    "key_questions": [
                        "Ready to unlock these additional benefits?",
                        "Which payment method would you prefer?",
                        "Would you like help with any new features?"
                    ]
                }
            ],
            key_questions=[
                "How valuable are the insights you're currently receiving?",
                "What additional insights would be most valuable?",
                "What's the cost of missing advanced analytics?",
                "How quickly would you like to see ROI?"
            ],
            value_proposition="Unlock 3x more business intelligence and revenue protection for less than the cost of one lost opportunity",
            roi_framework={
                "current_value": "Value they're receiving from free tier",
                "missed_opportunity": "Additional value they could capture",
                "upgrade_cost": "$99/month investment",
                "payback_period": "Typically 1-3 days"
            },
            next_steps=[
                "Process upgrade immediately",
                "Activate premium features",
                "Provide onboarding for new capabilities",
                "Schedule success check-in"
            ],
            success_indicators=[
                "Customer recognizes upgrade value",
                "ROI calculation makes sense",
                "Upgrade completed in conversation",
                "Immediate activation of premium features"
            ]
        )

        return guides

    def get_playbook(self, playbook_id: str) -> Optional[SalesPlaybook]:
        """Get specific sales playbook"""
        return self.playbooks.get(playbook_id)

    def get_competitive_intelligence(self, competitor: str) -> Optional[CompetitiveIntelligence]:
        """Get competitive intelligence for specific competitor"""
        return self.competitive_intelligence.get(competitor)

    def get_sales_asset(self, asset_id: str) -> Optional[SalesAsset]:
        """Get specific sales asset"""
        return self.sales_assets.get(asset_id)

    def get_conversation_guide(self, guide_id: str) -> Optional[SalesConversationGuide]:
        """Get specific conversation guide"""
        return self.conversation_guides.get(guide_id)

    def recommend_playbook(self, customer_data: Dict[str, Any]) -> List[str]:
        """Recommend relevant playbooks based on customer data"""
        recommendations = []

        segment = self._determine_customer_segment(customer_data)
        industry = customer_data.get("industry", "").lower()
        deal_type = customer_data.get("deal_type", "")
        current_tier = customer_data.get("current_tier", "")

        # Outbound prospecting for new leads
        if deal_type in ["new_business", "prospect"]:
            if segment in [CustomerSegment.STARTUP, CustomerSegment.SMB]:
                recommendations.append("outbound_prospecting")

        # Upgrade conversations for free tier customers
        if current_tier == "free" and deal_type != "new_business":
            recommendations.append("upgrade_conversation")

        # Enterprise deals
        if segment in [CustomerSegment.MID_MARKET, CustomerSegment.ENTERPRISE]:
            recommendations.append("enterprise_deal")

        # Competitive displacement
        if "competitor" in customer_data or customer_data.get("has_monitoring_tools"):
            recommendations.append("competitive_displacement")

        return recommendations

    def _determine_customer_segment(self, customer_data: Dict[str, Any]) -> CustomerSegment:
        """Determine customer segment based on company data"""
        employees = customer_data.get("employees", 0)
        revenue = customer_data.get("annual_revenue", 0)

        if employees <= 50 or revenue < 1000000:
            return CustomerSegment.STARTUP
        elif employees <= 500 or revenue < 50000000:
            return CustomerSegment.SMB
        elif employees <= 2000 or revenue < 500000000:
            return CustomerSegment.MID_MARKET
        else:
            return CustomerSegment.ENTERPRISE

    def generate_proposal_template(self, customer_data: Dict[str, Any],
                                 playbook_id: str) -> Dict[str, Any]:
        """Generate customized proposal template based on playbook and customer data"""
        playbook = self.get_playbook(playbook_id)
        if not playbook:
            return {}

        customer_name = customer_data.get("company_name", "Prospect")
        segment = self._determine_customer_segment(customer_data)

        proposal = {
            "customer_name": customer_name,
            "segment": segment.value,
            "playbook": playbook.name,
            "key_challenges": self._identify_key_challenges(customer_data),
            "proposed_solution": self._customize_solution(customer_data, playbook),
            "roi_analysis": self._generate_roi_analysis(customer_data),
            "implementation_timeline": self._create_implementation_timeline(playbook),
            "investment": self._calculate_investment(customer_data, playbook),
            "success_metrics": playbook.success_criteria
        }

        return proposal

    def _identify_key_challenges(self, customer_data: Dict[str, Any]) -> List[str]:
        """Identify key challenges based on customer data"""
        challenges = []

        if customer_data.get("has_performance_issues"):
            challenges.append("Performance issues affecting customer experience and revenue")

        if customer_data.get("has_downtime"):
            challenges.append("Unexpected downtime causing revenue loss and customer churn")

        if not customer_data.get("has_business_intelligence"):
            challenges.append("Limited visibility into business impact of technical performance")

        if customer_data.get("competitive_pressure"):
            challenges.append("Competitive pressure requires better market positioning")

        if customer_data.get("manual_reporting"):
            challenges.append("Manual reporting and analysis consuming valuable team time")

        return challenges

    def _customize_solution(self, customer_data: Dict[str, Any],
                          playbook: SalesPlaybook) -> Dict[str, Any]:
        """Customize solution based on customer needs and playbook"""
        return {
            "tier": "Growth" if customer_data.get("employees", 0) < 500 else "Enterprise",
            "key_features": self._prioritize_features(customer_data),
            "integration_requirements": customer_data.get("integration_needs", []),
            "customization": self._identify_customization_needs(customer_data),
            "support_level": "Priority" if customer_data.get("employees", 0) > 100 else "Standard"
        }

    def _prioritize_features(self, customer_data: Dict[str, Any]) -> List[str]:
        """Prioritize features based on customer needs"""
        priorities = []

        if customer_data.get("revenue_focus"):
            priorities.extend(["Revenue Impact Analysis", "ROI Tracking", "Executive Reporting"])

        if customer_data.get("competitive_focus"):
            priorities.extend(["Competitive Benchmarking", "Market Intelligence", "Industry Comparisons"])

        if customer_data.get("efficiency_focus"):
            priorities.extend(["Automated Insights", "Alert Management", "Performance Optimization"])

        return priorities

    def _identify_customization_needs(self, customer_data: Dict[str, Any]) -> List[str]:
        """Identify customization requirements"""
        customizations = []

        if customer_data.get("industry_specific"):
            customizations.append("Industry-specific metrics and benchmarks")

        if customer_data.get("custom_kpis"):
            customizations.append("Custom KPI tracking and reporting")

        if customer_data.get("executive_reporting"):
            customizations.append("Executive dashboard customization")

        return customizations

    def _generate_roi_analysis(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ROI analysis for customer"""
        employees = customer_data.get("employees", 50)
        revenue = customer_data.get("annual_revenue", 5000000)

        # Simplified ROI calculation
        monthly_revenue_protection = min(25000, revenue * 0.002)
        annual_efficiency_savings = employees * 1000  # $1K per employee
        total_annual_value = monthly_revenue_protection * 12 + annual_efficiency_savings

        return {
            "monthly_revenue_protection": monthly_revenue_protection,
            "annual_efficiency_savings": annual_efficiency_savings,
            "total_annual_value": total_annual_value,
            "investment": 1188,  # Growth tier annual
            "roi": total_annual_value / 1188 if total_annual_value > 0 else 0,
            "payback_period_days": 30
        }

    def _create_implementation_timeline(self, playbook: SalesPlaybook) -> Dict[str, str]:
        """Create implementation timeline based on playbook"""
        return {
            "day_1": "Account setup and initial integration",
            "day_2": "Dashboard configuration and customization",
            "day_3": "Team training and onboarding",
            "day_7": "First insights review and optimization",
            "day_30": "Success metrics review and expansion planning"
        }

    def _calculate_investment(self, customer_data: Dict[str, Any],
                            playbook: SalesPlaybook) -> Dict[str, Any]:
        """Calculate investment based on customer needs and playbook"""
        tier = "Enterprise" if customer_data.get("employees", 0) > 500 else "Growth"

        if tier == "Enterprise":
            return {
                "setup_fee": 5000,
                "monthly_fee": 499,
                "annual_total": 5988,
                "implementation_support": "Included"
            }
        else:
            return {
                "setup_fee": 0,
                "monthly_fee": 99,
                "annual_total": 1188,
                "implementation_support": "Standard"
            }
