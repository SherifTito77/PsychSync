#!/usr/bin/env python3
"""
Test script to debug asyncpg connection issues
"""
import asyncio
import asyncpg

async def test_basic_connection():
    """Test basic asyncpg connection"""
    try:
        print("Testing basic asyncpg connection...")
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="psychsync_user",
            password="C8Vsywo9yXRQSOaGwxjVVQ-Secure9",
            database="psychsync_db",
            server_settings={
                "application_name": "test_connection"
            }
        )
        print("✅ Basic connection successful!")

        # Test a simple query
        result = await conn.fetchval("SELECT 1")
        print(f"✅ Query successful: {result}")

        await conn.close()
        print("✅ Connection closed successfully")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

async def test_with_problematic_settings():
    """Test connection with various server_settings"""
    test_settings = [
        {},  # No settings
        {"application_name": "test"},  # Basic setting
        {"jit": "off"},  # JIT setting
        {"application_name": "test", "jit": "off"},  # Combined
    ]

    for i, settings in enumerate(test_settings):
        try:
            print(f"\nTest {i+1}: Testing with settings: {settings}")
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                user="psychsync_user",
                password="C8Vsywo9yXRQSOaGwxjVVQ-Secure9",
                database="psychsync_db",
                server_settings=settings
            )
            print(f"✅ Test {i+1} successful!")
            await conn.close()

        except Exception as e:
            print(f"❌ Test {i+1} failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_connection())
    asyncio.run(test_with_problematic_settings())