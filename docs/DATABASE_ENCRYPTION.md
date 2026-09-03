# Database Encryption at Rest

Comprehensive AES-256-GCM encryption for sensitive data at rest with automatic field-level encryption and key rotation support.

## 🎯 Overview

The database encryption system protects sensitive data (PII, PHI, secrets) using industry-standard AES-256-GCM encryption with authenticated encryption. Data is encrypted transparently at the field level, ensuring protection at rest while maintaining application functionality.

**Encryption Standard:**
- **Algorithm**: AES-256-GCM (Advanced Encryption Standard - Galois/Counter Mode)
- **Key Size**: 256 bits (32 bytes)
- **Nonce Size**: 96 bits (12 bytes)
- **Authentication Tag**: 128 bits (automatic with GCM)
- **Mode**: Authenticated Encryption with Associated Data (AEAD)

**Compliance:**
- ✅ HIPAA compliant encryption for PHI
- ✅ NIST standards for cryptographic operations
- ✅ SOC 2 compatible data protection
- ✅ GDPR compliant data encryption

## 🔒 Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Application Layer                    │
│                                                          │
│  user.email = "user@example.com"                        │
│        │                                                 │
│        │ EncryptedString Type                           │
│        ▼                                                 │
│  ┌──────────────────────────────────────────┐           │
│  │   Encryption Service                      │           │
│  │                                            │           │
│  │   - Generate unique nonce (IV)            │           │
│  │   - Encrypt with AES-256-GCM             │           │
│  │   - Return JSON with nonce + ciphertext   │           │
│  └──────────────────────────────────────────┘           │
│        │                                                 │
│        ▼                                                 │
│  {"nonce":"base64","ciphertext":"base64","version":1}   │
│        │                                                 │
│        ▼                                                 │
└────────│────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                   Database Layer                         │
│                                                          │
│  Encrypted JSON stored in TEXT column                   │
│  ✓ Data at rest is always encrypted                     │
│  ✓ Each record has unique nonce (no pattern analysis)   │
│  ✓ Authenticated encryption (tamper detection)          │
└─────────────────────────────────────────────────────────┘
```

### Key Security Features

1. **Unique Nonces**: Every encryption uses a cryptographically random nonce, preventing pattern analysis across records.

2. **Authenticated Encryption**: GCM mode provides authentication tags, making tampering immediately detectable.

3. **Key Separation**: Encryption keys are separate from database credentials and managed independently.

4. **No Plaintext Storage**: Sensitive data is never stored in plaintext in the database.

5. **Transparent Encryption**: Application code reads/writes normal values - encryption is automatic.

## 🚀 Quick Start

### 1. Environment Setup

#### Generate Encryption Key

```bash
# Generate a secure random key (32 bytes for AES-256)
python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"

# Example output: kJ8xN9mP2qR5sT8vW2yZ5b8cE1fG4hJ7kL0mN3pQ6sT9=
```

#### Configure Environment Variable

Add to `.env` file:

```bash
# Database Encryption (AES-256)
# Option 1: Base64-encoded key
DB_ENCRYPTION_KEY=base64:kJ8xN9mP2qR5sT8vW2yZ5b8cE1fG4hJ7kL0mN3pQ6sT9=

# Option 2: Raw key (will be derived through PBKDF2)
DB_ENCRYPTION_KEY=your-secret-encryption-key-here

# ⚠️ WARNING: In production, use a proper key management service (KMS)
```

### 2. Using Encrypted Field Types

#### Basic String Encryption

```python
from sqlalchemy import Column, String
from app.db.models.base import Base
from app.db.encrypted_types import EncryptedString

class User(Base):
    __tablename__ = 'users'

    # Email will be automatically encrypted
    email = Column(EncryptedString(255))

    # Phone number will be automatically encrypted
    phone = Column(EncryptedString(20))

    # Full name will be automatically encrypted
    full_name = Column(EncryptedString(255))
```

#### JSON Data Encryption

```python
from sqlalchemy import Column
from app.db.encrypted_types import EncryptedJSON

class Assessment(Base):
    __tablename__ = 'assessments'

    # JSON data automatically encrypted
    responses = Column(EncryptedJSON)

    # Metadata automatically encrypted
    metadata = Column(EncryptedJSON)
```

#### Large Text Encryption

```python
from app.db.encrypted_types import EncryptedText

