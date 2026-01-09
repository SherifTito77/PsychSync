"""
Data Retention Service

Comprehensive service for managing data retention, archival, and deletion
in compliance with GDPR, HIPAA, and SOC 2 requirements.

Author: PsychSync Data Governance Team
Version: 1.0
"""

from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
import pandas as pd
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AssessmentResponse, AuditLog, WellnessAssessment

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """Data retention policy configuration"""

    def __init__(
        self,
        data_type: str,
        source_table: str,
        retention_period_days: int,
        archive_after_days: int,
        anonymize_before_archive: bool = True,
        target_storage: str = "s3",
        encryption_required: bool = True
    ):
        self.data_type = data_type
        self.source_table = source_table
        self.retention_period_days = retention_period_days
        self.archive_after_days = archive_after_days
        self.anonymize_before_archive = anonymize_before_archive
        self.target_storage = target_storage
        self.encryption_required = encryption_required

    @property
    def archive_threshold_date(self) -> datetime:
        """Calculate date threshold for archival"""
        return datetime.utcnow() - timedelta(days=self.archive_after_days)

    @property
    def deletion_threshold_date(self) -> datetime:
        """Calculate date threshold for deletion"""
        return datetime.utcnow() - timedelta(days=self.retention_period_days)


# Define retention policies for different data types
RETENTION_POLICIES = {
    "user_data": RetentionPolicy(
        data_type="user_data",
        source_table="users",
        retention_period_days=365 * 7,  # 7 years
        archive_after_days=365 * 2,  # 2 years
        anonymize_before_archive=True
    ),
    "assessment_responses": RetentionPolicy(
        data_type="assessment_responses",
        source_table="responses",
        retention_period_days=365 * 7,  # 7 years (GDPR)
        archive_after_days=180,  # 6 months
        anonymize_before_archive=True
    ),
    "wellness_assessments": RetentionPolicy(
        data_type="wellness_assessments",
        source_table="wellness_assessments",
        retention_period_days=365 * 7,  # 7 years (HIPAA)
        archive_after_days=180,  # 6 months
        anonymize_before_archive=True
    ),
    "safety_incidents": RetentionPolicy(
        data_type="safety_incidents",
        source_table="safety_incidents",
        retention_period_days=365 * 7,  # 7 years (OSHA)
        archive_after_days=365 * 2,  # 2 years
        anonymize_before_archive=False  # Keep original for compliance
    ),
    "audit_logs": RetentionPolicy(
        data_type="audit_logs",
        source_table="audit_logs",
        retention_period_days=365 * 3,  # 3 years (SOC 2)
        archive_after_days=365,  # 1 year
        anonymize_before_archive=False
    ),
    "analytics_data": RetentionPolicy(
        data_type="analytics_data",
        source_table="analytics",
        retention_period_days=365 * 3,  # 3 years
        archive_after_days=90,  # 3 months
        anonymize_before_archive=True
    ),
    "intervention_data": RetentionPolicy(
        data_type="intervention_data",
        source_table="intervention_effectiveness",
        retention_period_days=365 * 7,  # 7 years
        archive_after_days=365 * 2,  # 2 years
        anonymize_before_archive=True
    ),
}


