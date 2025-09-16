"""create extensions and triggers

Revision ID: 0001
Revises: 
Create Date: 2025-09-10 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable useful extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")

    # Create updated_at trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;$$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS set_updated_at() CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS citext;")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
