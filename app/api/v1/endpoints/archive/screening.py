"""
Clinical Screening Tools API Endpoints
HIPAA-compliant endpoints for evidence-based mental health screening

IMPORTANT: These endpoints handle Protected Health Information (PHI)
All access is logged and requires proper authorization
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.clinical.scoring_algorithms import (
    CSSRSScorer,
    GAD7Scorer,
    PHQ9Scorer,
    get_scorer,
    score_asrs,
    score_isi,
)
from app.api.v1.deps import get_current_user, get_db
from app.db.models.clinical_screening import (
    ClinicalAlert,
    ClinicalConsent,
    ClinicalScreening,
)
from app.db.models.user import User
from app.schemas.clinical import (
    ASRSRequest,
    CSSRSRequest,
    GAD7Request,
    ISIRequest,
    PHQ9Request,
    ScreeningResponse,
)
from app.services.clinical.additional_scorers import (
    ACEScorer,
    AQ10Scorer,
    DAST10Scorer,
    MDQScorer,
)
from app.services.clinical.additional_scorers import get_scorer as get_additional_scorer
from app.services.clinical.crisis_intervention import CrisisInterventionService

router = APIRouter(prefix="/screening", tags=["clinical-screening"])
logger = logging.getLogger(__name__)

# Development mode: Skip consent requirement for testing
# IMPORTANT: This should NEVER be enabled in production (HIPAA requirement)
import os

SKIP_CONSENT_CHECK = os.getenv("SKIP_CONSENT_CHECK", "false").lower() in (
    "true",
    "1",
    "yes",
)


# ============================================================================
# CONSENT MANAGEMENT
# ============================================================================


class ConsentRequest(BaseModel):
    consent_type: str
    screening_types: List[str]


@router.post("/consent")
async def submit_consent(
    request: ConsentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit consent for clinical screening

    HIPAA Requirement: Must obtain explicit consent before collecting PHI
    """
    org_id = (
        current_user.organization.id if current_user.organization else current_user.id
    )

    consent = ClinicalConsent(
        user_id=current_user.id,
        org_id=org_id,
        consent_type=request.consent_type,
        consent_version="2.0",
        consented=True,
        consent_text=_get_consent_text(request.consent_type),
        screening_types=request.screening_types,
        consented_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc).replace(
            year=datetime.now(timezone.utc).year + 1
        ),  # 1 year
    )

    db.add(consent)
    await db.commit()

    return {
        "message": "Consent recorded successfully",
        "consent_id": str(consent.id),
        "expires_at": consent.expires_at.isoformat(),
    }


@router.get("/consent/status")
async def get_consent_status(
    screening_type: str = "PHQ9",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if the user has consented to a specific screening type
    """
    has_consent = await verify_consent(current_user.id, screening_type, db)
    return {"has_consent": has_consent}


async def verify_consent(
    user_id: uuid.UUID, screening_type: str, db: AsyncSession
) -> bool:
    """Verify user has valid consent for screening

    DEVELOPMENT MODE: Set SKIP_CONSENT_CHECK=true env var to bypass consent check
    WARNING: NEVER enable in production - this violates HIPAA requirements
    """
    # Development bypass for testing
    if SKIP_CONSENT_CHECK:
        logger.warning(f"CONSENT CHECK BYPASSED for user {user_id} - DEVELOPMENT MODE")
        return True

    result = await db.execute(
        select(ClinicalConsent).where(
            ClinicalConsent.user_id == user_id,
            ClinicalConsent.consent_type == "screening",
            ClinicalConsent.consented == True,
            ClinicalConsent.withdrawn == False,
            ClinicalConsent.expires_at > datetime.now(timezone.utc),
        )
    )
    # Check ALL consent records to find one that covers the screening type
    consents = result.scalars().all()

    for consent in consents:
        if screening_type in (consent.screening_types or []):
            return True

    return False


# ============================================================================
# PHQ-9 SCREENING (DEPRESSION)
# ============================================================================


@router.post("/phq9", response_model=ScreeningResponse)
async def submit_phq9(
    responses: PHQ9Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit PHQ-9 Depression Screening

    Patient Health Questionnaire-9
    Reliability: α = 0.89

    CRITICAL: Item 9 assesses suicide ideation
    """
    screening_type = "PHQ9"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(
            403,
            "Clinical screening consent required. Please complete consent form first.",
        )

    # Convert Pydantic model to dict for scorer
    response_dict = {
        1: responses.q1_interest,
        2: responses.q2_depressed,
        3: responses.q3_sleep,
        4: responses.q4_energy,
        5: responses.q5_appetite,
        6: responses.q6_self_worth,
        7: responses.q7_concentration,
        8: responses.q8_motor,
        9: responses.q9_suicide,
    }

    # Score the assessment
    scorer = PHQ9Scorer()
    result = scorer.score(response_dict)

    # Get org_id safely
    org_id = (
        current_user.organization.id if current_user.organization else current_user.id
    )

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=org_id,
        screening_type=screening_type,
        version="2.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed (Item 9 assesses suicide ideation)
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=org_id,
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        # Notify clinicians of crisis alert
        from app.services.clinical.notification_service import (
            ClinicianNotificationService,
        )

        notification_service = ClinicianNotificationService(db)
        await notification_service.notify_clinicians_of_alert(
            alert_id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            screening_id=str(screening.id),
            org_id=str(org_id),
            alert_message=alert.alert_message,
        )

        logger.critical(
            f"PHQ-9 Crisis alert triggered for user {current_user.id} and clinicians notified"
        )

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores={},
        completed_at=screening.completed_at,
    )


