# app/db/database.py - Database Configuration and Connection

# database.py - Database Configuration and Connection
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


load_dotenv()

DATABASE_URL = "postgresql+asyncpg://psychsync_user:password@localhost/psychsync_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Database URL from environment - using synchronous version
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://psychsync_user:password@localhost/psychsync_db"  # Removed +asyncpg for sync
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Create all database tables"""
    try:
        # Import all models here to ensure they're registered with Base
        from app.db.models.user import User
        from app.db.models.team import Team
        from app.db.models.assessment import Assessment
        from app.db.models.team_member import TeamMember
        from app.db.models.prediction import Prediction
        from app.db.models.organization import Organization  # Add if exists
        
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        # Don't raise the exception to prevent startup failure



# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import StaticPool
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # Database URL from environment
# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql+asyncpg://psychsync_user:password@localhost/psychsync_db"
# )

# # Create SQLAlchemy engine
# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,
#     pool_recycle=300,
#     echo=os.getenv("DB_ECHO", "false").lower() == "true"
# )

# # Create SessionLocal class
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Create Base class
# Base = declarative_base()

# # Dependency to get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Initialize database
# def init_db():
#     """Create all database tables"""
#     Base.metadata.create_all(bind=engine)

