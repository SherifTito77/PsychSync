# app/core/database_transactions.py
"""
Database Transaction Management System for PsychSync
Provides consistent transaction handling with proper error management
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handling import DatabaseOperationException
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def database_transaction(
    db: AsyncSession, isolation_level: str | None = None, timeout: float | None = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database transactions with comprehensive error handling

    Args:
        db: AsyncSession database session
        isolation_level: Transaction isolation level (READ COMMITTED, REPEATABLE READ, etc.)
        timeout: Transaction timeout in seconds

    Yields:
        AsyncSession: The database session with transaction management

    Raises:
        DatabaseOperationException: For database-related errors
    """
    transaction_start_time = logger._create_log_entry(
        logger.LogLevel.INFO, logger.EventType.DATABASE_OPERATION, "Transaction started"
    ).timestamp

    # Set isolation level if specified
    if isolation_level:
        await db.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))

    try:
        yield db

        # Commit transaction
        await db.commit()

        # Log successful commit
        logger.log_database_operation(
            operation="transaction_commit", table="multiple", success=True
        )

    except SQLAlchemyError as e:
        # Rollback on database errors
        try:
            await db.rollback()
            logger.log_database_operation(
                operation="transaction_rollback",
                table="multiple",
                success=False,
                error_details={"error": str(e)},
            )
        except Exception as rollback_error:
            logger.log_error(
                DatabaseOperationException(
                    "Failed to rollback transaction", "transaction_rollback", rollback_error
                ),
                operation="transaction_rollback",
            )

        raise DatabaseOperationException(f"Transaction failed: {e!s}", "database_transaction", e) from e

    except Exception as e:
        # Rollback on any other errors
        try:
            await db.rollback()
            logger.log_database_operation(
                operation="transaction_rollback",
                table="multiple",
                success=False,
                error_details={"error": str(e), "type": "non_database_error"},
            )
        except Exception as rollback_error:
            logger.log_error(
                DatabaseOperationException(
                    "Failed to rollback transaction", "transaction_rollback", rollback_error
                ),
                operation="transaction_rollback",
            )

        raise DatabaseOperationException(f"Transaction failed: {e!s}", "database_transaction", e) from e

    finally:
        # Clean up session state
        await db.expire_all()


