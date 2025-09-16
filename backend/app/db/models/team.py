import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class Team(Base):
    __tablename__ = "teams"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()")
    )
    org_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("organizations.id"),
        nullable=False
    )
    name = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("NOW()"),
        nullable=False
    )



# # backend/app/db/models/team.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID
# from ..base import Base


# class Team(Base):
# __tablename__ = "teams"


# id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
# org_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
# name = sa.Column(sa.Text, nullable=False)
# description = sa.Column(sa.Text, nullable=True)
# created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
# deleted_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)
# __table_args__ = (sa.UniqueConstraint('org_id', 'name', name='uq_team_org_name'),)