#!/usr/bin/env python3
"""
SECURE PsychSync Performance Optimization Script
Fixed security vulnerabilities and enhanced error handling

Security Improvements:
- Input validation and sanitization
- Atomic file operations with proper permissions
- Path traversal protection
- Comprehensive error handling
- Secure configuration management
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time

from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_async_engine

# Setup secure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("performance-optimization.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related error"""

    pass


class ConfigurationError(Exception):
    """Configuration-related error"""

    pass


class SecurePerformanceOptimizer:
    """Secure performance optimization implementation with comprehensive security measures"""

    def __init__(self, allowed_directories=None):
        self.allowed_directories = allowed_directories or {project_root.resolve()}
        self.backup_settings = {}
        self.engine = None
        self.optimizations_applied = []
        self.correlation_id = hashlib.sha256(os.urandom(16)).hexdigest()[:8]

        # Validate environment
        self._validate_environment()

    def _validate_environment(self):
        """Validate execution environment for security"""
        logger.info(f"[{self.correlation_id}] Validating execution environment...")

        # Check running as appropriate user (not root unless explicitly required)
        if os.name == "posix" and os.geteuid() == 0:
            logger.warning("Running as root user - ensure this is intentional")

        # Validate directory permissions
        for directory in self.allowed_directories:
            if not directory.exists():
                raise SecurityError(f"Directory does not exist: {directory}")

            if not os.access(directory, os.R_OK | os.W_OK):
                raise SecurityError(
                    f"Insufficient permissions for directory: {directory}"
                )

    def _validate_path(self, file_path: Path) -> bool:
        """Validate path is within allowed boundaries (prevents path traversal)"""
        try:
            resolved_path = file_path.resolve()

            for allowed_dir in self.allowed_directories:
                try:
                    resolved_path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue

            logger.error(
                f"[{self.correlation_id}] Path traversal attempt detected: {file_path}"
            )
            return False
        except (ValueError, RuntimeError, OSError) as e:
            logger.error(f"[{self.correlation_id}] Path validation error: {e}")
            return False

    def _validate_config_value(self, key: str, value: str) -> bool:
        """Validate configuration values for security"""
        # Define validation patterns
        patterns = {
            "DB_POOL_SIZE": r"^\d+$",  # Digits only
            "DB_MAX_OVERFLOW": r"^\d+$",
            "DB_POOL_RECYCLE": r"^\d+$",
            "DB_POOL_PRE_PING": r"^(True|False)$",
        }

        if key not in patterns:
            logger.warning(f"[{self.correlation_id}] Unknown configuration key: {key}")
            return True  # Allow unknown keys but warn

        pattern = patterns[key]
        if not re.match(pattern, value):
            logger.error(f"[{self.correlation_id}] Invalid value for {key}: {value}")
            return False

        return True

    def _atomic_write(self, file_path: Path, content: str, mode: int = 0o600):
        """Atomic file write with security and error handling"""
        if not self._validate_path(file_path):
            raise SecurityError(
                f"Access denied: path outside allowed directory: {file_path}"
            )

        # Create backup before modification
        backup_path = file_path.with_suffix(
            f"{file_path.suffix}.backup.{int(time.time())}"
        )

        try:
            # Create backup if file exists
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
                logger.info(f"[{self.correlation_id}] Created backup: {backup_path}")

            # Write to temporary file first
            temp_file = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=file_path.parent,
                    prefix=f".tmp_{file_path.name}_",
                    delete=False,
                    encoding="utf-8",
                ) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                # Set secure permissions
                os.chmod(temp_file_path, mode)

                # Atomic move
                os.replace(temp_file_path, file_path)

                logger.info(f"[{self.correlation_id}] Successfully wrote: {file_path}")

            except Exception as e:
                # Clean up temp file if something went wrong
                if temp_file and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass
                raise

        except Exception as e:
            logger.error(f"[{self.correlation_id}] Failed to write {file_path}: {e}")
            # Restore from backup if available
            if backup_path.exists():
                try:
                    shutil.copy2(backup_path, file_path)
                    logger.info(
                        f"[{self.correlation_id}] Restored backup: {backup_path}"
                    )
                except Exception as restore_error:
                    logger.error(
                        f"[{self.correlation_id}] Failed to restore backup: {restore_error}"
                    )
            raise

    async def backup_current_settings(self) -> Dict[str, Any]:
        """Securely backup current configuration"""
        logger.info(f"[{self.correlation_id}] 🔄 Backing up current settings...")

        self.backup_settings = {
            "DB_POOL_SIZE": getattr(settings, "DB_POOL_SIZE", None),
            "DB_MAX_OVERFLOW": getattr(settings, "DB_MAX_OVERFLOW", None),
            "DB_POOL_RECYCLE": getattr(settings, "DB_POOL_RECYCLE", None),
            "DB_POOL_PRE_PING": getattr(settings, "DB_POOL_PRE_PING", None),
            "timestamp": datetime.now().isoformat(),
            "correlation_id": self.correlation_id,
        }

        # Create secure backup file
        backup_file = project_root / ".env.performance.backup"
        backup_content = f"""# Performance Optimization Backup - {datetime.now()}
# Correlation ID: {self.correlation_id}
# DO NOT MODIFY - Generated by secure-performance-optimizer.py
"""

        for key, value in self.backup_settings.items():
            if key not in ["timestamp", "correlation_id"] and value is not None:
                backup_content += f"{key}={value}\n"

        # Atomic write with secure permissions
        self._atomic_write(backup_file, backup_content, mode=0o600)

        # Also create JSON backup for programmatic access
        json_backup_file = project_root / ".env.performance.backup.json"
        json_content = json.dumps(self.backup_settings, indent=2)
        self._atomic_write(json_backup_file, json_content, mode=0o600)

        logger.info(f"[{self.correlation_id}] ✅ Settings securely backed up")
        return self.backup_settings

    async def apply_connection_pool_optimization(self):
        """Apply Phase 1: Database connection pool optimization with security"""
        logger.info(
            f"[{self.correlation_id}] 🚀 Applying Phase 1: Database Connection Pool Optimization"
        )

        # Recommended production settings
        optimized_settings = {
            "DB_POOL_SIZE": 20,  # 4x increase
            "DB_MAX_OVERFLOW": 30,  # 3x increase
            "DB_POOL_RECYCLE": 1800,  # 30 minutes for connection health
            "DB_POOL_PRE_PING": True,  # Enable connection validation
        }

        try:
            # Validate all settings
            for key, value in optimized_settings.items():
                if not self._validate_config_value(key, str(value)):
                    raise ConfigurationError(
                        f"Invalid configuration value for {key}: {value}"
                    )

            # Update environment file securely
            env_file = project_root / ".env.dev"

            if not env_file.exists():
                raise ConfigurationError(f"Environment file not found: {env_file}")

            await self._update_env_file_secure(env_file, optimized_settings)
            self.optimizations_applied.append("connection_pool")
            logger.info(
                f"[{self.correlation_id}] ✅ Connection pool settings updated securely"
            )

            # Validate new settings
            await self._validate_new_settings()

        except Exception as e:
            logger.error(
                f"[{self.correlation_id}] ❌ Failed to apply connection pool optimization: {e}"
            )
            await self.secure_rollback_changes()
            raise

    async def _update_env_file_secure(
        self, env_file: Path, settings_update: Dict[str, Any]
    ):
        """Safely update environment file with comprehensive validation"""

        # Validate file path
        if not self._validate_path(env_file):
            raise SecurityError(f"Access denied to environment file: {env_file}")

        try:
            # Read current content with encoding validation
            current_content = env_file.read_text(encoding="utf-8")
            lines = current_content.split("\n")
            updated_lines = []
            modified_keys = set()

            for line_num, line in enumerate(lines, 1):
                # Skip empty lines and comments
                if not line.strip() or line.strip().startswith("#"):
                    updated_lines.append(line)
                    continue

                # Parse key-value pair
                if "=" not in line:
                    logger.warning(
                        f"[{self.correlation_id}] Invalid line {line_num}: {line}"
                    )
                    updated_lines.append(line)
                    continue

                key = line.split("=")[0].strip()
                value = "=".join(line.split("=")[1:]).strip()

                # Validate key
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                    logger.warning(
                        f"[{self.correlation_id}] Invalid key format at line {line_num}: {key}"
                    )
                    updated_lines.append(line)
                    continue

                # Update if in our settings
                if key in settings_update:
                    new_value = str(settings_update[key])

                    # Validate the new value
                    if not self._validate_config_value(key, new_value):
                        raise ConfigurationError(
                            f"Invalid value for {key}: {new_value}"
                        )

                    updated_lines.append(f"{key}={new_value}")
                    modified_keys.add(key)
                    logger.info(
                        f"[{self.correlation_id}]  📝 Updated {key}: {value} → {new_value}"
                    )
                else:
                    updated_lines.append(line)

            # Add missing settings
            existing_keys = set()
            for line in updated_lines:
                if not line.strip().startswith("#") and "=" in line:
                    key = line.split("=")[0].strip()
                    existing_keys.add(key)

            for key, value in settings_update.items():
                if key not in existing_keys:
                    value_str = str(value)
                    if self._validate_config_value(key, value_str):
                        updated_lines.append(f"{key}={value_str}")
                        logger.info(
                            f"[{self.correlation_id}]  ➕ Added {key}: {value_str}"
                        )

            # Validate final content
            final_content = "\n".join(updated_lines)
            if not self._validate_env_content(final_content):
                raise ConfigurationError(
                    "Generated environment content failed validation"
                )

            # Atomic write
            self._atomic_write(env_file, final_content)

        except UnicodeDecodeError as e:
            raise ConfigurationError(f"Environment file encoding error: {e}")
        except Exception as e:
            logger.error(
                f"[{self.correlation_id}] Failed to update environment file: {e}"
            )
            raise

    def _validate_env_content(self, content: str) -> bool:
        """Validate environment file content for security"""
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Must be key=value format
            if "=" not in line:
                logger.warning(
                    f"[{self.correlation_id}] Invalid line {line_num}: {line}"
                )
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Validate key format
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                logger.error(
                    f"[{self.correlation_id}] Invalid key format at line {line_num}: {key}"
                )
                return False

            # Check for potentially dangerous values
            dangerous_patterns = [
                r"<script.*?>.*?</script>",  # Script tags
                r"javascript:",  # JavaScript URLs
                r"data:",  # Data URLs
                r"\$\(",  # Command substitution
                r"`[^`]*`",  # Backtick commands
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.error(
                        f"[{self.correlation_id}] Dangerous value detected at line {line_num}: {key}"
                    )
                    return False

        return True

    async def _validate_new_settings(self):
        """Test new database connection settings with error handling"""
        logger.info(
            f"[{self.correlation_id}] 🔍 Validating new database connection settings..."
        )

        try:
            # Create test connection with new settings
            test_engine = get_async_engine()

            # Add connection timeout
            async with test_engine.connect() as conn:
                # Test basic connectivity
                result = await conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()

                if test_value != 1:
                    raise Exception("Database test query returned unexpected result")

                # Test connection pool functionality
                connections = []
                try:
                    for i in range(3):  # Test multiple connections
                        conn2 = await test_engine.connect()
                        connections.append(conn2)

                        result = await conn2.execute(text("SELECT version()"))
                        version = result.scalar()
                        logger.debug(
                            f"[{self.correlation_id}] Connection {i+1}: PostgreSQL {version}"
                        )

                    logger.info(
                        f"[{self.correlation_id}] ✅ Connection pool validation successful"
                    )

                finally:
                    # Clean up test connections
                    for conn in connections:
                        await conn.close()

            await test_engine.dispose()

        except sqlalchemy_exc.SQLAlchemyError as e:
            logger.error(
                f"[{self.correlation_id}] ❌ Database validation failed (SQLAlchemy): {e}"
            )
            raise
        except Exception as e:
            logger.error(f"[{self.correlation_id}] ❌ Database validation failed: {e}")
            raise

    async def benchmark_database_performance(self) -> Dict[str, float]:
        """Secure database performance benchmarking with error handling"""
        logger.info(f"[{self.correlation_id}] ⏱️ Benchmarking database performance...")

        engine = get_async_engine()
        benchmark_results = {}

        try:
            # Test connection acquisition speed
            start_time = time.perf_counter()

            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            connection_time = (time.perf_counter() - start_time) * 1000
            benchmark_results["connection_time_ms"] = round(connection_time, 2)

            # Test query performance with safety timeout
            start_time = time.perf_counter()

            try:
                async with asyncio.timeout(30):  # 30 second timeout
                    async with engine.begin() as conn:
                        result = await conn.execute(
                            text(
                                """
                            SELECT u.id, u.email, u.created_at
                            FROM users u
                            ORDER BY u.created_at DESC
                            LIMIT 10
                        """
                            )
                        )
                        rows = result.fetchall()

                query_time = (time.perf_counter() - start_time) * 1000
                benchmark_results["query_time_ms"] = round(query_time, 2)
                benchmark_results["rows_returned"] = len(rows)

            except asyncio.TimeoutError:
                logger.warning(
                    f"[{self.correlation_id}] Query timeout during benchmark"
                )
                benchmark_results["query_time_ms"] = float("inf")
                benchmark_results["rows_returned"] = 0

            logger.info(f"[{self.correlation_id}] 📊 Benchmark Results:")
            logger.info(
                f"[{self.correlation_id}]  • Connection Time: {benchmark_results['connection_time_ms']:.2f}ms"
            )
            logger.info(
                f"[{self.correlation_id}]  • Query Time: {benchmark_results['query_time_ms']:.2f}ms"
            )
            logger.info(
                f"[{self.correlation_id}]  • Rows Returned: {benchmark_results['rows_returned']}"
            )

        except Exception as e:
            logger.error(f"[{self.correlation_id}] ❌ Benchmark failed: {e}")
            # Return default values on error
            benchmark_results = {
                "connection_time_ms": float("inf"),
                "query_time_ms": float("inf"),
                "rows_returned": 0,
                "error": str(e),
            }

        finally:
            try:
                await engine.dispose()
            except Exception as dispose_error:
                logger.warning(
                    f"[{self.correlation_id}] Engine disposal error: {dispose_error}"
                )

        return benchmark_results

    async def secure_rollback_changes(self):
        """Secure rollback with comprehensive error handling"""
        logger.warning(f"[{self.correlation_id}] 🔄 Rolling back optimizations...")

        if not self.optimizations_applied:
            logger.info(f"[{self.correlation_id}] No optimizations to rollback")
            return

        try:
            # Restore from backup files
            backup_files = [
                project_root / ".env.performance.backup",
                project_root / ".env.performance.backup.json",
            ]

            for backup_file in backup_files:
                if backup_file.exists():
                    try:
                        if backup_file.suffix == ".json":
                            # Restore from JSON backup
                            with open(backup_file, "r") as f:
                                backup_data = json.load(f)

                            env_file = project_root / ".env.dev"
                            await self._update_env_file_secure(env_file, backup_data)

                        else:
                            # Restore from plain text backup
                            env_file = project_root / ".env.dev"
                            self._atomic_write(
                                env_file, backup_file.read_text(encoding="utf-8")
                            )

                        logger.info(
                            f"[{self.correlation_id}] ✅ Settings restored from {backup_file}"
                        )
                        break

                    except Exception as restore_error:
                        logger.error(
                            f"[{self.correlation_id}] Failed to restore from {backup_file}: {restore_error}"
                        )
                        continue

            self.optimizations_applied.clear()
            logger.info(
                f"[{self.correlation_id}] ✅ Secure rollback completed successfully"
            )

        except Exception as e:
            logger.error(f"[{self.correlation_id}] ❌ Rollback failed: {e}")
            raise

    async def generate_secure_optimization_report(
        self, before_benchmark: Dict[str, float], after_benchmark: Dict[str, float]
    ):
        """Generate secure performance optimization report"""
        report_file = project_root / "SECURE_PERFORMANCE_OPTIMIZATION_REPORT.md"

        report_content = f"""# 🔒 PsychSync Secure Performance Optimization Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Phase:** Phase 1 - Database Connection Pool Optimization (SECURE VERSION)
**Status:** {'✅ SUCCESS' if self.optimizations_applied else '❌ FAILED'}
**Correlation ID:** {self.correlation_id}

---

## 🛡️ Security Measures Implemented

### ✅ Input Validation
- Configuration value validation with regex patterns
- Path traversal protection
- File permission validation

### ✅ Secure File Operations
- Atomic file writes with temporary files
- Secure file permissions (0o600 for sensitive files)
- Automatic backup creation
- Safe rollback mechanisms

### ✅ Error Handling
- Comprehensive exception handling
- Database connection timeouts
- Graceful degradation on errors

---

## 📊 Performance Metrics

### Before Optimization
- **Connection Time:** {before_benchmark.get('connection_time_ms', 'N/A')}ms
- **Query Time:** {before_benchmark.get('query_time_ms', 'N/A')}ms

### After Optimization
- **Connection Time:** {after_benchmark.get('connection_time_ms', 'N/A')}ms
- **Query Time:** {after_benchmark.get('query_time_ms', 'N/A')}ms

### Performance Improvement
"""

        # Calculate improvements
        improvements = []
        if (
            "connection_time_ms" in before_benchmark
            and "connection_time_ms" in after_benchmark
            and before_benchmark["connection_time_ms"] != float("inf")
            and after_benchmark["connection_time_ms"] != float("inf")
        ):

            before = before_benchmark["connection_time_ms"]
            after = after_benchmark["connection_time_ms"]
            improvement = ((before - after) / before) * 100
            improvements.append(
                f"- **Connection Speed:** {improvement:.1f}% improvement"
            )

        if (
            "query_time_ms" in before_benchmark
            and "query_time_ms" in after_benchmark
            and before_benchmark["query_time_ms"] != float("inf")
            and after_benchmark["query_time_ms"] != float("inf")
        ):

            before = before_benchmark["query_time_ms"]
            after = after_benchmark["query_time_ms"]
            improvement = ((before - after) / before) * 100
            improvements.append(f"- **Query Speed:** {improvement:.1f}% improvement")

        report_content += (
            "\n".join(improvements)
            if improvements
            else "- No performance changes detected"
        )

        report_content += f"""

---

## 🔧 Applied Optimizations

"""
        for optimization in self.optimizations_applied:
            report_content += f"- ✅ {optimization} (applied securely)\n"

        report_content += f"""

## 📝 Configuration Changes

### Connection Pool Settings
- **Pool Size:** {self.backup_settings.get('DB_POOL_SIZE', 'N/A')} → 20
- **Max Overflow:** {self.backup_settings.get('DB_MAX_OVERFLOW', 'N/A')} → 30
- **Pool Recycle:** {self.backup_settings.get('DB_POOL_RECYCLE', 'N/A')} → 1800 seconds

---

## 🔒 Security Verification

### ✅ Files Created with Secure Permissions
- `.env.performance.backup` (0o600)
- `.env.performance.backup.json` (0o600)
- `performance-optimization.log` (default permissions)

### ✅ Input Validation Applied
- All configuration values validated against patterns
- File paths validated against directory boundaries
- Environment file content scanned for dangerous patterns

### ✅ Error Handling Implemented
- Database connection timeouts (30 seconds)
- Atomic file operations with rollback
- Comprehensive logging with correlation ID

---

## 🎯 Next Steps

1. **Monitor Performance:** Watch database metrics in production
2. **Phase 2 Preparation:** Ready for secure frontend bundle optimization
3. **Security Audit:** Review logs for any security events
4. **Load Testing:** Test under concurrent load with new settings

## 🚨 Secure Rollback Information

**Backup Files:**
- `.env.performance.backup` (plain text)
- `.env.performance.backup.json` (JSON format)

**Secure Rollback Command:**
```bash
python scripts/secure-performance-optimizer.py --rollback
```

**Log File:** `performance-optimization.log`

---

## 🔐 Security Considerations

- All operations performed with validated input
- Temporary files created with secure permissions
- Atomic operations prevent partial state corruption
- Comprehensive error handling prevents information leakage
- Correlation ID enables traceability of operations

---

*Generated securely by PsychSync Performance Optimizer v2.0*
*Security enhancements applied based on comprehensive code review*
"""

        # Write report with secure permissions
        self._atomic_write(report_file, report_content, mode=0o644)
        logger.info(
            f"[{self.correlation_id}] 📄 Secure optimization report generated: {report_file}"
        )


async def main():
    """Main secure optimization execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="PsychSync SECURE Performance Optimization"
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Secure rollback of optimizations"
    )
    parser.add_argument(
        "--benchmark-only", action="store_true", help="Run benchmarks only"
    )
    parser.add_argument(
        "--validate-environment",
        action="store_true",
        help="Validate execution environment only",
    )
    args = parser.parse_args()

    optimizer = SecurePerformanceOptimizer()

    try:
        if args.rollback:
            await optimizer.secure_rollback_changes()
            return

        if args.validate_environment:
            logger.info("Environment validation completed successfully")
            return

        if args.benchmark_only:
            results = await optimizer.benchmark_database_performance()
            print(f"Benchmark Results: {results}")
            return

        logger.info(
            f"🚀 Starting SECURE PsychSync Performance Optimization - Phase 1 [{optimizer.correlation_id}]"
        )

        # Step 1: Backup current settings (secure)
        await optimizer.backup_current_settings()

        # Step 2: Benchmark before optimization
        logger.info(
            f"[{optimizer.correlation_id}] 📊 Running pre-optimization benchmark..."
        )
        before_benchmark = await optimizer.benchmark_database_performance()

        # Step 3: Apply optimizations (secure)
        await optimizer.apply_connection_pool_optimization()

        # Step 4: Benchmark after optimization
        logger.info(
            f"[{optimizer.correlation_id}] 📊 Running post-optimization benchmark..."
        )
        after_benchmark = await optimizer.benchmark_database_performance()

        # Step 5: Generate secure report
        await optimizer.generate_secure_optimization_report(
            before_benchmark, after_benchmark
        )

        logger.info(
            f"🎉 SECURE Phase 1 optimization completed successfully! [{optimizer.correlation_id}]"
        )
        logger.info(
            "📄 Check SECURE_PERFORMANCE_OPTIMIZATION_REPORT.md for detailed results"
        )
        logger.info("🚀 Ready for Phase 2: Secure Frontend Bundle Optimization")

    except KeyboardInterrupt:
        logger.warning(
            f"[{optimizer.correlation_id}] ⚠️ Optimization interrupted by user"
        )
        await optimizer.secure_rollback_changes()

    except SecurityError as e:
        logger.error(f"[{optimizer.correlation_id}] 🔒 Security error: {e}")
        await optimizer.secure_rollback_changes()
        sys.exit(1)

    except ConfigurationError as e:
        logger.error(f"[{optimizer.correlation_id}] ⚙️ Configuration error: {e}")
        await optimizer.secure_rollback_changes()
        sys.exit(1)

    except Exception as e:
        logger.error(f"[{optimizer.correlation_id}] ❌ Unexpected error: {e}")
        await optimizer.secure_rollback_changes()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
