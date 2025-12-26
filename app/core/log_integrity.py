"""
Log Integrity Checker - Hash-based verification for log files
Prevents log tampering by maintaining cryptographic hashes
"""

import os
import hashlib
import json
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class LogIntegrityChecker:
    """Verifies log file integrity using cryptographic hashes"""

    def __init__(self, log_dir: str = "logs", integrity_file: str = "logs/integrity.json"):
        self.log_dir = Path(log_dir)
        self.integrity_file = Path(integrity_file)
        self.lock_file = self.log_dir / ".integrity.lock"

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def calculate_integrity(self) -> Dict[str, str]:
        """Calculate hashes for all log files"""
        integrity_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "files": {}
        }

        if not self.log_dir.exists():
            return integrity_data

        for log_file in self.log_dir.glob("*.log"):
            try:
                file_hash = self._get_file_hash(log_file)
                file_size = log_file.stat().st_size
                integrity_data["files"][log_file.name] = {
                    "sha256": file_hash,
                    "size": file_size,
                    "last_modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
            except Exception as e:
                print(f"Warning: Could not hash {log_file.name}: {e}")

        return integrity_data

    def save_integrity(self) -> bool:
        """Save current integrity state to file"""
        try:
            integrity_data = self.calculate_integrity()

            # Use file locking to prevent race conditions
            with open(self.integrity_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(integrity_data, f, indent=2)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return True
        except Exception as e:
            print(f"Error saving integrity: {e}")
            return False

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify current logs against saved integrity state"""
        if not self.integrity_file.exists():
            return {"status": "no_baseline", "message": "No integrity baseline found"}

        try:
            with open(self.integrity_file, "r") as f:
                saved_integrity = json.load(f)
        except Exception as e:
            return {"status": "error", "message": f"Could not read integrity file: {e}"}

        current_integrity = self.calculate_integrity()
        issues = []

        # Check all files from saved state
        for filename, saved_data in saved_integrity.get("files", {}).items():
            current_data = current_integrity.get("files", {}).get(filename)

            if not current_data:
                issues.append({
                    "file": filename,
                    "issue": "missing",
                    "message": f"Log file {filename} no longer exists"
                })
            elif current_data["sha256"] != saved_data["sha256"]:
                issues.append({
                    "file": filename,
                    "issue": "tampered",
                    "message": f"Log file {filename} has been modified"
                })

        # Check for new files
        for filename in current_integrity.get("files", {}):
            if filename not in saved_integrity.get("files", {}):
                issues.append({
                    "file": filename,
                    "issue": "new",
                    "message": f"New log file {filename} detected"
                })

        if issues:
            return {
                "status": "failed",
                "issues": issues,
                "message": f"Found {len(issues)} integrity issues"
            }
        else:
            return {
                "status": "passed",
                "message": "All log files integrity verified"
            }

    def create_baseline(self):
        """Create initial integrity baseline"""
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)

        success = self.save_integrity()
        if success:
            print(f"✅ Integrity baseline created at {self.integrity_file}")
        else:
            print(f"❌ Failed to create integrity baseline")

        return success


def main():
    """CLI interface for log integrity checking"""
    import argparse

    parser = argparse.ArgumentParser(description="Log Integrity Checker")
    parser.add_argument("action", choices=["create", "verify", "check"],
                       help="Action to perform")
    parser.add_argument("--log-dir", default="logs",
                       help="Log directory path")
    parser.add_argument("--integrity-file", default="logs/integrity.json",
                       help="Integrity state file path")

    args = parser.parse_args()

    checker = LogIntegrityChecker(
        log_dir=args.log_dir,
        integrity_file=args.integrity_file
    )

    if args.action == "create":
        success = checker.create_baseline()
        exit(0 if success else 1)

    elif args.action in ["verify", "check"]:
        result = checker.verify_integrity()

        if result["status"] == "passed":
            print("✅ " + result["message"])
            exit(0)
        elif result["status"] == "no_baseline":
            print("ℹ️  " + result["message"])
            print("   Run: python log_integrity.py create")
            exit(1)
        else:  # failed
            print("❌ " + result["message"])
            for issue in result.get("issues", []):
                print(f"   - {issue['file']}: {issue['issue']}")
            exit(1)


if __name__ == "__main__":
    main()
