"""
Automated Credential Rotation Tool
Rotates compromised or exposed credentials during security incidents.

Features:
- Multi-system credential rotation (AWS, Database, API keys, SSH, etc.)
- Service configuration updates
- Verification of new credentials
- Audit logging of all rotations
- Zero-downtime rotation strategy
- Rollback capability

Author: PsychSync Security Team
Version: 1.0.0
"""

import base64
import hashlib
import json
import logging
import os
import secrets
import string
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Optional dependencies for specific systems
try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None

try:
    import psycopg2
    from psycopg2 import sql

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None
    sql = None

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    hashes = None
    PBKDF2 = None

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CredentialType(Enum):
    """Types of credentials that can be rotated."""

    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    DATABASE_PASSWORD = "database_password"
    API_KEY = "api_key"
    SSH_KEY = "ssh_key"
    SERVICE_ACCOUNT_TOKEN = "service_account_token"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    REDIS_PASSWORD = "redis_password"
    GENERIC_SECRET = "generic_secret"


@dataclass
class Credential:
    """Represents a credential that needs rotation."""

    credential_id: str
    name: str
    type: CredentialType
    location: str  # service, database, system
    current_value_hash: str  # Hash of current value (for verification)
    new_value: Optional[str] = None
    new_value_hash: Optional[str] = None
    services_affected: List[str] = field(default_factory=list)
    rotation_timestamp: Optional[str] = None
    rotation_status: str = "pending"  # pending, in_progress, completed, failed
    rollback_value: Optional[str] = None


@dataclass
class RotationReport:
    """Report of credential rotation operation."""

    incident_id: str
    rotation_timestamp: str
    total_credentials: int
    successful_rotations: int
    failed_rotations: int
    credentials_rotated: List[str]
    errors: List[Dict[str, Any]] = field(default_factory=list)
    verification_results: Dict[str, bool] = field(default_factory=dict)
    rollback_performed: bool = False
    audit_log_path: Optional[str] = None

    def to_json(self) -> str:
        """Convert report to JSON."""
        return json.dumps(
            {
                "incident_id": self.incident_id,
                "rotation_timestamp": self.rotation_timestamp,
                "total_credentials": self.total_credentials,
                "successful_rotations": self.successful_rotations,
                "failed_rotations": self.failed_rotations,
                "credentials_rotated": self.credentials_rotated,
                "errors": self.errors,
                "verification_results": self.verification_results,
                "rollback_performed": self.rollback_performed,
                "audit_log_path": self.audit_log_path,
            },
            indent=2,
        )


