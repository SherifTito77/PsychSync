"""add_advanced_clinical_features

Revision ID: clinical_f654b6576f6a
Revises: c2049af57c94
Create Date: 2025-01-16 14:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "clinical_f654b6576f6a"
down_revision: Union[str, None] = "c2049af57c94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add advanced clinical features: new assessments, telehealth, chatbot, mobile"""

    # =====================================================================
    # 1. ADVANCED CLINICAL ASSESSMENTS TABLE
    # =====================================================================
    op.create_table(
        "clinical_assessments_extended",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_type", sa.String(50), nullable=False),
        sa.Column("assessment_version", sa.String(20), server_default="1.0"),
        # Response data
        sa.Column("responses", postgresql.JSONB, nullable=False),
        sa.Column("response_metadata", postgresql.JSONB),
        # Scoring results
        sa.Column("total_score", sa.Numeric(10, 2), nullable=False),
        sa.Column("severity_level", sa.String(50), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("subscale_scores", postgresql.JSONB),
        sa.Column("percentile_rank", sa.Integer),
        # Clinical interpretation
        sa.Column("interpretation", sa.Text, nullable=False),
        sa.Column("recommendations", postgresql.ARRAY(sa.Text)),
        sa.Column("risk_flags", postgresql.ARRAY(sa.String(100))),
        sa.Column("crisis_alert", sa.Boolean, server_default="false", nullable=False),
        # Clinical workflow
        sa.Column("clinician_reviewed", sa.Boolean, server_default="false"),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True)),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("clinician_notes", sa.Text),
        # Follow-up tracking
        sa.Column("follow_up_scheduled", sa.Boolean, server_default="false"),
        sa.Column("follow_up_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("follow_up_type", sa.String(50)),
        # Timestamps
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        # Soft delete
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        # Foreign key
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        # Constraints
        sa.CheckConstraint(
            "assessment_type IN ('LSAS', 'EAT26', 'YBOCS', 'PHQ9', 'GAD7', 'ASRS', 'ISI')",
            name="valid_assessment_type_extended",
        ),
        sa.CheckConstraint(
            "severity_level IN ('minimal', 'mild', 'moderate', 'moderately_severe', 'severe')",
            name="valid_severity_extended",
        ),
        sa.CheckConstraint(
            "risk_level IN ('low', 'moderate', 'high', 'critical')",
            name="valid_risk_level_extended",
        ),
    )

    # Indexes for clinical_assessments_extended
    op.create_index(
        "idx_clinical_ext_user_type",
        "clinical_assessments_extended",
        ["user_id", "assessment_type", "completed_at"],
    )
    op.create_index(
        "idx_clinical_ext_crisis",
        "clinical_assessments_extended",
        ["crisis_alert", "completed_at"],
        postgresql_where=sa.text("crisis_alert = true"),
    )
    op.create_index(
        "idx_clinical_ext_review",
        "clinical_assessments_extended",
        ["clinician_reviewed", "risk_level"],
        postgresql_where=sa.text("clinician_reviewed = false"),
    )

    # =====================================================================
    # 2. ASSESSMENT TRENDS TABLE
    # =====================================================================
    op.create_table(
        "assessment_trends",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_type", sa.String(50), nullable=False),
        # Trend calculations
        sa.Column("trend_direction", sa.String(20)),  # improving, stable, worsening
        sa.Column("slope", sa.Numeric(10, 6)),  # Linear regression slope
        sa.Column("r_squared", sa.Numeric(3, 2)),  # Goodness of fit
        # Statistics
        sa.Column("mean_score", sa.Numeric(10, 2)),
        sa.Column("median_score", sa.Numeric(10, 2)),
        sa.Column("std_deviation", sa.Numeric(10, 2)),
        sa.Column("min_score", sa.Numeric(10, 2)),
        sa.Column("max_score", sa.Numeric(10, 2)),
        # Change metrics
        sa.Column("score_change_30d", sa.Numeric(10, 2)),
        sa.Column("score_change_90d", sa.Numeric(10, 2)),
        sa.Column("percent_change_30d", sa.Numeric(5, 2)),
        # Assessment frequency
        sa.Column("total_assessments", sa.Integer),
        sa.Column("assessment_frequency_days", sa.Numeric(5, 2)),
        # Risk tracking
        sa.Column("high_risk_episodes", sa.Integer, server_default="0"),
        sa.Column("last_high_risk_date", sa.TIMESTAMP(timezone=True)),
        # Calculation metadata
        sa.Column(
            "calculated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("data_points_used", sa.Integer),
        sa.Column("date_range_start", sa.TIMESTAMP(timezone=True)),
        sa.Column("date_range_end", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "assessment_type", name="uq_user_assessment_trend"
        ),
    )

    op.create_index(
        "idx_trends_user_type", "assessment_trends", ["user_id", "assessment_type"]
    )
    op.create_index(
        "idx_trends_worsening",
        "assessment_trends",
        ["trend_direction"],
        postgresql_where=sa.text("trend_direction = 'worsening'"),
    )

    # =====================================================================
    # 3. TELEHEALTH SESSIONS TABLE
    # =====================================================================
    op.create_table(
        "telehealth_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinician_id", postgresql.UUID(as_uuid=True)),
        # Session details
        sa.Column("session_type", sa.String(50), nullable=False),
        sa.Column("consultation_reason", sa.Text),
        sa.Column("related_assessment_id", postgresql.UUID(as_uuid=True)),
        # Twilio Video details
        sa.Column("room_sid", sa.String(100), unique=True),
        sa.Column("room_name", sa.String(200), unique=True),
        sa.Column("user_token", sa.Text),
        sa.Column("clinician_token", sa.Text),
        # Scheduling
        sa.Column("scheduled_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer, server_default="50"),
        sa.Column("timezone", sa.String(50), server_default="UTC"),
        # Session tracking
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("actual_duration_minutes", sa.Integer),
        sa.Column("user_joined_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("clinician_joined_at", sa.TIMESTAMP(timezone=True)),
        # Recording
        sa.Column("recording_enabled", sa.Boolean, server_default="true"),
        sa.Column("recording_sid", sa.String(100)),
        sa.Column("recording_url", sa.Text),
        sa.Column("recording_duration_seconds", sa.Integer),
        # Session notes
        sa.Column("session_notes", sa.Text),
        sa.Column("clinician_notes", sa.Text),
        sa.Column("prescriptions_issued", postgresql.JSONB),
        sa.Column("diagnoses_discussed", postgresql.ARRAY(sa.String(100))),
        # Status
        sa.Column("status", sa.String(50), server_default="scheduled", nullable=False),
        sa.Column("cancellation_reason", sa.String(200)),
        sa.Column("cancelled_by", sa.String(50)),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True)),
        # Quality metrics
        sa.Column("connection_quality", sa.String(20)),
        sa.Column("technical_issues", postgresql.JSONB),
        sa.Column("user_satisfaction_rating", sa.Integer),
        sa.Column("feedback_comment", sa.Text),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinician_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "session_type IN ('initial', 'follow_up', 'crisis', 'routine')",
            name="valid_session_type",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show')",
            name="valid_session_status",
        ),
    )

    op.create_index(
        "idx_telehealth_user", "telehealth_sessions", ["user_id", "scheduled_time"]
    )
    op.create_index(
        "idx_telehealth_clinician",
        "telehealth_sessions",
        ["clinician_id", "scheduled_time"],
    )
    op.create_index(
        "idx_telehealth_upcoming",
        "telehealth_sessions",
        ["scheduled_time"],
        postgresql_where=sa.text("status = 'scheduled'"),
    )

    # =====================================================================
    # 4. CHATBOT CONVERSATIONS TABLE
    # =====================================================================
    op.create_table(
        "chatbot_conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Message content
        sa.Column("message_text", sa.Text, nullable=False),
        sa.Column("is_user_message", sa.Boolean, nullable=False),
        sa.Column("ai_response", sa.Text),
        sa.Column("response_generated_at", sa.TIMESTAMP(timezone=True)),
        # AI metadata
        sa.Column("model_used", sa.String(50)),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("response_time_ms", sa.Integer),
        sa.Column("confidence_score", sa.Numeric(3, 2)),
        # Crisis detection
        sa.Column("crisis_detected", sa.Boolean, server_default="false"),
        sa.Column("crisis_type", sa.String(100)),
        sa.Column("crisis_keywords_matched", postgresql.ARRAY(sa.String(100))),
        sa.Column("crisis_confidence", sa.Numeric(3, 2)),
        # Context & classification
        sa.Column("intent_classification", sa.String(100)),
        sa.Column("sentiment_score", sa.Numeric(3, 2)),
        sa.Column("context_retrieved", postgresql.JSONB),
        # Actions
        sa.Column("suggested_resources", postgresql.JSONB),
        sa.Column("escalated_to_human", sa.Boolean, server_default="false"),
        sa.Column("escalation_reason", sa.String(200)),
        # User feedback
        sa.Column("message_helpful", sa.Boolean),
        sa.Column("user_feedback", sa.Text),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        # Soft delete for privacy
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_index(
        "idx_chatbot_user_session",
        "chatbot_conversations",
        ["user_id", "session_id", "created_at"],
    )
    op.create_index(
        "idx_chatbot_crisis",
        "chatbot_conversations",
        ["crisis_detected", "created_at"],
        postgresql_where=sa.text("crisis_detected = true"),
    )
    op.create_index(
        "idx_chatbot_escalation",
        "chatbot_conversations",
        ["escalated_to_human", "created_at"],
        postgresql_where=sa.text("escalated_to_human = true"),
    )

    # =====================================================================
    # 5. MOBILE DEVICES TABLE
    # =====================================================================
    op.create_table(
        "mobile_devices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Device info
        sa.Column("device_token", sa.String(500), unique=True, nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("device_model", sa.String(100)),
        sa.Column("os_version", sa.String(50)),
        sa.Column("app_version", sa.String(20)),
        # Push notification settings
        sa.Column("push_enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("notification_preferences", postgresql.JSONB),
        # Activity tracking
        sa.Column("last_active", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_sync", sa.TIMESTAMP(timezone=True)),
        sa.Column("total_sessions", sa.Integer, server_default="0"),
        # Timestamps
        sa.Column(
            "registered_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
        ),
        # Deactivation
        sa.Column("deactivated_at", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "platform IN ('ios', 'android', 'web')", name="valid_platform"
        ),
    )

    op.create_index("idx_mobile_user", "mobile_devices", ["user_id"])
    op.create_index("idx_mobile_token", "mobile_devices", ["device_token"])
    op.create_index(
        "idx_mobile_active",
        "mobile_devices",
        ["user_id", "last_active"],
        postgresql_where=sa.text("deactivated_at IS NULL"),
    )

    # =====================================================================
    # 6. Add clinician columns to users table
    # =====================================================================
    op.add_column(
        "users",
        sa.Column("is_clinician", sa.Boolean, server_default="false", nullable=False),
    )
    op.add_column("users", sa.Column("clinician_license_number", sa.String(100)))
    op.add_column(
        "users", sa.Column("clinician_specialization", postgresql.ARRAY(sa.String(100)))
    )
    op.add_column("users", sa.Column("clinician_bio", sa.Text))
    op.add_column(
        "users", sa.Column("available_for_crisis", sa.Boolean, server_default="false")
    )

    # =====================================================================
    # 7. Create materialized view for population health analytics
    # =====================================================================
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS population_health_stats AS
        SELECT
            assessment_type,
            DATE_TRUNC('month', completed_at) as month,
            COUNT(*) as total_assessments,
            AVG(total_score) as avg_score,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_score) as median_score,
            STDDEV(total_score) as std_dev,
            COUNT(CASE WHEN crisis_alert = true THEN 1 END) as crisis_count,
            COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk_count,
            COUNT(CASE WHEN risk_level = 'moderate' THEN 1 END) as moderate_risk_count,
            COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low_risk_count
        FROM clinical_assessments_extended
        WHERE deleted_at IS NULL
        GROUP BY assessment_type, DATE_TRUNC('month', completed_at)
    """
    )

    op.create_index(
        "idx_pop_health_type_month",
        "population_health_stats",
        ["assessment_type", "month"],
        unique=True,
    )


def downgrade() -> None:
    """Remove advanced clinical features"""

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS population_health_stats")

    # Drop added columns from users
    op.drop_column("users", "available_for_crisis")
    op.drop_column("users", "clinician_bio")
    op.drop_column("users", "clinician_specialization")
    op.drop_column("users", "clinician_license_number")
    op.drop_column("users", "is_clinician")

    # Drop tables (in reverse order due to foreign keys)
    op.drop_table("mobile_devices")
    op.drop_table("chatbot_conversations")
    op.drop_table("telehealth_sessions")
    op.drop_table("assessment_trends")
    op.drop_table("clinical_assessments_extended")
