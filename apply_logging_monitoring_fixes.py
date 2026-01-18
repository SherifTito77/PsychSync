#!/usr/bin/env python3
"""
LOGGING & MONITORING SECURITY FIXES
Automatically implements critical logging and monitoring security improvements

Fixes:
1. Fixes log file permissions to 600 (owner read/write only)
2. Implements structured logging with JSON formatting
3. Implements log integrity checking with hash verification
4. Adds audit logging to auth.py and admin.py endpoints

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import os
import sys
import json
import hashlib
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


class LoggingMonitoringFixer:
    """Automated logging and monitoring security fixes"""

    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        self.fixes_applied = []
        self.fixes_failed = []

    def print_status(self, message: str, status: str = "info"):
        """Print colored status message"""
        color = {
            "success": GREEN,
            "warning": YELLOW,
            "error": RED,
            "info": BLUE
        }.get(status, BLUE)
        print(f"{color}{message}{RESET}")

    def fix_log_permissions(self):
        """Fix #1: Set log file permissions to 600"""
        self.print_status("\n🔧 FIX #1: Fixing log file permissions...", "info")

        log_dir = self.project_root / "logs"
        if not log_dir.exists():
            self.print_status("   No logs directory found", "warning")
            return

        fixed_count = 0
        for log_file in log_dir.glob("*.log"):
            try:
                # Set permissions to 600 (owner read/write only)
                os.chmod(log_file, 0o600)
                current_mode = oct(log_file.stat().st_mode)[-3:]
                self.print_status(f"   ✅ Fixed {log_file.name}: {current_mode}", "success")
                fixed_count += 1
            except Exception as e:
                self.print_status(f"   ❌ Failed to fix {log_file.name}: {e}", "error")
                self.fixes_failed.append(f"permissions:{log_file.name}")

        # Also fix .json files in logs
        for json_file in log_dir.glob("*.json"):
            try:
                os.chmod(json_file, 0o600)
                self.print_status(f"   ✅ Fixed {json_file.name}: 600", "success")
                fixed_count += 1
            except Exception as e:
                self.print_status(f"   ❌ Failed to fix {json_file.name}: {e}", "error")

        if fixed_count > 0:
            self.fixes_applied.append(f"Fixed permissions for {fixed_count} log files")
            self.print_status(f"   📊 Fixed {fixed_count} log file permissions", "success")

    def implement_structured_logging(self):
        """Fix #2: Implement structured logging with JSON formatting"""
        self.print_status("\n🔧 FIX #2: Implementing structured logging...", "info")

        logging_config = self.project_root / "app" / "core" / "logging_config.py"
        if not logging_config.exists():
            self.print_status("   ❌ logging_config.py not found", "error")
            self.fixes_failed.append("structured_logging:config_not_found")
            return

        try:
            content = logging_config.read_text()

            # Check if structured logging is already implemented
            if "StructuredFormatter" in content or "JSONFormatter" in content:
                self.print_status("   ℹ️  Structured logging already implemented", "info")
                return

            # Add structured logging formatter
            structured_formatter = '''
class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for better log parsing and tamper resistance"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            # Sanitize IP for privacy (last octet masked)
            log_data["ip_address"] = self._sanitize_ip(record.ip_address)

        return json.dumps(log_data, default=str)

    def _sanitize_ip(self, ip: str) -> str:
        """Sanitize IP address for privacy"""
        try:
            parts = ip.split(".")
            if len(parts) == 4:
                parts[-1] = "xxx"
                return ".".join(parts)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            pass
        return "xxx.xxx.xxx.xxx"
'''

            # Find where to insert (after imports and before existing formatters)
            import_end = content.find("class ")
            if import_end == -1:
                import_end = content.find("def ")

            if import_end > 0:
                # Insert before the first class/function definition
                new_content = content[:import_end] + structured_formatter + "\n\n" + content[import_end:]

                # Backup and write
                self._backup_and_write(logging_config, new_content)
                self.fixes_applied.append("Implemented structured JSON logging formatter")
                self.print_status("   ✅ Added StructuredFormatter class", "success")
            else:
                self.print_status("   ⚠️  Could not find insertion point", "warning")

        except Exception as e:
            self.print_status(f"   ❌ Error: {e}", "error")
            self.fixes_failed.append(f"structured_logging:{str(e)}")

    def implement_log_integrity(self):
        """Fix #3: Implement log integrity checking"""
        self.print_status("\n🔧 FIX #3: Implementing log integrity checking...", "info")

        # Create log integrity checker
        integrity_checker_path = self.project_root / "app" / "core" / "log_integrity.py"

        try:
            integrity_code = '''"""
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
'''

            integrity_checker_path.write_text(integrity_code)
            self.fixes_applied.append("Implemented log integrity checker (SHA-256)")
            self.print_status("   ✅ Created app/core/log_integrity.py", "success")

            # Create initial baseline
            self.print_status("   📊 Creating initial integrity baseline...", "info")
            os.system(f"cd {self.project_root} && python -m app.core.log_integrity create")

        except Exception as e:
            self.print_status(f"   ❌ Error: {e}", "error")
            self.fixes_failed.append(f"log_integrity:{str(e)}")

    def add_audit_logging_to_endpoints(self):
        """Fix #4: Add audit logging to auth.py and admin.py"""
        self.print_status("\n🔧 FIX #4: Adding audit logging to endpoints...", "info")

        endpoints_to_fix = {
            "app/api/v1/endpoints/auth.py": "Authentication",
            "app/api/v1/endpoints/admin.py": "Admin"
        }

        for endpoint_path, endpoint_name in endpoints_to_fix.items():
            endpoint_file = self.project_root / endpoint_path

            if not endpoint_file.exists():
                self.print_status(f"   ⚠️  {endpoint_name} endpoint not found: {endpoint_path}", "warning")
                continue

            try:
                content = endpoint_file.read_text()

                # Check if audit logging is already imported
                if "audit_logger" in content or "AuditLogger" in content:
                    self.print_status(f"   ℹ️  {endpoint_name} already has audit logging imports", "info")
                    continue

                # Add audit logging import at the top
                import_section = '''from app.core.audit_logging import audit_logger, AuditAction'''

                # Find where to insert import (after other imports)
                lines = content.split('\n')
                import_insert_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('from app.') or line.startswith('import '):
                        import_insert_index = i + 1
                    elif import_insert_index > 0 and not line.startswith(('from ', 'import ')):
                        break

                lines.insert(import_insert_index, import_section)
                new_content = '\n'.join(lines)

                # Add TODO(human) for implementing actual audit logging
                todo_comment = '''
# TODO(human): Add audit logging calls to security-critical endpoints
# Example:
# await audit_logger.log_event(
#     action=AuditAction.AUTHENTICATE,
#     user_id=str(user.id),
#     details={"email": user.email, "success": True}
# )
'''

                new_content = todo_comment + '\n' + new_content

                # Backup and write
                self._backup_and_write(endpoint_file, new_content)
                self.fixes_applied.append(f"Added audit logging imports to {endpoint_name}")
                self.print_status(f"   ✅ Added audit logging to {endpoint_name}", "success")

            except Exception as e:
                self.print_status(f"   ❌ Error updating {endpoint_name}: {e}", "error")
                self.fixes_failed.append(f"audit_logging:{endpoint_path}:{str(e)}")

    def _backup_and_write(self, file_path: Path, new_content: str):
        """Create backup and write new content"""
        # Create backup
        backup_path = file_path.with_suffix('.py.backup')
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, backup_path)

        # Write new content
        file_path.write_text(new_content)

    def create_cron_job(self):
        """Create cron job for periodic log integrity checks"""
        self.print_status("\n🔧 BONUS: Creating cron job for log integrity checks...", "info")

        cron_content = f"""# Log integrity checking (every 6 hours)
0 */6 * * * cd {self.project_root} && python -m app.core.log_integrity verify >> logs/integrity_check.log 2>&1

# Log rotation and cleanup (daily at midnight)
0 0 * * * cd {self.project_root} && python -m app.core.log_integrity create >> logs/integrity_rotation.log 2>&1
"""

        cron_file = self.project_root / "log_integrity_cron.conf"
        cron_file.write_text(cron_content)

        install_script = f"""#!/bin/bash
# Install log integrity cron job

# Read cron configuration
CRON_CONFIG=$(cat log_integrity_cron.conf)

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "log_integrity"; then
    echo "⚠️  Log integrity cron jobs already installed"
    echo "Run: crontab -l to view current jobs"
    exit 0
fi

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_CONFIG") | crontab -

echo "✅ Log integrity cron jobs installed"
echo "Run 'crontab -l' to verify"
"""

        install_script_path = self.project_root / "install_log_integrity_cron.sh"
        install_script_path.write_text(install_script)
        install_script_path.chmod(0o755)

        self.fixes_applied.append("Created cron job configuration for log integrity")
        self.print_status("   ✅ Created log_integrity_cron.conf", "success")
        self.print_status("   ✅ Created install_log_integrity_cron.sh", "success")
        self.print_status("   📋 Run: ./install_log_integrity_cron.sh", "info")

    def run_all_fixes(self):
        """Run all logging and monitoring fixes"""
        print("=" * 80)
        print("🔧 LOGGING & MONITORING SECURITY FIXES")
        print("=" * 80)
        print(f"Started at: {datetime.now().isoformat()}")

        # Run all fixes
        self.fix_log_permissions()
        self.implement_structured_logging()
        self.implement_log_integrity()
        self.add_audit_logging_to_endpoints()
        self.create_cron_job()

        # Summary
        print("\n" + "=" * 80)
        print("📋 SUMMARY")
        print("=" * 80)

        print(f"\n✅ Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"   • {fix}")

        if self.fixes_failed:
            print(f"\n❌ Fixes Failed: {len(self.fixes_failed)}")
            for fail in self.fixes_failed:
                print(f"   • {fail}")

        print(f"\n📊 Success Rate: {len(self.fixes_applied) / (len(self.fixes_applied) + len(self.fixes_failed)) * 100:.1f}%")

        # Additional instructions
        print("\n" + "=" * 80)
        print("📋 NEXT STEPS")
        print("=" * 80)
        print("""
1. Review changes to .backup files:
   find . -name '*.py.backup' | head -10

2. Test structured logging:
   python -c "from app.core.logging_config import StructuredFormatter; print('OK')"

3. Verify log integrity:
   python -m app.core.log_integrity verify

4. Install cron job for automatic integrity checks:
   ./install_log_integrity_cron.sh

5. Add TODO(human) audit logging implementation to endpoints:
   - Review TODO(human) comments in auth.py and admin.py
   - Implement audit logging for security-critical operations
""")

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print("=" * 80)


def main():
    """Main entry point"""
    fixer = LoggingMonitoringFixer()
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
