"""
Security Logging Configuration

Example configuration for enabling and customizing security logging.

Usage:
    from app.security.logging import security_logger
    from app.security.logging.config import configure_security_logging

    # Configure with defaults
    configure_security_logging()

    # Or configure with custom settings
    configure_security_logging(
        enable_siem=True,
        siem_configs=[...]
    )
"""


from app.security.logging import SecurityLogger
from app.security.logging.detection import SecurityEventDetector
from app.security.logging.integrity import LogIntegrityManager
from app.security.logging.redaction import DataRedactor
from app.security.logging.siem import SIEMConfig, SIEMStreamer, SIEMType


def configure_security_logging(
    enable_redaction: bool = True,
    enable_integrity: bool = True,
    enable_siem: bool = False,
    enable_detection: bool = True,
    siem_configs: list[SIEMConfig] | None = None,
    staging_dir: str | None = None,
    production_dir: str | None = None
) -> SecurityLogger:
    """
    Configure and initialize security logging system.

    Args:
        enable_redaction: Enable automatic PII/sensitive data redaction
        enable_integrity: Enable hash-chain log integrity
        enable_siem: Enable SIEM streaming
        enable_detection: Enable threat detection rules
        siem_configs: List of SIEM configurations
        staging_dir: Directory for write-ahead logs
        production_dir: Directory for production logs

    Returns:
        Configured SecurityLogger instance
    """

    # Initialize components
    redactor = DataRedactor(
        redact_email=True,
        redact_phone=True,
        redact_ssn=True,
        redact_credit_card=True,
        redact_api_keys=True,
        redact_jwt=True,
        redact_ip=False,  # Keep IPs for security analysis
        redact_uuid=False,  # Keep UUIDs for tracing
        hash_mode=False  # Set to True to hash instead of redact
    ) if enable_redaction else None

    integrity_manager = LogIntegrityManager(
        staging_dir=staging_dir or "/tmp/security_logs_staging",
        production_dir=production_dir or "/var/log/security_logs",
        hash_algorithm="sha256",
        checkpoint_interval=1000,
        enable_write_ahead=True,
        enable_signing=False,  # Enable with signing_key_path for cryptographic signatures
    ) if enable_integrity else None

    siem_streamer = SIEMStreamer() if enable_siem else None
    if siem_streamer and siem_configs:
        for config in siem_configs:
            siem_streamer.add_config(config)

    detector = SecurityEventDetector() if enable_detection else None

    # Create logger
    logger = SecurityLogger(
        redactor=redactor,
        integrity_manager=integrity_manager,
        siem_streamer=siem_streamer,
        detector=detector,
        enable_redaction=enable_redaction,
        enable_integrity=enable_integrity,
        enable_siem=enable_siem,
        enable_detection=enable_detection
    )

    return logger


def create_splunk_config(
    hec_url: str,
    hec_token: str,
    index: str = "security_logs"
) -> SIEMConfig:
    """Create Splunk HTTP Event Collector configuration"""
    return SIEMConfig(
        siem_type=SIEMType.SPLUNK,
        enabled=True,
        endpoint_url=hec_url,
        api_token=hec_token,
        index=index,
        batch_size=100,
        batch_timeout_seconds=10,
        max_retries=3,
        verify_ssl=True
    )


def create_elasticsearch_config(
    endpoint_url: str = "http://localhost:9200",
    index: str = "security_logs"
) -> SIEMConfig:
    """Create Elasticsearch configuration"""
    return SIEMConfig(
        siem_type=SIEMType.ELASTICSEARCH,
        enabled=True,
        endpoint_url=endpoint_url,
        index=index,
        batch_size=100,
        batch_timeout_seconds=10,
        max_retries=3,
        verify_ssl=True
    )


def create_azure_sentinel_config(
    workspace_id: str,
    shared_key: str,
    log_type: str = "SecurityLogs"
) -> SIEMConfig:
    """Create Microsoft Azure Sentinel configuration"""
    return SIEMConfig(
        siem_type=SIEMType.AZURE_SENTINEL,
        enabled=True,
        endpoint_url=workspace_id,
        api_token=shared_key,
        index=log_type,
        batch_size=100,
        batch_timeout_seconds=10,
        max_retries=3,
        verify_ssl=True
    )


def create_datadog_config(
    api_key: str
) -> SIEMConfig:
    """Create Datadog configuration"""
    return SIEMConfig(
        siem_type=SIEMType.DATADOG,
        enabled=True,
        api_token=api_key,
        batch_size=100,
        batch_timeout_seconds=10,
        max_retries=3,
        verify_ssl=True
    )


# Example configurations
EXAMPLE_SPLUNK_CONFIG = create_splunk_config(
    hec_url="https://splunk.example.com:8088/services/collector/event",
    hec_token=os.getenv("SPLUNK_TOKEN"),
    index="psychsync_security"
)

EXAMPLE_ELASTICSEARCH_CONFIG = create_elasticsearch_config(
    endpoint_url="http://elasticsearch.example.com:9200",
    index="psychsync-security-logs"
)

EXAMPLE_DATADOG_CONFIG = create_datadog_config(
    api_key=os.getenv("DATADOG_KEY")
)


