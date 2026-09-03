"""Create toxicity_burnout_snapshots and toxicity_burnout_alerts tables

Revision ID: 20260829_toxburn
Revises: 20260826_bench
Create Date: 2026-08-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260829_toxburn"
down_revision = "20260826_bench"
branch_labels = None
depends_on = None


def upgrade():
    # Composite snapshots table
    op.create_table(
        "toxicity_burnout_snapshots",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("team_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("snapshot_date", sa.Date, nullable=False, index=True),
        sa.Column(
            "scope", sa.String(20), nullable=False, server_default="organization"
        ),
        # Scores
        sa.Column("burnout_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("toxicity_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("combined_risk", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "cross_contamination_multiplier",
            sa.Float,
            nullable=False,
            server_default="1.0",
        ),
        # Labels
        sa.Column(
            "burnout_label", sa.String(20), nullable=False, server_default="Healthy"
        ),
        sa.Column(
            "toxicity_label", sa.String(20), nullable=False, server_default="Healthy"
        ),
        sa.Column(
            "combined_label", sa.String(20), nullable=False, server_default="Healthy"
        ),
        # Signal breakdowns
        sa.Column("burnout_signals", sa.JSON, nullable=True),
        sa.Column("toxicity_signals", sa.JSON, nullable=True),
        sa.Column(
            "active_burnout_sources", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column(
            "active_toxicity_sources", sa.Integer, nullable=False, server_default="0"
        ),
        # Patterns
        sa.Column("overlap_patterns", sa.JSON, nullable=True),
        sa.Column("recommendations", sa.JSON, nullable=True),
        sa.Column("data_sources", sa.JSON, nullable=True),
        # Metadata
        sa.Column("computation_time_ms", sa.Integer, nullable=True),
        sa.Column("is_scheduled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_tb_org_date",
        "toxicity_burnout_snapshots",
        ["organization_id", "snapshot_date"],
    )
    op.create_index(
        "idx_tb_team_date", "toxicity_burnout_snapshots", ["team_id", "snapshot_date"]
    )
    op.create_index(
        "idx_tb_risk",
        "toxicity_burnout_snapshots",
        ["organization_id", "combined_risk"],
    )
    op.create_index(
        "idx_tb_scope", "toxicity_burnout_snapshots", ["scope", "snapshot_date"]
    )

    # Alerts table
    op.create_table(
        "toxicity_burnout_alerts",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("team_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("snapshot_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            server_default="medium",
            index=True,
        ),
        sa.Column("alert_type", sa.String(100), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=False),
        # Scores at alert time
        sa.Column("burnout_score_at_alert", sa.Float, nullable=True),
        sa.Column("toxicity_score_at_alert", sa.Float, nullable=True),
        sa.Column("combined_risk_at_alert", sa.Float, nullable=True),
        # Resolution
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("resolved_by", UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_tba_org_severity",
        "toxicity_burnout_alerts",
        ["organization_id", "severity"],
    )
    op.create_index(
        "idx_tba_unresolved",
        "toxicity_burnout_alerts",
        ["organization_id", "is_resolved"],
    )
    op.create_index(
        "idx_tba_type", "toxicity_burnout_alerts", ["alert_type", "created_at"]
    )


def downgrade():
    op.drop_table("toxicity_burnout_alerts")
    op.drop_table("toxicity_burnout_snapshots")
