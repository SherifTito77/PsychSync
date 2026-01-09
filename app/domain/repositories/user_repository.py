# app/domain/repositories/user_repository.py

"""
DOMAIN USER REPOSITORY INTERFACE
Abstract repository interface for user domain

This interface defines the contract for user data access in the domain layer,
following the Dependency Inversion Principle and enabling clean architecture.

Author: Security Team
Version: 2.0 Enterprise Security
"""

from abc import ABC, abstractmethod
from typing import Any

from app.domain.entities.user import User


class UserRepository(ABC):
    """
    Abstract repository interface for User domain entity

    This interface defines the contract that all user repository implementations
    must follow, enabling dependency inversion and testability.
    """

    @abstractmethod
    async def save(self, user: User) -> User:
        """
        Save a user entity to the repository

        Args:
            user: The user entity to save

        Returns:
            The saved user entity with any updates (e.g., generated ID)
        """

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None:
        """
        Find a user by their ID

        Args:
            user_id: The unique identifier of the user

        Returns:
            The user entity if found, None otherwise
        """

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """
        Find a user by their email address

        Args:
            email: The email address to search for

        Returns:
            The user entity if found, None otherwise
        """

    @abstractmethod
    async def find_all(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[User]:
        """
        Find all users with optional pagination and filtering

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional filters to apply to the search

        Returns:
            List of user entities
        """

    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update an existing user entity

        Args:
            user: The user entity with updated information

        Returns:
            The updated user entity
        """

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user by their ID

        Args:
            user_id: The ID of the user to delete

        Returns:
            True if deletion was successful, False otherwise
        """

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count users with optional filtering

        Args:
            filters: Optional filters to apply to the count

        Returns:
            The total count of matching users
        """

    @abstractmethod
    async def email_exists(self, email: str, exclude_user_id: str | None = None) -> bool:
        """
        Check if an email address already exists in the repository

        Args:
            email: The email address to check
            exclude_user_id: Optional user ID to exclude from the check (for updates)

        Returns:
            True if email exists, False otherwise
        """

    @abstractmethod
    async def organization_exists(self, organization_id: str) -> bool:
        """
        Check if an organization exists

        Args:
            organization_id: The organization ID to check

        Returns:
            True if organization exists, False otherwise
        """

    @abstractmethod
    async def find_by_organization(
        self, organization_id: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """
        Find users by organization

        Args:
            organization_id: The organization ID to search for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of user entities belonging to the organization
        """

    @abstractmethod
    async def update_last_login(self, user_id: str, ip_address: str, user_agent: str):
        """
        Update user's last login information

        Args:
            user_id: The user ID to update
            ip_address: The IP address of the login
            user_agent: The user agent string of the login
        """

    @abstractmethod
    async def increment_failed_login(self, user_id: str) -> int:
        """
        Increment failed login attempts for a user

        Args:
            user_id: The user ID to update

        Returns:
            The new count of failed login attempts
        """

    @abstractmethod
    async def find_active_users_by_role(
        self, role: str, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """
        Find active users by role

        Args:
            role: The role to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of active users with the specified role
        """

    @abstractmethod
    async def search_users(self, search_term: str, limit: int = 20) -> list[User]:
        """
        Search users by email or full name

        Args:
            search_term: The term to search for
            limit: Maximum number of results to return

        Returns:
            List of matching user entities
        """
