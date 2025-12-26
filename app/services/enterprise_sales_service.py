"""
Enterprise Sales and Customer Success Service
B2B infrastructure for enterprise account management and customer success
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.services.billing import (
    RevenueGenerationService,
    SubscriptionTier,
    BillingCycle
)

logger = logging.getLogger(__name__)

class AccountTier(Enum):
    ENTERPRISE = "enterprise"
    CLINICAL = "clinical"
    PROFESSIONAL = "professional"
    STARTUP = "startup"

class CustomerHealthStatus(Enum):
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    CHURNED = "churned"
    NEW = "new"

class SLATier(Enum):
    BASIC = "basic"          # 99.5% uptime, 48hr response
    PROFESSIONAL = "professional"  # 99.8% uptime, 24hr response
    ENTERPRISE = "enterprise"      # 99.95% uptime, 4hr response
    CLINICAL = "clinical"          # 99.99% uptime, 1hr response

@dataclass
class SLAMetrics:
    uptime_percentage: float
    response_time_hours: int
    resolution_time_hours: int
    availability_guarantee: float
    compensation_percentage: float

@dataclass
class CustomerHealthMetrics:
    account_id: str
    organization_id: int
    health_score: float  # 0-100
    status: CustomerHealthStatus
    usage_frequency: float
    feature_adoption: float
    support_tickets: int
    nps_score: Optional[int]
    renewal_risk: str
    last_login: datetime
    mrr_value: float
    team_engagement: float
    key_risks: List[str]
    opportunities: List[str]

@dataclass
class EnterpriseAccount:
    organization_id: int
    account_name: str
    tier: AccountTier
    customer_success_manager: str
    contract_value: float
    contract_start: datetime
    contract_end: datetime
    users_licensed: int
    users_active: int
    sla_tier: SLATier
    health_metrics: CustomerHealthMetrics
    custom_integrations: List[str]
    training_completed: List[str]
    upcoming_renewal: bool
    expansion_opportunities: List[str]

class EnterpriseSalesService:
    """
    Enterprise sales and customer success management
    """

    def __init__(self):
        self.sla_metrics = self._initialize_sla_metrics()
        self.health_thresholds = self._initialize_health_thresholds()
        self.success_plays = self._initialize_success_plays()
        self.enterprise_features = self._initialize_enterprise_features()

    def _initialize_sla_metrics(self) -> Dict[SLATier, SLAMetrics]:
        """Initialize SLA metrics by tier"""
        return {
            SLATier.BASIC: SLAMetrics(
                uptime_percentage=99.5,
                response_time_hours=48,
                resolution_time_hours=72,
                availability_guarantee=99.5,
                compensation_percentage=10
            ),
            SLATier.PROFESSIONAL: SLAMetrics(
                uptime_percentage=99.8,
                response_time_hours=24,
                resolution_time_hours=48,
                availability_guarantee=99.8,
                compensation_percentage=20
            ),
            SLATier.ENTERPRISE: SLAMetrics(
                uptime_percentage=99.95,
                response_time_hours=4,
                resolution_time_hours=8,
                availability_guarantee=99.95,
                compensation_percentage=50
            ),
            SLATier.CLINICAL: SLAMetrics(
                uptime_percentage=99.99,
                response_time_hours=1,
                resolution_time_hours=4,
                availability_guarantee=99.99,
                compensation_percentage=100
            )
        }

    def _initialize_health_thresholds(self) -> Dict[str, Any]:
        """Initialize customer health scoring thresholds"""
        return {
            "healthy_score_min": 80,
            "at_risk_score_min": 60,
            "critical_score_min": 40,
            "usage_frequency_weight": 0.25,
            "feature_adoption_weight": 0.20,
            "support_tickets_weight": 0.15,
            "nps_weight": 0.20,
            "team_engagement_weight": 0.20
        }

    def _initialize_success_plays(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize customer success playbooks"""
        return {
            "new_onboarding": [
                {
                    "action": "Welcome call with CSM",
                    "timeline": "Day 1-3",
                    "owner": "Customer Success Manager",
                    "template": "enterprise_welcome_call"
                },
                {
                    "action": "Technical setup consultation",
                    "timeline": "Day 3-7",
                    "owner": "Solutions Engineer",
                    "template": "technical_setup"
                },
                {
                    "action": "Admin training session",
                    "timeline": "Week 2",
                    "owner": "Training Specialist",
                    "template": "admin_training"
                },
                {
                    "action": "30-day check-in",
                    "timeline": "Day 30",
                    "owner": "Customer Success Manager",
                    "template": "30_day_checkin"
                }
            ],
            "at_risk_intervention": [
                {
                    "action": "Account review meeting",
                    "timeline": "Immediate",
                    "owner": "Customer Success Manager",
                    "template": "account_review"
                },
                {
                    "action": "Usage analysis and optimization",
                    "timeline": "Week 1",
                    "owner": "Solutions Engineer",
                    "template": "usage_optimization"
                },
                {
                    "action": "Additional training",
                    "timeline": "Week 2",
                    "owner": "Training Specialist",
                    "template": "additional_training"
                },
                {
                    "action": "Executive business review",
                    "timeline": "Week 3",
                    "owner": "Account Executive",
                    "template": "executive_review"
                }
            ],
            "renewal_campaign": [
                {
                    "action": "90-day renewal notice",
                    "timeline": "Day 90 before renewal",
                    "owner": "Customer Success Manager",
                    "template": "renewal_notice_90"
                },
                {
                    "action": "Value demonstration",
                    "timeline": "Day 60 before renewal",
                    "owner": "Customer Success Manager",
                    "template": "value_demonstration"
                },
                {
                    "action": "Expansion opportunity discussion",
                    "timeline": "Day 30 before renewal",
                    "owner": "Account Executive",
                    "template": "expansion_discussion"
                },
                {
                    "action": "Final renewal confirmation",
                    "timeline": "Day 7 before renewal",
                    "owner": "Customer Success Manager",
                    "template": "renewal_confirmation"
                }
            ],
            "expansion_opportunity": [
                {
                    "action": "Usage pattern analysis",
                    "timeline": "Monthly",
                    "owner": "Customer Success Manager",
                    "template": "usage_analysis"
                },
                {
                    "action": "Feature upgrade recommendation",
                    "timeline": "Quarterly",
                    "owner": "Solutions Engineer",
                    "template": "feature_upgrade"
                },
                {
                    "action": "Business value assessment",
                    "timeline": "Semi-annually",
                    "owner": "Account Executive",
                    "template": "business_value"
                }
            ]
        }

    def _initialize_enterprise_features(self) -> Dict[AccountTier, List[str]]:
        """Initialize enterprise features by account tier"""
        return {
            AccountTier.STARTUP: [
                "Standard support",
                "Basic analytics",
                "Email support",
                "Standard security"
            ],
            AccountTier.PROFESSIONAL: [
                "Priority support",
                "Advanced analytics",
                "Phone support",
                "Advanced security",
                "API access",
                "Custom branding"
            ],
            AccountTier.ENTERPRISE: [
                "Dedicated Customer Success Manager",
                "Enterprise analytics dashboard",
                "24/7 phone support",
                "Enterprise security (SSO, SAML)",
                "Custom API integrations",
                "White-label solution",
                "Custom training programs",
                "Account-based marketing support"
            ],
            AccountTier.CLINICAL: [
                "Dedicated Clinical Account Manager",
                "HIPAA compliance support",
                "Clinical implementation specialist",
                "Emergency support hotline",
                "Clinical data export tools",
                "Research collaboration tools",
                "IRB support documentation",
                "Clinical validation studies",
                "Custom clinical workflows"
            ]
        }

    async def create_enterprise_account(
        self,
        organization: Organization,
        tier: AccountTier,
        contract_value: float,
        contract_term_months: int = 12,
        users_licensed: int = 100,
        customer_success_manager: str = "Unassigned",
        custom_requirements: List[str] = None
    ) -> EnterpriseAccount:
        """Create new enterprise account"""
        try:
            # Determine SLA tier based on account tier
            sla_tier = self._map_tier_to_sla(tier)

            # Initialize health metrics for new account
            health_metrics = CustomerHealthMetrics(
                account_id=f"account_{organization.id}",
                organization_id=organization.id,
                health_score=75.0,  # Start new accounts at 75
                status=CustomerHealthStatus.NEW,
                usage_frequency=0.0,
                feature_adoption=0.0,
                support_tickets=0,
                nps_score=None,
                renewal_risk="low",
                last_login=datetime.utcnow(),
                mrr_value=contract_value / contract_term_months,
                team_engagement=0.0,
                key_risks=["New account - limited usage data"],
                opportunities=["Full platform adoption", "Team training"]
            )

            # Create enterprise account
            account = EnterpriseAccount(
                organization_id=organization.id,
                account_name=organization.name,
                tier=tier,
                customer_success_manager=customer_success_manager,
                contract_value=contract_value,
                contract_start=datetime.utcnow(),
                contract_end=datetime.utcnow() + timedelta(days=contract_term_months * 30),
                users_licensed=users_licensed,
                users_active=0,
                sla_tier=sla_tier,
                health_metrics=health_metrics,
                custom_integrations=custom_requirements or [],
                training_completed=[],
                upcoming_renewal=False,
                expansion_opportunities=[]
            )

            # Schedule onboarding success plays
            await self._schedule_success_plays(account, "new_onboarding")

            logger.info(f"Created enterprise account for {organization.name} with tier {tier.value}")
            return account

        except Exception as e:
            logger.error(f"Failed to create enterprise account: {str(e)}")
            raise

    async def calculate_customer_health(
        self,
        organization_id: int,
        db: Session
    ) -> CustomerHealthMetrics:
        """Calculate comprehensive customer health score"""
        try:
            # Get organization data
            organization = db.query(Organization).filter(
                Organization.id == organization_id
            ).first()

            if not organization:
                raise ValueError(f"Organization {organization_id} not found")

            # Get usage metrics
            usage_metrics = await self._calculate_usage_metrics(organization_id, db)
            adoption_metrics = await self._calculate_adoption_metrics(organization_id, db)
            support_metrics = await self._calculate_support_metrics(organization_id, db)

            # Calculate component scores
            usage_score = min(100, usage_metrics["usage_frequency"] * 100)
            adoption_score = min(100, adoption_metrics["feature_adoption_percentage"] * 100)
            support_score = max(0, 100 - (support_metrics["open_tickets"] * 10))  # Penalty for tickets
            nps_score = support_metrics.get("nps_score", 70)  # Default NPS if not available
            engagement_score = min(100, usage_metrics["team_engagement"] * 100)

            # Weighted health score calculation
            weights = self.health_thresholds
            health_score = (
                usage_score * weights["usage_frequency_weight"] +
                adoption_score * weights["feature_adoption_weight"] +
                support_score * weights["support_tickets_weight"] +
                nps_score * weights["nps_weight"] +
                engagement_score * weights["team_engagement_weight"]
            )

            # Determine health status
            if health_score >= weights["healthy_score_min"]:
                status = CustomerHealthStatus.HEALTHY
                renewal_risk = "low"
            elif health_score >= weights["at_risk_score_min"]:
                status = CustomerHealthStatus.AT_RISK
                renewal_risk = "medium"
            elif health_score >= weights["critical_score_min"]:
                status = CustomerHealthStatus.CRITICAL
                renewal_risk = "high"
            else:
                status = CustomerHealthStatus.CRITICAL
                renewal_risk = "critical"

            # Identify risks and opportunities
            key_risks = self._identify_health_risks(usage_metrics, adoption_metrics, support_metrics)
            opportunities = self._identify_growth_opportunities(usage_metrics, adoption_metrics)

            # Create health metrics
            health_metrics = CustomerHealthMetrics(
                account_id=f"account_{organization_id}",
                organization_id=organization_id,
                health_score=round(health_score, 1),
                status=status,
                usage_frequency=usage_metrics["usage_frequency"],
                feature_adoption=adoption_metrics["feature_adoption_percentage"],
                support_tickets=support_metrics["open_tickets"],
                nps_score=nps_score,
                renewal_risk=renewal_risk,
                last_login=usage_metrics["last_login"],
                mrr_value=usage_metrics["mrr_value"],
                team_engagement=usage_metrics["team_engagement"],
                key_risks=key_risks,
                opportunities=opportunities
            )

            return health_metrics

        except Exception as e:
            logger.error(f"Failed to calculate customer health for org {organization_id}: {str(e)}")
            raise

    async def generate_expansion_opportunities(
        self,
        organization_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Identify expansion and upsell opportunities"""
        try:
            organization = db.query(Organization).filter(
                Organization.id == organization_id
            ).first()

            if not organization:
                raise ValueError(f"Organization {organization_id} not found")

            opportunities = []

            # Usage-based opportunities
            usage_metrics = await self._calculate_usage_metrics(organization_id, db)

            # License expansion opportunity
            if usage_metrics["active_users"] > usage_metrics["licensed_users"] * 0.8:
                opportunities.append({
                    "type": "license_expansion",
                    "description": "Approaching user limit - consider additional licenses",
                    "potential_value": (usage_metrics["active_users"] - usage_metrics["licensed_users"]) * 50,
                    "priority": "high",
                    "confidence": 0.9
                })

            # Feature upgrade opportunities
            adoption_metrics = await self._calculate_adoption_metrics(organization_id, db)

            # Advanced analytics upgrade
            if adoption_metrics["analytics_usage"] > 70 and organization.subscription_tier != "enterprise":
                opportunities.append({
                    "type": "tier_upgrade",
                    "description": "Heavy analytics usage - upgrade to Enterprise for advanced features",
                    "potential_value": 400,  # Monthly incremental value
                    "priority": "medium",
                    "confidence": 0.7
                })

            # Clinical module opportunity
            if "healthcare" in organization.name.lower() or "clinic" in organization.name.lower():
                opportunities.append({
                    "type": "clinical_module",
                    "description": "Healthcare organization - add clinical assessment modules",
                    "potential_value": 400,
                    "priority": "high",
                    "confidence": 0.8
                })

            # Custom integration opportunity
            tech_stack = await self._analyze_tech_stack(organization_id)
            if tech_stack.get("has_sso", False) and organization.subscription_tier != "enterprise":
                opportunities.append({
                    "type": "enterprise_integration",
                    "description": "SSO infrastructure detected - Enterprise tier with SAML integration",
                    "potential_value": 400,
                    "priority": "medium",
                    "confidence": 0.8
                })

            # Team training opportunity
            if adoption_metrics["feature_adoption_percentage"] < 50:
                opportunities.append({
                    "type": "training_package",
                    "description": "Low feature adoption - comprehensive team training recommended",
                    "potential_value": 200,
                    "priority": "high",
                    "confidence": 0.9
                })

            return sorted(opportunities, key=lambda x: x["confidence"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to generate expansion opportunities for org {organization_id}: {str(e)}")
            raise

    async def monitor_sla_compliance(
        self,
        sla_tier: SLATier,
        date_range_start: datetime,
        date_range_end: datetime
    ) -> Dict[str, Any]:
        """Monitor SLA compliance and calculate potential credits"""
        try:
            sla_metrics = self.sla_metrics[sla_tier]

            # Calculate actual uptime (this would integrate with monitoring systems)
            actual_uptime = await self._calculate_actual_uptime(date_range_start, date_range_end)

            # Calculate support response times (this would integrate with support systems)
            support_metrics = await self._calculate_support_metrics(date_range_start, date_range_end)

            # Determine SLA breaches
            uptime_breach = max(0, sla_metrics.uptime_percentage - actual_uptime)
            response_time_breaches = support_metrics.get("response_time_breaches", 0)

            # Calculate compensation credits
            total_compensation = 0
            breaches = []

            if uptime_breach > 0:
                uptime_credit = (uptime_breach / 100) * sla_metrics.compensation_percentage
                total_compensation += uptime_credit
                breaches.append({
                    "type": "uptime",
                    "sla_requirement": f"{sla_metrics.uptime_percentage}%",
                    "actual": f"{actual_uptime}%",
                    "breach_percentage": uptime_breach,
                    "credit_percentage": uptime_credit
                })

            if response_time_breaches > 0:
                response_credit = response_time_breaches * 0.1  # 10% credit per breach
                total_compensation += response_credit
                breaches.append({
                    "type": "response_time",
                    "sla_requirement": f"{sla_metrics.response_time_hours}h",
                    "breaches": response_time_breaches,
                    "credit_percentage": response_credit
                })

            return {
                "sla_tier": sla_tier.value,
                "monitoring_period": {
                    "start": date_range_start.isoformat(),
                    "end": date_range_end.isoformat()
                },
                "uptime": {
                    "required": sla_metrics.uptime_percentage,
                    "actual": actual_uptime,
                    "breach": max(0, sla_metrics.uptime_percentage - actual_uptime)
                },
                "support_performance": support_metrics,
                "breaches": breaches,
                "total_compensation_percentage": round(total_compensation, 2),
                "sla_status": "compliant" if total_compensation == 0 else "breached"
            }

        except Exception as e:
            logger.error(f"Failed to monitor SLA compliance: {str(e)}")
            raise

    async def schedule_qbr(
        self,
        organization_id: int,
        qbr_type: str = "quarterly",
        attendees: List[str] = None
    ) -> Dict[str, Any]:
        """Schedule Quarterly Business Review"""
        try:
            # Get account information
            health_metrics = await self.calculate_customer_health(organization_id, db=None)
            opportunities = await self.generate_expansion_opportunities(organization_id, db=None)

            # Prepare QBR content
            qbr_content = {
                "account_health": health_metrics,
                "usage_highlights": await self._get_usage_highlights(organization_id),
                "value_realization": await self._calculate_value_realization(organization_id),
                "expansion_opportunities": opportunities,
                "success_stories": await self._get_success_stories(organization_id),
                "recommendations": await self._generate_recommendations(organization_id)
            }

            # Schedule QBR meeting (this would integrate with calendaring)
            qbr_scheduled = {
                "organization_id": organization_id,
                "qbr_type": qbr_type,
                "scheduled_date": datetime.utcnow() + timedelta(weeks=2),  # Schedule 2 weeks out
                "duration_minutes": 60,
                "attendees": attendees or ["Customer Success Manager", "Account Executive"],
                "meeting_link": f"https://zoom.us/meeting/qbr_{organization_id}_{int(datetime.utcnow().timestamp())}",
                "preparation_required": True,
                "content_package": qbr_content
            }

            logger.info(f"Scheduled {qbr_type} QBR for organization {organization_id}")
            return qbr_scheduled

        except Exception as e:
            logger.error(f"Failed to schedule QBR for organization {organization_id}: {str(e)}")
            raise

    async def _schedule_success_plays(self, account: EnterpriseAccount, play_type: str):
        """Schedule customer success plays based on account status"""
        try:
            plays = self.success_plays.get(play_type, [])

            for play in plays:
                # Schedule play execution (this would integrate with task systems)
                scheduled_task = {
                    "account_id": account.organization_id,
                    "play_type": play_type,
                    "action": play["action"],
                    "timeline": play["timeline"],
                    "owner": play["owner"],
                    "template": play["template"],
                    "scheduled_date": self._calculate_schedule_date(account, play["timeline"]),
                    "status": "scheduled"
                }

                logger.info(f"Scheduled success play: {play['action']} for account {account.account_name}")

        except Exception as e:
            logger.error(f"Failed to schedule success plays: {str(e)}")

    def _map_tier_to_sla(self, tier: AccountTier) -> SLATier:
        """Map account tier to SLA tier"""
        mapping = {
            AccountTier.STARTUP: SLATier.BASIC,
            AccountTier.PROFESSIONAL: SLATier.PROFESSIONAL,
            AccountTier.ENTERPRISE: SLATier.ENTERPRISE,
            AccountTier.CLINICAL: SLATier.CLINICAL
        }
        return mapping.get(tier, SLATier.BASIC)

    async def _calculate_usage_metrics(self, organization_id: int, db: Session) -> Dict[str, Any]:
        """Calculate detailed usage metrics"""
        # This would integrate with analytics systems
        # Mock implementation for demonstration
        return {
            "usage_frequency": 0.75,  # 75% of expected usage
            "active_users": 45,
            "licensed_users": 50,
            "last_login": datetime.utcnow() - timedelta(days=3),
            "mrr_value": 500.0,
            "team_engagement": 0.68
        }

    async def _calculate_adoption_metrics(self, organization_id: int, db: Session) -> Dict[str, Any]:
        """Calculate feature adoption metrics"""
        # This would integrate with feature tracking systems
        return {
            "feature_adoption_percentage": 0.65,  # 65% of features used
            "analytics_usage": 0.80,
            "assessment_usage": 0.90,
            "team_features_usage": 0.45
        }

    async def _calculate_support_metrics(self, organization_id: int, db: Session) -> Dict[str, Any]:
        """Calculate support ticket metrics"""
        # This would integrate with support systems (Zendesk, etc.)
        return {
            "open_tickets": 2,
            "closed_tickets": 15,
            "average_resolution_time": 24.5,
            "nps_score": 75
        }

    def _identify_health_risks(
        self,
        usage_metrics: Dict[str, Any],
        adoption_metrics: Dict[str, Any],
        support_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify potential health risks"""
        risks = []

        if usage_metrics["usage_frequency"] < 0.5:
            risks.append("Low usage frequency")

        if adoption_metrics["feature_adoption_percentage"] < 0.4:
            risks.append("Poor feature adoption")

        if support_metrics["open_tickets"] > 5:
            risks.append("High number of support tickets")

        if usage_metrics["team_engagement"] < 0.5:
            risks.append("Low team engagement")

        return risks

    def _identify_growth_opportunities(
        self,
        usage_metrics: Dict[str, Any],
        adoption_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify growth opportunities"""
        opportunities = []

        if usage_metrics["active_users"] / usage_metrics["licensed_users"] > 0.8:
            opportunities.append("License expansion opportunity")

        if adoption_metrics["analytics_usage"] > 0.8:
            opportunities.append("Advanced analytics upgrade potential")

        if usage_metrics["usage_frequency"] > 0.8:
            opportunities.append("Power user - potential case study")

        return opportunities

    def _calculate_schedule_date(self, account: EnterpriseAccount, timeline: str) -> datetime:
        """Calculate schedule date based on timeline string"""
        now = datetime.utcnow()

        if "Day 1-3" in timeline:
            return now + timedelta(days=2)
        elif "Day 3-7" in timeline:
            return now + timedelta(days=5)
        elif "Week 2" in timeline:
            return now + timedelta(weeks=2)
        elif "Day 30" in timeline:
            return now + timedelta(days=30)
        elif "Immediate" in timeline:
            return now
        else:
            return now + timedelta(weeks=1)  # Default to 1 week

# Global enterprise sales service instance
enterprise_sales_service = EnterpriseSalesService()