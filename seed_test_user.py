#!/usr/bin/env python3
"""
Seed script to create a test user.
This version is asynchronous to work with asyncpg.
Run with: python seed_test_user.py
"""
import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# --- Add the project root to the Python path ---
# This allows us to import from the 'app' directory
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# --- Now we can import from our app ---
from app.core.security import get_password_hash
from app.core.config import settings

async def create_test_user():
    """Create a test user: testme@gmail.com / Testme@123"""
    
    # The DATABASE_URL should be the async one, e.g., "postgresql+asyncpg://..."
    DATABASE_URL = settings.DATABASE_URL
    
    # Check if the URL is for asyncpg, if not, we can't proceed.
    if "asyncpg" not in DATABASE_URL:
        print("✗ Error: DATABASE_URL is not configured for asyncpg.")
        print("  Please ensure your DATABASE_URL in .env starts with 'postgresql+asyncpg://'")
        return

    print(f"✓ Connecting to database...")
    
    try:
        # Create an async engine
        engine = create_async_engine(DATABASE_URL, echo=False) # Set echo=True to see SQL queries
        
        # Create a configured "Session" class
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            async with session.begin():
                # First, delete any existing user with this email
                await session.execute(
                    text("DELETE FROM users WHERE email = :email"),
                    {"email": "testme@gmail.com"}
                )
                print("✓ Cleared any existing test user")
                
                # Define the password
                password = "Testme@123"
                
                # Use the centralized get_password_hash function
                hashed_password = get_password_hash(password)
                
                print(f"✓ Password hashed successfully.")
                
                # Insert new user
                result = await session.execute(
                    text("""
                        INSERT INTO users (email, password_hash, full_name, is_active)
                        VALUES (:email, :password_hash, :full_name, :is_active)
                        RETURNING id, email
                    """),
                    {
                        "email": "testme@gmail.com",
                        "password_hash": hashed_password,
                        "full_name": "Test User",
                        "is_active": True
                    }
                )
                
                user = result.fetchone()
                
                # The commit is handled by the `async with session.begin():` context manager
                print("✓ Test user created successfully!")
                print(f"  Email: {user[1]}")
                print(f"  Password: Testme@123")
                print(f"  User ID: {user[0]}")
                print(f"\n✓ You can now login at: http://localhost:5173/login")

    except Exception as e:
        print(f"✗ Error creating test user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Use asyncio.run to execute the async function
    asyncio.run(create_test_user())