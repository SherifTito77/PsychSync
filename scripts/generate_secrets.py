#!/usr/bin/env python3
"""
Secure Secret Generator for PsychSync

Usage:
    python scripts/generate_secrets.py

This will generate:
- Strong JWT secret key
- Fernet encryption key
- Random database password
- Random Redis password
"""

import secrets
import string

from cryptography.fernet import Fernet


def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically strong secret key"""
    return secrets.token_urlsafe(length)


def generate_encryption_key() -> str:
    """Generate a Fernet-compatible encryption key"""
    return Fernet.generate_key().decode()


def generate_password(length: int = 32) -> str:
    """Generate a strong random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main():
    print("=" * 70)
    print("🔐 PsychSync Secret Generator")
    print("=" * 70)
    print()

    print("📝 Copy these values to your .env file:")
    print()

    # JWT Secret Key
    secret_key = generate_secret_key(64)
    print(f"# JWT Authentication")
    print(f"SECRET_KEY={secret_key}")
    print()

    # Encryption Key
    encryption_key = generate_encryption_key()
    print(f"# Data Encryption")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()

    # Database Password
    db_password = generate_password(32)
    print(f"# Database")
    print(f"DATABASE_URL=postgresql://psychsync:{db_password}@localhost:5432/psychsync")
    print()

    # Redis Password
    redis_password = generate_password(32)
    print(f"# Redis")
    print(f"REDIS_URL=redis://:{redis_password}@localhost:6379/0")
    print(f"REDIS_PASSWORD={redis_password}")
    print()

    print("=" * 70)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("=" * 70)
    print()
    print("1. NEVER commit .env to git")
    print("2. Store these secrets securely (password manager, vault)")
    print("3. Use different secrets for development/staging/production")
    print("4. Rotate secrets regularly (every 90 days recommended)")
    print("5. Use AWS Secrets Manager or HashiCorp Vault in production")
    print()
    print("✅ Secrets generated successfully!")
    print()


if __name__ == "__main__":
    main()
