# app/db/models/prediction.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    prediction_type = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=True)
    results = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
