"""
AI Output Sanitization and Validation

Validates and sanitizes AI/ML model outputs before rendering or execution
to prevent injection attacks, XSS, and malicious content delivery.

Author: Security Team
Version: 1.0
"""

import html
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("app.ai.security.output_sanitization")


class OutputType(Enum):
    """Types of AI outputs"""

    TEXT = "text"
    HTML = "html"
    JSON = "json"
    CODE = "code"
    RECOMMENDATION = "recommendation"
    ANALYSIS = "analysis"
    CLINICAL_INSIGHT = "clinical_insight"


@dataclass
class SanitizationResult:
    """Result of output sanitization"""

    is_safe: bool
    sanitized_output: Any
    warnings: List[str]
    blocked: bool
    reason: Optional[str]


class AIOutputSanitizer:
    """
    Comprehensive AI output validation and sanitization

    Features:
    - XSS attack prevention
    - Injection attempt detection
    - Dangerous content filtering
    - Output format validation
    - Length and size limits
    - Malicious code detection
    """

    # Dangerous patterns to block in outputs
    DANGEROUS_PATTERNS = {
        "xss": [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ],
        "injection": [
            r"';?\s*DROP\s+TABLE",
            r"';?\s*DELETE\s+FROM",
            r"';?\s*INSERT\s+INTO",
            r"';?\s*UPDATE\s+\w+\s+SET",
            r"\$\{.*\}",  # Template injection
            r"{{.*}}",  # Another template syntax
        ],
        "path_traversal": [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e",
        ],
        "command_injection": [
            r";\s*(ls|cat|rm|cd|pwd|whoami)",
            r"\|\s*(ls|cat|rm|cd)",
            r"`[^`]*`",  # Backtick commands
        ],
    }

    # Maximum output sizes
    MAX_SIZES = {
        OutputType.TEXT: 50000,
        OutputType.HTML: 100000,
        OutputType.JSON: 50000,
        OutputType.CODE: 20000,
        OutputType.RECOMMENDATION: 10000,
        OutputType.ANALYSIS: 50000,
        OutputType.CLINICAL_INSIGHT: 20000,
    }

    # Allowed HTML tags (if HTML output is permitted)
    ALLOWED_HTML_TAGS = {
        "p",
        "br",
        "strong",
        "em",
        "u",
        "b",
        "i",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "div",
        "span",
        "table",
        "tr",
        "td",
        "th",
        "a",
        "img",
    }

    def __init__(self):
        """Initialize the sanitizer with compiled patterns"""
        self.compiled_patterns = {}
        for category, patterns in self.DANGEROUS_PATTERNS.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns
            ]

    def sanitize(
        self,
        output: Any,
        output_type: OutputType = OutputType.TEXT,
        allow_html: bool = False,
        strip_html: bool = True,
    ) -> SanitizationResult:
        """
        Sanitize AI output to ensure it's safe for rendering

        Args:
            output: The raw AI output to sanitize
            output_type: Type of output being sanitized
            allow_html: Whether HTML tags are permitted
            strip_html: Whether to strip all HTML tags

        Returns:
            SanitizationResult with safe output and any warnings
        """
        warnings = []
        blocked = False
        block_reason = None
        sanitized = output

        try:
            # Convert to string for validation
            if isinstance(output, str):
                text_output = output
            elif isinstance(output, dict):
                # Recursively sanitize dictionary values
                sanitized = {}
                for key, value in output.items():
                    result = self.sanitize(value, output_type, allow_html, strip_html)
                    if result.blocked:
                        return result
                    warnings.extend(result.warnings)
                    sanitized[key] = result.sanitized_output
                text_output = str(output)
            elif isinstance(output, list):
                # Recursively sanitize list items
                sanitized = []
                for item in output:
                    result = self.sanitize(item, output_type, allow_html, strip_html)
                    if result.blocked:
                        return result
                    warnings.extend(result.warnings)
                    sanitized.append(result.sanitized_output)
                text_output = str(output)
            else:
                text_output = str(output)
                sanitized = text_output

            # Check size limits
            max_size = self.MAX_SIZES.get(output_type, 50000)
            if len(text_output) > max_size:
                warnings.append(f"Output exceeds maximum size of {max_size} characters")
                if isinstance(sanitized, str):
                    sanitized = sanitized[:max_size] + "... [truncated]"

            # Check for dangerous patterns
            dangerous_found = self._check_dangerous_patterns(text_output)
            if dangerous_found:
                blocked = True
                block_reason = f"Dangerous content detected: {dangerous_found}"
                logger.error(
                    f"AI output blocked: {block_reason}",
                    extra={
                        "output_type": output_type.value,
                        "pattern": dangerous_found,
                        "event_type": "ai_output_blocked",
                    },
                )
                return SanitizationResult(
                    is_safe=False,
                    sanitized_output="[OUTPUT BLOCKED]",
                    warnings=warnings,
                    blocked=True,
                    reason=block_reason,
                )

            # HTML sanitization
            if strip_html and isinstance(sanitized, str):
                sanitized = self._strip_html(sanitized)
                if "<" in text_output or ">" in text_output:
                    warnings.append("HTML content has been stripped for security")

            elif not allow_html and isinstance(sanitized, str):
                # Escape HTML entities
                sanitized = html.escape(sanitized)

            # Validate JSON output
            if output_type == OutputType.JSON and isinstance(sanitized, str):
                try:
                    import json

                    json.loads(sanitized)  # Validate JSON syntax
                except json.JSONDecodeError as e:
                    warnings.append(f"Invalid JSON output: {str(e)}")

            # Check for leaked secrets/tokens
            if self._check_for_secrets(text_output):
                blocked = True
                block_reason = "Potential secret or token leak detected"
                logger.error(
                    f"AI output blocked: {block_reason}",
                    extra={
                        "output_type": output_type.value,
                        "event_type": "ai_output_blocked",
                    },
                )
                return SanitizationResult(
                    is_safe=False,
                    sanitized_output="[OUTPUT BLOCKED]",
                    warnings=warnings,
                    blocked=True,
                    reason=block_reason,
                )

            # Validate clinical insights (special handling)
            if output_type == OutputType.CLINICAL_INSIGHT:
                clinical_warnings = self._validate_clinical_output(text_output)
                warnings.extend(clinical_warnings)

            # Log successful sanitization
            if warnings:
                logger.warning(
                    f"AI output sanitized with warnings",
                    extra={
                        "num_warnings": len(warnings),
                        "warnings": warnings,
                        "output_type": output_type.value,
                        "event_type": "ai_output_sanitized",
                    },
                )
            else:
                logger.info(
                    f"AI output validated as safe",
                    extra={
                        "output_type": output_type.value,
                        "event_type": "ai_output_safe",
                    },
                )

            return SanitizationResult(
                is_safe=True,
                sanitized_output=sanitized,
                warnings=warnings,
                blocked=False,
                reason=None,
            )

        except Exception as e:
            logger.error(
                f"Error during AI output sanitization: {str(e)}",
                extra={"event_type": "ai_output_sanitization_error"},
                exc_info=True,
            )
            return SanitizationResult(
                is_safe=False,
                sanitized_output="[SANITIZATION ERROR]",
                warnings=[f"Sanitization error: {str(e)}"],
                blocked=True,
                reason="Sanitization system error",
            )

    def _check_dangerous_patterns(self, text: str) -> Optional[str]:
        """Check for dangerous patterns in output"""
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    return f"{category}: {match.group()[:50]}..."
        return None

    def _check_for_secrets(self, text: str) -> bool:
        """Check if output might contain leaked secrets"""
        secret_indicators = [
            r"\b[A-Za-z0-9]{32,}\b",  # Long hex strings (API keys, tokens)
            r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",  # Bearer tokens
            r"Sk-[a-zA-Z0-9]{48}",  # OpenAI API keys
            r"ghp_[a-zA-Z0-9]{36}",  # GitHub tokens
            r"AIza[A-Za-z0-9\-_]{35}",  # Google API keys
            r"xoxb-[0-9]{12,13}-[0-9]{12,13}-[A-Za-z0-9]{24}",  # Slack tokens
        ]

        for pattern in secret_indicators:
            if re.search(pattern, text):
                return True

        return False

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from text"""
        # Remove script tags and content
        text = re.sub(
            r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
        )

        # Remove other HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up extra whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _validate_clinical_output(self, text: str) -> List[str]:
        """Validate clinical insight output for safety"""
        warnings = []

        # Check for diagnostic language (should be cautious)
        diagnostic_terms = [
            "diagnosis",
            "disorder",
            "disease",
            "condition",
            "patient has",
            "suffers from",
            "afflicted with",
        ]

        text_lower = text.lower()
        for term in diagnostic_terms:
            if term in text_lower:
                warnings.append(f"Contains diagnostic language: '{term}'")
                break

        # Check for definitive treatment recommendations
        # (should include disclaimers)
        if "should take" in text_lower or "must take" in text_lower:
            if "consult" not in text_lower and "doctor" not in text_lower:
                warnings.append("Treatment recommendation lacks medical disclaimer")

        return warnings

    def validate_code_output(
        self, code: str, language: str = "python"
    ) -> SanitizationResult:
        """
        Validate code output for safety

        Args:
            code: Code string to validate
            language: Programming language

        Returns:
            SanitizationResult with validation status
        """
        warnings = []

        # Check for dangerous operations
        dangerous_ops = {
            "python": ["eval(", "exec(", "compile(", "__import__"],
            "javascript": ["eval(", "execScript(", "Function("],
            "sql": ["DROP", "DELETE", "TRUNCATE", "ALTER"],
        }

        if language in dangerous_ops:
            for op in dangerous_ops[language]:
                if op in code:
                    warnings.append(f"Contains dangerous operation: {op}")

        # Check for file operations
        file_ops = ["open(", "file(", "read(", "write("]
        if any(op in code for op in file_ops):
            warnings.append("Contains file operations")

        # Check for network operations
        network_ops = ["urllib", "requests", "http", "socket"]
        if any(op in code for op in network_ops):
            warnings.append("Contains network operations")

        # Check for system commands
        system_ops = ["os.system", "subprocess", "Popen"]
        if any(op in code for op in system_ops):
            warnings.append("Contains system command execution")

        is_safe = len(warnings) == 0

        return SanitizationResult(
            is_safe=is_safe,
            sanitized_output=code,
            warnings=warnings,
            blocked=False,
            reason=None,
        )


# Global sanitizer instance
ai_output_sanitizer = AIOutputSanitizer()


def sanitize_ai_output(
    output: Any,
    output_type: OutputType = OutputType.TEXT,
    allow_html: bool = False,
    strip_html: bool = True,
) -> SanitizationResult:
    """
    Convenience function to sanitize AI output

    Usage:
        result = sanitize_ai_output(model_response, OutputType.TEXT)
        if result.blocked:
            logger.error(f"Output blocked: {result.reason}")
        elif result.warnings:
            logger.warning(f"Output sanitized: {result.warnings}")
        safe_output = result.sanitized_output
    """
    return ai_output_sanitizer.sanitize(output, output_type, allow_html, strip_html)
