#!/usr/bin/env python3
"""
PsychSync Archive Restoration Script

This script restores data from S3/Glacier archives back to the database
or exports it for review.

Usage:
    python scripts/restore_from_archive.py assessment_responses 2023-01-01 2023-12-31
    python scripts/restore_from_archive.py assessment_responses 2023-01-01 2023-12-31 --to-db
    python scripts/restore_from_archive.py analytics 2023-06-01 2023-06-30 --output-file /tmp/restore.csv

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
from typing import List, Dict, Optional, Tuple
import uuid
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import boto3
from botocore.exceptions import ClientError
import pandas as pd
import pyarrow.parquet as pq
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('archive_restoration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ArchiveRestorer:
    """Handle restoration of archived data"""

    def __init__(self, db_engine=None):
        if db_engine:
            self.engine = db_engine
            self.Session = sessionmaker(bind=db_engine)
        else:
            logger.warning("No database connection provided. Export-only mode.")
            self.engine = None
            self.Session = None

        self.s3_client = boto3.client('s3')
        self.archive_bucket = os.getenv('ARCHIVE_BUCKET', 'psychsync-data-archive')
        self.frozen_bucket = os.getenv('FROZEN_BUCKET', 'psychsync-frozen-archive')

    async def find_archives(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Find relevant archives from catalog or S3"""

        if self.engine:
            # Query from archive catalog if database available
            return await self._find_from_catalog(data_type, start_date, end_date)
        else:
            # Scan S3 bucket
            return await self._find_from_s3(data_type, start_date, end_date)

    async def _find_from_catalog(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Find archives from database catalog"""

        async with self.Session() as session:
            result = await session.execute(
                text("""
                    SELECT
                        archive_id,
                        data_type,
                        archive_location,
                        date_range_start,
                        date_range_end,
                        record_count,
                        file_size_bytes,
                        is_anonymized
                    FROM archive_catalog
                    WHERE data_type = :data_type
                      AND date_range_start <= :end_date
                      AND date_range_end >= :start_date
                    ORDER BY date_range_start ASC
                """),
                {
                    "data_type": data_type,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            archives = [dict(row) for row in result.fetchall()]
            logger.info(f"Found {len(archives)} archive(s) in catalog")
            return archives

    async def _find_from_s3(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Find archives by scanning S3 bucket"""

        archives = []

        try:
            # List objects in bucket with prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            prefix = f"{data_type}/"

            for page in paginator.paginate(Bucket=self.archive_bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    key = obj['Key']

                    # Try to parse date from key structure
                    # Expected: data_type/YYYY/MM/DD/data.parquet
                    try:
                        parts = key.split('/')
                        if len(parts) >= 4:
                            year = int(parts[1])
                            month = int(parts[2])
                            day = int(parts[3])

                            file_date = datetime(year, month, day)

                            if start_date <= file_date <= end_date:
                                archives.append({
                                    'archive_id': key.split('/')[-2],
                                    'archive_location': f"s3://{self.archive_bucket}/{key}",
                                    'date_range_start': file_date,
                                    'date_range_end': file_date,
                                    'record_count': None,
                                    'file_size_bytes': obj['Size']
                                })
                    except (ValueError, IndexError):
                        continue

            logger.info(f"Found {len(archives)} archive(s) in S3")
            return archives

        except ClientError as e:
            logger.error(f"Failed to list S3 objects: {e}")
            return []

    async def download_archive(self, archive_location: str, local_path: Path) -> bool:
        """Download archive from S3 to local file"""

        try:
            # Parse S3 location
            # Expected format: s3://bucket-name/path/to/file.parquet
            if archive_location.startswith('s3://'):
                location = archive_location[5:]  # Remove 's3://'
                bucket, key = location.split('/', 1)
            else:
                logger.error(f"Invalid S3 location format: {archive_location}")
                return False

            # Download file
            logger.info(f"Downloading from S3: {bucket}/{key}")
            self.s3_client.download_file(bucket, key, str(local_path))

            file_size = local_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✓ Downloaded {file_size:.2f} MB to {local_path}")

            return True

        except ClientError as e:
            logger.error(f"Failed to download archive: {e}")
            return False

    async def load_archive(self, archive_path: Path) -> pd.DataFrame:
        """Load archived data from Parquet file"""

        try:
            logger.info(f"Loading archive: {archive_path}")

            # Read Parquet file
            df = pd.read_parquet(archive_path)

            logger.info(f"✓ Loaded {len(df)} records, {len(df.columns)} columns")

            # Show sample data
            logger.info(f"\nSample data (first 3 rows):")
            logger.info(df.head(3).to_string())

            return df

        except Exception as e:
            logger.error(f"Failed to load archive: {e}")
            return pd.DataFrame()

    async def export_to_file(
        self,
        df: pd.DataFrame,
        output_file: Path,
        format: str = 'csv'
    ) -> bool:
        """Export data to file"""

        try:
            logger.info(f"Exporting to {format.upper()}: {output_file}")

            if format == 'csv':
                df.to_csv(output_file, index=False)
            elif format == 'json':
                df.to_json(output_file, orient='records', indent=2)
            elif format == 'parquet':
                df.to_parquet(output_file, index=False)
            else:
                logger.error(f"Unsupported format: {format}")
                return False

            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✓ Exported {len(df)} records to {output_file} ({file_size:.2f} MB)")

            return True

        except Exception as e:
            logger.error(f"Failed to export: {e}")
            return False

    async def restore_to_database(
        self,
        df: pd.DataFrame,
        data_type: str
    ) -> int:
        """Restore data to database"""

        if not self.engine:
            logger.error("No database connection available. Cannot restore to database.")
            return 0

        try:
            logger.info(f"Restoring {len(df)} records to database...")

            # Map data_type to table name
            table_mapping = {
                'assessment_responses': 'assessment_responses',
                'individual_responses': 'responses',
                'analytics': 'analytics',
                'audit_logs': 'audit_logs',
                'report_views': 'report_views',
                'wellness_assessments': 'wellness_assessments'
            }

            table_name = table_mapping.get(data_type)
            if not table_name:
                logger.error(f"Unknown data type: {data_type}")
                return 0

            async with self.Session() as session:
                # Check for existing records
                if 'id' in df.columns:
                    existing_ids = await session.execute(
                        text(f"SELECT id FROM {table_name} WHERE id = ANY(:ids)"),
                        {"ids": df['id'].tolist()}
                    )
                    existing = set(row[0] for row in existing_ids.fetchall())

                    # Filter out existing records
                    df_new = df[~df['id'].isin(existing)]
                    logger.info(f"  Skipping {len(existing)} existing records")
                else:
                    df_new = df

                if len(df_new) == 0:
                    logger.info("  No new records to insert")
                    return 0

                # Insert records
                # Convert DataFrame to list of dicts
                records = df_new.to_dict('records')

                # Use SQLAlchemy core for bulk insert
                from sqlalchemy import table, column
                from sqlalchemy.dialects.postgresql import insert as pg_insert

                # Create table object
                table_obj = table(table_name)

                # Insert records
                await session.execute(
                    table_obj.insert(),
                    records
                )

                await session.commit()

                logger.info(f"✓ Restored {len(df_new)} records to {table_name}")
                return len(df_new)

        except Exception as e:
            logger.error(f"Failed to restore to database: {e}")
            return 0

    async def restore(
        self,
        data_type: str,
        date_range: Tuple[datetime, datetime],
        target_db: bool = False,
        output_file: Optional[Path] = None,
        output_format: str = 'csv'
    ):
        """Main restoration process"""

        start_date, end_date = date_range

        logger.info("="*60)
        logger.info("ARCHIVE RESTORATION")
        logger.info("="*60)
        logger.info(f"Data Type: {data_type}")
        logger.info(f"Date Range: {start_date.date()} to {end_date.date()}")
        logger.info(f"Target Database: {target_db}")
        logger.info(f"Output File: {output_file}")
        logger.info("="*60)

        # Step 1: Find archives
        logger.info("\n[Step 1] Finding archives...")
        archives = await self.find_archives(data_type, start_date, end_date)

        if not archives:
            logger.warning(f"No archives found for {data_type} in date range")
            return

        logger.info(f"Found {len(archives)} archive(s):")
        for arch in archives:
            logger.info(f"  - {arch['archive_id']}: {arch['archive_location']}")

        # Step 2: Download and load each archive
        all_data = []

        for i, archive in enumerate(archives, 1):
            logger.info(f"\n[Step 2.{i}] Processing archive: {archive['archive_id']}")

            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                # Download
                if not await self.download_archive(archive['archive_location'], tmp_path):
                    continue

                # Load
                df = await self.load_archive(tmp_path)
                if not df.empty:
                    all_data.append(df)

            finally:
                # Cleanup temp file
                tmp_path.unlink(missing_ok=True)

        if not all_data:
            logger.error("No data loaded from any archive")
            return

        # Combine all data
        logger.info(f"\n[Step 3] Combining data from {len(all_data)} archive(s)...")
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"✓ Combined {len(combined_df)} total records")

        # Remove duplicates (if any)
        if 'id' in combined_df.columns:
            before = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['id'], keep='first')
            after = len(combined_df)
            if before > after:
                logger.info(f"  Removed {before - after} duplicate records")

        # Step 4: Export or restore
        if output_file:
            logger.info(f"\n[Step 4] Exporting to file: {output_file}")
            await self.export_to_file(combined_df, output_file, output_format)

        if target_db:
            logger.info(f"\n[Step 4] Restoring to database...")
            count = await self.restore_to_database(combined_df, data_type)
            logger.info(f"✓ Restored {count} records to database")

        logger.info("\n" + "="*60)
        logger.info("RESTORATION COMPLETE")
        logger.info("="*60)


