# app/migrate.py
from app.core.database import Base
from app.core.config import settings
from sqlalchemy import create_engine

def run_migrations():
    print("Running local migrations...")
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")

if __name__ == "__main__":
    run_migrations()

