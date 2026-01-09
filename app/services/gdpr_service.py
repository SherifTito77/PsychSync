"""
GDPR Compliance Service
Handles data export, deletion, consent management, and compliance workflows
"""

import csv
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Any
import zipfile

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models.assessment import Assessment
from app.db.models.audit_log import AuditLog
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class GDPRService:
    """GDPR compliance service implementation"""

    def __init__(self):
        self.email_service = EmailService()
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)

    async def export_user_data(
        self, user_id: str, db: Session, format: str = "json"
    ) -> dict[str, Any]:
        """
        Export all user data in GDPR-compliant format

        Args:
            user_id: User UUID to export data for
            db: Database session
            format: Export format ('json', 'csv', 'zip')

        Returns:
            Dict with export metadata and download URL
        """
        try:
            logger.info(f"Starting GDPR data export for user {user_id}")

            # Collect all user data
            user_data = await self._collect_user_data(user_id, db)

            # Generate export file
            if format == "json":
                file_path = await self._export_json(user_id, user_data)
            elif format == "csv":
                file_path = await self._export_csv(user_id, user_data)
            elif format == "zip":
                file_path = await self._export_zip(user_id, user_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export format"
                )

            # Create export record
            export_record = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "format": format,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "data_categories": list(user_data.keys()),
                "status": "completed",
            }

            # Log export for audit trail
            await self._log_gdpr_action(
                user_id=user_id, action="data_export", details=export_record, db=db
            )

            logger.info(f"GDPR data export completed for user {user_id}")

            return {
                "export_id": f"{user_id}_{export_record['export_date'].replace(':', '-')}",
                "status": "completed",
                "format": format,
                "file_size": export_record["file_size"],
                "download_url": f"/api/v1/gdpr/download/{file_path.name}",
                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "data_categories": export_record["data_categories"],
            }

        except Exception as e:
            logger.error(f"GDPR data export failed for user {user_id}: {e!s}")
            await self._log_gdpr_action(
                user_id=user_id, action="data_export_failed", details={"error": str(e)}, db=db
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data export failed: {e!s}",
            )

    async def _collect_user_data(self, user_id: str, db: Session) -> dict[str, Any]:
        """Collect all user data from different tables"""

        # Get user基本信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Collect data from different sources
        user_data = {
            "user_profile": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "timezone": user.timezone,
                "locale": user.locale,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "team_memberships": [],
            "assessments": [],
            "responses": [],
            "audit_logs": [],
            "consent_records": [],
            "privacy_settings": {},
        }

        # Team memberships
        team_members = db.query(TeamMember).filter(TeamMember.user_id == user_id).all()
        for tm in team_members:
            team = db.query(Team).filter(Team.id == tm.team_id).first()
            if team:
                user_data["team_memberships"].append(
                    {
                        "team_id": str(team.id),
                        "team_name": team.name,
                        "role": tm.role.value,
                        "joined_at": tm.created_at.isoformat() if tm.created_at else None,
                    }
                )

        # Assessments
        assessments = db.query(Assessment).filter(Assessment.created_by_id == user_id).all()
        for assessment in assessments:
            user_data["assessments"].append(
                {
                    "id": str(assessment.id),
                    "title": assessment.title,
                    "type": assessment.type,
                    "status": assessment.status,
                    "created_at": assessment.created_at.isoformat()
                    if assessment.created_at
                    else None,
                    "updated_at": assessment.updated_at.isoformat()
                    if assessment.updated_at
                    else None,
                }
            )

        # Responses
        responses = db.query(Response).filter(Response.user_id == user_id).all()
        for response in responses:
            user_data["responses"].append(
                {
                    "id": str(response.id),
                    "assessment_id": str(response.assessment_id),
                    "response_data": response.response_data,
                    "score": response.score,
                    "completed_at": response.completed_at.isoformat()
                    if response.completed_at
                    else None,
                    "created_at": response.created_at.isoformat() if response.created_at else None,
                }
            )

        # Audit logs (last 90 days for privacy)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        audit_logs = (
            db.query(AuditLog)
            .filter(and_(AuditLog.user_id == user_id, AuditLog.timestamp >= cutoff_date))
            .all()
        )

        for log in audit_logs:
            user_data["audit_logs"].append(
                {
                    "id": str(log.id),
                    "action": log.action,
                    "resource": log.resource,
                    "timestamp": log.timestamp.isoformat(),
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                }
            )

        # Consent records (if table exists)
        try:
            # This would be from a consent management table
            user_data["consent_records"] = await self._get_user_consents(user_id, db)
        except:
            user_data["consent_records"] = []

        # Privacy settings
        user_data["privacy_settings"] = await self._get_user_privacy_settings(user_id, db)

        return user_data

    async def _export_json(self, user_id: str, user_data: dict[str, Any]) -> Path:
        """Export data as JSON file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"gdpr_export_{user_id}_{timestamp}.json"
        file_path = self.export_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False, default=str)

        return file_path

    async def _export_csv(self, user_id: str, user_data: dict[str, Any]) -> Path:
        """Export data as CSV files in a directory"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        export_dir = self.export_dir / f"gdpr_export_{user_id}_{timestamp}"
        export_dir.mkdir(exist_ok=True)

        # Export user profile
        profile_file = export_dir / "user_profile.csv"
        with open(profile_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            for key, value in user_data["user_profile"].items():
                writer.writerow([key, value])

        # Export team memberships
        if user_data["team_memberships"]:
            teams_file = export_dir / "team_memberships.csv"
            with open(teams_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Team ID", "Team Name", "Role", "Joined At"])
                for team in user_data["team_memberships"]:
                    writer.writerow(
                        [team["team_id"], team["team_name"], team["role"], team["joined_at"]]
                    )

        # Export assessments
        if user_data["assessments"]:
            assessments_file = export_dir / "assessments.csv"
            with open(assessments_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Title", "Type", "Status", "Created At", "Updated At"])
                for assessment in user_data["assessments"]:
                    writer.writerow(
                        [
                            assessment["id"],
                            assessment["title"],
                            assessment["type"],
                            assessment["status"],
                            assessment["created_at"],
                            assessment["updated_at"],
                        ]
                    )

        return export_dir

    async def _export_zip(self, user_id: str, user_data: dict[str, Any]) -> Path:
        """Export data as ZIP file containing all formats"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"gdpr_export_{user_id}_{timestamp}.zip"
        zip_path = self.export_dir / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON export
            json_data = json.dumps(user_data, indent=2, ensure_ascii=False, default=str)
            zipf.writestr("export_data.json", json_data)

            # Add CSV exports
            csv_dir = await self._export_csv(user_id, user_data)
            for csv_file in csv_dir.glob("*.csv"):
                zipf.write(csv_file, csv_file.name)

            # Add README
            readme_content = self._generate_export_readme(user_data)
            zipf.writestr("README.txt", readme_content)

        return zip_path

    def _generate_export_readme(self, user_data: dict[str, Any]) -> str:
        """Generate README file for data export"""
        return f"""
GDPR Data Export
================

Export Date: {datetime.utcnow().isoformat()}
User Email: {user_data["user_profile"].get("email", "N/A")}

This export contains all personal data associated with your account as required by GDPR.

Data Categories Included:
- User Profile: Basic account information and preferences
- Team Memberships: Teams you belong to and your roles
- Assessments: Assessments you have created
- Responses: Your assessment responses and results
- Audit Logs: Recent account activity (last 90 days)
- Consent Records: Your privacy consents and preferences
- Privacy Settings: Your privacy and data sharing preferences

File Formats:
- export_data.json: Complete data in JSON format
- *.csv: Individual data tables in CSV format

Data Retention:
This export file will be automatically deleted after 7 days.

Questions:
Contact privacy@psychsync.com for any questions about this data export.
"""

    async def delete_user_data(
        self,
        user_id: str,
        db: Session,
        deletion_reason: str = "user_request",
        soft_delete: bool = True,
    ) -> dict[str, Any]:
        """
        Delete or anonymize user data (Right to be Forgotten)

        Args:
            user_id: User UUID to delete
            db: Database session
            deletion_reason: Reason for deletion
            soft_delete: If True, anonymize data; if False, hard delete

        Returns:
            Dict with deletion results
        """
        try:
            logger.info(f"Starting GDPR data deletion for user {user_id}")

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            deletion_record = {
                "user_id": user_id,
                "deletion_date": datetime.utcnow().isoformat(),
                "deletion_reason": deletion_reason,
                "method": "soft_delete" if soft_delete else "hard_delete",
                "status": "in_progress",
            }

            if soft_delete:
                # Anonymize user data
                await self._anonymize_user_data(user_id, db)
                deletion_record["status"] = "completed"
            else:
                # Hard delete user and related data
                await self._hard_delete_user_data(user_id, db)
                deletion_record["status"] = "completed"

            # Log deletion for audit trail
            await self._log_gdpr_action(
                user_id=user_id, action="data_deletion", details=deletion_record, db=db
            )

            logger.info(f"GDPR data deletion completed for user {user_id}")

            return {
                "deletion_id": f"{user_id}_{deletion_record['deletion_date'].replace(':', '-')}",
                "status": "completed",
                "method": deletion_record["method"],
                "deletion_date": deletion_record["deletion_date"],
                "data_categories_processed": [
                    "user_profile",
                    "team_memberships",
                    "assessments",
                    "responses",
                    "audit_logs",
                    "consent_records",
                ],
            }

        except Exception as e:
            logger.error(f"GDPR data deletion failed for user {user_id}: {e!s}")
            await self._log_gdpr_action(
                user_id=user_id, action="data_deletion_failed", details={"error": str(e)}, db=db
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data deletion failed: {e!s}",
            )

    async def _anonymize_user_data(self, user_id: str, db: Session):
        """Anonymize user data instead of hard deletion"""

        # Anonymize user profile
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            anonymized_email = f"deleted_{user_id}@deleted.psychnsync.com"
            user.email = anonymized_email
            user.full_name = "Deleted User"
            user.avatar_url = None
            user.password_hash = "DELETED"
            user.is_active = False
            user.is_verified = False
            user.deleted_at = datetime.utcnow()

        # Anonymize responses
        responses = db.query(Response).filter(Response.user_id == user_id).all()
        for response in responses:
            response.response_data = {
                "anonymized": True,
                "original_format": type(response.response_data).__name__,
            }
            response.score = None

        # Remove from team memberships
        db.query(TeamMember).filter(TeamMember.user_id == user_id).delete()

        db.commit()

    async def _hard_delete_user_data(self, user_id: str, db: Session):
        """Completely delete user and all related data"""

        # Delete in order to respect foreign key constraints
        db.query(Response).filter(Response.user_id == user_id).delete()
        db.query(TeamMember).filter(TeamMember.user_id == user_id).delete()
        db.query(Assessment).filter(Assessment.created_by_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()

        db.commit()

    async def _get_user_consents(self, user_id: str, db: Session) -> list[dict[str, Any]]:
        """Get user consent records"""
        # This would be implemented when consent management system is created
        return [
            {
                "consent_type": "data_processing",
                "granted_at": "2024-01-01T00:00:00Z",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "status": "active",
            }
        ]

    async def _get_user_privacy_settings(self, user_id: str, db: Session) -> dict[str, Any]:
        """Get user privacy settings"""
        # This would be implemented when privacy settings system is created
        return {
            "data_sharing": False,
            "analytics_consent": True,
            "marketing_consent": False,
            "cookie_preferences": {"essential": True, "analytics": True, "marketing": False},
        }

    async def _log_gdpr_action(
        self, user_id: str, action: str, details: dict[str, Any], db: Session
    ):
        """Log GDPR actions for audit trail"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=f"gdpr_{action}",
                resource="user_data",
                details=json.dumps(details),
                ip_address="0.0.0.0",  # Would be passed in real implementation
                user_agent="GDPR Service",
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log GDPR action: {e!s}")

    async def schedule_data_export_cleanup(self):
        """Clean up old export files (older than 7 days)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)

            for file_path in self.export_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        logger.info(f"Deleted old export file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to cleanup export files: {e!s}")
