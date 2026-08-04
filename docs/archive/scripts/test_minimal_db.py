#!/usr/bin/env python3
"""
Test minimal database configuration
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database_minimal import test_connection


async def main():
    print("Testing minimal database configuration...")
    success = await test_connection()
    if success:
        print("✅ Database configuration works!")
    else:
        print("❌ Database configuration failed!")


if __name__ == "__main__":
    asyncio.run(main())
