# app/init_db.py
# app/create_db.py
import os

from sqlalchemy import create_engine

from app.db.base import Base
from app.db.models import Base
from app.db.session import engine

# import all models so Base.metadata sees them


def init_db():
    Base.metadata.create_all(bind=engine)


# Path to your DATABASE_URL database
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "psychsync.db")
DB_URL = f"DATABASE_URL:///{DB_PATH}"

# Create engine
engine = create_engine(DB_URL, echo=True)

# Create all tables
Base.metadata.create_all(engine)

print(f"Database created at {DB_PATH}")
