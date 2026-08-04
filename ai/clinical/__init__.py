"""Canonical clinical AI package.

This package exposes deterministic clinical scoring and related helpers
through the top-level `ai` namespace.
"""

from . import scoring_algorithms

__all__ = ["scoring_algorithms"]