def get_example_configuration() -> dict:
    """Get example full configuration"""
    return {
        "enable_redaction": True,
        "enable_integrity": True,
        "enable_siem": True,
        "enable_detection": True,

        "redaction_settings": {
            "redact_email": True,
            "redact_phone": True,
            "redact_ssn": True,
            "redact_credit_card": True,
            "redact_api_keys": True,
            "redact_jwt": True,
            "redact_ip": False,  # Keep for security analysis
            "redact_uuid": False,  # Keep for tracing
            "hash_mode": False  # Set True to hash instead of redact
        },

        "integrity_settings": {
            "staging_dir": "/var/log/security_logs_staging",
            "production_dir": "/var/log/security_logs",
            "hash_algorithm": "sha256",
            "checkpoint_interval": 1000,
            "enable_write_ahead": True,
            "enable_signing": False,
            "signing_key_path": None
        },

        "siem_configs": [
            {
                "type": "splunk",
                "enabled": True,
                "endpoint_url": "https://splunk.example.com:8088/services/collector/event",
                "api_token": os.getenv("SPLUNK_TOKEN"),
                "index": "psychsync_security",
                "batch_size": 100,
                "batch_timeout_seconds": 10
            },
            {
                "type": "elasticsearch",
                "enabled": True,
                "endpoint_url": "http://elasticsearch.example.com:9200",
                "index": "psychsync-security-logs",
                "batch_size": 100,
                "batch_timeout_seconds": 10
            }
        ],

        "detection_settings": {
            "enable_pattern_detection": True,
            "enable_behavioral_detection": True,
            "enable_injection_detection": True,
            "enable_tool_anomaly_detection": True,
            "event_history_hours": 24
        }
    }


def configure_from_environment():
    """
    Configure security logging from environment variables.

    Environment Variables:
        SECURITY_LOGGING_ENABLED: Enable/disable security logging (default: true)
        SECURITY_LOGGING_REDACT: Enable redaction (default: true)
        SECURITY_LOGGING_INTEGRITY: Enable integrity checks (default: true)
        SECURITY_LOGGING_SIEM: Enable SIEM streaming (default: false)

        SIEM_SPLUNK_ENABLED: Enable Splunk (default: false)
        SIEM_SPLUNK_URL: Splunk HEC URL
        SIEM_SPLUNK_TOKEN: Splunk HEC token
        SIEM_SPLUNK_INDEX: Splunk index name (default: security_logs)

        SIEM_ELASTICSEARCH_ENABLED: Enable Elasticsearch (default: false)
        SIEM_ELASTICSEARCH_URL: Elasticsearch URL (default: http://localhost:9200)
        SIEM_ELASTICSEARCH_INDEX: Index name (default: security_logs)

        SIEM_DATADOG_ENABLED: Enable Datadog (default: false)
        SIEM_DATADOG_API_KEY: Datadog API key
    """
    import os

    # Main settings
    enabled = os.getenv("SECURITY_LOGGING_ENABLED", "true").lower() == "true"
    enable_redaction = os.getenv("SECURITY_LOGGING_REDACT", "true").lower() == "true"
    enable_integrity = os.getenv("SECURITY_LOGGING_INTEGRITY", "true").lower() == "true"
    enable_siem = os.getenv("SECURITY_LOGGING_SIEM", "false").lower() == "true"

    if not enabled:
        return SecurityLogger(
            enable_redaction=False,
            enable_integrity=False,
            enable_siem=False,
            enable_detection=False
        )

    # SIEM configurations
    siem_configs = []

    # Splunk
    if os.getenv("SIEM_SPLUNK_ENABLED", "false").lower() == "true":
        siem_configs.append(SIEMConfig(
            siem_type=SIEMType.SPLUNK,
            enabled=True,
            endpoint_url=os.getenv("SIEM_SPLUNK_URL", "https://localhost:8088/services/collector/event"),
            api_token=os.getenv("SIEM_SPLUNK_TOKEN", ""),
            index=os.getenv("SIEM_SPLUNK_INDEX", "security_logs")
        ))

    # Elasticsearch
    if os.getenv("SIEM_ELASTICSEARCH_ENABLED", "false").lower() == "true":
        siem_configs.append(SIEMConfig(
            siem_type=SIEMType.ELASTICSEARCH,
            enabled=True,
            endpoint_url=os.getenv("SIEM_ELASTICSEARCH_URL", "http://localhost:9200"),
            index=os.getenv("SIEM_ELASTICSEARCH_INDEX", "security_logs")
        ))

    # Datadog
    if os.getenv("SIEM_DATADOG_ENABLED", "false").lower() == "true":
        siem_configs.append(SIEMConfig(
            siem_type=SIEMType.DATADOG,
            enabled=True,
            api_token=os.getenv("SIEM_DATADOG_API_KEY", "")
        ))

    # Configure logger
    return configure_security_logging(
        enable_redaction=enable_redaction,
        enable_integrity=enable_integrity,
        enable_siem=enable_siem and siem_configs,
        enable_detection=True,
        siem_configs=siem_configs if enable_siem else None
    )
