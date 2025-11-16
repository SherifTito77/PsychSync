# app/db/models/audit_log.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base
class AuditLog(Base):
   __tablename__ = "audit_logs"
   id = sa.Column(UUID(as_uuid=True), primary_key=True,
   server_default=sa.text("gen_random_uuid()"))
   organization_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('organizations.id',
   ondelete='CASCADE'), nullable=False)
   actor_user_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id',
   ondelete='SET NULL'), nullable=True)
   action = sa.Column(sa.Text, nullable=False)
   entity = sa.Column(sa.Text, nullable=False)
   entity_id = sa.Column(UUID(as_uuid=True), nullable=True)
   meta = sa.Column(JSONB, nullable=True)
   created_at = sa.Column(sa.TIMESTAMP(timezone=True),
   server_default=sa.text("NOW()"), nullable=False)
   