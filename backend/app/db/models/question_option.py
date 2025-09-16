# backend/app/db/models/question_option.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class QuestionOption(Base):
   __tablename__ = "question_options"


   id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
   question_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
   label = sa.Column(sa.Text, nullable=False)
   value = sa.Column(sa.Text, nullable=False)
   weight = sa.Column(sa.Numeric, nullable=True)
   position = sa.Column(sa.Integer, nullable=False, server_default=sa.text('0'))