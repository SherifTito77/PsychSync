import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    user_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False
    )
    score = sa.Column(sa.UUID(as_uuid=True), nullable=False)
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False
    )





# # backend/app/db/models/assessment.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class Assessment(Base):
# __tablename__ = "assessments"


# id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# org_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
# team_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
# user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
# framework_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('frameworks.id', ondelete='RESTRICT'), nullable=False)
# status = sa.Column(sa.Text, nullable=False)
# started_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)
# completed_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)
# created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)