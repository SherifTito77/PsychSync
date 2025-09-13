# backend/app/db/models/role.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class Role(Base):
__tablename__ = "roles"


id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
scope = sa.Column(sa.Text, nullable=False)
code = sa.Column(sa.Text, nullable=False)
__table_args__ = (sa.UniqueConstraint('scope', 'code', name='uq_roles_scope_code'),)