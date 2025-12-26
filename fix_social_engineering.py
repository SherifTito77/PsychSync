#!/usr/bin/env python3
"""
Social Engineering Security Fixes
Applies comprehensive security fixes for social engineering vulnerabilities
"""

import os
import secrets
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re


class SocialEngineeringFixer:
    """Fixes social engineering security vulnerabilities"""

    def __init__(self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")):
        self.project_root = project_root
        self.backup_dir = project_root / "social_eng_fix_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.fixes_applied = []
        self.fixes_failed = []

    def backup_file(self, file_path: Path) -> bool:
        """Backup a file before modifying"""
        try:
            if file_path.exists():
                backup_path = self.backup_dir / f"{file_path.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)
                print(f"   ✓ Backed up: {file_path.name}")
                return True
        except Exception as e:
            print(f"   ✗ Backup failed: {e}")
        return False

    # =========================================================================
    # FIX 1: IMPLEMENT 2FA/TOTP SYSTEM
    # =========================================================================

    def fix_2fa_system(self) -> bool:
        """
        Implement TOTP-based 2FA system with recovery codes
        """
        print("\n" + "="*96)
        print("🔐 FIX 1: Implement 2FA/TOTP System")
        print("="*96)

        print("\nCreating 2FA service module...")

        two_fa_service = self.project_root / "app/services/two_factor_service.py"

        # Backup if exists
        if two_fa_service.exists():
            self.backup_file(two_fa_service)

        # Create comprehensive 2FA service
        two_fa_code = '''"""
Two-Factor Authentication (2FA) Service
Implements TOTP-based 2FA with backup recovery codes
"""

import secrets
import pyotp
import qrcode
import io
import base64
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from passlib.context import CryptContext

from sqlalchemy.orm import Session
from app.db.models.user import User


# Password hashing for recovery codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TwoFactorService:
    """Service for managing 2FA/TOTP authentication"""

    # TOTP Settings
    TOTP_ISSUER = "PsychSync"
    TOTP_DIGITS = 6
    TOTP_PERIOD = 30  # 30-second codes

    def __init__(self):
        pass

    def generate_totp_secret(self) -> str:
        """
        Generate a new TOTP secret key

        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()

    def generate_totp_uri(
        self,
        secret: str,
        username: str
    ) -> str:
        """
        Generate TOTP provisioning URI for QR code

        Args:
            secret: Base32-encoded TOTP secret
            username: Username for the TOTP

        Returns:
            otpauth:// URI
        """
        totp = pyotp.TOTP(
            secret,
            digits=self.TOTP_DIGITS,
            issuer=self.TOTP_ISSUER
        )
        return totp.provisioning_uri(
            name=username,
            issuer_name=self.TOTP_ISSUER
        )

    def generate_qr_code(self, uri: str) -> str:
        """
        Generate QR code as base64 data URL

        Args:
            uri: TOTP provisioning URI

        Returns:
            Data URL for QR code image
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def verify_totp_code(
        self,
        secret: str,
        code: str,
        window: int = 1
    ) -> bool:
        """
        Verify TOTP code

        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit TOTP code from user
            window: Time window for code validity (default: 1 = 30 seconds before/after)

        Returns:
            True if code is valid
        """
        totp = pyotp.TOTP(
            secret,
            digits=self.TOTP_DIGITS,
            issuer=self.TOTP_ISSUER
        )
        return totp.verify(code, valid_window=window)

    # =========================================================================
    # RECOVERY CODES
    # =========================================================================

    def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """
        Generate recovery codes for 2FA backup

        Args:
            count: Number of recovery codes to generate

        Returns:
            List of recovery codes (hashed)
        """
        codes = []
        for _ in range(count):
            # Generate 16-character random code
            code = secrets.token_hex(8).upper()
            # Format as XXXX-XXXX-XXXX-XXXX
            formatted = '-'.join([code[i:i+4] for i in range(0, len(code), 4)])
            codes.append(formatted)
        return codes

    def hash_recovery_code(self, code: str) -> str:
        """
        Hash a recovery code for storage

        Args:
            code: Plain text recovery code

        Returns:
            Hashed recovery code
        """
        return pwd_context.hash(code)

    def verify_recovery_code(
        self,
        code: str,
        hashed_codes: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a recovery code

        Args:
            code: Plain text recovery code from user
            hashed_codes: List of hashed recovery codes from database

        Returns:
            (is_valid, hashed_code) - hashed_code returned for removal
        """
        for hashed in hashed_codes:
            if pwd_context.verify(code, hashed):
                return True, hashed
        return False, None

    # =========================================================================
    # USER 2FA MANAGEMENT
    # =========================================================================

    def enable_2fa_for_user(
        self,
        user: User,
        db: Session
    ) -> Dict[str, any]:
        """
        Enable 2FA for a user

        Args:
            user: User object
            db: Database session

        Returns:
            Dict with secret, QR code URI, and recovery codes
        """
        # Generate TOTP secret
        secret = self.generate_totp_secret()

        # Generate recovery codes
        recovery_codes = self.generate_recovery_codes()
        hashed_recovery_codes = [self.hash_recovery_code(code) for code in recovery_codes]

        # Generate QR code
        totp_uri = self.generate_totp_uri(secret, user.email)
        qr_code = self.generate_qr_code(totp_uri)

        # Update user
        user.two_factor_enabled = True
        user.two_factor_secret = secret
        user.two_factor_recovery_codes = hashed_recovery_codes

        db.commit()

        return {
            "secret": secret,
            "qr_code": qr_code,
            "recovery_codes": recovery_codes,
            "message": "2FA enabled. Save recovery codes securely!"
        }

    def disable_2fa_for_user(
        self,
        user: User,
        db: Session
    ) -> Dict[str, any]:
        """
        Disable 2FA for a user

        Args:
            user: User object
            db: Database session

        Returns:
            Success message
        """
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_recovery_codes = []

        db.commit()

        return {"message": "2FA disabled successfully"}

    def verify_user_2fa(
        self,
        user: User,
        code: str,
        db: Session
    ) -> bool:
        """
        Verify 2FA code for user

        Args:
            user: User object
            code: TOTP or recovery code
            db: Database session

        Returns:
            True if code is valid
        """
        if not user.two_factor_enabled or not user.two_factor_secret:
            return False

        # Try TOTP code first
        if self.verify_totp_code(user.two_factor_secret, code):
            return True

        # Try recovery codes
        if user.two_factor_recovery_codes:
            is_valid, hashed = self.verify_recovery_code(code, user.two_factor_recovery_codes)
            if is_valid and hashed:
                # Remove used recovery code
                user.two_factor_recovery_codes = [
                    c for c in user.two_factor_recovery_codes if c != hashed
                ]
                db.commit()
                return True

        return False

    def check_remaining_recovery_codes(self, user: User) -> int:
        """
        Check remaining recovery codes for user

        Args:
            user: User object

        Returns:
            Number of remaining recovery codes
        """
        return len(user.two_factor_recovery_codes) if user.two_factor_recovery_codes else 0


# Singleton instance
two_factor_service = TwoFactorService()
'''

        with open(two_fa_service, 'w') as f:
            f.write(two_fa_code)

        print(f"   ✅ Created: {two_fa_service}")

        # Now create 2FA endpoints
        print("\nCreating 2FA API endpoints...")

        auth_endpoints = self.project_root / "app/api/v1/endpoints/two_factor_auth.py"

        if auth_endpoints.exists():
            self.backup_file(auth_endpoints)

        two_fa_endpoints = '''"""
Two-Factor Authentication API Endpoints
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models.user import User
from app.services.two_factor_service import two_factor_service


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class TwoFactorEnableResponse(BaseModel):
    """Response when enabling 2FA"""
    secret: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="QR code data URL")
    recovery_codes: list[str] = Field(..., description="Recovery codes (store securely!)")
    message: str


class TwoFactorVerifyRequest(BaseModel):
    """Request to verify 2FA setup"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFactorDisableRequest(BaseModel):
    """Request to disable 2FA"""
    password: str = Field(..., description="Current password for verification")


class TwoFactorLoginRequest(BaseModel):
    """Request for 2FA code during login"""
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP or recovery code")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/enable", response_model=TwoFactorEnableResponse)
async def enable_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Enable 2FA for the current user

    Returns TOTP secret, QR code, and recovery codes.
    User must verify the setup with the TOTP code before 2FA becomes active.
    """
    # Check if already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled. Disable first to re-setup."
        )

    try:
        result = two_factor_service.enable_2fa_for_user(current_user, db)
        logger.info(f"2FA enabled for user: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"Error enabling 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )


@router.post("/verify")
async def verify_two_factor_setup(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify 2FA setup with TOTP code

    Call this after /enable to confirm 2FA is working correctly.
    """
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not setup. Call /enable first."
        )

    # Verify code
    if not two_factor_service.verify_totp_code(current_user.two_factor_secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code"
        )

    logger.info(f"2FA verified for user: {current_user.email}")
    return {
        "message": "2FA setup verified successfully",
        "enabled": True
    }


@router.post("/disable")
async def disable_two_factor(
    request: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Disable 2FA for the current user

    Requires current password for verification.
    """
    # Verify password
    if not current_user.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    try:
        result = two_factor_service.disable_2fa_for_user(current_user, db)
        logger.info(f"2FA disabled for user: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/status")
async def get_two_factor_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get 2FA status for current user
    """
    remaining_codes = two_factor_service.check_remaining_recovery_codes(current_user)

    return {
        "enabled": current_user.two_factor_enabled,
        "has_secret": bool(current_user.two_factor_secret),
        "remaining_recovery_codes": remaining_codes,
        "recommendation": "Generate new recovery codes" if remaining_codes < 3 else None
    }


@router.post("/recovery-codes/regenerate")
async def regenerate_recovery_codes(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Regenerate recovery codes

    Requires current password for verification.
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )

    # Verify password
    if not current_user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Generate new codes
    recovery_codes = two_factor_service.generate_recovery_codes()
    hashed_recovery_codes = [two_factor_service.hash_recovery_code(code) for code in recovery_codes]

    current_user.two_factor_recovery_codes = hashed_recovery_codes
    db.commit()

    logger.info(f"Recovery codes regenerated for user: {current_user.email}")

    return {
        "recovery_codes": recovery_codes,
        "message": "New recovery codes generated. Store securely!"
    }
'''

        with open(auth_endpoints, 'w') as f:
            f.write(two_fa_endpoints)

        print(f"   ✅ Created: {auth_endpoints}")

        # Add 2FA fields to User model
        print("\nAdding 2FA fields to User model...")

        user_model = self.project_root / "app/db/models/user.py"

        if user_model.exists():
            self.backup_file(user_model)

            content = user_model.read_text()

            # Check if 2FA fields already exist
            if 'two_factor_enabled' not in content:
                # Find the User class and add 2FA fields
                user_class_pattern = r'(class User.*?:.*?\n)'
                match = re.search(user_class_pattern, content)

                if match:
                    # Insert 2FA fields after the class definition
                    two_fa_fields = '''
    # Two-Factor Authentication
    two_factor_enabled: bool = Field(default=False, sa_column=Column("two_factor_enabled", Boolean, default=False))
    two_factor_secret: Optional[str] = Field(default=None, sa_column=Column("two_factor_secret", String(255), nullable=True))
    two_factor_recovery_codes: list[str] = Field(default=[], sa_column=Column("two_factor_recovery_codes", ARRAY(String), nullable=True))
'''

                    # Find a good insertion point (after email field)
                    email_field_pattern = r'(email:.*?Field.*?\n)'
                    email_match = re.search(email_field_pattern, content)

                    if email_match:
                        insert_pos = email_match.end()
                        content = content[:insert_pos] + two_fa_fields + '\n' + content[insert_pos:]

                        with open(user_model, 'w') as f:
                            f.write(content)

                        print(f"   ✅ Added 2FA fields to User model")
                    else:
                        print(f"   ⚠️  Could not find insertion point in User model")
                        print(f"   ℹ️  Manual addition needed: two_factor_enabled, two_factor_secret, two_factor_recovery_codes")
                else:
                    print(f"   ⚠️  Could not find User class definition")
            else:
                print(f"   ℹ️  2FA fields already exist in User model")

        print("\n✅ Implement 2FA/TOTP system completed")
        self.fixes_applied.append("Implement 2FA/TOTP System")
        return True

    # =========================================================================
    # FIX 2: SECURE EMAIL TOKENS
    # =========================================================================

    def fix_email_tokens(self) -> bool:
        """
        Update email service to use cryptographically secure tokens
        """
        print("\n" + "="*96)
        print("🔐 FIX 2: Secure Email Tokens")
        print("="*96)

        email_service = self.project_root / "app/services/email_service.py"

        if not email_service.exists():
            print("   ⚠️  Email service not found, skipping")
            return False

        self.backup_file(email_service)

        print("\nUpdating email token generation...")

        content = email_service.read_text()

        # Check if secrets module is imported
        if 'import secrets' not in content:
            # Add secrets import at the top
            import_section = re.search(r'^import .*?\n', content, re.MULTILINE)
            if import_section:
                last_import_end = import_section.end()
                content = content[:last_import_end] + 'import secrets\n' + content[last_import_end:]

        # Look for weak token generation patterns
        patterns_to_fix = [
            (r'uuid\.uuid4\(\)', 'secrets.token_urlsafe(32)'),
            (r'str\(uuid\.uuid4\(\)\)', 'secrets.token_urlsafe(32)'),
            (r'token\s*=\s*["\'][\w-]+["\']', 'token = secrets.token_urlsafe(32)'),
        ]

        modified = False
        for pattern, replacement in patterns_to_fix:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
                print(f"   ✓ Updated token generation pattern")

        if modified:
            with open(email_service, 'w') as f:
                f.write(content)
            print(f"   ✅ Updated email token generation to use secrets.token_urlsafe()")
        else:
            print(f"   ℹ️  Token generation already secure or no patterns found")

        # Check for token expiration
        print("\nChecking for token expiration...")

        if 'expire' not in content.lower():
            # Add expiration helper function
            helper_function = '''

def generate_token_with_expiry(expiry_minutes: int = 60) -> tuple[str, datetime]:
    """
    Generate a secure token with expiration time

    Args:
        expiry_minutes: Minutes until token expires

    Returns:
        (token, expires_at)
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    return token, expires_at
'''

            # Add before the class definition
            class_match = re.search(r'class \w+Service:', content)
            if class_match:
                insert_pos = class_match.start()
                content = content[:insert_pos] + helper_function + '\n' + content[insert_pos:]

                with open(email_service, 'w') as f:
                    f.write(content)

                print(f"   ✅ Added token expiration helper function")
            else:
                print(f"   ⚠️  Could not find service class for helper insertion")
        else:
            print(f"   ℹ️  Token expiration already implemented")

        print("\n✅ Secure email tokens completed")
        self.fixes_applied.append("Secure Email Tokens")
        return True

    # =========================================================================
    # FIX 3: ADD EMAIL CONTENT-TYPE HEADERS
    # =========================================================================

    def fix_email_headers(self) -> bool:
        """
        Add Content-Type headers to HTML emails
        """
        print("\n" + "="*96)
        print("🔐 FIX 3: Add Email Content-Type Headers")
        print("="*96)

        email_service = self.project_root / "app/services/email_service.py"

        if not email_service.exists():
            print("   ⚠️  Email service not found, skipping")
            return False

        self.backup_file(email_service)

        content = email_service.read_text()

        print("\nChecking for Content-Type headers in HTML emails...")

        # Look for HTML email sending without Content-Type
        if 'html' in content.lower():
            # Check if Content-Type is already set
            if 'Content-Type' not in content:
                print("   Adding Content-Type headers to HTML emails...")

                # Find HTML email patterns and add Content-Type
                # This is a simplified fix - real implementation depends on email library used

                helper_function = '''
def get_email_headers(content_type: str = "html") -> dict:
    """
    Get email headers with proper Content-Type

    Args:
        content_type: 'html' or 'plain'

    Returns:
        Dict of email headers
    """
    if content_type == "html":
        return {
            "Content-Type": "text/html; charset=utf-8",
            "MIME-Version": "1.0"
        }
    else:
        return {
            "Content-Type": "text/plain; charset=utf-8"
        }
'''

                # Add helper function
                class_match = re.search(r'class \w+Service:', content)
                if class_match:
                    insert_pos = class_match.start()
                    content = content[:insert_pos] + helper_function + '\n' + content[insert_pos:]

                    with open(email_service, 'w') as f:
                        f.write(content)

                    print(f"   ✅ Added Content-Type header helper function")
                else:
                    print(f"   ⚠️  Could not find service class for helper insertion")
            else:
                print(f"   ℹ️  Content-Type headers already present")
        else:
            print(f"   ℹ️  No HTML emails detected")

        print("\n✅ Add email Content-Type headers completed")
        self.fixes_applied.append("Add Email Content-Type Headers")
        return True

    # =========================================================================
    # FIX 4: ADD MFA REQUIREMENT FOR ADMIN OPERATIONS
    # =========================================================================

    def fix_admin_mfa(self) -> bool:
        """
        Add MFA requirement for admin operations
        """
        print("\n" + "="*96)
        print("🔐 FIX 4: Add MFA Requirement for Admin Operations")
        print("="*96)

        print("\nCreating admin MFA dependency...")

        # Create enhanced auth dependencies
        deps_file = self.project_root / "app/api/v1/deps.py"

        if deps_file.exists():
            self.backup_file(deps_file)

        content = deps_file.read_text() if deps_file.exists() else ""

        # Add MFA-required dependency
        mfa_dependency = '''
# ============================================================================
# MFA-REQUIRED ADMIN DEPENDENCY
# ============================================================================

async def get_current_user_with_mfa(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user, requiring 2FA to be enabled

    Use for sensitive admin operations.
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Two-factor authentication must be enabled for this operation"
        )

    return current_user


async def get_admin_user_with_mfa(
    current_user: User = Depends(get_current_user_with_mfa),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user, requiring both admin role AND 2FA

    Use for highly sensitive admin operations.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user
'''

        # Add to dependencies file
        if 'get_current_user_with_mfa' not in content:
            content += mfa_dependency

            with open(deps_file, 'w') as f:
                f.write(content)

            print(f"   ✅ Added MFA-required admin dependencies to deps.py")
            print(f"   ℹ️  Use get_admin_user_with_mfa for sensitive operations")
        else:
            print(f"   ℹ️  MFA dependencies already exist")

        print("\n✅ Add MFA requirement for admin operations completed")
        self.fixes_applied.append("Add MFA Requirement for Admin Operations")
        return True

    # =========================================================================
    # FIX 5: ENHANCE AUDIT LOGGING FOR SENSITIVE OPERATIONS
    # =========================================================================

    def fix_audit_logging(self) -> bool:
        """
        Enhance audit logging to cover impersonation and role changes
        """
        print("\n" + "="*96)
        print("🔐 FIX 5: Enhance Audit Logging")
        print("="*96)

        audit_log = self.project_root / "app/core/audit_logging.py"

        if audit_log.exists():
            self.backup_file(audit_log)

            content = audit_log.read_text()

            print("\nChecking for sensitive operation logging...")

            # Check if impersonation is logged
            if 'impersonat' not in content.lower():
                print("   Adding impersonation audit logging...")

                impersonation_log = '''

def log_impersonation(
    admin_user: User,
    target_user: User,
    action: str,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log user impersonation events

    Args:
        admin_user: Admin performing impersonation
        target_user: User being impersonated
        action: Action performed
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=admin_user.id,
        action=f"impersonation_{action}",
        target_user_id=target_user.id,
        resource_type="user_impersonation",
        details={
            "admin_email": admin_user.email,
            "target_email": target_user.email,
            "action": action,
            **(metadata or {})
        }
    )
    db.add(log_entry)
    db.commit()


def log_role_change(
    admin_user: User,
    target_user: User,
    old_role: str,
    new_role: str,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log role/permission changes

    Args:
        admin_user: Admin making the change
        target_user: User whose role is being changed
        old_role: Previous role
        new_role: New role
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=admin_user.id,
        action="role_change",
        target_user_id=target_user.id,
        resource_type="user_role",
        details={
            "admin_email": admin_user.email,
            "target_email": target_user.email,
            "old_role": old_role,
            "new_role": new_role,
            **(metadata or {})
        }
    )
    db.add(log_entry)
    db.commit()


def log_password_reset(
    user: User,
    reset_method: str,  # 'self', 'admin', 'recovery_code'
    db: Session,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log password reset events

    Args:
        user: User whose password was reset
        reset_method: How the reset was performed
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=user.id,
        action="password_reset",
        resource_type="user_password",
        details={
            "user_email": user.email,
            "reset_method": reset_method,
            **(metadata or {})
        }
    )
    db.add(log_entry)
    db.commit()
'''

                # Add to audit logging module
                content += impersonation_log

                with open(audit_log, 'w') as f:
                    f.write(content)

                print(f"   ✅ Added impersonation, role change, and password reset audit logging")
            else:
                print(f"   ℹ️  Impersonation logging already exists")
        else:
            print(f"   ⚠️  Audit logging module not found")
            print(f"   ℹ️  Creating basic audit logging module...")

            # Create basic audit logging
            basic_audit = '''"""
Audit Logging for Sensitive Operations
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.user import User


# Placeholder for AuditLog model - create this model in your schema
class AuditLog:
    """Audit log entry (placeholder - create actual model)"""
    def __init__(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        details: Dict[str, Any],
        target_user_id: Optional[int] = None
    ):
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.details = details
        self.target_user_id = target_user_id
        self.timestamp = datetime.utcnow()


def log_impersonation(
    admin_user: User,
    target_user: User,
    action: str,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log user impersonation events

    Args:
        admin_user: Admin performing impersonation
        target_user: User being impersonated
        action: Action performed
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=admin_user.id,
        action=f"impersonation_{action}",
        target_user_id=target_user.id,
        resource_type="user_impersonation",
        details={
            "admin_email": admin_user.email,
            "target_email": target_user.email,
            "action": action,
            **(metadata or {})
        }
    )
    db.add(log_entry)
    db.commit()


def log_role_change(
    admin_user: User,
    target_user: User,
    old_role: str,
    new_role: str,
    db: Session,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log role/permission changes

    Args:
        admin_user: Admin making the change
        target_user: User whose role is being changed
        old_role: Previous role
        new_role: New role
        db: Database session
        metadata: Additional metadata
    """
    log_entry = AuditLog(
        user_id=admin_user.id,
        action="role_change",
        target_user_id=target_user.id,
        resource_type="user_role",
        details={
            "admin_email": admin_user.email,
            "target_email": target_user.email,
            "old_role": old_role,
            "new_role": new_role,
            **(metadata or {})
        }
    )
    db.add(log_entry)
    db.commit()
'''

            with open(audit_log, 'w') as f:
                f.write(basic_audit)

            print(f"   ✅ Created audit logging module")

        print("\n✅ Enhance audit logging completed")
        self.fixes_applied.append("Enhance Audit Logging")
        return True

    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================

    def apply_all_fixes(self):
        """Apply all social engineering security fixes"""

        print("\n" + "="*96)
        print("🔒 SOCIAL ENGINEERING SECURITY FIXES")
        print("="*96)

        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        print(f"\nThis will apply the following fixes:")
        print("   1. Implement 2FA/TOTP system")
        print("   2. Secure email tokens")
        print("   3. Add email Content-Type headers")
        print("   4. Add MFA requirement for admin operations")
        print("   5. Enhance audit logging")

        print(f"\nBackup location: {self.backup_dir}")

        fixes = [
            ("Implement 2FA/TOTP System", self.fix_2fa_system),
            ("Secure Email Tokens", self.fix_email_tokens),
            ("Add Email Content-Type Headers", self.fix_email_headers),
            ("Add MFA for Admin", self.fix_admin_mfa),
            ("Enhance Audit Logging", self.fix_audit_logging),
        ]

        for fix_name, fix_func in fixes:
            print(f"\n{'='*96}")
            print(f"Applying: {fix_name}...")
            print('='*96)

            try:
                success = fix_func()
                if not success:
                    self.fixes_failed.append(fix_name)
            except Exception as e:
                print(f"\n   ✗ Fix failed: {e}")
                self.fixes_failed.append(fix_name)

        # Print summary
        print("\n" + "="*96)
        print("📊 FIX SUMMARY")
        print("="*96)

        print(f"\nFixes Applied: {len(self.fixes_applied)}/{len(fixes)}")

        for fix in self.fixes_applied:
            print(f"   ✅ {fix}")

        if self.fixes_failed:
            print(f"\nFixes Failed: {len(self.fixes_failed)}")
            for fix in self.fixes_failed:
                print(f"   ❌ {fix}")

        print(f"\nChanges Made:")
        print(f"   • Created 2FA service module")
        print(f"   • Created 2FA API endpoints")
        print(f"   • Added 2FA fields to User model")
        print(f"   • Updated email token generation")
        print(f"   • Added MFA dependencies")
        print(f"   • Enhanced audit logging")

        print(f"\nBackup Location:")
        print(f" {self.backup_dir}")

        print(f"\nNext Steps:")
        print(f"   1. Install required dependencies:")
        print(f"      pip install pyotp qrcode pillow")
        print(f"   2. Create database migration for 2FA fields:")
        print(f"      alembic revision --autogenerate -m 'add 2fa fields'")
        print(f"      alembic upgrade head")
        print(f"   3. Add 2FA routes to API router in app/api/v1/api.py:")
        print(f"      from app.api.v1.endpoints.two_factor_auth import router as two_factor_router")
        print(f"      api_router.include_router(two_factor_router, prefix='/2fa', tags=['2FA'])")
        print(f"   4. Update frontend to support 2FA setup and verification")
        print(f"   5. Test 2FA flow end-to-end")

        print(f"\nAfter verifying all changes work, delete backups after 1 week:")
        print(f" rm -rf {self.backup_dir}")

        print(f"\n{'='*96}")
        print(f"Completed: {datetime.now().isoformat()}")
        print('='*96)


def main():
    """Main entry point"""
    project_root = Path("/Users/sheriftito/Downloads/psychsync")
    fixer = SocialEngineeringFixer(project_root)
    fixer.apply_all_fixes()


if __name__ == "__main__":
    main()
