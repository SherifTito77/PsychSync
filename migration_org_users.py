"""
Add organization_id to users table

Revision ID: add_org_to_users_001
Create Date: 2025-10-29
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_org_to_users_001'
down_revision = None  # Replace with your previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Check if the column already exists (in case it's already there)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'organization_id' not in columns:
        # Add organization_id column to users table
        op.add_column('users', 
            sa.Column('organization_id', sa.Integer(), nullable=True)
        )
        
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_users_organization_id',
            'users', 'organizations',
            ['organization_id'], ['id'],
            ondelete='SET NULL'
        )
        
        # Create index for better query performance
        op.create_index(
            'ix_users_organization_id',
            'users',
            ['organization_id']
        )


def downgrade():
    # Drop index
    op.drop_index('ix_users_organization_id', table_name='users')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    
    # Drop column
    op.drop_column('users', 'organization_id')
