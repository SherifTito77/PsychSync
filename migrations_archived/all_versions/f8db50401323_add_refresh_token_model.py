"""add refresh token model

Revision ID: f8db50401323
Revises: 016_add_jsonb_gin_indexes
Create Date: 2026-01-07 20:51:20.513823

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f8db50401323"
down_revision: Union[str, None] = "016_add_jsonb_gin_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            sa.String(length=36),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("device_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column(
            "last_used_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("replaced_by", sa.String(length=36), nullable=True),
    )

    # Create indexes
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index(
        "ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True
    )
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])

    # Create composite index for user lookups with active tokens
    op.create_index(
        "refresh_tokens_user_expires_idx", "refresh_tokens", ["user_id", "expires_at"]
    )

    # Create composite index for token hash lookup (optimized for active tokens)
    op.create_index(
        "refresh_tokens_hash_active_idx", "refresh_tokens", ["token_hash", "revoked"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("refresh_tokens_hash_active_idx", table_name="refresh_tokens")
    op.drop_index("refresh_tokens_user_expires_idx", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")

    # Drop table
    op.drop_table("refresh_tokens")
