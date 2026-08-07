"""Add clinical screening tables

Revision ID: 20250114_add_clinical_screening
Revises:
Create Date: 2025-01-14

This migration creates tables for HIPAA-compliant clinical mental health screening:
- clinical_screenings: Stores screening responses and results
- clinical_alerts: Crisis notifications and risk tracking
- clinical_referrals: Mental health professional referrals
- clinical_audit_logs: HIPAA audit trail
- clinical_consents: Explicit consent tracking

IMPORTANT: These tables contain Protected Health Information (PHI)
Ensure proper access controls and encryption are in place.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250114_add_clinical_screening"
down_revision = None  # Will be set when integrated
branch_labels = None
depends_on = None


def upgrade():
    # Create clinical_screenings table
    op.create_table(
        "clinical_screenings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Screening metadata
        sa.Column(
            "screening_type",
            sa.String(50),
            nullable=False,
            comment="PHQ9, GAD7, CSSRS, etc.",
        ),
        sa.Column("version", sa.String(20), server_default="2.0"),
        # Response data (JSONB for flexibility)
        sa.Column("responses", postgresql.JSONB, nullable=False),
        # Scoring results
        sa.Column("total_score", sa.Numeric(10, 2)),
        sa.Column(
            "severity_level",
            sa.String(50),
            comment="minimal, mild, moderate, moderately_severe, severe",
        ),
        sa.Column(
            "subscale_scores", postgresql.JSONB, comment="Multi-dimensional scores"
        ),
        # Risk assessment
        sa.Column("risk_level", sa.String(20), comment="low, moderate, high, critical"),
        sa.Column("risk_flags", postgresql.JSONB, comment="Specific risk indicators"),
        sa.Column("crisis_alert", sa.Boolean, server_default="false", nullable=False),
        # Clinical validation
        sa.Column(
            "validated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("validation_notes", sa.Text),
        sa.Column("validated_at", sa.TIMESTAMP(timezone=True)),
        # Follow-up tracking
        sa.Column("referral_made", sa.Boolean, server_default="false"),
        sa.Column("referral_type", sa.String(100)),
        sa.Column("follow_up_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("follow_up_completed", sa.Boolean, server_default="false"),
        # Consent (HIPAA requirement)
        sa.Column("informed_consent", sa.Boolean, server_default="false"),
        sa.Column("consent_timestamp", sa.TIMESTAMP(timezone=True)),
        sa.Column("consent_version", sa.String(20), server_default="2.0"),
        # Timestamps
        sa.Column(
            "started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        # Soft delete (HIPAA: never truly delete PHI)
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )

    # Create indexes for clinical_screenings
    op.create_index(
        "idx_clinical_user_type", "clinical_screenings", ["user_id", "screening_type"]
    )
    op.create_index(
        "idx_clinical_crisis", "clinical_screenings", ["crisis_alert", "created_at"]
    )
    op.create_index(
        "idx_clinical_org_type", "clinical_screenings", ["org_id", "screening_type"]
    )
    op.create_index(
        "idx_clinical_risk_level", "clinical_screenings", ["risk_level", "created_at"]
    )

    # Create clinical_alerts table
    op.create_table(
        "clinical_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "screening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_screenings.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Alert details
        sa.Column(
            "alert_type",
            sa.String(50),
            nullable=False,
            comment="suicide_risk, self_harm, severe_symptoms",
        ),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            comment="moderate, high, critical",
        ),
        sa.Column("alert_message", sa.Text, nullable=False),
        # Response tracking
        sa.Column("acknowledged", sa.Boolean, server_default="false"),
        sa.Column(
            "acknowledged_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")
        ),
        sa.Column("acknowledged_at", sa.TIMESTAMP(timezone=True)),
        # Resolution
        sa.Column(
            "resolution_status",
            sa.String(50),
            server_default="pending",
            comment="pending, in_progress, resolved, escalated",
        ),
        sa.Column("resolution_notes", sa.Text),
        sa.Column(
            "resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
        # Escalation
        sa.Column("escalated", sa.Boolean, server_default="false"),
        sa.Column(
            "escalation_level",
            sa.String(50),
            comment="supervisor, clinical_team, emergency_services",
        ),
        sa.Column("escalation_notes", sa.Text),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
    )

    # Create indexes for clinical_alerts
    op.create_index(
        "idx_alerts_unresolved", "clinical_alerts", ["resolution_status", "created_at"]
    )
    op.create_index(
        "idx_alerts_critical", "clinical_alerts", ["severity", "acknowledged"]
    )
    op.create_index(
        "idx_alerts_org", "clinical_alerts", ["org_id", "resolution_status"]
    )

    # Create clinical_referrals table
    op.create_table(
        "clinical_referrals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "screening_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_screenings.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_alerts.id"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Referral details
        sa.Column(
            "referral_type",
            sa.String(100),
            nullable=False,
            comment="therapist, psychiatrist, EAP, crisis_line",
        ),
        sa.Column(
            "urgency",
            sa.String(20),
            nullable=False,
            comment="routine, urgent, emergency",
        ),
        # Provider information
        sa.Column("provider_name", sa.Text),
        sa.Column("provider_contact", sa.Text),
        sa.Column("provider_specialty", sa.String(100)),
        # Status
        sa.Column(
            "status",
            sa.String(50),
            server_default="pending",
            comment="pending, contacted, scheduled, completed, declined",
        ),
        sa.Column("user_contacted", sa.Boolean, server_default="false"),
        sa.Column("user_contacted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("appointment_scheduled", sa.Boolean, server_default="false"),
        sa.Column("appointment_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("appointment_completed", sa.Boolean, server_default="false"),
        # Follow-up
        sa.Column("follow_up_required", sa.Boolean, server_default="true"),
        sa.Column("follow_up_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("follow_up_notes", sa.Text),
        # Consent
        sa.Column("consent_obtained", sa.Boolean, server_default="false"),
        sa.Column("consent_date", sa.TIMESTAMP(timezone=True)),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
    )

    op.create_index(
        "idx_referrals_pending",
        "clinical_referrals",
        ["status", "urgency", "created_at"],
    )
    op.create_index("idx_referrals_user", "clinical_referrals", ["user_id", "status"])

    # Create clinical_audit_logs table (HIPAA requirement)
    op.create_table(
        "clinical_audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # What was accessed
        sa.Column(
            "entity_type",
            sa.String(50),
            nullable=False,
            comment="screening, alert, referral",
        ),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Who accessed it
        sa.Column(
            "accessed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("user_role", sa.String(50), nullable=False),
        # Action details
        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
            comment="view, create, update, delete, export",
        ),
        sa.Column("action_details", postgresql.JSONB),
        # Access context
        sa.Column("ip_address", sa.String(45), comment="IPv6 compatible"),
        sa.Column("user_agent", sa.Text),
        sa.Column("session_id", sa.String(255)),
        # Authorization
        sa.Column(
            "authorization_method",
            sa.String(50),
            comment="role_based, explicit_consent, emergency_access",
        ),
        # Timestamp (6-year retention minimum per HIPAA)
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Create indexes for clinical_audit_logs
    op.create_index(
        "idx_audit_entity", "clinical_audit_logs", ["entity_type", "entity_id"]
    )
    op.create_index(
        "idx_audit_user", "clinical_audit_logs", ["accessed_by", "created_at"]
    )
    op.create_index("idx_audit_time", "clinical_audit_logs", ["created_at"])

    # Create clinical_consents table (HIPAA requirement)
    op.create_table(
        "clinical_consents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Consent details
        sa.Column(
            "consent_type",
            sa.String(50),
            nullable=False,
            comment="screening, data_sharing, referral, crisis_contact",
        ),
        sa.Column(
            "consent_version",
            sa.String(20),
            nullable=False,
            comment="Track consent form versions",
        ),
        # Consent status
        sa.Column("consented", sa.Boolean, server_default="false"),
        sa.Column(
            "consent_text",
            sa.Text,
            nullable=False,
            comment="Full consent language shown to user",
        ),
        # Consent scope
        sa.Column(
            "screening_types", postgresql.JSONB, comment="Which assessments are covered"
        ),
        sa.Column(
            "data_sharing_scope",
            postgresql.JSONB,
            comment="What data can be shared, with whom",
        ),
        # Withdrawal (HIPAA right)
        sa.Column("withdrawn", sa.Boolean, server_default="false"),
        sa.Column("withdrawn_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("withdrawal_reason", sa.Text),
        # Digital signature evidence
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        # Timestamps
        sa.Column(
            "consented_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), comment="Annual renewal"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Create indexes for clinical_consents
    op.create_index(
        "idx_consent_user_type",
        "clinical_consents",
        ["user_id", "consent_type", "consented"],
    )
    op.create_index("idx_consent_expiry", "clinical_consents", ["expires_at"])

    # Add comments for documentation
    op.execute(
        "COMMENT ON TABLE clinical_screenings IS 'HIPAA: Stores PHI for mental health screening assessments'"
    )
    op.execute(
        "COMMENT ON TABLE clinical_alerts IS 'HIPAA: Crisis alerts requiring immediate clinical response'"
    )
    op.execute(
        "COMMENT ON TABLE clinical_referrals IS 'HIPAA: Referrals to mental health professionals'"
    )
    op.execute(
        "COMMENT ON TABLE clinical_audit_logs IS 'HIPAA: Immutable audit trail - 6 year minimum retention'"
    )
    op.execute(
        "COMMENT ON TABLE clinical_consents IS 'HIPAA: Explicit consent tracking for clinical assessments'"
    )


def downgrade():
    # Drop tables in reverse order (foreign key dependencies)
    op.drop_table("clinical_consents")
    op.drop_table("clinical_audit_logs")
    op.drop_table("clinical_referrals")
    op.drop_table("clinical_alerts")
    op.drop_table("clinical_screenings")
