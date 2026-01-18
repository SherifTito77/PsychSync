"""
Repository Interfaces - Dependency Inversion Principle (DIP) Fix

Dependency Inversion Principle (DIP): Depend on abstractions, not concretions.

This module provides repository interfaces so that high-level modules (services, API)
can depend on abstractions instead of concrete database implementations.

Architecture:
    - IUserRepository: User data access abstraction
    - IAssessmentRepository: Assessment data access abstraction
    - ITeamRepository: Team data access abstraction
    - IOrganizationRepository: Organization data access abstraction

Benefits:
    - Services don't depend on SQLAlchemy concrete types
    - Can swap implementations (SQLAlchemy → MongoDB → Redis) without changing services
    - Easy to mock for testing
    - Follows DIP (high-level modules don't depend on low-level modules)

Usage:
    # High-level service depends on abstraction
    class UserService:
        def __init__(self, user_repo: IUserRepository):
            self.user_repo = user_repo  # Abstract, not concrete

    # Low-level module implements interface
    class SQLAlchemyUserRepository(IUserRepository):
        async def get_by_id(self, user_id: UUID) -> User:
            # SQLAlchemy implementation

Author: Development Team
Version: 1.0 (SOLID DIP Fix)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Common Repository Interface
# =============================================================================


class RepositoryInterface(ABC):
    """
    Base repository interface with common operations.

    All repository interfaces inherit from this to ensure consistency.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID | str) -> Optional[Any]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> List[Any]:
        """List entities with optional filters."""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count entities."""
        pass


# =============================================================================
# User Repository Interface
# =============================================================================


class IUserRepository(RepositoryInterface):
    """
    User repository interface.

    Abstracts user data access operations. Services depend on this
    interface instead of concrete SQLAlchemy implementations.

    Methods:
        - get_by_id: Get user by ID
        - get_by_email: Get user by email
        - get_by_username: Get user by username
        - list: List users with filters
        - create: Create new user
        - update: Update existing user
        - delete: Delete user
        - count: Count users
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional["User"]:
        """
        Get user by ID.

        Args:
            id: User UUID

        Returns:
            User object if found, None otherwise

        Contract:
            - Returns None if not found (never raises)
            - Includes related data if eager loading enabled
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional["User"]:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            User object if found, None otherwise

        Contract:
            - Performs case-insensitive search
            - Returns None if not found (never raises)
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional["User"]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User object if found, None otherwise

        Contract:
            - Returns None if not found (never raises)
        """
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: UUID | None = None,
        team_id: UUID | None = None,
        active: bool | None = None,
        **filters: Any,
    ) -> List["User"]:
        """
        List users with optional filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            organization_id: Filter by organization
            team_id: Filter by team
            active: Filter by active status
            **filters: Additional filters

        Returns:
            List of user objects

        Contract:
            - Returns empty list if no users found
            - Respects skip and limit parameters
            - Returns users in deterministic order
        """
        pass

    @abstractmethod
    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        **kwargs: Any,
    ) -> "User":
        """
        Create new user.

        Args:
            email: User email address (must be unique)
            password_hash: Hashed password
            full_name: User's full name
            **kwargs: Additional user attributes

        Returns:
            Created User object with generated ID

        Contract:
            - Raises ConflictError if email already exists
            - Raises ValidationError if data invalid
            - Returns User with all fields populated
            - Hashes password before storing
        """
        pass

    @abstractmethod
    async def update(
        self,
        id: UUID,
        email: str | None = None,
        password_hash: str | None = None,
        full_name: str | None = None,
        **kwargs: Any,
    ) -> Optional["User"]:
        """
        Update user.

        Args:
            id: User ID
            email: New email address (optional)
            password_hash: New password hash (optional)
            full_name: New full name (optional)
            **kwargs: Additional fields to update

        Returns:
            Updated User object if found, None otherwise

        Contract:
            - Returns None if user not found
            - Performs partial update (only provided fields)
            - Raises ConflictError if email already exists
            - Raises ValidationError if data invalid
        """
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """
        Delete user (soft delete).

        Args:
            id: User ID

        Returns:
            True if deleted, False if not found

        Contract:
            - Performs soft delete (sets is_active=False)
            - Returns False if user not found
            - Returns True if successfully deleted
        """
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """
        Count users with optional filters.

        Args:
            **filters: Filter parameters

        Returns:
            Number of users matching filters
        """
        pass


# =============================================================================
# Assessment Repository Interface
# =============================================================================


