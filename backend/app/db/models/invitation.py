# backend/app/db/models/invitation.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from ..base import Base
class Invitation(Base):
    __tablename__ = "invitations"
    id = sa.Column(UUID(as_uuid=True), primary_key=True,
    server_default=sa.text("gen_random_uuid()"))
    org_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('organizations.id',
    ondelete='CASCADE'), nullable=False)
    email = sa.Column(CITEXT, nullable=False)
    token = sa.Column(sa.Text, nullable=False, unique=True)
    expires_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False)
    accepted_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)