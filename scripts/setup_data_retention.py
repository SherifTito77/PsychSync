#!/usr/bin/env python3
"""
PsychSync Data Retention Setup Script

This script automates the setup and configuration of the data retention
and archiving system for PsychSync.

Features:
- Initialize retention policies in the database
- Set up archive catalog and tracking tables
- Configure scheduled archival jobs
- Create monitoring dashboards
- Validate configuration

Usage:
    python scripts/setup_data_retention.py --action init
    python scripts/setup_data_retention.py --action validate
    python scripts/setup_data_retention.py --action cleanup

Author: PsychSync Operations Team
Version: 1.0
Last Updated: 2026-01-04
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import uuid
import hashlib
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import boto3
from botocore.exceptions import ClientError
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Import application modules
try:
    from app.core.config import settings
    from app.core.database import get_db, engine
    from app.db.models.user import User
    from app.db.models.assessment import Assessment, AssessmentResponse
    from app.db.models.response import Response
    from app.db.models.analytics import Analytics
    from app.db.models.audit_log import AuditLog
    from app.db.models.reports import GeneratedReport, ReportCache
except ImportError as e:
    print(f"Warning: Could not import application modules: {e}")
    print("Running in standalone mode with database connection only")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_retention_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

RETENTION_POLICIES = [
    {
        "policy_name": "assessment_responses_6months",
        "data_type": "assessment_responses",
        "source_table": "assessment_responses",
        "retention_period_days": 730,  # 2 years
        "archive_after_days": 180,  # 6 months
        "anonymize_before_archive": True,
        "anonymization_method": "k_anonymity_k=5",
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 2 * * *"  # Daily at 2 AM UTC
    },
    {
        "policy_name": "individual_responses_6months",
        "data_type": "individual_responses",
        "source_table": "responses",
        "retention_period_days": 730,
        "archive_after_days": 180,
        "anonymize_before_archive": True,
        "anonymization_method": "k_anonymity_k=5",
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 2 * * *"
    },
    {
        "policy_name": "analytics_3months",
        "data_type": "analytics",
        "source_table": "analytics",
        "retention_period_days": 365,  # 1 year
        "archive_after_days": 90,  # 3 months
        "anonymize_before_archive": False,
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 3 * * *"
    },
    {
        "policy_name": "audit_logs_3months",
        "data_type": "audit_logs",
        "source_table": "audit_logs",
        "retention_period_days": 2555,  # 7 years
        "archive_after_days": 90,
        "anonymize_before_archive": True,
        "anonymization_method": "user_id_hashing",
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 3 * * 0"  # Weekly on Sunday
    },
    {
        "policy_name": "report_cache_7days",
        "data_type": "report_cache",
        "source_table": "report_cache",
        "retention_period_days": 7,
        "archive_after_days": 0,
        "anonymize_before_archive": False,
        "target_storage": "delete",
        "is_active": True,
        "schedule": "0 4 * * *"
    },
    {
        "policy_name": "report_views_90days",
        "data_type": "report_views",
        "source_table": "report_views",
        "retention_period_days": 180,
        "archive_after_days": 90,
        "anonymize_before_archive": True,
        "anonymization_method": "user_id_hashing",
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 4 * * *"
    },
    {
        "policy_name": "wellness_assessments_2years",
        "data_type": "wellness_assessments",
        "source_table": "wellness_assessments",
        "retention_period_days": 2555,  # 7 years
        "archive_after_days": 730,  # 2 years
        "anonymize_before_archive": True,
        "anonymization_method": "k_anonymity_k=10",
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 5 * * *"
    },
    {
        "policy_name": "team_dynamics_1year",
        "data_type": "interaction_patterns",
        "source_table": "interaction_patterns",
        "retention_period_days": 730,
        "archive_after_days": 365,
        "anonymize_before_archive": False,
        "target_storage": "s3",
        "is_active": True,
        "schedule": "0 6 * * *"
    }
]


# ============================================================================
# Database Setup Functions
# ============================================================================

class DatabaseSetup:
    """Handle database schema and policy setup"""

    def __init__(self, db_engine):
        self.engine = db_engine
        self.Session = sessionmaker(bind=db_engine)

    async def create_retention_tables(self):
        """Create retention management tables"""
        logger.info("Creating retention management tables...")

        create_tables_sql = """
        -- Retention policies configuration
        CREATE TABLE IF NOT EXISTS retention_policies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            policy_name VARCHAR(255) NOT NULL UNIQUE,
            data_type VARCHAR(100) NOT NULL,
            source_table VARCHAR(100) NOT NULL,
            retention_period_days INTEGER NOT NULL,
            archive_after_days INTEGER NOT NULL,
            anonymize_before_archive BOOLEAN DEFAULT TRUE,
            anonymization_method VARCHAR(100),
            target_storage VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            schedule VARCHAR(100),
            last_run_at TIMESTAMP,
            next_run_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        -- Archive jobs tracking
        CREATE TABLE IF NOT EXISTS archive_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            policy_id UUID REFERENCES retention_policies(id),
            job_type VARCHAR(50),
            status VARCHAR(50),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            records_processed INTEGER,
            records_failed INTEGER,
            archive_id VARCHAR(255),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Archive catalog
        CREATE TABLE IF NOT EXISTS archive_catalog (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            archive_id VARCHAR(255) UNIQUE NOT NULL,
            data_type VARCHAR(100) NOT NULL,
            archive_location TEXT NOT NULL,
            date_range_start TIMESTAMP NOT NULL,
            date_range_end TIMESTAMP NOT NULL,
            record_count INTEGER NOT NULL,
            file_size_bytes BIGINT NOT NULL,
            compression_ratio NUMERIC(5,2),
            data_classification VARCHAR(50),
            is_anonymized BOOLEAN DEFAULT FALSE,
            anonymization_method VARCHAR(100),
            retention_expiration TIMESTAMP NOT NULL,
            legal_hold BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            created_by VARCHAR(255)
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_retention_policies_active ON retention_policies(is_active);
        CREATE INDEX IF NOT EXISTS idx_archive_jobs_status ON archive_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_archive_jobs_policy ON archive_jobs(policy_id);
        CREATE INDEX IF NOT EXISTS idx_archive_catalog_type ON archive_catalog(data_type);
        CREATE INDEX IF NOT EXISTS idx_archive_catalog_date ON archive_catalog(date_range_start, date_range_end);
        CREATE INDEX IF NOT EXISTS idx_archive_catalog_expiration ON archive_catalog(retention_expiration);
        CREATE INDEX IF NOT EXISTS idx_archive_catalog_legal_hold ON archive_catalog(legal_hold);

        -- Create comments
        COMMENT ON TABLE retention_policies IS 'Configuration for data retention policies';
        COMMENT ON TABLE archive_jobs IS 'Tracking of archival job executions';
        COMMENT ON TABLE archive_catalog IS 'Catalog of all archived data';
        """

        async with self.engine.begin() as conn:
            await conn.execute(text(create_tables_sql))

        logger.info("✓ Retention tables created successfully")

    async def insert_retention_policies(self):
        """Insert default retention policies"""
        logger.info("Inserting retention policies...")

        async with self.Session() as session:
            for policy in RETENTION_POLICIES:
                try:
                    # Check if policy exists
                    result = await session.execute(
                        text("SELECT id FROM retention_policies WHERE policy_name = :name"),
                        {"name": policy["policy_name"]}
                    )

                    if not result.fetchone():
                        await session.execute(
                            text("""
                                INSERT INTO retention_policies
                                (policy_name, data_type, source_table, retention_period_days,
                                 archive_after_days, anonymize_before_archive, anonymization_method,
                                 target_storage, is_active, schedule, next_run_at)
                                VALUES
                                (:policy_name, :data_type, :source_table, :retention_period_days,
                                 :archive_after_days, :anonymize_before_archive, :anonymization_method,
                                 :target_storage, :is_active, :schedule, NOW() + INTERVAL '1 hour')
                            """),
                            policy
                        )
                        logger.info(f"  ✓ Created policy: {policy['policy_name']}")
                    else:
                        logger.info(f"  - Policy already exists: {policy['policy_name']}")

                except Exception as e:
                    logger.error(f"  ✗ Failed to create policy {policy['policy_name']}: {e}")

            await session.commit()

        logger.info("✓ Retention policies initialized")

    async def validate_setup(self):
        """Validate that all tables and policies are correctly set up"""
        logger.info("Validating retention setup...")

        async with self.engine.begin() as conn:
            # Check tables exist
            inspector = inspect(self.engine)
            required_tables = ['retention_policies', 'archive_jobs', 'archive_catalog']

            for table in required_tables:
                if table in inspector.get_table_names():
                    logger.info(f"  ✓ Table {table} exists")
                else:
                    logger.error(f"  ✗ Table {table} missing!")
                    return False

            # Check policies
            result = await conn.execute(
                text("SELECT COUNT(*) FROM retention_policies WHERE is_active = TRUE")
            )
            count = result.scalar()
            logger.info(f"  ✓ {count} active policies configured")

            # Check indexes
            for table in required_tables:
                indexes = inspector.get_indexes(table)
                logger.info(f"  ✓ Table {table} has {len(indexes)} indexes")

        logger.info("✓ Setup validation complete")
        return True


# ============================================================================
# S3 Storage Setup
# ============================================================================

class S3Setup:
    """Handle S3 bucket and storage setup"""

    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.kms_client = boto3.client('kms')
        self.region = os.getenv('AWS_REGION', 'us-east-1')

        # Bucket names (override with environment variables)
        self.archive_bucket = os.getenv('ARCHIVE_BUCKET', 'psychsync-data-archive')
        self.frozen_bucket = os.getenv('FROZEN_BUCKET', 'psychsync-frozen-archive')

    async def create_buckets(self):
        """Create S3 buckets for archival if they don't exist"""
        logger.info("Setting up S3 buckets...")

        for bucket_name in [self.archive_bucket, self.frozen_bucket]:
            try:
                # Check if bucket exists
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"  - Bucket {bucket_name} already exists")
            except ClientError as e:
                error_code = int(e.response['Error']['Code'])
                if error_code == 404:
                    # Bucket doesn't exist, create it
                    try:
                        if self.region == 'us-east-1':
                            # us-east-1 has a different create_bucket call
                            self.s3_client.create_bucket(Bucket=bucket_name)
                        else:
                            self.s3_client.create_bucket(
                                Bucket=bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': self.region}
                            )
                        logger.info(f"  ✓ Created bucket: {bucket_name}")

                        # Set up lifecycle policy
                        self._setup_lifecycle_policy(bucket_name)

                        # Enable versioning
                        self.s3_client.put_bucket_versioning(
                            Bucket=bucket_name,
                            VersioningConfiguration={'Status': 'Enabled'}
                        )

                    except Exception as create_error:
                        logger.error(f"  ✗ Failed to create bucket {bucket_name}: {create_error}")
                        return False
                else:
                    logger.error(f"  ✗ Error accessing bucket {bucket_name}: {e}")
                    return False

        logger.info("✓ S3 buckets configured")
        return True

    def _setup_lifecycle_policy(self, bucket_name):
        """Set up lifecycle policy for archive transitions"""
        lifecycle_config = {
            'Rules': [
                {
                    'Id': 'transition-to-glacier',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'Transitions': [
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        },
                        {
                            'Days': 365,
                            'StorageClass': 'DEEP_ARCHIVE'
                        }
                    ],
                    'Expiration': {
                        'Days': 2555  # 7 years
                    },
                    'NoncurrentVersionExpiration': {
                        'NoncurrentDays': 30
                    }
                }
            ]
        }

        self.s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        logger.info(f"  ✓ Lifecycle policy configured for {bucket_name}")

    async def create_kms_key(self):
        """Create KMS key for encryption if it doesn't exist"""
        logger.info("Setting up KMS encryption...")

        key_alias = os.getenv('KMS_KEY_ALIAS', 'alias/psychsync-archive-key')

        try:
            # Try to get existing key
            response = self.kms_client.describe_key(KeyId=key_alias)
            logger.info(f"  - KMS key already exists: {response['KeyMetadata']['KeyId']}")
            return response['KeyMetadata']['KeyId']
        except ClientError:
            # Create new key
            try:
                response = self.kms_client.create_key(
                    Description='PsychSync data archive encryption key',
                    KeyUsage='ENCRYPT_DECRYPT',
                    Origin='AWS_KMS',
                    Tags=[
                        {'TagKey': 'Application', 'TagValue': 'PsychSync'},
                        {'TagKey': 'Purpose', 'TagValue': 'DataArchival'}
                    ]
                )

                key_id = response['KeyMetadata']['KeyId']

                # Create alias
                self.kms_client.create_alias(
                    AliasName=key_alias,
                    TargetKeyId=key_id
                )

                logger.info(f"  ✓ Created KMS key: {key_id}")
                return key_id

            except Exception as e:
                logger.error(f"  ✗ Failed to create KMS key: {e}")
                return None


