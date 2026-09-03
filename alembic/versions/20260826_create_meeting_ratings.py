"""Create meeting_ratings table

Revision ID: 20260826_meetings
Revises: 20260825_fb360
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260826_meetings"
down_revision = "20260825_fb360"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "meeting_ratings",
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
            index=True,
        ),
        sa.Column("team_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column(
            "rater_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("meeting_date", sa.Date, nullable=False, index=True),
        sa.Column("meeting_subject", sa.String(500), nullable=True),
        sa.Column("organizer_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("effectiveness_score", sa.Integer, nullable=False),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("comment", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_meeting_org_date", "meeting_ratings", ["organization_id", "meeting_date"]
    )
    op.create_index(
        "idx_meeting_organizer", "meeting_ratings", ["organizer_id", "meeting_date"]
    )
    op.create_index("idx_meeting_team", "meeting_ratings", ["team_id", "meeting_date"])


def downgrade():
    op.drop_table("meeting_ratings")
