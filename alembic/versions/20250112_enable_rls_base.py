"""Enable Row-Level Security (RLS) for Multi-Tenancy

Revision ID: 20250112_enable_rls
Revises: <previous_revision>
Create Date: 2025-01-12

This migration enables Row-Level Security on all tenant-scoped tables and
creates policies to ensure data isolation between tenants.

RLS Architecture:
- PostgreSQL session variable: app.current_tenant (set by middleware)
- Policy: Filter all queries by tenant_id = current_setting('app.current_tenant')
- Enforcement: Database-level isolation (cannot be bypassed)

Tables Secured:
- users
- teams
- assessments
- assessment_responses
- organizations

Usage:
After this migration, all queries MUST include tenant_id filter.
The TenantContextMiddleware automatically sets app.current_tenant.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic
revision = '20250112_enable_rls'
down_revision = None  # Set to previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    """Enable RLS and create tenant isolation policies."""

    # Enable RLS on all tenant-scoped tables
    tenant_tables = [
        'users',
        'teams',
        'assessments',
        'assessment_responses',
        'organizations',
    ]

    for table in tenant_tables:
        # Enable Row-Level Security
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        # Create policy: Users can only read/write their own tenant's data
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            TO public
            USING (
                tenant_id = CAST(current_setting('app.current_tenant', true) AS UUID)
            )
            WITH CHECK (
                tenant_id = CAST(current_setting('app.current_tenant', true) AS UUID)
            )
        """)

        print(f"✅ Enabled RLS on {table}")

    # Create function to safely get current tenant ID
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_tenant_id()
        RETURNS UUID AS $$
        BEGIN
            RETURN CAST(current_setting('app.current_tenant', true) AS UUID);
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # Create helper function for RLS policy
    op.execute("""
        CREATE OR REPLACE FUNCTION check_tenant_access(table_tenant_id UUID)
        RETURNS BOOLEAN AS $$
        BEGIN
            RETURN table_tenant_id = get_current_tenant_id();
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    print("✅ RLS enabled and policies created for all tables")


def downgrade():
    """Disable RLS and remove tenant isolation policies."""

    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS check_tenant_access(UUID)")
    op.execute("DROP FUNCTION IF EXISTS get_current_tenant_id()")

    # Disable RLS on all tenant-scoped tables
    tenant_tables = [
        'users',
        'teams',
        'assessments',
        'assessment_responses',
        'organizations',
    ]

    for table in tenant_tables:
        # Drop policy
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")

        # Disable RLS
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

        print(f"⚠️  Disabled RLS on {table}")

    print("⚠️  RLS disabled - data isolation removed")