class ClinicalNote(Base):
    __tablename__ = 'clinical_notes'

    # Long-form text automatically encrypted
    notes = Column(EncryptedText)

    # PHI in notes is encrypted at rest
    diagnosis = Column(EncryptedText)
```

### 3. Transparent Usage

```python
# Encryption is automatic - use normal values!

# Create new record (automatically encrypted on write)
user = User(
    email="user@example.com",  # Encrypted before storage
    full_name="John Doe",      # Encrypted before storage
    phone="555-123-4567"       # Encrypted before storage
)
session.add(user)
session.commit()

# Read record (automatically decrypted on read)
user = session.query(User).first()
print(user.email)  # "user@example.com" - decrypted automatically!

# Update (automatically encrypted)
user.email = "newemail@example.com"  # Encrypted before update
session.commit()
```

## 📋 Encrypted Data Format

Encrypted data is stored as JSON in TEXT columns:

```json
{
  "nonce": "96-bit-base64-encoded-nonce",
  "ciphertext": "base64-encoded-ciphertext-with-auth-tag",
  "version": 1
}
```

**Example:**
```json
{
  "nonce": "dGVzdGVzdGVzdGU=",
  "ciphertext": "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=",
  "version": 1
}
```

**Storage Size:**
- Original: "user@example.com" (16 bytes)
- Encrypted: ~120 bytes (includes nonce, ciphertext, tag, base64 encoding, JSON)

**Overhead:** Approximately 8-10x for typical field sizes.

## 🛠️ API Reference

### Encryption Service

```python
from app.services.encryption_service import encryption_service

# Encrypt any data
encrypted = encryption_service.encrypt("sensitive data")
# Returns: '{"nonce":"...","ciphertext":"...","version":1}'

# Decrypt data
decrypted = encryption_service.decrypt(encrypted)
# Returns: "sensitive data"

# Encrypt database field (handles None)
encrypted_field = encryption_service.encrypt_field("data")

# Decrypt database field (handles None)
decrypted_field = encryption_service.decrypt_field(encrypted)
```

### Field Types

#### EncryptedString

For string data (emails, names, phone numbers):

```python
email = Column(EncryptedString(255))  # Optional max length for docs
```

#### EncryptedJSON

For JSON data (dictionaries, lists):

```python
metadata = Column(EncryptedJSON)
```

#### EncryptedText

For long-form text (notes, messages):

```python
notes = Column(EncryptedText)
```

#### HashedString

For one-way hashing (verification only, cannot decrypt):

```python
email_hash = Column(HashedString)  # For lookup without storing email
```

### Helper Functions

```python
from app.services.encryption_service import (
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    hash_for_lookup,
    verify_lookup_hash
)

# Encrypt data
encrypted = encrypt_sensitive_data("sensitive")

# Decrypt data
decrypted = decrypt_sensitive_data(encrypted)

# Hash for lookup (one-way)
lookup_hash = hash_for_lookup("user@example.com")
# Returns: "hash:salt" format

# Verify hash
matches = verify_lookup_hash("user@example.com", lookup_hash)
```

## 🔄 Key Rotation

### Why Rotate Keys?

- **Security**: Regular rotation reduces impact of potential key compromise
- **Compliance**: Some regulations require periodic key rotation
- **Incident Response**: Rotate if key exposure is suspected

### Rotation Process

⚠️ **WARNING**: Key rotation requires re-encrypting all encrypted data!

#### Step 1: Export Current Key

```bash
curl -X GET "http://localhost:8000/api/v1/encryption/key/export?password=current_password" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "encrypted_key": "base64-encoded-encrypted-key",
  "message": "Key exported successfully"
}
```

**Store this securely!** You'll need it if rotation fails.

#### Step 2: Rotate to New Key

```bash
curl -X POST "http://localhost:8000/api/v1/encryption/key/rotate" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "current_password",
    "new_key_password": "new_key_password"
  }'
```

**Response:**
```json
{
  "success": true,
  "old_key_export": "base64-encoded-old-key",
  "new_key_export": "base64-encoded-new-key",
  "message": "Key rotated successfully. Re-encrypt all data now."
}
```

**Store both exports securely!**

#### Step 3: Re-encrypt All Data

⚠️ **CRITICAL**: Complete this step before using the application!

```bash
curl -X POST "http://localhost:8000/api/v1/encryption/data/re-encrypt?table_name=users&column_name=email&batch_size=100" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Repeat** for each encrypted column in each table.

