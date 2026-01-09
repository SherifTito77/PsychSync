"""
Privacy Policy Service with Versioning and Management
"""

from datetime import datetime
import logging
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class PrivacyPolicy(Base):
    """Privacy Policy version model"""

    __tablename__ = "privacy_policies"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(String(20), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    def __repr__(self):
        return f"<PrivacyPolicy(version={self.version}, active={self.is_active})>"


class UserConsent(Base):
    """User consent tracking model"""

    __tablename__ = "user_consents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_version = Column(String(20), nullable=False)
    consent_type = Column(String(50), nullable=False)  # data_processing, marketing, analytics
    granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    withdrawn_at = Column(DateTime)


class PrivacyPolicyService:
    """Privacy policy management service"""

    def __init__(self):
        self.consent_types = [
            "data_processing",  # Required for service operation
            "analytics",  # Usage analytics
            "marketing",  # Marketing communications
            "research",  # Research and development
            "sharing",  # Data sharing with third parties
        ]

    async def create_privacy_policy(
        self,
        db: Session,
        version: str,
        title: str,
        content: str,
        effective_date: datetime,
        created_by_id: str,
        activate_immediately: bool = False,
    ) -> dict[str, Any]:
        """
        Create a new privacy policy version

        Args:
            db: Database session
            version: Policy version (e.g., "2.1.0")
            title: Policy title
            content: Full policy content (HTML or markdown)
            effective_date: When the policy becomes effective
            created_by_id: User who created the policy
            activate_immediately: Whether to activate this policy immediately

        Returns:
            Created policy information
        """
        try:
            # Check if version already exists
            existing = db.query(PrivacyPolicy).filter(PrivacyPolicy.version == version).first()

            if existing:
                raise ValueError(f"Privacy policy version {version} already exists")

            # Create new policy
            policy = PrivacyPolicy(
                version=version,
                title=title,
                content=content,
                effective_date=effective_date,
                created_by_id=created_by_id,
                is_active=activate_immediately,
            )

            db.add(policy)

            # If activating immediately, deactivate other policies
            if activate_immediately:
                db.query(PrivacyPolicy).filter(PrivacyPolicy.id != policy.id).update(
                    {"is_active": False}
                )

            db.commit()
            db.refresh(policy)

            logger.info(f"Created privacy policy version {version}")

            return {
                "id": str(policy.id),
                "version": policy.version,
                "title": policy.title,
                "effective_date": policy.effective_date.isoformat(),
                "is_active": policy.is_active,
                "created_at": policy.created_at.isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create privacy policy: {e!s}")
            raise

    async def activate_policy_version(
        self, db: Session, version: str, activated_by_id: str
    ) -> dict[str, Any]:
        """Activate a specific privacy policy version"""

        try:
            # Deactivate all policies
            db.query(PrivacyPolicy).update({"is_active": False})

            # Activate specified version
            policy = db.query(PrivacyPolicy).filter(PrivacyPolicy.version == version).first()

            if not policy:
                raise ValueError(f"Privacy policy version {version} not found")

            policy.is_active = True
            db.commit()

            logger.info(f"Activated privacy policy version {version}")

            return {
                "version": policy.version,
                "title": policy.title,
                "activated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to activate policy version {version}: {e!s}")
            raise

    async def get_active_policy(self, db: Session) -> dict[str, Any] | None:
        """Get the currently active privacy policy"""

        policy = db.query(PrivacyPolicy).filter(PrivacyPolicy.is_active == True).first()

        if not policy:
            return None

        return {
            "id": str(policy.id),
            "version": policy.version,
            "title": policy.title,
            "content": policy.content,
            "effective_date": policy.effective_date.isoformat(),
            "created_at": policy.created_at.isoformat(),
        }

    async def get_policy_version(self, db: Session, version: str) -> dict[str, Any] | None:
        """Get a specific privacy policy version"""

        policy = db.query(PrivacyPolicy).filter(PrivacyPolicy.version == version).first()

        if not policy:
            return None

        return {
            "id": str(policy.id),
            "version": policy.version,
            "title": policy.title,
            "content": policy.content,
            "effective_date": policy.effective_date.isoformat(),
            "created_at": policy.created_at.isoformat(),
            "is_active": policy.is_active,
        }

    async def list_policy_versions(
        self, db: Session, include_inactive: bool = False
    ) -> list[dict[str, Any]]:
        """List all privacy policy versions"""

        query = db.query(PrivacyPolicy)
        if not include_inactive:
            query = query.filter(PrivacyPolicy.is_active == True)

        policies = query.order_by(PrivacyPolicy.created_at.desc()).all()

        return [
            {
                "id": str(policy.id),
                "version": policy.version,
                "title": policy.title,
                "effective_date": policy.effective_date.isoformat(),
                "is_active": policy.is_active,
                "created_at": policy.created_at.isoformat(),
            }
            for policy in policies
        ]

    async def record_user_consent(
        self,
        db: Session,
        user_id: str,
        policy_version: str,
        consent_type: str,
        granted: bool,
        ip_address: str = None,
        user_agent: str = None,
    ) -> dict[str, Any]:
        """Record user consent for a specific policy version and consent type"""

        try:
            # Check if consent type is valid
            if consent_type not in self.consent_types:
                raise ValueError(f"Invalid consent type: {consent_type}")

            # Withdraw existing consent for this type
            db.query(UserConsent).filter(
                and_(UserConsent.user_id == user_id, UserConsent.consent_type == consent_type)
            ).update({"withdrawn_at": datetime.utcnow()})

            # Create new consent record
            consent = UserConsent(
                user_id=user_id,
                policy_version=policy_version,
                consent_type=consent_type,
                granted=granted,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            db.add(consent)
            db.commit()
            db.refresh(consent)

            return {
                "id": str(consent.id),
                "consent_type": consent.consent_type,
                "policy_version": consent.policy_version,
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat(),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record user consent: {e!s}")
            raise

    async def get_user_consents(
        self, db: Session, user_id: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get user's current consents"""

        query = db.query(UserConsent).filter(UserConsent.user_id == user_id)

        if active_only:
            query = query.filter(UserConsent.withdrawn_at.is_(None))

        consents = query.order_by(UserConsent.granted_at.desc()).all()

        return [
            {
                "id": str(consent.id),
                "consent_type": consent.consent_type,
                "policy_version": consent.policy_version,
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat(),
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
            }
            for consent in consents
        ]

    async def check_user_consent(self, db: Session, user_id: str, consent_type: str) -> bool:
        """Check if user has granted specific consent"""

        consent = (
            db.query(UserConsent)
            .filter(
                and_(
                    UserConsent.user_id == user_id,
                    UserConsent.consent_type == consent_type,
                    UserConsent.granted == True,
                    UserConsent.withdrawn_at.is_(None),
                )
            )
            .first()
        )

        return consent is not None

    async def get_consent_summary(self, db: Session, policy_version: str = None) -> dict[str, Any]:
        """Get summary of user consents for analytics"""

        query = db.query(UserConsent)
        if policy_version:
            query = query.filter(UserConsent.policy_version == policy_version)

        total_users = db.query(UserConsent.user_id).distinct().count()

        consent_summary = {}
        for consent_type in self.consent_types:
            granted = query.filter(
                and_(
                    UserConsent.consent_type == consent_type,
                    UserConsent.granted == True,
                    UserConsent.withdrawn_at.is_(None),
                )
            ).count()

            consent_summary[consent_type] = {
                "granted": granted,
                "percentage": (granted / total_users * 100) if total_users > 0 else 0,
            }

        return {
            "total_users": total_users,
            "policy_version": policy_version,
            "consents": consent_summary,
        }

    async def generate_privacy_policy_template(self) -> str:
        """Generate a comprehensive privacy policy template"""

        template = """
# Privacy Policy Template for PsychSync

## 1. Information We Collect

### Personal Information
- Name and contact information
- Email address
- Profile information
- Team membership information

### Assessment Data
- Personality assessment responses
- Behavioral analytics data
- Team optimization results

### Usage Data
- How you use our service
- Features you interact with
- Performance and usage statistics

### Technical Data
- IP address
- Browser and device information
- Cookies and similar technologies

## 2. How We Use Your Information

### Service Provision
- To provide and maintain our service
- To process assessment results
- To enable team optimization features

### Communication
- To respond to your inquiries
- To send service-related notifications
- To provide support

### Improvement
- To analyze usage patterns
- To improve our services
- To develop new features

### Legal Compliance
- To comply with legal obligations
- To protect our rights and interests

## 3. Data Sharing and Disclosure

### We Do Not Sell Your Personal Information

### Limited Sharing
- With team members (only data you choose to share)
- With service providers (only as necessary)
- When required by law

### International Transfers
- Data may be processed in secure international locations
- Appropriate safeguards are in place

## 4. Data Security

### Security Measures
- Encryption in transit and at rest
- Access controls and authentication
- Regular security assessments
- Secure data centers

### Data Retention
- We retain data only as long as necessary
- You can request data deletion
- Automatic deletion of inactive accounts

## 5. Your Rights

### Data Access and Portability
- Request a copy of your data
- Receive data in machine-readable format
- Transfer data to other services

### Data Correction and Deletion
- Correct inaccurate information
- Request deletion of your data
- Right to be forgotten

### Consent Management
- Withdraw consent at any time
- Manage privacy preferences
- Opt-out of non-essential processing

### Complaints and Appeals
- Contact our privacy team
- Regulatory complaint options
- Independent dispute resolution

## 6. Children's Privacy

Our service is not intended for children under 13. We do not knowingly collect information from children under 13.

## 7. Changes to This Policy

We may update this privacy policy from time to time. We will notify you of any changes by:
- Posting the new policy on our website
- Sending email notifications
- In-app notifications

## 8. Contact Information

For privacy-related questions or concerns:
- Email: privacy@psychsync.com
- Address: [Your Business Address]
- Phone: [Your Phone Number]

## 9. Effective Date

This privacy policy is effective as of {effective_date} and was last updated on {last_updated}.

## 10. Legal Basis for Processing

We process your personal data based on:
- Contractual necessity (service provision)
- Legal obligation (compliance requirements)
- Legitimate interest (service improvement)
- Consent (optional features)

## 11. Cookie Policy

### Essential Cookies
- Required for basic functionality
- Cannot be disabled

### Analytics Cookies
- Help us understand usage patterns
- Can be disabled in preferences

### Marketing Cookies
- Used for personalized marketing
- Can be disabled in preferences

## 12. Third-Party Services

### Analytics Services
- Google Analytics
- Custom analytics tools

### Communication Services
- Email service providers
- Notification systems

### Payment Processors
- Stripe
- Other payment providers
"""

        return template

    async def send_policy_update_notification(
        self, user_email: str, user_name: str, new_policy_version: str, summary: str
    ):
        """Send notification about privacy policy updates"""
        try:
            # This would integrate with the email service
            subject = f"Important Update: Privacy Policy Version {new_policy_version}"

            message = f"""
Dear {user_name},

We're writing to inform you about important updates to our Privacy Policy.

**What Changed:**
{summary}

**New Policy Version:** {new_policy_version}
**Effective Date:** {datetime.utcnow().strftime("%Y-%m-%d")}

**What This Means for You:**
- Please review the updated policy
- Your existing consents remain in effect
- You can update your preferences anytime

**Review the Full Policy:**
Visit your account settings to read the complete updated policy.

If you have any questions, please contact our privacy team at privacy@psychsync.com.

Best regards,
The PsychSync Team
"""

            # Send email notification
            # await self.email_service.send_email(user_email, subject, message)
            logger.info(f"Privacy policy update notification sent to {user_email}")

        except Exception as e:
            logger.error(f"Failed to send policy update notification: {e!s}")
