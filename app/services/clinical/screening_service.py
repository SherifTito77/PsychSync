"""
Clinical Screening Service

Encapsulates all database operations for clinical screenings, keeping
API endpoints thin (score → delegate → return).

HIPAA note: all operations are logged at the caller level via the endpoint layer.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clinical_screening import ClinicalConsent, ClinicalScreening
from app.services.clinical.crisis_intervention import CrisisInterventionService

logger = logging.getLogger(__name__)

# Some scorers (score_asrs, score_isi) return plain dicts; others return ScoringResult.
# _f() normalises both so the service doesn't need to know which it received.
_UNSET = object()


def _f(result: Any, key: str, default: Any = _UNSET) -> Any:
    if isinstance(result, dict):
        return result[key] if default is _UNSET else result.get(key, default)
    return getattr(result, key)


class ScreeningService:
    """Service layer for clinical screening DB operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Consent
    # ------------------------------------------------------------------

    async def submit_consent(
        self,
        user_id: UUID,
        org_id: Optional[UUID],
        consent_type: str,
        screening_types: List[str],
        consent_text: str,
    ) -> ClinicalConsent:
        """Persist a new consent record and return it."""
        now = datetime.utcnow()
        consent = ClinicalConsent(
            user_id=user_id,
            org_id=org_id,
            consent_type=consent_type,
            consent_version="2.0",
            consented=True,
            consent_text=consent_text,
            screening_types=screening_types,
            consented_at=now,
            expires_at=now.replace(year=now.year + 1),
        )
        self.db.add(consent)
        await self.db.commit()
        return consent

    async def verify_consent(self, user_id: UUID, screening_type: str) -> bool:
        """Return True if user has a valid, non-expired consent covering screening_type."""
        result = await self.db.execute(
            select(ClinicalConsent).where(
                ClinicalConsent.user_id == user_id,
                ClinicalConsent.consent_type == "screening",
                ClinicalConsent.consented == True,  # noqa: E712
                ClinicalConsent.withdrawn == False,  # noqa: E712
                ClinicalConsent.expires_at > datetime.utcnow(),
            )
        )
        consent = result.scalar_one_or_none()
        if not consent:
            return False
        return screening_type in (consent.screening_types or [])

    # ------------------------------------------------------------------
    # Screening persistence + crisis escalation
    # ------------------------------------------------------------------

    async def save_and_escalate(
        self,
        *,
        user_id: UUID,
        org_id: Optional[UUID],
        screening_type: str,
        version: str,
        response_dict: Dict[str, Any],
        result: Any,  # ScoringResult dataclass or plain dict
        background_tasks: BackgroundTasks,
        user_email: str,
        user_name: str,
        notify_clinicians: bool = True,
    ) -> ClinicalScreening:
        """
        Persist screening result and, when a crisis is flagged, create an alert
        and activate the crisis protocol (including clinician notification).

        Returns the saved ClinicalScreening ORM instance.
        """
        now = datetime.utcnow()
        screening = ClinicalScreening(
            user_id=user_id,
            org_id=org_id,
            screening_type=screening_type,
            version=version,
            responses=response_dict,
            total_score=_f(result, "total_score"),
            severity_level=_f(result, "severity_level"),
            risk_level=_f(result, "risk_level"),
            risk_flags=_f(result, "risk_flags"),
            crisis_alert=_f(result, "crisis_alert"),
            informed_consent=True,
            consent_timestamp=now,
            completed_at=now,
        )
        self.db.add(screening)
        await self.db.commit()
        await self.db.refresh(screening)

        if _f(result, "crisis_alert"):
            await self._handle_crisis(
                screening=screening,
                user_id=user_id,
                org_id=org_id,
                result=result,
                background_tasks=background_tasks,
                user_email=user_email,
                user_name=user_name,
                notify_clinicians=notify_clinicians,
            )

        return screening

    async def _handle_crisis(
        self,
        *,
        screening: ClinicalScreening,
        user_id: UUID,
        org_id: Optional[UUID],
        result: Any,
        background_tasks: BackgroundTasks,
        user_email: str,
        user_name: str,
        notify_clinicians: bool,
    ) -> None:
        crisis_service = CrisisInterventionService(self.db)
        alert = await crisis_service.create_alert(
            screening_id=screening.id,
            user_id=user_id,
            org_id=org_id,
            risk_level=_f(result, "risk_level"),
            risk_flags=_f(result, "risk_flags"),
            screening_data={"screening_type": screening.screening_type},
        )
        await crisis_service.activate_crisis_protocol(
            alert=alert,
            background_tasks=background_tasks,
            user_email=user_email,
            user_name=user_name,
        )

        if notify_clinicians:
            from app.services.clinical.notification_service import (
                ClinicianNotificationService,
            )

            notifier = ClinicianNotificationService(self.db)
            await notifier.notify_clinicians_of_alert(
                alert_id=str(alert.id),
                alert_type=alert.alert_type,
                severity=alert.severity,
                screening_id=str(screening.id),
                org_id=str(org_id),
                alert_message=alert.alert_message,
            )

        logger.critical(
            "Crisis alert triggered: screening_type=%s user=%s",
            screening.screening_type,
            user_id,
        )
