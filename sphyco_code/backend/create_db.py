
# backend/create_db.py
from psychsync_database_models import Base
from sqlalchemy import create_engine
import os

# Path to your SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "psychsync.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DB_URL, echo=True)

# Create all tables
Base.metadata.create_all(engine)

print(f"Database created at {DB_PATH}")
