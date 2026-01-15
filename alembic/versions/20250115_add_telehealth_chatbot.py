"""Add telehealth, chatbot, and mobile support tables

Revision ID: 20250115_add_telehealth_chatbot
Revises: 20250114_add_clinical_screening
Create Date: 2025-01-15

This migration creates tables for advanced clinical features:
- telehealth_sessions: Secure video consultations with clinicians
- chatbot_conversations: AI mental health support with crisis detection
- mobile_devices: Mobile app push notification management

IMPORTANT HIPAA CONSIDERATIONS:
- All video recordings must be encrypted at rest
- Chatbot conversations may contain PHI - proper logging required
- Mobile device tokens must be securely stored
- BAA required with Twilio for video services
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20250115_add_telehealth_chatbot'
down_revision = '20250114_add_clinical_screening'
branch_labels = None
depends_on = None


def upgrade():
    # ==========================================================================
    # TELEHEALTH SESSIONS TABLE
    # ==========================================================================
    op.create_table(
        'telehealth_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clinician_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),

        # Session details
        sa.Column('session_type', sa.String(50), nullable=False, comment='initial, follow_up, crisis, group'),
        sa.Column('scheduled_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer, default=60),

        # Twilio Video integration
        sa.Column('room_sid', sa.String(100), unique=True, comment='Twilio room identifier'),
        sa.Column('room_name', sa.String(255), comment='Unique room name for session'),
        sa.Column('user_token', sa.Text, comment='JWT token for patient access'),
        sa.Column('clinician_token', sa.Text, comment='JWT token for clinician access'),
        sa.Column('token_expires_at', sa.TIMESTAMP(timezone=True)),

        # Session status
        sa.Column('status', sa.String(50), server_default='scheduled', comment='scheduled, in_progress, completed, cancelled, no_show'),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('ended_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('actual_duration_minutes', sa.Integer),

        # Recording (HIPAA: encrypted storage required)
        sa.Column('recording_enabled', sa.Boolean, server_default='false', comment='Requires explicit consent'),
        sa.Column('recording_url', sa.Text, comment='S3 path to encrypted recording'),
        sa.Column('recording_encrypted', sa.Boolean, server_default='true'),

        # Clinical notes
        sa.Column('session_notes', sa.Text, comment='Clinician session notes (PHI)'),
        sa.Column('diagnosis_codes', postgresql.ARRAY(sa.String(10)), comment='ICD-10 codes'),
        sa.Column('treatment_plan', sa.Text),
        sa.Column('follow_up_recommendations', sa.Text),

        # Cancellation/rescheduling
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('cancellation_reason', sa.Text),
        sa.Column('cancelled_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('rescheduled_to', sa.TIMESTAMP(timezone=True)),

        # Patient feedback
        sa.Column('patient_satisfaction', sa.Integer, comment='1-5 rating'),
        sa.Column('patient_feedback', sa.Text),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),

        # Soft delete for clinical records
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True)),
    )

    # Indexes for telehealth_sessions
    op.create_index('idx_telehealth_user_status', 'telehealth_sessions', ['user_id', 'status'])
    op.create_index('idx_telehealth_clinician_schedule', 'telehealth_sessions', ['clinician_id', 'scheduled_time'])
    op.create_index('idx_telehealth_org', 'telehealth_sessions', ['org_id', 'created_at'])
    op.create_index('idx_telehealth_upcoming', 'telehealth_sessions', ['scheduled_time', 'status'])


    # ==========================================================================
    # CHATBOT CONVERSATIONS TABLE
    # ==========================================================================
    op.create_table(
        'chatbot_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),

        # Conversation tracking
        sa.Column('session_id', sa.String(100), nullable=False, comment='Unique conversation session'),
        sa.Column('conversation_number', sa.Integer, comment='Sequential conversation for user'),

        # Message details
        sa.Column('message_text', sa.Text, nullable=False, comment='User or AI message'),
        sa.Column('is_user_message', sa.Boolean, nullable=False, comment='True=user, False=AI'),
        sa.Column('message_sequence', sa.Integer, comment='Order in conversation'),

        # AI response metadata
        sa.Column('ai_model_used', sa.String(100), comment='gpt-4, gpt-3.5-turbo, etc.'),
        sa.Column('ai_response', sa.Text, comment='AI generated response'),
        sa.Column('confidence_score', sa.Numeric(5, 4), comment='AI confidence in response'),
        sa.Column('tokens_used', sa.Integer, comment='OpenAI tokens consumed'),

        # Crisis detection (CRITICAL)
        sa.Column('crisis_detected', sa.Boolean, server_default='false', nullable=False),
        sa.Column('crisis_level', sa.String(20), comment='low, moderate, high, emergency'),
        sa.Column('crisis_keywords', postgresql.ARRAY(sa.Text), comment='Triggering keywords'),
        sa.Column('escalated_to_human', sa.Boolean, server_default='false'),
        sa.Column('escalated_to_clinician_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('escalated_at', sa.TIMESTAMP(timezone=True)),

        # Context and metadata
        sa.Column('context_screening_type', sa.String(50), comment='Related clinical assessment'),
        sa.Column('context_score', sa.Integer, comment='Related assessment score'),
        sa.Column('suggested_resources', postgresql.JSONB, comment='Resources provided by AI'),
        sa.Column('user_sentiment', sa.String(20), comment='positive, neutral, negative, crisis'),

        # RAG (Retrieval Augmented Generation)
        sa.Column('rag_sources_used', postgresql.ARRAY(sa.String), comment='Knowledge base sources'),
        sa.Column('rag_relevance_scores', postgresql.JSONB),

        # Feedback for improvement
        sa.Column('helpful_rating', sa.Boolean, comment='User feedback on response'),
        sa.Column('flagged_for_review', sa.Boolean, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # Indexes for chatbot_conversations
    op.create_index('idx_chatbot_user_session', 'chatbot_conversations', ['user_id', 'session_id'])
    op.create_index('idx_chatbot_crisis', 'chatbot_conversations', ['crisis_detected', 'created_at'])
    op.create_index('idx_chatbot_escalated', 'chatbot_conversations', ['escalated_to_human', 'created_at'])
    op.create_index('idx_chatbot_timestamp', 'chatbot_conversations', ['created_at'])


    # ==========================================================================
    # MOBILE DEVICES TABLE (for future mobile apps)
    # ==========================================================================
    op.create_table(
        'mobile_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),

        # Device identification
        sa.Column('device_token', sa.String(500), nullable=False, comment='FCM or APNs token'),
        sa.Column('platform', sa.String(20), nullable=False, comment='ios, android'),
        sa.Column('device_name', sa.String(100)),
        sa.Column('device_model', sa.String(100)),
        sa.Column('os_version', sa.String(50)),

        # App information
        sa.Column('app_version', sa.String(20)),
        sa.Column('build_number', sa.String(20)),

        # Push notification settings
        sa.Column('push_enabled', sa.Boolean, server_default='true'),
        sa.Column('notification_preferences', postgresql.JSONB, comment='Custom notification settings'),

        # Location (optional, for crisis resources)
        sa.Column('location_enabled', sa.Boolean, server_default='false'),
        sa.Column('last_location', postgresql.JSONB, comment='Encrypted location data'),

        # Activity tracking
        sa.Column('last_active', sa.TIMESTAMP(timezone=True)),
        sa.Column('install_date', sa.TIMESTAMP(timezone=True)),
        sa.Column('last_opened_at', sa.TIMESTAMP(timezone=True)),

        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('uninstalled', sa.Boolean, server_default='false'),
        sa.Column('uninstalled_at', sa.TIMESTAMP(timezone=True)),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
    )

    # Indexes for mobile_devices
    op.create_index('idx_mobile_user_token', 'mobile_devices', ['user_id', 'device_token'])
    op.create_index('idx_mobile_active', 'mobile_devices', ['is_active', 'uninstalled'])
    op.create_index('idx_mobile_platform', 'mobile_devices', ['platform', 'created_at'])


    # ==========================================================================
    # ANALYTICS AGGREGATION TABLE (for population health insights)
    # ==========================================================================
    op.create_table(
        'clinical_analytics_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),

        # Snapshot metadata
        sa.Column('snapshot_date', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('snapshot_type', sa.String(50), nullable=False, comment='daily, weekly, monthly'),

        # Assessment completion metrics
        sa.Column('total_assessments_completed', sa.Integer),
        sa.Column('assessments_by_type', postgresql.JSONB, comment='PHQ9: 150, GAD7: 120, etc.'),

        # Risk distribution
        sa.Column('risk_level_distribution', postgresql.JSONB, comment='low: 70%, moderate: 20%, etc.'),

        # Crisis metrics
        sa.Column('crisis_alerts_triggered', sa.Integer),
        sa.Column('crisis_alerts_resolved', sa.Integer),
        sa.Column('average_response_time_minutes', sa.Numeric(10, 2)),

        # Telehealth metrics
        sa.Column('telehealth_sessions_completed', sa.Integer),
        sa.Column('average_session_duration_minutes', sa.Numeric(10, 2)),
        sa.Column('patient_satisfaction_score', sa.Numeric(3, 2)),

        # Chatbot metrics
        sa.Column('chatbot_conversations', sa.Integer),
        sa.Column('chatbot_crisis_escallations', sa.Integer),
        sa.Column('chatbot_satisfaction_rate', sa.Numeric(5, 2)),

        # Trend data
        sa.Column('trend_data', postgresql.JSONB, comment='Week-over-week changes'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # Indexes for analytics
    op.create_index('idx_analytics_org_date', 'clinical_analytics_snapshots', ['org_id', 'snapshot_date'])
    op.create_index('idx_analytics_type', 'clinical_analytics_snapshots', ['snapshot_type', 'snapshot_date'])


def downgrade():
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('clinical_analytics_snapshots')
    op.drop_table('mobile_devices')
    op.drop_table('chatbot_conversations')
    op.drop_table('telehealth_sessions')
