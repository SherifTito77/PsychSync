"""
Unified AI Security Wrapper

Provides a simple, unified interface for securing AI/ML operations.
Wraps all AI security controls (input validation, PII redaction, output
sanitization, monitoring) into an easy-to-use decorator and context manager.

Author: Security Team
Version: 1.0
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional, Tuple
from contextlib import contextmanager

from ai.security.ai_input_validator import validate_ai_input, ValidationSeverity
from ai.security.pii_redaction import redact_pii, assess_privacy_risk
from ai.security.ai_output_sanitizer import sanitize_ai_output, OutputType
from ai.security.ai_security_monitoring import (
    log_ai_security_event,
    SecurityEventType,
    SecurityEventSeverity
)

logger = logging.getLogger("app.ai.security.wrapper")


class AISecurityError(Exception):
    """Raised when AI security check fails"""
    pass


def secure_ai_processing(
    input_type: str = 'text_input',
    output_type: OutputType = OutputType.TEXT,
    redact_pii: bool = True,
    sanitize_output: bool = True,
    allow_html_output: bool = False,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    Decorator to secure AI processing functions

    Automatically applies:
    - Input validation and sanitization
    - PII/PHI redaction
    - Output sanitization
    - Security event logging

    Usage:
        @secure_ai_processing(
            input_type='personality_response',
            output_type=OutputType.ANALYSIS,
            redact_pii=True
        )
        def process_personality_assessment(user_input):
            # Process user_input (already validated and redacted)
            result = ai_model.analyze(user_input)
            return result  # Will be sanitized automatically
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                # Extract input from arguments (assume first arg is the input)
                if not args:
                    raise AISecurityError("No input provided to AI function")

                user_input = args[0]

                # Step 1: Validate input
                validation_result = validate_ai_input(
                    user_input,
                    input_type=input_type,
                    sanitize=True
                )

                if not validation_result.is_valid:
                    # Log security event
                    log_ai_security_event(
                        event_type=SecurityEventType.INPUT_VALIDATION_FAILED,
                        severity=SecurityEventSeverity.HIGH,
                        details={
                            "issues": validation_result.issues,
                            "severity": validation_result.severity.value
                        },
                        user_id=user_id,
                        session_id=session_id,
                        ip_address=ip_address
                    )

                    if validation_result.severity == ValidationSeverity.CRITICAL:
                        raise AISecurityError(
                            f"Input validation failed: {validation_result.issues}"
                        )

                # Use validated input
                validated_input = validation_result.sanitized_input

                # Step 2: Redact PII if enabled
                if redact_pii and isinstance(validated_input, str):
                    redaction_result = redact_pii(validated_input)
                    if redaction_result.findings:
                        log_ai_security_event(
                            event_type=SecurityEventType.PII_DETECTED,
                            severity=SecurityEventSeverity.MEDIUM,
                            details={
                                "num_findings": len(redaction_result.findings),
                                "risk_score": redaction_result.risk_score
                            },
                            user_id=user_id,
                            session_id=session_id,
                            ip_address=ip_address
                        )

                    validated_input = redaction_result.redacted_text

                # Step 3: Call the AI function with secured input
                result = func(validated_input, *args[1:], **kwargs)

                # Step 4: Sanitize output if enabled
                if sanitize_output:
                    sanitization_result = sanitize_ai_output(
                        result,
                        output_type=output_type,
                        allow_html=allow_html_output,
                        strip_html=True
                    )

                    if sanitization_result.blocked:
                        log_ai_security_event(
                            event_type=SecurityEventType.OUTPUT_BLOCKED,
                            severity=SecurityEventSeverity.CRITICAL,
                            details={"reason": sanitization_result.reason},
                            user_id=user_id,
                            session_id=session_id,
                            ip_address=ip_address
                        )
                        raise AISecurityError(
                            f"Output blocked: {sanitization_result.reason}"
                        )

                    if sanitization_result.warnings:
                        log_ai_security_event(
                            event_type=SecurityEventType.DANGEROUS_OUTPUT_DETECTED,
                            severity=SecurityEventSeverity.MEDIUM,
                            details={"warnings": sanitization_result.warnings},
                            user_id=user_id,
                            session_id=session_id,
                            ip_address=ip_address
                        )

                    result = sanitization_result.sanitized_output

                return result

            except AISecurityError:
                raise
            except Exception as e:
                logger.error(
                    f"Error in secure AI processing wrapper: {str(e)}",
                    extra={"event_type": "ai_wrapper_error"},
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


@contextmanager
def secure_ai_context(
    input_type: str = 'text_input',
    output_type: OutputType = OutputType.TEXT,
    redact_pii: bool = True,
    sanitize_output: bool = True,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Context manager for securing AI processing

    Usage:
        with secure_ai_context(
            input_type='clinical_note',
            redact_pii=True,
            user_id=user.id
        ) as security:
            # Validate and redact input
            secured_input = security.validate_input(clinical_note)

            # Process with AI
            result = ai_model.analyze(secured_input)

            # Sanitize output
            safe_result = security.sanitize_output(result)
    """

    class SecurityContext:
        def __init__(self):
            self.validation_result = None
            self.redaction_result = None
            self.sanitization_result = None

        def validate_input(self, user_input: Any) -> Any:
            """Validate and sanitize user input"""
            self.validation_result = validate_ai_input(
                user_input,
                input_type=input_type,
                sanitize=True
            )

            if not self.validation_result.is_valid:
                log_ai_security_event(
                    event_type=SecurityEventType.INPUT_VALIDATION_FAILED,
                    severity=SecurityEventSeverity.HIGH,
                    details={
                        "issues": self.validation_result.issues,
                        "severity": self.validation_result.severity.value
                    },
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address
                )

            return self.validation_result.sanitized_input

        def redact_input(self, user_input: str) -> str:
            """Redact PII from input"""
            self.redaction_result = redact_pii(user_input)

            if self.redaction_result.findings:
                log_ai_security_event(
                    event_type=SecurityEventType.PII_DETECTED,
                    severity=SecurityEventSeverity.MEDIUM,
                    details={
                        "num_findings": len(self.redaction_result.findings),
                        "risk_score": self.redaction_result.risk_score
                    },
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address
                )

            return self.redaction_result.redacted_text

        def sanitize_output(self, output: Any) -> Any:
            """Sanitize AI output"""
            self.sanitization_result = sanitize_ai_output(
                output,
                output_type=output_type,
                strip_html=True
            )

            if self.sanitization_result.blocked:
                log_ai_security_event(
                    event_type=SecurityEventType.OUTPUT_BLOCKED,
                    severity=SecurityEventSeverity.CRITICAL,
                    details={"reason": self.sanitization_result.reason},
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address
                )
                raise AISecurityError(
                    f"Output blocked: {self.sanitization_result.reason}"
                )

            return self.sanitization_result.sanitized_output

    context = SecurityContext()

    try:
        yield context
    except Exception as e:
        logger.error(
            f"Error in secure AI context: {str(e)}",
            extra={"event_type": "ai_context_error"},
            exc_info=True
        )
        raise


