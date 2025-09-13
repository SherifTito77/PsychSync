# backend/app/db/models/response.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..base import Base


class Response(Base):
__tablename__ = "responses"


id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
assessment_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=Fa