# app/db/models/score.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base
class Score(Base):
    
    __tablename__ = "scores"
    id = sa.Column(UUID(as_uuid=True), primary_key=True,
    server_default=sa.text("gen_random_uuid()"))
    assessment_id = sa.Column(UUID(as_uuid=True),
    sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False)
    dimension = sa.Column(sa.Text, nullable=False)
    value = sa.Column(sa.Numeric, nullable=False)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True),
    server_default=sa.text("NOW()"), nullable=False)
    __table_args__ = (sa.UniqueConstraint('assessment_id', 'dimension',
    name='uq_score_assessment_dimension'),)
