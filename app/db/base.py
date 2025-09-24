# app/db/base.py
from sqlalchemy.orm import DeclarativeBase

# from sqlalchemy.orm import declarative_base
# Base = declarative_base()


# Central declarative base class
class Base(DeclarativeBase):
    """Base for all ORM models. Alembic will import Base.metadata."""
    pass



# # Import all models so Alembic can detect them
# from app.db.models import (
#     user,
#     role,
#     organization,
#     org_member,
#     team,
#     team_member,
#     framework,
#     question,
#     question_option,
#     assessment,
#     response,
#     score,
#     invitation,
#     audit_log,
#     personality_profile,
#     behavioral_insight,
#     team_compatibility_matrix,
#     prediction,
#     user_story,
#     sprint,
# )  # noqa
