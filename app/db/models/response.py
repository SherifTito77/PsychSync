import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
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

    def __repr__(self):
        return (
            f"<Response(id={self.id}, assessment_id={self.assessment_id}, user_id={self.user_id})>"
        )


# Alias for backward compatibility and clearer naming
AssessmentResponse = Response
