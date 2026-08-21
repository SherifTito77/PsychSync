"""Add RLS policies for clinical_screenings and related tables.

Revision ID: 20260818_rls_clinical
Revises: 20260816_hipaa_secure
Create Date: 2026-08-18

Clinician-level access hierarchy:
- Users can read their own screenings
- Clinicians/psychiatrists can read screenings in their org
- Validators can read screenings they validated
- Admins/super_admins have full org access
- Platform admins bypass RLS

All org-scoped policies guard against empty session variables to prevent
silent data exposure when middleware fails to set context.
"""

from alembic import op

revision = "20260818_rls_clinical"
down_revision = "20260816_hipaa_secure"
branch_labels = None
depends_on = None

CLINICAL_TABLES = [
    "clinical_screenings",
    "clinical_alerts",
    "clinical_referrals",
    "clinical_consents",
]


def upgrade():
    # Enable RLS on clinical tables
    for table in CLINICAL_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    # ── clinical_screenings ──────────────────────────────────────────
    # Users see their own screenings
    op.execute(
        """
        CREATE POLICY clinical_screening_user_select
        ON clinical_screenings FOR SELECT
        USING (
            current_setting('app.current_user_id', true) != ''
            AND user_id::text = current_setting('app.current_user_id', true)
        );
    """
    )

    # Clinicians and admins see org-wide screenings
    op.execute(
        """
        CREATE POLICY clinical_screening_staff_select
        ON clinical_screenings FOR SELECT
        USING (
            current_setting('app.current_org_id', true) != ''
            AND org_id::text = current_setting('app.current_org_id', true)
            AND current_setting('app.current_user_role', true) IN (
                'admin', 'super_admin', 'clinician', 'psychiatrist', 'hr'
            )
        );
    """
    )

    # Validators see screenings they validated
    op.execute(
        """
        CREATE POLICY clinical_screening_validator_select
        ON clinical_screenings FOR SELECT
        USING (
            current_setting('app.current_user_id', true) != ''
            AND validated_by::text = current_setting('app.current_user_id', true)
        );
    """
    )

    # Platform admin bypass
    op.execute(
        """
        CREATE POLICY clinical_screening_admin_bypass
        ON clinical_screenings FOR ALL
        USING (
            current_setting('app.is_platform_admin', true) = 'true'
        );
    """
    )

    # Insert: only clinicians/admins can create screenings in their org
    op.execute(
        """
        CREATE POLICY clinical_screening_insert
        ON clinical_screenings FOR INSERT
        WITH CHECK (
            current_setting('app.current_org_id', true) != ''
            AND org_id::text = current_setting('app.current_org_id', true)
            AND current_setting('app.current_user_role', true) IN (
                'admin', 'super_admin', 'clinician', 'psychiatrist'
            )
        );
    """
    )

    # Update: only clinicians/admins in same org
    op.execute(
        """
        CREATE POLICY clinical_screening_update
        ON clinical_screenings FOR UPDATE
        USING (
            current_setting('app.current_org_id', true) != ''
            AND org_id::text = current_setting('app.current_org_id', true)
            AND current_setting('app.current_user_role', true) IN (
                'admin', 'super_admin', 'clinician', 'psychiatrist'
            )
        );
    """
    )

    # ── clinical_alerts ──────────────────────────────────────────────
    op.execute(
        """
        CREATE POLICY clinical_alert_org_access
        ON clinical_alerts FOR SELECT
        USING (
            current_setting('app.current_org_id', true) != ''
            AND org_id::text = current_setting('app.current_org_id', true)
            AND current_setting('app.current_user_role', true) IN (
                'admin', 'super_admin', 'clinician', 'psychiatrist', 'hr', 'manager'
            )
        );
    """
    )

    op.execute(
        """
        CREATE POLICY clinical_alert_admin_bypass
        ON clinical_alerts FOR ALL
        USING (
            current_setting('app.is_platform_admin', true) = 'true'
        );
    """
    )

    # ── clinical_referrals ───────────────────────────────────────────
    op.execute(
        """
        CREATE POLICY clinical_referral_org_access
        ON clinical_referrals FOR SELECT
        USING (
            current_setting('app.current_org_id', true) != ''
            AND org_id::text = current_setting('app.current_org_id', true)
            AND current_setting('app.current_user_role', true) IN (
                'admin', 'super_admin', 'clinician', 'psychiatrist'
            )
        );
    """
    )

    op.execute(
        """
        CREATE POLICY clinical_referral_admin_bypass
        ON clinical_referrals FOR ALL
        USING (
            current_setting('app.is_platform_admin', true) = 'true'
        );
    """
    )

    # ── clinical_consents ─────────────────────────────────────────────
    # Users see their own consent records
    op.execute(
        """
        CREATE POLICY clinical_consent_user_select
        ON clinical_consents FOR SELECT
        USING (
            current_setting('app.current_user_id', true) != ''
            AND user_id::text = current_setting('app.current_user_id', true)
        );
    """
    )

    # Admins see org-wide consent
    op.execute(
        """
        CREATE POLICY clinical_consent_admin_select
        ON clinical_consents FOR SELECT
        USING (
            current_setting('app.current_org_id', true) != ''
            AND org_id::text = current_setting('app.current_org_id', true)
            AND current_setting('app.current_user_role', true) IN (
                'admin', 'super_admin', 'clinician'
            )
        );
    """
    )

    op.execute(
        """
        CREATE POLICY clinical_consent_admin_bypass
        ON clinical_consents FOR ALL
        USING (
            current_setting('app.is_platform_admin', true) = 'true'
        );
    """
    )

    # ── Indexes for RLS performance ──────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_clinical_screenings_org_user "
        "ON clinical_screenings (org_id, user_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_clinical_screenings_validated_by "
        "ON clinical_screenings (validated_by) WHERE validated_by IS NOT NULL;"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_clinical_alerts_org "
        "ON clinical_alerts (org_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_clinical_referrals_org "
        "ON clinical_referrals (org_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_clinical_consent_org_user "
        "ON clinical_consents (org_id, user_id);"
    )


def downgrade():
    # Drop all policies first
    policy_names = [
        ("clinical_screenings", "clinical_screening_user_select"),
        ("clinical_screenings", "clinical_screening_staff_select"),
        ("clinical_screenings", "clinical_screening_validator_select"),
        ("clinical_screenings", "clinical_screening_admin_bypass"),
        ("clinical_screenings", "clinical_screening_insert"),
        ("clinical_screenings", "clinical_screening_update"),
        ("clinical_alerts", "clinical_alert_org_access"),
        ("clinical_alerts", "clinical_alert_admin_bypass"),
        ("clinical_referrals", "clinical_referral_org_access"),
        ("clinical_referrals", "clinical_referral_admin_bypass"),
        ("clinical_consents", "clinical_consent_user_select"),
        ("clinical_consents", "clinical_consent_admin_select"),
        ("clinical_consents", "clinical_consent_admin_bypass"),
    ]
    for table, policy in policy_names:
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table};")

    # Then disable RLS
    for table in CLINICAL_TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP INDEX IF EXISTS idx_clinical_screenings_org_user;")
    op.execute("DROP INDEX IF EXISTS idx_clinical_screenings_validated_by;")
    op.execute("DROP INDEX IF EXISTS idx_clinical_alerts_org;")
    op.execute("DROP INDEX IF EXISTS idx_clinical_referrals_org;")
    op.execute("DROP INDEX IF EXISTS idx_clinical_consent_org_user;")
