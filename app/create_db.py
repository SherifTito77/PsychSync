# create_db.py
from app.db.session import engine
from app.db.base import Base

# Import all models so they are registered with Base.metadata
from app.db.models import user  # noqa

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("✅ Database tables created successfully.")
