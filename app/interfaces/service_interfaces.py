"""
Segregated Service Interfaces - Interface Segregation Principle (ISP) Fix

Interface Segregation Principle (ISP): Clients should not depend on interfaces they don't use.

This module provides fine-grained interfaces instead of monolithic BaseService.
Services can inherit only the interfaces they actually use.

Architecture:
    - IReadOnlyService: For read-only operations
    - IWriteOnlyService: For write operations
    - ICrudService: For full CRUD (combines read + write)
    - IBulkOperationService: For bulk operations
    - ICachedService: For services with caching
    - IValidatedService: For services with validation

Usage:
    # Read-only service (e.g., reporting)
    class ReportingService(IReadOnlyService[Report]):
        async def get_by_id(...): ...
        async def list(...): ...
        async def count(...): ...
        # No create/update/delete required!

    # Full CRUD service
    class UserService(ICrudService[User, UserCreate, UserUpdate]):
        async def get_by_id(...): ...
        async def list(...): ...
        async def create(...): ...
        async def update(...): ...
        async def delete(...): ...

Author: Development Team
Version: 1.0 (SOLID ISP Fix)
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Type Variables for Generic Types
# =============================================================================

T = TypeVar("T")  # Entity type
C = TypeVar("C")  # Create schema type
U = TypeVar("U")  # Update schema type


# =============================================================================
# Read-Only Interface
# =============================================================================


class IReadOnlyService(ABC, Generic[T]):
    """
    Read-only service interface.

    For services that only read data and never create, update, or delete.
    Examples: Reporting, analytics, dashboards, logs.

    Methods:
        - get_by_id: Get single entity by ID
        - list: Get list of entities with optional filters
        - count: Count entities with optional filters
    """

    @abstractmethod
    async def get_by_id(
        self,
        db: AsyncSession,
        id: str | UUID,
        **kwargs: Any,
    ) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            db: Database session
            id: Entity ID
            **kwargs: Additional filters

        Returns:
            Entity if found, None otherwise

        Contract:
            - Returns None if not found (never raises NotFoundError)
            - Uses read-only transaction
            - Does not modify database state
        """
        pass

    @abstractmethod
    async def list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> List[T]:
        """
        Get list of entities.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filters

        Returns:
            List of entities

        Contract:
            - Returns empty list if no entities found
            - Respects skip and limit parameters
            - Returns entities in deterministic order
        """
        pass

    @abstractmethod
    async def count(
        self,
        db: AsyncSession,
        **filters: Any,
    ) -> int:
        """
        Count entities.

        Args:
            db: Database session
            **filters: Additional filters

        Returns:
            Number of entities

        Contract:
            - Returns 0 if no entities found
            - Performs efficient COUNT query
        """
        pass


# =============================================================================
# Write-Only Interface
# =============================================================================


class IWriteOnlyService(ABC, Generic[T, C]):
    """
    Write-only service interface.

    For services that only create/write data and never read.
    Examples: Audit logging, event sourcing, append-only streams.

    Methods:
        - create: Create new entity
    """

    @abstractmethod
    async def create(
        self,
        db: AsyncSession,
        data: C,
        **kwargs: Any,
    ) -> T:
        """
        Create new entity.

        Args:
            db: Database session
            data: Create schema
            **kwargs: Additional parameters

        Returns:
            Created entity with generated ID

        Contract:
            - Returns created entity with all fields populated
            - Uses atomic transaction (all-or-nothing)
            - Raises ValidationError if data invalid
            - Raises ConflictError if constraint violated
            - Logs creation event
        """
        pass


# =============================================================================
# Full CRUD Interface
# =============================================================================


class ICrudService(IReadOnlyService[T], IWriteOnlyService[T, C]):
    """
    Full CRUD service interface (combines read + write + update + delete).

    For services that support full CRUD operations.
    Examples: User management, assessment management, team management.

    Methods (inherited):
        - get_by_id: Get entity by ID
        - list: List entities
        - count: Count entities
        - create: Create entity
    Additional methods:
        - update: Update existing entity
        - delete: Delete entity
    """

    @abstractmethod
    async def update(
        self,
        db: AsyncSession,
        id: str | UUID,
        data: U,
        **kwargs: Any,
    ) -> Optional[T]:
        """
        Update entity.

        Args:
            db: Database session
            id: Entity ID
            data: Update schema
            **kwargs: Additional parameters

        Returns:
            Updated entity if found, None otherwise

        Contract:
            - Returns None if entity not found (never raises NotFoundError)
            - Uses atomic transaction
            - Performs partial update (only provided fields)
            - Raises ValidationError if data invalid
            - Logs update event
        """
        pass

    @abstractmethod
    async def delete(
        self,
        db: AsyncSession,
        id: str | UUID,
        **kwargs: Any,
    ) -> bool:
        """
        Delete entity.

        Args:
            db: Database session
            id: Entity ID
            **kwargs: Additional parameters

        Returns:
            True if deleted, False if not found

        Contract:
            - Returns False if entity not found (never raises NotFoundError)
            - Uses atomic transaction
            - Performs soft delete if entity supports it
            - Logs deletion event
        """
        pass


