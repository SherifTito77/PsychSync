"""add biometric health tables

Revision ID: 20250114_add_biometric_health
Revises: 20250112_satisfaction_tracking
Create Date: 2025-01-14

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250114_add_biometric_health"
down_revision = "20250114_fix_framework_pk"
branch_labels = None
depends_on = None


def upgrade():
    """Create biometric health data tables"""

    # Create biometric_health_data table
    op.create_table(
        "biometric_health_data",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("measurement_date", sa.Date(), nullable=False),
        sa.Column("data_source", sa.String(length=50), nullable=False),
        sa.Column("device_info", postgresql.JSON(), nullable=True),
        sa.Column("sync_timestamp", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "resting_heart_rate", sa.Numeric(precision=5, scale=2), nullable=True
        ),
        sa.Column(
            "heart_rate_variability", sa.Numeric(precision=6, scale=2), nullable=True
        ),
        sa.Column("avg_heart_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("max_heart_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("min_heart_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("blood_pressure_systolic", sa.Integer(), nullable=True),
        sa.Column("blood_pressure_diastolic", sa.Integer(), nullable=True),
        sa.Column(
            "blood_pressure_timestamp", sa.TIMESTAMP(timezone=True), nullable=True
        ),
        sa.Column("oxygen_saturation", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("respiratory_rate", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("sleep_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column(
            "sleep_quality_score", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column("deep_sleep_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("rem_sleep_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("light_sleep_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("awake_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("sleep_efficiency", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("sleep_latency", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("sleep_consistency", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("steps_count", sa.Integer(), nullable=True),
        sa.Column("active_calories", sa.Integer(), nullable=True),
        sa.Column("total_calories", sa.Integer(), nullable=True),
        sa.Column("activity_minutes", sa.Integer(), nullable=True),
        sa.Column("moderate_activity_minutes", sa.Integer(), nullable=True),
        sa.Column("vigorous_activity_minutes", sa.Integer(), nullable=True),
        sa.Column("sedentary_minutes", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("floors_climbed", sa.Integer(), nullable=True),
        sa.Column("stress_score", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column(
            "stress_body_indicator", sa.Numeric(precision=3, scale=2), nullable=True
        ),
        sa.Column("recovery_score", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("hrv_balance", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "body_fat_percentage", sa.Numeric(precision=4, scale=2), nullable=True
        ),
        sa.Column("muscle_mass_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("bmi", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column(
            "body_temperature_celsius", sa.Numeric(precision=4, scale=2), nullable=True
        ),
        sa.Column("hydration_ml", sa.Integer(), nullable=True),
        sa.Column("health_events", postgresql.JSON(), nullable=True),
        sa.Column("risk_flags", postgresql.JSON(), nullable=True),
        sa.Column("alerts_triggered", postgresql.JSON(), nullable=True),
        sa.Column("data_completeness", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column(
            "consent_given", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("consent_date", sa.Date(), nullable=True),
        sa.Column("data_sharing_preferences", postgresql.JSON(), nullable=True),
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
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_biometric_health_data_organization_id"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_biometric_health_data_user_id")
        ),
        comment="Biometric health data from wearables and health devices",
    )

    # Create indexes for biometric_health_data
    op.create_index(
        "idx_biometric_user_date",
        "biometric_health_data",
        ["user_id", "measurement_date"],
        unique=False,
    )
    op.create_index(
        "idx_biometric_org_date",
        "biometric_health_data",
        ["organization_id", "measurement_date"],
        unique=False,
    )
    op.create_index(
        "idx_biometric_source",
        "biometric_health_data",
        ["data_source", "measurement_date"],
        unique=False,
    )
    op.create_index(
        "idx_biometric_rhr",
        "biometric_health_data",
        ["resting_heart_rate"],
        unique=False,
    )
    op.create_index(
        "idx_biometric_hrv",
        "biometric_health_data",
        ["heart_rate_variability"],
        unique=False,
    )
    op.create_index(
        "idx_biometric_sleep", "biometric_health_data", ["sleep_hours"], unique=False
    )

    # Create health_data_consent table
    op.create_table(
        "health_data_consent",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "consent_given", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("consent_date", sa.Date(), nullable=True),
        sa.Column(
            "consent_version",
            sa.String(length=20),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column(
            "biometric_collection", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "biometric_processing", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "biometric_sharing", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "research_participation",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("data_sources", postgresql.JSON(), nullable=True),
        sa.Column(
            "data_retention_days", sa.Integer(), nullable=False, server_default="365"
        ),
        sa.Column(
            "anonymization_allowed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "consent_withdrawn", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("withdrawal_date", sa.Date(), nullable=True),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
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
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_health_data_consent_organization_id"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_health_data_consent_user_id")
        ),
        sa.UniqueConstraint("user_id", name="uq_health_data_consent_user_id"),
        comment="User consent for biometric health data collection",
    )

    # Create indexes for health_data_consent
    op.create_index(
        "idx_health_consent_org",
        "health_data_consent",
        ["organization_id", "consent_given"],
        unique=False,
    )


def downgrade():
    """Drop biometric health data tables"""

    # Drop indexes first
    op.drop_index("idx_health_consent_org", table_name="health_data_consent")
    op.drop_index("idx_biometric_sleep", table_name="biometric_health_data")
    op.drop_index("idx_biometric_hrv", table_name="biometric_health_data")
    op.drop_index("idx_biometric_rhr", table_name="biometric_health_data")
    op.drop_index("idx_biometric_source", table_name="biometric_health_data")
    op.drop_index("idx_biometric_org_date", table_name="biometric_health_data")
    op.drop_index("idx_biometric_user_date", table_name="biometric_health_data")

    # Drop tables
    op.drop_table("health_data_consent")
    op.drop_table("biometric_health_data")
