"""Create OKR tables: objectives, key_results, kr_progress_updates,
initiatives, okr_check_ins, okr_retrospectives

Revision ID: 20260830_okr
Revises: 20260829_toxburn
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260830_okr"
down_revision = "20260829_toxburn"
branch_labels = None
depends_on = None


def upgrade():
    # Objectives table
    op.create_table(
        "objectives",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("objective_type", sa.String(50), nullable=False),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column(
            "owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("team", sa.String(100), nullable=True),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("progress_percentage", sa.Float, server_default="0"),
        sa.Column(
            "parent_objective_id",
            UUID(as_uuid=True),
            sa.ForeignKey("objectives.id"),
            nullable=True,
        ),
        sa.Column("strategic_priority", sa.String(50), nullable=True),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("outcome_summary", sa.Text, nullable=True),
        sa.Column("health_risk_flag", sa.String(20), nullable=True),
        sa.Column("health_risk_signals", sa.JSON, nullable=True),
        sa.Column("health_risk_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("context", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_objectives_org", "objectives", ["organization_id"])
    op.create_index("ix_objectives_tenant", "objectives", ["tenant_id"])
    op.create_index("ix_objectives_owner", "objectives", ["owner_id"])
    op.create_index("idx_objectives_period_year", "objectives", ["period", "year"])
    op.create_index("idx_objectives_status", "objectives", ["status"])
    op.create_index("idx_objectives_team", "objectives", ["team"])
    op.create_index("ix_objectives_health_risk", "objectives", ["health_risk_flag"])

    # Key Results table
    op.create_table(
        "key_results",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "objective_id",
            UUID(as_uuid=True),
            sa.ForeignKey("objectives.id"),
            nullable=False,
        ),
        sa.Column(
            "owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("target_value", sa.Float, nullable=False),
        sa.Column("current_value", sa.Float, server_default="0"),
        sa.Column("unit_of_measure", sa.String(50), nullable=True),
        sa.Column("baseline_value", sa.Float, nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="not_started"
        ),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("weight", sa.Float, server_default="1.0"),
        sa.Column("progress_percentage", sa.Float, server_default="0"),
        sa.Column("final_value", sa.Float, nullable=True),
        sa.Column("outcome_summary", sa.Text, nullable=True),
        sa.Column("depends_on_kr_ids", sa.JSON, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("context", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_key_results_objective", "key_results", ["objective_id"])
    op.create_index("idx_key_results_status", "key_results", ["status"])
    op.create_index("idx_key_results_owner", "key_results", ["owner_id"])

    # KR Progress Updates table
    op.create_table(
        "kr_progress_updates",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "key_result_id",
            UUID(as_uuid=True),
            sa.ForeignKey("key_results.id"),
            nullable=False,
        ),
        sa.Column(
            "updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("current_value", sa.Float, nullable=False),
        sa.Column("progress_percentage", sa.Float, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("blockers", sa.Text, nullable=True),
        sa.Column("next_steps", sa.Text, nullable=True),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column(
            "update_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_kr_updates_kr", "kr_progress_updates", ["key_result_id"])
    op.create_index(
        "idx_kr_updates_kr_date",
        "kr_progress_updates",
        ["key_result_id", "update_date"],
    )

    # Initiatives table
    op.create_table(
        "initiatives",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "key_result_id",
            UUID(as_uuid=True),
            sa.ForeignKey("key_results.id"),
            nullable=False,
        ),
        sa.Column(
            "owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("planned_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="not_started"
        ),
        sa.Column("completion_percentage", sa.Integer, server_default="0"),
        sa.Column("depends_on_initiative_ids", sa.JSON, nullable=True),
        sa.Column("estimated_hours", sa.Integer, nullable=True),
        sa.Column("actual_hours", sa.Integer, nullable=True),
        sa.Column("outcome_summary", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("context", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_initiatives_kr", "initiatives", ["key_result_id"])
    op.create_index("idx_initiatives_status", "initiatives", ["status"])
    op.create_index(
        "idx_initiatives_dates",
        "initiatives",
        ["planned_start_date", "planned_end_date"],
    )

    # OKR Check-Ins table
    op.create_table(
        "okr_check_ins",
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
            nullable=True,
        ),
        sa.Column("team", sa.String(100), nullable=False),
        sa.Column("meeting_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meeting_type", sa.String(50), nullable=False),
        sa.Column("attendee_ids", sa.JSON, nullable=False),
        sa.Column("agenda_items", sa.JSON, nullable=True),
        sa.Column("discussions", sa.JSON, nullable=True),
        sa.Column("decisions_made", sa.Text, nullable=True),
        sa.Column("action_items", sa.JSON, nullable=True),
        sa.Column("objectives_reviewed", sa.JSON, nullable=True),
        sa.Column("overall_health", sa.String(20), nullable=True),
        sa.Column("next_check_in_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_okr_checkins_org", "okr_check_ins", ["organization_id"])
    op.create_index("ix_okr_checkins_team", "okr_check_ins", ["team"])
    op.create_index("ix_okr_checkins_date", "okr_check_ins", ["meeting_date"])
    op.create_index(
        "idx_okr_checkins_team_date", "okr_check_ins", ["team", "meeting_date"]
    )

    # OKR Retrospectives table
    op.create_table(
        "okr_retrospectives",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("team", sa.String(100), nullable=False),
        sa.Column("overall_performance_rating", sa.String(20), nullable=False),
        sa.Column("objectives_achieved", sa.Integer, server_default="0"),
        sa.Column("total_objectives", sa.Integer, server_default="0"),
        sa.Column("key_results_achieved", sa.Integer, server_default="0"),
        sa.Column("total_key_results", sa.Integer, server_default="0"),
        sa.Column("successes", sa.Text, nullable=True),
        sa.Column("lessons_learned", sa.Text, nullable=True),
        sa.Column("failures", sa.Text, nullable=True),
        sa.Column("challenges", sa.Text, nullable=True),
        sa.Column("improvement_commitments", sa.JSON, nullable=True),
        sa.Column("participant_sentiment", sa.String(20), nullable=True),
        sa.Column("anonymous_feedback", sa.JSON, nullable=True),
        sa.Column(
            "facilitated_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("retrospective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_okr_retros_team", "okr_retrospectives", ["team"])
    op.create_index(
        "idx_okr_retros_period_year", "okr_retrospectives", ["period", "year"]
    )


def downgrade():
    op.drop_table("okr_retrospectives")
    op.drop_table("okr_check_ins")
    op.drop_table("initiatives")
    op.drop_table("kr_progress_updates")
    op.drop_table("key_results")
    op.drop_table("objectives")
