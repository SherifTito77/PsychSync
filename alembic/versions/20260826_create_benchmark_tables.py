"""Create external benchmark tables

Revision ID: 20260826_bench
Revises: 20260826_meetings
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260826_bench"
down_revision = "20260826_meetings"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "benchmark_opt_ins",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("opted_in", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("company_size", sa.String(20), nullable=True),
        sa.Column("maturity_stage", sa.String(20), nullable=True),
        sa.Column("opted_in_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("opted_out_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "benchmark_contributions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("industry", sa.String(100), nullable=True, index=True),
        sa.Column("company_size", sa.String(20), nullable=True, index=True),
        sa.Column("maturity_stage", sa.String(20), nullable=True, index=True),
        sa.Column("team_health", sa.Numeric(5, 1), nullable=True),
        sa.Column("collaboration", sa.Numeric(5, 1), nullable=True),
        sa.Column("manager_health", sa.Numeric(5, 1), nullable=True),
        sa.Column("psychological_safety", sa.Numeric(5, 1), nullable=True),
        sa.Column("change_readiness", sa.Numeric(5, 1), nullable=True),
        sa.Column("friction_index", sa.Numeric(5, 1), nullable=True),
        sa.Column("burnout_risk", sa.Numeric(5, 1), nullable=True),
        sa.Column("team_count", sa.Integer, nullable=True),
        sa.Column("employee_count", sa.Integer, nullable=True),
        sa.Column("contribution_period", sa.String(10), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_bench_industry_size",
        "benchmark_contributions",
        ["industry", "company_size"],
    )
    op.create_index(
        "idx_bench_org_period",
        "benchmark_contributions",
        ["organization_id", "contribution_period"],
    )


def downgrade():
    op.drop_table("benchmark_contributions")
    op.drop_table("benchmark_opt_ins")
