"""Add CHECK constraints and triggers for clinical data integrity.

Revision ID: 20260818_clinical_ck
Revises: 20260818_rls_clinical
Create Date: 2026-08-18

Ensures data integrity at the database level for:
- Valid score ranges per screening type
- Severity/risk level consistency
- Consent required before screening storage
- Auto-crisis alert trigger on critical risk
"""

from alembic import op

revision = "20260818_clinical_ck"
down_revision = "20260818_rls_clinical"
branch_labels = None
depends_on = None


def upgrade():
    # ── CHECK constraints on clinical_screenings ─────────────────────

    # Valid screening types
    op.execute(
        """
        ALTER TABLE clinical_screenings
        ADD CONSTRAINT ck_screening_type_valid
        CHECK (screening_type IN (
            'PHQ9', 'GAD7', 'PHQ2', 'GAD2', 'PCL5', 'AUDIT', 'DAST10',
            'CSSRS', 'MDQ', 'ASRS', 'EPDS', 'PSS10', 'K10', 'WHO5',
            'WHODAS', 'CUSTOM'
        ));
    """
    )

    # Score must be non-negative
    op.execute(
        """
        ALTER TABLE clinical_screenings
        ADD CONSTRAINT ck_screening_score_range
        CHECK (total_score >= 0 AND total_score <= 100);
    """
    )

    # Severity level values
    op.execute(
        """
        ALTER TABLE clinical_screenings
        ADD CONSTRAINT ck_severity_level_valid
        CHECK (severity_level IS NULL OR severity_level IN (
            'none', 'minimal', 'mild', 'moderate', 'moderately_severe', 'severe'
        ));
    """
    )

    # Risk level values
    op.execute(
        """
        ALTER TABLE clinical_screenings
        ADD CONSTRAINT ck_risk_level_valid
        CHECK (risk_level IS NULL OR risk_level IN (
            'low', 'moderate', 'high', 'critical'
        ));
    """
    )

    # Consent must be given before screening is stored
    op.execute(
        """
        ALTER TABLE clinical_screenings
        ADD CONSTRAINT ck_consent_required
        CHECK (informed_consent = true);
    """
    )

    # If referral_made is true, referral_type must be set
    op.execute(
        """
        ALTER TABLE clinical_screenings
        ADD CONSTRAINT ck_referral_consistency
        CHECK (
            (referral_made = false OR referral_made IS NULL)
            OR (referral_made = true AND referral_type IS NOT NULL)
        );
    """
    )

    # ── CHECK constraints on clinical_alerts ─────────────────────────

    op.execute(
        """
        ALTER TABLE clinical_alerts
        ADD CONSTRAINT ck_alert_severity_valid
        CHECK (severity IN ('moderate', 'high', 'critical'));
    """
    )

    # ── CHECK constraints on clinical_referrals ──────────────────────

    op.execute(
        """
        ALTER TABLE clinical_referrals
        ADD CONSTRAINT ck_referral_urgency_valid
        CHECK (urgency IN ('routine', 'urgent', 'emergency'));
    """
    )

    op.execute(
        """
        ALTER TABLE clinical_referrals
        ADD CONSTRAINT ck_referral_status_valid
        CHECK (status IN (
            'pending', 'contacted', 'scheduled', 'completed', 'declined', 'cancelled'
        ));
    """
    )

    # ── Trigger: auto-set crisis_alert on critical risk ──────────────

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_auto_crisis_alert()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Auto-set crisis_alert when risk_level is critical
            IF NEW.risk_level = 'critical' THEN
                NEW.crisis_alert := true;
            END IF;

            -- Auto-set crisis_alert on specific screening score thresholds
            IF NEW.screening_type = 'PHQ9' AND NEW.total_score >= 20 THEN
                NEW.crisis_alert := true;
            END IF;
            IF NEW.screening_type = 'CSSRS' AND NEW.total_score >= 4 THEN
                NEW.crisis_alert := true;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER trg_auto_crisis_alert
        BEFORE INSERT OR UPDATE ON clinical_screenings
        FOR EACH ROW
        EXECUTE FUNCTION fn_auto_crisis_alert();
    """
    )

    # ── Trigger: prevent deletion of clinical data (soft delete only) ─

    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_prevent_clinical_hard_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Allow superuser/migration bypass when explicitly flagged
            IF current_setting('app.allow_hard_delete', true) = 'true' THEN
                RETURN OLD;
            END IF;

            RAISE EXCEPTION
                'Hard deletion of clinical records is prohibited. Use soft delete (set deleted_at).';
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER trg_prevent_screening_delete
        BEFORE DELETE ON clinical_screenings
        FOR EACH ROW
        EXECUTE FUNCTION fn_prevent_clinical_hard_delete();
    """
    )


def downgrade():
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_auto_crisis_alert ON clinical_screenings;")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_prevent_screening_delete ON clinical_screenings;"
    )
    op.execute("DROP FUNCTION IF EXISTS fn_auto_crisis_alert();")
    op.execute("DROP FUNCTION IF EXISTS fn_prevent_clinical_hard_delete();")

    # Drop constraints
    constraints = [
        ("clinical_screenings", "ck_screening_type_valid"),
        ("clinical_screenings", "ck_screening_score_range"),
        ("clinical_screenings", "ck_severity_level_valid"),
        ("clinical_screenings", "ck_risk_level_valid"),
        ("clinical_screenings", "ck_consent_required"),
        ("clinical_screenings", "ck_referral_consistency"),
        ("clinical_alerts", "ck_alert_severity_valid"),
        ("clinical_referrals", "ck_referral_urgency_valid"),
        ("clinical_referrals", "ck_referral_status_valid"),
    ]
    for table, constraint in constraints:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint};")
