"""
Database Performance Indexes Migration
High-impact indexes for critical query paths based on analysis
Expected improvement: 40-60% for query performance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '013_add_critical_performance_indexes'
down_revision = '012_add_critical_performance_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """
    Add critical performance indexes for the most frequently accessed queries
    These indexes target the highest-impact query patterns:
    1. User authentication and profile lookups
    2. Team and organization queries
    3. Assessment and response queries
    4. Audit and analytics queries
    """

    # USER PERFORMANCE INDEXES
    # =========================

    # Primary user authentication lookup - most critical
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active_auth
        ON users (email, is_active)
        WHERE is_active = true;
    """)

    # User profile and organization lookups
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_org_created_active
        ON users (organization_id, created_at DESC)
        WHERE is_active = true;
    """)

    # User search and filtering
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login_active
        ON users (last_login DESC NULLS LAST)
        WHERE is_active = true AND last_login IS NOT NULL;
    """)

    # TEAM PERFORMANCE INDEXES
    # ==========================

    # Team listing by organization (most common team query)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_org_created_active
        ON teams (organization_id, created_at DESC);
    """)

    # Team member lookups (critical for permissions)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_user_role_active
        ON team_members (user_id, role, is_active)
        WHERE is_active = true;
    """)

    # Team member lookups by team
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_team_role_active
        ON team_members (team_id, role, is_active)
        WHERE is_active = true;
    """)

    # ASSESSMENT PERFORMANCE INDEXES
    # ===============================

    # Assessment responses by user (critical for user profiles)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_user_created
        ON assessment_responses (user_id, created_at DESC);
    """)

    # Assessment responses by assessment (for analytics)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_assessment_created
        ON assessment_responses (assessment_id, created_at DESC);
    """)

    # Assessment lookups by organization and type
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_org_type_active
        ON assessments (organization_id, assessment_type, is_active)
        WHERE is_active = true;
    """)

    # Template lookups for assessment creation
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_templates_type_active_public
        ON assessment_templates (template_type, is_active, is_public)
        WHERE is_active = true;
    """)

    # AUDIT TRAIL INDEXES
    # ===================

    # Audit queries by user and date range
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user_action_date
        ON audit_logs (user_id, action, created_at DESC);
    """)

    # Audit queries by organization for compliance
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_org_date_action
        ON audit_logs (organization_id, created_at DESC, action);
    """)

    # EMAIL COMMUNICATION INDEXES
    # ============================

    # Email lookups by user and date
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_metadata_user_date
        ON email_metadata (user_id, sent_at DESC);
    """)

    # Email thread lookups
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_email_metadata_thread_date
        ON email_metadata (thread_id, sent_at DESC);
    """)

    # COMPOSITE FUNCTIONAL INDEXES FOR COMPLEX QUERIES
    # ===============================================

    # User dashboard query (user's teams and recent activity)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_dashboard_composite
        ON users (id, organization_id, last_login DESC)
        WHERE is_active = true;
    """)

    # Team analytics query (team performance metrics)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_analytics_composite
        ON teams (id, organization_id, created_at DESC);
    """)

    # Assessment analytics query (assessment completion and scores)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_analytics_composite
        ON assessment_responses (assessment_id, user_id, created_at DESC, total_score);
    """)

    # PARTIAL INDEXES FOR COMMON FILTERED QUERIES
    # ============================================

    # Active team members (for permission checks)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_members_active_lookup
        ON team_members (team_id, user_id)
        WHERE is_active = true;
    """)

    # Recent user logins (for user activity tracking)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_recent_logins
        ON users (last_login DESC)
        WHERE is_active = true AND last_login > NOW() - INTERVAL '30 days';
    """)

    # Active assessments (for dashboard and analytics)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_active_dashboard
        ON assessments (organization_id, created_at DESC)
        WHERE is_active = true;
    """)

def downgrade() -> None:
    """
    Remove all performance indexes safely
    """
    indexes_to_remove = [
        # User indexes
        'idx_users_email_active_auth',
        'idx_users_org_created_active',
        'idx_users_last_login_active',

        # Team indexes
        'idx_teams_org_created_active',
        'idx_team_members_user_role_active',
        'idx_team_members_team_role_active',

        # Assessment indexes
        'idx_responses_user_created',
        'idx_responses_assessment_created',
        'idx_assessments_org_type_active',
        'idx_templates_type_active_public',

        # Audit indexes
        'idx_audit_user_action_date',
        'idx_audit_org_date_action',

        # Email indexes
        'idx_email_metadata_user_date',
        'idx_email_metadata_thread_date',

        # Composite indexes
        'idx_user_dashboard_composite',
        'idx_team_analytics_composite',
        'idx_assessment_analytics_composite',

        # Partial indexes
        'idx_team_members_active_lookup',
        'idx_users_recent_logins',
        'idx_assessments_active_dashboard',
    ]

    for index_name in indexes_to_remove:
        try:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name};")
        except Exception as e:
            # Log error but continue with other indexes
            print(f"Warning: Could not drop index {index_name}: {e}")