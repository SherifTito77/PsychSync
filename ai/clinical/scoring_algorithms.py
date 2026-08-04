"""Canonical import surface for clinical scoring algorithms.

The implementation currently lives in `app.ai.clinical.scoring_algorithms`
as a compatibility bridge. This module keeps the public `ai.*` path stable.
"""

from app.ai.clinical.scoring_algorithms import *  # noqa: F401,F403

from .scoring.compatibility import score_gad7_legacy, score_phq9_legacy

# Redirected scorers for compatibility
# Re-bind monolith functions to new modular ones
score_phq9 = score_phq9_legacy
score_gad7 = score_gad7_legacy