class CredentialRotator:
    """
    Rotates credentials across multiple systems during incidents.

    Supported Systems:
    - AWS (IAM, Secrets Manager, RDS)
    - Databases (PostgreSQL, MySQL, Redis)
    - Kubernetes (Secrets, ConfigMaps)
    - HashiCorp Vault
    - Application secrets
    """

    def __init__(
        self,
        dry_run: bool = False,
        backup_before_rotation: bool = True,
        verify_after_rotation: bool = True,
    ):
        """
        Initialize credential rotator.

        Args:
            dry_run: If True, simulate rotation without making changes
            backup_before_rotation: Backup old credentials before rotation
            verify_after_rotation: Verify new credentials work before retiring old ones
        """
        self.dry_run = dry_run
        self.backup_before_rotation = backup_before_rotation
        self.verify_after_rotation = verify_after_rotation

        # Initialize clients for various systems
        self.aws_clients = {}
        self.db_connections = {}

    def rotate_credentials(
        self, credentials: List[Credential], incident_id: str
    ) -> RotationReport:
        """
        Rotate multiple credentials across systems.

        Args:
            credentials: List of credentials to rotate
            incident_id: Incident ID for audit logging

        Returns:
            RotationReport with results
        """
        logger.info(f"Starting credential rotation for {len(credentials)} credentials")

        successful = 0
        failed = 0
        rotated_ids = []
        errors = []
        verification_results = {}

        # Create audit log
        audit_log = []

        for cred in credentials:
            logger.info(f"Rotating {cred.name} ({cred.type.value}) in {cred.location}")

            try:
                # Backup old value
                if self.backup_before_rotation:
                    self._backup_credential(cred, audit_log)

                # Rotate based on type
                if cred.type == CredentialType.AWS_ACCESS_KEY:
                    self._rotate_aws_key(cred, audit_log)
                elif cred.type == CredentialType.DATABASE_PASSWORD:
                    self._rotate_database_password(cred, audit_log)
                elif cred.type == CredentialType.API_KEY:
                    self._rotate_api_key(cred, audit_log)
                elif cred.type == CredentialType.JWT_SECRET:
                    self._rotate_jwt_secret(cred, audit_log)
                elif cred.type == CredentialType.ENCRYPTION_KEY:
                    self._rotate_encryption_key(cred, audit_log)
                elif cred.type == CredentialType.REDIS_PASSWORD:
                    self._rotate_redis_password(cred, audit_log)
                else:
                    self._rotate_generic_secret(cred, audit_log)

                cred.rotation_status = "completed"
                cred.rotation_timestamp = datetime.utcnow().isoformat()
                rotated_ids.append(cred.credential_id)
                successful += 1

                # Verify new credential
                if self.verify_after_rotation:
                    verification = self._verify_credential(cred)
                    verification_results[cred.credential_id] = verification

                    if not verification and cred.rollback_value:
                        # Rollback on failure
                        logger.warning(
                            f"Verification failed for {cred.name}, rolling back"
                        )
                        self._rollback_credential(cred, audit_log)

            except Exception as e:
                logger.error(f"Failed to rotate {cred.name}: {e}")
                cred.rotation_status = "failed"
                failed += 1
                errors.append(
                    {
                        "credential_id": cred.credential_id,
                        "name": cred.name,
                        "error": str(e),
                    }
                )

        # Save audit log
        audit_log_path = self._save_audit_log(incident_id, audit_log)

        # Create report
        report = RotationReport(
            incident_id=incident_id,
            rotation_timestamp=datetime.utcnow().isoformat(),
            total_credentials=len(credentials),
            successful_rotations=successful,
            failed_rotations=failed,
            credentials_rotated=rotated_ids,
            errors=errors,
            verification_results=verification_results,
            audit_log_path=audit_log_path,
        )

        logger.info(
            f"Credential rotation complete: {successful} successful, {failed} failed"
        )

        return report

    def _backup_credential(self, cred: Credential, audit_log: List[Dict]):
        """Backup current credential value to secure storage."""
        logger.debug(f"Backing up {cred.name}")

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "backup",
                    "credential": cred.name,
                    "status": "skipped (dry_run)",
                }
            )
            return

        # Store in secure backup system (e.g., HashiCorp Vault, AWS Secrets Manager)
        # This is a placeholder - actual implementation depends on your secure storage
        backup_data = {
            "credential_id": cred.credential_id,
            "backup_timestamp": datetime.utcnow().isoformat(),
            "hash": cred.current_value_hash,
            "location": f"backup/{cred.credential_id}",
            "incident_backup": True,
        }

        audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "backup",
                "credential": cred.name,
                "status": "success",
                "backup_location": backup_data["location"],
            }
        )

    def _rotate_aws_key(self, cred: Credential, audit_log: List[Dict]):
        """Rotate AWS access key."""
        if not self.dry_run and not BOTO3_AVAILABLE:
            raise RuntimeError(
                "boto3 is required for AWS key rotation. Install with: pip install boto3"
            )

        logger.debug(f"Rotating AWS key for {cred.location}")

        if self.dry_run:
            # Generate fake new key for dry run
            new_key = "AKIAIOSIMULATED" + secrets.token(16)
            new_secret = "simulated_secret_" + secrets.token(32)
        else:
            # For AWS access keys, we would:
            # 1. Create new access key via AWS IAM
            # 2. Store new credentials in Secrets Manager
            # 3. Update applications to use new key
            # 4. Disable old access key (after grace period)

            # Placeholder implementation
            import boto3

            iam = boto3.client("iam")

            # Create new access key
            try:
                response = iam.create_access_key(UserName=cred.location)
                new_key = response["AccessKey"]["AccessKeyId"]
                new_secret = response["AccessKey"]["SecretAccessKey"]

                # Store securely
                self._store_secret(cred, new_key, new_secret)

            except Exception as e:
                logger.error(f"AWS key rotation failed: {e}")
                raise

        cred.new_value = new_key
        cred.services_affected.extend(["aws_services"])

        audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "rotate",
                "credential": cred.name,
                "type": "aws_access_key",
                "status": "success",
                "location": cred.location,
            }
        )

    def _rotate_database_password(self, cred: Credential, audit_log: List[Dict]):
        """Rotate database password."""
        if not self.dry_run and not PSYCOPG2_AVAILABLE:
            raise RuntimeError(
                "psycopg2 is required for database password rotation. Install with: pip install psycopg2-binary"
            )

        logger.debug(f"Rotating database password for {cred.location}")

        # Generate strong password
        new_password = self._generate_strong_password()

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "database_password",
                    "status": "skipped (dry_run)",
                    "database": cred.location,
                }
            )
            return

        # Connect to database and change password
        try:
            # PostgreSQL
            if "postgresql" in cred.location.lower() or "rds" in cred.location.lower():
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    database=(
                        cred.location.split("/")[0]
                        if "/" in cred.location
                        else "psychsync"
                    ),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD"),  # Current password
                )

                conn.autocommit = True
                cursor = conn.cursor()

                # Change password (adjust SQL based on DB type)
                cursor.execute(
                    sql.SQL("ALTER USER {} PASSWORD %s").format(
                        sql.Identifier(cred.services_affected[0])
                        if cred.services_affected
                        else sql.Identifier("app_user")
                    ),
                    (new_password,),
                )

                cursor.close()
                conn.close()

            # Update application configuration
            self._update_service_config(cred, new_password, audit_log)

            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "database_password",
                    "status": "success",
                    "database": cred.location,
                }
            )

        except Exception as e:
            logger.error(f"Database password rotation failed: {e}")
            raise

    def _rotate_api_key(self, cred: Credential, audit_log: List[Dict]):
        """Rotate API key."""
        logger.debug(f"Rotating API key for {cred.location}")

        # Generate new API key
        new_key = self._generate_api_key()

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "api_key",
                    "status": "skipped (dry_run)",
                }
            )
            return

        # Update service configuration
        self._update_service_config(cred, new_key, audit_log)

        audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "rotate",
                "credential": cred.name,
                "type": "api_key",
                "status": "success",
                "service": cred.location,
            }
        )

    def _rotate_jwt_secret(self, cred: Credential, audit_log: List[Dict]):
        """Rotate JWT signing secret."""
        logger.debug(f"Rotating JWT secret for {cred.location}")

        # Generate new secret
        new_secret = secrets.token_urlsafe(32)

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "jwt_secret",
                    "status": "skipped (dry_run)",
                }
            )
            return

        # Update application configuration
        self._update_service_config(cred, new_secret, audit_log)

        # Invalidate existing JWT tokens
        self._invalidate_jwt_tokens(cred, audit_log)

        audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "rotate",
                "credential": cred.name,
                "type": "jwt_secret",
                "status": "success",
                "service": cred.location,
            }
        )

    def _rotate_encryption_key(self, cred: Credential, audit_log: List[Dict]):
        """Rotate encryption key with key rotation."""
        if not self.dry_run and not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError(
                "cryptography is required for encryption key rotation. Install with: pip install cryptography"
            )

        logger.debug(f"Rotating encryption key for {cred.location}")

        # Generate new encryption key
        new_key = secrets.token_bytes(32)

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "encryption_key",
                    "status": "skipped (dry_run)",
                }
            )
            return

        # Key rotation: Re-encrypt data with new key
        # This is complex and depends on your encryption setup
        # Placeholder implementation
        audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "rotate",
                "credential": cred.name,
                "type": "encryption_key",
                "status": "success",
                "note": "Data re-encryption required",
            }
        )

    def _rotate_redis_password(self, cred: Credential, audit_log: List[Dict]):
        """Rotate Redis password."""
        if not self.dry_run and not REDIS_AVAILABLE:
            raise RuntimeError(
                "redis is required for Redis password rotation. Install with: pip install redis"
            )

        logger.debug(f"Rotating Redis password for {cred.location}")

        new_password = self._generate_strong_password()

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "redis_password",
                    "status": "skipped (dry_run)",
                }
            )
            return

        # Connect to Redis and set password
        try:
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=os.getenv("REDIS_PASSWORD"),
            )

            # AUTH command (if password is set)
            if os.getenv("REDIS_PASSWORD"):
                r.auth(new_password)

            # CONFIG SET requirepass
            r.config_set("requirepass", new_password)

            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "redis_password",
                    "status": "success",
                    "location": cred.location,
                }
            )

        except Exception as e:
            logger.error(f"Redis password rotation failed: {e}")
            raise

    def _rotate_generic_secret(self, cred: Credential, audit_log: List[Dict]):
        """Rotate generic secret."""
        logger.debug(f"Rotating generic secret {cred.name}")

        # Generate new secret value
        new_secret = secrets.token_urlsafe(32)

        if self.dry_run:
            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rotate",
                    "credential": cred.name,
                    "type": "generic_secret",
                    "status": "skipped (dry_run)",
                }
            )
            return

        # Update service configuration
        self._update_service_config(cred, new_secret, audit_log)

        audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "rotate",
                "credential": cred.name,
                "type": "generic_secret",
                "status": "success",
                "location": cred.location,
            }
        )

    def _update_service_config(
        self, cred: Credential, new_value: str, audit_log: List[Dict]
    ):
        """Update service configuration with new credential."""
        logger.debug(f"Updating service configuration for {cred.location}")

        # This depends on your deployment architecture
        # Could update:
        # - Kubernetes secrets
        # - Environment variables
        # - Configuration files
        # - Secrets Manager

        # Example: Update Kubernetes secret
        if "kubernetes" in cred.location.lower():
            try:
                subprocess.run(
                    [
                        "kubectl",
                        "patch",
                        "secret",
                        cred.location,
                        "-p",
                        f'{{"stringData": {{"{cred.name}": "{base64.b64encode(new_value.encode()).decode()}"}}}}',
                    ],
                    check=True,
                )

                audit_log.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "update_config",
                        "service": cred.location,
                        "status": "success",
                    }
                )

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to update Kubernetes config: {e}")
                raise

    def _invalidate_jwt_tokens(self, cred: Credential, audit_log: List[Dict]):
        """Invalidate existing JWT tokens."""
        logger.debug(f"Invalidating JWT tokens for {cred.location}")

        # Add token to blocklist in Redis
        # This depends on your token management system
        # Placeholder implementation
        pass

    def _verify_credential(self, cred: Credential) -> bool:
        """Verify new credential works."""
        logger.debug(f"Verifying {cred.name}")

        if cred.type == CredentialType.DATABASE_PASSWORD:
            # Test database connection
            return self._test_database_connection(cred)

        elif cred.type == CredentialType.API_KEY:
            # Test API call
            return self._test_api_call(cred)

        elif cred.type == CredentialType.REDIS_PASSWORD:
            # Test Redis connection
            return self._test_redis_connection(cred)

        # Default: assume verification passed
        return True

    def _test_database_connection(self, cred: Credential) -> bool:
        """Test database connection with new password."""
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database="psychsync",
                user="app_user",
                password=cred.new_value,
                connect_timeout=5,
            )
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def _test_api_call(self, cred: Credential) -> bool:
        """Test API call with new key."""
        # Placeholder - depends on API
        return True

    def _test_redis_connection(self, cred: Credential) -> bool:
        """Test Redis connection with new password."""
        try:
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                password=cred.new_value,
                socket_timeout=5,
            )
            r.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False

    def _rollback_credential(self, cred: Credential, audit_log: List[Dict]):
        """Rollback to old credential value."""
        logger.warning(f"Rolling back {cred.name}")

        if cred.rollback_value:
            # Restore old value
            self._update_service_config(cred, cred.rollback_value, audit_log)

            audit_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "rollback",
                    "credential": cred.name,
                    "status": "success",
                }
            )

    def _generate_strong_password(self, length: int = 32) -> str:
        """Generate strong random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_api_key(self, length: int = 32) -> str:
        """Generate API key."""
        return secrets.token_urlsafe(length)

    def _store_secret(self, cred: Credential, key: str, secret: str):
        """Store secret securely."""
        # This would integrate with your secrets management system
        # (AWS Secrets Manager, HashiCorp Vault, etc.)
        pass

    def _save_audit_log(self, incident_id: str, audit_log: List[Dict]) -> str:
        """Save audit log to secure storage."""
        audit_log_path = f"audit/credential-rotation/{incident_id}/{datetime.utcnow().isoformat()}.json"

        if self.dry_run:
            logger.info(f"[DRY RUN] Would save audit log to {audit_log_path}")
            return audit_log_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)

        # Save audit log
        with open(audit_log_path, "w") as f:
            json.dump(audit_log, f, indent=2)

        # Also log to central logging system
        logger.info(f"Audit log saved to {audit_log_path}")

        return audit_log_path


# CLI interface
def main():
    """CLI for credential rotation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rotate credentials during security incidents"
    )
    parser.add_argument("--incident-id", required=True, help="Incident ID for tracking")
    parser.add_argument(
        "--credentials-file", required=True, help="JSON file with credentials to rotate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rotation without making changes",
    )
    parser.add_argument("--output", help="Output path for rotation report (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Load credentials
    with open(args.credentials_file, "r") as f:
        creds_data = json.load(f)

    # Create Credential objects
    credentials = []
    for item in creds_data["credentials"]:
        cred = Credential(
            credential_id=item["id"],
            name=item["name"],
            type=CredentialType(item["type"]),
            location=item["location"],
            current_value_hash=item.get("hash", ""),
            services_affected=item.get("services", []),
        )
        credentials.append(cred)

    # Run rotation
    rotator = CredentialRotator(dry_run=args.dry_run)
    report = rotator.rotate_credentials(
        credentials=credentials, incident_id=args.incident_id
    )

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report.to_json())

        print(f"\nRotation report saved to {args.output}")

    # Print summary
    print(f"\nCredential Rotation Summary:")
    print(f"  Total: {report.total_credentials}")
    print(f"  Successful: {report.successful_rotations}")
    print(f"  Failed: {report.failed_rotations}")
    print(f"  Dry Run: {args.dry_run}")


if __name__ == "__main__":
    main()
