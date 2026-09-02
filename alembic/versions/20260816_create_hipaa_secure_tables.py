"""Create HIPAA-compliant secure tables

Standalone migration for encrypted PHI storage tables.
Creates: users_secure, organizations_secure, teams_secure,
         team_members_secure, assessments_secure, responses_secure

Uses SQLAlchemy metadata.create_all() for dialect-agnostic table creation
(works on both PostgreSQL and SQLite).

Revision ID: 20260816_hipaa_secure
Revises: None (standalone - branched migration history)
Create Date: 2026-08-16
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260816_hipaa_secure"
down_revision: Union[str, None] = "20260209_add_kafka_dlq"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SECURE_TABLES = [
    "users_secure",
    "organizations_secure",
    "teams_secure",
    "team_members_secure",
    "assessments_secure",
    "responses_secure",
]


def upgrade() -> None:
    # Import models to register them in Base.metadata
    from app.db.models import (  # noqa: F401
        SecureAssessment,
        SecureOrganization,
        SecureResponse,
        SecureTeam,
        SecureTeamMember,
        SecureUser,
    )
    from app.core.database import Base

    bind = op.get_bind()
    tables = [
        Base.metadata.tables[t] for t in SECURE_TABLES if t in Base.metadata.tables
    ]
    Base.metadata.create_all(bind, tables=tables, checkfirst=True)


def downgrade() -> None:
    for table_name in reversed(SECURE_TABLES):
        op.drop_table(table_name)
