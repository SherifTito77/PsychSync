"""
AI Security Framework

Comprehensive security suite for AI/ML systems including:
- Input validation and sanitization
- Prompt injection detection
- PII/PHI redaction
- Output sanitization
- Security monitoring and SOC integration

Author: Security Team
Version: 1.0
"""

from app.ai.security.ai_input_validator import (
    AIInputValidator,
    ValidationResult,
    ValidationSeverity,
    ai_input_validator,
    validate_ai_input,
)
from app.ai.security.ai_output_sanitizer import (
    AIOutputSanitizer,
    OutputType,
    SanitizationResult,
    ai_output_sanitizer,
    sanitize_ai_output,
)
from app.ai.security.ai_security_monitoring import (
    AISecurityMonitor,
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
    ai_security_monitor,
    get_security_summary,
    log_ai_security_event,
)
from app.ai.security.pii_redaction import (
    PIICategory,
    PIIRedactor,
    RedactionResult,
    assess_privacy_risk,
    pii_redactor,
    redact_pii,
)

__all__ = [
    # Input Validator
    "AIInputValidator",
    "ValidationResult",
    "ValidationSeverity",
    "ai_input_validator",
    "validate_ai_input",
    # PII Redaction
    "PIIRedactor",
    "RedactionResult",
    "PIICategory",
    "pii_redactor",
    "redact_pii",
    "assess_privacy_risk",
    # Output Sanitizer
    "AIOutputSanitizer",
    "SanitizationResult",
    "OutputType",
    "ai_output_sanitizer",
    "sanitize_ai_output",
    # Security Monitoring
    "AISecurityMonitor",
    "SecurityEvent",
    "SecurityEventSeverity",
    "SecurityEventType",
    "ai_security_monitor",
    "log_ai_security_event",
    "get_security_summary",
]
