# app/create_scoring_tables.py
"""
Create scoring tables
Run: python create_scoring_tables.py
"""
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.db.models.scoring import AssessmentScoringConfig, ScoringDimension

def create_tables():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✓ Scoring tables created successfully!")

if __name__ == "__main__":
    print("Creating scoring tables...")
    create_tables()
    