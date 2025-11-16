# app/create_assessment_tables.py
"""
Create assessment tables
Run this once: python create_assessment_tables.py
"""
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.assessment import (
    Assessment,
    AssessmentSection,
    Question,
    AssessmentAssignment,
    AssessmentResponse
)

def create_tables():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✓ Assessment tables created successfully!")

if __name__ == "__main__":
    print("Creating assessment tables...")
    create_tables()
    
    