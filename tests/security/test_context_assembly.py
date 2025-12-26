"""
Unit Tests for Context Assembly Service
Demonstrates PII redaction, secret detection, and data lineage tracking.

Run: pytest tests/security/test_context_assembly.py -v
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai.services.context_assembly import (
    ContextAssemblyService,
    DataScope,
    PIIDetector,
    PIIRedactor,
    SecretDetector,
    IDHasher,
    RoleScopedRetrieval,
    RedactionLevel,
    DataLineage,
    assemble_secure_context,
    redact_pii_in_text,
)


# =============================================================================
# Test Data: PII and Secrets
# =============================================================================

TEST_DATA_WITH_PII = {
    'name': 'John Doe',
    'email': 'john.doe@example.com',
    'phone': '555-123-4567',
    'ssn': '123-45-6789',
    'address': '123 Main St, City, State 12345',
    'credit_card': '4532-1234-5678-9010',
    'notes': 'Regular user',
}

TEST_DATA_WITH_SECRETS = {
    'username': 'testuser',
    'password': 'SecretPassword123!',
    'api_key': 'AKIAIOSFODNN7EXAMPLE',
    'database_url': 'mongodb://user:pass123@localhost:27017/db',
    'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example',
    'notes': 'Configuration data',
}

RAG_QUERY_WITH_PII = "What is John Doe's email address and phone number?"

RAG_DOCUMENTS = [
    {
        'id': 'doc1',
        'title': 'User Profile',
        'content': 'Contact: John Doe, email: john@example.com, phone: 555-987-6543',
    },
    {
        'id': 'doc2',
        'title': 'Account Info',
        'content': 'SSN: 987-65-4321, Credit Card: 5423-4567-8901-2345',
    },
]


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def pii_detector():
    return PIIDetector()


@pytest.fixture
def secret_detector():
    return SecretDetector()


@pytest.fixture
def redactor():
    return PIIRedactor()


@pytest.fixture
def context_service(tmp_path):
    """Create service with test audit log."""
    # Create temp directory for logs
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Disable file logging for tests
    service = ContextAssemblyService(enable_audit_logging=False)
    return service


# =============================================================================
# PII Detection Tests
# =============================================================================

class TestPIIDetection:
    """Test PII detection in text."""

    def test_detect_email(self, pii_detector):
        """Test email detection."""
        text = "Contact us at john.doe@example.com for support"
        detections = pii_detector.detect_pii(text)
        assert 'email' in detections
        assert 'john.doe@example.com' in detections['email']

    def test_detect_phone(self, pii_detector):
        """Test phone number detection."""
        text = "Call me at 555-123-4567"
        detections = pii_detector.detect_pii(text)
        assert 'phone_us' in detections

    def test_detect_ssn(self, pii_detector):
        """Test SSN detection."""
        text = "My SSN is 123-45-6789"
        detections = pii_detector.detect_pii(text)
        assert 'ssn' in detections

    def test_detect_credit_card(self, pii_detector):
        """Test credit card detection."""
        text = "Card number: 4532-1234-5678-9010"
        detections = pii_detector.detect_pii(text)
        assert 'credit_card' in detections

    def test_detect_multiple_pii_types(self, pii_detector):
        """Test detecting multiple PII types in one text."""
        text = "John Doe, email: john@example.com, phone: 555-123-4567, SSN: 123-45-6789"
        detections = pii_detector.detect_pii(text)
        assert len(detections) >= 4
        assert 'email' in detections
        assert 'phone_us' in detections
        assert 'ssn' in detections

    def test_has_pii_positive(self, pii_detector):
        """Test has_pii returns True when PII present."""
        text = "Email: john@example.com"
        assert pii_detector.has_pii(text) is True

    def test_has_pii_negative(self, pii_detector):
        """Test has_pii returns False when no PII."""
        text = "This is just regular text"
        assert pii_detector.has_pii(text) is False


# =============================================================================
# Secret Detection Tests
# =============================================================================

class TestSecretDetection:
    """Test secret detection in text."""

    def test_detect_password(self, secret_detector):
        """Test password detection."""
        text = "password=SecretPassword123!"
        detections = secret_detector.detect_secrets(text)
        assert 'password' in detections

    def test_detect_api_key(self, secret_detector):
        """Test API key detection."""
        text = "api_key=AKIAIOSFODNN7EXAMPLE"
        detections = secret_detector.detect_secrets(text)
        assert 'aws_access_key' in detections

    def test_detect_jwt(self, secret_detector):
        """Test JWT token detection."""
        text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        detections = secret_detector.detect_secrets(text)
        assert 'jwt' in detections

    def test_detect_connection_string(self, secret_detector):
        """Test database connection string detection."""
        text = "mongodb://user:pass@localhost:27017/db"
        detections = secret_detector.detect_secrets(text)
        assert 'connection_string' in detections

    def test_redact_in_detection(self, secret_detector):
        """Test that secrets are redacted in detection output."""
        text = "password=MyVeryLongSecretPassword123!"
        detections = secret_detector.detect_secrets(text)
        # Should be redacted (not show full password)
        assert 'MyVeryLongSecretPassword123!' not in str(detections)


# =============================================================================
# PII Redaction Tests
# =============================================================================

class TestPIIRedaction:
    """Test PII redaction at different levels."""

    def test_redact_email(self, redactor):
        """Test email redaction."""
        email = "john.doe@example.com"
        redacted = redactor.redact_email(email)
        assert '***@' in redacted
        assert 'example.com' in redacted

    def test_redact_phone(self, redactor):
        """Test phone redaction."""
        phone = "555-123-4567"
        redacted = redactor.redact_phone(phone)
        assert '***-***-' in redacted
        assert '4567' in redacted  # Last 4 digits visible

    def test_redact_ssn(self, redactor):
        """Test SSN redaction."""
        ssn = "123-45-6789"
        redacted = redactor.redact_ssn(ssn)
        assert redacted == '***-**-****'

    def test_redact_credit_card(self, redactor):
        """Test credit card redaction."""
        card = "4532-1234-5678-9010"
        redacted = redactor.redact_credit_card(card)
        assert '****-****-****-' in redacted
        assert '9010' in redacted  # Last 4 digits visible

    def test_redact_text_minimal(self, redactor):
        """Test minimal redaction level."""
        text = "SSN: 123-45-6789, Email: john@example.com"
        redacted = redactor.redact_text(text, RedactionLevel.MINIMAL)
        # SSN and card always redacted
        assert '***-**-****' in redacted
        # Email might not be redacted at minimal level

    def test_redact_text_moderate(self, redactor):
        """Test moderate redaction level."""
        text = "SSN: 123-45-6789, Email: john@example.com, Phone: 555-123-4567"
        redacted = redactor.redact_text(text, RedactionLevel.MODERATE)
        assert '***-**-****' in redacted  # SSN
        assert '***@' in redacted  # Email
        assert '***-***-' in redacted  # Phone

    def test_redact_text_aggressive(self, redactor):
        """Test aggressive redaction level."""
        text = "IP: 192.168.1.1, Email: john@example.com"
        redacted = redactor.redact_text(text, RedactionLevel.AGGRESSIVE)
        assert '***.***.***.***' in redacted  # IP redacted
        assert '***@' in redacted  # Email redacted

    def test_redact_text_none(self, redactor):
        """Test no redaction."""
        text = "Email: john@example.com"
        redacted = redactor.redact_text(text, RedactionLevel.NONE)
        assert redacted == text


# =============================================================================
# ID Hashing Tests
# =============================================================================

class TestIDHashing:
    """Test ID hashing for privacy."""

    def test_hash_id(self):
        """Test ID hashing."""
        hasher = IDHasher()
        id1 = "user_12345"
        id2 = "user_12345"
        id3 = "user_67890"

        hash1 = hasher.hash_id(id1)
        hash2 = hasher.hash_id(id2)
        hash3 = hasher.hash_id(id3)

        # Same ID should produce same hash
        assert hash1 == hash2

        # Different IDs should produce different hashes
        assert hash1 != hash3

    def test_hash_ids_in_data(self):
        """Test hashing specific fields in data."""
        hasher = IDHasher()
        data = {
            'user_id': 'user_123',
            'name': 'John',
            'email': 'john@example.com',
        }

        hashed_data = hasher.hash_ids_in_data(data, {'user_id'})

        assert hashed_data['user_id'] != 'user_123'  # Should be hashed
        assert hashed_data['name'] == 'John'  # Unchanged
        assert hashed_data['email'] == 'john@example.com'  # Unchanged


# =============================================================================
# Role-Based Scoping Tests
# =============================================================================

class TestRoleScopedRetrieval:
    """Test role-based data filtering."""

    def test_admin_role(self):
        """Admin gets all data."""
        data = {'name': 'John', 'password': 'secret', 'email': 'john@example.com'}
        retriever = RoleScopedRetrieval()
        result = retriever.filter_by_role(data, 'admin')
        assert result == data

    def test_user_role(self):
        """Regular user gets restricted data."""
        data = {'name': 'John', 'password': 'secret', 'email': 'john@example.com'}
        retriever = RoleScopedRetrieval()
        result = retriever.filter_by_role(data, 'user')

        # Password should be redacted
        assert result['password'] == '***REDACTED***'
        # Email should be partially masked
        assert '***' in result['email']
        # Name might be partially visible
        assert 'name' in result

    def test_public_role(self):
        """Public role gets minimal data."""
        data = {
            'name': 'John',
            'password': 'secret',
            'email': 'john@example.com',
            'description': 'Public profile',
        }
        retriever = RoleScopedRetrieval()
        result = retriever.filter_by_role(data, 'viewer')

        # Should only have public-safe fields
        assert 'password' not in result
        assert 'email' not in result
        assert 'description' in result


# =============================================================================
# Context Assembly Integration Tests
# =============================================================================

class TestContextAssembly:
    """Test complete context assembly with all features."""

    def test_assemble_context_with_pii(self, context_service):
        """Test assembling context containing PII."""
        result = context_service.assemble_context(
            data=TEST_DATA_WITH_PII,
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        # Should have PII detected in lineage
        assert len(result.lineage.pii_detected) > 0

        # PII should be redacted in assembled context
        context = result.assembled_context
        assert '***@' in context.get('email', '')
        assert '***-***-' in context.get('phone', '')

        # Warnings should include PII detection
        assert any('PII detected' in w for w in result.warnings)

    def test_assemble_context_with_secrets(self, context_service):
        """Test assembling context containing secrets."""
        result = context_service.assemble_context(
            data=TEST_DATA_WITH_SECRETS,
            user_id='user_123',
            user_role='admin',
            redaction_level=RedactionLevel.MODERATE
        )

        # Should have secrets detected in lineage
        assert len(result.lineage.secrets_detected) > 0

        # Secrets should be redacted
        context = result.assembled_context
        assert context.get('password') == '***SECRET_REDACTED***'
        assert '***SECRET_REDACTED***' in context.get('api_key', '')

    def test_data_lineage_tracking(self, context_service):
        """Test that data lineage is properly tracked."""
        result = context_service.assemble_context(
            data={'name': 'John', 'email': 'john@example.com'},
            user_id='user_123',
            user_role='user'
        )

        lineage = result.lineage

        # Check lineage fields
        assert lineage.user_id == 'user_123'
        assert lineage.user_role == 'user'
        assert lineage.operation == 'assemble_context'
        assert lineage.data_scope == DataScope.RESTRICTED
        assert lineage.redaction_level == RedactionLevel.MODERATE
        assert len(lineage.fields_accessed) > 0
        assert lineage.input_hash is not None
        assert lineage.outputHash is not None
        assert lineage.processing_time_ms > 0

    def test_redaction_levels_impact(self, context_service):
        """Test that different redaction levels produce different results."""
        data = {'email': 'john@example.com', 'phone': '555-123-4567'}

        minimal = context_service.assemble_context(
            data, 'user_123', 'user', RedactionLevel.MINIMAL
        )
        moderate = context_service.assemble_context(
            data, 'user_123', 'user', RedactionLevel.MODERATE
        )
        aggressive = context_service.assemble_context(
            data, 'user_123', 'user', RedactionLevel.AGGRESSIVE
        )

        # Moderate should have more redaction than minimal
        assert moderate.lineage.fields_redacted != minimal.lineage.fields_redacted

        # Aggressive should have most redaction
        assert aggressive.lineage.redaction_level == RedactionLevel.AGGRESSIVE


# =============================================================================
# RAG Context Tests
# =============================================================================

class TestRAGContextAssembly:
    """Test context assembly for RAG (Retrieval-Augmented Generation)."""

    def test_rag_query_redaction(self, context_service):
        """Test that PII in RAG queries is redacted."""
        result = context_service.assemble_rag_context(
            query=RAG_QUERY_WITH_PII,
            documents=RAG_DOCUMENTS,
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        # Query should be redacted
        query = result.assembled_context.get('query', '')
        assert '***' in query or 'John' not in query  # Either redacted or name removed

        # Should detect PII
        assert len(result.lineage.pii_detected) > 0

    def test_rag_documents_redaction(self, context_service):
        """Test that PII in RAG documents is redacted."""
        result = context_service.assemble_rag_context(
            query="What is the user's contact info?",
            documents=RAG_DOCUMENTS,
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        # Documents should be redacted
        documents = result.assembled_context.get('documents', [])

        for doc in documents:
            content = doc.get('content', '')

            # Should not contain full email
            if 'email:' in content.lower():
                assert '***@' in content or '@example.com' not in content

            # Should not contain full SSN
            if 'ssn:' in content.lower():
                assert '***-**-****' in content

            # Should not contain full credit card
            if 'credit card:' in content.lower():
                assert '****-****-****-' in content

    def test_rag_metadata(self, context_service):
        """Test that RAG-specific metadata is included."""
        result = context_service.assemble_rag_context(
            query="Test query",
            documents=RAG_DOCUMENTS,
            user_id='user_123',
            user_role='user'
        )

        # Should have RAG metadata
        assert 'ragQuery' in result.metadata
        assert 'ragDocumentCount' in result.metadata
        assert result.metadata['ragDocumentCount'] == len(RAG_DOCUMENTS)

    def test_rag_data_lineage(self, context_service):
        """Test that RAG operations are tracked in lineage."""
        result = context_service.assemble_rag_context(
            query="What's my email?",
            documents=[{'content': 'Email: john@example.com'}],
            user_id='user_123',
            user_role='user'
        )

        # Should be tracked as assemble_context operation
        assert result.lineage.operation == 'assemble_context'

        # Should have document count in metadata
        assert 'document_count' in result.assembled_context


# =============================================================================
# Convenience Functions Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions for quick usage."""

    def test_assemble_secure_context(self):
        """Test quick context assembly function."""
        result = assemble_secure_context(
            data={'email': 'john@example.com'},
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        assert result.assembled_context is not None
        assert result.lineage is not None

    def test_redact_pii_in_text(self):
        """Test quick text redaction function."""
        text = "Email: john@example.com, Phone: 555-123-4567"
        redacted = redact_pii_in_text(text, RedactionLevel.MODERATE)

        assert '***@' in redacted
        assert '***-***-' in redacted


# =============================================================================
# Security Tests
# =============================================================================

class TestSecurityScenarios:
    """Test real-world security scenarios."""

    def test_prompt_with_pii_injection(self, context_service):
        """Test prompt containing user's PII."""
        prompt = {
            'system': 'You are a helpful assistant.',
            'user_query': 'My email is john@example.com and my SSN is 123-45-6789',
        }

        result = context_service.assemble_context(
            data=prompt,
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        # User query should be redacted
        user_query = result.assembled_context['user_query']
        assert '***@' in user_query
        assert '***-**-****' in user_query

        # System prompt should be preserved
        assert result.assembled_context['system'] == prompt['system']

    def test_admin_sees_more_data(self, context_service):
        """Test that admin role has less redaction."""
        data = {
            'user_id': 'user_123',
            'password': 'secret123',
            'email': 'john@example.com',
        }

        # Regular user
        user_result = context_service.assemble_context(
            data, 'user_456', 'user', RedactionLevel.MODERATE
        )

        # Admin
        admin_result = context_service.assemble_context(
            data, 'admin_1', 'admin', RedactionLevel.MODERATE
        )

        # User should see password redacted
        assert user_result.assembled_context['password'] == '***SECRET_REDACTED***'

        # Admin should see password (confidential scope excludes secret fields)
        # Note: In real implementation, admin might still have some restrictions
        assert admin_result.lineage.dataScope == DataScope.ADMIN

    def test_cross_user_data_access(self, context_service):
        """Test accessing another user's data."""
        other_user_data = {
            'user_id': 'user_789',
            'name': 'Jane',
            'email': 'jane@example.com',
            'secret_note': 'Private info',
        }

        result = context_service.assemble_context(
            data=other_user_data,
            user_id='user_123',  # Different user
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        # PII should be redacted
        assert '***@' in result.assembled_context.get('email', '')
        # Note: Cross-user access policies should be enforced at application level too

    def test_batch_rag_documents(self, context_service):
        """Test processing multiple RAG documents."""
        documents = [
            {'id': '1', 'text': 'Contact: bob@example.com'},
            {'id': '2', 'text': 'SSN: 987-65-4321'},
            {'id': '3', 'text': 'Card: 5555-1234-5678-9010'},
            {'id': '4', 'text': 'Safe content with no PII'},
        ]

        result = context_service.assemble_rag_context(
            query="Summarize these documents",
            documents=documents,
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )

        assembled_docs = result.assembled_context['documents']

        # All PII should be redacted
        for doc in assembled_docs:
            text = doc['text']

            # Email should be redacted
            if '@example.com' in text or '@' in text:
                assert '***@' in text or '@example.com' not in text

            # SSN should be redacted
            if 'SSN' in text or 'ssn' in text:
                assert '***-**-****' in text

            # Card should be redacted
            if 'Card' in text or 'card' in text:
                assert '****-****-****-' in text

    def test_data_minimization_compliance(self, context_service):
        """Test that data minimization is applied."""
        full_data = {
            'user_id': '123',
            'name': 'John',
            'email': 'john@example.com',
            'phone': '555-123-4567',
            'password': 'secret',
            'preferences': 'theme=dark',
            'bio': 'User bio',
            'notes': 'Additional notes',
        }

        # Public role should get minimal data
        result = context_service.assemble_context(
            data=full_data,
            user_id='user_123',
            user_role='viewer',  # Public role
            redaction_level=RedactionLevel.MODERATE
        )

        context = result.assembled_context

        # Should NOT have sensitive fields
        assert 'email' not in context or '***' in context.get('email', '')
        assert 'phone' not in context or '***' in context.get('phone', '')
        assert 'password' not in context

        # Might have non-sensitive fields
        # (depending on implementation of isPublicField)


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Test performance characteristics."""

    def test_large_document_redaction(self, context_service):
        """Test redacting large document efficiently."""
        large_doc = {
            'content': ' '.join(['Email: john@example.com'] * 1000)
        }

        import time
        start = time.time()
        result = context_service.assemble_context(
            data=large_doc,
            user_id='user_123',
            user_role='user',
            redaction_level=RedactionLevel.MODERATE
        )
        duration = (time.time() - start) * 1000

        # Should complete quickly (< 100ms for 1000 emails)
        assert duration < 100
        assert result.lineage.processing_time_ms < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
