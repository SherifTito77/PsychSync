"""
Context Assembly Service for Secure Data Handling
Provides data minimization, PII redaction, and audit logging for AI systems.

Features:
- Data minimization: Include only necessary fields
- PII anonymization: Names, emails, phones, addresses
- Secret redaction: API keys, passwords, tokens
- ID hashing: Sensitive identifiers
- Role-scoped retrieval: RBAC-based data access
- Audit logging: Complete data lineage tracking

Author: PsychSync Security Team
Version: 1.0.0
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

# Configure audit logging
audit_logger = logging.getLogger('context_assembly_audit')


class DataScope(Enum):
    """Data access scopes based on user role."""
    PUBLIC = "public"           # Non-sensitive data only
    RESTRICTED = "restricted"   # Partial data (masked)
    CONFIDENTIAL = "confidential"  # Full data access
    ADMIN = "admin"             # All data including secrets


class RedactionLevel(Enum):
    """PII redaction levels."""
    NONE = "none"              # No redaction
    MINIMAL = "minimal"        # Mask sensitive fields only
    MODERATE = "moderate"      # Mask + anonymize PII
    AGGRESSIVE = "aggressive"  # Maximum redaction


@dataclass
class DataLineage:
    """Audit trail for data access and transformations."""
    timestamp: str
    user_id: str
    user_role: str
    operation: str
    data_scope: DataScope
    redaction_level: RedactionLevel
    fields_accessed: List[str]
    fields_redacted: List[str]
    pii_detected: List[str]
    secrets_detected: List[str]
    input_hash: str
    output_hash: str
    processing_time_ms: float


@dataclass
class ContextAssemblyResult:
    """Result of context assembly operation."""
    assembled_context: Dict[str, Any]
    lineage: DataLineage
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert result to JSON (excluding sensitive data)."""
        safe_copy = {
            'assembled_context': self.assembled_context,
            'lineage': asdict(self.lineage),
            'warnings': self.warnings,
            'metadata': self.metadata
        }
        return json.dumps(safe_copy, indent=2)


