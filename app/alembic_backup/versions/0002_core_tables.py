"""create core domain tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-09-10 16:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    # ... continue with responses, scores, invitations, audit_logs
    # all tables should use op.create_table + sa.Column + sa.ForeignKey



def upgrade() -> None:
    # question_options
    op.execute("""
    CREATE TABLE question_options (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        label TEXT NOT NULL,
        value TEXT NOT NULL,
        weight NUMERIC,
        position INT NOT NULL
    );
    CREATE INDEX question_options_q_pos_idx ON question_options (question_id, position);
    """)

    # assessments
    op.execute("""
    CREATE TABLE assessments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        framework_id UUID NOT NULL REFERENCES frameworks(id) ON DELETE RESTRICT,
        status TEXT NOT NULL CHECK (status IN ('assigned','in_progress','completed','expired')),
        started_at timestamptz,
        completed_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT NOW()
    );
    CREATE INDEX assessments_lookup_idx ON assessments (org_id, team_id, user_id, framework_id);
    """)

    # responses
    op.execute("""
    CREATE TABLE responses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
        question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        answer_json JSONB NOT NULL,
        created_at timestamptz NOT NULL DEFAULT NOW(),
        UNIQUE (assessment_id, question_id)
    );
    CREATE INDEX responses_assessment_idx ON responses (assessment_id);
    """)

    # scores
    op.execute("""
    CREATE TABLE scores (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
        dimension TEXT NOT NULL,
        value NUMERIC NOT NULL,
        created_at timestamptz NOT NULL DEFAULT NOW(),
        UNIQUE (assessment_id, dimension)
    );
    CREATE INDEX scores_assessment_dim_idx ON scores (assessment_id, dimension);
    """)

    # invitations
    op.execute("""
    CREATE TABLE invitations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        email CITEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        expires_at timestamptz NOT NULL,
        accepted_at timestamptz
    );
    CREATE INDEX invitations_org_email_idx ON invitations (org_id, email);
    """)

    # audit_logs
    op.execute("""
    CREATE TABLE audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        action TEXT NOT NULL,
        entity TEXT NOT NULL,
        entity_id UUID,
        meta JSONB,
        created_at timestamptz NOT NULL DEFAULT NOW()
    );
    CREATE INDEX audit_logs_org_time_idx ON audit_logs (org_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS invitations CASCADE;")
    op.execute("DROP TABLE IF EXISTS scores CASCADE;")
    op.execute("DROP TABLE IF EXISTS responses CASCADE;")
    op.execute("DROP TABLE IF EXISTS assessments CASCADE;")
    op.execute("DROP TABLE IF EXISTS question_options CASCADE;")
