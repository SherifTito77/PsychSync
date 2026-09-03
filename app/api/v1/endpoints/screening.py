"""
Clinical Screening Tools API Endpoints
HIPAA-compliant endpoints for evidence-based mental health screening

IMPORTANT: These endpoints handle Protected Health Information (PHI)
All access is logged and requires proper authorization
"""

import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.hipaa import audit_phi_access, require_clinical_access
from app.api.dependencies.secure_phi import resolve_user_phi
from app.api.v1.deps import get_db
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
from app.services.clinical.screening_service import ScreeningService
from app.services.clinical.scoring_algorithms import (
    CSSRSScorer,
    GAD7Scorer,
    PHQ9Scorer,
    score_asrs,
    score_isi,
)

logger = logging.getLogger(__name__)


async def _audit_screening_access(
    request: Request,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Router-level audit: log every screening read/write as PHI access."""
    action = "write" if request.method in ("POST", "PUT", "PATCH") else "read"
    await audit_phi_access(
        db,
        current_user,
        "clinical_screenings",
        action,
        details={"endpoint": request.url.path, "method": request.method},
        request=request,
    )


router = APIRouter(
    prefix="/screening",
    tags=["clinical-screening"],
    dependencies=[Depends(_audit_screening_access)],
)


# ============================================================================
# CONSENT MANAGEMENT
# ============================================================================


@router.get("/consent/status")
async def get_consent_status(
    screening_type: str = "general",
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """Check whether the user has given consent for a screening type."""
    try:
        svc = ScreeningService(db)
        has_consent = await svc.verify_consent(current_user.id, screening_type)
        return {"has_consent": has_consent, "screening_type": screening_type}
    except Exception:
        return {"has_consent": False, "screening_type": screening_type}


@router.post("/consent")
async def submit_consent(
    consent_type: str = "screening",
    screening_types: str = "general",
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit consent for clinical screening

    HIPAA Requirement: Must obtain explicit consent before collecting PHI
    """
    try:
        svc = ScreeningService(db)
        consent = await svc.submit_consent(
            user_id=current_user.id,
            org_id=getattr(current_user, "org_id", None),
            consent_type=consent_type,
            screening_types=screening_types.split(","),
            consent_text=_get_consent_text(consent_type),
        )
        return {
            "message": "Consent recorded successfully",
            "consent_id": str(consent.id),
            "expires_at": consent.expires_at.isoformat(),
        }
    except Exception:
        return {
            "message": "Consent acknowledged",
            "consent_type": consent_type,
            "screening_types": screening_types,
        }


async def _require_consent(user_id, screening_type: str, svc: ScreeningService) -> None:
    """Raise 403 if valid consent is missing."""
    if not await svc.verify_consent(user_id, screening_type):
        raise HTTPException(
            403,
            "Clinical screening consent required. Please complete consent form first.",
        )


async def _save_screening(
    svc: ScreeningService,
    *,
    current_user: User,
    db: AsyncSession,
    screening_type: str,
    version: str,
    response_dict: dict,
    result,
    background_tasks: BackgroundTasks,
    notify_clinicians: bool = True,
):
    """Save screening with PHI resolved from SecureUser when available."""
    phi = await resolve_user_phi(db, current_user)
    return await svc.save_and_escalate(
        user_id=current_user.id,
        org_id=getattr(current_user, "org_id", None),
        screening_type=screening_type,
        version=version,
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        user_email=phi.email,
        user_name=phi.full_name,
        notify_clinicians=notify_clinicians,
    )


# ============================================================================
# PHQ-9 SCREENING (DEPRESSION)
# ============================================================================


@router.post("/phq9", response_model=ScreeningResponse)
async def submit_phq9(
    responses: PHQ9Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit PHQ-9 Depression Screening

    Patient Health Questionnaire-9
    Reliability: α = 0.89

    CRITICAL: Item 9 assesses suicide ideation
    """
    screening_type = "PHQ9"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

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
    result = PHQ9Scorer.score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="2.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
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
# GAD-7 SCREENING (ANXIETY)
# ============================================================================


@router.post("/gad7", response_model=ScreeningResponse)
async def submit_gad7(
    responses: GAD7Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit GAD-7 Anxiety Screening

    Generalized Anxiety Disorder-7 Scale
    Reliability: α = 0.92
    """
    screening_type = "GAD7"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {
        1: responses.q1_nervous,
        2: responses.q2_control_worry,
        3: responses.q3_worry_too_much,
        4: responses.q4_trouble_relaxing,
        5: responses.q5_restless,
        6: responses.q6_irritable,
        7: responses.q7_afraid,
    }
    result = GAD7Scorer.score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="2.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
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
# C-SSRS SCREENING (SUICIDE RISK) - CRITICAL
# ============================================================================


@router.post("/cssrs", response_model=ScreeningResponse)
async def submit_cssrs(
    responses: CSSRSRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit C-SSRS Suicide Risk Screening

    CRITICAL: ANY positive response triggers immediate crisis protocol
    Columbia-Suicide Severity Rating Scale
    """
    screening_type = "CSSRS"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

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
    result = CSSRSScorer.score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="2.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
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
        subscale_scores=result.subscale_scores,
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
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit MDQ (Mood Disorder Questionnaire) - Bipolar Screening

    Sensitivity: 0.73, Specificity: 0.90
    13 symptom items + clustering + impairment assessment
    """
    screening_type = "MDQ"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {f"q{i}": getattr(responses, f"q{i}") for i in range(1, 14)}
    response_dict["q14_clustered"] = responses.q14_clustered
    response_dict["q15_impairment"] = responses.q15_impairment
    result = MDQScorer().score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
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
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit DAST-10 (Drug Abuse Screening Test)

    Reliability: α = 0.92
    Substance use disorder screening
    """
    screening_type = "DAST10"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {i: getattr(responses, f"q{i}") for i in range(1, 11)}
    result = DAST10Scorer().score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit AQ-10 (Autism Spectrum Quotient)

    Sensitivity: 0.88, Specificity: 0.91
    Adult autism screening
    """
    screening_type = "AQ10"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {i: getattr(responses, f"q{i}") for i in range(1, 11)}
    result = AQ10Scorer().score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit ACE (Adverse Childhood Experiences)

    Childhood trauma screening
    Predictive validity for adult health outcomes
    """
    screening_type = "ACE"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {i: getattr(responses, f"q{i}") for i in range(1, 11)}
    result = ACEScorer().score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
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
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit LSAS (Liebowitz Social Anxiety Scale)

    24 items, each rated on fear (0-3) and avoidance (0-3)
    Reliability: α = 0.95
    """
    from app.services.clinical.advanced_scorers import LSASScorer

    screening_type = "LSAS"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {}
    for i in range(1, 25):
        item_key = f"item_{i}"
        if item_key in responses:
            response_dict[item_key] = {
                "fear": responses[item_key].get("fear", 0),
                "avoidance": responses[item_key].get("avoidance", 0),
            }
    result = LSASScorer().score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
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
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit EAT-26 (Eating Attitudes Test)

    26 items, 6-point scale
    Reliability: α = 0.83
    """
    from app.services.clinical.advanced_scorers import EAT26Scorer

    screening_type = "EAT26"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_items = responses.get("responses", {})
    behavioral_questions = responses.get("behavioral_questions", {})
    result = EAT26Scorer().score(response_items, behavioral_questions)
    response_dict = {
        "item_responses": response_items,
        "behavioral_questions": behavioral_questions,
    }
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
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
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit Y-BOCS (Yale-Brown Obsessive Compulsive Scale)

    10 items (5 obsessions, 5 compulsions), 0-4 scale each
    Reliability: Inter-rater α = 0.98
    """
    from app.services.clinical.advanced_scorers import YBOCSScorer

    screening_type = "YBOCS"
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

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
    result = YBOCSScorer().score(response_dict)
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
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
    current_user: User = Depends(require_clinical_access),
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
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

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
    result = score_asrs(response_dict)  # returns dict
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.1",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
    )
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
    current_user: User = Depends(require_clinical_access),
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
    svc = ScreeningService(db)
    await _require_consent(current_user.id, screening_type, svc)

    response_dict = {
        "1": responses.q1,
        "2": responses.q2,
        "3": responses.q3,
        "4": responses.q4,
        "5": responses.q5,
        "6": responses.q6,
        "7": responses.q7,
    }
    result = score_isi(response_dict)  # returns dict
    screening = await _save_screening(
        svc,
        current_user=current_user,
        db=db,
        screening_type=screening_type,
        version="1.0",
        response_dict=response_dict,
        result=result,
        background_tasks=background_tasks,
        notify_clinicians=False,
    )
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
