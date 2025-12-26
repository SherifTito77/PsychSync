"""
AI Input Sanitization and Validation Framework

Provides comprehensive input validation and sanitization for all AI/ML components
to prevent prompt injection, data poisoning, and adversarial input attacks.

Author: Security Team
Version: 1.0
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("app.ai.security.input_validation")


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: Any
    issues: List[str]
    severity: ValidationSeverity
    metadata: Dict[str, Any]


class AIInputValidator:
    """
    Comprehensive input validation and sanitization for AI/ML systems

    Features:
    - Prompt injection detection
    - Data sanitization
    - Length and character validation
    - Malicious pattern detection
    - Context boundary enforcement
    """

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'disregard\s+(all\s+)?previous\s+(instructions|commands)',
        r'forget\s+(all\s+)?previous',
        r'override\s+(your\s+)?programming',
        r'bypass\s+(security|restrictions|filters)',
        r'act\s+as\s+(a\s+)?(different|new)',
        r'pretend\s+(to\s+be)?',
        r'roleplay\s+as',
        r'simulate\s+(a\s+)?',
        r'you\s+are\s+now',
        r'system\s*:\s*ignore',
        r'developer\s*:\s*ignore',
        r'<\|.*?\|>',  # Special token patterns
        r'!!!',  # Attention grabbers
        r'###\s*INSTRUCTION',
        r'---\s*INSTRUCTION',
        r'<<<\s*INSTRUCTION',
    ]

    # Malicious patterns
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript\s*:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>',  # Iframes
        r'<object[^>]*>',  # Objects
        r'<embed[^>]*>',  # Embeds
        r'data:text/html',  # Data URLs
        r'eval\s*\(',  # Eval functions
        r'document\.',  # Document access
        r'window\.',  # Window access
    ]

    # Character limits for different input types
    MAX_LENGTHS = {
        'text_input': 10000,
        'personality_response': 5000,
        'clinical_note': 50000,
        'user_context': 2000,
        'prompt': 5000,
        'assessment_answer': 1000,
    }

    # Allowed character sets
    ALLOWED_CHARS = {
        'text': r'[\w\s\.\,\!\?\-\\\"\(\)\[\]\{\}\:\;\'\@\\\#\$\%\^\&\*\+\=\_\~\`]',
        'numeric': r'[\d\.\-]',
        'alpha': r'[a-zA-Z]',
        'alphanumeric': r'[a-zA-Z0-9]',
    }

    def __init__(self):
        """Initialize the validator with compiled regex patterns"""
        self.injection_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.PROMPT_INJECTION_PATTERNS
        ]
        self.malicious_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.MALICIOUS_PATTERNS
        ]

    def validate_input(
        self,
        input_data: Any,
        input_type: str = 'text_input',
        sanitize: bool = True
    ) -> ValidationResult:
        """
        Validate and optionally sanitize input data

        Args:
            input_data: The input to validate (string, dict, list)
            input_type: Type of input (determines validation rules)
            sanitize: Whether to sanitize the input

        Returns:
            ValidationResult with validation status and sanitized data
        """
        issues = []
        severity = ValidationSeverity.INFO
        sanitized = input_data

        try:
            # Convert to string for validation
            if isinstance(input_data, str):
                text_input = input_data
            elif isinstance(input_data, dict):
                # Recursively validate dictionary values
                sanitized = {}
                for key, value in input_data.items():
                    result = self.validate_input(value, input_type, sanitize)
                    if not result.is_valid:
                        issues.extend(result.issues)
                    sanitized[key] = result.sanitized_input
                text_input = str(input_data)
            elif isinstance(input_data, list):
                # Recursively validate list items
                sanitized = []
                for item in input_data:
                    result = self.validate_input(item, input_type, sanitize)
                    if not result.is_valid:
                        issues.extend(result.issues)
                    sanitized.append(result.sanitized_input)
                text_input = str(input_data)
            else:
                text_input = str(input_data)

            # Check length constraints
            max_length = self.MAX_LENGTHS.get(input_type, 10000)
            if len(text_input) > max_length:
                issues.append(f"Input exceeds maximum length of {max_length} characters")
                severity = ValidationSeverity.ERROR
                if sanitize:
                    if isinstance(sanitized, str):
                        sanitized = sanitized[:max_length]

            # Check for prompt injection
            injection_result = self._check_prompt_injection(text_input)
            if injection_result:
                issues.append(f"Potential prompt injection detected: {injection_result}")
                severity = ValidationSeverity.CRITICAL
                if sanitize:
                    sanitized = self._sanitize_injection_attempt(text_input)

            # Check for malicious patterns
            malicious_result = self._check_malicious_patterns(text_input)
            if malicious_result:
                issues.append(f"Malicious pattern detected: {malicious_result}")
                severity = ValidationSeverity.CRITICAL
                if sanitize:
                    sanitized = self._sanitize_malicious_content(text_input)

            # Check character set
            if input_type in self.ALLOWED_CHARS:
                char_result = self._check_characters(text_input, input_type)
                if char_result:
                    issues.append(f"Invalid characters detected: {char_result}")
                    if severity.value < ValidationSeverity.ERROR.value:
                        severity = ValidationSeverity.ERROR
                    if sanitize:
                        sanitized = self._sanitize_characters(text_input, input_type)

            # Check for context boundary violations
            context_result = self._check_context_boundaries(text_input)
            if context_result:
                issues.append(f"Context boundary violation: {context_result}")
                if severity.value < ValidationSeverity.WARNING.value:
                    severity = ValidationSeverity.WARNING

            is_valid = severity.value < ValidationSeverity.ERROR.value

            # Log validation results
            if not is_valid:
                logger.warning(
                    f"AI input validation failed: {input_type}",
                    extra={
                        "issues": issues,
                        "severity": severity.value,
                        "input_length": len(text_input),
                        "event_type": "ai_input_validation_failed"
                    }
                )
            else:
                logger.info(
                    f"AI input validation passed: {input_type}",
                    extra={
                        "input_length": len(text_input),
                        "event_type": "ai_input_validation_passed"
                    }
                )

            return ValidationResult(
                is_valid=is_valid,
                sanitized_input=sanitized,
                issues=issues,
                severity=severity,
                metadata={
                    "input_type": input_type,
                    "original_length": len(text_input) if isinstance(text_input, str) else 0,
                    "sanitized_length": len(sanitized) if isinstance(sanitized, str) else 0,
                }
            )

        except Exception as e:
            logger.error(
                f"Error during AI input validation: {str(e)}",
                extra={"event_type": "ai_input_validation_error"},
                exc_info=True
            )
            return ValidationResult(
                is_valid=False,
                sanitized_input=input_data,
                issues=[f"Validation error: {str(e)}"],
                severity=ValidationSeverity.ERROR,
                metadata={"error": str(e)}
            )

    def _check_prompt_injection(self, text: str) -> Optional[str]:
        """Check for prompt injection patterns"""
        for pattern in self.injection_patterns:
            match = pattern.search(text)
            if match:
                return f"Pattern: {match.group()[:50]}..."
        return None

    def _check_malicious_patterns(self, text: str) -> Optional[str]:
        """Check for malicious code patterns"""
        for pattern in self.malicious_patterns:
            match = pattern.search(text)
            if match:
                return f"Pattern: {match.group()[:50]}..."
        return None

    def _check_characters(self, text: str, char_type: str) -> Optional[str]:
        """Check for invalid characters"""
        if char_type not in self.ALLOWED_CHARS:
            return None

        allowed_pattern = self.ALLOWED_CHARS[char_type]
        # Find characters that don't match the allowed pattern
        invalid_chars = re.sub(allowed_pattern, '', text)
        if invalid_chars:
            # Get unique invalid characters
            unique_invalid = set(invalid_chars[:50])  # Limit to 50 for display
            return f"Invalid characters: {', '.join(unique_invalid)}"
        return None

    def _check_context_boundaries(self, text: str) -> Optional[str]:
        """Check for context boundary violations"""
        # Check for escape sequences
        escape_patterns = [
            r'\\[nrt]',
            r'\x00-\x1f',  # Control characters
        ]

        for pattern in escape_patterns:
            if re.search(pattern, text):
                return f"Contains control or escape characters"

        # Check for JSON/SQL injection attempts
        if '"}";' in text or "'); DROP" in text:
            return "Potential injection attempt detected"

        return None

    def _sanitize_injection_attempt(self, text: str) -> str:
        """Sanitize text with injection attempts"""
        # Remove suspicious patterns
        for pattern in self.injection_patterns:
            text = pattern.sub('[REDACTED]', text)

        # Limit repeated special characters
        text = re.sub(r'([!@#$%^&*])\1{3,}', r'\1', text)

        return text.strip()

    def _sanitize_malicious_content(self, text: str) -> str:
        """Sanitize malicious code patterns"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove JavaScript protocols
        text = re.sub(r'javascript\s*:', '[REDACTED]', text, flags=re.IGNORECASE)

        # Remove dangerous functions
        dangerous_funcs = ['eval', 'document', 'window']
        for func in dangerous_funcs:
            text = re.sub(rf'\b{func}\b', '[REDACTED]', text, flags=re.IGNORECASE)

        return text.strip()

    def _sanitize_characters(self, text: str, char_type: str) -> str:
        """Remove invalid characters"""
        if char_type not in self.ALLOWED_CHARS:
            return text

        allowed_pattern = self.ALLOWED_CHARS[char_type]
        # Keep only allowed characters
        sanitized = re.sub(allowed_pattern, '', text)

        # If we removed too much, return original with warning
        if len(sanitized) > len(text) / 2:
            return text  # Don't sanitize if it would remove too much

        return re.sub(allowed_pattern, '', text)


# Global validator instance
ai_input_validator = AIInputValidator()


def validate_ai_input(
    input_data: Any,
    input_type: str = 'text_input',
    sanitize: bool = True
) -> ValidationResult:
    """
    Convenience function to validate AI input

    Usage:
        result = validate_ai_input(user_input, 'personality_response')
        if result.is_valid:
            process_with_ai(result.sanitized_input)
    """
    return ai_input_validator.validate_input(input_data, input_type, sanitize)
