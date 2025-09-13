
# backend/app/db/base.py
from sqlalchemy.orm import DeclarativeBase

# Central declarative base class
class Base(DeclarativeBase):
    """Base for all ORM models. Alembic will import Base.metadata."""
    pass


# Import all models so Alembic can see them
from app.db.models import organization, user, team, assessment




# # backend/app/db/base.py
# import sqlalchemy as sa
# # from sqlalchemy.orm import DeclarativeBase


# class Base(DeclarativeBase):
# """Central declarative base for all models. Alembic will import Base.metadata."""
# pass

# from sqlalchemy.orm import declarative_base

# Base = declarative_base()

# # Import models here so Alembic can see them
# from app.db.models import organization, user, team, assessment
