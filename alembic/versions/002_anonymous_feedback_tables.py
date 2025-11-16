"""Add anonymous feedback system tables

Revision ID: 002_anonymous_feedback_tables
Revises: 001_base_tables
Create Date: 2025-11-12 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_anonymous_feedback_tables'
down_revision: Union[str, None] = '001_base_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create anonymous_feedback table
    op.create_table('anonymous_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tracking_id', sa.String(length=255), nullable=False),
        sa.Column('feedback_type', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id_hash', sa.String(length=255), nullable=True),
        sa.Column('evidence_urls', sa.JSON(), nullable=True),
        sa.Column('submitter_fingerprint', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_date', sa.DateTime(), nullable=True),
        sa.Column('assigned_reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('public_resolution_notes', sa.Text(), nullable=True),
        sa.Column('urgency_score', sa.String(length=10), nullable=True),
        sa.Column('auto_assigned', sa.String(length=10), nullable=True),
        sa.Column('investigation_priority', sa.String(length=20), nullable=True),
        sa.Column('incident_date', sa.DateTime(), nullable=True),
        sa.Column('actions_taken_summary', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_reviewer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracking_id')
    )
    op.create_index('ix_anonymous_feedback_tracking_id', 'anonymous_feedback', ['tracking_id'], unique=False)

    # Create anonymous_feedback_pattern table
    op.create_table('anonymous_feedback_pattern',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pattern_type', sa.String(length=100), nullable=False),
        sa.Column('affected_categories', sa.JSON(), nullable=True),
        sa.Column('pattern_description', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.String(length=10), nullable=True),
        sa.Column('sample_size', sa.String(length=20), nullable=True),
        sa.Column('time_period_days', sa.String(length=10), nullable=True),
        sa.Column('first_detected', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create anonymous_feedback_template table
    op.create_table('anonymous_feedback_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feedback_type', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('description_template', sa.Text(), nullable=True),
        sa.Column('example_situations', sa.JSON(), nullable=True),
        sa.Column('guidance_questions', sa.JSON(), nullable=True),
        sa.Column('required_elements', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('anonymous_feedback_template')
    op.drop_table('anonymous_feedback_pattern')
    op.drop_index('ix_anonymous_feedback_tracking_id', table_name='anonymous_feedback')
    op.drop_table('anonymous_feedback')