"""Add optimized composite and partial indexes for secure models.

Revision ID: 20260818_opt_indexes
Revises: 20260818_rls_audit
Create Date: 2026-08-18

Targets the most common query patterns:
- RLS policy evaluation (org_id + is_active filters)
- Clinical dashboard queries (org + screening type + date)
- Audit log lookups (user + time range)
- Password history checks (user + date ordering)
"""

from alembic import op

revision = "20260818_opt_indexes"
down_revision = "20260818_rls_audit"
branch_labels = None
depends_on = None


def upgrade():
    # ── Secure models: RLS policy evaluation ─────────────────────────
    # These indexes directly support the RLS USING clauses

    # users_secure: org + active (most common RLS filter)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sec_user_org_active_role
        ON users_secure (organization_id, is_active, role)
        WHERE deleted_at IS NULL;
    """
    )

    # responses_secure: user ownership lookups
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sec_resp_user_status
        ON responses_secure (user_id, status, created_at DESC)
        WHERE deleted_at IS NULL;
    """
    )

    # responses_secure: assessment-based lookups (no direct org column)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sec_resp_assessment_created
        ON responses_secure (assessment_id, created_at DESC)
        WHERE deleted_at IS NULL;
    """
    )

    # assessments_secure: org + published (dashboard listing)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sec_assess_org_status
        ON assessments_secure (organization_id, status)
        WHERE deleted_at IS NULL AND status = 'published';
    """
    )

    # teams_secure: org membership listing
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sec_team_org_active
        ON teams_secure (organization_id, is_active)
        WHERE deleted_at IS NULL;
    """
    )

    # ── Clinical tables: dashboard and reporting ─────────────────────

    # Screening dashboard: org + type + date (filter + sort)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_screen_dashboard
        ON clinical_screenings (org_id, screening_type, created_at DESC);
    """
    )

    # Risk monitoring: org + risk level (active crisis filtering)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_screen_risk
        ON clinical_screenings (org_id, risk_level)
        WHERE risk_level IN ('high', 'critical') AND deleted_at IS NULL;
    """
    )

    # Crisis alerts: unresolved alerts (monitoring dashboard)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_alert_unresolved
        ON clinical_alerts (org_id, severity, created_at DESC)
        WHERE resolved_at IS NULL;
    """
    )

    # Referral tracking: pending referrals
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_referral_pending
        ON clinical_referrals (org_id, urgency, created_at DESC)
        WHERE status IN ('pending', 'contacted');
    """
    )

    # ── Audit and compliance ─────────────────────────────────────────

    # Audit log: user activity timeline
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_user_timeline
        ON audit_logs (user_id, timestamp DESC)
        WHERE severity IN ('high', 'critical');
    """
    )

    # Data access log: HIPAA accounting of disclosures
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_data_access_record
        ON data_access_logs (table_name, record_id, timestamp DESC);
    """
    )

    # Clinical audit: entity access history
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_audit_entity
        ON clinical_audit_logs (entity_type, entity_id, created_at DESC);
    """
    )

    # ── Password history: reuse check ────────────────────────────────
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pwd_history_user_date
        ON password_history (user_id, changed_at DESC);
    """
    )

    # ── RLS violation log: investigation queries ─────────────────────
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rls_violation_tenant
        ON rls_violation_log (attempted_tenant_id, violation_time DESC);
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rls_violation_bypass
        ON rls_violation_log (bypass_type, violation_time DESC)
        WHERE bypass_type = 'cross_tenant_attempt';
    """
    )


def downgrade():
    indexes = [
        "idx_sec_user_org_active_role",
        "idx_sec_resp_user_status",
        "idx_sec_resp_assessment_created",
        "idx_sec_assess_org_status",
        "idx_sec_team_org_active",
        "idx_clinical_screen_dashboard",
        "idx_clinical_screen_risk",
        "idx_clinical_alert_unresolved",
        "idx_clinical_referral_pending",
        "idx_audit_user_timeline",
        "idx_data_access_record",
        "idx_clinical_audit_entity",
        "idx_pwd_history_user_date",
        "idx_rls_violation_tenant",
        "idx_rls_violation_bypass",
    ]
    for idx in indexes:
        op.execute(f"DROP INDEX IF EXISTS {idx};")
