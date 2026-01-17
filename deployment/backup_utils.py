"""
Backup utilities for PsychSync production environment
Handles database backups, S3 uploads, and retention policies
"""

import os
import subprocess
import gzip
import boto3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups and S3 storage"""

    def __init__(self):
        self.s3_client = None
        self._initialize_s3()

    def _initialize_s3(self):
        """Initialize S3 client if credentials are available"""
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('BACKUP_S3_REGION', 'us-west-2')
            )
            logger.info("S3 client initialized")
        else:
            logger.warning("AWS credentials not found, S3 uploads disabled")

    def create_database_backup(self, database_url: str, output_path: str) -> bool:
        """Create a PostgreSQL database backup"""
        try:
            # Parse database URL
            # Expected format: postgresql://user:password@host:port/database
            if not database_url.startswith('postgresql://'):
                raise ValueError("Invalid database URL format")

            # Remove postgresql:// prefix for pg_dump
            pg_url = database_url.replace('postgresql://', '')

            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                f'postgresql://{pg_url}',
                '--no-password',
                '--format=custom',
                '--compress=9',
                '--verbose',
                f'--file={output_path}'
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            if '@' in pg_url:
                # Extract password from URL
                password_part = pg_url.split('@')[0].split(':')[-1]
                env['PGPASSWORD'] = password_part

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.info(f"Database backup created: {output_path}")
                return True
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Backup creation timed out")
            return False
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return False

    def compress_backup(self, input_path: str) -> str:
        """Compress backup file with gzip"""
        compressed_path = f"{input_path}.gz"

        try:
            with open(input_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # Remove uncompressed file
            os.remove(input_path)
            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"Compression failed: {str(e)}")
            raise

    def upload_to_s3(self, file_path: str, bucket: str, key: str) -> bool:
        """Upload file to S3 bucket"""
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False

        try:
            self.s3_client.upload_file(
                file_path,
                bucket,
                key,
                ExtraArgs={
                    'StorageClass': 'STANDARD_IA',
                    'ServerSideEncryption': 'AES256'
                }
            )

            # Verify upload
            self.s3_client.head_object(Bucket=bucket, Key=key)
            logger.info(f"File uploaded to S3: s3://{bucket}/{key}")
            return True

        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return False

    def cleanup_old_backups(self, backup_dir: str, retention_days: int) -> None:
        """Remove old local backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            for filename in os.listdir(backup_dir):
                if filename.startswith('psychsync_db_') and filename.endswith('.sql.gz'):
                    file_path = os.path.join(backup_dir, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"Deleted old backup: {filename}")

        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")

    def cleanup_s3_backups(self, bucket: str, retention_days: int) -> None:
        """Remove old S3 backup files"""
        if not self.s3_client:
            return

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_str = cutoff_date.strftime('%Y%m%d')

            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix='database/')

            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Extract date from filename
                        if 'psychsync_db_' in key:
                            try:
                                date_part = key.split('psychsync_db_')[1].split('_')[0]
                                if len(date_part) == 8 and date_part.isdigit():
                                    if int(date_part) < int(cutoff_str):
                                        self.s3_client.delete_object(Bucket=bucket, Key=key)
                                        logger.info(f"Deleted old S3 backup: {key}")
                            except (IndexError, ValueError):
                                continue

        except ClientError as e:
            logger.error(f"S3 cleanup failed: {str(e)}")

    def get_backup_size(self, file_path: str) -> str:
        """Get human-readable file size"""
        try:
            size_bytes = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"
        except OSError:
            return "Unknown"


def main():
    """Main backup function for testing"""
    import argparse
    from urllib.parse import urlparse

    parser = argparse.ArgumentParser(description='PsychSync Database Backup')
    parser.add_argument('--database-url', required=True, help='Database connection URL')
    parser.add_argument('--backup-dir', default='/backups', help='Backup directory')
    parser.add_argument('--s3-bucket', help='S3 bucket for uploads')
    args = parser.parse_args()

    # Initialize backup manager
    backup_manager = BackupManager()

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'psychsync_db_{timestamp}.sql'
    backup_path = os.path.join(args.backup_dir, filename)

    # Create backup directory
    os.makedirs(args.backup_dir, exist_ok=True)

    try:
        # Create backup
        if backup_manager.create_database_backup(args.database_url, backup_path):
            # Compress backup
            compressed_path = backup_manager.compress_backup(backup_path)

            # Upload to S3 if specified
            if args.s3_bucket:
                s3_key = f'database/{os.path.basename(compressed_path)}'
                backup_manager.upload_to_s3(compressed_path, args.s3_bucket, s3_key)

            # Get file size
            size = backup_manager.get_backup_size(compressed_path)
            print(f"Backup completed successfully: {size}")

        else:
            print("Backup failed")
            return 1

    except Exception as e:
        logger.error(f"Backup process failed: {str(e)}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
