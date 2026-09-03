#!/usr/bin/env python3
"""
Stamp Alembic Version
Creates an entry in alembic_version to track schema state
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

from app.core.config import settings


def stamp_alembic(version="001_base_tables"):
    """Stamp alembic version table"""
    print(f"📝 Stamping Alembic Version: {version}")
    print("=" * 70)

    # Create sync engine
    database_url = str(settings.DATABASE_URL)
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                );
            """
                )
            )
            exists = result.scalar()

            if not exists:
                print("Creating alembic_version table...")
                conn.execute(
                    text(
                        """
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(255) NOT NULL PRIMARY KEY
                    );
                """
                    )
                )
                conn.commit()
                print("✅ Table created")
            else:
                print("✅ alembic_version table exists")

            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version;"))
            current = result.scalar()

            if current:
                print(f"Current version: {current}")
                response = input(f"Update to {version}? (yes/no): ")
                if response.lower() != "yes":
                    print("Cancelled")
                    return 0
            else:
                print("No current version")

            # Update version
            conn.execute(
                text(
                    """
                INSERT INTO alembic_version (version_num)
                VALUES (:version)
                ON CONFLICT (version_num) DO UPDATE
                SET version_num = EXCLUDED.version_num;
            """
                ),
                {"version": version},
            )
            conn.commit()

            print(f"✅ Stamped as: {version}")

            # Verify
            result = conn.execute(text("SELECT version_num FROM alembic_version;"))
            stamped = result.scalar()
            print(f"Verified: {stamped}")

        print()
        print("=" * 70)
        print("✅ Alembic version stamped successfully!")
        print("=" * 70)
        print()
        print("You can now run:")
        print("  alembic current")
        print("  pytest tests/api/test_regression*.py -v")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        engine.dispose()

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stamp Alembic version")
    parser.add_argument(
        "--version",
        default="001_base_tables",
        help="Version to stamp (default: 001_base_tables)",
    )
    args = parser.parse_args()

    sys.exit(stamp_alembic(args.version))
