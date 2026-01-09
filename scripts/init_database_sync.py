#!/usr/bin/env python3
"""
Synchronous Database Initialization
Creates database schema using SQLAlchemy with sync engine
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.core.database import Base
from app.core.config import settings


def init_database():
    """Initialize database with all tables"""
    print("🚀 Synchronous Database Initialization")
    print("=" * 70)
    print()

    # Create sync engine (replace asyncpg with psycopg2)
    database_url = str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(database_url, echo=False)

    try:
        print("Step 1: Dropping existing tables (if any)...")
        Base.metadata.drop_all(engine)
        print("✅ Dropped existing tables")
        print()

        print("Step 2: Creating all tables...")
        Base.metadata.create_all(engine)
        print("✅ Tables created successfully!")
        print()

        # List created tables
        print("Step 3: Verifying created tables...")
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT LIKE 'alembic%'
                ORDER BY tablename;
            """))
            tables = [row[0] for row in result]

            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")

        print()
        print("=" * 70)
        print("✅ Database initialization complete!")
        print("=" * 70)
        print()
        print("Database ready for regression tests!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(init_database())
