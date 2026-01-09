# app/create_team_tables.py
"""
Create team tables
Run this once: python create_team_tables.py
"""

from sqlalchemy import create_engine

from app.core.config import settings
from app.core.database import Base


def create_tables():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✓ Team tables created successfully!")


if __name__ == "__main__":
    print("Creating team tables...")
    create_tables()