class IAssessmentRepository(RepositoryInterface):
    """
    Assessment repository interface.

    Abstracts assessment data access operations.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional["Assessment"]:
        """Get assessment by ID."""
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional["Assessment"]:
        """Get assessment by code."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        team_id: UUID | None = None,
        framework_code: str | None = None,
        status: str | None = None,
        **filters: Any,
    ) -> List["Assessment"]:
        """List assessments with filters."""
        pass

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        framework_code: str,
        organization_id: UUID | None = None,
        team_id: UUID | None = None,
        **kwargs: Any,
    ) -> "Assessment":
        """Create new assessment."""
        pass

    @abstractmethod
    async def update(
        self,
        id: UUID,
        status: str | None = None,
        completed_at: datetime | None = None,
        **kwargs: Any,
    ) -> Optional["Assessment"]:
        """Update assessment."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete assessment."""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count assessments."""
        pass


# =============================================================================
# Team Repository Interface
# =============================================================================


class ITeamRepository(RepositoryInterface):
    """
    Team repository interface.

    Abstracts team data access operations.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional["Team"]:
        """Get team by ID."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: UUID | None = None,
        **filters: Any,
    ) -> List["Team"]:
        """List teams."""
        pass

    @abstractmethod
    async def create(
        self,
        name: str,
        organization_id: UUID,
        **kwargs: Any,
    ) -> "Team":
        """Create new team."""
        pass

    @abstractmethod
    async def update(
        self,
        id: UUID,
        name: str | None = None,
        **kwargs: Any,
    ) -> Optional["Team"]:
        """Update team."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete team."""
        pass

    @abstractmethod
    async def add_member(
        self,
        team_id: UUID,
        user_id: UUID,
        role: str = "member",
    ) -> bool:
        """Add user to team."""
        pass

    @abstractmethod
    async def remove_member(
        self,
        team_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Remove user from team."""
        pass

    @abstractmethod
    async def get_members(
        self,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List["User"]:
        """Get team members."""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count teams."""
        pass


# =============================================================================
# Organization Repository Interface
# =============================================================================


class IOrganizationRepository(RepositoryInterface):
    """
    Organization repository interface.

    Abstracts organization data access operations.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional["Organization"]:
        """Get organization by ID."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> List["Organization"]:
        """List organizations."""
        pass

    @abstractmethod
    async def create(
        self,
        name: str,
        **kwargs: Any,
    ) -> "Organization":
        """Create new organization."""
        pass

    @abstractmethod
    async def update(
        self,
        id: UUID,
        name: str | None = None,
        **kwargs: Any,
    ) -> Optional["Organization"]:
        """Update organization."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete organization."""
        pass

    @abstractmethod
    async def get_teams(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List["Team"]:
        """Get organization's teams."""
        pass

    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Count organizations."""
        pass


# =============================================================================
# Response Repository Interface
# =============================================================================


class IResponseRepository(RepositoryInterface):
    """
    Response repository interface.

    Abstracts assessment response data access operations.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional["Response"]:
        """Get response by ID."""
        pass

    @abstractmethod
    async def get_by_assessment(
        self,
        assessment_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List["Response"]:
        """Get responses for an assessment."""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        assessment_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List["Response"]:
        """Get responses from a user."""
        pass

    @abstractmethod
    async def create(
        self,
        assessment_id: UUID,
        user_id: UUID,
        question_id: str,
        response_data: Any,
        **kwargs: Any,
    ) -> "Response":
        """Create new response."""
        pass

    @abstractmethod
    async def bulk_create(
        self,
        responses: List[Dict[str, Any]],
    ) -> List["Response"]:
        """Create multiple responses at once."""
        pass

    @abstractmethod
    async def delete_by_assessment(self, assessment_id: UUID) -> int:
        """Delete all responses for an assessment."""
        pass


# =============================================================================
# Factory Function for Dependency Injection
# =============================================================================


def get_user_repository() -> IUserRepository:
    """
    Get user repository instance (for dependency injection).

    This is a factory function that returns the appropriate repository implementation.
    In production, this would be configured at application startup.

    Example:
        # In production
        from app.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
        return SQLAlchemyUserRepository(db)

        # In tests
        from tests.mocks import MockUserRepository
        return MockUserRepository()
    """
    # Import concrete implementation
    from app.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
    # This would typically be injected via DI container
    raise NotImplementedError("Implement DI container for repository creation")


def get_assessment_repository() -> IAssessmentRepository:
    """Get assessment repository instance."""
    raise NotImplementedError("Implement DI container for repository creation")


def get_team_repository() -> ITeamRepository:
    """Get team repository instance."""
    raise NotImplementedError("Implement DI container for repository creation")


def get_organization_repository() -> IOrganizationRepository:
    """Get organization repository instance."""
    raise NotImplementedError("Implement DI container for repository creation")


def get_response_repository() -> IResponseRepository:
    """Get response repository instance."""
    raise NotImplementedError("Implement DI container for repository creation")
