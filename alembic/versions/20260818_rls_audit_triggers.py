"""Add RLS audit triggers for bypass and cross-tenant access logging.

Revision ID: 20260818_rls_audit
Revises: 20260818_clinical_ck
Create Date: 2026-08-18

Creates:
1. fn_log_rls_admin_bypass() — logs whenever platform admin bypass is used
2. fn_audit_cross_tenant_access() — logs when a query touches rows
   outside the caller's org_id
3. Attaches triggers to all RLS-protected tables
"""

from alembic import op

revision = "20260818_rls_audit"
down_revision = "20260818_clinical_ck"
branch_labels = None
depends_on = None

# Tables grouped by their org column name
# Secure models use "organization_id", clinical models use "org_id"
TABLES_WITH_ORGANIZATION_ID = [
    "users_secure",
    "teams_secure",
    "assessments_secure",
]

TABLES_WITH_ORG_ID = [
    "clinical_screenings",
    "clinical_alerts",
    "clinical_referrals",
]

# organizations_secure IS the org (id column = the org), no cross-tenant guard needed
# team_members_secure has no direct org column, skip
# responses_secure has no org column directly (linked via assessment)

ALL_TRIGGER_TABLES = TABLES_WITH_ORGANIZATION_ID + TABLES_WITH_ORG_ID


