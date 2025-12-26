"""
Base file for AI processors
Backward compatibility import from processors_base
"""

from .processors_base import *

# Re-export everything from processors_base for backward compatibility
__all__ = [
    'PersonalityFrameworkProcessor',
    'PsychSyncProcessorError'
]