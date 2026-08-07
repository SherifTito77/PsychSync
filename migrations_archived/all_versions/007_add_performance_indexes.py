"""Add critical performance indexes for production optimization

Revision ID: 007_add_performance_indexes
Revises: 006_add_data_anonymization_tables
Create Date: 2025-11-20 14:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "007_add_performance_indexes"
down_revision = "006_add_data_anonymization_tables"
branch_labels = None
depends_on = None


def upgrade():
    """Add critical performance indexes for production query optimization"""

    # CRITICAL: User email and status queries (most frequent lookups)
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_email_active_verified
        ON users(email, is_active, is_verified);
    """
    )

    # HIGH PRIORITY: Assessment queries by organization and status
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessment_org_status_created
        ON assessments(organization_id, status, created_at DESC);
    """
    )

    # HIGH PRIORITY: User assessment responses for scoring
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_response_user_assessment_created
        ON assessment_responses(user_id, assessment_id, created_at);
    """
    )

    # MEDIUM PRIORITY: Team member queries for optimization
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_team_member_team_user_active
        ON team_members(team_id, user_id) WHERE is_active = true;
    """
    )

    # MEDIUM PRIORITY: Organization queries
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organization_active_created
        ON organizations(is_active, created_at DESC);
    """
    )

    # LOW PRIORITY: Response scoring queries
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_response_assessment_scored
        ON assessment_responses(assessment_id, score) WHERE score IS NOT NULL;
    """
    )


def downgrade():
    """Remove performance indexes (safe CONCURRENTLY removal)"""

    indexes = [
        "idx_user_email_active_verified",
        "idx_assessment_org_status_created",
        "idx_response_user_assessment_created",
        "idx_team_member_team_user_active",
        "idx_organization_active_created",
        "idx_response_assessment_scored",
    ]

    for index_name in indexes:
        try:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name};")
        except Exception:
            # Index might not exist or cannot be dropped safely
            pass
