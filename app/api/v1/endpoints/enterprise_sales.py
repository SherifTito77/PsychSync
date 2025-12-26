"""
Enterprise Sales and Customer Success API Endpoints
B2B account management, health monitoring, and customer success operations
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
from app.db.models.organization import Organization
from app.services.enterprise_sales_service import (
    EnterpriseSalesService,
    AccountTier,
    CustomerHealthStatus,
    SLATier,
    EnterpriseAccount,
    enterprise_sales_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enterprise", tags=["Enterprise Sales & Success"])


@check_rate_limit(identifier="public", endpoint_type="public")
@router.post("/accounts/create")
async def create_enterprise_account(
    organization_id: int,
    tier: AccountTier,
    contract_value: float,
    contract_term_months: int = 12,
    users_licensed: int = 100,
    customer_success_manager: str = "Unassigned",
    custom_requirements: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new enterprise account
    """
    try:
        # Verify user has admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for enterprise account creation"
            )

        # Get organization
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Create enterprise account
        account = await enterprise_sales_service.create_enterprise_account(
            organization=organization,
            tier=tier,
            contract_value=contract_value,
            contract_term_months=contract_term_months,
            users_licensed=users_licensed,
            customer_success_manager=customer_success_manager,
            custom_requirements=custom_requirements
        )

        return {
            "success": True,
            "account": {
                "organization_id": account.organization_id,
                "account_name": account.account_name,
                "tier": account.tier.value,
                "contract_value": account.contract_value,
                "contract_start": account.contract_start.isoformat(),
                "contract_end": account.contract_end.isoformat(),
                "users_licensed": account.users_licensed,
                "sla_tier": account.sla_tier.value,
                "customer_success_manager": account.customer_success_manager
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create enterprise account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enterprise account: {str(e)}"
        )

@router.get("/accounts/health/{organization_id}")
async def get_account_health(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive customer health metrics
    """
    try:
        # Verify user can access this organization
        if not current_user.is_admin and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        health_metrics = await enterprise_sales_service.calculate_customer_health(
            organization_id, db
        )

        return {
            "account_id": health_metrics.account_id,
            "organization_id": health_metrics.organization_id,
            "health_score": health_metrics.health_score,
            "health_status": health_metrics.status.value,
            "metrics": {
                "usage_frequency": round(health_metrics.usage_frequency, 2),
                "feature_adoption": round(health_metrics.feature_adoption, 2),
                "support_tickets": health_metrics.support_tickets,
                "nps_score": health_metrics.nps_score,
                "renewal_risk": health_metrics.renewal_risk,
                "team_engagement": round(health_metrics.team_engagement, 2),
                "mrr_value": health_metrics.mrr_value
            },
            "key_risks": health_metrics.key_risks,
            "opportunities": health_metrics.opportunities,
            "last_login": health_metrics.last_login.isoformat() if health_metrics.last_login else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account health for org {organization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            d
@check_rate_limit(identifier="public", endpoint_type="public")
etail=f"Failed to retrieve account health: {str(e)}"
        )

@router.get("/accounts/opportunities/{organization_id}")
async def get_expansion_opportunities(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get expansion and upsell opportunities
    """
    try:
        # Verify user can access this organization
        if not current_user.is_admin and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        opportunities = await enterprise_sales_service.generate_expansion_opportunities(
            organization_id, db
        )

        return {
            "organization_id": organization_id,
            "total_opportunities": len(opportunities),
            "opportunities": opportunities,
            "total_potential_value": sum(opp.get("potential_value", 0) for opp in opportunities)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get expansion opportunities for org {organization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve expansion opportunities: {str(e)}"
        )

@router.post("/sla/monitor")
async def monitor_sla_compliance(
    sla_tier: SLATier,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Monitor SLA compliance and calculate credits
    """
    try:
        # Verify user has admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for SLA monitoring"
            )

        # Parse date range
        if date_range_start:
            start_date = datetime.fromisoformat(date_range_start.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow() - timedelta(days=30)

        if date_range_end:
            end_date = datetime.fromisoformat(date_range_end.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()

        sla_compliance = await enterprise_sales_service.monitor_sla_compliance(
            sla_tier=sla_tier,
            date_range_start=start_date,
            date_range_end=end_date
        )

        return sla_compliance

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to monitor SLA compliance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to monitor SLA compliance: {str(e)}"
        )

@router.post("/qbr/schedule")
async def schedule_qbr(
    organization_id: int,
    qbr_type: str = "quarterly",
    attendees: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Schedule Quarterly Business Review
    """
    try:
        # Verify user can access this organization
        if not current_user.is_admin and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        qbr_details = await enterprise_sales_service.schedule_qbr(
            organization_id=organization_id,
            qbr_type=qbr_type,
            attendees=attendees
        )

        # Schedule follow-up tasks
        background_tasks.add_task(
            _send_qbr_invitation,
            organization_id,
            qbr_details["meeting_link"],
            qbr_details["scheduled_date"],
            attendees or []
        )

        return {
            "success": True,
            "qbr_scheduled": qbr_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule QBR for org {organization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule QBR: {str(e)}"
        )

@router.get("/accounts/dashboard")
async def get_enterprise_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get enterprise account management dashboard
    """
    try:
        # Verify user has admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for enterprise dashboard"
            )

        # Get all organizations with enterprise features
        enterprise_orgs = db.query(Organization).filter(
            Organization.subscription_tier.in_(["enterprise", "clinical"])
        ).all()

        dashboard_data = {
            "summary": {
                "total_enterprise_accounts": len(enterprise_orgs),
                "total_mrr": sum(org.mrr_value or 0 for org in enterprise_orgs),
                "health_distribution": {},
                "upcoming_renewals": 0
            },
            "accounts": [],
            "sla_compliance": {},
            "top_opportunities": []
        }

        # Process each enterprise account
        for org in enterprise_orgs:
            try:
                health = await enterprise_sales_service.calculate_customer_health(org.id, db)
                opportunities = await enterprise_sales_service.generate_expansion_opportunities(org.id, db)

                account_data = {
                    "organization_id": org.id,
                    "name": org.name,
                    "tier": org.subscription_tier,
                    "health_score": health.health_score,
                    "health_status": health.status.value,
                    "mrr_value": health.mrr_value,
                    "active_users": health.usage_frequency * 100,  # Approximate
                    "opportunities_count": len(opportunities),
                    "renewal_risk": health.renewal_risk
                }

                dashboard_data["accounts"].append(account_data)

                # Update health distribution
                health_status = health.status.value
                dashboard_data["summary"]["health_distribution"][health_status] = \
                    dashboard_data["summary"]["health_distribution"].get(health_status, 0) + 1

                # Collect top opportunities
                for opp in opportunities[:3]:  # Top 3 per account
                    dashboard_data["top_opportunities"].append({
                        "organization_name": org.name,
                        "opportunity": opp
                    })

            except Exception as e:
                logger.warning(f"Failed to process enterprise account {org.id}: {str(e)}")
                continue

        # Sort opportunities by potential value
        dashboard_data["top_opportunities"] = sorted(
            dashboard_data["top_opportunities"],
            key=lambda x: x["opportunity"].get("potential_value", 0),
            reverse=True
        )[:10]  # Top 10 overall

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get enterprise dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve enterprise dashboard: {str(e)}"
        )

@router.get("/features/tiers")
async def get_enterprise_features():
    """
    Get enterprise features by tier
    """
    try:
        features = enterprise_sales_service.enterprise_features

        return {
            "tiers": {
                tier.value: {
                    "tier": tier.value,
                    "features": features_list
                }
                for tier, features_list in features.items()
            }
        }

    except Exception as e:
        logger.error(f"Failed to get enterprise features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enterprise features"
        )

@router.post("/accounts/interventions")
async def trigger_intervention_playbook(
    organization_id: int,
    intervention_type: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger customer success intervention playbook
    """
    try:
        # Verify user can access this organization
        if not current_user.is_admin and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )

        # Validate intervention type
        valid_interventions = ["new_onboarding", "at_risk_intervention", "renewal_campaign", "expansion_opportunity"]
        if intervention_type not in valid_interventions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid intervention type. Valid options: {', '.join(valid_interventions)}"
            )

        # Get organization
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Create mock enterprise account for scheduling
        account = EnterpriseAccount(
            organization_id=organization_id,
            account_name=organization.name,
            tier=AccountTier.ENTERPRISE,  # Default
            customer_success_manager="System",
            contract_value=0,
            contract_start=datetime.utcnow(),
            contract_end=datetime.utcnow(),
            users_licensed=0,
            users_active=0,
            sla_tier=SLATier.ENTERPRISE,
            health_metrics=None,  # Will be filled by service
            custom_integrations=[],
            training_completed=[],
            upcoming_renewal=False,
            expansion_opportunities=[]
        )

        # Schedule success plays
        await enterprise_sales_service._schedule_success_plays(account, intervention_type)

        # Trigger immediate notification
        background_tasks.add_task(
            _notify_customer_success_team,
            organization_id,
            intervention_type,
            current_user.email
        )

        return {
            "success": True,
            "organization_id": organization_id,
            "intervention_type": intervention_type,
            "scheduled_plays": len(enterprise_sales_service.success_plays.get(intervention_type, [])),
            "message": f"Successfully triggered {intervention_type} playbook"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger intervention for org {organization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger intervention: {str(e)}"
        )

# Background task functions
async def _send_qbr_invitation(
    organization_id: int,
    meeting_link: str,
    scheduled_date: datetime,
    attendees: List[str]
):
    """Send QBR invitation email (background task)"""
    try:
        logger.info(f"QBR invitation sent for organization {organization_id}")
        # This would integrate with email service
    except Exception as e:
        logger.error(f"Failed to send QBR invitation: {str(e)}")

async def _notify_customer_success_team(
    organization_id: int,
    intervention_type: str,
    triggered_by: str
):
    """Notify customer success team (background task)"""
    try:
        logger.info(f"Customer success team notified about {intervention_type} for organization {organization_id}")
        # This would integrate with Slack/email notifications
    except Exception as e:
        logger.error(f"Failed to notify customer success team: {str(e)}")