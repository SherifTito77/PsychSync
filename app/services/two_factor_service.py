"""
Two-Factor Authentication (2FA) Service
Implements TOTP-based 2FA with backup recovery codes
"""

import base64
import io
import secrets

import pyotp
import qrcode
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

    def generate_totp_uri(self, secret: str, username: str) -> str:
        """
        Generate TOTP provisioning URI for QR code

        Args:
            secret: Base32-encoded TOTP secret
            username: Username for the TOTP

        Returns:
            otpauth:// URI
        """
        totp = pyotp.TOTP(secret, digits=self.TOTP_DIGITS, issuer=self.TOTP_ISSUER)
        return totp.provisioning_uri(name=username, issuer_name=self.TOTP_ISSUER)

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
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """
        Verify TOTP code

        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit TOTP code from user
            window: Time window for code validity (default: 1 = 30 seconds before/after)

        Returns:
            True if code is valid
        """
        totp = pyotp.TOTP(secret, digits=self.TOTP_DIGITS, issuer=self.TOTP_ISSUER)
        return totp.verify(code, valid_window=window)

    # =========================================================================
    # RECOVERY CODES
    # =========================================================================

    def generate_recovery_codes(self, count: int = 10) -> list[str]:
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
            formatted = "-".join([code[i : i + 4] for i in range(0, len(code), 4)])
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
        self, code: str, hashed_codes: list[str]
    ) -> tuple[bool, str | None]:
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

    def enable_2fa_for_user(self, user: User, db: Session) -> dict[str, any]:
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
        hashed_recovery_codes = [
            self.hash_recovery_code(code) for code in recovery_codes
        ]

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
            "message": "2FA enabled. Save recovery codes securely!",
        }

    def disable_2fa_for_user(self, user: User, db: Session) -> dict[str, any]:
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

    def verify_user_2fa(self, user: User, code: str, db: Session) -> bool:
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
            is_valid, hashed = self.verify_recovery_code(
                code, user.two_factor_recovery_codes
            )
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
        return (
            len(user.two_factor_recovery_codes) if user.two_factor_recovery_codes else 0
        )


# Singleton instance
two_factor_service = TwoFactorService()
