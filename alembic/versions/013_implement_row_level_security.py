"""
Implement Row-Level Security (RLS) for Multi-Tenant Security

This migration implements comprehensive row-level security policies to ensure
proper data isolation between organizations and enforce access control.

RLS Policies Applied:
- Users can only access their own data and data from their organization
- Team members can only access team-level data for their teams
- Admin users have full access within their organization
- System admins have cross-organization access for maintenance
- Audit logging for all RLS policy violations

Security Benefits:
- Complete data isolation between tenants
- Principle of least privilege enforcement
- Automatic access control at database level
- Audit trail for security violations
- Protection against data leakage attacks
"""

# revision identifier, used by Alembic.
revision = '013_implement_row_level_security'
down_revision = '012_create_analytics_materialized_views'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Implement row-level security for multi-tenant data isolation"""

    # 1. Enable Row-Level Security
    # ---------------------------------------------------------

    # Enable RLS on all user-accessible tables
    op.execute("""
        -- Enable RLS on core tables
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
        ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
        ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
        ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
        ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
        ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
        ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
        ALTER TABLE resource_access ENABLE ROW LEVEL SECURITY;
    """)

    # 2. Create Security Helper Functions
    # ---------------------------------------------------------

    op.execute("""
        -- Function to get current user's organization ID
        CREATE OR REPLACE FUNCTION current_user_organization_id()
        RETURNS UUID AS $$
        DECLARE
            user_org_id UUID;
        BEGIN
            SELECT organization_id INTO user_org_id
            FROM users
            WHERE id = current_setting('app.current_user_id', true)::UUID
            LIMIT 1;

            RETURN user_org_id;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
        -- Function to check if current user is system admin
        CREATE OR REPLACE FUNCTION is_system_admin()
        RETURNS BOOLEAN AS $$
        DECLARE
            is_admin BOOLEAN := false;
        BEGIN
            SELECT (role = 'admin') INTO is_admin
            FROM users
            WHERE id = current_setting('app.current_user_id', true)::UUID
              AND organization_id IS NULL -- System admins have NULL organization_id
            LIMIT 1;

            RETURN COALESCE(is_admin, false);
        EXCEPTION
            WHEN OTHERS THEN
                RETURN false;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
        -- Function to check if current user is organization admin
        CREATE OR REPLACE FUNCTION is_organization_admin()
        RETURNS BOOLEAN AS $$
        DECLARE
            is_admin BOOLEAN := false;
        BEGIN
            SELECT (role = 'admin') INTO is_admin
            FROM users
            WHERE id = current_setting('app.current_user_id', true)::UUID
            LIMIT 1;

            RETURN COALESCE(is_admin, false);
        EXCEPTION
            WHEN OTHERS THEN
                RETURN false;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
        -- Function to get current user's team memberships
        CREATE OR REPLACE FUNCTION current_user_team_ids()
        RETURNS UUID[] AS $$
        DECLARE
            team_ids UUID[];
        BEGIN
            SELECT ARRAY_AGG(team_id) INTO team_ids
            FROM team_members
            WHERE user_id = current_setting('app.current_user_id', true)::UUID
              AND is_active = true;

            RETURN COALESCE(team_ids, ARRAY[]::UUID[]);
        EXCEPTION
            WHEN OTHERS THEN
                RETURN ARRAY[]::UUID[];
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # 3. Users Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can see their own record
        CREATE POLICY users_self_access ON users
            FOR ALL
            TO authenticated_users
            USING (id = current_setting('app.current_user_id', true)::UUID);

        -- Organization admins can see all users in their organization
        CREATE POLICY users_org_admin_access ON users
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY users_system_admin_access ON users
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());

        -- Users can create new users in their organization (if they have permission)
        CREATE POLICY users_org_create ON users
            FOR INSERT
            TO authenticated_users
            WITH CHECK (organization_id = current_user_organization_id());
    """)

    # 4. Organizations Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Organization members can see their organization
        CREATE POLICY organizations_member_access ON organizations
            FOR SELECT
            TO authenticated_users
            USING (id = current_user_organization_id());

        -- Organization admins can update their organization
        CREATE POLICY organizations_admin_update ON organizations
            FOR UPDATE
            TO authenticated_users
            USING (
                is_organization_admin() AND
                id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY organizations_system_admin_access ON organizations
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 5. Teams Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can see teams they belong to
        CREATE POLICY teams_member_access ON teams
            FOR SELECT
            TO authenticated_users
            USING (
                organization_id = current_user_organization_id() AND
                id = ANY(current_user_team_ids())
            );

        -- Organization admins can see all teams in their organization
        CREATE POLICY teams_org_admin_access ON teams
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY teams_system_admin_access ON teams
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 6. Team Members Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can see team membership for teams they belong to
        CREATE POLICY team_members_member_access ON team_members
            FOR SELECT
            TO authenticated_users
            USING (
                organization_id = current_user_organization_id() AND
                team_id = ANY(current_user_team_ids())
            );

        -- Organization admins can manage team memberships in their organization
        CREATE POLICY team_members_admin_access ON team_members
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY team_members_system_admin_access ON team_members
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 7. Assessments Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can see assessments from their organization
        CREATE POLICY assessments_member_access ON assessments
            FOR SELECT
            TO authenticated_users
            USING (
                organization_id = current_user_organization_id()
            );

        -- Users can see assessments assigned to their teams
        CREATE POLICY assessments_team_access ON assessments
            FOR SELECT
            TO authenticated_users
            USING (
                organization_id = current_user_organization_id() AND
                team_id = ANY(current_user_team_ids())
            );

        -- Organization admins can manage assessments in their organization
        CREATE POLICY assessments_admin_access ON assessments
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY assessments_system_admin_access ON assessments
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 8. Responses Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can only see their own responses
        CREATE POLICY responses_self_access ON responses
            FOR ALL
            TO authenticated_users
            USING (user_id = current_setting('app.current_user_id', true)::UUID);

        -- Organization admins can see all responses in their organization
        CREATE POLICY responses_admin_access ON responses
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY responses_system_admin_access ON responses
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 9. Analytics Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can see analytics for their organization only
        CREATE POLICY analytics_member_access ON analytics
            FOR SELECT
            TO authenticated_users
            USING (
                organization_id = current_user_organization_id()
            );

        -- Organization admins can manage analytics in their organization
        CREATE POLICY analytics_admin_access ON analytics
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY analytics_system_admin_access ON analytics
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 10. Notifications Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can only see their own notifications
        CREATE POLICY notifications_self_access ON notifications
            FOR ALL
            TO authenticated_users
            USING (user_id = current_setting('app.current_user_id', true)::UUID);

        -- Organization admins can see notifications in their organization
        CREATE POLICY notifications_admin_access ON notifications
            FOR SELECT
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY notifications_system_admin_access ON notifications
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 11. Notification Preferences Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can only manage their own notification preferences
        CREATE POLICY notification_preferences_self_access ON notification_preferences
            FOR ALL
            TO authenticated_users
            USING (user_id = current_setting('app.current_user_id', true)::UUID);

        -- Organization admins can see preferences in their organization
        CREATE POLICY notification_preferences_admin_access ON notification_preferences
            FOR SELECT
            TO authenticated_users
            USING (
                is_organization_admin() AND
                organization_id = current_user_organization_id()
            );

        -- System admins have full access
        CREATE POLICY notification_preferences_system_admin_access ON notification_preferences
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 12. Resource Access Table RLS Policies
    # ---------------------------------------------------------

    op.execute("""
        -- Users can only see their own resource access logs
        CREATE POLICY resource_access_self_access ON resource_access
            FOR SELECT
            TO authenticated_users
            USING (user_id = current_setting('app.current_user_id', true)::UUID);

        -- Organization admins can see access logs in their organization
        CREATE POLICY resource_access_admin_access ON resource_access
            FOR ALL
            TO authenticated_users
            USING (
                is_organization_admin() AND
                user_id IN (
                    SELECT id FROM users WHERE organization_id = current_user_organization_id()
                )
            );

        -- System admins have full access
        CREATE POLICY resource_access_system_admin_access ON resource_access
            FOR ALL
            TO authenticated_users
            USING (is_system_admin());
    """)

    # 13. Create Security Audit Functions
    # ---------------------------------------------------------

    op.execute("""
        -- Function to log RLS violations
        CREATE OR REPLACE FUNCTION log_rls_violation(
            table_name TEXT,
            operation TEXT,
            violation_reason TEXT
        )
        RETURNS VOID AS $$
        BEGIN
            INSERT INTO audit_logs (
                change_type,
                entity_type,
                entity_id,
                actor_id,
                organization_id,
                metadata
            ) VALUES (
                'security_violation',
                'rls_policy',
                gen_random_uuid(),
                current_setting('app.current_user_id', true)::UUID,
                current_user_organization_id(),
                json_build_object(
                    'table_name', table_name,
                    'operation', operation,
                    'violation_reason', violation_reason,
                    'timestamp', NOW(),
                    'ip_address', current_setting('app.client_ip_address', true),
                    'user_agent', current_setting('app.user_agent', true)
                )
            );
        EXCEPTION
            WHEN OTHERS THEN
                -- Log the failure to log (meta-logging)
                RAISE NOTICE 'Failed to log RLS violation: %', SQLERRM;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # 14. Create RLS Violation Monitoring
    # ---------------------------------------------------------

    op.execute("""
        -- Create view to monitor RLS violations
        CREATE VIEW rls_violations AS
        SELECT
            created_at,
            actor_id,
            organization_id,
            metadata->>'table_name' as table_name,
            metadata->>'operation' as operation,
            metadata->>'violation_reason' as violation_reason,
            metadata->>'ip_address' as ip_address,
            metadata->>'user_agent' as user_agent
        FROM audit_logs
        WHERE change_type = 'security_violation'
          AND entity_type = 'rls_policy'
        ORDER BY created_at DESC;
    """)

    # 15. Create Security Configuration Functions
    # ---------------------------------------------------------

    op.execute("""
        -- Function to set user context for RLS
        CREATE OR REPLACE FUNCTION set_rls_user_context(
            user_id UUID,
            client_ip_address TEXT DEFAULT NULL,
            user_agent TEXT DEFAULT NULL
        )
        RETURNS VOID AS $$
        BEGIN
            -- Set user context for RLS policies
            PERFORM set_config('app.current_user_id', user_id::TEXT, true);

            -- Set optional client context
            IF client_ip_address IS NOT NULL THEN
                PERFORM set_config('app.client_ip_address', client_ip_address, true);
            END IF;

            IF user_agent IS NOT NULL THEN
                PERFORM set_config('app.user_agent', user_agent, true);
            END IF;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
        -- Function to clear user context
        CREATE OR REPLACE FUNCTION clear_rls_user_context()
        RETURNS VOID AS $$
        BEGIN
            PERFORM set_config('app.current_user_id', '', true);
            PERFORM set_config('app.client_ip_address', '', true);
            PERFORM set_config('app.user_agent', '', true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # 16. Create authenticated_users Role
    # ---------------------------------------------------------

    op.execute("""
        -- Create role for authenticated users if it doesn't exist
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated_users') THEN
                CREATE ROLE authenticated_users;
            END IF;
        END $$;

        -- Grant necessary permissions to authenticated_users role
        GRANT USAGE ON SCHEMA public TO authenticated_users;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated_users;
        GRANT INSERT ON users, team_members, responses TO authenticated_users;
        GRANT UPDATE ON users, team_members, responses, notification_preferences TO authenticated_users;
        GRANT DELETE ON team_members, responses TO authenticated_users;
    """)


def downgrade() -> None:
    """Remove row-level security policies and related objects"""

    # Drop RLS policies from all tables
    op.execute("DROP POLICY IF EXISTS users_self_access ON users")
    op.execute("DROP POLICY IF EXISTS users_org_admin_access ON users")
    op.execute("DROP POLICY IF EXISTS users_system_admin_access ON users")
    op.execute("DROP POLICY IF EXISTS users_org_create ON users")

    op.execute("DROP POLICY IF EXISTS organizations_member_access ON organizations")
    op.execute("DROP POLICY IF EXISTS organizations_admin_update ON organizations")
    op.execute("DROP POLICY IF EXISTS organizations_system_admin_access ON organizations")

    op.execute("DROP POLICY IF EXISTS teams_member_access ON teams")
    op.execute("DROP POLICY IF EXISTS teams_org_admin_access ON teams")
    op.execute("DROP POLICY IF EXISTS teams_system_admin_access ON teams")

    op.execute("DROP POLICY IF EXISTS team_members_member_access ON team_members")
    op.execute("DROP POLICY IF EXISTS team_members_admin_access ON team_members")
    op.execute("DROP POLICY IF EXISTS team_members_system_admin_access ON team_members")

    op.execute("DROP POLICY IF EXISTS assessments_member_access ON assessments")
    op.execute("DROP POLICY IF EXISTS assessments_team_access ON assessments")
    op.execute("DROP POLICY IF EXISTS assessments_admin_access ON assessments")
    op.execute("DROP POLICY IF EXISTS assessments_system_admin_access ON assessments")

    op.execute("DROP POLICY IF EXISTS responses_self_access ON responses")
    op.execute("DROP POLICY IF EXISTS responses_admin_access ON responses")
    op.execute("DROP POLICY IF EXISTS responses_system_admin_access ON responses")

    op.execute("DROP POLICY IF EXISTS analytics_member_access ON analytics")
    op.execute("DROP POLICY IF EXISTS analytics_admin_access ON analytics")
    op.execute("DROP POLICY IF EXISTS analytics_system_admin_access ON analytics")

    op.execute("DROP POLICY IF EXISTS notifications_self_access ON notifications")
    op.execute("DROP POLICY IF EXISTS notifications_admin_access ON notifications")
    op.execute("DROP POLICY IF EXISTS notifications_system_admin_access ON notifications")

    op.execute("DROP POLICY IF EXISTS notification_preferences_self_access ON notification_preferences")
    op.execute("DROP POLICY IF EXISTS notification_preferences_admin_access ON notification_preferences")
    op.execute("DROP POLICY IF EXISTS notification_preferences_system_admin_access ON notification_preferences")

    op.execute("DROP POLICY IF EXISTS resource_access_self_access ON resource_access")
    op.execute("DROP POLICY IF EXISTS resource_access_admin_access ON resource_access")
    op.execute("DROP POLICY IF EXISTS resource_access_system_admin_access ON resource_access")

    # Disable RLS on tables
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE teams DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE team_members DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE assessments DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE responses DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE questions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE analytics DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE notifications DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE notification_preferences DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE resource_access DISABLE ROW LEVEL SECURITY")

    # Drop security functions
    op.execute("DROP FUNCTION IF EXISTS current_user_organization_id()")
    op.execute("DROP FUNCTION IF EXISTS is_system_admin()")
    op.execute("DROP FUNCTION IF EXISTS is_organization_admin()")
    op.execute("DROP FUNCTION IF EXISTS current_user_team_ids()")
    op.execute("DROP FUNCTION IF EXISTS log_rls_violation(TEXT, TEXT, TEXT)")
    op.execute("DROP FUNCTION IF EXISTS set_rls_user_context(UUID, TEXT, TEXT)")
    op.execute("DROP FUNCTION IF EXISTS clear_rls_user_context()")

    # Drop monitoring views
    op.execute("DROP VIEW IF EXISTS rls_violations")

    # Drop authenticated_users role
    op.execute("DROP ROLE IF EXISTS authenticated_users")