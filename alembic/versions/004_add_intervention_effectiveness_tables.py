"""Add intervention effectiveness tracking tables

Revision ID: 004_add_intervention_effectiveness_tables
Revises: 001_base_tables
Create Date: 2025-11-16 14:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_intervention_effectiveness_tables"
down_revision: Union[str, None] = "e54429b44d1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create intervention effectiveness tracking tables"""

    # Interventions table - stores intervention definitions
    op.create_table(
        "interventions",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("team_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("intervention_type", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("target_metrics", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="planned"
        ),
        sa.Column(
            "priority", sa.String(length=20), nullable=False, server_default="medium"
        ),
        sa.Column("budget", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("participants_target", sa.Integer(), nullable=True),
        sa.Column("actual_participants", sa.Integer(), nullable=True),
        sa.Column("expected_outcomes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "success_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "implementation_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("external_references", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_date >= start_date", name="check_intervention_dates"),
        sa.CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'cancelled', 'paused')",
            name="check_intervention_status",
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="check_intervention_priority",
        ),
    )
    op.create_index(op.f("ix_interventions_id"), "interventions", ["id"], unique=False)
    op.create_index(
        "ix_interventions_organization",
        "interventions",
        ["organization_id"],
        unique=False,
    )
    op.create_index("ix_interventions_team", "interventions", ["team_id"], unique=False)
    op.create_index(
        "ix_interventions_status", "interventions", ["status"], unique=False
    )
    op.create_index(
        "ix_interventions_dates",
        "interventions",
        ["start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        "ix_interventions_type_category",
        "interventions",
        ["intervention_type", "category"],
        unique=False,
    )

    # Intervention participants table - tracks who participated in each intervention
    op.create_table(
        "intervention_participants",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("intervention_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "participant_role",
            sa.String(length=50),
            nullable=False,
            server_default="participant",
        ),
        sa.Column(
            "enrollment_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("participation_level", sa.String(length=20), nullable=True),
        sa.Column("engagement_score", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("attendance_rate", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column(
            "completion_status",
            sa.String(length=20),
            nullable=False,
            server_default="enrolled",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "custom_attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
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
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["interventions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "completion_status IN ('enrolled', 'active', 'completed', 'dropped', 'withdrawn')",
            name="check_participant_status",
        ),
        sa.CheckConstraint(
            "participation_level IN ('low', 'medium', 'high', 'very_high')",
            name="check_participation_level",
        ),
    )
    op.create_index(
        op.f("ix_intervention_participants_id"),
        "intervention_participants",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_participants_intervention",
        "intervention_participants",
        ["intervention_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_participants_user",
        "intervention_participants",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_participants_status",
        "intervention_participants",
        ["completion_status"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_participants_dates",
        "intervention_participants",
        ["enrollment_date", "completion_date"],
        unique=False,
    )

    # Pre-intervention measurements table
    op.create_table(
        "pre_intervention_measurements",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("intervention_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("measurement_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("baseline_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("baseline_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("measurement_method", sa.String(length=100), nullable=True),
        sa.Column("data_source", sa.String(length=100), nullable=True),
        sa.Column("confidence_level", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("statistical_notes", sa.Text(), nullable=True),
        sa.Column("qualitative_notes", sa.Text(), nullable=True),
        sa.Column(
            "baseline_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["interventions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pre_intervention_measurements_id"),
        "pre_intervention_measurements",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_pre_intervention_measurements_intervention",
        "pre_intervention_measurements",
        ["intervention_id"],
        unique=False,
    )
    op.create_index(
        "ix_pre_intervention_measurements_user",
        "pre_intervention_measurements",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_pre_intervention_measurements_metric",
        "pre_intervention_measurements",
        ["metric_name"],
        unique=False,
    )
    op.create_index(
        "ix_pre_intervention_measurements_date",
        "pre_intervention_measurements",
        ["measurement_date"],
        unique=False,
    )

    # Post-intervention measurements table
    op.create_table(
        "post_intervention_measurements",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("intervention_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("measurement_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("follow_up_period_days", sa.Integer(), nullable=True),
        sa.Column("measurement_method", sa.String(length=100), nullable=True),
        sa.Column("data_source", sa.String(length=100), nullable=True),
        sa.Column("confidence_level", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("statistical_notes", sa.Text(), nullable=True),
        sa.Column("qualitative_notes", sa.Text(), nullable=True),
        sa.Column(
            "sustainability_indicators",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["interventions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_post_intervention_measurements_id"),
        "post_intervention_measurements",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_post_intervention_measurements_intervention",
        "post_intervention_measurements",
        ["intervention_id"],
        unique=False,
    )
    op.create_index(
        "ix_post_intervention_measurements_user",
        "post_intervention_measurements",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_post_intervention_measurements_metric",
        "post_intervention_measurements",
        ["metric_name"],
        unique=False,
    )
    op.create_index(
        "ix_post_intervention_measurements_date",
        "post_intervention_measurements",
        ["measurement_date"],
        unique=False,
    )

    # Intervention effectiveness analysis table
    op.create_table(
        "intervention_effectiveness",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("intervention_id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("effect_size", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column(
            "confidence_interval_lower",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
        ),
        sa.Column(
            "confidence_interval_upper",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
        ),
        sa.Column("p_value", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("statistical_significance", sa.Boolean(), nullable=True),
        sa.Column("test_type", sa.String(length=100), nullable=False),
        sa.Column("sample_size_pre", sa.Integer(), nullable=True),
        sa.Column("sample_size_post", sa.Integer(), nullable=True),
        sa.Column(
            "pre_intervention_mean", sa.Numeric(precision=10, scale=4), nullable=True
        ),
        sa.Column(
            "post_intervention_mean", sa.Numeric(precision=10, scale=4), nullable=True
        ),
        sa.Column(
            "pre_intervention_std", sa.Numeric(precision=10, scale=4), nullable=True
        ),
        sa.Column(
            "post_intervention_std", sa.Numeric(precision=10, scale=4), nullable=True
        ),
        sa.Column(
            "percent_improvement", sa.Numeric(precision=5, scale=2), nullable=True
        ),
        sa.Column("clinical_significance", sa.String(length=20), nullable=True),
        sa.Column("practical_significance", sa.Boolean(), nullable=True),
        sa.Column("effect_category", sa.String(length=50), nullable=False),
        sa.Column("analysis_method", sa.String(length=100), nullable=False),
        sa.Column(
            "control_group_used", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "control_group_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("effect_duration_days", sa.Integer(), nullable=True),
        sa.Column(
            "sustainability_score", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column("external_validity", sa.String(length=20), nullable=True),
        sa.Column("limitations", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column(
            "statistical_assumptions_met",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "analysis_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
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
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["interventions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "effect_category IN ('positive', 'negative', 'neutral', 'mixed')",
            name="check_effect_category",
        ),
        sa.CheckConstraint(
            "clinical_significance IN ('trivial', 'small', 'medium', 'large', 'very_large')",
            name="check_clinical_significance",
        ),
        sa.CheckConstraint(
            "external_validity IN ('high', 'medium', 'low', 'unknown')",
            name="check_external_validity",
        ),
    )
    op.create_index(
        op.f("ix_intervention_effectiveness_id"),
        "intervention_effectiveness",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_effectiveness_intervention",
        "intervention_effectiveness",
        ["intervention_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_effectiveness_metric",
        "intervention_effectiveness",
        ["metric_name"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_effectiveness_significance",
        "intervention_effectiveness",
        ["statistical_significance"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_effectiveness_category",
        "intervention_effectiveness",
        ["effect_category"],
        unique=False,
    )

    # Intervention outcomes table - overall intervention success metrics
    op.create_table(
        "intervention_outcomes",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("intervention_id", sa.Uuid(), nullable=False),
        sa.Column(
            "overall_success_score", sa.Numeric(precision=3, scale=2), nullable=False
        ),
        sa.Column(
            "target_achievement_rate", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column("roi_estimate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("cost_per_outcome", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "participant_satisfaction", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column(
            "stakeholder_satisfaction", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column("sustainability_rating", sa.String(length=20), nullable=True),
        sa.Column("scalability_rating", sa.String(length=20), nullable=True),
        sa.Column(
            "replication_confidence", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column(
            "unexpected_outcomes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("lessons_learned", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("best_practices", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("next_steps", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "success_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "failure_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "contextual_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("overall_recommendation", sa.String(length=20), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["interventions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "sustainability_rating IN ('very_low', 'low', 'medium', 'high', 'very_high')",
            name="check_sustainability_rating",
        ),
        sa.CheckConstraint(
            "scalability_rating IN ('very_low', 'low', 'medium', 'high', 'very_high')",
            name="check_scalability_rating",
        ),
        sa.CheckConstraint(
            "overall_recommendation IN ('highly_recommended', 'recommended', 'conditional', 'not_recommended')",
            name="check_overall_recommendation",
        ),
    )
    op.create_index(
        op.f("ix_intervention_outcomes_id"),
        "intervention_outcomes",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_outcomes_intervention",
        "intervention_outcomes",
        ["intervention_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_outcomes_recommendation",
        "intervention_outcomes",
        ["overall_recommendation"],
        unique=False,
    )

    # Comparative effectiveness table - compares different interventions
    op.create_table(
        "comparative_effectiveness",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("intervention_a_id", sa.Uuid(), nullable=False),
        sa.Column("intervention_b_id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("comparison_method", sa.String(length=100), nullable=False),
        sa.Column(
            "effect_size_difference", sa.Numeric(precision=10, scale=4), nullable=False
        ),
        sa.Column("statistical_significance", sa.Boolean(), nullable=True),
        sa.Column(
            "confidence_interval",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("practical_significance", sa.String(length=20), nullable=True),
        sa.Column(
            "cost_effectiveness_ratio", sa.Numeric(precision=10, scale=4), nullable=True
        ),
        sa.Column("time_to_effect", sa.Integer(), nullable=True),
        sa.Column("duration_effect", sa.Integer(), nullable=True),
        sa.Column(
            "side_effects_profile",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "participant_preference", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column(
            "implementation_difficulty",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "contextual_applicability",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("recommendation", sa.String(length=100), nullable=True),
        sa.Column(
            "comparison_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["intervention_a_id"],
            ["interventions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["intervention_b_id"],
            ["interventions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_comparative_effectiveness_id"),
        "comparative_effectiveness",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_comparative_effectiveness_intervention_a",
        "comparative_effectiveness",
        ["intervention_a_id"],
        unique=False,
    )
    op.create_index(
        "ix_comparative_effectiveness_intervention_b",
        "comparative_effectiveness",
        ["intervention_b_id"],
        unique=False,
    )
    op.create_index(
        "ix_comparative_effectiveness_metric",
        "comparative_effectiveness",
        ["metric_name"],
        unique=False,
    )

    # Trigger to update updated_at columns
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Add triggers for updated_at
    op.execute(
        """
        CREATE TRIGGER update_interventions_updated_at
            BEFORE UPDATE ON interventions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_intervention_participants_updated_at
            BEFORE UPDATE ON intervention_participants
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_intervention_effectiveness_updated_at
            BEFORE UPDATE ON intervention_effectiveness
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_intervention_outcomes_updated_at
            BEFORE UPDATE ON intervention_outcomes
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    """Drop intervention effectiveness tracking tables"""

    # Drop triggers
    op.execute(
        "DROP TRIGGER IF EXISTS update_interventions_updated_at ON interventions"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS update_intervention_participants_updated_at ON intervention_participants"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS update_intervention_effectiveness_updated_at ON intervention_effectiveness"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS update_intervention_outcomes_updated_at ON intervention_outcomes"
    )

    # Drop tables in reverse order of creation
    op.drop_index(
        "ix_comparative_effectiveness_metric", table_name="comparative_effectiveness"
    )
    op.drop_index(
        "ix_comparative_effectiveness_intervention_b",
        table_name="comparative_effectiveness",
    )
    op.drop_index(
        "ix_comparative_effectiveness_intervention_a",
        table_name="comparative_effectiveness",
    )
    op.drop_index(
        op.f("ix_comparative_effectiveness_id"), table_name="comparative_effectiveness"
    )
    op.drop_table("comparative_effectiveness")

    op.drop_index(
        "ix_intervention_outcomes_recommendation", table_name="intervention_outcomes"
    )
    op.drop_index(
        "ix_intervention_outcomes_intervention", table_name="intervention_outcomes"
    )
    op.drop_index(
        op.f("ix_intervention_outcomes_id"), table_name="intervention_outcomes"
    )
    op.drop_table("intervention_outcomes")

    op.drop_index(
        "ix_intervention_effectiveness_category",
        table_name="intervention_effectiveness",
    )
    op.drop_index(
        "ix_intervention_effectiveness_significance",
        table_name="intervention_effectiveness",
    )
    op.drop_index(
        "ix_intervention_effectiveness_metric", table_name="intervention_effectiveness"
    )
    op.drop_index(
        "ix_intervention_effectiveness_intervention",
        table_name="intervention_effectiveness",
    )
    op.drop_index(
        op.f("ix_intervention_effectiveness_id"),
        table_name="intervention_effectiveness",
    )
    op.drop_table("intervention_effectiveness")

    op.drop_index(
        "ix_post_intervention_measurements_date",
        table_name="post_intervention_measurements",
    )
    op.drop_index(
        "ix_post_intervention_measurements_metric",
        table_name="post_intervention_measurements",
    )
    op.drop_index(
        "ix_post_intervention_measurements_user",
        table_name="post_intervention_measurements",
    )
    op.drop_index(
        "ix_post_intervention_measurements_intervention",
        table_name="post_intervention_measurements",
    )
    op.drop_index(
        op.f("ix_post_intervention_measurements_id"),
        table_name="post_intervention_measurements",
    )
    op.drop_table("post_intervention_measurements")

    op.drop_index(
        "ix_pre_intervention_measurements_date",
        table_name="pre_intervention_measurements",
    )
    op.drop_index(
        "ix_pre_intervention_measurements_metric",
        table_name="pre_intervention_measurements",
    )
    op.drop_index(
        "ix_pre_intervention_measurements_user",
        table_name="pre_intervention_measurements",
    )
    op.drop_index(
        "ix_pre_intervention_measurements_intervention",
        table_name="pre_intervention_measurements",
    )
    op.drop_index(
        op.f("ix_pre_intervention_measurements_id"),
        table_name="pre_intervention_measurements",
    )
    op.drop_table("pre_intervention_measurements")

    op.drop_index(
        "ix_intervention_participants_dates", table_name="intervention_participants"
    )
    op.drop_index(
        "ix_intervention_participants_status", table_name="intervention_participants"
    )
    op.drop_index(
        "ix_intervention_participants_user", table_name="intervention_participants"
    )
    op.drop_index(
        "ix_intervention_participants_intervention",
        table_name="intervention_participants",
    )
    op.drop_index(
        op.f("ix_intervention_participants_id"), table_name="intervention_participants"
    )
    op.drop_table("intervention_participants")

    op.drop_index("ix_interventions_type_category", table_name="interventions")
    op.drop_index("ix_interventions_dates", table_name="interventions")
    op.drop_index("ix_interventions_status", table_name="interventions")
    op.drop_index("ix_interventions_team", table_name="interventions")
    op.drop_index("ix_interventions_organization", table_name="interventions")
    op.drop_index(op.f("ix_interventions_id"), table_name="interventions")
    op.drop_table("interventions")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
