"""Create pulse_snapshots table for Organizational Pulse Engine

Stores point-in-time predictive intelligence snapshots answering
7 key organizational questions with early warnings and interventions.

Revision ID: 20260824_pulse_snapshots
Revises: None (standalone - branched migration history)
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

revision: str = "20260824_pulse_snapshots"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pulse_snapshots",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "overall_pulse_score", sa.Float(), nullable=False, server_default="50.0"
        ),
        sa.Column(
            "overall_trend", sa.String(20), nullable=False, server_default="'stable'"
        ),
        sa.Column(
            "total_teams_analyzed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("teams_at_risk", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_alerts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "interventions_recommended",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("isolated_teams", sa.JSON(), nullable=True),
        sa.Column("manager_burnout_signals", sa.JSON(), nullable=True),
        sa.Column("collaboration_effectiveness", sa.JSON(), nullable=True),
        sa.Column("friction_trends", sa.JSON(), nullable=True),
        sa.Column("flight_risk_teams", sa.JSON(), nullable=True),
        sa.Column("change_impact_predictions", sa.JSON(), nullable=True),
        sa.Column("proactive_interventions", sa.JSON(), nullable=True),
        sa.Column("early_warnings", sa.JSON(), nullable=True),
        sa.Column("predictions", sa.JSON(), nullable=True),
        sa.Column("computation_time_ms", sa.Integer(), nullable=True),
        sa.Column("data_sources_used", sa.JSON(), nullable=True),
        sa.Column("is_scheduled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Organizational pulse snapshots for predictive intelligence",
    )

    # Unique constraint: one pulse per org per day
    op.create_unique_constraint(
        "uq_pulse_snapshot_date",
        "pulse_snapshots",
        ["organization_id", "snapshot_date"],
    )

    # Indexes
    op.create_index(
        "idx_pulse_org_date", "pulse_snapshots", ["organization_id", "snapshot_date"]
    )
    op.create_index(
        "idx_pulse_risk", "pulse_snapshots", ["organization_id", "teams_at_risk"]
    )


def downgrade() -> None:
    op.drop_index("idx_pulse_risk", table_name="pulse_snapshots")
    op.drop_index("idx_pulse_org_date", table_name="pulse_snapshots")
    op.drop_constraint("uq_pulse_snapshot_date", "pulse_snapshots", type_="unique")
    op.drop_table("pulse_snapshots")