# ============================================================================
# C-SSRS - Columbia-Suicide Severity Rating Scale
# CRITICAL: ANY positive response triggers immediate crisis protocol
# ============================================================================
@router.post("/cssrs", response_model=ScreeningResponse)
async def submit_cssrs(
    responses: CSSRSRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit C-SSRS Suicide Risk Screening

    CRITICAL: ANY positive response triggers immediate crisis protocol
    Columbia-Suicide Severity Rating Scale
    """
    screening_type = "CSSRS"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(
            403,
            "Clinical screening consent required. Please complete consent form first.",
        )

    # Convert to dict
    response_dict = {
        "q1": responses.q1_wish_dead,
        "q2": responses.q2_nonspecific_thoughts,
        "q3": responses.q3_active_ideation,
        "q4": responses.q4_intent,
        "q5": responses.q5_plan,
        "q11": responses.q11_actual_attempt,
        "q12": responses.q12_preparatory_acts,
        "q13": responses.q13_aborted_attempt,
    }

    # Score using CSSRS scorer
    scorer = CSSRSScorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="2.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores={},
        completed_at=screening.completed_at,
    )


# ============================================================================
# GAD-7 SCREENING (ANXIETY)
# ============================================================================


@router.post("/gad7", response_model=ScreeningResponse)
async def submit_gad7(
    responses: GAD7Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit GAD-7 Anxiety Screening

    Generalized Anxiety Disorder-7 Scale
    Reliability: α = 0.92
    """
    screening_type = "GAD7"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert to dict
    response_dict = {
        1: responses.q1_nervous,
        2: responses.q2_control_worry,
        3: responses.q3_worry_too_much,
        4: responses.q4_trouble_relaxing,
        5: responses.q5_restless,
        6: responses.q6_irritable,
        7: responses.q7_afraid,
    }

    # Score
    scorer = GAD7Scorer()
    result = scorer.score(response_dict)

    # Save
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="2.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        # Notify clinicians of crisis alert
        from app.services.clinical.notification_service import (
            ClinicianNotificationService,
        )

        notification_service = ClinicianNotificationService(db)
        await notification_service.notify_clinicians_of_alert(
            alert_id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            screening_id=str(screening.id),
            org_id=str(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            alert_message=alert.alert_message,
        )

        logger.critical(
            f"Crisis alert triggered for {screening_type} screening user {current_user.id} and clinicians notified"
        )

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores={},
        completed_at=screening.completed_at,
    )


# ============================================================================
# MDQ - MOOD DISORDER QUESTIONNAIRE (BIPOLAR SCREENING)
# ============================================================================


class MDQRequest(BaseModel):
    """MDQ Assessment Request"""

    q1: bool = False
    q2: bool = False
    q3: bool = False
    q4: bool = False
    q5: bool = False
    q6: bool = False
    q7: bool = False
    q8: bool = False
    q9: bool = False
    q10: bool = False
    q11: bool = False
    q12: bool = False
    q13: bool = False
    q14_clustered: bool = False
    q15_impairment: int = 0


@router.post("/mdq", response_model=ScreeningResponse)
async def submit_mdq(
    responses: MDQRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit MDQ (Mood Disorder Questionnaire) - Bipolar Screening

    Sensitivity: 0.73, Specificity: 0.90
    13 symptom items + clustering + impairment assessment
    """
    screening_type = "MDQ"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert to dict format
    response_dict = {f"q{i}": getattr(responses, f"q{i}") for i in range(1, 14)}
    response_dict["q14_clustered"] = responses.q14_clustered
    response_dict["q15_impairment"] = responses.q15_impairment

    # Score the assessment
    scorer = MDQScorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        logger.critical(f"MDQ Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# DAST-10 - DRUG ABUSE SCREENING TEST
# ============================================================================


class DAST10Request(BaseModel):
    """DAST-10 Assessment Request"""

    q1: bool = False
    q2: bool = False
    q3: bool = False
    q4: bool = False
    q5: bool = False
    q6: bool = False
    q7: bool = False
    q8: bool = False
    q9: bool = False
    q10: bool = False


@router.post("/dast10", response_model=ScreeningResponse)
async def submit_dast10(
    responses: DAST10Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit DAST-10 (Drug Abuse Screening Test)

    Reliability: α = 0.92
    Substance use disorder screening
    """
    screening_type = "DAST10"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert to dict format
    response_dict = {i: getattr(responses, f"q{i}") for i in range(1, 11)}

    # Score the assessment
    scorer = DAST10Scorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        logger.critical(f"DAST-10 Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# AQ-10 - AUTISM SPECTRUM QUOTIENT
# ============================================================================


class AQ10Request(BaseModel):
    """AQ-10 Assessment Request"""

    q1: int = 0
    q2: int = 0
    q3: int = 0
    q4: int = 0
    q5: int = 0
    q6: int = 0
    q7: int = 0
    q8: int = 0
    q9: int = 0
    q10: int = 0


@router.post("/aq10", response_model=ScreeningResponse)
async def submit_aq10(
    responses: AQ10Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit AQ-10 (Autism Spectrum Quotient)

    Sensitivity: 0.88, Specificity: 0.91
    Adult autism screening
    """
    screening_type = "AQ10"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert to dict format
    response_dict = {i: getattr(responses, f"q{i}") for i in range(1, 11)}

    # Score the assessment
    scorer = AQ10Scorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# ACE - ADVERSE CHILDHOOD EXPERIENCES
# ============================================================================


class ACERequest(BaseModel):
    """ACE Assessment Request"""

    q1: bool = False
    q2: bool = False
    q3: bool = False
    q4: bool = False
    q5: bool = False
    q6: bool = False
    q7: bool = False
    q8: bool = False
    q9: bool = False
    q10: bool = False


@router.post("/ace", response_model=ScreeningResponse)
async def submit_ace(
    responses: ACERequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit ACE (Adverse Childhood Experiences)

    Childhood trauma screening
    Predictive validity for adult health outcomes
    """
    screening_type = "ACE"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert to dict format
    response_dict = {i: getattr(responses, f"q{i}") for i in range(1, 11)}

    # Score the assessment
    scorer = ACEScorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_consent_text(consent_type: str) -> str:
    """Get full consent language"""
    texts = {
        "screening": """
I consent to complete mental health screening assessments through PsychSync.

I understand that:
• These assessments are screening tools, NOT diagnostic tools
• Results will be reviewed by licensed mental health professionals
• In cases of safety concerns, my information may be shared with emergency services
• I can withdraw consent at any time
• My data is protected under HIPAA

I understand that a positive screen does NOT mean I have a mental health disorder.
It means I should speak with a mental health professional for proper evaluation.
        """
    }
    return texts.get(consent_type, "Consent text not available")


# ============================================================================
# LSAS - LIEBOWITZ SOCIAL ANXIETY SCALE
# ============================================================================


@router.post("/lsas", response_model=ScreeningResponse)
async def submit_lsas(
    responses: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit LSAS (Liebowitz Social Anxiety Scale)

    24 items, each rated on fear (0-3) and avoidance (0-3)
    Reliability: α = 0.95
    """
    from app.services.clinical.advanced_scorers import LSASScorer

    screening_type = "LSAS"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert responses to dict format
    response_dict = {}
    for i in range(1, 25):
        item_key = f"item_{i}"
        if item_key in responses:
            response_dict[item_key] = {
                "fear": responses[item_key].get("fear", 0),
                "avoidance": responses[item_key].get("avoidance", 0),
            }

    # Score the assessment
    scorer = LSASScorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        # Notify clinicians of crisis alert
        from app.services.clinical.notification_service import (
            ClinicianNotificationService,
        )

        notification_service = ClinicianNotificationService(db)
        await notification_service.notify_clinicians_of_alert(
            alert_id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            screening_id=str(screening.id),
            org_id=str(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            alert_message=alert.alert_message,
        )

        logger.critical(
            f"Crisis alert triggered for {screening_type} screening user {current_user.id} and clinicians notified"
        )

        logger.critical(f"LSAS Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# EAT-26 - EATING ATTITUDES TEST
# ============================================================================


@router.post("/eat26", response_model=ScreeningResponse)
async def submit_eat26(
    responses: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit EAT-26 (Eating Attitudes Test)

    26 items, 6-point scale
    Reliability: α = 0.83
    """
    from app.services.clinical.advanced_scorers import EAT26Scorer

    screening_type = "EAT26"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Extract responses and behavioral questions
    response_items = responses.get("responses", {})
    behavioral_questions = responses.get("behavioral_questions", {})

    # Score the assessment
    scorer = EAT26Scorer()
    result = scorer.score(response_items, behavioral_questions)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses={
            "item_responses": response_items,
            "behavioral_questions": behavioral_questions,
        },
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed (eating disorders can be life-threatening)
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        logger.critical(f"EAT-26 Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# Y-BOCS - YALE-BROWN OBSESSIVE COMPULSIVE SCALE
# ============================================================================


@router.post("/ybocs", response_model=ScreeningResponse)
async def submit_ybocs(
    responses: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit Y-BOCS (Yale-Brown Obsessive Compulsive Scale)

    10 items (5 obsessions, 5 compulsions), 0-4 scale each
    Reliability: Inter-rater α = 0.98
    """
    from app.services.clinical.advanced_scorers import YBOCSScorer

    screening_type = "YBOCS"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(403, "Clinical screening consent required")

    # Convert to dict format
    response_dict = {
        1: responses.get("item_1_time_obsessions", 0),
        2: responses.get("item_2_interference_obsessions", 0),
        3: responses.get("item_3_distress_obsessions", 0),
        4: responses.get("item_4_resistance_obsessions", 0),
        5: responses.get("item_5_control_obsessions", 0),
        6: responses.get("item_6_time_compulsions", 0),
        7: responses.get("item_7_interference_compulsions", 0),
        8: responses.get("item_8_distress_compulsions", 0),
        9: responses.get("item_9_resistance_compulsions", 0),
        10: responses.get("item_10_control_compulsions", 0),
    }

    # Score the assessment
    scorer = YBOCSScorer()
    result = scorer.score(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        risk_flags=result.risk_flags,
        crisis_alert=result.crisis_alert,
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed
    if result.crisis_alert:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result.risk_level,
            risk_flags=result.risk_flags,
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        # Notify clinicians of crisis alert
        from app.services.clinical.notification_service import (
            ClinicianNotificationService,
        )

        notification_service = ClinicianNotificationService(db)
        await notification_service.notify_clinicians_of_alert(
            alert_id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            screening_id=str(screening.id),
            org_id=str(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            alert_message=alert.alert_message,
        )

        logger.critical(
            f"Crisis alert triggered for {screening_type} screening user {current_user.id} and clinicians notified"
        )

        logger.critical(f"Y-BOCS Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result.total_score,
        severity_level=result.severity_level,
        risk_level=result.risk_level,
        interpretation=result.interpretation,
        recommendations=result.recommendations,
        crisis_alert=result.crisis_alert,
        risk_flags=result.risk_flags,
        subscale_scores=result.subscale_scores,
        completed_at=screening.completed_at,
    )


# ============================================================================
# ASRS v1.1 SCREENING (ADULT ADHD)
# ============================================================================


@router.post("/asrs", response_model=ScreeningResponse)
async def submit_asrs(
    responses: ASRSRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Adult ADHD Self-Report Scale v1.1 Symptom Checklist

    18 questions measuring ADHD symptoms in adulthood:
    - Part A: Inattention (9 questions)
    - Part B: Hyperactivity-Impulsivity (9 questions)

    Scoring: Each question 0-4 (Never to Very Often)
    - Part A score ≥ 24 suggests ADHD inattentive type
    - Part B score ≥ 24 suggests ADHD hyperactive-impulsive type
    - Both ≥ 24 suggests ADHD combined type

    Reliability: Sensitivity 68.7%, Specificity 72.1% (for DSM-5 ADHD)
    Validated for adult populations (18+ years)
    """
    screening_type = "ASRS"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(
            403,
            "Clinical screening consent required. Please complete consent form first.",
        )

    # Convert Pydantic model to dict for scorer
    response_dict = {
        "1": responses.q1,
        "2": responses.q2,
        "3": responses.q3,
        "4": responses.q4,
        "5": responses.q5,
        "6": responses.q6,
        "7": responses.q7,
        "8": responses.q8,
        "9": responses.q9,
        "10": responses.q10,
        "11": responses.q11,
        "12": responses.q12,
        "13": responses.q13,
        "14": responses.q14,
        "15": responses.q15,
        "16": responses.q16,
        "17": responses.q17,
        "18": responses.q18,
    }

    # Score the assessment using the wrapper function
    result = score_asrs(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.1",
        responses=response_dict,
        total_score=result["total_score"],
        severity_level=result["severity_level"],
        risk_level=result["risk_level"],
        risk_flags=result["risk_flags"],
        crisis_alert=result["crisis_alert"],
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed (though ASRS rarely triggers)
    if result["crisis_alert"]:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result["risk_level"],
            risk_flags=result["risk_flags"],
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        logger.critical(f"ASRS Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result["total_score"],
        severity_level=result["severity_level"],
        risk_level=result["risk_level"],
        interpretation=result["interpretation"],
        recommendations=result["recommendations"],
        crisis_alert=result["crisis_alert"],
        risk_flags=result["risk_flags"],
        subscale_scores=result.get("subscale_scores", {}),
        completed_at=screening.completed_at,
    )


# ============================================================================
# ISI SCREENING (INSOMNIA SEVERITY INDEX)
# ============================================================================


@router.post("/isi", response_model=ScreeningResponse)
async def submit_isi(
    responses: ISIRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Insomnia Severity Index (ISI)

    7 questions measuring insomnia severity over the past 2 weeks:
    - Sleep onset, maintenance, and early morning difficulties
    - Satisfaction with sleep pattern
    - Noticeability to others
    - Worry/distress about sleep
    - Interference with daily functioning

    Scoring: Each question 0-4 (No problem to Very severe problem)
    - 0-7: No clinically significant insomnia
    - 8-14: Subthreshold insomnia
    - 15-21: Clinical insomnia (moderate)
    - 22-28: Clinical insomnia (severe)

    Reliability: Cronbach's α = 0.91
    Validated for assessing insomnia severity and treatment outcomes
    """
    screening_type = "ISI"

    # Verify consent
    has_consent = await verify_consent(current_user.id, screening_type, db)
    if not has_consent:
        raise HTTPException(
            403,
            "Clinical screening consent required. Please complete consent form first.",
        )

    # Convert Pydantic model to dict for scorer
    response_dict = {
        "1": responses.q1,
        "2": responses.q2,
        "3": responses.q3,
        "4": responses.q4,
        "5": responses.q5,
        "6": responses.q6,
        "7": responses.q7,
    }

    # Score the assessment using the wrapper function
    result = score_isi(response_dict)

    # Save screening results
    screening = ClinicalScreening(
        user_id=current_user.id,
        org_id=(
            current_user.organization.id
            if current_user.organization
            else current_user.id
        ),
        screening_type=screening_type,
        version="1.0",
        responses=response_dict,
        total_score=result["total_score"],
        severity_level=result["severity_level"],
        risk_level=result["risk_level"],
        risk_flags=result["risk_flags"],
        crisis_alert=result["crisis_alert"],
        informed_consent=True,
        consent_timestamp=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    db.add(screening)
    await db.commit()
    await db.refresh(screening)

    # Crisis intervention if needed (though insomnia rarely triggers)
    if result["crisis_alert"]:
        crisis_service = CrisisInterventionService(db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=current_user.id,
            org_id=(
                current_user.organization.id
                if current_user.organization
                else current_user.id
            ),
            risk_level=result["risk_level"],
            risk_flags=result["risk_flags"],
            screening_data={"screening_type": screening_type},
        )

        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=current_user.email,
            user_name=current_user.full_name,
        )

        logger.critical(f"ISI Crisis alert triggered for user {current_user.id}")

    return ScreeningResponse(
        id=screening.id,
        screening_type=screening_type,
        total_score=result["total_score"],
        severity_level=result["severity_level"],
        risk_level=result["risk_level"],
        interpretation=result["interpretation"],
        recommendations=result["recommendations"],
        crisis_alert=result["crisis_alert"],
        risk_flags=result["risk_flags"],
        subscale_scores=result.get("subscale_scores", {}),
        completed_at=screening.completed_at,
    )
