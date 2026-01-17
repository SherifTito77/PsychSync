"""
Legal Rights Awareness API Endpoints
Provides employees with access to legal rights information and resources
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.db.models.user import User
from app.services.legal_rights_service import LegalRightsService, LegalRightsAnalyzer
from app.middleware.rate_limiter import check_rate_limit

router = APIRouter(prefix="/legal-rights")


# ============================================
# Pydantic Models
# ============================================

class LaborLawResponse(BaseModel):
    """Labor law information"""
    id: str
    country_name: str
    law_name: str
    category: str
    description: str
    min_wage: Optional[float]
    max_weekly_hours: Optional[int]
    overtime_threshold: Optional[int]
    overtime_rate: Optional[float]
    mandatory_break_minutes: Optional[int]
    min_vacation_days: Optional[int]

    class Config:
        from_attributes = True


class RightsSummaryResponse(BaseModel):
    """Employee rights summary"""
    country_code: str
    country_name: str
    total_laws: int
    categories: dict
    key_protections: dict
    protection_levels: dict


class RightsResourceResponse(BaseModel):
    """Employee rights resource"""
    id: str
    title: str
    category: str
    resource_type: str
    summary: Optional[str]
    url: Optional[str]
    thumbnail_url: Optional[str]
    video_url: Optional[str]
    duration_minutes: Optional[int]
    view_count: int

    class Config:
        from_attributes = True


class ContractViolationCreate(BaseModel):
    """Create a contract violation report"""
    affected_employee_id: Optional[str] = None
    violation_type: str = Field(..., description="Type of violation")
    category: str = Field(..., description="Violation category")
    severity: str = Field(..., pattern="^(low|medium|high|critical|legal_action_required)$")
    title: str = Field(..., min_length=10, max_length=255)
    description: str = Field(..., min_length=50, max_length=5000)
    labor_law_violated: Optional[str] = None
    law_reference: Optional[str] = None
    incident_date_range: Optional[dict] = None
    evidence_urls: Optional[list[str]] = None


class ContractViolationResponse(BaseModel):
    """Contract violation details"""
    id: str
    violation_type: str
    category: str
    severity: str
    title: str
    description: str
    status: str
    detected_at: datetime
    legal_risk_score: Optional[int]

    class Config:
        from_attributes = True


class KnowledgeCheckRequest(BaseModel):
    """Knowledge check submission"""
    check_type: str = Field(..., description="Type of knowledge check")
    responses: List[dict] = Field(..., min_items=1)


class KnowledgeCheckResponse(BaseModel):
    """Knowledge check results"""
    id: str
    check_type: str
    score_percentage: int
    passed: bool
    knowledge_gaps: List[str]
    recommended_resources: List[str]
    completed_at: datetime

    class Config:
        from_attributes = True


class LegalAidResourceResponse(BaseModel):
    """Legal aid resource"""
    id: str
    name: str
    resource_type: str
    description: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    address: Optional[str]
    specializations: Optional[list]
    free_consultation: bool
    rating: Optional[float]

    class Config:
        from_attributes = True


class ComplianceReportResponse(BaseModel):
    """Organization compliance report"""
    legal_risk_score: int
    total_open_violations: int
    critical_violations: int
    high_severity_violations: int
    violations_by_category: dict
    compliance_percentage: int
    recommendations: List[str]
    analyzed_at: str


# ============================================
# LABOR LAW ENDPOINTS
# ============================================

@router.get("/labor-laws", response_model=List[LaborLawResponse])
async def get_labor_laws(
    country_code: str = Query(..., description="ISO country code (e.g., US, UK, CA)"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    state_region: Optional[str] = Query(None, description="Optional state/region"),
) -> Any:
    """
    Get labor laws for a specific country

    Returns comprehensive labor law information including:
    - Minimum wage requirements
    - Maximum working hours
    - Overtime regulations
    - Break requirements
    - Vacation entitlements
    """
    try:
        # Return sample data for now
        sample_laws = [
            {
                "id": "1",
                "country_code": "US",
                "country_name": "United States",
                "state_region": None,
                "law_name": "Fair Labor Standards Act (FLSA)",
                "category": "wages_hours",
                "description": "Establishes minimum wage, overtime pay, recordkeeping, and youth employment standards.",
                "min_wage": 7.25,
                "max_weekly_hours": 40,
                "overtime_threshold": 40,
                "overtime_rate": 1.5,
                "mandatory_break_minutes": None,
                "min_vacation_days": 0,
                "last_updated": "2024-01-01",
                "is_active": True
            },
            {
                "id": "2",
                "country_code": "US",
                "country_name": "United States",
                "state_region": None,
                "law_name": "Family and Medical Leave Act (FMLA)",
                "category": "leave",
                "description": "Provides eligible employees with up to 12 weeks of unpaid, job-protected leave per year.",
                "min_wage": None,
                "max_weekly_hours": None,
                "overtime_threshold": None,
                "overtime_rate": None,
                "mandatory_break_minutes": None,
                "min_vacation_days": None,
                "last_updated": "2024-01-01",
                "is_active": True
            },
            {
                "id": "3",
                "country_code": "US",
                "country_name": "United States",
                "state_region": None,
                "law_name": "Occupational Safety and Health Act (OSHA)",
                "category": "safety",
                "description": "Ensures safe and healthful working conditions by setting and enforcing standards.",
                "min_wage": None,
                "max_weekly_hours": None,
                "overtime_threshold": None,
                "overtime_rate": None,
                "mandatory_break_minutes": None,
                "min_vacation_days": None,
                "last_updated": "2024-01-01",
                "is_active": True
            },
            {
                "id": "4",
                "country_code": "US",
                "country_name": "United States",
                "state_region": None,
                "law_name": "Title VII of the Civil Rights Act",
                "category": "discrimination",
                "description": "Prohibits employment discrimination based on race, color, religion, sex, or national origin.",
                "min_wage": None,
                "max_weekly_hours": None,
                "overtime_threshold": None,
                "overtime_rate": None,
                "mandatory_break_minutes": None,
                "min_vacation_days": None,
                "last_updated": "2024-01-01",
                "is_active": True
            }
        ]

        # Filter by category if provided
        if category:
            sample_laws = [law for law in sample_laws if law["category"] == category]

        return sample_laws

    except Exception as e:
        logger.error(f"Error retrieving labor laws: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve labor laws")


@router.get("/rights-summary", response_model=RightsSummaryResponse)
async def get_rights_summary(
    country_code: str = Query(..., description="ISO country code"),
    state_region: Optional[str] = Query(None, description="Optional state/region"),
) -> Any:
    """
    Get comprehensive summary of employee rights

    Provides an easy-to-understand summary of all employee rights
    organized by category with key protections highlighted.
    """
    try:
        # Return sample data
        return {
            "country_code": country_code.upper(),
            "country_name": "United States" if country_code.upper() == "US" else country_code.upper(),
            "total_laws": 4,
            "categories": {
                "wages_hours": 2,
                "leave": 1,
                "safety": 1,
                "discrimination": 1
            },
            "key_protections": {
                "min_wage": 7.25,
                "max_weekly_hours": 40,
                "overtime_threshold": 40,
                "overtime_rate": 1.5,
                "min_vacation_days": 0
            },
            "protection_levels": {
                "discrimination": 9,
                "safety": 8,
                "wages": 7,
                "leave": 7
            }
        }
    except Exception as e:
        logger.error(f"Error generating rights summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate rights summary")


# ============================================
# EDUCATIONAL RESOURCES ENDPOINTS
# ============================================

@router.get("/resources", response_model=List[RightsResourceResponse])
async def get_rights_resources(
    category: Optional[str] = Query(None, description="Filter by category"),
    resource_type: Optional[str] = Query(None, description="Filter by type"),
    featured_only: bool = Query(False, description="Only featured resources"),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """
    Get educational resources about employee rights

    Returns articles, videos, guides, and tools to help employees
    understand their legal rights in the workplace.
    """
    try:
        # Return sample resources
        sample_resources = [
            {
                "id": "1",
                "title": "Understanding Your Workplace Rights",
                "category": "general",
                "resource_type": "article",
                "summary": "A comprehensive guide to understanding your fundamental rights as an employee.",
                "url": "https://www.dol.gov/general/topic",
                "thumbnail_url": None,
                "video_url": None,
                "duration_minutes": None,
                "view_count": 1250
            },
            {
                "id": "2",
                "title": "Overtime Pay Explained",
                "category": "wages_hours",
                "resource_type": "video",
                "summary": "Learn when you're entitled to overtime pay and how it's calculated.",
                "url": "https://www.youtube.com/watch?v=example",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "video_url": "https://www.youtube.com/watch?v=example",
                "duration_minutes": 15,
                "view_count": 3420
            },
            {
                "id": "3",
                "title": "Workplace Discrimination: What You Need to Know",
                "category": "discrimination",
                "resource_type": "guide",
                "summary": "Understanding your protections against workplace discrimination and harassment.",
                "url": "https://www.eeoc.gov/",
                "thumbnail_url": None,
                "video_url": None,
                "duration_minutes": None,
                "view_count": 892
            }
        ]

        # Apply filters
        if category:
            sample_resources = [r for r in sample_resources if r["category"] == category]
        if resource_type:
            sample_resources = [r for r in sample_resources if r["resource_type"] == resource_type]

        return sample_resources[:limit]

    except Exception as e:
        logger.error(f"Error retrieving resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve resources")


@router.post("/resources/{resource_id}/helpful")
async def mark_resource_helpful(
    resource_id: str,
    helpful: bool = Query(..., description="True if helpful, False if not"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Mark a resource as helpful or not helpful"""
    try:
        service = LegalRightsService(db)
        success = await service.mark_resource_helpful(
            resource_id=UUID(resource_id),
            helpful=helpful
        )

        if not success:
            raise HTTPException(status_code=404, detail="Resource not found")

        return {"message": "Feedback recorded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


# ============================================
# CONTRACT VIOLATION ENDPOINTS
# ============================================

@check_rate_limit(identifier="user", limit_name="strict")
@router.post("/violations/report", response_model=ContractViolationResponse)
async def report_violation(
    violation_data: ContractViolationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Report a potential contract or labor law violation

    Allows employees to report suspected violations of their rights.
    Reports can be anonymous if no affected_employee_id is provided.
    """
    try:
        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = LegalRightsService(db)
        violation = await service.create_violation_report(
            organization_id=current_user.organization_id,
            violation_data=violation_data.dict(),
            reported_by=current_user.id
        )
        return violation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating violation report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create violation report")


@router.get("/violations", response_model=List[ContractViolationResponse])
async def get_violations(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """
    Get contract violations for your organization

    Requires appropriate permissions to view violations.
    Regular employees can only see their own reported violations.
    HR/Admin can see all violations.
    """
    try:
        # Return empty list for now - no violations
        return []

    except Exception as e:
        logger.error(f"Error retrieving violations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve violations")


# ============================================
# KNOWLEDGE CHECK ENDPOINTS
# ============================================

@router.post("/knowledge-check", response_model=KnowledgeCheckResponse)
async def submit_knowledge_check(
    check_data: KnowledgeCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Submit a knowledge check assessment

    Tests employees' understanding of their legal rights.
    Provides feedback on knowledge gaps and recommended resources.
    """
    try:
        if not current_user.organization_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")

        service = LegalRightsService(db)
        knowledge_check = await service.create_knowledge_check(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            check_type=check_data.check_type,
            responses=check_data.responses
        )
        return knowledge_check

    except Exception as e:
        logger.error(f"Error creating knowledge check: {e}")
        raise HTTPException(status_code=500, detail="Failed to create knowledge check")


@router.get("/knowledge-check/history", response_model=List[KnowledgeCheckResponse])
async def get_knowledge_check_history(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get your knowledge check history"""
    try:
        service = LegalRightsService(db)
        history = await service.get_user_knowledge_history(
            user_id=current_user.id,
            limit=limit
        )
        return history

    except Exception as e:
        logger.error(f"Error retrieving knowledge check history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


# ============================================
# LEGAL AID ENDPOINTS
# ============================================

@router.get("/legal-aid", response_model=List[LegalAidResourceResponse])
async def find_legal_aid(
    country_code: str = Query(..., description="ISO country code"),
    state_region: Optional[str] = Query(None, description="Optional state/region"),
    city: Optional[str] = Query(None, description="Optional city"),
    specialization: Optional[str] = Query(None, description="Area of specialization"),
    free_only: bool = Query(False, description="Only free/pro bono services"),
) -> Any:
    """
    Find legal aid resources

    Returns a list of lawyers, legal aid organizations, labor boards,
    and hotlines that can help with employment law issues.
    """
    try:
        # Return sample legal aid resources
        sample_resources = [
            {
                "id": "1",
                "name": "National Employment Law Project",
                "resource_type": "organization",
                "description": "Non-profit organization advocating for workers' rights",
                "phone": "1-866-667-8352",
                "email": "info@nelp.org",
                "website": "https://www.nelp.org",
                "address": "1200 18th Street NW, Suite 200, Washington, DC 20036",
                "specializations": ["employment law", "worker rights", "policy advocacy"],
                "free_consultation": True,
                "rating": 4.8
            },
            {
                "id": "2",
                "name": "Legal Aid Society - Employment Law Division",
                "resource_type": "legal_aid",
                "description": "Provides free legal services for low-income workers",
                "phone": "1-800-641-6967",
                "email": "employment@legalaid.org",
                "website": "https://www.legalaid.org",
                "address": None,
                "specializations": ["wrongful termination", "discrimination", "wage theft"],
                "free_consultation": True,
                "rating": 4.6
            },
            {
                "id": "3",
                "name": "US Department of Labor - Wage and Hour Division",
                "resource_type": "government",
                "description": "Federal agency enforcing labor laws",
                "phone": "1-866-4US-WAGE (1-866-487-9243)",
                "email": None,
                "website": "https://www.dol.gov/agencies/whd",
                "address": "200 Constitution Avenue NW, Washington, DC 20210",
                "specializations": ["wage and hour", "overtime", "child labor"],
                "free_consultation": True,
                "rating": None
            }
        ]

        # Apply filters
        if specialization:
            sample_resources = [r for r in sample_resources if specialization.lower() in " ".join(r.get("specializations", [])).lower()]

        if free_only:
            sample_resources = [r for r in sample_resources if r.get("free_consultation", False)]

        return sample_resources

    except Exception as e:
        logger.error(f"Error finding legal aid: {e}")
        raise HTTPException(status_code=500, detail="Failed to find legal aid resources")


# ============================================
# COMPLIANCE ANALYTICS (ADMIN/HR ONLY)
# ============================================

@router.get("/compliance/report", response_model=ComplianceReportResponse)
async def get_compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get organization compliance report (Admin/HR only)

    Provides comprehensive analysis of legal compliance status
    including risk scores, open violations, and recommendations.
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

        analyzer = LegalRightsAnalyzer(db)
        report = await analyzer.analyze_organization_compliance(
            organization_id=current_user.organization_id
        )
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")
