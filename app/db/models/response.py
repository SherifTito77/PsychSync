import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Response(Base):
    __tablename__ = "responses"

    id = sa.Column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    assessment_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("assessment_questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Response data
    answer_text = sa.Column(sa.Text, nullable=True)
    answer_value = sa.Column(sa.Integer, nullable=True)  # For numeric answers (1-5 scales)
    answer_data = sa.Column(JSONB, nullable=True)  # For complex answers like multiple choice

    # Scoring and analytics
    score = sa.Column(sa.Float, nullable=True)
    normalized_score = sa.Column(sa.Float, nullable=True)  # 0-1 scale

    # Response metadata
    response_time_ms = sa.Column(sa.Integer, nullable=True)  # Time taken to answer
    confidence_rating = sa.Column(sa.Integer, nullable=True)  # User's confidence (1-5)

    # Timestamps
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )
    updated_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )

    # Relationships
    assessment = relationship("Assessment")
# user = relationship("User", back_populates="responses")  # TEMPORARILY DISABLED
# question = relationship("AssessmentQuestion", back_populates="responses")  # TEMPORARILY DISABLED

    # Performance optimization indexes
    __table_args__ = (
        # Composite index for user's responses ordered by date (most common query)
        # Optimizes: SELECT * FROM responses WHERE user_id = ? ORDER BY created_at DESC
        Index('idx_response_user_created', 'user_id', sa.text('created_at DESC')),

        # Composite index for assessment responses by user
        # Optimizes: SELECT * FROM responses WHERE assessment_id = ? AND user_id = ?
        Index('idx_response_assessment_user', 'assessment_id', 'user_id'),

        # Composite index for user's responses in assessment
        # Optimizes: SELECT * FROM responses WHERE user_id = ? AND assessment_id = ? ORDER BY created_at DESC
        Index('idx_response_user_assessment_created', 'user_id', 'assessment_id', sa.text('created_at DESC')),

        # GIN index for JSONB queries on answer_data
        # Optimizes: WHERE answer_data->>'question_type' = 'multiple_choice'
        Index('idx_response_answer_data_gin', 'answer_data', postgresql_using='gin'),
    )

    def __repr__(self):
        return (
            f"<Response(id={self.id}, assessment_id={self.assessment_id}, user_id={self.user_id})>"
        )


# Alias for backward compatibility and clearer naming
AssessmentResponse = Response
