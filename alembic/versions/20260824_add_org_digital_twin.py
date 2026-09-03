"""Add org digital twin snapshots

Revision ID: 20260824_org_twin
Revises: None (standalone — apply after fixing alembic heads)
Create Date: 2026-08-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_org_twin"
down_revision = "20260823_ona_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "org_digital_twin_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "computed_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "overall_health_score", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column(
            "overall_trend", sa.String(20), nullable=False, server_default="'stable'"
        ),
        sa.Column("teams_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("managers_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "collaboration_score", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("performance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "turnover_risk_score", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("culture_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("state", postgresql.JSON(), nullable=False, server_default="'{}'"),
        sa.Column(
            "is_simulation", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("simulation_params", postgresql.JSON(), nullable=True),
        sa.Column(
            "data_sources", postgresql.JSON(), nullable=False, server_default="'{}'"
        ),
    )

    op.create_index(
        "ix_org_twin_org_id",
        "org_digital_twin_snapshots",
        ["organization_id"],
    )
    op.create_index(
        "ix_org_twin_computed_at",
        "org_digital_twin_snapshots",
        ["computed_at"],
    )
    op.create_index(
        "ix_org_twin_org_computed",
        "org_digital_twin_snapshots",
        ["organization_id", "computed_at"],
    )
    op.create_index(
        "ix_org_twin_org_version",
        "org_digital_twin_snapshots",
        ["organization_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("org_digital_twin_snapshots")
