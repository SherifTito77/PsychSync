"""
Log Integrity Management

Provides tamper-evident logging through:
- Hash-chaining: Each log entry contains hash of previous entry
- Write-ahead logging: Logs written to immutable staging area first
- Merkle tree verification: Efficient integrity checking for large batches
- Cryptographic signing: Optional signing of log batches
"""

import hashlib
import logging

logger = logging.getLogger(__name__)
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from app.security.logging.schemas import SecurityEvent, SecurityLogBatch


@dataclass
class IntegrityCheckpoint:
    """Checkpoint for periodic integrity verification"""

    checkpoint_id: str
    timestamp: datetime
    log_count: int
    last_hash: str
    merkle_root: str | None = None
    signature: str | None = None


class LogIntegrityManager:
    """
    Manages log integrity through hash-chaining and write-ahead logging.

    Implements NIST SP 800-92 recommendations for log integrity.
    """

    def __init__(
        self,
        staging_dir: str = "/tmp/security_logs_staging",
        production_dir: str = "/var/log/security_logs",
        hash_algorithm: str = "sha256",
        checkpoint_interval: int = 1000,  # Create checkpoint every N logs
        enable_write_ahead: bool = True,
        enable_signing: bool = False,
        signing_key_path: str | None = None,
    ):
        self.staging_dir = Path(staging_dir)
        self.production_dir = Path(production_dir)
        self.hash_algorithm = hash_algorithm
        self.checkpoint_interval = checkpoint_interval
        self.enable_write_ahead = enable_write_ahead
        self.enable_signing = enable_signing
        self.signing_key_path = signing_key_path

        # State
        self.previous_hash = "0"  # Genesis hash
        self.log_count = 0
        self.checkpoints: list[IntegrityCheckpoint] = []
        self.lock = Lock()

        # Initialize directories
        self._initialize_directories()

        # Load existing state
        self._load_state()

    def _initialize_directories(self):
        """Create necessary directories if they don't exist"""
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.production_dir.mkdir(parents=True, exist_ok=True)

        # Create immutable flag directory
        immutable_dir = self.staging_dir / "immutable"
        immutable_dir.mkdir(exist_ok=True)

    def _load_state(self):
        """Load previous hash and checkpoints from disk"""
        state_file = self.production_dir / "integrity_state.json"

        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                    self.previous_hash = state.get("previous_hash", "0")
                    self.log_count = state.get("log_count", 0)

                # Load checkpoints
                checkpoint_file = self.production_dir / "checkpoints.json"
                if checkpoint_file.exists():
                    with open(checkpoint_file) as f:
                        checkpoints_data = json.load(f)
                        self.checkpoints = [
                            IntegrityCheckpoint(
                                checkpoint_id=cp["checkpoint_id"],
                                timestamp=datetime.fromisoformat(cp["timestamp"]),
                                log_count=cp["log_count"],
                                last_hash=cp["last_hash"],
                                merkle_root=cp.get("merkle_root"),
                                signature=cp.get("signature"),
                            )
                            for cp in checkpoints_data
                        ]

                logger.info(
                    f"Loaded integrity state: {self.log_count} logs, previous_hash={self.previous_hash[:16]}..."
                )
            except Exception as e:
                logger.warning(f"Warning: Failed to load integrity state: {e}")

    def _save_state(self):
        """Save current state to disk"""
        state_file = self.production_dir / "integrity_state.json"

        with open(state_file, "w") as f:
            json.dump(
                {
                    "previous_hash": self.previous_hash,
                    "log_count": self.log_count,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
            )

        # Save checkpoints
        checkpoint_file = self.production_dir / "checkpoints.json"
        with open(checkpoint_file, "w") as f:
            json.dump(
                [
                    {
                        "checkpoint_id": cp.checkpoint_id,
                        "timestamp": cp.timestamp.isoformat(),
                        "log_count": cp.log_count,
                        "last_hash": cp.last_hash,
                        "merkle_root": cp.merkle_root,
                        "signature": cp.signature,
                    }
                    for cp in self.checkpoints
                ],
                f,
                indent=2,
            )

    def _compute_hash(self, data: str) -> str:
        """Compute hash of data using configured algorithm"""
        if self.hash_algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        if self.hash_algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")

    def _compute_event_hash(self, event: SecurityEvent) -> str:
        """
        Compute hash of event for integrity verification.

        Hash includes: event_type, timestamp, actor_user_id, resource_id,
                      description, and previous_hash
        """
        hash_data = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "actor_user_id": event.actor_user_id,
            "resource_id": event.resource_id,
            "description": event.description,
            "previous_hash": self.previous_hash,
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return self._compute_hash(hash_string)

    def chain_event(self, event: SecurityEvent) -> SecurityEvent:
        """
        Add event to hash chain.

        Each event contains the hash of the previous event, creating
        a tamper-evident chain. If any event is modified, all subsequent
        events will fail verification.

        Args:
            event: Event to add to chain

        Returns:
            Event with hash fields populated
        """
        with self.lock:
            # Set previous hash
            event.previous_hash = self.previous_hash

            # Compute current hash
            event.current_hash = self._compute_event_hash(event)

            # Update state
            self.previous_hash = event.current_hash
            self.log_count += 1

            # Create checkpoint if needed
            if self.log_count % self.checkpoint_interval == 0:
                self._create_checkpoint()

            # Save state periodically
            if self.log_count % 100 == 0:
                self._save_state()

            return event

    def _create_checkpoint(self):
        """Create integrity checkpoint"""
        checkpoint = IntegrityCheckpoint(
            checkpoint_id=f"cp_{int(time.time())}",
            timestamp=datetime.utcnow(),
            log_count=self.log_count,
            last_hash=self.previous_hash,
        )

        self.checkpoints.append(checkpoint)

        # Keep only last 100 checkpoints
        if len(self.checkpoints) > 100:
            self.checkpoints = self.checkpoints[-100:]

    def write_ahead(self, event: SecurityEvent) -> str:
        """
        Write event to immutable staging area (write-ahead log).

        This ensures logs are persisted before processing continues,
        preventing log loss on system failure.

        Args:
            event: Event to write

        Returns:
            Path to written log file
        """
        if not self.enable_write_ahead:
            return ""

        # Create staging file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"log_{timestamp}_{event.event_id}.json"
        staging_path = self.staging_dir / "immutable" / filename

        # Write to staging
        with open(staging_path, "w") as f:
            json.dump(event.dict(), f, indent=2, default=str)

        # Make file immutable (append-only)
        try:
            os.chmod(staging_path, 0o444)  # Read-only
        except Exception as e:
            logger.warning(f"Warning: Could not make log file immutable: {e}")

        return str(staging_path)

    def promote_to_production(self, staging_path: str) -> str:
        """
        Promote log from staging to production.

        Args:
            staging_path: Path to staged log file

        Returns:
            Production log file path
        """
        # Create production path
        staging_filename = Path(staging_path).name
        production_path = self.production_dir / staging_filename

        # Move file
        os.rename(staging_path, production_path)

        return str(production_path)

    def verify_chain(self, events: list[SecurityEvent]) -> tuple[bool, list[str]]:
        """
        Verify integrity of hash chain.

        Args:
            events: List of events to verify

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        expected_previous_hash = "0"  # Genesis hash

        for i, event in enumerate(events):
            # Verify previous hash link
            if event.previous_hash != expected_previous_hash:
                errors.append(
                    f"Event {i} ({event.event_id}): Broken chain link. "
                    f"Expected prev_hash={expected_previous_hash[:16]}, "
                    f"got={event.previous_hash[:16] if event.previous_hash else 'None'}"
                )

            # Verify current hash
            computed_hash = self._compute_event_hash(event)
            if event.current_hash != computed_hash:
                errors.append(
                    f"Event {i} ({event.event_id}): Invalid hash. "
                    f"Expected={computed_hash[:16]}, got={event.current_hash[:16] if event.current_hash else 'None'}"
                )

            # Update expected hash for next iteration
            expected_previous_hash = event.current_hash

        is_valid = len(errors) == 0
        return is_valid, errors

    def verify_batch(self, batch: SecurityLogBatch) -> tuple[bool, list[str]]:
        """
        Verify integrity of a log batch.

        Args:
            batch: Batch to verify

        Returns:
            (is_valid, list_of_errors)
        """
        # Verify event chain
        is_valid, errors = self.verify_chain(batch.events)

        # Verify batch hash if present
        if batch.batch_hash:
            computed_batch_hash = self._compute_batch_hash(batch)
            if batch.batch_hash != computed_batch_hash:
                errors.append(
                    f"Batch {batch.batch_id}: Invalid batch hash. "
                    f"Expected={computed_batch_hash[:16]}, got={batch.batch_hash[:16]}"
                )

        is_valid = len(errors) == 0
        return is_valid, errors

    def _compute_batch_hash(self, batch: SecurityLogBatch) -> str:
        """Compute hash of entire batch"""
        # Create Merkle root of all events
        if not batch.events:
            return self._compute_hash("")

        merkle_root = self._compute_merkle_root(
            [e.current_hash for e in batch.events if e.current_hash]
        )

        # Include batch metadata
        hash_data = {
            "batch_id": batch.batch_id,
            "timestamp": batch.batch_timestamp.isoformat(),
            "event_count": batch.event_count,
            "merkle_root": merkle_root,
        }

        return self._compute_hash(json.dumps(hash_data, sort_keys=True))

    def _compute_merkle_root(self, hashes: list[str]) -> str:
        """
        Compute Merkle root from list of hashes.

        Efficient O(log n) verification for large batches.
        """
        if not hashes:
            return ""

        # Convert all to strings if needed
        hash_strings = [
            h if isinstance(h, str) else h.decode() if isinstance(h, bytes) else str(h)
            for h in hashes
        ]

        # If odd number of hashes, duplicate last one
        if len(hash_strings) % 2 == 1:
            hash_strings.append(hash_strings[-1])

        # Reduce by pairing and hashing
        while len(hash_strings) > 1:
            new_level = []
            for i in range(0, len(hash_strings), 2):
                combined = hash_strings[i] + hash_strings[i + 1]
                new_hash = self._compute_hash(combined)
                new_level.append(new_hash)
            hash_strings = new_level

            # Handle odd number at each level
            if len(hash_strings) % 2 == 1:
                hash_strings.append(hash_strings[-1])

        return hash_strings[0]

    def create_batch(self, events: list[SecurityEvent]) -> SecurityLogBatch:
        """
        Create a log batch with integrity verification.

        Args:
            events: List of events to batch

        Returns:
            Batch with hash computed
        """
        batch = SecurityLogBatch(events=events, event_count=len(events))

        # Compute batch hash
        batch.batch_hash = self._compute_batch_hash(batch)

        # Optionally sign batch
        if self.enable_signing:
            batch.signature = self._sign_batch(batch)

        return batch

    def _sign_batch(self, batch: SecurityLogBatch) -> str | None:
        """Cryptographically sign batch (placeholder)"""
        # In production, use actual cryptographic signing
        # For now, return placeholder
        if not self.signing_key_path:
            return None

        # TODO: Implement actual signing using RSA/ECDSA
        # import cryptography.hazmat.primitives.asymmetric as asym
        # ...
        return f"SIGNED:{batch.batch_hash[:16]}"

    def get_integrity_report(self) -> dict[str, Any]:
        """
        Generate integrity report.

        Returns:
            Dictionary with integrity statistics
        """
        return {
            "total_logs": self.log_count,
            "current_hash": self.previous_hash,
            "checkpoints_count": len(self.checkpoints),
            "last_checkpoint": (
                self.checkpoints[-1].dict() if self.checkpoints else None
            ),
            "hash_algorithm": self.hash_algorithm,
            "write_ahead_enabled": self.enable_write_ahead,
            "signing_enabled": self.enable_signing,
            "staging_dir": str(self.staging_dir),
            "production_dir": str(self.production_dir),
        }

    async def verify_recent_logs(self, count: int = 100) -> tuple[bool, list[str]]:
        """
        Verify most recent logs for integrity.

        Args:
            count: Number of recent logs to verify

        Returns:
            (is_valid, list_of_errors)
        """
        # Load recent logs from production directory
        log_files = sorted(self.production_dir.glob("log_*.json"), reverse=True)[:count]

        events = []
        for log_file in log_files:
            try:
                with open(log_file) as f:
                    event_data = json.load(f)
                    event = SecurityEvent(**event_data)
                    events.append(event)
            except Exception as e:
                return False, [f"Failed to load log file {log_file}: {e}"]

        # Sort by timestamp to verify chain
        events.sort(key=lambda e: e.timestamp)

        # Verify chain
        return self.verify_chain(events)


# Singleton instance
_default_integrity_manager = None


def get_integrity_manager() -> LogIntegrityManager:
    """Get default integrity manager instance"""
    global _default_integrity_manager
    if _default_integrity_manager is None:
        _default_integrity_manager = LogIntegrityManager()
    return _default_integrity_manager