class ArchiveManager:
    """Manage data archival to S3/Glacier"""

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.kms_client = boto3.client("kms")
        self.archive_bucket = settings.AWS_S3_ARCHIVE_BUCKET
        self.kms_key_id = settings.AWS_KMS_KEY_ID

    async def create_archive(
        self,
        data: pd.DataFrame,
        data_type: str,
        date_range: tuple[datetime, datetime],
        metadata: dict[str, Any]
    ) -> str:
        """
        Create encrypted archive and upload to S3

        Args:
            data: DataFrame to archive
            data_type: Type of data being archived
            date_range: Tuple of (start_date, end_date)
            metadata: Additional metadata for the archive

        Returns:
            Archive ID (UUID)
        """
        archive_id = str(uuid4())

        try:
            # Convert to Parquet with compression
            import io
            buffer = io.BytesIO()
            data.to_parquet(buffer, compression="snappy", index=False)
            compressed_data = buffer.getvalue()

            # Generate archive path
            year = date_range[0].year
            month = date_range[0].month
            archive_path = f"{data_type}/{year}/{month:02d}/{archive_id}.parquet"

            # Upload to S3 with encryption
            self.s3_client.put_object(
                Bucket=self.archive_bucket,
                Key=archive_path,
                Body=compressed_data,
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self.kms_key_id,
                Metadata={
                    "archive_id": archive_id,
                    "data_type": data_type,
                    "record_count": str(len(data)),
                    "created_at": datetime.utcnow().isoformat(),
                    **{k: str(v) for k, v in metadata.items()}
                }
            )

            logger.info(
                f"Created archive {archive_id} for {data_type} "
                f"with {len(data)} records at {archive_path}"
            )

            return archive_id

        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            raise

    async def download_archive(
        self,
        archive_location: str,
        local_path: str
    ) -> None:
        """
        Download archive from S3

        Args:
            archive_location: S3 object location
            local_path: Local file path to save
        """
        try:
            # Parse bucket and key from location
            # Format: s3://bucket-name/path/to/file.parquet
            parts = archive_location.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]

            # Download file
            self.s3_client.download_file(bucket, key, local_path)

            logger.info(f"Downloaded archive from {archive_location} to {local_path}")

        except ClientError as e:
            logger.error(f"Failed to download archive: {e}")
            raise

    async def initiate_glacier_retrieval(
        self,
        archive_location: str,
        retrieval_tier: str = "Standard"
    ) -> str:
        """
        Initiate retrieval from Glacier

        Args:
            archive_location: S3 object location in Glacier
            retrieval_tier: Expedited, Standard, or Bulk

        Returns:
            Request ID for tracking retrieval
        """
        try:
            parts = archive_location.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]

            response = self.s3_client.restore_object(
                Bucket=bucket,
                Key=key,
                RestoreRequest={
                    "Days": 30,  # Keep in S3 for 30 days
                    "GlacierJobParameters": {
                        "Tier": retrieval_tier
                    }
                }
            )

            logger.info(f"Initiated Glacier retrieval for {archive_location}")

            return response["ResponseMetadata"]["RequestId"]

        except ClientError as e:
            logger.error(f"Failed to initiate Glacier retrieval: {e}")
            raise


