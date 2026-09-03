"""Create 360-degree feedback tables

Revision ID: 20260825_fb360
Revises: 20260825_actions
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "20260825_fb360"
down_revision = "20260825_actions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feedback_rounds",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="draft", index=True
        ),
        sa.Column("competency_set", JSON, nullable=True),
        sa.Column("opens_at", sa.Date, nullable=True),
        sa.Column("closes_at", sa.Date, nullable=True),
        sa.Column(
            "min_raters_per_category", sa.Integer, nullable=False, server_default="3"
        ),
        sa.Column(
            "created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "feedback_requests",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "round_id",
            UUID(as_uuid=True),
            sa.ForeignKey("feedback_rounds.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "subject_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "rater_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("rater_category", sa.String(20), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("reminded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_fb_req_round_subject", "feedback_requests", ["round_id", "subject_id"]
    )
    op.create_index("idx_fb_req_rater", "feedback_requests", ["rater_id", "status"])

    op.create_table(
        "feedback_responses_360",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("feedback_requests.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "round_id",
            UUID(as_uuid=True),
            sa.ForeignKey("feedback_rounds.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "subject_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "rater_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("rater_category", sa.String(20), nullable=False, index=True),
        sa.Column("competency_scores", JSON, nullable=False),
        sa.Column("open_ended", sa.Text, nullable=True),
        sa.Column(
            "submitted_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_fb_resp_round_subject",
        "feedback_responses_360",
        ["round_id", "subject_id"],
    )

    op.create_table(
        "feedback_competencies",
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
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("is_default", sa.String(5), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("feedback_competencies")
    op.drop_table("feedback_responses_360")
    op.drop_table("feedback_requests")
    op.drop_table("feedback_rounds")
