"""add corporate integrations tables

Revision ID: 20250114_add_corporate_integrations
Revises: 20250114_add_biometric_health
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250114_add_corporate_integrations'
down_revision = '20250114_add_biometric_health'
branch_labels = None
depends_on = None


def upgrade():
    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('integration_type', sa.Enum('EMAIL', 'CALENDAR', 'SLACK', 'JIRA', 'GITHUB', 'ZOOM', name='integrationtype'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'ERROR', 'PENDING', 'DISABLED', name='integrationstatus'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('privacy_level', sa.Enum('METADATA_ONLY', 'ANONYMIZED', 'FULL', name='privacylevel'), nullable=False, server_default='metadata_only'),
        sa.Column('sync_frequency_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('data_retention_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('requires_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('encrypted_credentials', sa.Text(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('next_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(), nullable=True),
        sa.Column('consecutive_sync_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('records_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('custom_settings', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integrations_id'), 'integrations', ['id'], unique=False)
    op.create_index(op.f('ix_integrations_integration_type'), 'integrations', ['integration_type'], unique=False)
    op.create_index(op.f('ix_integrations_organization_id'), 'integrations', ['organization_id'], unique=False)

    # Create integration_consents table
    op.create_table(
        'integration_consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('consent_version', sa.String(length=50), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_consents_id'), 'integration_consents', ['id'], unique=False)

    # Create behavioral_profiles table
    op.create_table(
        'behavioral_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('profile_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('time_window_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('burnout_risk_score', sa.Float(), nullable=False),
        sa.Column('toxicity_exposure_score', sa.Float(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('retention_risk_score', sa.Float(), nullable=False),
        sa.Column('work_life_balance_score', sa.Float(), nullable=False),
        sa.Column('email_signals', postgresql.JSON(), nullable=True),
        sa.Column('calendar_signals', postgresql.JSON(), nullable=True),
        sa.Column('slack_signals', postgresql.JSON(), nullable=True),
        sa.Column('jira_signals', postgresql.JSON(), nullable=True),
        sa.Column('data_sources_active', postgresql.JSON(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_behavioral_profiles_id'), 'behavioral_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_behavioral_profiles_profile_date'), 'behavioral_profiles', ['profile_date'], unique=False)
    op.create_index(op.f('ix_behavioral_profiles_user_id'), 'behavioral_profiles', ['user_id'], unique=False)

    # Create behavioral_insights table
    op.create_table(
        'behavioral_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('data_sources', postgresql.JSON(), nullable=True),
        sa.Column('indicators', postgresql.JSON(), nullable=True),
        sa.Column('recommendations', postgresql.JSON(), nullable=True),
        sa.Column('signal_values', postgresql.JSON(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['profile_id'], ['behavioral_profiles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_behavioral_insights_category'), 'behavioral_insights', ['category'], unique=False)
    op.create_index(op.f('ix_behavioral_insights_detected_at'), 'behavioral_insights', ['detected_at'], unique=False)
    op.create_index(op.f('ix_behavioral_insights_id'), 'behavioral_insights', ['id'], unique=False)
    op.create_index(op.f('ix_behavioral_insights_severity'), 'behavioral_insights', ['severity'], unique=False)
    op.create_index(op.f('ix_behavioral_insights_user_id'), 'behavioral_insights', ['user_id'], unique=False)

    # Create integration_sync_logs table
    op.create_table(
        'integration_sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('records_fetched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(), nullable=True),
        sa.Column('sync_metadata', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_sync_logs_id'), 'integration_sync_logs', ['id'], unique=False)

    # Create email_metadata table
    op.create_table(
        'email_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=False),
        sa.Column('sender', sa.String(length=255), nullable=False),
        sa.Column('recipients', postgresql.JSON(), nullable=True),
        sa.Column('cc_recipients', postgresql.JSON(), nullable=True),
        sa.Column('bcc_recipients', postgresql.JSON(), nullable=True),
        sa.Column('subject_length', sa.Integer(), nullable=False),
        sa.Column('is_urgent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('urgency_level', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('hour_of_day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('is_after_hours', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_weekend', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_external', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('in_reply_to', sa.String(length=255), nullable=True),
        sa.Column('thread_size', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('response_time_seconds', sa.Float(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('attachment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['connection_id'], ['integrations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    op.create_index(op.f('ix_email_metadata_day_of_week'), 'email_metadata', ['day_of_week'], unique=False)
    op.create_index(op.f('ix_email_metadata_hour_of_day'), 'email_metadata', ['hour_of_day'], unique=False)
    op.create_index(op.f('ix_email_metadata_id'), 'email_metadata', ['id'], unique=False)
    op.create_index(op.f('ix_email_metadata_is_after_hours'), 'email_metadata', ['is_after_hours'], unique=False)
    op.create_index(op.f('ix_email_metadata_is_weekend'), 'email_metadata', ['is_weekend'], unique=False)
    op.create_index(op.f('ix_email_metadata_message_id'), 'email_metadata', ['message_id'], unique=True)
    op.create_index(op.f('ix_email_metadata_sent_at'), 'email_metadata', ['sent_at'], unique=False)
    op.create_index(op.f('ix_email_metadata_thread_id'), 'email_metadata', ['thread_id'], unique=False)
    op.create_index(op.f('ix_email_metadata_user_id'), 'email_metadata', ['user_id'], unique=False)

    # Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('attendees_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meeting_type', sa.String(length=50), nullable=False),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_all_day', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_after_hours', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_weekend', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_back_to_back', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gap_minutes_before', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gap_minutes_after', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('organizer_email', sa.String(length=255), nullable=False),
        sa.Column('is_organizer', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['connection_id'], ['integrations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_calendar_events_event_id'), 'calendar_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_calendar_events_id'), 'calendar_events', ['id'], unique=False)
    op.create_index(op.f('ix_calendar_events_is_after_hours'), 'calendar_events', ['is_after_hours'], unique=False)
    op.create_index(op.f('ix_calendar_events_is_weekend'), 'calendar_events', ['is_weekend'], unique=False)
    op.create_index(op.f('ix_calendar_events_start_time'), 'calendar_events', ['start_time'], unique=False)
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)

    # Create slack_messages table
    op.create_table(
        'slack_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('channel_id', sa.String(length=255), nullable=False),
        sa.Column('channel_name', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('hour_of_day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('reply_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('has_mentions', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_links', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_attachments', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emoji_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_after_hours', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_weekend', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['connection_id'], ['integrations.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    op.create_index(op.f('ix_slack_messages_channel_id'), 'slack_messages', ['channel_id'], unique=False)
    op.create_index(op.f('ix_slack_messages_id'), 'slack_messages', ['id'], unique=False)
    op.create_index(op.f('ix_slack_messages_is_after_hours'), 'slack_messages', ['is_after_hours'], unique=False)
    op.create_index(op.f('ix_slack_messages_is_weekend'), 'slack_messages', ['is_weekend'], unique=False)
    op.create_index(op.f('ix_slack_messages_message_id'), 'slack_messages', ['message_id'], unique=True)
    op.create_index(op.f('ix_slack_messages_timestamp'), 'slack_messages', ['timestamp'], unique=False)
    op.create_index(op.f('ix_slack_messages_user_id'), 'slack_messages', ['user_id'], unique=False)


def downgrade():
    op.drop_table('slack_messages')
    op.drop_table('calendar_events')
    op.drop_table('email_metadata')
    op.drop_table('integration_sync_logs')
    op.drop_table('behavioral_insights')
    op.drop_table('behavioral_profiles')
    op.drop_table('integration_consents')
    op.drop_table('integrations')