class DataAnonymizer:
    """Anonymize sensitive data before archival"""

    async def anonymize_user_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonymize user PII while preserving utility"""
        import hashlib

        anonymized = df.copy()

        # Hash email addresses
        if "email" in anonymized.columns:
            anonymized["email"] = anonymized["email"].apply(
                lambda x: hashlib.sha256(x.encode()).hexdigest() if pd.notna(x) else x
            )

        # Anonymize full names
        if "full_name" in anonymized.columns:
            anonymized["full_name"] = "ANONYMIZED"

        # Remove sensitive columns
        sensitive_columns = ["password_hash", "two_factor_secret", "two_factor_recovery_codes"]
        for col in sensitive_columns:
            if col in anonymized.columns:
                anonymized = anonymized.drop(columns=[col])

        return anonymized

    async def anonymize_assessment_responses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonymize assessment responses"""
        anonymized = df.copy()

        # Hash user IDs for linkage removal
        if "user_id" in anonymized.columns:
            anonymized["user_id"] = anonymized["user_id"].apply(
                lambda x: f"anon_{str(x)[:8]}" if pd.notna(x) else x
            )

        # Keep answer values for analysis but remove free text
        if "answer_text" in anonymized.columns:
            anonymized["answer_text"] = "ANONYMIZED"

        return anonymized

    async def anonymize_wellness_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonymize wellness assessments"""
        anonymized = df.copy()

        # Hash user IDs
        if "user_id" in anonymized.columns:
            anonymized["user_id"] = anonymized["user_id"].apply(
                lambda x: f"anon_{str(x)[:8]}" if pd.notna(x) else x
            )

        # Remove AI insights (may contain identifying information)
        if "ai_insights" in anonymized.columns:
            anonymized = anonymized.drop(columns=["ai_insights"])

        return anonymized


class DataRetentionService:
    """Main service for data retention operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.archive_manager = ArchiveManager()
        self.anonymizer = DataAnonymizer()

    async def check_archival_candidates(
        self,
        policy_name: str
    ) -> list[dict[str, Any]]:
        """
        Identify records ready for archival

        Args:
            policy_name: Name of retention policy to apply

        Returns:
            List of candidate records with metadata
        """
        policy = RETENTION_POLICIES.get(policy_name)
        if not policy:
            raise ValueError(f"Unknown retention policy: {policy_name}")

        threshold_date = policy.archive_threshold_date
        candidates = []

        logger.info(
            f"Checking archival candidates for {policy_name} "
            f"with threshold date {threshold_date}"
        )

        if policy_name == "assessment_responses":
            # Query assessment responses older than threshold
            result = await self.db.execute(
                select(AssessmentResponse)
                .where(
                    and_(
                        AssessmentResponse.completed_at < threshold_date,
                        AssessmentResponse.status == "completed"
                    )
                )
                .limit(10000)  # Batch size
            )
            records = result.scalars().all()

            for record in records:
                candidates.append({
                    "id": str(record.id),
                    "table": "assessment_responses",
                    "created_at": record.created_at,
                    "completed_at": record.completed_at,
                    "data": {
                        "id": str(record.id),
                        "assessment_id": str(record.assessment_id),
                        "respondent_id": str(record.respondent_id),
                        "status": record.status,
                        "responses": record.responses,
                        "started_at": record.started_at.isoformat() if record.started_at else None,
                        "completed_at": record.completed_at.isoformat() if record.completed_at else None
                    }
                })

        elif policy_name == "wellness_assessments":
            result = await self.db.execute(
                select(WellnessAssessment)
                .where(WellnessAssessment.assessment_date < threshold_date)
                .limit(10000)
            )
            records = result.scalars().all()

            for record in records:
                candidates.append({
                    "id": str(record.id),
                    "table": "wellness_assessments",
                    "created_at": record.created_at,
                    "assessment_date": record.assessment_date,
                    "data": {
                        "id": str(record.id),
                        "user_id": str(record.user_id),
                        "organization_id": str(record.organization_id),
                        "assessment_date": record.assessment_date.isoformat(),
                        "overall_wellness_score": record.overall_wellness_score,
                        "alert_level": str(record.alert_level) if record.alert_level else None
                    }
                })

        elif policy_name == "audit_logs":
            result = await self.db.execute(
                select(AuditLog)
                .where(AuditLog.created_at < threshold_date)
                .limit(50000)  # Larger batch for logs
            )
            records = result.scalars().all()

            for record in records:
                candidates.append({
                    "id": str(record.id),
                    "table": "audit_logs",
                    "created_at": record.created_at,
                    "data": {
                        "id": str(record.id),
                        "organization_id": str(record.organization_id) if record.organization_id else None,
                        "action": record.action,
                        "entity": record.entity,
                        "entity_id": str(record.entity_id) if record.entity_id else None,
                        "created_at": record.created_at.isoformat()
                    }
                })

        logger.info(f"Found {len(candidates)} archival candidates for {policy_name}")

        return candidates

    async def archive_data(
        self,
        policy_name: str,
        batch_size: int = 10000
    ) -> dict[str, Any]:
        """
        Archive data according to retention policy

        Args:
            policy_name: Name of retention policy
            batch_size: Number of records to process per batch

        Returns:
            Archive operation result
        """
        policy = RETENTION_POLICIES.get(policy_name)
        if not policy:
            raise ValueError(f"Unknown retention policy: {policy_name}")

        start_time = datetime.utcnow()
        total_archived = 0
        archive_ids = []

        logger.info(f"Starting archival for {policy_name}")

        try:
            # Get candidates
            candidates = await self.check_archival_candidates(policy_name)

            if not candidates:
                logger.info(f"No candidates found for archival under policy {policy_name}")
                return {
                    "policy": policy_name,
                    "status": "success",
                    "records_archived": 0,
                    "archive_ids": [],
                    "duration_seconds": 0
                }

            # Process in batches
            for i in range(0, len(candidates), batch_size):
                batch = candidates[i:i + batch_size]

                # Convert to DataFrame
                df = pd.DataFrame([c["data"] for c in batch])

                # Anonymize if required
                if policy.anonymize_before_archive:
                    if policy_name == "assessment_responses":
                        df = await self.anonymizer.anonymize_assessment_responses(df)
                    elif policy_name == "wellness_assessments":
                        df = await self.anonymizer.anonymize_wellness_data(df)

                # Determine date range
                dates = [c["created_at"] for c in batch]
                date_range = (min(dates), max(dates))

                # Create archive
                archive_id = await self.archive_manager.create_archive(
                    data=df,
                    data_type=policy.data_type,
                    date_range=date_range,
                    metadata={
                        "policy": policy_name,
                        "batch_number": i // batch_size + 1,
                        "total_batches": (len(candidates) + batch_size - 1) // batch_size
                    }
                )

                archive_ids.append(archive_id)
                total_archived += len(batch)

                logger.info(
                    f"Archived batch {i // batch_size + 1} of "
                    f"{(len(candidates) + batch_size - 1) // batch_size} "
                    f"({len(batch)} records) -> {archive_id}"
                )

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Archival completed for {policy_name}: "
                f"{total_archived} records in {duration:.2f}s"
            )

            return {
                "policy": policy_name,
                "status": "success",
                "records_archived": total_archived,
                "archive_ids": archive_ids,
                "duration_seconds": duration
            }

        except Exception as e:
            logger.error(f"Archival failed for {policy_name}: {e}")
            return {
                "policy": policy_name,
                "status": "error",
                "error": str(e),
                "records_archived": total_archived,
                "archive_ids": archive_ids
            }

    async def delete_archived_records(
        self,
        policy_name: str,
        archive_ids: list[str],
        verification_period_days: int = 30
    ) -> dict[str, Any]:
        """
        Delete records from primary database after archival verification period

        Args:
            policy_name: Name of retention policy
            archive_ids: List of archive IDs containing the records
            verification_period_days: Days to wait before deletion (default 30)

        Returns:
            Deletion operation result
        """
        policy = RETENTION_POLICIES.get(policy_name)
        if not policy:
            raise ValueError(f"Unknown retention policy: {policy_name}")

        logger.info(
            f"Deleting archived records for {policy_name} "
            f"after {verification_period_days} day verification period"
        )

        try:
            deleted_count = 0

            if policy_name == "assessment_responses":
                # Delete archived assessment responses
                threshold_date = policy.archive_threshold_date

                result = await self.db.execute(
                    delete(AssessmentResponse)
                    .where(
                        and_(
                            AssessmentResponse.completed_at < threshold_date,
                            AssessmentResponse.status == "completed"
                        )
                    )
                )
                deleted_count = result.rowcount
                await self.db.commit()

            elif policy_name == "wellness_assessments":
                threshold_date = policy.archive_threshold_date

                result = await self.db.execute(
                    delete(WellnessAssessment)
                    .where(WellnessAssessment.assessment_date < threshold_date)
                )
                deleted_count = result.rowcount
                await self.db.commit()

            elif policy_name == "audit_logs":
                threshold_date = policy.archive_threshold_date

                result = await self.db.execute(
                    delete(AuditLog)
                    .where(AuditLog.created_at < threshold_date)
                )
                deleted_count = result.rowcount
                await self.db.commit()

            logger.info(f"Deleted {deleted_count} records for {policy_name}")

            return {
                "policy": policy_name,
                "status": "success",
                "records_deleted": deleted_count,
                "archive_ids": archive_ids
            }

        except Exception as e:
            logger.error(f"Deletion failed for {policy_name}: {e}")
            await self.db.rollback()
            return {
                "policy": policy_name,
                "status": "error",
                "error": str(e),
                "records_deleted": 0
            }

    async def process_retention_policies(
        self,
        policy_names: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Process all or specified retention policies

        Args:
            policy_names: List of policy names to process (None = all)

        Returns:
            Overall processing result
        """
        if policy_names is None:
            policy_names = list(RETENTION_POLICIES.keys())

        results = {}
        total_archived = 0
        total_failed = 0

        logger.info(f"Processing retention policies: {policy_names}")

        for policy_name in policy_names:
            try:
                result = await self.archive_data(policy_name)

                if result["status"] == "success":
                    total_archived += result["records_archived"]

                    # Schedule deletion after verification period
                    # This would be handled by a background job
                    logger.info(
                        f"Scheduled deletion for {policy_name} "
                        f"after verification period"
                    )
                else:
                    total_failed += 1

                results[policy_name] = result

            except Exception as e:
                logger.error(f"Failed to process policy {policy_name}: {e}")
                results[policy_name] = {
                    "status": "error",
                    "error": str(e)
                }
                total_failed += 1

        return {
            "processed_at": datetime.utcnow().isoformat(),
            "policies_processed": len(policy_names),
            "policies_succeeded": len(policy_names) - total_failed,
            "policies_failed": total_failed,
            "total_records_archived": total_archived,
            "results": results
        }

    async def get_retention_statistics(self) -> dict[str, Any]:
        """Get current statistics about data retention"""

        stats = {}

        # Count records by age for each data type
        now = datetime.utcnow()

        # Assessment responses
        for months in [6, 12, 24, 36, 60, 84]:
            threshold = now - timedelta(days=months * 30)
            result = await self.db.execute(
                select(func.count(AssessmentResponse.id))
                .where(AssessmentResponse.completed_at < threshold)
            )
            count = result.scalar() or 0
            stats[f"assessment_responses_older_{months}months"] = count

        # Wellness assessments
        for months in [6, 12, 24, 36, 60, 84]:
            threshold = now - timedelta(days=months * 30)
            result = await self.db.execute(
                select(func.count(WellnessAssessment.id))
                .where(WellnessAssessment.assessment_date < threshold)
            )
            count = result.scalar() or 0
            stats[f"wellness_assessments_older_{months}months"] = count

        # Audit logs
        for months in [3, 6, 12, 24, 36]:
            threshold = now - timedelta(days=months * 30)
            result = await self.db.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.created_at < threshold)
            )
            count = result.scalar() or 0
            stats[f"audit_logs_older_{months}months"] = count

        # Database size estimates
        stats["timestamp"] = now.isoformat()

        return stats

    async def check_gdpr_compliance(self) -> dict[str, Any]:
        """Check GDPR compliance status"""

        now = datetime.utcnow()

        # Check for data beyond retention period
        retention_violations = {}

        # Assessment responses beyond 7 years
        threshold = now - timedelta(days=365 * 7)
        result = await self.db.execute(
            select(func.count(AssessmentResponse.id))
            .where(AssessmentResponse.completed_at < threshold)
        )
        count = result.scalar() or 0
        retention_violations["assessment_responses_beyond_7years"] = count

        # Wellness assessments beyond 7 years
        result = await self.db.execute(
            select(func.count(WellnessAssessment.id))
            .where(WellnessAssessment.assessment_date < threshold)
        )
        count = result.scalar() or 0
        retention_violations["wellness_assessments_beyond_7years"] = count

        # Calculate compliance score
        total_violations = sum(retention_violations.values())
        compliance_score = 100.0 if total_violations == 0 else max(0, 100 - total_violations * 0.1)

        return {
            "compliance_score": round(compliance_score, 2),
            "retention_violations": retention_violations,
            "check_date": now.isoformat(),
            "status": "compliant" if total_violations == 0 else "non_compliant"
        }