class PIIDetector:
    """
    Detect and classify PII in text data.

    Patterns detected:
    - Email addresses
    - Phone numbers (US and international)
    - Social Security Numbers
    - Credit card numbers
    - IP addresses
    - Names (heuristic)
    - Addresses (heuristic)
    """

    # Regex patterns for PII detection
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone_us': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'phone_intl': r'\b\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',
        'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
        'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        'api_key': r'\b[A-Za-z0-9]{32,}\b',  # Generic API key pattern
        'aws_key': r'\bAKIA[0-9A-Z]{16}\b',
        'github_token': r'\bghp_[A-Za-z0-9]{36}\b',
        'bearer_token': r'\bBearer [A-Za-z0-9\-._~+/]+=*\b',
    }

    # Name detection patterns (heuristic)
    NAME_PATTERNS = [
        r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+',
        r'\b[A-Z][a-z]+\s+(?:et\s+al|and\s+others)',
    ]

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping PII type to list of matches
        """
        detections = {}

        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                detections[pii_type] = matches

        return detections

    def has_pii(self, text: str) -> bool:
        """Check if text contains any PII."""
        detections = self.detect_pii(text)
        return len(detections) > 0


class SecretDetector:
    """
    Detect and redact secrets and sensitive credentials.

    Detects:
    - API keys (various formats)
    - Passwords (context-based)
    - Tokens (JWT, bearer, OAuth)
    - Database connection strings
    - Private keys
    """

    SECRET_PATTERNS = {
        'password': r'(?i)(?:password|passwd|pwd)\s*[=:]\s*[^\s\'"<>]+',
        'api_key': r'(?i)(?:api[_-]?key|apikey)\s*[=:]\s*[^\s\'"<>]+',
        'secret_key': r'(?i)(?:secret[_-]?key|secretkey)\s*[=:]\s*[^\s\'"<>]+',
        'token': r'(?i)(?:token|auth[_-]?token)\s*[=:]\s*[^\s\'"<>]+',
        'connection_string': r'(?i)(?:mongodb|mysql|postgres|redis)://[^\s\'"<>]+',
        'jwt': r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b',
        'private_key': r'-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----',
        'aws_access_key': r'\bAKIA[0-9A-Z]{16}\b',
        'azure_key': r'\b[A-Za-z0-9/+=]{88}\b',  # Azure storage key
    }

    def detect_secrets(self, text: str) -> Dict[str, List[str]]:
        """
        Detect secrets in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping secret type to list of matches (redacted)
        """
        detections = {}

        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                # Redact for logging
                redacted = [self._redact_match(m) for m in matches]
                detections[secret_type] = redacted

        return detections

    def _redact_match(self, match: str) -> str:
        """Redact a match for safe logging."""
        if len(match) > 20:
            return f"{match[:8]}...{match[-4:]}"  # Show first 8 and last 4 chars
        return "*" * len(match)

    def has_secrets(self, text: str) -> bool:
        """Check if text contains any secrets."""
        detections = self.detect_secrets(text)
        return len(detections) > 0


class DataMinimizer:
    """
    Minimize data by including only necessary fields.

    Implements need-to-know principle for data access.
    """

    def __init__(self, required_fields: Optional[Set[str]] = None):
        """
        Initialize data minimizer.

        Args:
            required_fields: Set of fields that are required (None = all fields allowed)
        """
        self.required_fields = required_fields

    def minimize(self, data: Dict[str, Any], scope: DataScope) -> Dict[str, Any]:
        """
        Minimize data based on scope.

        Args:
            data: Input data dictionary
            scope: Data access scope

        Returns:
            Minimized data dictionary
        """
        if scope == DataScope.ADMIN:
            # Admins get everything
            return data.copy()

        if scope == DataScope.CONFIDENTIAL:
            # Confidential gets most data, except secrets
            return {k: v for k, v in data.items() if not self._is_secret_field(k)}

        if scope == DataScope.RESTRICTED:
            # Restricted gets masked sensitive fields
            return self._mask_sensitive_fields(data)

        if scope == DataScope.PUBLIC:
            # Public gets only non-sensitive fields
            return {k: v for k, v in data.items() if self._is_public_field(k)}

        return {}

    def _is_secret_field(self, field_name: str) -> bool:
        """Check if field is a secret field."""
        secret_keywords = {'password', 'secret', 'token', 'key', 'auth'}
        return any(keyword in field_name.lower() for keyword in secret_keywords)

    def _is_public_field(self, field_name: str) -> bool:
        """Check if field is safe for public access."""
        sensitive_keywords = {
            'email', 'phone', 'ssn', 'social', 'credit', 'card',
            'password', 'secret', 'token', 'address', 'location'
        }
        return not any(keyword in field_name.lower() for keyword in sensitive_keywords)

    def _mask_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields."""
        masked = {}
        for key, value in data.items():
            if self._is_secret_field(key):
                masked[key] = "***REDACTED***"
            elif isinstance(value, str):
                masked[key] = self._mask_pii_partial(key, value)
            else:
                masked[key] = value
        return masked

    def _mask_pii_partial(self, field_name: str, value: str) -> str:
        """Partially mask PII fields."""
        if 'email' in field_name.lower():
            # Show first 2 chars, mask until @
            parts = value.split('@')
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
        elif 'phone' in field_name.lower():
            # Show last 4 digits only
            digits = re.sub(r'\D', '', value)
            if len(digits) >= 4:
                return f"***-***-{digits[-4:]}"
        elif 'name' in field_name.lower():
            # Show first initial only
            parts = value.split()
            if parts:
                return f"{parts[0][0]}."

        return value


