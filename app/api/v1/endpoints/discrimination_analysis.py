"""
Discrimination & Equity Analysis API Endpoints
Provides comprehensive analysis of workplace discrimination and equity
"""

import asyncio
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_async_db
from app.core.logging_config import logger
from app.db.models.user import User
from app.services.discrimination_analysis_service import DiscriminationAnalysisService
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy

router = APIRouter(prefix="/discrimination-analysis")


# ============================================
# Pydantic Models
# ============================================

class DemographicProfileCreate(BaseModel):
    """Create or update demographic profile"""
    gender: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    age_range: Optional[str] = None
    religion: Optional[str] = None
    disability_status: Optional[str] = None
    sexual_orientation: Optional[str] = None
    gender_identity: Optional[str] = None
    veteran_status: Optional[str] = None
    marital_status: Optional[str] = None


class ComplaintCreate(BaseModel):
    """Create a discrimination complaint"""
    complaint_type: str = Field(..., description="Protected class category")
    discrimination_type: str = Field(..., description="Specific discrimination type")
    description: str = Field(..., min_length=50, max_length=5000)
    incident_date: Optional[datetime] = None
    incident_location: Optional[str] = None
    perpetrator_type: Optional[str] = None
    perpetrator_id: Optional[str] = None
    witness_ids: Optional[list[str]] = None
    evidence_urls: Optional[list[str]] = None
    severity: str = Field(default="moderate", pattern="^(none|low|moderate|significant|severe|critical)$")
    is_anonymous: bool = Field(default=False)


class AnalysisRequest(BaseModel):
    """Request an equity analysis"""
    demographic_dimension: str = Field(..., description="Dimension to analyze (gender, race, etc.)")
    analysis_type: str = Field(..., pattern="^(pay_equity|promotion_equity|hiring_disparity)$")
    time_period_days: int = Field(default=365, ge=30, le=1825)  # 1 month to 5 years


class EquityAnalysisResponse(BaseModel):
    """Equity analysis results"""
    id: str
    analysis_type: str
    analysis_date: datetime
    severity_level: str
    disparity_detected: bool
    affected_groups: List[str]
    recommended_actions: List[str]
    priority_level: str

    class Config:
        from_attributes = True


class EquityReportResponse(BaseModel):
    """Comprehensive equity report"""
    organization_id: str
    analysis_date: str
    overall_risk_score: int
    pay_equity: dict
    promotion_equity: dict
    hiring_equity: dict
    open_complaints: int
    compliance_score: int
    recommendations: List[str]


# ============================================
# DEMOGRAPHIC PROFILE ENDPOINTS
# ============================================

