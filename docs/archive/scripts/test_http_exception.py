#!/usr/bin/env python3
from fastapi import HTTPException, status

try:
    # Simulate the exception raising
    raise HTTPException(status_code=401, detail="Invalid credentials")
except HTTPException as e:
    print(f"HTTPException caught: status={e.status_code}, detail={e.detail}")
    print(f"Type: {type(e)}")
