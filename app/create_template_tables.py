# app/create_template_tables.py
"""
Create template tables
Run this once: python create_template_tables.py
"""
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.db.models.template import AssessmentTemplate
from app.db.models.user import User

def create_tables():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✓ Template tables created successfully!")

if __name__ == "__main__":
    print("Creating template tables...")
    create_tables()
    
    