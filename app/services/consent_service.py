"""
Consent Management Service
Handles granular user consent management with audit trails and compliance tracking
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, and_
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()


class ConsentType(str, Enum):
    """Types of consent that can be managed"""

    DATA_PROCESSING = "data_processing"  # Required for service operation
    ANALYTICS = "analytics"  # Usage analytics and improvement
    MARKETING = "marketing"  # Marketing communications
    RESEARCH = "research"  # Research and development
    THIRD_PARTY_SHARING = "third_party_sharing"  # Sharing with third parties
    COOKIES_ESSENTIAL = "cookies_essential"  # Essential cookies
    COOKIES_ANALYTICS = "cookies_analytics"  # Analytics cookies
    COOKIES_MARKETING = "cookies_marketing"  # Marketing cookies
    LOCATION_TRACKING = "location_tracking"  # Location-based services
    BIOMETRIC_DATA = "biometric_data"  # Biometric data processing
    AUTOMATED_DECISIONS = "automated_decisions"  # Automated decision making


class ConsentStatus(str, Enum):
    """Status of consent records"""

    ACTIVE = "active"  # Currently granted
    WITHDRAWN = "withdrawn"  # Explicitly withdrawn
    EXPIRED = "expired"  # Time-limited consent expired
    REVOKED = "revoked"  # Revoked by system/admin


class ConsentPurpose(Base):
    """Consent purpose definition"""

    __tablename__ = "consent_purposes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    consent_type = Column(String(100), nullable=False, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    legal_basis = Column(
        String(100), nullable=False
    )  # consent, contract, legal_obligation, vital_interests, public_task, legitimate_interests
    required = Column(Boolean, default=False)  # Whether consent is required for service
    auto_renew = Column(Boolean, default=True)  # Whether consent auto-renews
    expiry_days = Column(Integer, nullable=True)  # Days until consent expires (None = no expiry)
    data_categories = Column(JSONB, nullable=True)  # What data categories this consent covers
    created_at = Column(DateTime, default=datetime.utcnow)


class UserConsentRecord(Base):
    """Detailed user consent record"""

    __tablename__ = "user_consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String(100), nullable=False, index=True)
    purpose_id = Column(UUID(as_uuid=True), ForeignKey("consent_purposes.id"), nullable=True)

    # Consent details
    status = Column(String(20), nullable=False, default=ConsentStatus.ACTIVE)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    withdrawn_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Context information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    consent_form_version = Column(String(20))  # Version of consent form used
    consent_language = Column(String(10), default="en")  # Language of consent

    # Additional details
    granular_preferences = Column(JSONB, nullable=True)  # Granular consent preferences
    purpose_specific_data = Column(JSONB, nullable=True)  # Specific data categories consented to
    withdrawal_reason = Column(Text, nullable=True)  # Reason for withdrawal

    # Legal compliance
    lawful_basis = Column(String(100), nullable=False)
    legitimate_interest_purpose = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConsentHistory(Base):
    """Historical tracking of consent changes"""

    __tablename__ = "consent_history"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    consent_record_id = Column(
        UUID(as_uuid=True), ForeignKey("user_consent_records.id"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Change details
    action = Column(String(50), nullable=False)  # granted, withdrawn, modified, expired
    previous_status = Column(String(20))
    new_status = Column(String(20))

    # Context
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    change_reason = Column(Text)
    admin_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # If changed by admin


class ConsentManagementService:
    """Comprehensive consent management service"""

    def __init__(self):
        self.required_consents = {ConsentType.DATA_PROCESSING, ConsentType.COOKIES_ESSENTIAL}

        self.automated_decision_consents = {
            ConsentType.AUTOMATED_DECISIONS,
            ConsentType.BIOMETRIC_DATA,
        }

    async def initialize_consent_purposes(self, db: Session):
        """Initialize default consent purposes"""

        default_purposes = [
            {
                "consent_type": ConsentType.DATA_PROCESSING,
                "name": "Data Processing",
                "description": "Processing your personal data to provide PsychSync services including team optimization, assessments, and analytics.",
                "legal_basis": "contract",
                "required": True,
                "auto_renew": True,
                "data_categories": ["profile", "assessment_data", "team_data"],
            },
            {
                "consent_type": ConsentType.ANALYTICS,
                "name": "Analytics and Improvement",
                "description": "Anonymous usage analytics to improve our services and user experience.",
                "legal_basis": "legitimate_interests",
                "required": False,
                "auto_renew": True,
                "data_categories": ["usage_patterns", "performance_metrics"],
            },
            {
                "consent_type": ConsentType.MARKETING,
                "name": "Marketing Communications",
                "description": "Receive information about new features, updates, and promotional offers.",
                "legal_basis": "consent",
                "required": False,
                "auto_renew": False,
                "data_categories": ["contact_information"],
            },
            {
                "consent_type": ConsentType.RESEARCH,
                "name": "Research and Development",
                "description": "Use anonymized data for research purposes to improve team optimization algorithms.",
                "legal_basis": "legitimate_interests",
                "required": False,
                "auto_renew": True,
                "data_categories": ["anonymized_assessment_data", "aggregated_metrics"],
            },
            {
                "consent_type": ConsentType.THIRD_PARTY_SHARING,
                "name": "Third Party Data Sharing",
                "description": "Share necessary data with trusted third-party service providers to operate our service.",
                "legal_basis": "legitimate_interests",
                "required": True,
                "auto_renew": True,
                "data_categories": ["minimal_operational_data"],
            },
            {
                "consent_type": ConsentType.COOKIES_ANALYTICS,
                "name": "Analytics Cookies",
                "description": "Cookies that help us understand how you use our website.",
                "legal_basis": "consent",
                "required": False,
                "auto_renew": False,
                "data_categories": ["cookies", "tracking_data"],
            },
            {
                "consent_type": ConsentType.AUTOMATED_DECISIONS,
                "name": "Automated Decision Making",
                "description": "AI-powered team optimization and recommendations based on your data.",
                "legal_basis": "contract",
                "required": True,
                "auto_renew": True,
                "data_categories": ["assessment_responses", "personality_data"],
            },
        ]

        for purpose_data in default_purposes:
            existing = (
                db.query(ConsentPurpose)
                .filter(ConsentPurpose.consent_type == purpose_data["consent_type"])
                .first()
            )

            if not existing:
                purpose = ConsentPurpose(**purpose_data)
                db.add(purpose)

        db.commit()

    async def grant_consent(
        self,
        db: Session,
        user_id: str,
        consent_type: str,
        granular_preferences: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        consent_form_version: str = "1.0",
        consent_language: str = "en",
    ) -> dict[str, Any]:
        """
        Grant consent for a specific purpose

        Args:
            db: Database session
            user_id: User ID
            consent_type: Type of consent
            granular_preferences: Granular consent preferences
            ip_address: Client IP address
            user_agent: Client user agent
            consent_form_version: Version of consent form
            consent_language: Language of consent

        Returns:
            Created consent record
        """
        try:
            # Get consent purpose
            purpose = (
                db.query(ConsentPurpose).filter(ConsentPurpose.consent_type == consent_type).first()
            )

            if not purpose:
                raise ValueError(f"Invalid consent type: {consent_type}")

            # Check if user already has active consent
            existing_consent = (
                db.query(UserConsentRecord)
                .filter(
                    and_(
                        UserConsentRecord.user_id == user_id,
                        UserConsentRecord.consent_type == consent_type,
                        UserConsentRecord.status == ConsentStatus.ACTIVE,
                    )
                )
                .first()
            )

            if existing_consent:
                # Update existing consent
                existing_consent.granular_preferences = granular_preferences
                existing_consent.updated_at = datetime.utcnow()
                consent_record = existing_consent
            else:
                # Create new consent record
                expires_at = None
                if purpose.expiry_days:
                    expires_at = datetime.utcnow() + timedelta(days=purpose.expiry_days)

                consent_record = UserConsentRecord(
                    user_id=user_id,
                    consent_type=consent_type,
                    purpose_id=purpose.id,
                    status=ConsentStatus.ACTIVE,
                    granted_at=datetime.utcnow(),
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    consent_form_version=consent_form_version,
                    consent_language=consent_language,
                    granular_preferences=granular_preferences or {},
                    purpose_specific_data=purpose.data_categories,
                    lawful_basis=purpose.legal_basis,
                )

                db.add(consent_record)

            db.commit()
            db.refresh(consent_record)

            # Log consent history
            await self._log_consent_change(
                db=db,
                consent_record_id=consent_record.id,
                user_id=user_id,
                action="granted",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(f"Consent granted for user {user_id}, type {consent_type}")

            return {
                "consent_id": str(consent_record.id),
                "consent_type": consent_record.consent_type,
                "status": consent_record.status,
                "granted_at": consent_record.granted_at.isoformat(),
                "expires_at": consent_record.expires_at.isoformat()
                if consent_record.expires_at
                else None,
                "lawful_basis": consent_record.lawful_basis,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to grant consent: {e!s}")
            raise

    async def withdraw_consent(
        self,
        db: Session,
        user_id: str,
        consent_type: str,
        withdrawal_reason: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> dict[str, Any]:
        """Withdraw previously granted consent"""

        try:
            # Check if consent can be withdrawn
            if consent_type in self.required_consents:
                raise ValueError(f"Cannot withdraw required consent: {consent_type}")

            # Get active consent record
            consent_record = (
                db.query(UserConsentRecord)
                .filter(
                    and_(
                        UserConsentRecord.user_id == user_id,
                        UserConsentRecord.consent_type == consent_type,
                        UserConsentRecord.status == ConsentStatus.ACTIVE,
                    )
                )
                .first()
            )

            if not consent_record:
                raise ValueError(f"No active consent found for type: {consent_type}")

            # Update consent record
            consent_record.status = ConsentStatus.WITHDRAWN
            consent_record.withdrawn_at = datetime.utcnow()
            consent_record.withdrawal_reason = withdrawal_reason

            db.commit()

            # Log consent history
            await self._log_consent_change(
                db=db,
                consent_record_id=consent_record.id,
                user_id=user_id,
                action="withdrawn",
                previous_status=ConsentStatus.ACTIVE,
                new_status=ConsentStatus.WITHDRAWN,
                ip_address=ip_address,
                user_agent=user_agent,
                change_reason=withdrawal_reason,
            )

            logger.info(f"Consent withdrawn for user {user_id}, type {consent_type}")

            return {
                "consent_id": str(consent_record.id),
                "consent_type": consent_record.consent_type,
                "status": consent_record.status,
                "withdrawn_at": consent_record.withdrawn_at.isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to withdraw consent: {e!s}")
            raise

    async def get_user_consents(
        self, db: Session, user_id: str, include_history: bool = False, active_only: bool = True
    ) -> dict[str, Any]:
        """Get user's current consent status"""

        try:
            # Get consent purposes
            purposes = db.query(ConsentPurpose).all()
            purpose_map = {p.consent_type: p for p in purposes}

            # Get user's consent records
            query = db.query(UserConsentRecord).filter(UserConsentRecord.user_id == user_id)

            if active_only:
                query = query.filter(UserConsentRecord.status == ConsentStatus.ACTIVE)

            consent_records = query.all()

            # Build consent status
            consent_status = {}
            for purpose in purposes:
                user_consent = next(
                    (c for c in consent_records if c.consent_type == purpose.consent_type), None
                )

                consent_status[purpose.consent_type] = {
                    "name": purpose.name,
                    "description": purpose.description,
                    "required": purpose.required,
                    "legal_basis": purpose.lawful_basis,
                    "current_status": user_consent.status if user_consent else None,
                    "granted_at": user_consent.granted_at.isoformat() if user_consent else None,
                    "withdrawn_at": user_consent.withdrawn_at.isoformat()
                    if user_consent and user_consent.withdrawn_at
                    else None,
                    "expires_at": user_consent.expires_at.isoformat()
                    if user_consent and user_consent.expires_at
                    else None,
                    "granular_preferences": user_consent.granular_preferences
                    if user_consent
                    else None,
                    "consent_id": str(user_consent.id) if user_consent else None,
                }

            result = {
                "user_id": user_id,
                "consent_status": consent_status,
                "last_updated": max(
                    (c.updated_at for c in consent_records), default=datetime.utcnow()
                ).isoformat(),
            }

            if include_history:
                result["consent_history"] = await self._get_consent_history(db, user_id)

            return result

        except Exception as e:
            logger.error(f"Failed to get user consents: {e!s}")
            raise

    async def check_consent(
        self, db: Session, user_id: str, consent_type: str, granular_check: str = None
    ) -> bool:
        """Check if user has valid consent"""

        try:
            consent_record = (
                db.query(UserConsentRecord)
                .filter(
                    and_(
                        UserConsentRecord.user_id == user_id,
                        UserConsentRecord.consent_type == consent_type,
                        UserConsentRecord.status == ConsentStatus.ACTIVE,
                    )
                )
                .first()
            )

            if not consent_record:
                return False

            # Check if consent has expired
            if consent_record.expires_at and consent_record.expires_at < datetime.utcnow():
                # Mark as expired
                consent_record.status = ConsentStatus.EXPIRED
                db.commit()
                return False

            # Check granular preferences if specified
            if granular_check and consent_record.granular_preferences:
                return consent_record.granular_preferences.get(granular_check, False)

            return True

        except Exception as e:
            logger.error(f"Failed to check consent: {e!s}")
            return False

    async def process_consent_request(
        self,
        db: Session,
        user_id: str,
        consent_data: list[dict[str, Any]],
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Process bulk consent request (e.g., from consent form)"""

        try:
            results = []
            errors = []

            for consent_item in consent_data:
                try:
                    consent_type = consent_item.get("consent_type")
                    action = consent_item.get("action")  # "grant" or "withdraw"

                    if not consent_type or not action:
                        errors.append(f"Missing consent_type or action for item: {consent_item}")
                        continue

                    if action == "grant":
                        result = await self.grant_consent(
                            db=db,
                            user_id=user_id,
                            consent_type=consent_type,
                            granular_preferences=consent_item.get("granular_preferences"),
                            ip_address=context.get("ip_address"),
                            user_agent=context.get("user_agent"),
                            consent_form_version=context.get("form_version", "1.0"),
                            consent_language=context.get("language", "en"),
                        )
                        results.append(result)

                    elif action == "withdraw":
                        result = await self.withdraw_consent(
                            db=db,
                            user_id=user_id,
                            consent_type=consent_type,
                            withdrawal_reason=consent_item.get("reason"),
                            ip_address=context.get("ip_address"),
                            user_agent=context.get("user_agent"),
                        )
                        results.append(result)

                except Exception as e:
                    errors.append(f"Failed to process consent item {consent_item}: {e!s}")

            return {
                "user_id": user_id,
                "processed_count": len(results),
                "error_count": len(errors),
                "results": results,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Failed to process consent request: {e!s}")
            raise

    async def get_consent_analytics(
        self, db: Session, start_date: datetime = None, end_date: datetime = None
    ) -> dict[str, Any]:
        """Get consent analytics for compliance reporting"""

        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # Get consent records in period
            consent_records = (
                db.query(UserConsentRecord)
                .filter(
                    and_(
                        UserConsentRecord.granted_at >= start_date,
                        UserConsentRecord.granted_at <= end_date,
                    )
                )
                .all()
            )

            # Analyze consent patterns
            analytics = {
                "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
                "total_consent_grants": len(consent_records),
                "consent_by_type": {},
                "consent_by_language": {},
                "withdrawn_consents": 0,
                "expired_consents": 0,
                "unique_users": len(set(c.user_id for c in consent_records)),
                "consent_form_versions": {},
            }

            for consent in consent_records:
                # By consent type
                consent_type = consent.consent_type
                analytics["consent_by_type"][consent_type] = (
                    analytics["consent_by_type"].get(consent_type, 0) + 1
                )

                # By language
                language = consent.consent_language or "en"
                analytics["consent_by_language"][language] = (
                    analytics["consent_by_language"].get(language, 0) + 1
                )

                # By status
                if consent.status == ConsentStatus.WITHDRAWN:
                    analytics["withdrawn_consents"] += 1
                elif consent.status == ConsentStatus.EXPIRED:
                    analytics["expired_consents"] += 1

                # By form version
                version = consent.consent_form_version or "unknown"
                analytics["consent_form_versions"][version] = (
                    analytics["consent_form_versions"].get(version, 0) + 1
                )

            # Get current active consents
            active_consents = (
                db.query(UserConsentRecord)
                .filter(
                    and_(
                        UserConsentRecord.status == ConsentStatus.ACTIVE,
                        UserConsentRecord.expires_at > datetime.utcnow()
                        if UserConsentRecord.expires_at.isnot(None)
                        else True,
                    )
                )
                .all()
            )

            analytics["current_active_consents"] = len(active_consents)
            analytics["active_consent_breakdown"] = {}
            for consent in active_consents:
                consent_type = consent.consent_type
                analytics["active_consent_breakdown"][consent_type] = (
                    analytics["active_consent_breakdown"].get(consent_type, 0) + 1
                )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get consent analytics: {e!s}")
            raise

    async def _log_consent_change(
        self,
        db: Session,
        consent_record_id: str,
        user_id: str,
        action: str,
        previous_status: str = None,
        new_status: str = None,
        ip_address: str = None,
        user_agent: str = None,
        change_reason: str = None,
    ):
        """Log consent change for audit trail"""

        try:
            history = ConsentHistory(
                consent_record_id=consent_record_id,
                user_id=user_id,
                action=action,
                previous_status=previous_status,
                new_status=new_status,
                ip_address=ip_address,
                user_agent=user_agent,
                change_reason=change_reason,
            )

            db.add(history)
            db.commit()

        except Exception as e:
            logger.error(f"Failed to log consent change: {e!s}")

    async def _get_consent_history(
        self, db: Session, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get user's consent change history"""

        try:
            history = (
                db.query(ConsentHistory)
                .filter(ConsentHistory.user_id == user_id)
                .order_by(ConsentHistory.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "action": h.action,
                    "consent_type": h.consent_record.consent_type if h.consent_record else None,
                    "timestamp": h.timestamp.isoformat(),
                    "previous_status": h.previous_status,
                    "new_status": h.new_status,
                    "ip_address": h.ip_address,
                    "change_reason": h.change_reason,
                }
                for h in history
            ]

        except Exception as e:
            logger.error(f"Failed to get consent history: {e!s}")
            return []

    async def cleanup_expired_consents(self, db: Session):
        """Clean up expired consent records"""

        try:
            # Find expired consents
            expired_consents = (
                db.query(UserConsentRecord)
                .filter(
                    and_(
                        UserConsentRecord.status == ConsentStatus.ACTIVE,
                        UserConsentRecord.expires_at < datetime.utcnow(),
                    )
                )
                .all()
            )

            # Mark as expired
            for consent in expired_consents:
                consent.status = ConsentStatus.EXPIRED
                await self._log_consent_change(
                    db=db,
                    consent_record_id=consent.id,
                    user_id=consent.user_id,
                    action="expired",
                    previous_status=ConsentStatus.ACTIVE,
                    new_status=ConsentStatus.EXPIRED,
                )

            db.commit()
            logger.info(f"Marked {len(expired_consents)} consent records as expired")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup expired consents: {e!s}")
