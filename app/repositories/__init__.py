# app/repositories/__init__.py

"""
ENTERPRISE-GRADE REPOSITORY PACKAGE
Data access layer following repository pattern with comprehensive security

REPOSITORY PATTERN BENEFITS:
- Abstraction over database operations
- Consistent data access patterns
- Built-in security and validation
- Performance monitoring
- Error handling standardization
- Audit logging integration
- Soft delete support
- Relationship management

PACKAGE STRUCTURE:
- base_repository.py: Abstract base repository with common operations
- user_repository.py: User-specific data access operations
- assessment_repository.py: Assessment-specific operations
- response_repository.py: Response data access
- team_repository.py: Team management operations

Author: Security Team
Version: 2.0 Enterprise Security
"""

from .base_repository import BaseRepository
from .user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository"
]

# Package information
__version__ = "2.0.0"
__author__ = "Security Team"
__description__ = "Enterprise-grade repository pattern implementation"