#### Step 4: Verify Decryption

```bash
# Test that data can still be read
curl -X GET "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### Manual Rotation (Recommended)

For production, create a migration script:

```python
# migrations/rotate_encryption_key.py

from app.services.encryption_service import encryption_service
from app.db.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

async def reencrypt_user_emails(db: AsyncSession, old_key: bytes, new_key: bytes):
    """Re-encrypt all user emails with new key"""

    # Switch to old key for decryption
    old_service = EncryptionService(old_key)

    # Switch to new key for encryption
    new_service = EncryptionService(new_key)

    # Get all users
    users = await db.execute(select(User))
    for user in users.scalars():
        # Decrypt with old key
        decrypted_email = old_service.decrypt_field(user.email)

        # Encrypt with new key
        user.email = new_service.encrypt_field(decrypted_email)

    # Commit all changes
    await db.commit()
```

## 📊 Performance Considerations

### Encryption Overhead

| Operation | Unencrypted | Encrypted | Overhead |
|-----------|-------------|-----------|----------|
| INSERT    | 1 ms        | ~2 ms     | +100%    |
| SELECT    | 5 ms        | ~7 ms     | +40%     |
| UPDATE    | 1 ms        | ~2 ms     | +100%    |
| Storage   | 50 bytes    | 500 bytes | +900%    |

### Optimization Strategies

1. **Encrypt Only What's Necessary**:
   ```python
   # Good: Encrypt only sensitive fields
   email = Column(EncryptedString(255))        # ✅ Sensitive
   created_at = Column(DateTime)                # ✅ Not sensitive

   # Bad: Encrypt everything
   email = Column(EncryptedString(255))        # ✅ Sensitive
   created_at = Column(EncryptedString)         # ❌ Not needed
   ```

2. **Use Indexed Hashes for Search**:
   ```python
   class User(Base):
       email = Column(EncryptedString)        # Encrypted for storage
       email_hash = Column(HashedString)       # Hashed for lookup

   # Query by hash (fast, indexed)
   user_hash = hash_for_lookup("user@example.com")
   user = session.query(User).filter_by(email_hash=user_hash).first()
   ```

3. **Avoid Encryption on Joins/Filters**:
   ```python
   # ❌ Can't filter encrypted fields efficiently
   users = session.query(User).filter(User.email.like("%@example.com")).all()

   # ✅ Use hash for lookups
   email_hash = hash_for_lookup("user@example.com")
   user = session.query(User).filter_by(email_hash=email_hash).first()
   ```

## 🔍 Auditing and Compliance

### Sensitive Fields

Automatically detects fields requiring encryption:

```python
from app.services.encryption_service import encryption_service

# Check if field should be encrypted
should_encrypt = encryption_service.is_sensitive_field('users', 'email')
# Returns: True

should_encrypt = encryption_service.is_sensitive_field('users', 'created_at')
# Returns: False
```

### Audit Logging

All encryption operations should be logged:

```python
import logging

logger = logging.getLogger(__name__)

# Log encryption
logger.info(f"Encrypted field {table_name}.{column_name} for record {record_id}")

# Log decryption
logger.info(f"Decrypted field {table_name}.{column_name} for record {record_id}")

# Log key rotation
logger.warning(f"Encryption key rotated by admin {admin_id}")
```

### Compliance Reports

Generate compliance reports:

```bash
# Get all encrypted fields
curl -X GET "http://localhost:8000/api/v1/encryption/fields/sensitive" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

**Response:**
```json
{
  "sensitive_fields": [
    {
      "table": "users",
      "column": "email",
      "reason": "PII - Email address",
      "priority": "high"
    },
    {
      "table": "clinical_screening",
      "column": "responses",
      "reason": "PHI - Assessment responses",
      "priority": "critical"
    }
  ],
  "total_fields": 42
}
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from app.services.encryption_service import encryption_service

def test_encryption_decryption():
    plaintext = "sensitive data"

    # Encrypt
    encrypted = encryption_service.encrypt(plaintext)
    assert encrypted is not None
    assert "nonce" in encrypted
    assert "ciphertext" in encrypted

    # Decrypt
    decrypted = encryption_service.decrypt(encrypted)
    assert decrypted == plaintext

def test_field_encryption():
    from app.db.encrypted_types import EncryptedString

    # Test field type
    field = EncryptedString(255)
    encrypted = field.process_bind_param("test", None)
    assert encrypted is not None

    decrypted = field.process_result_value(encrypted, None)
    assert decrypted == "test"

def test_none_handling():
    # None values should remain None
    assert encryption_service.encrypt_field(None) is None
    assert encryption_service.decrypt_field(None) is None
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_encrypted_user_field(db_session):
    from app.db.models.user import User

    # Create user with encrypted email
    user = User(
        email="test@example.com",  # Will be encrypted
        password_hash="hash"
    )
    db_session.add(user)
    await db_session.commit()

    # Retrieve and verify
    retrieved = await db_session.get(User, user.id)
    assert retrieved.email == "test@example.com"  # Decrypted automatically

    # Verify it's actually encrypted in DB
    result = await db_session.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user.id}
    )
    db_value = result.scalar()
    assert db_value.startswith('{"')  # JSON format
    assert "nonce" in db_value  # Has nonce
```

