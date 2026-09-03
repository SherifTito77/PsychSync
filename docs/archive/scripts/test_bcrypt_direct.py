#!/usr/bin/env python3
import bcrypt

# Test bcrypt hashing and verification
test_password = "test123"

# Create hash
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(test_password.encode("utf-8"), salt)
hash_str = hashed.decode("utf-8") if isinstance(hashed, bytes) else hashed
print(f"Hash: {hash_str}")

# Verify - hashed needs to be bytes
hashed_bytes = hash_str.encode("utf-8") if isinstance(hash_str, str) else hash_str
try:
    is_valid = bcrypt.checkpw(test_password.encode("utf-8"), hashed_bytes)
    print(f"Password valid: {is_valid}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
