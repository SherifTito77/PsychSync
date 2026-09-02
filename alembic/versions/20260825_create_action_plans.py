"""Create action_plans table

Revision ID: 20260825_actions
Revises: 20260825_pulse
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260825_actions"
down_revision = "20260825_pulse"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "action_plans",
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
        sa.Column("team_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("source", sa.String(50), nullable=False, index=True),
        sa.Column("source_reference_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), nullable=True, index=True),
        sa.Column(
            "priority",
            sa.String(20),
            nullable=False,
            server_default="medium",
            index=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="proposed",
            index=True,
        ),
        sa.Column("due_date", sa.Date, nullable=True, index=True),
        sa.Column("accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("related_metric", sa.String(50), nullable=True),
        sa.Column("metric_before", sa.Numeric(5, 1), nullable=True),
        sa.Column("metric_after", sa.Numeric(5, 1), nullable=True),
        sa.Column("outcome_notes", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("idx_action_owner_status", "action_plans", ["owner_id", "status"])
    op.create_index(
        "idx_action_org_status", "action_plans", ["organization_id", "status"]
    )
    op.create_index("idx_action_source", "action_plans", ["source", "created_at"])
    op.create_index("idx_action_due", "action_plans", ["due_date", "status"])
    op.create_index("idx_action_team", "action_plans", ["team_id", "status"])


def downgrade():
    op.drop_table("action_plans")
