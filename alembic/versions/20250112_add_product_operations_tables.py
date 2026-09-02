"""Add product operations tables

Revision ID: 20250112_add_product_ops
Revises:
Create Date: 2025-01-12 10:00:00.000000

Adds tables for:
- A/B testing framework
- Feature request management
- Churn prediction
- User activation tracking
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20250112_add_product_ops"
down_revision: Union[str, None] = "20250112_satisfaction_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # A/B TESTING TABLES
    # ========================================================================

    # A/B Experiments table
    op.create_table(
        "ab_experiments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="draft"
        ),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_ab_experiments_name", "ab_experiments", ["name"])
    op.create_index("idx_ab_experiments_status", "ab_experiments", ["status"])

    # A/B Variants table
    op.create_table(
        "ab_variants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("traffic_split", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_control", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["ab_experiments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id", "name"),
    )

    # A/B Events table
    op.create_table(
        "ab_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("properties", postgresql.JSONB(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["ab_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["variant_id"], ["ab_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ab_events_user", "ab_events", ["user_id"])
    op.create_index("idx_ab_events_experiment", "ab_events", ["experiment_id"])
    op.create_index("idx_ab_events_type", "ab_events", ["event_type"])
    op.create_index("idx_ab_events_timestamp", "ab_events", ["timestamp"])

    # A/B Conversions table
    op.create_table(
        "ab_conversions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversion_type", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["ab_experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["variant_id"], ["ab_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ab_conversions_user", "ab_conversions", ["user_id"])
    op.create_index(
        "idx_ab_conversions_experiment", "ab_conversions", ["experiment_id"]
    )

    # ========================================================================
    # FEATURE REQUEST TABLES
    # ========================================================================

    # Feature requests table
    op.create_table(
        "feature_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="backlog"
        ),
        sa.Column("theme", sa.String(length=10), nullable=False),
        sa.Column("subcategory", sa.String(length=50), nullable=True),
        sa.Column("request_type", sa.String(length=10), nullable=False),
        sa.Column("priority", sa.String(length=5), nullable=False, server_default="P3"),
        sa.Column("effort", sa.String(length=5), nullable=False, server_default="M"),
        sa.Column("value", sa.String(length=5), nullable=False, server_default="V3"),
        # RICE scoring
        sa.Column("reach_score", sa.Float(), nullable=True),
        sa.Column("impact_score", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("effort_score", sa.Float(), nullable=True),
        sa.Column("rice_score", sa.Float(), nullable=True),
        # Source info
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Links
        sa.Column("opportunity_id", sa.String(length=255), nullable=True),
        sa.Column("ticket_id", sa.String(length=255), nullable=True),
        # Planning
        sa.Column("target_release", sa.String(length=255), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("estimated_start_date", sa.Date(), nullable=True),
        sa.Column("estimated_end_date", sa.Date(), nullable=True),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("declined_reason", sa.Text(), nullable=True),
        # Full-text search
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(["submitted_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_feature_requests_status", "feature_requests", ["status"])
    op.create_index("idx_feature_requests_theme", "feature_requests", ["theme"])
    op.create_index("idx_feature_requests_rice", "feature_requests", ["rice_score"])
    op.create_index(
        "idx_feature_requests_search",
        "feature_requests",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index(
        "idx_feature_requests_customer", "feature_requests", ["customer_id"]
    )

    # Feature request relations table
    op.create_table(
        "feature_request_relations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("parent_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_request_id"], ["feature_requests.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["child_request_id"], ["feature_requests.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_request_id", "child_request_id", "relation_type"),
    )

    # Feature request votes table
    op.create_table(
        "feature_request_votes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("feature_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["feature_request_id"], ["feature_requests.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feature_request_id", "user_id"),
    )
    op.create_index(
        "idx_feature_votes_request", "feature_request_votes", ["feature_request_id"]
    )

    # ========================================================================
    # CHURN PREDICTION TABLES
    # ========================================================================

    # Churn risk scores table
    op.create_table(
        "churn_risk_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        # Overall risk
        sa.Column("overall_risk", sa.String(length=20), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        # Signal scores
        sa.Column("usage_decline_score", sa.Integer(), nullable=True),
        sa.Column("adoption_stagnation_score", sa.Integer(), nullable=True),
        sa.Column("failed_conversion_score", sa.Integer(), nullable=True),
        sa.Column("support_sentiment_score", sa.Integer(), nullable=True),
        sa.Column("assessment_limit_score", sa.Integer(), nullable=True),
        sa.Column("login_frequency_score", sa.Integer(), nullable=True),
        sa.Column("survey_sentiment_score", sa.Integer(), nullable=True),
        sa.Column("competitor_research_score", sa.Integer(), nullable=True),
        # Primary factors
        sa.Column("primary_risk_factors", postgresql.ARRAY(sa.Text()), nullable=True),
        # Interventions
        sa.Column("last_intervention_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "intervention_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "overall_score BETWEEN 0 AND 100", name="check_overall_score_range"
        ),
    )
    op.create_index("idx_churn_risk_user", "churn_risk_scores", ["user_id"])
    op.create_index("idx_churn_risk_overall", "churn_risk_scores", ["overall_risk"])
    op.create_index("idx_churn_risk_date", "churn_risk_scores", ["calculated_at"])

    # Churn trigger executions log
    op.create_table(
        "churn_trigger_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_name", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("action_taken", sa.Text(), nullable=False),
        sa.Column("result", sa.String(length=50), nullable=True),
        sa.Column("result_details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_churn_trigger_user", "churn_trigger_executions", ["user_id"])
    op.create_index(
        "idx_churn_trigger_date", "churn_trigger_executions", ["executed_at"]
    )

    # Churn trigger cooldowns table
    op.create_table(
        "churn_trigger_cooldowns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trigger_name", sa.String(length=100), nullable=False),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "trigger_name"),
    )

    # ========================================================================
    # USER ACTIVATION TRACKING
    # ========================================================================

    # User activation table
    op.create_table(
        "user_activation",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "segment",
            sa.String(length=50),
            nullable=False,
            server_default="individual_free",
        ),
        # Timestamps
        sa.Column("signup_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "first_assessment_timestamp", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "first_results_viewed_timestamp", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("activation_timestamp", sa.DateTime(timezone=True), nullable=True),
        # Flags
        sa.Column("is_activated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("activation_type", sa.String(length=50), nullable=True),
        # Metrics
        sa.Column("time_to_activation_minutes", sa.Integer(), nullable=True),
        sa.Column("time_to_first_assessment_minutes", sa.Integer(), nullable=True),
        # Team-specific
        sa.Column(
            "invited_team_member", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "first_invite_sent_timestamp", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "first_invite_accepted_timestamp", sa.DateTime(timezone=True), nullable=True
        ),
        # Premium-specific
        sa.Column(
            "upgraded_to_premium", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("upgrade_timestamp", sa.DateTime(timezone=True), nullable=True),
        # Enterprise-specific
        sa.Column(
            "completed_onboarding", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "onboarding_completed_timestamp", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "configured_sso", sa.Boolean(), nullable=False, server_default="false"
        ),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("idx_user_activation_user_id", "user_activation", ["user_id"])
    op.create_index(
        "idx_user_activation_is_activated", "user_activation", ["is_activated"]
    )
    op.create_index("idx_user_activation_segment", "user_activation", ["segment"])
    op.create_index(
        "idx_user_activation_timestamp", "user_activation", ["signup_timestamp"]
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_table("user_activation")
    op.drop_table("churn_trigger_cooldowns")
    op.drop_table("churn_trigger_executions")
    op.drop_table("churn_risk_scores")
    op.drop_table("feature_request_votes")
    op.drop_table("feature_request_relations")
    op.drop_table("feature_requests")
    op.drop_table("ab_conversions")
    op.drop_table("ab_events")
    op.drop_table("ab_variants")
    op.drop_table("ab_experiments")