class PIIRedactor:
    """
    Redact or anonymize PII in text.

    Supports:
    - Email redaction (user@domain → u***@domain.com)
    - Phone masking (555-1234 → ***-***-1234)
    - SSN masking (123-45-6789 → ***-**-****)
    - Credit card masking
    - Name anonymization
    """

    EMAIL_REPLACEMENT = r'\1***@\2\3'
    PHONE_REPLACEMENT = r'***-***-\3'
    SSN_REPLACEMENT = r'***-**-****'
    CARD_REPLACEMENT = r'****-****-****-\4'

    def redact_email(self, email: str) -> str:
        """Redact email address (show domain)."""
        pattern = r'\b([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,}))\b'
        return re.sub(pattern, self.EMAIL_REPLACEMENT, email, flags=re.IGNORECASE)

    def redact_phone(self, phone: str) -> str:
        """Redact phone number (show last 4 digits)."""
        # US format
        pattern = r'\b\d{3}[-.]?(\d{3})[-.]?(\d{4})\b'
        if re.search(pattern, phone):
            return re.sub(pattern, self.PHONE_REPLACEMENT, phone)

        # International format
        intl_pattern = r'\b(\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?)\d{1,4}[-.\s]?(\d{1,4})\b'
        matches = re.findall(intl_pattern, phone)
        if matches:
            # Show last few digits only
            return re.sub(intl_pattern, r'\1***', phone)

        return phone

    def redact_ssn(self, ssn: str) -> str:
        """Redact SSN completely."""
        return re.sub(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', self.SSN_REPLACEMENT, ssn)

    def redact_credit_card(self, card: str) -> str:
        """Redact credit card (show last 4 digits)."""
        pattern = r'\b(\d{4}[-.\s]?){3}(\d{4})\b'
        return re.sub(pattern, self.CARD_REPLACEMENT, card)

    def redact_text(self, text: str, level: RedactionLevel = RedactionLevel.MODERATE) -> str:
        """
        Redact all PII in text based on level.

        Args:
            text: Text to redact
            level: Redaction intensity

        Returns:
            Redacted text
        """
        if level == RedactionLevel.NONE:
            return text

        redacted = text

        # Always redact SSNs and credit cards
        redacted = self.redact_ssn(redacted)
        redacted = self.redact_credit_card(redacted)

        if level in [RedactionLevel.MODERATE, RedactionLevel.AGGRESSIVE]:
            # Redact emails and phones
            redacted = self.redact_email(redacted)
            redacted = self.redact_phone(redacted)

        if level == RedactionLevel.AGGRESSIVE:
            # Additional redactions (IP addresses, etc.)
            redacted = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '***.***.***.***', redacted)

        return redacted


class IDHasher:
    """
    Hash sensitive identifiers for privacy.

    Uses SHA-256 for one-way hashing of IDs.
    """

    def __init__(self, salt: Optional[str] = None):
        """
        Initialize ID hasher.

        Args:
            salt: Salt for hashing (auto-generated if None)
        """
        self.salt = salt or hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16]

    def hash_id(self, identifier: str) -> str:
        """
        Hash an identifier.

        Args:
            identifier: ID to hash

        Returns:
            Hashed ID (hex string)
        """
        salted = f"{self.salt}{identifier}".encode('utf-8')
        return hashlib.sha256(salted).hexdigest()

    def hash_ids_in_data(self, data: Dict[str, Any], id_fields: Set[str]) -> Dict[str, Any]:
        """
        Hash specific ID fields in data.

        Args:
            data: Data dictionary
            id_fields: Set of field names to hash

        Returns:
            Data with hashed IDs
        """
        result = data.copy()
        for field in id_fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.hash_id(result[field])
        return result


class RoleScopedRetrieval:
    """
    Role-based data retrieval with automatic scoping.

    Maps user roles to data access scopes.
    """

    ROLE_TO_SCOPE = {
        'user': DataScope.RESTRICTED,
        'premium_user': DataScope.CONFIDENTIAL,
        'admin': DataScope.ADMIN,
        'analyst': DataScope.CONFIDENTIAL,
        'viewer': DataScope.PUBLIC,
        'superadmin': DataScope.ADMIN,
    }

    def get_scope_for_role(self, role: str) -> DataScope:
        """
        Get data access scope for role.

        Args:
            role: User role

        Returns:
            DataScope for the role
        """
        return self.ROLE_TO_SCOPE.get(role.lower(), DataScope.PUBLIC)

    def filter_by_role(self, data: Dict[str, Any], role: str) -> Dict[str, Any]:
        """
        Filter data based on user role.

        Args:
            data: Data to filter
            role: User role

        Returns:
            Filtered data
        """
        scope = self.get_scope_for_role(role)
        minimizer = DataMinimizer()
        return minimizer.minimize(data, scope)