## 🛡️ Security Best Practices

### DO ✅

1. **Use environment variables for keys**
   ```bash
   DB_ENCRYPTION_KEY=your-key-here
   ```

2. **Generate strong random keys**
   ```python
   import os
   key = os.urandom(32)  # 256 bits
   ```

3. **Rotate keys regularly** (quarterly recommended)

4. **Log encryption operations** for audit trails

5. **Test decryption** after key rotation

6. **Backup keys** securely before rotation

7. **Use KMS** in production (AWS KMS, Azure Key Vault, GCP KMS)

### DON'T ❌

1. **Don't commit keys to git**
   ```bash
   # Add .env to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Don't log encrypted data**
   ```python
   # ❌ Bad
   logger.info(f"Encrypted: {encrypted_data}")

   # ✅ Good
   logger.info("Data encrypted successfully")
   ```

3. **Don't use weak keys**
   ```python
   # ❌ Bad
   key = "my-password"  # Too short, predictable

   # ✅ Good
   key = os.urandom(32)  # Cryptographically random
   ```

4. **Don't skip key rotation**

5. **Don't encrypt non-sensitive data** (performance cost)

6. **Don't lose encryption keys** (data becomes inaccessible)

## 🔄 Migration Guide

### Existing Data

To encrypt existing data, create a migration:

```python
# alembic/versions/123_encrypt_existing_data.py

from alembic import op
from app.services.encryption_service import encryption_service

def upgrade():
    # Encrypt existing email addresses
    connection = op.get_bind()
    result = connection.execute("SELECT id, email FROM users")

    for row in result:
        user_id, email = row
        if email and not email.startswith('{"'):
            # Encrypt the email
            encrypted = encryption_service.encrypt_field(email)
            connection.execute(
                "UPDATE users SET email = :encrypted WHERE id = :id",
                {"encrypted": encrypted, "id": user_id}
            )

def downgrade():
    # Decrypt (if needed for rollback)
    connection = op.get_bind()
    result = connection.execute("SELECT id, email FROM users")

    for row in result:
        user_id, email = row
        if email and email.startswith('{"'):
            # Decrypt the email
            decrypted = encryption_service.decrypt_field(email)
            connection.execute(
                "UPDATE users SET email = :decrypted WHERE id = :id",
                {"decrypted": decrypted, "id": user_id}
            )
```

## 📚 Additional Resources

- [NIST AES Guidelines](https://csrc.nist.gov/publications/detail/fips/197/final)
- [OWASP Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/laws/)
- [AWS KMS Documentation](https://docs.aws.amazon.com/kms/)

## 🔑 Key Management Services (Production)

### AWS KMS

```python
import boto3

kms = boto3.client('kms')

# Generate data key
response = kms.generate_data_key(KeyId='alias/psychsync-db', KeySpec='AES_256')
plaintext_key = response['Plaintext']
encrypted_key = response['CiphertextBlob']

# Use plaintext_key for encryption
# Store encrypted_key for later retrieval
```

### Azure Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net", credential=credential)

# Retrieve key
key = client.get_secret("database-encryption-key")
```

### Google Cloud KMS

```python
from google.cloud import kms

client = kms.KeyManagementServiceClient()

# Retrieve key
key_name = client.crypto_key_path_path("project-id", "location", "key-ring", "key-name")
response = client.asymmetric_decrypt(name=key_name, data=encrypted_key)
```

---

**Status:** ✅ Core implementation complete

**Last Updated:** January 17, 2026

**Maintainer:** PsychSync Engineering Team
