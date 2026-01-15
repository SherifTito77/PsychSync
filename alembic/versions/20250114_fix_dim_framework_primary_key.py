"""Fix dim_framework primary key constraint

Revision ID: 20250114_fix_framework_pk
Revises:
Create Date: 2025-01-14

This migration fixes the DimFramework table which incorrectly had two primary keys.
The framework_key column should be a unique UUID surrogate key, while framework_code
is the natural key and primary key referenced by foreign keys in other tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250114_fix_framework_pk'
down_revision = None  # Standalone migration due to branched history
branch_labels = None
depends_on = None


def upgrade():
    """Fix the DimFramework primary key constraint.

    This requires dropping the incorrect dual primary key setup and recreating
    the table with the correct schema where framework_code is the primary key
    and framework_key is a unique UUID column.
    """

    # Check if dim_framework table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'dim_framework' not in tables:
        # Table doesn't exist yet, will be created by other migrations
        return

    # Get existing data to preserve it
    conn.execute(sa.text("""
        CREATE TEMP TABLE dim_framework_backup AS
        SELECT * FROM dim_framework
    """))

    # Drop foreign key constraints that reference dim_framework
    try:
        conn.execute(sa.text("""
            ALTER TABLE fact_assessment_completion
            DROP CONSTRAINT IF EXISTS fact_assessment_completion_framework_key_fkey
        """))
    except Exception:
        pass

    try:
        conn.execute(sa.text("""
            ALTER TABLE fact_assessment_completion
            DROP CONSTRAINT fact_assessment_completion_framework_key_fkey
        """))
    except Exception:
        pass

    # Drop the old table
    conn.execute(sa.text("DROP TABLE dim_framework CASCADE"))

    # Recreate with correct schema
    conn.execute(sa.text("""
        CREATE TABLE dim_framework (
            framework_key UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
            framework_code VARCHAR(50) NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            category VARCHAR(50),
            version VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # Restore data
    conn.execute(sa.text("""
        INSERT INTO dim_framework (
            framework_key, framework_code, name, description, category,
            version, is_active, created_at, updated_at
        )
        SELECT
            framework_key, framework_code, name, description, category,
            version, is_active, created_at, updated_at
        FROM dim_framework_backup
    """))

    # Drop backup table
    conn.execute(sa.text("DROP TABLE dim_framework_backup"))

    # Recreate foreign key constraint
    conn.execute(sa.text("""
        ALTER TABLE fact_assessment_completion
        ADD CONSTRAINT fact_assessment_completion_framework_key_fkey
        FOREIGN KEY (framework_key) REFERENCES dim_framework(framework_code)
    """))

    # Add comment
    conn.execute(sa.text("""
        COMMENT ON TABLE dim_framework IS
        'Dimension table for assessment frameworks (Big Five, MBTI, etc.)'
    """))


def downgrade():
    """Revert the schema change."""

    # Get existing data
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TEMP TABLE dim_framework_backup AS
        SELECT * FROM dim_framework
    """))

    # Drop foreign key
    conn.execute(sa.text("""
        ALTER TABLE fact_assessment_completion
        DROP CONSTRAINT IF EXISTS fact_assessment_completion_framework_key_fkey
    """))

    # Drop table
    conn.execute(sa.text("DROP TABLE dim_framework CASCADE"))

    # Recreate old (incorrect) schema
    conn.execute(sa.text("""
        CREATE TABLE dim_framework (
            framework_key UUID DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
            framework_code VARCHAR(50) NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            category VARCHAR(50),
            version VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # Restore data
    conn.execute(sa.text("""
        INSERT INTO dim_framework (
            framework_key, framework_code, name, description, category,
            version, is_active, created_at, updated_at
        )
        SELECT
            framework_key, framework_code, name, description, category,
            version, is_active, created_at, updated_at
        FROM dim_framework_backup
    """))

    conn.execute(sa.text("DROP TABLE dim_framework_backup"))

    # Recreate foreign key
    conn.execute(sa.text("""
        ALTER TABLE fact_assessment_completion
        ADD CONSTRAINT fact_assessment_completion_framework_key_fkey
        FOREIGN KEY (framework_key) REFERENCES dim_framework(framework_code)
    """))
