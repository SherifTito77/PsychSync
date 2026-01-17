#!/usr/bin/env python3
"""
Debug script to test bcrypt password verification
"""
import bcrypt
from passlib.context import CryptContext

# Use the same configuration as the application
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    deprecated="auto",
    bcrypt__rounds=12
)

def test_password_verification():
    """Test password verification with the actual hash from database"""

    # Actual hash from database
    stored_hash = "$2b$12$dfeyv4E9hfTSnlWpnCdDOulofJxxsSK6GUD1WwDtiPTpoEN.BkaEy"

    # Test passwords
    test_passwords = [
        "Admin@12345",
        "admin",
        "password",
        "Admin123",
        "admin@example.com"
    ]

    print("=== PASSWORD VERIFICATION DEBUG ===")
    print(f"Stored hash: {stored_hash}")
    print(f"Hash algorithm: {stored_hash.split('$')[1] if len(stored_hash.split('$')) > 1 else 'unknown'}")
    print(f"Hash rounds: {stored_hash.split('$')[2] if len(stored_hash.split('$')) > 2 else 'unknown'}")
    print()

    for password in test_passwords:
        print(f"Testing password: '{password}'")

        # Test with passlib (used by the application)
        try:
            result_passlib = pwd_context.verify(password, stored_hash)
            print(f"  Passlib result: {result_passlib}")
        except Exception as e:
            print(f"  Passlib error: {e}")

        # Test with direct bcrypt
        try:
            result_bcrypt = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            print(f"  Bcrypt result: {result_bcrypt}")
        except Exception as e:
            print(f"  Bcrypt error: {e}")

        # Generate new hash for comparison
        try:
            new_hash = pwd_context.hash(password)
            print(f"  New hash would be: {new_hash}")
        except Exception as e:
            print(f"  Hash generation error: {e}")

        print()

def test_hash_generation():
    """Test hash generation for known passwords"""
    print("=== HASH GENERATION TEST ===")

    password = "Admin@12345"
    print(f"Password: '{password}'")

    # Generate multiple hashes to see the pattern
    for i in range(3):
        new_hash = pwd_context.hash(password)
        print(f"Generated hash {i+1}: {new_hash}")

        # Verify the generated hash
        verification = pwd_context.verify(password, new_hash)
        print(f"  Verification: {verification}")
        print()

if __name__ == "__main__":
    test_password_verification()
    test_hash_generation()
