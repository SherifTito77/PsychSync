"""Create pulse survey tables

Revision ID: 20260825_pulse
Revises:
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260825_pulse"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pulse_survey_campaigns",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "frequency", sa.String(20), nullable=False, server_default="biweekly"
        ),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="draft", index=True
        ),
        sa.Column(
            "question_set", sa.String(50), nullable=False, server_default="standard"
        ),
        sa.Column(
            "created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_pulse_campaign_org_status",
        "pulse_survey_campaigns",
        ["organization_id", "status"],
    )

    op.create_table(
        "pulse_survey_responses",
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
        sa.Column(
            "campaign_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pulse_survey_campaigns.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "respondent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("team_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("survey_round", sa.String(50), nullable=True, index=True),
        sa.Column("survey_date", sa.Date, nullable=False, index=True),
        sa.Column("team_health_perception", sa.Numeric(3, 1), nullable=True),
        sa.Column("collaboration_effectiveness", sa.Numeric(3, 1), nullable=True),
        sa.Column("manager_support", sa.Numeric(3, 1), nullable=True),
        sa.Column("psychological_safety", sa.Numeric(3, 1), nullable=True),
        sa.Column("workload_balance", sa.Numeric(3, 1), nullable=True),
        sa.Column("engagement_level", sa.Numeric(3, 1), nullable=True),
        sa.Column("burnout_felt", sa.Numeric(3, 1), nullable=True),
        sa.Column("change_readiness", sa.Numeric(3, 1), nullable=True),
        sa.Column("biggest_challenge", sa.Text, nullable=True),
        sa.Column("response_time_seconds", sa.Integer, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_pulse_resp_org_date",
        "pulse_survey_responses",
        ["organization_id", "survey_date"],
    )
    op.create_index(
        "idx_pulse_resp_team_date", "pulse_survey_responses", ["team_id", "survey_date"]
    )
    op.create_index(
        "idx_pulse_resp_round",
        "pulse_survey_responses",
        ["organization_id", "survey_round"],
    )
    op.create_index(
        "idx_pulse_resp_user",
        "pulse_survey_responses",
        ["respondent_id", "survey_date"],
    )


def downgrade():
    op.drop_table("pulse_survey_responses")
    op.drop_table("pulse_survey_campaigns")
