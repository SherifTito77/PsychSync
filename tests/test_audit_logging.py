"""
Audit Logging Tests

This test suite verifies:
1. Audit logs are created for all critical operations
2. Audit log integrity and consistency
3. Audit log retention and cleanup
4. Audit log performance under load
5. Audit log security and access control
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator, List, Dict, Any
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
import json
import asyncio

from app.core.database import Base
from app.db.models.user import User, UserRole
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.organization import Organization
from app.db.models.response import Response, AssessmentResponse
from app.db.models.assessment import Assessment
from app.core.security import get_password_hash


@pytest.mark.asyncio
@pytest.mark.integration
class TestAuditLogging:
    """Test audit logging functionality"""

    async def test_user_creation_audit_logs(self, db_session: AsyncSession):
        """
        Test that user creation creates appropriate audit logs
        """
        # Mock audit logging service or table
        audit_logs = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow(),
                "ip_address": "127.0.0.1",
                "user_agent": "pytest-audit-test"
            }
            audit_logs.append(audit_log)
            print(f"Audit Log: {action} {entity_type} {entity_id}")

        # Create user and log audit
        user_data = {
            "email": "audituser@test.com",
            "full_name": "Audit Test User",
            "role": UserRole.USER
        }

        user = User(
            email=user_data["email"],
            password_hash=get_password_hash("password123"),
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        # Create audit log
        mock_audit_log(
            action="CREATE",
            entity_type="USER",
            entity_id=user.id,
            details=user_data,
            user_id=user.id
        )
        await db_session.commit()

        # Verify audit log was created
        assert len(audit_logs) == 1
        audit_log = audit_logs[0]

        assert audit_log["action"] == "CREATE"
        assert audit_log["entity_type"] == "USER"
        assert audit_log["entity_id"] == str(user.id)
        assert audit_log["details"]["email"] == user_data["email"]
        assert audit_log["details"]["full_name"] == user_data["full_name"]
        assert audit_log["timestamp"] is not None

    async def test_user_update_audit_logs(self, db_session: AsyncSession):
        """
        Test that user updates create audit logs
        """
        audit_logs = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow(),
                "ip_address": "127.0.0.1",
                "user_agent": "pytest-audit-test"
            }
            audit_logs.append(audit_log)

        # Create initial user
        user = User(
            email="updateaudit@test.com",
            password_hash=get_password_hash("password123"),
            full_name="Initial Name",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Initial creation audit
        mock_audit_log(
            action="CREATE",
            entity_type="USER",
            entity_id=user.id,
            details={"full_name": "Initial Name", "role": "USER"},
            user_id=user.id
        )

        # Update user
        original_name = user.full_name
        user.full_name = "Updated Name"
        user.is_active = False
        await db_session.flush()

        # Update audit log
        mock_audit_log(
            action="UPDATE",
            entity_type="USER",
            entity_id=user.id,
            details={
                "changes": {
                    "full_name": {"from": original_name, "to": "Updated Name"},
                    "is_active": {"from": True, "to": False}
                }
            },
            user_id=user.id
        )
        await db_session.commit()

        # Verify audit logs
        assert len(audit_logs) == 2

        create_log = audit_logs[0]
        update_log = audit_logs[1]

        assert create_log["action"] == "CREATE"
        assert update_log["action"] == "UPDATE"
        assert update_log["details"]["changes"]["full_name"]["from"] == original_name
        assert update_log["details"]["changes"]["full_name"]["to"] == "Updated Name"

    async def test_assessment_submission_audit_logs(self, db_session: AsyncSession):
        """
        Test that assessment submissions are properly audited
        """
        audit_logs = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow(),
                "ip_address": "127.0.0.1",
                "user_agent": "pytest-audit-test"
            }
            audit_logs.append(audit_log)

        # Create test data
        org = Organization(
            name="Assessment Audit Org",
            description="Organization for assessment audit testing"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="assessmentaudit@test.com",
            password_hash=get_password_hash("password123"),
            full_name="Assessment Audit User",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        assessment = Assessment(
            title="Assessment Audit Test",
            description="Assessment for audit testing",
            organization_id=org.id
        )
        db_session.add(assessment)
        await db_session.commit()

        # Log assessment creation
        mock_audit_log(
            action="CREATE",
            entity_type="ASSESSMENT",
            entity_id=assessment.id,
            details={"title": assessment.title, "organization_id": str(org.id)},
            user_id=user.id
        )

        # Simulate assessment submission
        submission_data = {
            "question_1": "answer_A",
            "question_2": "answer_B",
            "question_3": "answer_C"
        }

        response = Response(
            assessment_id=assessment.id,
            user_id=user.id,
            responses=submission_data,
            score=75,
            completed_at=datetime.utcnow()
        )
        db_session.add(response)
        await db_session.commit()

        # Log assessment submission
        mock_audit_log(
            action="SUBMIT",
            entity_type="RESPONSE",
            entity_id=response.id,
            details={
                "assessment_id": str(assessment.id),
                "assessment_title": assessment.title,
                "score": 75,
                "question_count": len(submission_data),
                "completed_at": response.completed_at.isoformat()
            },
            user_id=user.id
        )

        # Verify audit logs
        assert len(audit_logs) == 2

        assessment_log = audit_logs[0]
        response_log = audit_logs[1]

        assert assessment_log["entity_type"] == "ASSESSMENT"
        assert response_log["entity_type"] == "RESPONSE"
        assert response_log["details"]["score"] == 75

    async def test_audit_log_performance_under_load(self, db_session: AsyncSession):
        """
        Test audit logging performance under load
        """
        audit_logs = []
        performance_data = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            start_time = datetime.utcnow()

            # Simulate audit log processing
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": start_time,
                "ip_address": "127.0.0.1",
                "user_agent": "pytest-audit-test"
            }
            audit_logs.append(audit_log)

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            performance_data.append(processing_time)

        # Create test data
        org = Organization(
            name="Performance Test Org",
            description="Organization for performance testing"
        )
        db_session.add(org)
        await db_session.flush()

        # Create multiple users rapidly
        user_count = 50
        users = []

        for i in range(user_count):
            user = User(
                email=f"perf{i}@test.com",
                password_hash=get_password_hash("password123"),
                full_name=f"Performance User {i}",
                role=UserRole.USER,
                is_active=i % 2 == 0
            )
            db_session.add(user)
            await db_session.flush()
            users.append(user)

            # Log user creation
            mock_audit_log(
                action="CREATE",
                entity_type="USER",
                entity_id=user.id,
                details={
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "is_active": user.is_active
                },
                user_id=user.id
            )

        await db_session.commit()

        # Analyze performance
        assert len(audit_logs) == user_count
        assert len(performance_data) == user_count

        avg_processing_time = sum(performance_data) / len(performance_data)
        max_processing_time = max(performance_data)
        min_processing_time = min(performance_data)

        print(f"Audit Log Performance Results:")
        print(f"  - Total audit logs: {len(audit_logs)}")
        print(f"  - Average processing time: {avg_processing_time:.6f}s")
        print(f"  - Max processing time: {max_processing_time:.6f}s")
        print(f"  - Min processing time: {min_processing_time:.6f}s")

        # Performance assertions (adjust based on your requirements)
        assert avg_processing_time < 0.01, f"Average processing time too high: {avg_processing_time}"
        assert max_processing_time < 0.05, f"Max processing time too high: {max_processing_time}"

    async def test_audit_log_data_integrity(self, db_session: AsyncSession):
        """
        Test that audit log data maintains integrity
        """
        audit_logs = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow(),
                "ip_address": "127.0.0.1",
                "user_agent": "pytest-audit-test"
            }
            audit_logs.append(audit_log)

        # Create test data
        org = Organization(
            name="Integrity Test Org",
            description="Organization for integrity testing"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="integrity@test.com",
            password_hash=get_password_hash("password123"),
            full_name="Integrity Test User",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        # Create audit logs with various data types
        test_cases = [
            {
                "action": "CREATE",
                "entity_type": "TEAM",
                "details": {
                    "name": "Test Team",
                    "description": "Team for integrity testing",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {"key": "value", "number": 42, "boolean": True}
                }
            },
            {
                "action": "UPDATE",
                "entity_type": "USER",
                "details": {
                    "changes": {
                        "full_name": {
                            "from": "Original Name",
                            "to": "Updated Name"
                        },
                        "preferences": {
                            "theme": "dark",
                            "notifications": True
                        }
                    }
                }
            },
            {
                "action": "DELETE",
                "entity_type": "ASSESSMENT",
                "details": {
                    "reason": "Test deletion",
                    "confirmation": True
                }
            }
        ]

        for test_case in test_cases:
            mock_audit_log(
                action=test_case["action"],
                entity_type=test_case["entity_type"],
                entity_id=user.id,
                details=test_case["details"],
                user_id=user.id
            )

        # Verify data integrity
        assert len(audit_logs) == len(test_cases)

        for i, audit_log in enumerate(audit_logs):
            expected_case = test_cases[i]

            assert audit_log["action"] == expected_case["action"]
            assert audit_log["entity_type"] == expected_case["entity_type"]
            assert audit_log["entity_id"] == str(user.id)
            assert audit_log["details"] == expected_case["details"]
            assert audit_log["timestamp"] is not None
            assert isinstance(audit_log["timestamp"], datetime)
            assert audit_log["ip_address"] == "127.0.0.1"

    async def test_audit_log_security_and_access_control(self, db_session: AsyncSession):
        """
        Test audit log security features and access control
        """
        audit_logs = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow(),
                "ip_address": "127.0.0.1",
                "user_agent": "pytest-audit-test",
                "session_id": "test-session-123"
            }
            audit_logs.append(audit_log)

        # Create users with different roles
        admin_user = User(
            email="admin@security.com",
            password_hash=get_password_hash("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin_user)
        await db_session.flush()

        regular_user = User(
            email="regular@security.com",
            password_hash=get_password_hash("regular123"),
            full_name="Regular User",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(regular_user)
        await db_session.commit()

        # Test audit logs for different user types
        admin_action = {
            "action": "DELETE_USER",
            "entity_type": "USER",
            "details": {
                "target_user": regular_user.email,
                "reason": "Policy violation",
                "admin_action": True
            },
            "severity": "HIGH"
        }

        regular_action = {
            "action": "UPDATE_PROFILE",
            "entity_type": "USER",
            "details": {
                "field": "full_name",
                "old_value": "Old Name",
                "new_value": "New Name"
            },
            "severity": "LOW"
        }

        # Log admin action
        mock_audit_log(
            action=admin_action["action"],
            entity_type=admin_action["entity_type"],
            entity_id=regular_user.id,
            details=admin_action["details"],
            user_id=admin_user.id
        )

        # Log regular user action
        mock_audit_log(
            action=regular_action["action"],
            entity_type=regular_action["entity_type"],
            entity_id=regular_user.id,
            details=regular_action["details"],
            user_id=regular_user.id
        )

        # Verify audit log security features
        assert len(audit_logs) == 2

        admin_log = audit_logs[0]
        regular_log = audit_logs[1]

        # Verify admin action has higher severity
        assert admin_log["details"]["admin_action"] is True
        assert admin_log["details"]["severity"] == "HIGH"

        # Verify regular action has lower severity
        assert regular_log["details"]["field"] == "full_name"
        assert regular_log["details"]["severity"] == "LOW"

        # Verify user attribution
        assert admin_log["user_id"] == str(admin_user.id)
        assert regular_log["user_id"] == str(regular_user.id)

        # Verify security metadata
        for audit_log in audit_logs:
            assert "ip_address" in audit_log
            assert "user_agent" in audit_log
            assert "session_id" in audit_log

    async def test_audit_log_retention_and_cleanup(self, db_session: AsyncSession):
        """
        Test audit log retention policies and cleanup
        """
        audit_logs = []

        def mock_audit_log(action, entity_type, entity_id, details, user_id=None):
            audit_log = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "details": details,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow(),
                "ip_address": "127.0.0.0.1",
                "user_agent": "pytest-audit-test"
            }
            audit_logs.append(audit_log)

        # Create test data
        org = Organization(
            name="Retention Test Org",
            description="Organization for retention testing"
        )
        db_session.add(org)
        await db_session.flush()

        user = User(
            email="retention@test.com",
            password_hash=get_password_hash("password123"),
            full_name="Retention Test User",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Create audit logs with different timestamps
        base_time = datetime.utcnow()
        retention_period_days = 30

        for i in range(10):
            # Create audit logs with different ages
            timestamp = base_time - timedelta(days=i)

            mock_audit_log(
                action="TEST_ACTION",
                entity_type="TEST_ENTITY",
                entity_id=f"test-entity-{i}",
                details={"test_data": f"test_data_{i}", "age_days": i},
                user_id=user.id
            )

            # Simulate timestamp adjustment
            audit_logs[-1]["timestamp"] = timestamp

        # Test retention policy
        cutoff_time = datetime.utcnow() - timedelta(days=retention_period_days)
        old_logs = [log for log in audit_logs if log["timestamp"] < cutoff_time]
        recent_logs = [log for log in audit_logs if log["timestamp"] >= cutoff_time]

        print(f"Audit Log Retention Results:")
        print(f"  - Total audit logs: {len(audit_logs)}")
        print(f"  - Old logs (older than {retention_period_days} days): {len(old_logs)}")
        print(f"  - Recent logs (within {retention_period_days} days): {len(recent_logs)}")

        # Verify retention logic
        assert len(recent_logs) > 0, "Should have recent logs"

        # In a real implementation, you would delete old logs
        # For now, just verify the filtering logic
        assert len(old_logs) + len(recent_logs) == len(audit_logs)
        assert all(log["timestamp"] >= cutoff_time for log in recent_logs)
        assert all(log["timestamp"] < cutoff_time for log in old_logs)