async def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='PsychSync Archive Restoration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export archive to file for review
  python scripts/restore_from_archive.py assessment_responses 2023-01-01 2023-12-31

  # Restore directly to database
  python scripts/restore_from_archive.py assessment_responses 2023-01-01 2023-12-31 --to-db

  # Export to specific file
  python scripts/restore_from_archive.py analytics 2023-06-01 2023-06-30 --output-file /tmp/restore.json --format json

  # Export without database connection
  python scripts/restore_from_archive.py assessment_responses 2023-01-01 2023-12-31 --output-file restore.csv
        """
    )

    parser.add_argument(
        'data_type',
        help='Type of data to restore (e.g., assessment_responses, analytics, audit_logs)'
    )

    parser.add_argument(
        'start_date',
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        'end_date',
        help='End date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--to-db',
        action='store_true',
        help='Restore to database (requires DB connection)'
    )

    parser.add_argument(
        '--output-file',
        type=Path,
        help='Export to file instead of database'
    )

    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'parquet'],
        default='csv',
        help='Output format (default: csv)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Download and show data without restoring'
    )

    args = parser.parse_args()

    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        logger.error("Use YYYY-MM-DD format")
        sys.exit(1)

    # Get database connection (optional)
    db_engine = None
    if args.to_db:
        try:
            from app.core.database import engine as app_engine
            db_engine = app_engine
            logger.info("Database connection established")
        except ImportError:
            logger.warning("Could not import database engine. Running without DB connection.")
        except Exception as e:
            logger.warning(f"Could not connect to database: {e}")

    # Create restorer
    restorer = ArchiveRestorer(db_engine)

    # Set default output file if none specified and not restoring to DB
    if not args.to_db and not args.output_file:
        args.output_file = Path(f"restore_{args.data_type}_{args.start_date}_{args.end_date}.{args.format}")

    # Run restoration
    try:
        await restorer.restore(
            data_type=args.data_type,
            date_range=(start_date, end_date),
            target_db=args.to_db and not args.dry_run,
            output_file=args.output_file,
            output_format=args.format
        )

        if args.dry_run:
            logger.info("\n[DRY RUN] No data was restored or written to disk")

    except Exception as e:
        logger.error(f"Restoration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
