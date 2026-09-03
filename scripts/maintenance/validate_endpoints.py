#!/usr/bin/env python3
"""
API Endpoint Integrity Validator
Checks for orphaned endpoint files not registered in api.py
"""

import os
import re


def validate_endpoints():
    api_file = "app/api/v1/api.py"
    endpoints_dir = "app/api/v1/endpoints/"

    with open(api_file, "r") as f:
        content = f.read()

    # Extract all imported router modules
    registered_modules = re.findall(
        r"from app\.api\.v1\.endpoints import \((.*?)\)", content, re.DOTALL
    )
    if registered_modules:
        registered = [m.strip() for m in registered_modules[0].split(",")]
    else:
        # Fallback for simple imports
        registered = re.findall(
            r"import app\.api\.v1\.endpoints\.(.*?)$", content, re.MULTILINE
        )

    # Get all python files in endpoints directory
    all_files = [
        f.replace(".py", "")
        for f in os.listdir(endpoints_dir)
        if f.endswith(".py") and f != "__init__.py"
    ]

    orphaned = [f for f in all_files if f not in registered]

    if orphaned:
        print(f"⚠️ Found {len(orphaned)} potentially orphaned endpoint files:")
        for f in orphaned:
            print(f"  - {f}.py")
    else:
        print("✅ All endpoint files are registered in api.py")


if __name__ == "__main__":
    validate_endpoints()
