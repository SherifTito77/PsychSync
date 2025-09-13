# backend/app/db/models/question.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class Question(Base):
__tablename__ = "questions"


id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
framework_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('frameworks.id', ondelete='CASCADE'), nullable=False)
code = sa.Column(sa.Text, nullable=True)
body = sa.Column(sa.Text, nullable=False)
kind = sa.Column(sa.Text, nullable=False)
position = sa.Column(sa.Integer, nullable=False, server_default=sa.text('0'))
created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)