# Re-export from canonical source to eliminate duplication.
# app/services/personality/strengths.py is the single source of truth.
from app.services.personality.strengths import StrengthsProcessor  # noqa: F401
