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

from ai.security.ai_input_validator import (
    AIInputValidator,
    ValidationResult,
    ValidationSeverity,
    ai_input_validator,
    validate_ai_input
)

from ai.security.pii_redaction import (
    PIIRedactor,
    RedactionResult,
    PIICategory,
    pii_redactor,
    redact_pii,
    assess_privacy_risk
)

from ai.security.ai_output_sanitizer import (
    AIOutputSanitizer,
    SanitizationResult,
    OutputType,
    ai_output_sanitizer,
    sanitize_ai_output
)

from ai.security.ai_security_monitoring import (
    AISecurityMonitor,
    SecurityEvent,
    SecurityEventSeverity,
    SecurityEventType,
    ai_security_monitor,
    log_ai_security_event,
    get_security_summary
)

__all__ = [
    # Input Validator
    'AIInputValidator',
    'ValidationResult',
    'ValidationSeverity',
    'ai_input_validator',
    'validate_ai_input',

    # PII Redaction
    'PIIRedactor',
    'RedactionResult',
    'PIICategory',
    'pii_redactor',
    'redact_pii',
    'assess_privacy_risk',

    # Output Sanitizer
    'AIOutputSanitizer',
    'SanitizationResult',
    'OutputType',
    'ai_output_sanitizer',
    'sanitize_ai_output',

    # Security Monitoring
    'AISecurityMonitor',
    'SecurityEvent',
    'SecurityEventSeverity',
    'SecurityEventType',
    'ai_security_monitor',
    'log_ai_security_event',
    'get_security_summary',
]
