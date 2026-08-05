# Re-export from canonical source to eliminate duplication.
# app/services/personality/predictive_index.py is the single source of truth.
from app.services.personality.predictive_index import (
    PredictiveIndexProcessor,
)  # noqa: F401