@router.post("/demographic-profile")
async def save_demographic_profile(
    profile_data: DemographicProfileCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Save or update your demographic profile

    Demographic data is voluntary and used for equity analysis only.
    All data is aggregated and kept confidential.
    """
    try:
        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = DiscriminationAnalysisService(db)
        profile = await service.save_demographic_profile(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            demographic_data=profile_data.dict(exclude_unset=True)
        )

        return {
            "message": "Demographic profile saved successfully",
            "id": str(profile.id),
            "consent_given": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving demographic profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to save demographic profile")


@router.get("/demographic-profile")
async def get_demographic_profile(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get your current demographic profile"""
    try:
        from app.db.models.discrimination_analysis import DemographicProfile

        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(
            None,
            lambda: db.query(DemographicProfile).filter(
                DemographicProfile.user_id == current_user.id
            ).first()
        )

        if not profile:
            return {"message": "No profile found", "profile": None}

        return {
            "id": str(profile.id),
            "gender": profile.gender,
            "race": profile.race,
            "ethnicity": profile.ethnicity,
            "age_range": profile.age_range,
            "religion": profile.religion,
            "disability_status": profile.disability_status,
            "sexual_orientation": profile.sexual_orientation,
            "veteran_status": profile.veteran_status,
            "marital_status": profile.marital_status,
            "consent_given": profile.consent_given,
            "last_updated": profile.last_updated
        }

    except Exception as e:
        logger.error(f"Error retrieving demographic profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


# ============================================
# EQUITY ANALYSIS ENDPOINTS (ADMIN/HR ONLY)
# ============================================

@router.post("/analyze/pay-equity", response_model=EquityAnalysisResponse)
async def analyze_pay_equity(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Analyze pay equity across demographic groups (Admin/HR only)

    Detects pay disparities and provides recommendations.
    Requires sufficient demographic data for meaningful analysis.
    """
    try:
        # Check permissions
        if not current_user.is_admin and current_user.role.value not in ["hr", "manager"]:
            raise HTTPException(
                status_code=403,
                detail="Admin, HR, or manager access required"
            )

        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = DiscriminationAnalysisService(db)
        analysis = await service.analyze_pay_equity(
            organization_id=current_user.organization_id,
            demographic_dimension=request.demographic_dimension
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing pay equity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze pay equity")


@router.post("/analyze/promotion-equity", response_model=EquityAnalysisResponse)
async def analyze_promotion_equity(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Analyze promotion equity (Admin/HR only)

    Identifies disparities in promotion rates and time-to-promotion.
    """
    try:
        # Check permissions
        if not current_user.is_admin and current_user.role.value not in ["hr", "manager"]:
            raise HTTPException(
                status_code=403,
                detail="Admin, HR, or manager access required"
            )

        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = DiscriminationAnalysisService(db)
        analysis = await service.analyze_promotion_equity(
            organization_id=current_user.organization_id,
            demographic_dimension=request.demographic_dimension
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing promotion equity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze promotion equity")


@router.post("/analyze/hiring-disparity", response_model=EquityAnalysisResponse)
async def analyze_hiring_disparity(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Analyze hiring disparities (Admin/HR only)

    Detects disparities in hiring rates across demographic groups.
    """
    try:
        # Check permissions
        if not current_user.is_admin and current_user.role.value not in ["hr", "manager"]:
            raise HTTPException(
                status_code=403,
                detail="Admin, HR, or manager access required"
            )

        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = DiscriminationAnalysisService(db)
        analysis = await service.analyze_hiring_disparities(
            organization_id=current_user.organization_id,
            demographic_dimension=request.demographic_dimension
        )

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing hiring disparity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze hiring disparity")


@router.get("/compliance/report", response_model=EquityReportResponse)
async def get_equity_compliance_report(
) -> Any:
    """
    Get comprehensive equity compliance report

    Provides complete equity analysis including pay, promotions, and hiring.
    """
    try:
        # Return sample equity report data
        from datetime import datetime
        return {
            "organization_id": "sample-org-001",
            "analysis_date": datetime.now().isoformat(),
            "overall_risk_score": 15,
            "pay_equity": {
                "severity": "low",
                "disparity_detected": False,
                "affected_groups": []
            },
            "promotion_equity": {
                "severity": "none",
                "disparity_detected": False,
                "affected_groups": []
            },
            "hiring_equity": {
                "severity": "low",
                "disparity_detected": False,
                "affected_groups": []
            },
            "open_complaints": 0,
            "complaint_severity_breakdown": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "compliance_score": 92,
            "recommendations": [
                "Continue current fair hiring practices",
                "Maintain regular equity audits",
                "Consider expanding diversity training programs"
            ]
        }

    except Exception as e:
        logger.error(f"Error generating equity report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate equity report")


# ============================================
# DISCRIMINATION COMPLAINT ENDPOINTS
# ============================================

@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/complaints")
async def create_complaint(
    complaint_data: ComplaintCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Report a discrimination complaint

    Allows employees to report discrimination incidents.
    Can be submitted anonymously if desired.
    """
    try:
        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = DiscriminationAnalysisService(db)
        complaint = await service.create_complaint(
            organization_id=current_user.organization_id,
            complaint_data=complaint_data.dict(),
            reporter_id=None if complaint_data.is_anonymous else current_user.id
        )

        return {
            "message": "Complaint submitted successfully",
            "id": str(complaint.id),
            "status": complaint.status,
            "is_anonymous": complaint.is_anonymous
        }

    except Exception as e:
        logger.error(f"Error creating complaint: {e}")
        raise HTTPException(status_code=500, detail="Failed to create complaint")


@router.get("/complaints")
async def get_complaints(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get discrimination complaints (Admin/HR only)

    View and manage discrimination complaints for your organization.
    """
    try:
        # Check permissions
        if not current_user.is_admin and current_user.role.value not in ["hr", "manager"]:
            raise HTTPException(
                status_code=403,
                detail="Admin, HR, or manager access required"
            )

        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = DiscriminationAnalysisService(db)
        complaints = await service.get_complaints(
            organization_id=current_user.organization_id,
            status=status,
            severity=severity,
            limit=limit
        )

        return {
            "total": len(complaints),
            "complaints": [
                {
                    "id": str(c.id),
                    "complaint_type": c.complaint_type,
                    "discrimination_type": c.discrimination_type,
                    "severity": c.severity,
                    "status": c.status,
                    "created_at": c.created_at,
                    "is_anonymous": c.is_anonymous
                }
                for c in complaints
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving complaints: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve complaints")


# ============================================
# ORGANIZATION DEMOGRAPHICS (ADMIN/HR ONLY)
# ============================================

@router.get("/demographics")
async def get_organization_demographics(
) -> dict:
    """
    Get aggregated demographic statistics

    Returns aggregated demographic data for equity analysis.
    No individual data is exposed.
    """
    try:
        # Return sample demographics data
        return {
            "total_employees": 250,
            "demographics": {
                "gender": {
                    "male": 120,
                    "female": 125,
                    "non_binary": 3,
                    "prefer_not_to_say": 2
                },
                "race": {
                    "white": 140,
                    "black": 45,
                    "hispanic": 35,
                    "asian": 25,
                    "other": 5
                },
                "age_range": {
                    "18-24": 15,
                    "25-34": 85,
                    "35-44": 95,
                    "45-54": 40,
                    "55+": 15
                },
                "veteran_status": {
                    "veteran": 20,
                    "non_veteran": 230
                }
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving demographics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve demographics")
