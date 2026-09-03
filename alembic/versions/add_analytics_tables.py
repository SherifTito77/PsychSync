"""Add analytics tables

Revision ID: 002_add_analytics
Revises: 001_initial_schema
Create Date: 2024-01-16 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_analytics"
down_revision = "002_anonymous_feedback_tables"
branch_labels = None
depends_on = None


def upgrade():
    """Create analytics-related tables."""

    # Analytics events table for tracking user interactions
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("properties", postgresql.JSONB(), nullable=True),
        sa.Column(
            "timestamp",
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
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_analytics_events_user_id", "user_id"),
        sa.Index("idx_analytics_events_org_id", "organization_id"),
        sa.Index("idx_analytics_events_timestamp", "timestamp"),
        sa.Index("idx_analytics_events_type", "event_type"),
    )

    # Dashboard metrics cache table
    op.create_table(
        "dashboard_metrics_cache",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("metric_key", sa.String(255), nullable=False),
        sa.Column("metric_data", postgresql.JSONB(), nullable=False),
        sa.Column("time_period", sa.String(50), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_dashboard_cache_key", "metric_key"),
        sa.Index("idx_dashboard_cache_expires", "expires_at"),
    )

    # User engagement tracking table
    op.create_table(
        "user_engagement",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("sessions_count", sa.Integer(), default=0, nullable=False),
        sa.Column("session_duration_minutes", sa.Float(), default=0.0, nullable=False),
        sa.Column("pages_viewed", sa.Integer(), default=0, nullable=False),
        sa.Column("actions_completed", sa.Integer(), default=0, nullable=False),
        sa.Column("engagement_score", sa.Float(), default=0.0, nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.Index("idx_user_engagement_user_date", "user_id", "date"),
        sa.UniqueConstraint("user_id", "date", name="uq_user_engagement_date"),
    )

    # System performance metrics table
    op.create_table(
        "system_metrics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("metric_unit", sa.String(20), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column(
            "timestamp",
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
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_system_metrics_name_timestamp", "metric_name", "timestamp"),
        sa.Index("idx_system_metrics_tags", "tags", postgresql_using="gin"),
    )

    # Analytics insights table
    op.create_table(
        "analytics_insights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "insight_type", sa.String(50), nullable=False
        ),  # user, assessment, team, system
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),  # high, medium, low
        sa.Column("metric_name", sa.String(100), nullable=True),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("change_percentage", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_analytics_insights_type", "insight_type"),
        sa.Index("idx_analytics_insights_priority", "priority"),
        sa.Index("idx_analytics_insights_active", "is_active", "valid_until"),
    )

    # Time series aggregated data table
    op.create_table(
        "time_series_data",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("dimension", sa.String(50), nullable=True),  # day, week, month, hour
        sa.Column("date_key", sa.String(10), nullable=False),  # YYYY-MM-DD format
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("count", sa.Integer(), default=1, nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_time_series_metric_date", "metric_name", "date_key"),
        sa.Index("idx_time_series_dimension", "dimension"),
        sa.UniqueConstraint(
            "metric_name",
            "dimension",
            "date_key",
            "organization_id",
            "team_id",
            name="uq_time_series_record",
        ),
    )

    # Business metrics table
    op.create_table(
        "business_metrics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("metric_unit", sa.String(20), nullable=True),
        sa.Column(
            "period_type", sa.String(20), nullable=False
        ),  # daily, weekly, monthly, yearly
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_business_metrics_name_period", "metric_name", "period_start"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
    )

    # Add comments to tables
    op.execute(
        "COMMENT ON TABLE analytics_events IS 'Tracks all user interaction events for analytics'"
    )
    op.execute(
        "COMMENT ON TABLE dashboard_metrics_cache IS 'Cache table for dashboard metric calculations'"
    )
    op.execute(
        "COMMENT ON TABLE user_engagement IS 'Daily engagement metrics per user'"
    )
    op.execute(
        "COMMENT ON TABLE system_metrics IS 'System performance and health metrics'"
    )
    op.execute(
        "COMMENT ON TABLE analytics_insights IS 'AI-generated insights from analytics data'"
    )
    op.execute(
        "COMMENT ON TABLE time_series_data IS 'Aggregated time series data for fast dashboard queries'"
    )
    op.execute(
        "COMMENT ON TABLE business_metrics IS 'Business KPI and financial metrics'"
    )


def downgrade():
    """Drop analytics tables."""
    op.drop_table("business_metrics")
    op.drop_table("time_series_data")
    op.drop_table("analytics_insights")
    op.drop_table("system_metrics")
    op.drop_table("user_engagement")
    op.drop_table("dashboard_metrics_cache")
    op.drop_table("analytics_events")
