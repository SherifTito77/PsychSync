#!/usr/bin/env python3
"""
Simple script to create test users with bcrypt passwords in SQLite database
"""

import sqlite3
import sys
import uuid

import bcrypt

# Database file
DB_FILE = "psychsync_dev.db"


def create_test_users():
    """Create test users with proper bcrypt hashes"""

    # Connect to SQLite database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Test users to create
    test_users = [
        {
            "email": "testuser2025@example.com",
            "password": "TestUser123!",
            "role": "USER",
            "first_name": "Test",
            "last_name": "User",
        },
        {
            "email": "testadmin2025@example.com",
            "password": "Admin123!",
            "role": "ADMIN",
            "first_name": "Test",
            "last_name": "Admin",
        },
        {
            "email": "testuser2025pass@example.com",
            "password": "User2025@Pass",
            "role": "USER",
            "first_name": "Test",
            "last_name": "User2",
        },
    ]

    print("🔐 Creating test users with bcrypt passwords...")

    for user_data in test_users:
        email = user_data["email"]
        password = user_data["password"]

        # Generate bcrypt hash
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()

        if existing:
            # Update existing user
            print(f"🔄 Updating existing user: {email}")
            cursor.execute(
                """
                UPDATE users SET
                    password_hash = ?,
                    role = ?,
                    first_name = ?,
                    last_name = ?
                WHERE email = ?
            """,
                (
                    password_hash,
                    user_data["role"],
                    user_data["first_name"],
                    user_data["last_name"],
                    email,
                ),
            )
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            print(f"➕ Creating new user: {email}")
            cursor.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, role, first_name, last_name,
                    is_active, is_verified, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, datetime('now'), datetime('now'))
            """,
                (
                    user_id,
                    email,
                    password_hash,
                    user_data["role"],
                    user_data["first_name"],
                    user_data["last_name"],
                ),
            )

    # Commit changes
    conn.commit()

    # Verify users
    print("\n✅ Test users created:")
    cursor.execute(
        """
        SELECT email, role, first_name, last_name,
               substr(password_hash, 1, 20) || '...' as hash_preview
        FROM users
        WHERE email LIKE 'testuser2025%' OR email LIKE 'testadmin2025%'
        ORDER BY email
    """
    )

    for row in cursor.fetchall():
        print(f"  📧 {row[0]} | 🔑 {row[1]} | 👤 {row[2]} {row[3]} | 🔐 {row[4]}")

    conn.close()
    print("\n🎉 Test users with bcrypt passwords created successfully!")


if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