def upgrade():
    # The rls_violation_log table may exist from the 2025 enhanced RLS migration
    # with a different schema. Add missing columns rather than CREATE IF NOT EXISTS.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rls_violation_log (
            id BIGSERIAL PRIMARY KEY,
            table_name VARCHAR(255) NOT NULL,
            operation VARCHAR(50) NOT NULL,
            attempted_tenant_id UUID,
            user_id UUID,
            ip_address INET,
            user_agent TEXT,
            violation_time TIMESTAMPTZ DEFAULT NOW()
        );
    """
    )

    # Add columns that may not exist from the older migration
    op.execute(
        "ALTER TABLE rls_violation_log ADD COLUMN IF NOT EXISTS current_tenant_id UUID;"
    )
    op.execute(
        "ALTER TABLE rls_violation_log ADD COLUMN IF NOT EXISTS user_role VARCHAR(100);"
    )
    op.execute(
        "ALTER TABLE rls_violation_log ADD COLUMN IF NOT EXISTS bypass_type VARCHAR(50);"
    )
    op.execute("ALTER TABLE rls_violation_log ADD COLUMN IF NOT EXISTS details JSONB;")

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rls_violation_time
        ON rls_violation_log (violation_time DESC);
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rls_violation_user
        ON rls_violation_log (user_id, violation_time DESC);
    """
    )

    # ── Helper: safe UUID cast (returns NULL if setting is empty) ────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION safe_setting_uuid(setting_name TEXT)
        RETURNS UUID AS $$
        DECLARE
            val TEXT;
        BEGIN
            val := current_setting(setting_name, true);
            IF val IS NULL OR val = '' THEN
                RETURN NULL;
            END IF;
            RETURN val::uuid;
        EXCEPTION WHEN invalid_text_representation THEN
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """
    )

    # ── Admin bypass audit for tables with "org_id" column ───────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_log_admin_bypass_org_id()
        RETURNS TRIGGER AS $$
        BEGIN
            IF current_setting('app.is_platform_admin', true) = 'true' THEN
                INSERT INTO rls_violation_log (
                    table_name, operation, attempted_tenant_id,
                    current_tenant_id, user_id, user_role,
                    bypass_type, details
                ) VALUES (
                    TG_TABLE_NAME, TG_OP,
                    CASE WHEN TG_OP = 'DELETE' THEN OLD.org_id ELSE NEW.org_id END,
                    safe_setting_uuid('app.current_org_id'),
                    safe_setting_uuid('app.current_user_id'),
                    current_setting('app.current_user_role', true),
                    'platform_admin',
                    jsonb_build_object(
                        'record_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END
                    )
                );
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    )

    # ── Admin bypass audit for tables with "organization_id" column ──
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_log_admin_bypass_organization_id()
        RETURNS TRIGGER AS $$
        BEGIN
            IF current_setting('app.is_platform_admin', true) = 'true' THEN
                INSERT INTO rls_violation_log (
                    table_name, operation, attempted_tenant_id,
                    current_tenant_id, user_id, user_role,
                    bypass_type, details
                ) VALUES (
                    TG_TABLE_NAME, TG_OP,
                    CASE WHEN TG_OP = 'DELETE' THEN OLD.organization_id ELSE NEW.organization_id END,
                    safe_setting_uuid('app.current_org_id'),
                    safe_setting_uuid('app.current_user_id'),
                    current_setting('app.current_user_role', true),
                    'platform_admin',
                    jsonb_build_object(
                        'record_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END
                    )
                );
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    )

    # ── Cross-tenant guard for tables with "org_id" column ───────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_cross_tenant_guard_org_id()
        RETURNS TRIGGER AS $$
        DECLARE
            caller_org UUID;
        BEGIN
            IF current_setting('app.is_platform_admin', true) = 'true' THEN
                RETURN NEW;
            END IF;

            caller_org := safe_setting_uuid('app.current_org_id');

            IF caller_org IS NOT NULL
               AND NEW.org_id IS NOT NULL
               AND NEW.org_id != caller_org
            THEN
                INSERT INTO rls_violation_log (
                    table_name, operation, attempted_tenant_id,
                    current_tenant_id, user_id, user_role,
                    bypass_type, details
                ) VALUES (
                    TG_TABLE_NAME, TG_OP, NEW.org_id, caller_org,
                    safe_setting_uuid('app.current_user_id'),
                    current_setting('app.current_user_role', true),
                    'cross_tenant_attempt',
                    jsonb_build_object('record_id', NEW.id, 'blocked', true)
                );
                RAISE EXCEPTION 'Cross-tenant write blocked on %: target org % != session org %',
                    TG_TABLE_NAME, NEW.org_id, caller_org;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    )

    # ── Cross-tenant guard for tables with "organization_id" column ──
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_cross_tenant_guard_organization_id()
        RETURNS TRIGGER AS $$
        DECLARE
            caller_org UUID;
        BEGIN
            IF current_setting('app.is_platform_admin', true) = 'true' THEN
                RETURN NEW;
            END IF;

            caller_org := safe_setting_uuid('app.current_org_id');

            IF caller_org IS NOT NULL
               AND NEW.organization_id IS NOT NULL
               AND NEW.organization_id != caller_org
            THEN
                INSERT INTO rls_violation_log (
                    table_name, operation, attempted_tenant_id,
                    current_tenant_id, user_id, user_role,
                    bypass_type, details
                ) VALUES (
                    TG_TABLE_NAME, TG_OP, NEW.organization_id, caller_org,
                    safe_setting_uuid('app.current_user_id'),
                    current_setting('app.current_user_role', true),
                    'cross_tenant_attempt',
                    jsonb_build_object('record_id', NEW.id, 'blocked', true)
                );
                RAISE EXCEPTION 'Cross-tenant write blocked on %: target org % != session org %',
                    TG_TABLE_NAME, NEW.organization_id, caller_org;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    )

    # ── Attach triggers: tables with organization_id ────────────────
    for table in TABLES_WITH_ORGANIZATION_ID:
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_rls_admin_audit
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION fn_log_admin_bypass_organization_id();
        """
        )
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_cross_tenant_guard
            BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION fn_cross_tenant_guard_organization_id();
        """
        )

    # ── Attach triggers: tables with org_id ──────────────────────────
    for table in TABLES_WITH_ORG_ID:
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_rls_admin_audit
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION fn_log_admin_bypass_org_id();
        """
        )
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_cross_tenant_guard
            BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION fn_cross_tenant_guard_org_id();
        """
        )


def downgrade():
    for table in ALL_TRIGGER_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_rls_admin_audit ON {table};")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_cross_tenant_guard ON {table};")

    op.execute("DROP FUNCTION IF EXISTS fn_log_admin_bypass_org_id();")
    op.execute("DROP FUNCTION IF EXISTS fn_log_admin_bypass_organization_id();")
    op.execute("DROP FUNCTION IF EXISTS fn_cross_tenant_guard_org_id();")
    op.execute("DROP FUNCTION IF EXISTS fn_cross_tenant_guard_organization_id();")
    op.execute("DROP FUNCTION IF EXISTS safe_setting_uuid(TEXT);")
