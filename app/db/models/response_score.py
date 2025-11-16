# app/db/models/response_score.py

from sqlalchemy import Column, Integer, Float, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func

from app.db.base import Base

class ResponseScore(Base):
    """
    Stores the calculated score for a user's response to an assessment.
    """
    __tablename__ = "response_scores"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to the response this score belongs to
    response_id = Column(Integer, ForeignKey("assessment_responses.id"), nullable=False, unique=True)
    
    # Scoring details
    total_score = Column(Float, nullable=False)
    max_possible_score = Column(Float, nullable=False)
    percentage_score = Column(Float, nullable=False)
    
    # Store detailed scores for different subscales (e.g., for personality tests)
    subscale_scores = Column(JSON, nullable=True)
    
    # A simple interpretation of the score
    interpretation = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


