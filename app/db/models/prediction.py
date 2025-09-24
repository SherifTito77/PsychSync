# app/db/models/prediction.py
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    prediction_type = Column(String(100), nullable=False)  # performance, conflict, velocity
    prediction_data = Column(JSON, nullable=False)         # Detailed prediction results
    confidence_score = Column(Float, nullable=False)
    generated_by = Column(String(100), nullable=False)     # AI model version
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Optional: Validation/feedback fields
    actual_outcome = Column(JSON, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    feedback_provided = Column(Boolean, default=False)

    # Relationships
    team = relationship("Team", back_populates="predictions")