class ContextAssemblyService:
    """
    Main service for assembling secure context for AI systems.

    Combines all security features:
    - Data minimization
    - PII detection and redaction
    - Secret detection and redaction
    - ID hashing
    - Role-scoped retrieval
    - Audit logging
    """

    def __init__(
        self,
        pii_detector: Optional[PIIDetector] = None,
        secret_detector: Optional[SecretDetector] = None,
        redactor: Optional[PIIRedactor] = None,
        hasher: Optional[IDHasher] = None,
        enable_audit_logging: bool = True
    ):
        """
        Initialize context assembly service.

        Args:
            pii_detector: PII detector instance
            secret_detector: Secret detector instance
            redactor: PII redactor instance
            hasher: ID hasher instance
            enable_audit_logging: Enable audit logging
        """
        self.pii_detector = pii_detector or PIIDetector()
        self.secret_detector = secret_detector or SecretDetector()
        self.redactor = redactor or PIIRedactor()
        self.hasher = hasher or IDHasher()
        self.role_retrieval = RoleScopedRetrieval()
        self.enable_audit_logging = enable_audit_logging

        # Configure audit logger
        if self.enable_audit_logging:
            handler = logging.FileHandler('logs/context_assembly_audit.log')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            audit_logger.addHandler(handler)
            audit_logger.setLevel(logging.INFO)

    def assemble_context(
        self,
        data: Dict[str, Any],
        user_id: str,
        user_role: str,
        redaction_level: RedactionLevel = RedactionLevel.MODERATE,
        id_fields: Optional[Set[str]] = None,
        required_fields: Optional[Set[str]] = None
    ) -> ContextAssemblyResult:
        """
        Assemble secure context for AI processing.

        Args:
            data: Input data (can contain PII/secrets)
            user_id: User ID requesting access
            user_role: User role (for RBAC)
            redaction_level: PII redaction level
            id_fields: Fields to hash (if any)
            required_fields: Fields that must be included

        Returns:
            ContextAssemblyResult with assembled context and lineage
        """
        start_time = datetime.now(timezone.utc)

        # Calculate input hash for lineage
        input_hash = self._calculate_hash(data)

        # Initialize lineage tracking
        lineage = DataLineage(
            timestamp=start_time.isoformat(),
            user_id=user_id,
            user_role=user_role,
            operation="assemble_context",
            data_scope=self.role_retrieval.get_scope_for_role(user_role),
            redaction_level=redaction_level,
            fields_accessed=[],
            fields_redacted=[],
            pii_detected=[],
            secrets_detected=[],
            input_hash=input_hash,
            output_hash="",  # Will calculate at end
            processing_time_ms=0
        )

        warnings = []

        # Step 1: Role-based filtering
        scope = self.role_retrieval.get_scope_for_role(user_role)
        filtered_data = self.role_retrieval.filter_by_role(data, user_role)
        lineage.fields_accessed = list(filtered_data.keys())

        # Step 2: Hash sensitive IDs
        if id_fields:
            filtered_data = self.hasher.hash_ids_in_data(filtered_data, id_fields)

        # Step 3: Detect PII
        text_data = self._dict_to_text(filtered_data)
        pii_detections = self.pii_detector.detect_pii(text_data)
        if pii_detections:
            lineage.pii_detected = list(pii_detections.keys())
            warnings.append(f"PII detected: {', '.join(lineage.pii_detected)}")

        # Step 4: Detect secrets
        secret_detections = self.secret_detector.detect_secrets(text_data)
        if secret_detections:
            lineage.secrets_detected = list(secret_detections.keys())
            warnings.append(f"Secrets detected and redacted: {', '.join(lineage.secrets_detected)}")

        # Step 5: Redact PII and secrets
        assembled_context = self._redact_data(filtered_data, redaction_level)
        lineage.fields_redacted = list(set(data.keys()) - set(assembled_context.keys()))

        # Add metadata
        metadata = {
            'assembled_at': start_time.isoformat(),
            'user_role': user_role,
            'data_scope': scope.value,
            'redaction_level': redaction_level.value,
            'original_field_count': len(data),
            'assembled_field_count': len(assembled_context),
            'fields_redacted': len(lineage.fields_redacted),
        }

        # Calculate output hash
        output_hash = self._calculate_hash(assembled_context)

        # Calculate processing time
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds() * 1000

        lineage.output_hash = output_hash
        lineage.processing_time_ms = processing_time

        # Create result
        result = ContextAssemblyResult(
            assembled_context=assembled_context,
            lineage=lineage,
            warnings=warnings,
            metadata=metadata
        )

        # Audit log
        if self.enable_audit_logging:
            self._log_audit(result)

        return result

    def assemble_rag_context(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        user_id: str,
        user_role: str,
        redaction_level: RedactionLevel = RedactionLevel.MODERATE
    ) -> ContextAssemblyResult:
        """
        Assemble secure context for RAG (Retrieval-Augmented Generation).

        Args:
            query: User query (may contain PII)
            documents: Retrieved documents (may contain PII/secrets)
            user_id: User ID
            user_role: User role
            redaction_level: PII redaction level

        Returns:
            ContextAssemblyResult with redacted query and documents
        """
        # Assemble context with query and documents
        data = {
            'query': query,
            'documents': documents,
            'document_count': len(documents)
        }

        result = self.assemble_context(
            data=data,
            user_id=user_id,
            user_role=user_role,
            redaction_level=redaction_level
        )

        # Add RAG-specific metadata
        result.metadata['rag_query'] = result.assembled_context.get('query', '')
        result.metadata['rag_document_count'] = result.assembled_context.get('document_count', 0)

        return result

    def _redact_data(self, data: Dict[str, Any], level: RedactionLevel) -> Dict[str, Any]:
        """Redact PII and secrets in data dictionary."""
        redacted = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Detect and redact secrets first
                if self.secret_detector.has_secrets(value):
                    redacted[key] = "***SECRET_REDACTED***"
                else:
                    # Redact PII
                    redacted[key] = self.redactor.redact_text(value, level)
            elif isinstance(value, dict):
                redacted[key] = self._redact_data(value, level)
            elif isinstance(value, list):
                redacted[key] = [
                    self._redact_data(item, level) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value

        return redacted

    def _dict_to_text(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to text for PII detection."""
        return json.dumps(data, default=str)

    def _calculate_hash(self, data: Any) -> str:
        """Calculate SHA-256 hash of data."""
        data_str = json.dumps(data, default=str, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def _log_audit(self, result: ContextAssemblyResult):
        """Log audit trail."""
        audit_info = {
            'timestamp': result.lineage.timestamp,
            'user_id': result.lineage.user_id,
            'role': result.lineage.user_role,
            'operation': result.lineage.operation,
            'scope': result.lineage.data_scope.value,
            'redaction_level': result.lineage.redaction_level.value,
            'fields_accessed': len(result.lineage.fields_accessed),
            'fields_redacted': len(result.lineage.fields_redacted),
            'pii_detected': result.lineage.pii_detected,
            'secrets_detected': result.lineage.secrets_detected,
            'processing_time_ms': result.lineage.processing_time_ms,
            'input_hash': result.lineage.input_hash,
            'output_hash': result.lineage.output_hash,
        }

        audit_logger.info(f"Context Assembly: {json.dumps(audit_info)}")


# Convenience functions for quick usage
def assemble_secure_context(
    data: Dict[str, Any],
    user_id: str,
    user_role: str,
    redaction_level: RedactionLevel = RedactionLevel.MODERATE
) -> ContextAssemblyResult:
    """
    Quick function to assemble secure context.

    Args:
        data: Input data
        user_id: User ID
        user_role: User role
        redaction_level: PII redaction level

    Returns:
        ContextAssemblyResult
    """
    service = ContextAssemblyService()
    return service.assemble_context(data, user_id, user_role, redaction_level)


def redact_pii_in_text(text: str, level: RedactionLevel = RedactionLevel.MODERATE) -> str:
    """Quick function to redact PII in text."""
    redactor = PIIRedactor()
    return redactor.redact_text(text, level)
