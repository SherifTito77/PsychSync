# app/core/logging_config.py
import logging
from pathlib import Path
import sys

from app.core.log_sanitizer import SensitiveDataFilter


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


def setup_logging():
    """Setup comprehensive logging configuration with sensitive data sanitization"""
    # Create logs directory if it doesn't exist (use local directory for development)
    log_dir = Path("./logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging format
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter(redaction_string="[REDACTED]")

    # Setup handlers
    handlers = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(sensitive_filter)  # Add sanitization to stdout
    handlers.append(stdout_handler)

    # Add file handler if log directory is writable
    try:
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)  # Add sanitization to file logs
        handlers.append(file_handler)
    except (OSError, PermissionError):
        # Fall back to current directory logging if /var/log is not writable
        try:
            fallback_handler = logging.FileHandler("app.log")
            fallback_handler.setFormatter(formatter)
            fallback_handler.addFilter(sensitive_filter)  # Add sanitization to fallback
            handlers.append(fallback_handler)
        except OSError:
            # Continue with just stdout logging
            pass

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # Override existing configuration
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)  # Suppress bcrypt warnings


# Create a logger for use throughout the application
logger = logging.getLogger(__name__)