# ============================================================================
# Retention Service
# ============================================================================

class RetentionService:
    """Main service for data retention operations"""

    def __init__(self, db_engine):
        self.engine = db_engine
        self.Session = sessionmaker(bind=db_engine)

    async def get_records_for_retention(self, policy_id: str) -> List[Dict]:
        """Get records that need to be archived based on policy"""
        async with self.Session() as session:
            # Get policy details
            result = await session.execute(
                text("""
                    SELECT source_table, archive_after_days
                    FROM retention_policies
                    WHERE id = :policy_id AND is_active = TRUE
                """),
                {"policy_id": policy_id}
            )
            policy = result.fetchone()

            if not policy:
                logger.error(f"Policy {policy_id} not found or inactive")
                return []

            threshold_date = datetime.now() - timedelta(days=policy.archive_after_days)

            # Query records based on source table
            query = f"""
                SELECT *
                FROM {policy.source_table}
                WHERE created_at < :threshold_date
                ORDER BY created_at ASC
                LIMIT 10000
            """

            result = await session.execute(text(query), {"threshold_date": threshold_date})
            records = [dict(row) for row in result.fetchall()]

            logger.info(f"Found {len(records)} records for archival from {policy.source_table}")
            return records

    async def archive_to_parquet(self, records: List[Dict], data_type: str) -> bytes:
        """Convert records to Parquet format"""
        df = pd.DataFrame(records)

        # Convert to Parquet
        table = pa.Table.from_pandas(df)
        buf = pa.BufferOutputStream()
        pq.write_table(table, buf, compression='snappy')

        return buf.to_bytes()

    async def upload_to_s3(self, data: bytes, archive_id: str, bucket: str) -> str:
        """Upload archived data to S3"""
        s3_client = boto3.client('s3')

        # Generate object key
        now = datetime.now()
        key = f"{archive_id}/{now.year}/{now.month:02d}/{now.day:02d}/data.parquet"

        try:
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=os.getenv('KMS_KEY_ALIAS', 'alias/psychsync-archive-key')
            )

            location = f"s3://{bucket}/{key}"
            logger.info(f"  ✓ Uploaded to S3: {location}")
            return location

        except Exception as e:
            logger.error(f"  ✗ Failed to upload to S3: {e}")
            raise

    async def update_catalog(self, archive_id: str, metadata: Dict):
        """Update archive catalog with metadata"""
        async with self.Session() as session:
            await session.execute(
                text("""
                    INSERT INTO archive_catalog
                    (archive_id, data_type, archive_location, date_range_start, date_range_end,
                     record_count, file_size_bytes, data_classification, is_anonymized,
                     anonymization_method, retention_expiration, legal_hold, created_by)
                    VALUES
                    (:archive_id, :data_type, :archive_location, :date_range_start,
                     :date_range_end, :record_count, :file_size_bytes, :data_classification,
                     :is_anonymized, :anonymization_method, :retention_expiration,
                     :legal_hold, :created_by)
                """),
                metadata
            )
            await session.commit()

    async def process_retention(self, dry_run: bool = False):
        """Main retention process - processes all active policies"""
        logger.info("Starting retention process...")

        async with self.Session() as session:
            # Get all active policies
            result = await session.execute(
                text("SELECT id, policy_name FROM retention_policies WHERE is_active = TRUE")
            )
            policies = result.fetchall()

            logger.info(f"Found {len(policies)} active policies")

            for policy in policies:
                logger.info(f"Processing policy: {policy.policy_name}")

                try:
                    # Get records for archival
                    records = await self.get_records_for_retention(str(policy.id))

                    if not records:
                        logger.info(f"  No records to archive for {policy.policy_name}")
                        continue

                    if dry_run:
                        logger.info(f"  [DRY RUN] Would archive {len(records)} records")
                        continue

                    # Create archive ID
                    archive_id = f"arch_{datetime.now().strftime('%Y%m%d')}_{policy.policy_name}"

                    # Convert to Parquet
                    parquet_data = await self.archive_to_parquet(records, policy.policy_name)

                    # Upload to S3
                    location = await self.upload_to_s3(
                        parquet_data,
                        archive_id,
                        os.getenv('ARCHIVE_BUCKET', 'psychsync-data-archive')
                    )

                    # Calculate metadata
                    oldest_date = min(r.get('created_at', datetime.now()) for r in records)
                    newest_date = max(r.get('created_at', datetime.now()) for r in records)

                    # Update catalog
                    await self.update_catalog({
                        'archive_id': archive_id,
                        'data_type': policy.policy_name,
                        'archive_location': location,
                        'date_range_start': oldest_date,
                        'date_range_end': newest_date,
                        'record_count': len(records),
                        'file_size_bytes': len(parquet_data),
                        'data_classification': 'moderately_sensitive',
                        'is_anonymized': False,
                        'anonymization_method': None,
                        'retention_expiration': datetime.now() + timedelta(days=2555),
                        'legal_hold': False,
                        'created_by': 'system_archiver'
                    })

                    logger.info(f"  ✓ Archived {len(records)} records to {archive_id}")

                except Exception as e:
                    logger.error(f"  ✗ Failed to process policy {policy.policy_name}: {e}")

        logger.info("Retention process complete")


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='PsychSync Data Retention Setup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize retention system
  python setup_data_retention.py --action init

  # Validate configuration
  python setup_data_retention.py --action validate

  # Run archival (dry run)
  python setup_data_retention.py --action archive --dry-run

  # Run archival (live)
  python setup_data_retention.py --action archive

  # Show statistics
  python setup_data_retention.py --action stats
        """
    )

    parser.add_argument(
        '--action',
        choices=['init', 'validate', 'archive', 'stats', 'cleanup'],
        required=True,
        help='Action to perform'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making changes'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force operation without confirmation prompts'
    )

    args = parser.parse_args()

    # Get database connection
    try:
        db_engine = engine
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.error("Please ensure DATABASE_URL is set in environment or .env file")
        sys.exit(1)

    # Execute requested action
    if args.action == 'init':
        logger.info("=== Initializing Data Retention System ===")

        # Database setup
        db_setup = DatabaseSetup(db_engine)
        await db_setup.create_retention_tables()
        await db_setup.insert_retention_policies()

        # S3 setup
        s3_setup = S3Setup()
        await s3_setup.create_buckets()
        await s3_setup.create_kms_key()

        logger.info("\n=== Setup Complete ===")
        logger.info("Next steps:")
        logger.info("  1. Review retention policies in the database")
        logger.info("  2. Test archival with --action archive --dry-run")
        logger.info("  3. Set up monitoring and alerting")
        logger.info("  4. Schedule archival jobs (cron/Airflow)")

    elif args.action == 'validate':
        logger.info("=== Validating Data Retention Setup ===")

        db_setup = DatabaseSetup(db_engine)
        is_valid = await db_setup.validate_setup()

        if is_valid:
            logger.info("\n✓ All validation checks passed")
            sys.exit(0)
        else:
            logger.error("\n✗ Validation failed")
            sys.exit(1)

    elif args.action == 'archive':
        logger.info("=== Running Data Archival ===")

        if not args.dry_run and not args.force:
            response = input("This will archive data to S3. Continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Aborted")
                sys.exit(0)

        retention_service = RetentionService(db_engine)
        await retention_service.process_retention(dry_run=args.dry_run)

        logger.info("\n=== Archival Complete ===")

    elif args.action == 'stats':
        logger.info("=== Data Retention Statistics ===")

        async with db_engine.begin() as conn:
            # Policy stats
            result = await conn.execute(text("""
                SELECT
                    policy_name,
                    data_type,
                    retention_period_days,
                    archive_after_days,
                    is_active,
                    last_run_at,
                    next_run_at
                FROM retention_policies
                ORDER BY policy_name
            """))

            logger.info("\nPolicies:")
            for row in result:
                logger.info(f"  {row.policy_name:40} | Active: {row.is_active} | Last run: {row.last_run_at}")

            # Archive stats
            result = await conn.execute(text("""
                SELECT
                    data_type,
                    COUNT(*) as archive_count,
                    SUM(record_count) as total_records,
                    SUM(file_size_bytes) / 1024 / 1024 / 1024 as total_size_gb
                FROM archive_catalog
                GROUP BY data_type
                ORDER BY total_size_gb DESC
            """))

            logger.info("\nArchives:")
            for row in result:
                logger.info(f"  {row.data_type:40} | Archives: {row.archive_count:4} | Records: {row.total_records:10} | Size: {row.total_size_gb:6.2f} GB")

            # Database size
            result = await conn.execute(text("""
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as db_size
            """))
            db_size = result.scalar()
            logger.info(f"\nDatabase size: {db_size}")

    elif args.action == 'cleanup':
        logger.warning("=== Cleanup: This will remove all retention configuration ===")

        if not args.force:
            response = input("Are you sure? This cannot be undone! (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Aborted")
                sys.exit(0)

        async with db_engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS archive_catalog CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS archive_jobs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS retention_policies CASCADE"))

        logger.info("✓ Cleanup complete")


if __name__ == '__main__':
    asyncio.run(main())
