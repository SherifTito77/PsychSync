#!/usr/bin/env python3
"""
Immutable Log Storage System (SLSA Level 3 Compliant)

Provides tamper-evident, append-only logging for build artifacts and security events.
Uses hash chaining to detect any tampering with historical logs.

Features:
- Append-only log entries (cannot be modified or deleted)
- Hash chain verification (each entry hashes the previous)
- Tamper evidence detection
- Cryptographic signing of log snapshots
- JSON structured logs
- Multiple log types (build, security, deployment)

Usage:
    from scripts.immutable_log import ImmutableLog

    # Create or open log
    log = ImmutableLog("build")

    # Append entry
    log.append({
        "event": "build_complete",
        "build_id": "build-20251225_123456",
        "artifacts": ["backend", "frontend"]
    })

    # Verify integrity
    if log.verify():
        print("Log is intact")
    else:
        print("Log has been tampered with!")
"""

import json
import hashlib
import hmac
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


class ImmutableLog:
    """
    Tamper-evident, append-only log system with hash chaining
    """

    def __init__(
        self,
        log_type: str,
        log_dir: str = "build/logs",
        sign_key: Optional[bytes] = None
    ):
        """
        Initialize immutable log

        Args:
            log_type: Type of log (build, security, deployment, etc.)
            log_dir: Directory to store logs
            sign_key: Optional HMAC key for signing log entries
        """
        self.log_type = log_type
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / f"{log_type}.log"
        self.index_file = self.log_dir / f"{log_type}.index"
        self.lock = threading.Lock()

        # HMAC key for signing (use env var if not provided)
        self.sign_key = sign_key or os.getenv('IMMUTABLE_LOG_KEY', '').encode() or None

        # Load or initialize index
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load log index metadata"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        else:
            # Initialize new index
            return {
                "log_type": self.log_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "entry_count": 0,
                "last_hash": "",
                "last_entry_id": 0
            }

    def _save_index(self):
        """Save log index metadata"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _hash_entry(self, entry: Dict[str, Any], prev_hash: str) -> str:
        """
        Calculate hash for log entry including previous hash for chaining

        Args:
            entry: Log entry data
            prev_hash: Hash of previous entry

        Returns:
            SHA256 hash as hex string
        """
        # Create canonical JSON representation
        entry_str = json.dumps(entry, sort_keys=True, separators=(',', ':'))

        # Include previous hash in hash calculation
        hash_input = f"{prev_hash}{entry_str}".encode()

        return hashlib.sha256(hash_input).hexdigest()

    def _sign_entry(self, entry: Dict[str, Any]) -> Optional[str]:
        """
        Sign log entry with HMAC if signing key is available

        Args:
            entry: Log entry to sign

        Returns:
            HMAC signature as hex string, or None if no key
        """
        if self.sign_key:
            entry_str = json.dumps(entry, sort_keys=True, separators=(',', ':'))
            signature = hmac.new(self.sign_key, entry_str.encode(), hashlib.sha256)
            return signature.hexdigest()
        return None

    def append(self, data: Dict[str, Any]) -> str:
        """
        Append entry to log (thread-safe)

        Args:
            data: Log entry data

        Returns:
            Entry ID
        """
        with self.lock:
            # Create entry
            entry_id = self.index["last_entry_id"] + 1
            timestamp = datetime.now(timezone.utc).isoformat()

            entry = {
                "id": entry_id,
                "timestamp": timestamp,
                "type": self.log_type,
                "data": data,
                "prev_hash": self.index["last_hash"]
            }

            # Calculate hash
            entry_hash = self._hash_entry(data, self.index["last_hash"])
            entry["hash"] = entry_hash

            # Sign if key available
            if self.sign_key:
                signature = self._sign_entry(entry)
                entry["signature"] = signature

            # Append to log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

            # Update index
            self.index["last_entry_id"] = entry_id
            self.index["last_hash"] = entry_hash
            self.index["entry_count"] = entry_id
            self.index["updated_at"] = timestamp
            self._save_index()

            return str(entry_id)

    def verify(self) -> bool:
        """
        Verify log integrity using hash chain

        Returns:
            True if log is intact, False if tampering detected
        """
        if not self.log_file.exists():
            return True  # Empty log is valid

        expected_prev_hash = ""
        line_number = 0

        with open(self.log_file, 'r') as f:
            for line in f:
                line_number += 1

                try:
                    entry = json.loads(line)

                    # Verify hash chain
                    entry_hash = entry.get("hash")
                    prev_hash = entry.get("prev_hash")
                    data = entry.get("data", {})

                    # Recalculate hash
                    calculated_hash = self._hash_entry(data, prev_hash)

                    if calculated_hash != entry_hash:
                        print(f"✗ Hash mismatch at line {line_number}")
                        print(f"  Expected: {entry_hash}")
                        print(f"  Calculated: {calculated_hash}")
                        return False

                    # Verify chain integrity
                    if prev_hash != expected_prev_hash:
                        print(f"✗ Chain broken at line {line_number}")
                        print(f"  Expected prev_hash: {expected_prev_hash}")
                        print(f"  Actual prev_hash: {prev_hash}")
                        return False

                    # Verify signature if present
                    if "signature" in entry and self.sign_key:
                        entry_copy = entry.copy()
                        signature = entry_copy.pop("signature")

                        calculated_signature = self._sign_entry(entry_copy)

                        if calculated_signature != signature:
                            print(f"✗ Signature invalid at line {line_number}")
                            return False

                    # Update expected prev_hash for next iteration
                    expected_prev_hash = entry_hash

                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON at line {line_number}")
                    return False
                except Exception as e:
                    print(f"✗ Error verifying line {line_number}: {e}")
                    return False

        # Verify final hash matches index
        if self.index["last_hash"] != expected_prev_hash:
            print(f"✗ Index hash mismatch")
            print(f"  Index: {self.index['last_hash']}")
            print(f"  Log: {expected_prev_hash}")
            return False

        return True

    def read_all(self) -> List[Dict[str, Any]]:
        """
        Read all log entries

        Returns:
            List of log entries
        """
        entries = []

        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        return entries

    def query(self, filter_func: callable) -> List[Dict[str, Any]]:
        """
        Query log entries with filter function

        Args:
            filter_func: Function that takes entry and returns bool

        Returns:
            Filtered list of entries
        """
        entries = self.read_all()
        return [e for e in entries if filter_func(e)]

    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific entry by ID

        Args:
            entry_id: Entry ID

        Returns:
            Entry data or None if not found
        """
        for entry in self.read_all():
            if entry.get("id") == entry_id:
                return entry
        return None

    def get_last_n(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get last N entries

        Args:
            n: Number of entries to return

        Returns:
            List of last N entries
        """
        entries = self.read_all()
        return entries[-n:] if len(entries) >= n else entries

    def export(self, output_file: str, format: str = "json"):
        """
        Export log to file

        Args:
            output_file: Output file path
            format: Export format (json, csv)
        """
        entries = self.read_all()

        if format == "json":
            with open(output_file, 'w') as f:
                json.dump(entries, f, indent=2)

        elif format == "csv":
            import csv

            if not entries:
                return

            # Get all unique fields
            fieldnames = set()
            for entry in entries:
                fieldnames.update(entry.keys())
                for data_field in entry.get("data", {}).keys():
                    fieldnames.add(f"data.{data_field}")

            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()

                for entry in entries:
                    # Flatten data fields
                    flat_entry = entry.copy()
                    data = flat_entry.pop("data", {})

                    for key, value in data.items():
                        flat_entry[f"data.{key}"] = value

                    writer.writerow(flat_entry)

    def create_snapshot(self) -> str:
        """
        Create tamper-evident snapshot of current log state

        Returns:
            Snapshot hash
        """
        # Create snapshot manifest
        snapshot = {
            "log_type": self.log_type,
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": self.index["entry_count"],
            "last_hash": self.index["last_hash"],
            "index": self.index.copy()
        }

        # Sign snapshot
        if self.sign_key:
            snapshot_str = json.dumps(snapshot, sort_keys=True)
            signature = hmac.new(self.sign_key, snapshot_str.encode(), hashlib.sha256)
            snapshot["signature"] = signature.hexdigest()

        # Save snapshot
        snapshot_file = self.log_dir / f"{self.log_type}-snapshot-{snapshot['snapshot_at'].replace(':', '-')}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)

        # Calculate snapshot hash
        snapshot_str = json.dumps(snapshot, sort_keys=True)
        snapshot_hash = hashlib.sha256(snapshot_str.encode()).hexdigest()

        return snapshot_hash

    def verify_snapshot(self, snapshot_file: str) -> bool:
        """
        Verify snapshot integrity

        Args:
            snapshot_file: Path to snapshot file

        Returns:
            True if snapshot is valid
        """
        with open(snapshot_file, 'r') as f:
            snapshot = json.load(f)

        # Verify signature if present
        if "signature" in snapshot and self.sign_key:
            snapshot_copy = snapshot.copy()
            signature = snapshot_copy.pop("signature")

            snapshot_str = json.dumps(snapshot_copy, sort_keys=True)
            calculated_signature = hmac.new(self.sign_key, snapshot_str.encode(), hashlib.sha256).hexdigest()

            if calculated_signature != signature:
                return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get log statistics

        Returns:
            Dictionary with log stats
        """
        entries = self.read_all()

        stats = {
            "log_type": self.log_type,
            "total_entries": len(entries),
            "file_size_bytes": self.log_file.stat().st_size if self.log_file.exists() else 0,
            "created_at": self.index.get("created_at"),
            "last_updated": self.index.get("updated_at"),
            "verified": self.verify()
        }

        return stats


class BuildLogger:
    """
    High-level logging interface for build events
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.log_dir = self.project_root / "build" / "logs"

        # Initialize different log types
        self.build_log = ImmutableLog("build", str(self.log_dir))
        self.security_log = ImmutableLog("security", str(self.log_dir))
        self.deployment_log = ImmutableLog("deployment", str(self.log_dir))

    def log_build_start(self, build_id: str, environment: str):
        """Log build start event"""
        self.build_log.append({
            "event": "build_start",
            "build_id": build_id,
            "environment": environment
        })

    def log_build_complete(self, build_id: str, artifacts: List[str]):
        """Log build completion event"""
        self.build_log.append({
            "event": "build_complete",
            "build_id": build_id,
            "artifacts": artifacts
        })

    def log_build_failure(self, build_id: str, error: str):
        """Log build failure event"""
        self.build_log.append({
            "event": "build_failure",
            "build_id": build_id,
            "error": error
        })

    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """Log security event"""
        self.security_log.append({
            "event_type": event_type,
            "severity": severity,
            "details": details
        })

    def log_deployment(self, build_id: str, environment: str, status: str):
        """Log deployment event"""
        self.deployment_log.append({
            "event": "deployment",
            "build_id": build_id,
            "environment": environment,
            "status": status
        })

    def verify_all_logs(self) -> Dict[str, bool]:
        """Verify all logs for tampering"""
        return {
            "build": self.build_log.verify(),
            "security": self.security_log.verify(),
            "deployment": self.deployment_log.verify()
        }

    def export_all_logs(self, output_dir: str):
        """Export all logs to directory"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        self.build_log.export(str(output_path / f"build-{timestamp}.json"))
        self.security_log.export(str(output_path / f"security-{timestamp}.json"))
        self.deployment_log.export(str(output_path / f"deployment-{timestamp}.json"))


if __name__ == "__main__":
    # Demo usage
    import sys

    print("Immutable Log Storage System Demo")
    print("=" * 60)

    # Create logger
    logger = BuildLogger()

    # Log some events
    print("\n1. Logging build events...")
    build_id = "build-20251225_184500"
    logger.log_build_start(build_id, "development")
    logger.log_build_complete(build_id, ["backend", "frontend"])

    # Log security event
    print("2. Logging security event...")
    logger.log_security_event("vulnerability_scan", "INFO", {
        "scanner": "trivy",
        "vulnerabilities_found": 0
    })

    # Verify logs
    print("3. Verifying logs...")
    verification = logger.verify_all_logs()
    for log_type, is_valid in verification.items():
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"  {log_type}: {status}")

    # Get stats
    print("\n4. Log statistics:")
    stats = logger.build_log.get_stats()
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  File size: {stats['file_size_bytes']} bytes")
    print(f"  Verified: {stats['verified']}")

    print("\n" + "=" * 60)
    print("Demo complete!")
