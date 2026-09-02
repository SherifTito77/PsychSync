"""Create peer_recognitions table

Revision ID: 20260830_peerrec
Revises: 20260830_okr
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260830_peerrec"
down_revision = "20260830_okr"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "peer_recognitions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column(
            "team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True
        ),
        sa.Column(
            "recognizer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "recipient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "recognition_type",
            sa.String(30),
            nullable=False,
            server_default="thank_you",
        ),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_peer_rec_org", "peer_recognitions", ["organization_id"])
    op.create_index("ix_peer_rec_recipient", "peer_recognitions", ["recipient_id"])
    op.create_index("ix_peer_rec_team", "peer_recognitions", ["team_id"])
    op.create_index(
        "ix_peer_rec_created", "peer_recognitions", ["organization_id", "created_at"]
    )


def downgrade():
    op.drop_table("peer_recognitions")
