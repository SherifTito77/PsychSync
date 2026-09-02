"""Add Kafka Dead Letter Queue table

Revision ID: 20260209_add_kafka_dlq
Revises:
Create Date: 2026-02-09

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260209_add_kafka_dlq"
down_revision = "1e98a671d787"
branch_labels = None
depends_on = None


def upgrade():
    # Create kafka_dead_letter_tasks table
    op.create_table(
        "kafka_dead_letter_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("original_topic", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(255), nullable=False),
        sa.Column("partition", sa.Integer(), nullable=False),
        sa.Column("offset", sa.Integer(), nullable=False),
        sa.Column("consumer_group", sa.String(255), nullable=False),
        sa.Column("event_data", sa.Text(), nullable=True),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("exception_message", sa.Text(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("event_metadata", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    # Create indexes for performance
    op.create_index(
        "ix_kafka_dead_letter_tasks_event_id",
        "kafka_dead_letter_tasks",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_original_topic",
        "kafka_dead_letter_tasks",
        ["original_topic"],
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_event_type",
        "kafka_dead_letter_tasks",
        ["event_type"],
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_consumer_group",
        "kafka_dead_letter_tasks",
        ["consumer_group"],
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_reason", "kafka_dead_letter_tasks", ["reason"]
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_status", "kafka_dead_letter_tasks", ["status"]
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_created_at",
        "kafka_dead_letter_tasks",
        ["created_at"],
    )
    op.create_index(
        "ix_kafka_dead_letter_tasks_next_retry_at",
        "kafka_dead_letter_tasks",
        ["next_retry_at"],
    )

    # Create composite indexes for common queries
    op.create_index(
        "ix_kafka_dlq_event_type_status",
        "kafka_dead_letter_tasks",
        ["event_type", "status"],
    )
    op.create_index(
        "ix_kafka_dlq_reason_status", "kafka_dead_letter_tasks", ["reason", "status"]
    )
    op.create_index(
        "ix_kafka_dlq_created_at_status",
        "kafka_dead_letter_tasks",
        ["created_at", "status"],
    )
    op.create_index(
        "ix_kafka_dlq_consumer_group_status",
        "kafka_dead_letter_tasks",
        ["consumer_group", "status"],
    )


def downgrade():
    # Drop indexes
    op.drop_index(
        "ix_kafka_dlq_consumer_group_status", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dlq_created_at_status", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index("ix_kafka_dlq_reason_status", table_name="kafka_dead_letter_tasks")
    op.drop_index(
        "ix_kafka_dlq_event_type_status", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_next_retry_at", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_created_at", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_status", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_reason", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_consumer_group",
        table_name="kafka_dead_letter_tasks",
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_event_type", table_name="kafka_dead_letter_tasks"
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_original_topic",
        table_name="kafka_dead_letter_tasks",
    )
    op.drop_index(
        "ix_kafka_dead_letter_tasks_event_id", table_name="kafka_dead_letter_tasks"
    )

    # Drop table
    op.drop_table("kafka_dead_letter_tasks")
