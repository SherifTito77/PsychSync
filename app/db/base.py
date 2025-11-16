# app/db/base.py
"""
DEPRECATED - Use app.core.database.Base instead
This file kept for backward compatibility during migration
"""

# Import the authoritative Base from core.database
from app.core.database import Base

# Legacy alias for backward compatibility
DeclarativeBase = type(Base)



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
