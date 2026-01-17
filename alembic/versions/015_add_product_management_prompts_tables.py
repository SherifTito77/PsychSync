"""add_product_management_prompts_tables

Revision ID: 015_add_product_management_prompts_tables
Revises: 014_enterprise_security_implementation
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_add_product_management_prompts_tables'
down_revision = '014_enterprise_security_implementation'
branch_labels = None
depends_on = None


def upgrade():
    """Create product management prompts tables."""

    # Create prompt_executions table
    op.create_table(
        'prompt_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.String(length=50), nullable=False, comment='Prompt identifier (e.g., \'rs_001\')'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('context', postgresql.JSON(), nullable=True, comment='Additional context provided for execution'),
        sa.Column('use_ai', sa.Boolean(), nullable=False, server_default='false', comment='Whether AI enhancement was used'),
        sa.Column('outputs_generated', postgresql.JSON(), nullable=True, comment='Outputs generated from prompt'),
        sa.Column('ai_output', sa.Text(), nullable=True, comment='AI-generated suggestion if applicable'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed', comment='Execution status: completed, failed, partial'),
        sa.Column('quality_rating', sa.Integer(), nullable=True, comment='User rating of output quality (1-5)'),
        sa.Column('feedback', sa.Text(), nullable=True, comment='User feedback on execution'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for prompt_executions
    op.create_index('ix_prompt_executions_user_date', 'prompt_executions', ['user_id', 'executed_at'])
    op.create_index('ix_prompt_executions_prompt_date', 'prompt_executions', ['prompt_id', 'executed_at'])
    op.create_index(op.f('ix_prompt_executions_prompt_id'), 'prompt_executions', ['prompt_id'])
    op.create_index(op.f('ix_prompt_executions_user_id'), 'prompt_executions', ['user_id'])

    # Create prompt_templates table
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False, comment='Custom category name'),
        sa.Column('base_prompt_id', sa.String(length=50), nullable=True, comment='If derived from base prompt'),
        sa.Column('prompt_text', sa.Text(), nullable=False, comment='The prompt text/template'),
        sa.Column('expected_outputs', postgresql.JSON(), nullable=True, comment='List of expected outputs'),
        sa.Column('use_cases', postgresql.JSON(), nullable=True, comment='List of use cases'),
        sa.Column('complexity', sa.String(length=50), nullable=True, comment='low, medium, high'),
        sa.Column('estimated_time', sa.String(length=50), nullable=True, comment='Estimated completion time'),
        sa.Column('prompt_type', sa.String(length=50), nullable=True, comment='strategic, tactical, analytical, etc.'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='Number of times this template has been used'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for prompt_templates
    op.create_index(op.f('ix_prompt_templates_organization_id'), 'prompt_templates', ['organization_id'])
    op.create_index(op.f('ix_prompt_templates_created_by'), 'prompt_templates', ['created_by'])

    # Create prompt_workflows table
    op.create_table(
        'prompt_workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal', sa.String(length=255), nullable=False, comment='High-level goal this workflow addresses'),
        sa.Column('prompt_sequence', postgresql.JSON(), nullable=False, comment='Ordered list of prompt IDs'),
        sa.Column('estimated_total_time', sa.String(length=50), nullable=True, comment='Estimated completion time'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false', comment='Whether workflow is shared publicly'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for prompt_workflows
    op.create_index(op.f('ix_prompt_workflows_organization_id'), 'prompt_workflows', ['organization_id'])
    op.create_index(op.f('ix_prompt_workflows_created_by'), 'prompt_workflows', ['created_by'])

    # Create prompt_favorites table
    op.create_table(
        'prompt_favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.String(length=50), nullable=False, comment='Base prompt ID or template ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'prompt_id', name='ix_prompt_favorites_user_prompt')
    )

    # Create index for prompt_favorites
    op.create_index(op.f('ix_prompt_favorites_user_id'), 'prompt_favorites', ['user_id'])
    op.create_index(op.f('ix_prompt_favorites_prompt_id'), 'prompt_favorites', ['prompt_id'])

    # Create prompt_results table
    op.create_table(
        'prompt_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('result_type', sa.String(length=100), nullable=False, comment='Type of result: document, framework, analysis, etc.'),
        sa.Column('content', postgresql.JSON(), nullable=False, comment='Structured result data'),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='false', comment='Whether result is shared with team'),
        sa.Column('shared_with', postgresql.JSON(), nullable=True, comment='List of user IDs result is shared with'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['execution_id'], ['prompt_executions.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for prompt_results
    op.create_index(op.f('ix_prompt_results_execution_id'), 'prompt_results', ['execution_id'])
    op.create_index(op.f('ix_prompt_results_organization_id'), 'prompt_results', ['organization_id'])


def downgrade():
    """Drop product management prompts tables."""

    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('prompt_results')
    op.drop_table('prompt_favorites')
    op.drop_table('prompt_workflows')
    op.drop_table('prompt_templates')
    op.drop_table('prompt_executions')
