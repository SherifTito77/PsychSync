"""
Enhanced Compliance Audit Service
Provides comprehensive audit logging for GDPR compliance and security monitoring
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()


class AuditAction(str, Enum):
    """Audit action types"""

    # User actions
    USER_REGISTER = "user_register"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # GDPR actions
    GDPR_DATA_EXPORT = "gdpr_data_export"
    GDPR_DATA_DELETE = "gdpr_data_delete"
    GDPR_CONSENT_GRANT = "gdpr_consent_grant"
    GDPR_CONSENT_WITHDRAW = "gdpr_consent_withdraw"

    # Data actions
    DATA_CREATE = "data_create"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # Security actions
    SECURITY_LOGIN_FAILED = "security_login_failed"
    SECURITY_PASSWORD_CHANGE = "security_password_change"
    SECURITY_2FA_ENABLED = "security_2fa_enabled"
    SECURITY_2FA_DISABLED = "security_2fa_disabled"

    # System actions
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_ERROR = "system_error"


class ComplianceAudit(Base):
    """Enhanced compliance audit log model"""

    __tablename__ = "compliance_audit_logs"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Core audit fields
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    session_id = Column(String(255), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Request context
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)

    # Data context
    old_values = Column(JSONB, nullable=True)  # Previous state
    new_values = Column(JSONB, nullable=True)  # New state
    audit_metadata = Column(JSONB, nullable=True)  # Additional context

    # Compliance fields
    legal_basis = Column(String(100), nullable=True)  # GDPR legal basis
    retention_period = Column(Integer, nullable=True)  # Days to retain
    data_subject_id = Column(
        String(255), nullable=True, index=True
    )  # Data subject identifier

    # Security fields
    risk_level = Column(
        String(20), default="low", index=True
    )  # low, medium, high, critical
    success = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)

    # Classification
    data_classification = Column(
        String(50), default="internal"
    )  # public, internal, confidential, restricted
    impact_level = Column(String(20), default="low")  # low, medium, high

    # Hashing for integrity
    data_hash = Column(
        String(64), nullable=True, index=True
    )  # SHA-256 hash of key fields

    # Indexes for performance
    __table_args__ = (
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_action_timestamp", "action", "timestamp"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_compliance", "legal_basis", "retention_period"),
        Index("idx_audit_security", "risk_level", "success"),
        Index("idx_audit_data_subject", "data_subject_id", "timestamp"),
    )


class ComplianceAuditService:
    """Enhanced compliance audit service"""

    def __init__(self):
        self.high_risk_actions = {
            AuditAction.GDPR_DATA_DELETE,
            AuditAction.USER_DELETE,
            AuditAction.SECURITY_2FA_DISABLED,
            AuditAction.DATA_EXPORT,
        }

        self.sensitive_actions = {
            AuditAction.GDPR_DATA_EXPORT,
            AuditAction.GDPR_CONSENT_WITHDRAW,
            AuditAction.SECURITY_PASSWORD_CHANGE,
        }

    async def log_action(
        self,
        db: Session,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: str = None,
        session_id: str = None,
        old_values: dict = None,
        new_values: dict = None,
        audit_metadata: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        request_method: str = None,
        request_path: str = None,
        legal_basis: str = None,
        data_subject_id: str = None,
        success: bool = True,
        error_message: str = None,
        data_classification: str = "internal",
    ) -> ComplianceAudit:
        """
        Log an audit action with comprehensive context

        Args:
            db: Database session
            action: Action type (from AuditAction enum)
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            user_id: User ID performing the action
            session_id: Session ID for tracking
            old_values: Previous state of the resource
            new_values: New state of the resource
            metadata: Additional context data
            ip_address: Client IP address
            user_agent: Client user agent
            request_method: HTTP method
            request_path: Request path
            legal_basis: GDPR legal basis for processing
            data_subject_id: Data subject identifier
            success: Whether action succeeded
            error_message: Error message if action failed
            data_classification: Data classification level

        Returns:
            Created audit log entry
        """
        try:
            # Determine risk level and impact
            risk_level = self._determine_risk_level(action, data_classification)
            impact_level = self._determine_impact_level(action, success)

            # Create audit entry
            audit_log = ComplianceAudit(
                user_id=user_id,
                session_id=session_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                old_values=old_values,
                new_values=new_values,
                audit_metadata=audit_metadata,
                legal_basis=legal_basis,
                data_subject_id=data_subject_id,
                success=success,
                error_message=error_message,
                data_classification=data_classification,
                impact_level=impact_level,
                risk_level=risk_level,
                retention_period=self._determine_retention_period(
                    action, data_classification
                ),
            )

            # Calculate integrity hash
            audit_log.data_hash = self._calculate_data_hash(audit_log)

            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            # Trigger alerts for high-risk actions
            if audit_log.risk_level in ["high", "critical"]:
                await self._trigger_security_alert(audit_log)

            # Log to external system if configured
            await self._log_to_external_system(audit_log)

            return audit_log

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log audit action: {e!s}")
            raise

    async def search_audit_logs(
        self,
        db: Session,
        filters: dict[str, Any] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "timestamp",
        sort_desc: bool = True,
    ) -> dict[str, Any]:
        """
        Search audit logs with advanced filtering

        Args:
            db: Database session
            filters: Search filters
            page: Page number
            limit: Results per page
            sort_by: Field to sort by
            sort_desc: Sort descending if True

        Returns:
            Paginated audit log results
        """
        try:
            query = db.query(ComplianceAudit)

            # Apply filters
            if filters:
                if filters.get("user_id"):
                    query = query.filter(ComplianceAudit.user_id == filters["user_id"])

                if filters.get("action"):
                    query = query.filter(ComplianceAudit.action == filters["action"])

                if filters.get("resource_type"):
                    query = query.filter(
                        ComplianceAudit.resource_type == filters["resource_type"]
                    )

                if filters.get("ip_address"):
                    query = query.filter(
                        ComplianceAudit.ip_address == filters["ip_address"]
                    )

                if filters.get("risk_level"):
                    query = query.filter(
                        ComplianceAudit.risk_level == filters["risk_level"]
                    )

                if filters.get("data_subject_id"):
                    query = query.filter(
                        ComplianceAudit.data_subject_id == filters["data_subject_id"]
                    )

                if filters.get("start_date"):
                    query = query.filter(
                        ComplianceAudit.timestamp >= filters["start_date"]
                    )

                if filters.get("end_date"):
                    query = query.filter(
                        ComplianceAudit.timestamp <= filters["end_date"]
                    )

                if filters.get("success") is not None:
                    query = query.filter(ComplianceAudit.success == filters["success"])

            # Apply sorting
            sort_column = getattr(ComplianceAudit, sort_by, ComplianceAudit.timestamp)
            if sort_desc:
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

            # Count total results
            total = query.count()

            # Apply pagination
            offset = (page - 1) * limit
            results = query.offset(offset).limit(limit).all()

            # Format results
            formatted_results = [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "timestamp": log.timestamp.isoformat(),
                    "ip_address": log.ip_address,
                    "success": log.success,
                    "risk_level": log.risk_level,
                    "impact_level": log.impact_level,
                    "data_classification": log.data_classification,
                    "old_values": log.old_values,
                    "new_values": log.new_values,
                    "metadata": log.metadata,
                    "error_message": log.error_message,
                }
                for log in results
            ]

            return {
                "results": formatted_results,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
            }

        except Exception as e:
            logger.error(f"Failed to search audit logs: {e!s}")
            raise

    async def get_user_activity_summary(
        self, db: Session, user_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Get activity summary for a specific user"""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get user's audit logs
        logs = (
            db.query(ComplianceAudit)
            .filter(
                and_(
                    ComplianceAudit.user_id == user_id,
                    ComplianceAudit.timestamp >= start_date,
                )
            )
            .all()
        )

        # Analyze activity patterns
        actions_by_type = {}
        actions_by_risk = {}
        failed_actions = 0
        total_actions = len(logs)

        for log in logs:
            # Count by action type
            actions_by_type[log.action] = actions_by_type.get(log.action, 0) + 1

            # Count by risk level
            actions_by_risk[log.risk_level] = actions_by_risk.get(log.risk_level, 0) + 1

            # Count failures
            if not log.success:
                failed_actions += 1

        # Get recent activity
        recent_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:10]

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": total_actions,
            "failed_actions": failed_actions,
            "success_rate": (
                ((total_actions - failed_actions) / total_actions * 100)
                if total_actions > 0
                else 0
            ),
            "actions_by_type": actions_by_type,
            "actions_by_risk": actions_by_risk,
            "recent_activity": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "success": log.success,
                    "risk_level": log.risk_level,
                }
                for log in recent_logs
            ],
        }

    async def generate_compliance_report(
        self, db: Session, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Generate comprehensive compliance report"""

        # Get all audit logs in the period
        logs = (
            db.query(ComplianceAudit)
            .filter(
                and_(
                    ComplianceAudit.timestamp >= start_date,
                    ComplianceAudit.timestamp <= end_date,
                )
            )
            .all()
        )

        # Analyze data
        report_data = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_actions": len(logs),
                "successful_actions": sum(1 for log in logs if log.success),
                "failed_actions": sum(1 for log in logs if not log.success),
                "high_risk_actions": sum(
                    1 for log in logs if log.risk_level in ["high", "critical"]
                ),
                "gdpr_actions": sum(
                    1 for log in logs if log.action.startswith("gdpr_")
                ),
            },
            "actions_by_type": {},
            "actions_by_risk_level": {},
            "actions_by_legal_basis": {},
            "data_access_patterns": {},
            "security_incidents": [],
        }

        # Categorize actions
        for log in logs:
            # By action type
            report_data["actions_by_type"][log.action] = (
                report_data["actions_by_type"].get(log.action, 0) + 1
            )

            # By risk level
            report_data["actions_by_risk_level"][log.risk_level] = (
                report_data["actions_by_risk_level"].get(log.risk_level, 0) + 1
            )

            # By legal basis
            if log.legal_basis:
                report_data["actions_by_legal_basis"][log.legal_basis] = (
                    report_data["actions_by_legal_basis"].get(log.legal_basis, 0) + 1
                )

            # Data access patterns
            if log.action in [AuditAction.DATA_READ, AuditAction.DATA_EXPORT]:
                report_data["data_access_patterns"][log.resource_type] = (
                    report_data["data_access_patterns"].get(log.resource_type, 0) + 1
                )

            # Security incidents
            if not log.success and log.risk_level in ["high", "critical"]:
                report_data["security_incidents"].append(
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "user_id": str(log.user_id) if log.user_id else None,
                        "action": log.action,
                        "error_message": log.error_message,
                        "ip_address": log.ip_address,
                    }
                )

        # Add recommendations
        report_data["recommendations"] = self._generate_compliance_recommendations(
            report_data
        )

        return report_data

    def _determine_risk_level(self, action: str, data_classification: str) -> str:
        """Determine risk level based on action and data classification"""

        if action in self.high_risk_actions:
            return "critical"
        if action in self.sensitive_actions:
            return "high"
        if data_classification in ["confidential", "restricted"]:
            return "medium"
        return "low"

    def _determine_impact_level(self, action: str, success: bool) -> str:
        """Determine impact level based on action and success"""

        if not success and action in self.high_risk_actions:
            return "high"
        if action in self.high_risk_actions:
            return "medium"
        return "low"

    def _determine_retention_period(self, action: str, data_classification: str) -> int:
        """Determine retention period in days"""

        # GDPR requires audit logs to be kept for specific periods
        if action.startswith("gdpr_"):
            return 2555  # 7 years for GDPR compliance
        if data_classification in ["confidential", "restricted"]:
            return 1825  # 5 years for sensitive data
        return 1095  # 3 years for standard logs

    def _calculate_data_hash(self, audit_log: ComplianceAudit) -> str:
        """Calculate SHA-256 hash for data integrity"""

        data_string = f"{audit_log.action}{audit_log.resource_type}{audit_log.timestamp}{audit_log.user_id}"
        return hashlib.sha256(data_string.encode()).hexdigest()

    async def _trigger_security_alert(self, audit_log: ComplianceAudit):
        """Trigger security alert for high-risk actions"""
        try:
            alert_message = f"High-risk action detected: {audit_log.action} by user {audit_log.user_id}"
            logger.warning(alert_message)

            # Here you could integrate with:
            # - SIEM systems
            # - Security monitoring tools
            # - Alert notification systems
            # - Incident response workflows

        except Exception as e:
            logger.error(f"Failed to trigger security alert: {e!s}")

    async def _log_to_external_system(self, audit_log: ComplianceAudit):
        """Log to external monitoring systems"""
        try:
            # Integration points:
            # - Splunk
            # - ELK Stack
            # - CloudWatch
            # - Security information systems

            external_log = {
                "timestamp": audit_log.timestamp.isoformat(),
                "action": audit_log.action,
                "user_id": str(audit_log.user_id) if audit_log.user_id else None,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id,
                "ip_address": audit_log.ip_address,
                "risk_level": audit_log.risk_level,
                "success": audit_log.success,
                "data_classification": audit_log.data_classification,
            }

            logger.info(f"External audit log: {json.dumps(external_log)}")

        except Exception as e:
            logger.error(f"Failed to log to external system: {e!s}")

    def _generate_compliance_recommendations(
        self, report_data: dict[str, Any]
    ) -> list[str]:
        """Generate compliance recommendations based on report data"""

        recommendations = []

        # High failure rate
        if (
            report_data["summary"]["failed_actions"]
            / max(report_data["summary"]["total_actions"], 1)
            > 0.1
        ):
            recommendations.append(
                "High failure rate detected. Review error handling and user guidance."
            )

        # High number of high-risk actions
        if report_data["summary"]["high_risk_actions"] > 100:
            recommendations.append(
                "Consider implementing additional approval workflows for high-risk actions."
            )

        # Security incidents
        if len(report_data["security_incidents"]) > 0:
            recommendations.append(
                "Security incidents detected. Review security controls and monitoring."
            )

        # GDPR compliance
        if report_data["summary"]["gdpr_actions"] == 0:
            recommendations.append(
                "No GDPR-related actions logged. Ensure privacy compliance is being tracked."
            )

        return recommendations

    async def cleanup_old_logs(self, db: Session):
        """Clean up audit logs past their retention period"""
        try:
            # Get logs past retention period
            cutoff_date = datetime.utcnow() - timedelta(days=3650)  # 10 years maximum

            # Delete old logs (in production, this would be more sophisticated)
            deleted_count = (
                db.query(ComplianceAudit)
                .filter(ComplianceAudit.timestamp < cutoff_date)
                .delete()
            )

            db.commit()
            logger.info(f"Cleaned up {deleted_count} old audit logs")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old audit logs: {e!s}")