def assess_input_security(input_data: Any, input_type: str = 'text_input') -> Dict[str, Any]:
    """
    Assess the security posture of input data

    Returns comprehensive security assessment including:
    - Validation status
    - PII risk score
    - Recommendations

    Usage:
        assessment = assess_input_security(user_input, 'personality_response')
        if assessment['risk_score'] > 0.5:
            logger.warning(f"High risk input: {assessment['recommendations']}")
    """
    try:
        # Validate input
        validation_result = validate_ai_input(input_data, input_type, sanitize=False)

        # Assess PII risk
        if isinstance(input_data, str):
            privacy_risk = assess_privacy_risk(input_data)
        else:
            privacy_risk = {"risk_score": 0.0, "num_findings": 0}

        # Calculate overall risk score
        validation_risk = 0.0 if validation_result.is_valid else 0.5
        privacy_risk_score = privacy_risk.get("risk_score", 0.0)

        overall_risk = max(validation_risk, privacy_risk_score)

        # Generate recommendations
        recommendations = []
        if not validation_result.is_valid:
            recommendations.append("Input contains invalid or potentially malicious content")
            recommendations.extend(validation_result.issues)

        if privacy_risk.get("num_findings", 0) > 0:
            recommendations.append("Input contains PII/PHI - should be redacted before processing")
            recommendations.append(privacy_risk.get("recommendation", ""))

        if overall_risk < 0.2:
            recommendations.append("Input appears safe for processing")
        elif overall_risk < 0.5:
            recommendations.append("Input has moderate risk - consider additional validation")
        else:
            recommendations.append("Input has high risk - additional safeguards required")

        return {
            "overall_risk_score": overall_risk,
            "validation_passed": validation_result.is_valid,
            "privacy_risk_score": privacy_risk_score,
            "pii_findings": privacy_risk.get("num_findings", 0),
            "recommendations": recommendations,
            "safe_to_process": overall_risk < 0.5
        }

    except Exception as e:
        logger.error(
            f"Error assessing input security: {str(e)}",
            exc_info=True
        )
        return {
            "overall_risk_score": 1.0,  # Assume high risk on error
            "validation_passed": False,
            "privacy_risk_score": 0.0,
            "pii_findings": 0,
            "recommendations": [f"Error assessing security: {str(e)}"],
            "safe_to_process": False
        }


__all__ = [
    'AISecurityError',
    'secure_ai_processing',
    'secure_ai_context',
    'assess_input_security'
]
