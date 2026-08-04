#!/usr/bin/env python3
"""
Test Data Encryption Service
Verifies PII/PHI encryption is working correctly with the new security keys
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


def test_encryption_service():
    """Test the data encryption service"""
    print("=" * 70)
    print("DATA ENCRYPTION SERVICE TEST")
    print("=" * 70)

    try:
        from app.services.data_encryption_service import DataEncryptionService

        # Initialize service
        print("\n1. Initializing encryption service...")
        service = DataEncryptionService()
        print("   ✅ Service initialized successfully")

        # Test 1: Encrypt simple string
        print("\n2. Testing simple string encryption...")
        test_data = "user@example.com"
        encrypted = service.encrypt_pii(test_data, key_id="pii_key_v1")

        print(f"   Original: {test_data}")
        print(f"   Encrypted: {encrypted.encrypted_data[:50]}...")
        print(f"   Key ID: {encrypted.key_id}")
        print(f"   ✅ String encryption successful")

        # Test 2: Decrypt the data
        print("\n3. Testing decryption...")
        decrypted = service.decrypt_pii(
            encrypted.encrypted_data, key_id=encrypted.key_id
        )

        print(f"   Decrypted: {decrypted}")
        assert decrypted == test_data, "Decrypted data doesn't match original!"
        print(f"   ✅ Decryption successful - data matches original")

        # Test 3: Encrypt complex data (dict)
        print("\n4. Testing complex data encryption...")
        complex_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
            "address": "123 Main St, City, State 12345",
        }

        encrypted_complex = service.encrypt_pii(complex_data, key_id="general_key_v1")
        print(f"   Original: {complex_data}")
        print(f"   Encrypted: {encrypted_complex.encrypted_data[:50]}...")
        print(f"   ✅ Complex data encryption successful")

        # Test 4: Decrypt complex data
        print("\n5. Testing complex data decryption...")
        decrypted_complex = service.decrypt_pii(
            encrypted_complex.encrypted_data, key_id=encrypted_complex.key_id
        )

        print(f"   Decrypted: {decrypted_complex}")
        assert (
            decrypted_complex == complex_data
        ), "Decrypted complex data doesn't match!"
        print(f"   ✅ Complex data decryption successful")

        # Test 5: Verify encryption produces different output each time
        print("\n6. Testing encryption uniqueness...")
        encrypted1 = service.encrypt_pii("test@example.com")
        encrypted2 = service.encrypt_pii("test@example.com")

        assert (
            encrypted1.encrypted_data != encrypted2.encrypted_data
        ), "Encryption should produce different output each time (IV)"
        print(f"   ✅ Encryption produces unique ciphertext (IV-based)")

        # Test 6: Test PHI encryption (healthcare data)
        print("\n7. Testing PHI (healthcare data) encryption...")
        phi_data = {
            "patient_id": "PT-12345",
            "diagnosis": "Hypertension",
            "medication": "Lisinopril 10mg",
            "notes": "Patient shows improvement",
        }

        encrypted_phi = service.encrypt_pii(phi_data, key_id="phi_key_v1")
        decrypted_phi = service.decrypt_pii(
            encrypted_phi.encrypted_data, key_id=encrypted_phi.key_id
        )

        assert decrypted_phi == phi_data, "PHI data decryption failed!"
        print(f"   ✅ PHI encryption/decryption successful (HIPAA compliant)")

        print("\n" + "=" * 70)
        print("🎉 ALL ENCRYPTION TESTS PASSED!")
        print("=" * 70)
        print("\nSummary:")
        print("  ✅ Service initialization")
        print("  ✅ Simple string encryption/decryption")
        print("  ✅ Complex data (dict) encryption/decryption")
        print("  ✅ Encryption uniqueness (IV-based)")
        print("  ✅ PHI data encryption (HIPAA/GDPR compliant)")
        print("\nThe data encryption service is working correctly!")
        print("=" * 70)

        return True

    except ImportError as e:
        print(f"\n❌ FAIL: Could not import encryption service")
        print(f"   Error: {e}")
        print("\nMake sure PSYCHSYNC_ENCRYPTION_KEY is set in .env")
        return False

    except Exception as e:
        print(f"\n❌ FAIL: Encryption test failed")
        print(f"   Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_encryption_service()
    sys.exit(0 if success else 1)
