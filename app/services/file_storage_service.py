"""
File Storage Service

Abstracts file storage between local filesystem (development) and S3 (production).
App Runner has an ephemeral filesystem — files vanish on redeploy.
"""

import logging
import os
from io import BytesIO

logger = logging.getLogger(__name__)


class FileStorageService:
    """Stores files locally in dev, S3 in production."""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.use_s3 = self.environment == "production" and os.getenv("AWS_S3_BUCKET")
        self.bucket = os.getenv("AWS_S3_BUCKET", "psychsync-uploads")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.local_dir = os.getenv("UPLOAD_DIR", "uploads")
        self._s3_client = None

    @property
    def s3_client(self):
        if self._s3_client is None and self.use_s3:
            import boto3

            self._s3_client = boto3.client("s3", region_name=self.region)
        return self._s3_client

    async def save(
        self, data: bytes, path: str, content_type: str = "application/octet-stream"
    ) -> str:
        """Save file and return its path/URL."""
        if self.use_s3:
            return self._save_s3(data, path, content_type)
        return self._save_local(data, path)

    def _save_s3(self, data: bytes, path: str, content_type: str) -> str:
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=BytesIO(data),
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{path}"
        logger.info(f"File saved to S3: {path}")
        return url

    def _save_local(self, data: bytes, path: str) -> str:
        full_path = os.path.join(self.local_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        logger.info(f"File saved locally: {full_path}")
        return full_path

    async def read(self, path: str) -> bytes:
        """Read file from storage."""
        if self.use_s3:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=path)
            return response["Body"].read()
        full_path = os.path.join(self.local_dir, path)
        with open(full_path, "rb") as f:
            return f.read()

    async def delete(self, path: str) -> None:
        """Delete file from storage."""
        if self.use_s3:
            self.s3_client.delete_object(Bucket=self.bucket, Key=path)
        else:
            full_path = os.path.join(self.local_dir, path)
            if os.path.exists(full_path):
                os.remove(full_path)

    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        if self.use_s3:
            try:
                self.s3_client.head_object(Bucket=self.bucket, Key=path)
                return True
            except self.s3_client.exceptions.ClientError:
                return False
        return os.path.exists(os.path.join(self.local_dir, path))


file_storage = FileStorageService()
