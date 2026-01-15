"""add satisfaction tracking models

Revision ID: 20250112_satisfaction_tracking
Revises: 20250112_add_tenant_columns
Create Date: 2025-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250112_satisfaction_tracking'
down_revision = '20250112_add_tenant_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Create satisfaction_surveys table
    op.create_table(
        'satisfaction_surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('survey_type', sa.Enum('csat', 'nps', 'ces', name='surveytype'), nullable=False),
        sa.Column('touchpoint_type', sa.Enum('onboarding', 'support', 'feature_usage', 'assessment_quality',
                                            'purchase', 'team_setup', 'report_sharing', name='touchpointtype'),
                  nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('follow_up_consent', sa.Boolean(), default=True),
        sa.Column('nps_category', sa.Enum('promoter', 'passive', 'detractor', name='npscategory'), nullable=True),
        sa.Column('survey_channel', sa.String(length=50), nullable=True),
        sa.Column('response_time_seconds', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('context', postgresql.JSONB(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create indexes for satisfaction_surveys
    op.create_index('idx_satisfaction_survey_type_date', 'satisfaction_surveys', ['survey_type', 'responded_at'])
    op.create_index('idx_satisfaction_org_date', 'satisfaction_surveys', ['organization_id', 'responded_at'])

    # Create satisfaction_aggregations table
    op.create_table(
        'satisfaction_aggregations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('survey_type', sa.Enum('csat', 'nps', 'ces', name='surveytype'), nullable=False),
        sa.Column('touchpoint_type', sa.Enum('onboarding', 'support', 'feature_usage', 'assessment_quality',
                                            'purchase', 'team_setup', 'report_sharing', name='touchpointtype'),
                  nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_responses', sa.Integer(), default=0),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('satisfied_count', sa.Integer(), default=0),
        sa.Column('satisfaction_percentage', sa.Float(), nullable=True),
        sa.Column('promoter_count', sa.Integer(), default=0),
        sa.Column('passive_count', sa.Integer(), default=0),
        sa.Column('detractor_count', sa.Integer(), default=0),
        sa.Column('nps_score', sa.Integer(), nullable=True),
        sa.Column('easy_count', sa.Integer(), default=0),
        sa.Column('ease_percentage', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create indexes for satisfaction_aggregations
    op.create_index('idx_satisfaction_agg_period', 'satisfaction_aggregations', ['period_type', 'period_start'])
    op.create_index('idx_satisfaction_agg_org', 'satisfaction_aggregations', ['organization_id', 'period_type'])

    # Create composite_satisfaction_indices table
    op.create_table(
        'composite_satisfaction_indices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('csat_score', sa.Float(), nullable=True),
        sa.Column('nps_raw', sa.Integer(), nullable=True),
        sa.Column('nps_normalized', sa.Float(), nullable=True),
        sa.Column('ces_score', sa.Float(), nullable=True),
        sa.Column('csi_score', sa.Float(), nullable=False),
        sa.Column('performance_level', sa.String(length=20), nullable=False),
        sa.Column('previous_csi_score', sa.Float(), nullable=True),
        sa.Column('change_amount', sa.Float(), nullable=True),
        sa.Column('change_percentage', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create indexes for composite_satisfaction_indices
    op.create_index('idx_csi_org_period', 'composite_satisfaction_indices', ['organization_id', 'period_start'])
    op.create_index('idx_csi_score', 'composite_satisfaction_indices', ['csi_score'])

    # Create customer_lifecycle_stages table
    op.create_table(
        'customer_lifecycle_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('current_stage', sa.String(length=50), nullable=False, index=True),
        sa.Column('previous_stage', sa.String(length=50), nullable=True),
        sa.Column('stage_entry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('stage_exit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('days_in_stage', sa.Integer(), nullable=True),
        sa.Column('entered_via', sa.String(length=100), nullable=True),
        sa.Column('conversion_source', sa.String(length=100), nullable=True),
        sa.Column('context', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create indexes for customer_lifecycle_stages
    op.create_index('idx_lifecycle_user_stage', 'customer_lifecycle_stages', ['user_id', 'current_stage'])
    op.create_index('idx_lifecycle_org_stage', 'customer_lifecycle_stages', ['organization_id', 'current_stage'])

    # Create satisfaction_follow_ups table
    op.create_table(
        'satisfaction_follow_ups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('satisfaction_surveys.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True, index=True),
        sa.Column('alert_level', sa.String(length=20), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('follow_up_type', sa.String(length=50), nullable=False),
        sa.Column('follow_up_status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('customer_sentiment_after', sa.String(length=20), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create indexes for satisfaction_follow_ups
    op.create_index('idx_follow_up_alert', 'satisfaction_follow_ups', ['alert_level', 'follow_up_status'])
    op.create_index('idx_follow_up_due', 'satisfaction_follow_ups', ['due_at', 'follow_up_status'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('satisfaction_follow_ups')
    op.drop_table('customer_lifecycle_stages')
    op.drop_table('composite_satisfaction_indices')
    op.drop_table('satisfaction_aggregations')
    op.drop_table('satisfaction_surveys')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS surveytype')
    op.execute('DROP TYPE IF EXISTS touchpointtype')
    op.execute('DROP TYPE IF EXISTS npscategory')
