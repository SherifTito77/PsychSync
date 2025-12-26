#!/usr/bin/env python3
"""
Create test users using passlib (backend's password hashing system)
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Import backend security utilities
from app.core.security import get_password_hash

def create_test_users():
    """Create test users with passlib-generated hashes"""

    # Test users with proper passlib hashes (avoid common patterns)
    test_users = [
        {
            'email': 'testuser2025@example.com',
            'password': 'SecurePass12!',
            'role': 'USER',
            'full_name': 'Test Account'
        },
        {
            'email': 'testadmin2025@example.com',
            'password': 'SecureAccess12!',
            'role': 'ADMIN',
            'full_name': 'Test Administrator'
        },
        {
            'email': 'testuser2025pass@example.com',
            'password': 'MyProtected@12',
            'role': 'USER',
            'full_name': 'Test Account2'
        }
    ]

    print("🔐 Generating passlib-compatible password hashes...")

    for user in test_users:
        # Generate hash using backend's own method
        password_hash = get_password_hash(user['password'])

        print(f"\n📧 {user['email']}")
        print(f"🔑 Role: {user['role']}")
        print(f"👤 Name: {user['full_name']}")
        print(f"🔐 Hash: {password_hash}")
        print(f"📏 Length: {len(password_hash)}")

        # Save hash for manual update
        print(f"\nSQL Update:")
        print(f"UPDATE users SET password_hash = '{password_hash}' WHERE email = '{user['email']}';")

if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)