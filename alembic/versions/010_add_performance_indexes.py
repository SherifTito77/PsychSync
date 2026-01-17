"""Add performance indexes

Revision ID: 010_add_performance_indexes
Revises: 009_add_critical_database_indexes
Create Date: 2024-01-21 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '010_add_performance_indexes'
down_revision = '009_add_critical_database_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance-optimizing database indexes."""

    # Users table indexes for common query patterns
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_org_created_at
        ON users(organization_id, created_at DESC);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active
        ON users(email) WHERE is_active = true;
    """)

    # Assessments table indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_user_status_created
        ON assessments(user_id, status, created_at DESC);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_org_type
        ON assessments(organization_id, assessment_type)
        WHERE status = 'active';
    """)

    # Responses table indexes for analytics queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_assessment_created
        ON responses(assessment_id, created_at DESC);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_user_score
        ON responses(user_id, total_score)
        WHERE total_score IS NOT NULL;
    """)

    # Teams table indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_org_created
        ON teams(organization_id, created_at DESC);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_name_active
        ON teams(name) WHERE is_active = true;
    """)

    # Organization relationships
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_teams_user_team
        ON user_teams(user_id, team_id);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_teams_role
        ON user_teams(role) WHERE role IN ('admin', 'manager');
    """)

    # Response analytics indexes
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_response_analytics_response_question
        ON response_analytics(response_id, question_id);
    """)

    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_response_analytics_score_value
        ON response_analytics(score_value)
        WHERE score_value IS NOT NULL;
    """)

def downgrade() -> None:
    """Remove performance indexes."""

    # Drop indexes in reverse order
    indexes = [
        'idx_response_analytics_score_value',
        'idx_response_analytics_response_question',
        'idx_user_teams_role',
        'idx_user_teams_user_team',
        'idx_teams_name_active',
        'idx_teams_org_created',
        'idx_responses_user_score',
        'idx_responses_assessment_created',
        'idx_assessments_org_type',
        'idx_assessments_user_status_created',
        'idx_users_email_active',
        'idx_users_org_created_at'
    ]

    for index_name in indexes:
        try:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name};")
        except Exception:
            # Index might not exist or concurrent operation not supported
            pass