# =============================================================================
# Bulk Operations Interface
# =============================================================================


class IBulkOperationService(ABC, Generic[T, C]):
    """
    Bulk operations service interface.

    For services that support bulk create/update/delete operations.
    Examples: Batch imports, bulk updates, batch processing.

    Methods:
        - bulk_create: Create multiple entities at once
    """

    @abstractmethod
    async def bulk_create(
        self,
        db: AsyncSession,
        items: List[C],
        **kwargs: Any,
    ) -> List[T]:
        """
        Create multiple entities at once.

        Args:
            db: Database session
            items: List of create schemas
            **kwargs: Additional parameters

        Returns:
            List of created entities

        Contract:
            - Uses efficient bulk insert (single query)
            - All-or-nothing transaction
            - Returns entities in same order as input
            - Raises ValidationError if any item invalid
            - Logs bulk creation event
        """
        pass


# =============================================================================
# Cached Service Interface
# =============================================================================


class ICachedService(ABC):
    """
    Cached service interface.

    For services that support caching to improve performance.
    Examples: Frequently accessed data, reference data, lookups.

    Methods:
        - get_cache_key: Generate cache key for operations
        - invalidate_cache: Invalidate cached entries
    """

    @abstractmethod
    def get_cache_key(
        self,
        operation: str,
        **kwargs: Any,
    ) -> str:
        """
        Generate cache key for caching operations.

        Args:
            operation: Operation type (e.g., "get_by_id", "list")
            **kwargs: Parameters to include in key

        Returns:
            Cache key string

        Contract:
            - Returns deterministic key for same inputs
            - Includes all relevant parameters in key
            - Uses consistent key format
        """
        pass

    @abstractmethod
    async def invalidate_cache(
        self,
        db: AsyncSession,
        id: str | UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Invalidate cached entries.

        Args:
            db: Database session
            id: Entity ID (if invalidating single entity)
            **kwargs: Additional cache key parameters

        Contract:
            - Invalidates entity cache if id provided
            - Invalidates list cache if id not provided
            - Logs cache invalidation event
        """
        pass


# =============================================================================
# Validated Service Interface
# =============================================================================


class IValidatedService(ABC, Generic[C, U]):
    """
    Validated service interface.

    For services that validate data before create/update operations.
    Examples: All services that work with user input.

    Methods:
        - validate_create_data: Validate data for creation
        - validate_update_data: Validate data for update
    """

    @abstractmethod
    def validate_create_data(
        self,
        data: C,
    ) -> None:
        """
        Validate data for entity creation.

        Args:
            data: Create schema to validate

        Raises:
            ValidationError: If data is invalid

        Contract:
            - Raises ValidationError with detailed error messages
            - Checks all business rules
            - Checks data types and formats
            - Checks constraint violations
        """
        pass

    @abstractmethod
    def validate_update_data(
        self,
        data: U,
        existing: T,
    ) -> None:
        """
        Validate data for entity update.

        Args:
            data: Update schema to validate
            existing: Existing entity (for comparison)

        Raises:
            ValidationError: If data is invalid

        Contract:
            - Raises ValidationError with detailed error messages
            - Checks all business rules
            - Allows partial updates
            - Validates against existing entity state
        """
        pass


# =============================================================================
# Complete Service Interface (Backward Compatible)
# =============================================================================


class ICompleteService(
    ICrudService[T, C, U],
    IBulkOperationService[T, C],
    ICachedService,
    IValidatedService[C, U],
):
    """
    Complete service interface combining all capabilities.

    This is provided for backward compatibility but is NOT recommended
    for new services as it violates ISP. Prefer using segregated interfaces.

    Usage:
        # DON'T DO THIS (violates ISP):
        class ReportingService(ICompleteService[Report, ...]):
            # Must implement 12+ methods even though only reads

        # DO THIS (follows ISP):
        class ReportingService(IReadOnlyService[Report]):
            # Only implements 3 methods it actually uses
    """

    pass


# =============================================================================
# Interface Type Definitions for IDE Support
# =============================================================================

# Type alias for read-only repository (commonly used)
ReadOnlyService = IReadOnlyService

# Type alias for CRUD repository (commonly used)
CrudService = ICrudService

# Type alias for complete service (backward compatible)
CompleteService = ICompleteService
