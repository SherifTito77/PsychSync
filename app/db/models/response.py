import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

class Response(Base):
    __tablename__ = "responses"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    assessment_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey('assessments.id', ondelete='CASCADE'),
        nullable=False
    )
    question_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey('questions.id', ondelete='CASCADE'),
        nullable=False
    )
    answer_text = sa.Column(sa.String, nullable=True)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False)




# # app/db/models/response.py
# import sqlalchemy as sa
# from sqlalchemy.dialects.postgresql import UUID, JSONB
# from ..base import Base


# class Response(Base):
#    __tablename__ = "responses"


#    id = sa.Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
#    assessment_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False