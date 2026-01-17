"""add_notification_system

Revision ID: c2049af57c94
Revises: 20250115_add_telehealth_chatbot
Create Date: 2026-01-15 20:12:11.898810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2049af57c94'
down_revision: Union[str, None] = '20250115_add_telehealth_chatbot'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('sms_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_on_crisis_alert', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_on_high_risk', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_on_moderate_risk', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notify_on_pending_review', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_on_weekly_summary', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('min_severity_for_notification', sa.String(), nullable=True, server_default='moderate'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('quiet_hours_start', sa.TIME(), nullable=True, server_default='22:00'),
        sa.Column('quiet_hours_end', sa.TIME(), nullable=True, server_default='08:00'),
        sa.Column('timezone', sa.String(), nullable=True, server_default='America/New_York'),
        sa.Column('bypass_quiet_hours_for_critical', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_notification_prefs_user')
    )
    op.create_index('idx_notification_prefs_user', 'notification_preferences', ['user_id'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('recipient_id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('notification_type', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(), nullable=True, server_default='normal'),
        sa.Column('channel', sa.String(), nullable=True, server_default='email'),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('delivery_status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('delivery_attempts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('delivered_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('read_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('action_taken', sa.String(), nullable=True),
        sa.Column('action_taken_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['clinical_screenings.id'], ondelete='CASCADE')
    )
    op.create_index('idx_notifications_recipient', 'notifications', ['recipient_id', 'created_at'])
    op.create_index('idx_notifications_unread', 'notifications', ['recipient_id', 'read'])
    op.create_index('idx_notifications_status', 'notifications', ['delivery_status', 'created_at'])

    # Create notification_queue table
    op.create_table(
        'notification_queue',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('notification_id', sa.UUID(), nullable=True),
        sa.Column('recipient_id', sa.UUID(), nullable=False),
        sa.Column('scheduled_for', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('retry_after', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('processing_started', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('processing_completed', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_notification_queue_scheduled', 'notification_queue', ['scheduled_for', 'status'])
    op.create_index('idx_notification_queue_recipient', 'notification_queue', ['recipient_id', 'status'])


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_index('idx_notification_queue_recipient', table_name='notification_queue')
    op.drop_index('idx_notification_queue_scheduled', table_name='notification_queue')
    op.drop_table('notification_queue')

    op.drop_index('idx_notifications_status', table_name='notifications')
    op.drop_index('idx_notifications_unread', table_name='notifications')
    op.drop_index('idx_notifications_recipient', table_name='notifications')
    op.drop_table('notifications')

    op.drop_index('idx_notification_prefs_user', table_name='notification_preferences')
    op.drop_table('notification_preferences')
