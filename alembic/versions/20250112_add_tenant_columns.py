"""Add tenant_id columns for multi-tenancy support

Revision ID: 20250112_add_tenant_columns
Revises: f8db50401323
Create Date: 2025-01-12

This migration adds tenant_id columns to all core tables to enable multi-tenancy.
This is a prerequisite for Row-Level Security (RLS) policies.

Tables Modified:
- users: Add tenant_id (from organization_id migration)
- teams: Add tenant_id (from organization_id migration)
- assessments: Add tenant_id (from organization_id migration)
- assessment_responses: Add tenant_id (inherited from assessment)

Migration Strategy:
1. Add tenant_id columns (nullable initially)
2. Migrate existing data from organization_id to tenant_id
3. Make columns non-nullable
4. Create indexes for performance
5. Enable RLS policies (next migration)

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '20250112_add_tenant_columns'
down_revision = 'f8db50401323'
branch_labels = None
depends_on = None


def upgrade():
    """Add tenant_id columns to core tables."""

    # ============================================
    # Step 1: Add tenant_id columns (nullable)
    # ============================================

    # Users table
    op.add_column(
        'users',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Teams table
    op.add_column(
        'teams',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Assessments table
    op.add_column(
        'assessments',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Assessment responses table
    op.add_column(
        'assessment_responses',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    print("✅ Added tenant_id columns (nullable)")

    # ============================================
    # Step 2: Migrate existing data from organization_id
    # ============================================

    # Migrate users: tenant_id = organization_id
    op.execute("""
        UPDATE users
        SET tenant_id = organization_id
        WHERE organization_id IS NOT NULL
    """)

    # Migrate teams: tenant_id = organization_id
    op.execute("""
        UPDATE teams
        SET tenant_id = organization_id
        WHERE organization_id IS NOT NULL
    """)

    # Migrate assessments: tenant_id = organization_id
    op.execute("""
        UPDATE assessments
        SET tenant_id = organization_id
        WHERE organization_id IS NOT NULL
    """)

    # Migrate assessment_responses: tenant_id from assessment
    op.execute("""
        UPDATE assessment_responses
        SET tenant_id = assessments.tenant_id
        FROM assessments
        WHERE assessment_responses.assessment_id = assessments.id
        AND assessments.tenant_id IS NOT NULL
    """)

    print("✅ Migrated existing data from organization_id to tenant_id")

    # ============================================
    # Step 3: Make columns non-nullable
    # ============================================

    # First, ensure all rows have tenant_id
    op.execute("""
        UPDATE users SET tenant_id = organization_id
        WHERE tenant_id IS NULL AND organization_id IS NOT NULL
    """)

    op.execute("""
        UPDATE teams SET tenant_id = organization_id
        WHERE tenant_id IS NULL AND organization_id IS NOT NULL
    """)

    op.execute("""
        UPDATE assessments SET tenant_id = organization_id
        WHERE tenant_id IS NULL AND organization_id IS NOT NULL
    """)

    # Set NOT NULL constraint
    op.alter_column(
        'users',
        'tenant_id',
        nullable=False
    )

    op.alter_column(
        'teams',
        'tenant_id',
        nullable=False
    )

    op.alter_column(
        'assessments',
        'tenant_id',
        nullable=False
    )

    # assessment_responses can remain nullable (responses without assessment)
    op.create_check_constraint(
        'ck_assessment_responses_tenant_or_assessment',
        'assessment_responses',
        'tenant_id IS NOT NULL OR assessment_id IS NOT NULL'
    )

    print("✅ Made tenant_id columns non-nullable")

    # ============================================
    # Step 4: Create indexes for performance
    # ============================================

    # Create indexes on tenant_id
    op.create_index(
        'idx_users_tenant_id',
        'users',
        ['tenant_id']
    )

    op.create_index(
        'idx_teams_tenant_id',
        'teams',
        ['tenant_id']
    )

    op.create_index(
        'idx_assessments_tenant_id',
        'assessments',
        ['tenant_id']
    )

    op.create_index(
        'idx_assessment_responses_tenant_id',
        'assessment_responses',
        ['tenant_id']
    )

    # Composite indexes for common queries
    op.create_index(
        'idx_users_tenant_email',
        'users',
        ['tenant_id', 'email']
    )

    op.create_index(
        'idx_teams_tenant_org',
        'teams',
        ['tenant_id', 'organization_id']
    )

    op.create_index(
        'idx_assessments_tenant_created',
        'assessments',
        ['tenant_id', 'created_at']
    )

    print("✅ Created indexes on tenant_id columns")

    # ============================================
    # Step 5: Add foreign key constraints (optional)
    # ============================================

    # Add FK to organizations table
    op.create_foreign_key(
        'fk_users_tenant_organization',
        'users',
        'organizations',
        ['tenant_id'],
        ['id']
    )

    op.create_foreign_key(
        'fk_teams_tenant_organization',
        'teams',
        'organizations',
        ['tenant_id'],
        ['id']
    )

    op.create_foreign_key(
        'fk_assessments_tenant_organization',
        'assessments',
        'organizations',
        ['tenant_id'],
        ['id']
    )

    print("✅ Added foreign key constraints to organizations")

    print("\n" + "="*80)
    print("✅ TENANT_ID COLUMNS ADDED SUCCESSFULLY")
    print("="*80)
    print("\nNext steps:")
    print("1. Run: alembic upgrade head")
    print("2. Verify data migration: SELECT COUNT(*) FROM users WHERE tenant_id IS NULL;")
    print("3. Apply RLS policies: alembic upgrade 20250112_enable_rls")
    print("4. Test tenant isolation")


def downgrade():
    """Remove tenant_id columns (rollback)."""

    # Drop foreign keys
    op.drop_constraint(
        'fk_assessments_tenant_organization',
        'assessments',
        type_='foreignkey'
    )

    op.drop_constraint(
        'fk_teams_tenant_organization',
        'teams',
        type_='foreignkey'
    )

    op.drop_constraint(
        'fk_users_tenant_organization',
        'users',
        type_='foreignkey'
    )

    # Drop indexes
    op.drop_index('idx_assessments_tenant_created')
    op.drop_index('idx_teams_tenant_org')
    op.drop_index('idx_users_tenant_email')
    op.drop_index('idx_assessment_responses_tenant_id')
    op.drop_index('idx_assessments_tenant_id')
    op.drop_index('idx_teams_tenant_id')
    op.drop_index('idx_users_tenant_id')

    # Make columns nullable
    op.alter_column('assessments', 'tenant_id', nullable=True)
    op.alter_column('teams', 'tenant_id', nullable=True)
    op.alter_column('users', 'tenant_id', nullable=True)

    # Drop check constraint
    op.drop_constraint('ck_assessment_responses_tenant_or_assessment', 'assessment_responses')

    # Drop columns
    op.drop_column('assessment_responses', 'tenant_id')
    op.drop_column('assessments', 'tenant_id')
    op.drop_column('teams', 'tenant_id')
    op.drop_column('users', 'tenant_id')

    print("⚠️  Rolled back: tenant_id columns removed")