class TransactionManager:
    """
    Advanced transaction manager with nested transaction support
    and performance monitoring
    """

    def __init__(self):
        self.active_transactions: dict[str, dict[str, Any]] = {}
        self.transaction_stats = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "rolled_back_transactions": 0,
        }

    @asynccontextmanager
    async def transaction(
        self, db: AsyncSession, name: str = None, savepoint: bool = False, readonly: bool = False
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Advanced transaction management with savepoints and performance tracking

        Args:
            db: AsyncSession database session
            name: Transaction name for logging
            savepoint: Create a savepoint (for nested transactions)
            readonly: Make transaction read-only

        Yields:
            AsyncSession: Database session with transaction management
        """
        import time
        import uuid

        transaction_id = str(uuid.uuid4())
        transaction_name = name or f"tx_{transaction_id[:8]}"
        start_time = time.time()

        # Track transaction
        self.active_transactions[transaction_id] = {
            "name": transaction_name,
            "start_time": start_time,
            "savepoint": savepoint,
            "readonly": readonly,
        }

        self.transaction_stats["total_transactions"] += 1

        logger.info(
            logger.EventType.DATABASE_OPERATION,
            f"Transaction '{transaction_name}' started",
            operation_name="transaction_start",
            transaction_id=transaction_id,
            transaction_name=transaction_name,
            savepoint=savepoint,
            readonly=readonly,
        )

        savepoint_obj = None
        if savepoint:
            savepoint_obj = await db.begin_nested()

        try:
            yield db

            if savepoint:
                await savepoint_obj.commit()
                logger.info(
                    logger.EventType.DATABASE_OPERATION,
                    f"Savepoint '{transaction_name}' committed",
                    operation_name="savepoint_commit",
                    transaction_id=transaction_id,
                )
            else:
                await db.commit()
                duration_ms = (time.time() - start_time) * 1000

                self.transaction_stats["successful_transactions"] += 1

                logger.log_database_operation(
                    operation="transaction_commit",
                    table="multiple",
                    duration_ms=duration_ms,
                    success=True,
                    transaction_id=transaction_id,
                    transaction_name=transaction_name,
                )

        except Exception as e:
            if savepoint:
                await savepoint_obj.rollback()
                logger.warning(
                    logger.EventType.DATABASE_OPERATION,
                    f"Savepoint '{transaction_name}' rolled back",
                    operation_name="savepoint_rollback",
                    transaction_id=transaction_id,
                    error_details={"error": str(e)},
                )
            else:
                await db.rollback()
                duration_ms = (time.time() - start_time) * 1000

                self.transaction_stats["failed_transactions"] += 1
                self.transaction_stats["rolled_back_transactions"] += 1

                logger.log_database_operation(
                    operation="transaction_rollback",
                    table="multiple",
                    duration_ms=duration_ms,
                    success=False,
                    transaction_id=transaction_id,
                    transaction_name=transaction_name,
                    error_details={"error": str(e)},
                )

            raise

        finally:
            # Clean up transaction tracking
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]

    async def execute_in_transaction(
        self, db: AsyncSession, operations: list[Callable], name: str = "batch_operations"
    ) -> list[Any]:
        """
        Execute multiple operations in a single transaction

        Args:
            db: AsyncSession database session
            operations: List of async functions to execute
            name: Transaction name for logging

        Returns:
            List of results from operations

        Raises:
            DatabaseOperationException: If any operation fails
        """
        results = []

        async with self.transaction(db, name=name):
            for i, operation in enumerate(operations):
                try:
                    result = await operation(db)
                    results.append(result)

                    logger.debug(
                        logger.EventType.DATABASE_OPERATION,
                        f"Operation {i + 1}/{len(operations)} completed in transaction '{name}'",
                        operation_name=f"{name}_operation_{i + 1}",
                        operation_index=i + 1,
                        total_operations=len(operations),
                    )

                except Exception as e:
                    logger.error(
                        logger.EventType.DATABASE_OPERATION,
                        f"Operation {i + 1}/{len(operations)} failed in transaction '{name}'",
                        operation_name=f"{name}_operation_{i + 1}",
                        operation_index=i + 1,
                        total_operations=len(operations),
                        error_details={"error": str(e)},
                    )
                    raise

        return results

    def get_transaction_stats(self) -> dict[str, Any]:
        """Get transaction performance statistics"""
        return {
            **self.transaction_stats,
            "success_rate": (
                self.transaction_stats["successful_transactions"]
                / max(self.transaction_stats["total_transactions"], 1)
                * 100
            ),
            "active_transactions": len(self.active_transactions),
        }

    def get_active_transactions(self) -> list[dict[str, Any]]:
        """Get list of currently active transactions"""
        import time

        current_time = time.time()

        active = []
        for tx_id, tx_info in self.active_transactions.items():
            active.append(
                {
                    "transaction_id": tx_id,
                    "name": tx_info["name"],
                    "duration_seconds": current_time - tx_info["start_time"],
                    "savepoint": tx_info["savepoint"],
                    "readonly": tx_info["readonly"],
                }
            )

        return active


# Global transaction manager instance
transaction_manager = TransactionManager()

# TODO(human): Implement distributed transaction coordinator
# This should handle transactions across multiple databases or services
# using two-phase commit patterns for data consistency


class DistributedTransactionCoordinator:
    """
    Coordinates transactions across multiple databases or services
    Uses two-phase commit protocol to ensure data consistency
    """

    def __init__(self):
        self.participants: list[str] = []
        self.transaction_id: str | None = None

    async def begin_transaction(self, participants: list[str]) -> str:
        """Begin a distributed transaction"""
        import uuid

        self.transaction_id = str(uuid.uuid4())
        self.participants = participants

        logger.info(
            logger.EventType.DATABASE_OPERATION,
            "Distributed transaction started",
            operation_name="distributed_transaction_begin",
            transaction_id=self.transaction_id,
            participants=participants,
        )

        # Phase 1: Prepare all participants
        for participant in participants:
            await self._prepare_participant(participant)

        return self.transaction_id

    async def _prepare_participant(self, participant: str):
        """Prepare a participant for two-phase commit"""
        # Implementation depends on your system architecture
        # This would:
        # 1. Connect to the participant service/database
        # 2. Start a transaction with prepare phase
        # 3. Ensure the participant is ready to commit
        # 4. Return confirmation or raise exception if not ready

        logger.debug(
            logger.EventType.DATABASE_OPERATION,
            f"Preparing participant: {participant}",
            operation_name="prepare_participant",
            transaction_id=self.transaction_id,
            participant=participant,
        )

    async def commit_transaction(self):
        """Commit the distributed transaction (Phase 2)"""
        if not self.transaction_id:
            raise DatabaseOperationException(
                "No active distributed transaction", "distributed_commit"
            )

        try:
            # Phase 2: Commit all participants
            for participant in self.participants:
                await self._commit_participant(participant)

            logger.info(
                logger.EventType.DATABASE_OPERATION,
                "Distributed transaction committed",
                operation_name="distributed_transaction_commit",
                transaction_id=self.transaction_id,
                participants=self.participants,
            )

        except Exception:
            # If any commit fails, attempt to rollback all
            await self._rollback_all_participants()
            raise

    async def rollback_transaction(self):
        """Rollback the distributed transaction"""
        if not self.transaction_id:
            return

        await self._rollback_all_participants()

    async def _commit_participant(self, participant: str):
        """Commit a specific participant"""
        # Implementation depends on your system architecture
        logger.debug(
            logger.EventType.DATABASE_OPERATION,
            f"Committing participant: {participant}",
            operation_name="commit_participant",
            transaction_id=self.transaction_id,
            participant=participant,
        )

    async def _rollback_all_participants(self):
        """Rollback all participants"""
        for participant in self.participants:
            try:
                await self._rollback_participant(participant)
            except Exception as e:
                logger.error(
                    logger.EventType.DATABASE_OPERATION,
                    f"Failed to rollback participant: {participant}",
                    operation_name="rollback_participant",
                    transaction_id=self.transaction_id,
                    participant=participant,
                    error_details={"error": str(e)},
                )

    async def _rollback_participant(self, participant: str):
        """Rollback a specific participant"""
        # Implementation depends on your system architecture
        logger.debug(
            logger.EventType.DATABASE_OPERATION,
            f"Rolling back participant: {participant}",
            operation_name="rollback_participant",
            transaction_id=self.transaction_id,
            participant=participant,
        )


# Global distributed transaction coordinator
distributed_coordinator = DistributedTransactionCoordinator()
