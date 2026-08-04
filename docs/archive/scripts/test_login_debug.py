#!/usr/bin/env python3
import asyncio

import bcrypt

# Simulate the login process
test_password = "test123"

# Test with a valid bcrypt hash (for "test123")
# Generated using bcrypt.hashpw()
test_hash = "$2b$12$bKEnsMuNKXueVJjNVdQ4MOcyx0OwRxlcaI.2biMK2mG"
print(f"Testing password '{test_password}' against hash...")
print(f"Hash: {test_hash}")

try:
    is_valid = bcrypt.checkpw(test_password.encode("utf-8"), test_hash.encode("utf-8"))
    print(f"Password valid: {is_valid}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
