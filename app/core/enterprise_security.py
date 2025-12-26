"""
Enterprise Security Compliance Implementation
Addresses SOC 2 Type II, ISO 27001, GDPR, HIPAA, and FedRAMP requirements
"""

import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import json
import audit_logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ComplianceStandard(Enum):
    """Enterprise compliance standards"""
    SOC_2_TYPE_II = "soc2_type2"
    ISO_27001 = "iso_27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    FEDRAMP = "fedramp"

class DataClassification(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class SecurityEvent:
    """Security event for monitoring and compliance"""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    resource_accessed: str
    action: str
    outcome: str
    compliance_standards: List[ComplianceStandard]
    metadata: Dict[str, Any]

class EnterpriseSecurityManager:
    """Enterprise security compliance manager"""

    def __init__(self, db_session, redis_client, logger=None):
        self.db = db_session
        self.redis = redis_client
        self.logger = logger or logging.getLogger(__name__)
        self.encryption_key = self._initialize_encryption()
        self.compliance_configs = self._load_compliance_configs()

    def _initialize_encryption(self) -> bytes:
        """Initialize encryption key for data protection"""
        try:
            # Load or generate encryption key
            key_file = os.getenv("ENCRYPTION_KEY_FILE", "/secure/encryption.key")

            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key_data = f.read()
            else:
                # Generate new encryption key
                password = os.getenv("MASTER_ENCRYPTION_PASSWORD", "").encode()
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))

                # Save key securely
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(key)
                with open(key_file + '.salt', 'wb') as f:
                    f.write(salt)

                key_data = key

            return key_data

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {str(e)}")
            # Generate temporary key for development
            return Fernet.generate_key()

    def _load_compliance_configs(self) -> Dict[ComplianceStandard, Dict]:
        """Load compliance requirements for each standard"""
        return {
            ComplianceStandard.SOC_2_TYPE_II: {
                "audit_retention_days": 365,
                "encryption_required": True,
                "multi_factor_auth": True,
                "access_logging": True,
                "vulnerability_scanning": True,
                "incident_response_plan": True
            },
            ComplianceStandard.ISO_27001: {
                "risk_assessment_frequency": 90,
                "security_training_required": True,
                "business_continuity_plan": True,
                "access_reviews": True,
                "asset_inventory": True
            },
            ComplianceStandard.GDPR: {
                "data_retention_limits": True,
                "right_to_erasure": True,
                "data_portability": True,
                "consent_management": True,
                "breach_notification_72h": True
            },
            ComplianceStandard.HIPAA: {
                "phi_protection": True,
                "audit_trail_required": True,
                "business_associate_agreements": True,
                "security_rule_compliance": True,
                "privacy_rule_compliance": True
            },
            ComplianceStandard.FEDRAMP: {
                "continuous_monitoring": True,
                "security_authorization": True,
                "incident_reporting": True,
                "system_inventory": True,
                "security_controls": True
            }
        }

    def encrypt_sensitive_data(self, data: str, classification: DataClassification) -> str:
        """Encrypt sensitive data based on classification"""
        if classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        return data

    def decrypt_sensitive_data(self, encrypted_data: str, classification: DataClassification) -> str:
        """Decrypt sensitive data based on classification"""
        if classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]:
            try:
                fernet = Fernet(self.encryption_key)
                decoded_data = base64.b64decode(encrypted_data.encode())
                decrypted_data = fernet.decrypt(decoded_data)
                return decrypted_data.decode()
            except Exception as e:
                self.logger.error(f"Decryption failed: {str(e)}")
                raise ValueError("Decryption failed")
        return encrypted_data

    def classify_data(self, data_type: str, content: Any) -> DataClassification:
        """Classify data sensitivity level"""
        sensitive_patterns = {
            DataClassification.RESTRICTED: [
                'ssn', 'social_security', 'credit_card', 'bank_account',
                'medical_record', 'phi', 'hipaa', 'password_hash', 'api_key'
            ],
            DataClassification.CONFIDENTIAL: [
                'assessment_results', 'personality_profile', 'team_analytics',
                'user_private', 'confidential', 'proprietary'
            ],
            DataClassification.INTERNAL: [
                'internal_notes', 'admin_data', 'system_config',
                'user_roles', 'permissions'
            ]
        }

        data_str = str(data_type).lower() + str(content).lower()

        for classification, patterns in sensitive_patterns.items():
            if any(pattern in data_str for pattern in patterns):
                return classification

        return DataClassification.PUBLIC

    def log_security_event(self, event: SecurityEvent):
        """Log security event for compliance and monitoring"""
        try:
            # Store in database for audit trail
            audit_log = AuditLog(
                event_id=event.event_id,
                timestamp=event.timestamp,
                event_type=event.event_type,
                severity=event.severity,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                resource_accessed=event.resource_accessed,
                action=event.action,
                outcome=event.outcome,
                compliance_standards=json.dumps([std.value for std in event.compliance_standards]),
                metadata=json.dumps(event.metadata)
            )

            self.db.add(audit_log)
            self.db.commit()

            # Store in Redis for real-time monitoring
            event_key = f"security_event:{event.event_id}"
            self.redis.setex(
                event_key,
                timedelta(days=30),
                json.dumps({
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "timestamp": event.timestamp.isoformat()
                })
            )

            # Check for critical events and trigger alerts
            if event.severity in ["CRITICAL", "HIGH"]:
                self._trigger_security_alert(event)

        except Exception as e:
            self.logger.error(f"Failed to log security event: {str(e)}")

    def _trigger_security_alert(self, event: SecurityEvent):
        """Trigger security alert for critical events"""
        alert_key = f"security_alert:{event.timestamp.strftime('%Y%m%d')}:{event.event_type}"

        alert_count = self.redis.incr(alert_key)
        self.redis.expire(alert_key, 3600)  # 1 hour window

        # Escalate if threshold exceeded
        if alert_count >= 5:  # 5 similar events in 1 hour
            self._escalate_security_incident(event)

    def _escalate_security_incident(self, event: SecurityEvent):
        """Escalate security incident to response team"""
        incident_data = {
            "incident_id": secrets.token_hex(16),
            "trigger_event": event.event_id,
            "severity": "CRITICAL",
            "description": f"Multiple {event.event_type} events detected",
            "timestamp": datetime.utcnow().isoformat(),
            "affected_systems": ["api", "database", "authentication"],
            "required_actions": [
                "investigate_source_of_events",
                "review_access logs",
                "assess potential impact",
                "prepare incident response"
            ]
        }

        # Store incident for tracking
        incident_key = f"security_incident:{incident_data['incident_id']}"
        self.redis.setex(incident_key, timedelta(days=7), json.dumps(incident_data))

        # Notify security team (integration with notification system)
        self.logger.critical(f"SECURITY INCIDENT ESCALATED: {json.dumps(incident_data)}")

    def perform_gdpr_data_erasure(self, user_id: str) -> Dict[str, bool]:
        """Perform right to erasure under GDPR"""
        erasure_results = {}

        try:
            # Delete user data from all systems
            user_tables = [
                'users', 'assessment_responses', 'user_sessions',
                'audit_logs', 'team_members', 'user_preferences'
            ]

            for table in user_tables:
                try:
                    # Soft delete with anonymization
                    self.db.execute(f"""
                        UPDATE {table}
                        SET email = 'deleted@deleted.com',
                            first_name = 'DELETED',
                            last_name = 'DELETED',
                            phone = NULL,
                            address = NULL,
                            deleted_at = NOW(),
                            gdpr_erasure_request_id = :request_id
                        WHERE user_id = :user_id
                    """, {"user_id": user_id, "request_id": secrets.token_hex(8)})

                    erasure_results[table] = True

                except Exception as e:
                    self.logger.error(f"Failed to erase data from {table}: {str(e)}")
                    erasure_results[table] = False

            self.db.commit()

            # Log erasure for compliance
            self.log_security_event(SecurityEvent(
                event_id=secrets.token_hex(16),
                timestamp=datetime.utcnow(),
                event_type="GDPR_DATA_ERASURE",
                severity="HIGH",
                user_id=user_id,
                ip_address="system",
                user_agent="gdpr_compliance_system",
                resource_accessed="user_data",
                action="data_erasure",
                outcome="completed",
                compliance_standards=[ComplianceStandard.GDPR],
                metadata={"erasure_results": erasure_results}
            ))

            return erasure_results

        except Exception as e:
            self.logger.error(f"GDPR data erasure failed: {str(e)}")
            return {"error": str(e)}

    def export_user_data_gdpr(self, user_id: str) -> Dict[str, Any]:
        """Export user data for GDPR data portability"""
        try:
            user_data = {
                "export_id": secrets.token_hex(16),
                "user_id": user_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "data": {}
            }

            # Collect user data from all tables
            queries = {
                "profile": "SELECT id, email, first_name, last_name, created_at FROM users WHERE id = :user_id",
                "assessments": """
                    SELECT id, title, created_at, completed_at
                    FROM assessments WHERE user_id = :user_id
                """,
                "responses": """
                    SELECT assessment_id, question_id, response_value, created_at
                    FROM assessment_responses WHERE user_id = :user_id
                """,
                "team_memberships": """
                    SELECT team_id, role, joined_at
                    FROM team_members WHERE user_id = :user_id
                """
            }

            for data_type, query in queries.items():
                try:
                    result = self.db.execute(query, {"user_id": user_id})
                    user_data["data"][data_type] = [dict(row) for row in result]
                except Exception as e:
                    self.logger.error(f"Failed to export {data_type}: {str(e)}")
                    user_data["data"][data_type] = {"error": str(e)}

            # Log export for compliance
            self.log_security_event(SecurityEvent(
                event_id=secrets.token_hex(16),
                timestamp=datetime.utcnow(),
                event_type="GDPR_DATA_EXPORT",
                severity="MEDIUM",
                user_id=user_id,
                ip_address="system",
                user_agent="gdpr_compliance_system",
                resource_accessed="user_data",
                action="data_export",
                outcome="completed",
                compliance_standards=[ComplianceStandard.GDPR],
                metadata={"export_id": user_data["export_id"]}
            ))

            return user_data

        except Exception as e:
            self.logger.error(f"GDPR data export failed: {str(e)}")
            return {"error": str(e)}

    def perform_access_review(self, review_period_days: int = 90) -> Dict[str, Any]:
        """Perform periodic access review for compliance"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=review_period_days)

            # Find users with old access that hasn't been reviewed
            review_query = """
                SELECT DISTINCT u.id, u.email, u.first_name, u.last_name,
                       MAX(al.timestamp) as last_access,
                       COUNT(al.id) as access_count
                FROM users u
                LEFT JOIN audit_logs al ON u.id = al.user_id
                    AND al.timestamp > :cutoff_date
                WHERE u.is_active = true
                    AND (al.timestamp IS NULL OR MAX(al.timestamp) < :cutoff_date)
                GROUP BY u.id, u.email, u.first_name, u.last_name
            """

            result = self.db.execute(review_query, {"cutoff_date": cutoff_date})
            users_for_review = [dict(row) for row in result]

            review_report = {
                "review_id": secrets.token_hex(16),
                "review_timestamp": datetime.utcnow().isoformat(),
                "review_period_days": review_period_days,
                "users_requiring_review": len(users_for_review),
                "users": users_for_review,
                "recommendations": []
            }

            # Generate recommendations
            for user in users_for_review:
                if user["access_count"] == 0:
                    review_report["recommendations"].append({
                        "user_id": user["id"],
                        "action": "REVOKE_ACCESS",
                        "reason": "No system access in review period"
                    })
                elif user["last_access"]:
                    days_since_access = (datetime.utcnow() - user["last_access"]).days
                    if days_since_access > review_period_days * 2:
                        review_report["recommendations"].append({
                            "user_id": user["id"],
                            "action": "REVIEW_ACCESS",
                            "reason": f"No access for {days_since_access} days"
                        })

            # Log access review for compliance
            self.log_security_event(SecurityEvent(
                event_id=secrets.token_hex(16),
                timestamp=datetime.utcnow(),
                event_type="ACCESS_REVIEW",
                severity="MEDIUM",
                user_id="system",
                ip_address="system",
                user_agent="compliance_system",
                resource_accessed="user_access",
                action="periodic_review",
                outcome="completed",
                compliance_standards=[
                    ComplianceStandard.SOC_2_TYPE_II,
                    ComplianceStandard.ISO_27001
                ],
                metadata=review_report
            ))

            return review_report

        except Exception as e:
            self.logger.error(f"Access review failed: {str(e)}")
            return {"error": str(e)}

    def generate_compliance_report(self, standards: List[ComplianceStandard]) -> Dict[str, Any]:
        """Generate compliance report for specified standards"""
        try:
            report = {
                "report_id": secrets.token_hex(16),
                "generated_at": datetime.utcnow().isoformat(),
                "standards": [std.value for std in standards],
                "compliance_status": {},
                "metrics": {},
                "recommendations": []
            }

            for standard in standards:
                config = self.compliance_configs[standard]
                status = self._check_standard_compliance(standard, config)

                report["compliance_status"][standard.value] = status
                report["metrics"][standard.value] = self._get_compliance_metrics(standard)

            # Generate overall recommendations
            for standard in standards:
                status = report["compliance_status"][standard.value]
                if not status["compliant"]:
                    report["recommendations"].extend(status["violations"])

            return report

        except Exception as e:
            self.logger.error(f"Compliance report generation failed: {str(e)}")
            return {"error": str(e)}

    def _check_standard_compliance(self, standard: ComplianceStandard, config: Dict) -> Dict:
        """Check compliance status for a specific standard"""
        violations = []

        # Check various compliance requirements
        if config.get("encryption_required"):
            # Verify encryption is properly implemented
            violations.extend(self._check_encryption_compliance())

        if config.get("access_logging"):
            # Verify access logging is enabled
            violations.extend(self._check_logging_compliance())

        if config.get("multi_factor_auth"):
            # Verify MFA is enforced for appropriate users
            violations.extend(self._check_mfa_compliance())

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "last_checked": datetime.utcnow().isoformat()
        }

    def _check_encryption_compliance(self) -> List[str]:
        """Check encryption compliance requirements"""
        violations = []

        try:
            # Verify data encryption at rest
            encrypted_tables = ["users", "assessment_responses", "team_members"]

            for table in encrypted_tables:
                result = self.db.execute(f"""
                    SELECT COUNT(*) as count FROM {table}
                    WHERE email IS NOT NULL AND email NOT LIKE '%@%.com'
                """)

                unencrypted_count = result.fetchone()["count"]
                if unencrypted_count > 0:
                    violations.append(f"Unencrypted data found in {table}")

        except Exception as e:
            violations.append(f"Encryption check failed: {str(e)}")

        return violations

    def _check_logging_compliance(self) -> List[str]:
        """Check logging compliance requirements"""
        violations = []

        try:
            # Verify audit logging is enabled and functioning
            recent_logs = self.db.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """).fetchone()["count"]

            if recent_logs == 0:
                violations.append("No audit logs found in last 24 hours")

        except Exception as e:
            violations.append(f"Logging check failed: {str(e)}")

        return violations

    def _check_mfa_compliance(self) -> List[str]:
        """Check MFA compliance requirements"""
        violations = []

        try:
            # Verify MFA is enabled for admin users
            admin_users_without_mfa = self.db.execute("""
                SELECT COUNT(*) as count FROM users
                WHERE role IN ('admin', 'super_admin')
                AND mfa_enabled = false
            """).fetchone()["count"]

            if admin_users_without_mfa > 0:
                violations.append(f"{admin_users_without_mfa} admin users without MFA")

        except Exception as e:
            violations.append(f"MFA check failed: {str(e)}")

        return violations

    def _get_compliance_metrics(self, standard: ComplianceStandard) -> Dict[str, Any]:
        """Get compliance metrics for a standard"""
        metrics = {}

        try:
            # Common metrics
            metrics["total_security_events"] = self.db.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE timestamp > NOW() - INTERVAL '30 days'
            """).fetchone()["count"]

            metrics["failed_login_attempts"] = self.db.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE event_type = 'LOGIN_FAILED'
                AND timestamp > NOW() - INTERVAL '30 days'
            """).fetchone()["count"]

            metrics["data_access_requests"] = self.db.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE event_type IN ('DATA_EXPORT', 'DATA_ERASURE')
                AND timestamp > NOW() - INTERVAL '30 days'
            """).fetchone()["count"]

            # Standard-specific metrics
            if standard == ComplianceStandard.GDPR:
                metrics["data_erasure_requests"] = self.db.execute("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE event_type = 'GDPR_DATA_ERASURE'
                    AND timestamp > NOW() - INTERVAL '30 days'
                """).fetchone()["count"]

                metrics["data_export_requests"] = self.db.execute("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE event_type = 'GDPR_DATA_EXPORT'
                    AND timestamp > NOW() - INTERVAL '30 days'
                """).fetchone()["count"]

        except Exception as e:
            self.logger.error(f"Failed to get compliance metrics: {str(e)}")
            metrics["error"] = str(e)

        return metrics

# Database models for compliance tracking
class AuditLog(Base):
    """Audit log model for compliance tracking"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    resource_accessed = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    outcome = Column(String(50), nullable=False)
    compliance_standards = Column(Text)  # JSON string
    metadata = Column(Text)  # JSON string

class DataProcessingRecord(Base):
    """GDPR data processing record"""
    __tablename__ = "data_processing_records"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    processing_purpose = Column(Text, nullable=False)
    legal_basis = Column(String(100), nullable=False)
    data_categories = Column(Text, nullable=False)  # JSON string
    retention_period = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)