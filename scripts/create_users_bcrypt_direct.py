#!/usr/bin/env python3
"""
Create test users using direct bcrypt (passlib has compatibility issues)
"""

import uuid

import bcrypt


def create_test_users():
    """Create test users with direct bcrypt hashes"""

    # Test users with compatible passwords (avoid common patterns, exactly 12 chars)
    test_users = [
        {
            "email": "testuser2025@example.com",
            "password": "SecurePass12!",
            "role": "USER",
            "full_name": "Test Account",
        },
        {
            "email": "testadmin2025@example.com",
            "password": "AdminSecure12!",
            "role": "ADMIN",
            "full_name": "Test Administrator",
        },
        {
            "email": "testuser2025pass@example.com",
            "password": "MySecure@12Pwd",
            "role": "USER",
            "full_name": "Test Account2",
        },
    ]

    print("🔐 Generating direct bcrypt password hashes...")

    for user in test_users:
        # Generate hash using bcrypt directly
        password_bytes = user["password"].encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

        print(f"\n📧 {user['email']}")
        print(f"🔑 Role: {user['role']}")
        print(f"👤 Name: {user['full_name']}")
        print(f"🔐 Hash: {password_hash}")
        print(f"📏 Length: {len(password_hash)}")

        # Save hash for manual update
        print(f"\nSQL Update:")
        print(
            f"UPDATE users SET password_hash = '{password_hash}' WHERE email = '{user['email']}';"
        )


if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
