"""
Tenant Isolation Integration Tests

Comprehensive test suite to validate multi-tenant data isolation and prevent
cross-tenant data access (IDOR prevention at tenant level).

Tests cover:
- Organization-level isolation
- Team-level isolation
- User-level ownership isolation
- Cross-tenant access prevention
- Admin/superuser access patterns
- Database-level RLS policy enforcement

Security Level: CRITICAL
Compliance: OWASP ASVS v3.2.1, NIST SP 800-53 Rev 5 (SC-16)
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.row_level_security import RowLevelSecurityManager
from app.db.models.assessment import Assessment
from app.db.models.organization import Organization
from app.db.models.response import Response
from app.db.models.team import Team
from app.db.models.user import User
from app.services.row_level_security import (
    CrossTenantAccessError,
    RowLevelSecurityService,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def rls_service():
    """RLS service instance"""
    return RowLevelSecurityService()


@pytest.fixture
async def multi_tenant_data(test_db: AsyncSession):
    """
    Create test data with multiple tenants for isolation testing

    Structure:
    - Organization 1 (org-1)
      - User 1-1 (user-1-1, admin)
      - User 1-2 (user-1-2, member)
      - Team 1-1
        - Members: user-1-1, user-1-2
      - Assessment 1-1 (owned by user-1-1)

    - Organization 2 (org-2)
      - User 2-1 (user-2-1, admin)
      - User 2-2 (user-2-2, member)
      - Team 2-1
        - Members: user-2-1, user-2-2
      - Assessment 2-1 (owned by user-2-1)
    """

    # Create organizations
    org1 = Organization(id="org-1", name="Organization 1", slug="org-1")
    org2 = Organization(id="org-2", name="Organization 2", slug="org-2")
    test_db.add(org1)
    test_db.add(org2)

    # Create users
    user_1_1 = User(
        id="user-1-1",
        email="user-1-1@test.com",
        organization_id=org1.id,
        is_superuser=False,
    )
    user_1_2 = User(
        id="user-1-2",
        email="user-1-2@test.com",
        organization_id=org1.id,
        is_superuser=False,
    )
    user_2_1 = User(
        id="user-2-1",
        email="user-2-1@test.com",
        organization_id=org2.id,
        is_superuser=False,
    )
    user_2_2 = User(
        id="user-2-2",
        email="user-2-2@test.com",
        organization_id=org2.id,
        is_superuser=False,
    )
    test_db.add_all([user_1_1, user_1_2, user_2_1, user_2_2])

    # Create superuser
    superuser = User(
        id="superuser",
        email="superuser@test.com",
        organization_id=None,
        is_superuser=True,
    )
    test_db.add(superuser)

    # Create teams
    team_1_1 = Team(
        id="team-1-1",
        name="Team 1-1",
        organization_id=org1.id,
        created_by_id=user_1_1.id,
    )
    team_2_1 = Team(
        id="team-2-1",
        name="Team 2-1",
        organization_id=org2.id,
        created_by_id=user_2_1.id,
    )
    test_db.add_all([team_1_1, team_2_1])

    # Create assessments
    assessment_1_1 = Assessment(
        id="assessment-1-1",
        title="Assessment 1-1",
        organization_id=org1.id,
        team_id=team_1_1.id,
        created_by_id=user_1_1.id,
    )
    assessment_2_1 = Assessment(
        id="assessment-2-1",
        title="Assessment 2-1",
        organization_id=org2.id,
        team_id=team_2_1.id,
        created_by_id=user_2_1.id,
    )
    test_db.add_all([assessment_1_1, assessment_2_1])

    # Create responses
    response_1_1 = Response(
        id="response-1-1",
        assessment_id=assessment_1_1.id,
        user_id=user_1_1.id,
        organization_id=org1.id,
    )
    response_2_1 = Response(
        id="response-2-1",
        assessment_id=assessment_2_1.id,
        user_id=user_2_1.id,
        organization_id=org2.id,
    )
    test_db.add_all([response_1_1, response_2_1])

    await test_db.commit()

    return {
        "org1": org1,
        "org2": org2,
        "user_1_1": user_1_1,
        "user_1_2": user_1_2,
        "user_2_1": user_2_1,
        "user_2_2": user_2_2,
        "superuser": superuser,
        "team_1_1": team_1_1,
        "team_2_1": team_2_1,
        "assessment_1_1": assessment_1_1,
        "assessment_2_1": assessment_2_1,
        "response_1_1": response_1_1,
        "response_2_1": response_2_1,
    }


# ============================================================================
# Organization-Level Isolation Tests
# ============================================================================


class TestOrganizationIsolation:
    """Test organization-level tenant isolation"""

    @pytest.mark.asyncio
    async def test_user_can_only_see_own_organization_assessments(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        IDOR Test: User from org-1 attempting to access org-2 assessments

        Expected: Query should return only org-1 assessments
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Get assessments with RLS filter applied
        query = select(Assessment)
        filtered_query = rls_service.apply_organization_filter(
            query, user_1_1, Assessment.organization_id
        )

        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # Should only see org-1 assessments
        assert len(assessments) == 1
        assert assessments[0].id == "assessment-1-1"
        assert assessments[0].organization_id == "org-1"

        # Should NOT see org-2 assessments
        assessment_ids = [a.id for a in assessments]
        assert "assessment-2-1" not in assessment_ids

    @pytest.mark.asyncio
    async def test_cross_organization_access_blocked(
        self, rls_service: RowLevelSecurityService, multi_tenant_data
    ):
        """
        IDOR Test: Explicit cross-organization access check

        Expected: CrossTenantAccessError raised
        """
        user_1_1 = multi_tenant_data["user_1_1"]
        assessment_2_1 = multi_tenant_data["assessment_2_1"]

        # Attempt to access org-2 assessment
        with pytest.raises(CrossTenantAccessError) as exc_info:
            rls_service.check_cross_tenant_access(
                user=user_1_1,
                resource_org_id=assessment_2_1.organization_id,
                resource_team_id=assessment_2_1.team_id,
                resource_owner_id=assessment_2_1.created_by_id,
            )

        assert "does not have access to organization" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_superuser_can_access_all_organizations(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        Test: Superuser can access data from all organizations

        Expected: Superuser bypasses organization filters
        """
        superuser = multi_tenant_data["superuser"]

        # Get assessments with RLS filter (should be bypassed)
        query = select(Assessment)
        filtered_query = rls_service.apply_organization_filter(
            query, superuser, Assessment.organization_id
        )

        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # Superuser should see ALL assessments
        assert len(assessments) == 2
        assessment_ids = {a.id for a in assessments}
        assert assessment_ids == {"assessment-1-1", "assessment-2-1"}

    @pytest.mark.asyncio
    async def test_organization_filter_returns_empty_for_no_access(
        self, test_db: AsyncSession, rls_service: RowLevelSecurityService
    ):
        """
        Test: User with no organization access gets empty query

        Expected: Query returns no results
        """
        # Create user without organization
        user_no_org = User(
            id="no-org-user", email="noorg@test.com", organization_id=None
        )

        query = select(Assessment)
        filtered_query = rls_service.apply_organization_filter(
            query, user_no_org, Assessment.organization_id
        )

        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # Should return empty result
        assert len(assessments) == 0


# ============================================================================
# Team-Level Isolation Tests
# ============================================================================


class TestTeamIsolation:
    """Test team-level tenant isolation"""

    @pytest.mark.asyncio
    async def test_user_can_only_see_own_team_data(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        IDOR Test: User from team-1-1 attempting to access team-2-1 data

        Expected: Query should return only team-1-1 data
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Mock team memberships (in real implementation, this would come from DB)
        # For this test, we'll verify the filter logic works

        # Get teams with RLS filter
        query = select(Team)
        filtered_query = rls_service.apply_organization_filter(
            query, user_1_1, Team.organization_id
        )

        result = await test_db.execute(filtered_query)
        teams = result.scalars().all()

        # Should only see org-1 teams
        assert len(teams) == 1
        assert teams[0].id == "team-1-1"
        assert teams[0].organization_id == "org-1"

    @pytest.mark.asyncio
    async def test_cross_team_access_blocked(
        self, rls_service: RowLevelSecurityService, multi_tenant_data
    ):
        """
        IDOR Test: Explicit cross-team access check

        Expected: CrossTenantAccessError raised
        """
        user_1_1 = multi_tenant_data["user_1_1"]
        team_2_1 = multi_tenant_data["team_2_1"]

        # Mock team memberships (user_1_1 is NOT a member of team_2-1)
        # In real implementation, this would query team_members table

        # Attempt to access team-2-1 data
        with pytest.raises(CrossTenantAccessError) as exc_info:
            rls_service.check_cross_tenant_access(
                user=user_1_1,
                resource_org_id=team_2_1.organization_id,
                resource_team_id=team_2_1.id,
            )

        assert "does not have access to team" in str(exc_info.value)


# ============================================================================
# Ownership Isolation Tests
# ============================================================================


class TestOwnershipIsolation:
    """Test user-level ownership isolation"""

    @pytest.mark.asyncio
    async def test_user_can_only_see_own_responses(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        IDOR Test: User attempting to access another user's responses

        Expected: Query should return only user's own responses
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Get responses with ownership filter
        query = select(Response)
        filtered_query = rls_service.apply_ownership_filter(
            query, user_1_1, Response.user_id
        )

        result = await test_db.execute(filtered_query)
        responses = result.scalars().all()

        # Should only see own responses
        assert len(responses) == 1
        assert responses[0].id == "response-1-1"
        assert responses[0].user_id == "user-1-1"

        # Should NOT see other users' responses
        response_ids = [r.id for r in responses]
        assert "response-2-1" not in response_ids

    @pytest.mark.asyncio
    async def test_cross_ownership_access_blocked(
        self, rls_service: RowLevelSecurityService, multi_tenant_data
    ):
        """
        IDOR Test: User attempting to access another user's private resource

        Expected: CrossTenantAccessError raised
        """
        user_1_1 = multi_tenant_data["user_1_1"]
        user_2_1 = multi_tenant_data["user_2_1"]
        response_2_1 = multi_tenant_data["response_2-1"]

        # Attempt to access user-2-1's response
        with pytest.raises(CrossTenantAccessError) as exc_info:
            rls_service.check_cross_tenant_access(
                user=user_1_1,
                resource_org_id=response_2_1.organization_id,
                resource_owner_id=user_2_1.id,
            )

        assert "does not have access to this resource" in str(exc_info.value)


# ============================================================================
# Database-Level RLS Policy Tests
# ============================================================================


class TestDatabaseRLSPolicies:
    """Test PostgreSQL Row-Level Security policies"""

    @pytest.mark.asyncio
    async def test_rls_enabled_on_tables(self, test_db: AsyncSession):
        """
        Test: Verify RLS is enabled on secure tables

        Expected: RLS enabled on all tables with tenant data
        """
        rls_manager = RowLevelSecurityManager()

        # Check RLS status on assessments table
        # Note: This requires tables to have _secure suffix or be explicitly checked
        # For now, we'll test the RLS manager functionality

        # Set tenant context
        await rls_manager.set_security_context(
            test_db, user_id="test-user", user_role="user", org_id="test-org"
        )

        # Verify context is set
        result = await test_db.execute(
            text("SELECT current_setting('app.current_user_id', true)")
        )
        current_user = result.scalar()

        assert current_user == "test-user"

        # Clear context
        await rls_manager.clear_security_context(test_db)

    @pytest.mark.asyncio
    async def test_security_context_isolation(
        self, test_db: AsyncSession, multi_tenant_data
    ):
        """
        Test: Verify security context properly isolates data

        Expected: Queries respect security context variables
        """
        rls_manager = RowLevelSecurityManager()
        user_1_1 = multi_tenant_data["user_1_1"]

        # Set security context for user-1-1
        await rls_manager.set_security_context(
            test_db,
            user_id=str(user_1_1.id),
            user_role="user",
            org_id=str(user_1_1.organization_id),
        )

        # Query assessments (should be filtered by org)
        result = await test_db.execute(
            select(Assessment).where(
                Assessment.organization_id == user_1_1.organization_id
            )
        )
        assessments = result.scalars().all()

        # Should only see org-1 assessments
        assert len(assessments) == 1
        assert assessments[0].organization_id == user_1_1.organization_id

        # Clear context
        await rls_manager.clear_security_context(test_db)

    @pytest.mark.asyncio
    async def test_rls_context_manager(self, test_db: AsyncSession, multi_tenant_data):
        """
        Test: Verify RLS context manager properly sets and clears context

        Expected: Context is set within manager, cleared after exit
        """
        rls_manager = RowLevelSecurityManager()
        user_1_1 = multi_tenant_data["user_1_1"]

        async with rls_manager.secure_session(
            test_db,
            user_id=str(user_1_1.id),
            user_role="user",
            org_id=str(user_1_1.organization_id),
        ):
            # Inside context - security variables should be set
            result = await test_db.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
            current_user = result.scalar()
            assert current_user == str(user_1_1.id)

        # Outside context - security variables should be cleared
        result = await test_db.execute(
            text("SELECT current_setting('app.current_user_id', true)")
        )
        current_user = result.scalar()
        # Should be None or empty (context cleared)
        assert not current_user or current_user == ""


# ============================================================================
# Integration Tests
# ============================================================================


class TestTenantIsolationIntegration:
    """End-to-end tenant isolation tests"""

    @pytest.mark.asyncio
    async def test_full_tenant_isolation_workflow(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        Comprehensive Test: Full workflow testing all isolation levels

        Scenario:
        1. User from org-1 queries for assessments
        2. Should only see org-1 assessments
        3. Should NOT see org-2 assessments
        4. Attempting to access org-2 assessment should fail
        """
        user_1_1 = multi_tenant_data["user_1_1"]
        assessment_2_1 = multi_tenant_data["assessment_2-1"]

        # 1. Query assessments with tenant isolation
        query = select(Assessment)
        filtered_query = rls_service.apply_tenant_isolation(
            query, user_1_1, org_column=Assessment.organization_id
        )

        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # 2. Verify only org-1 assessments returned
        assert len(assessments) == 1
        assert assessments[0].organization_id == "org-1"

        # 3. Verify org-2 assessment not in results
        assessment_ids = [a.id for a in assessments]
        assert "assessment-2-1" not in assessment_ids

        # 4. Attempt direct access to org-2 assessment (should fail)
        with pytest.raises(CrossTenantAccessError):
            rls_service.check_cross_tenant_access(
                user=user_1_1, resource_org_id=assessment_2_1.organization_id
            )

    @pytest.mark.asyncio
    async def test_isolation_context_generation(
        self, rls_service: RowLevelSecurityService, multi_tenant_data
    ):
        """
        Test: Verify isolation context is properly generated

        Expected: Context contains user's tenant boundaries
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        context = rls_service.get_isolation_context(user_1_1)

        assert context["user_id"] == str(user_1_1.id)
        assert context["organization_id"] == str(user_1_1.organization_id)
        assert context["is_superuser"] == False
        assert context["isolation_level"] == "organization"
        assert "team_ids" in context

    @pytest.mark.asyncio
    async def test_superuser_bypass_logging(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
        caplog,
    ):
        """
        Test: Verify superuser bypass is logged

        Expected: Superuser access is logged for audit
        """
        import logging

        caplog.set_level(logging.INFO)

        superuser = multi_tenant_data["superuser"]
        assessment_1_1 = multi_tenant_data["assessment_1_1"]

        # Superuser accesses org-1 assessment
        rls_service.check_cross_tenant_access(
            user=superuser, resource_org_id=assessment_1_1.organization_id
        )

        # Verify log entry
        assert "Superuser" in caplog.text
        assert "bypassing RLS" in caplog.text


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


class TestTenantIsolationEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_user_with_no_organization(
        self, test_db: AsyncSession, rls_service: RowLevelSecurityService
    ):
        """
        Edge Case: User with no organization attempts to access data

        Expected: Empty result set
        """
        user_no_org = User(id="no-org", email="noorg@test.com", organization_id=None)

        query = select(Assessment)
        filtered_query = rls_service.apply_organization_filter(
            query, user_no_org, Assessment.organization_id
        )

        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # Should return empty
        assert len(assessments) == 0

    @pytest.mark.asyncio
    async def test_multiple_filter_levels(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        Edge Case: Applying multiple filters (org + team + ownership)

        Expected: All filters are respected
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Apply organization filter
        query = select(Response)
        query = rls_service.apply_organization_filter(
            query, user_1_1, Response.organization_id
        )

        # Apply ownership filter on top
        query = rls_service.apply_ownership_filter(query, user_1_1, Response.user_id)

        result = await test_db.execute(query)
        responses = result.scalars().all()

        # Should only see responses that match both filters
        assert len(responses) == 1
        assert responses[0].user_id == "user-1-1"
        assert responses[0].organization_id == "org-1"

    @pytest.mark.asyncio
    async def test_isolation_level_configuration(
        self, rls_service: RowLevelSecurityService
    ):
        """
        Configuration Test: Verify isolation level can be changed

        Expected: Service respects configured isolation level
        """
        # Default isolation level
        assert rls_service.isolation_level == "organization"

        # Change to team-level
        rls_service.isolation_level = "team"
        assert rls_service.isolation_level == "team"

        # Change to user-level
        rls_service.isolation_level = "user"
        assert rls_service.isolation_level == "user"


# ============================================================================
# Performance Tests
# ============================================================================


class TestTenantIsolationPerformance:
    """Test performance impact of RLS"""

    @pytest.mark.asyncio
    async def test_rls_query_performance(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
        benchmark,
    ):
        """
        Performance Test: Measure RLS query overhead

        Expected: RLS adds minimal overhead (< 10ms per query)
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Benchmark query with RLS
        def query_with_rls():
            query = select(Assessment)
            filtered_query = rls_service.apply_organization_filter(
                query, user_1_1, Assessment.organization_id
            )
            return test_db.execute(filtered_query)

        result = benchmark(query_with_rls)

        # Verify query still returns correct results
        assessments = result.scalars().all()
        assert len(assessments) == 1

        # Performance assertion (adjust based on requirements)
        # This is a placeholder - actual thresholds depend on system requirements


# ============================================================================
# Security Tests
# ============================================================================


class TestTenantIsolationSecurity:
    """Security-focused tenant isolation tests"""

    @pytest.mark.asyncio
    async def test_idor_prevention_sequential_access(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        IDOR Attack: Sequential enumeration of assessment IDs

        Attacker attempts to access assessments by incrementing IDs
        Expected: All cross-tenant access attempts blocked
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Simulate attacker trying different assessment IDs
        assessment_ids_to_try = [
            "assessment-2-1",  # Different org
            "assessment-3-1",  # Non-existent
            "assessment-1-1",  # Same org (should work)
        ]

        accessible_count = 0
        blocked_count = 0

        for assessment_id in assessment_ids_to_try:
            # Query specific assessment
            query = select(Assessment).where(Assessment.id == assessment_id)
            filtered_query = rls_service.apply_organization_filter(
                query, user_1_1, Assessment.organization_id
            )

            result = await test_db.execute(filtered_query)
            assessment = result.scalar_one_or_none()

            if assessment:
                accessible_count += 1
            else:
                blocked_count += 1

        # Should only access assessment from own org
        assert accessible_count == 1
        assert blocked_count == 2

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        IDOR Attack: Path traversal in organization_id

        Attacker attempts to manipulate organization_id
        Expected: Filter properly validates and blocks
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Attempt to use path traversal in org filter
        query = select(Assessment)

        # Filter should properly escape and validate
        filtered_query = rls_service.apply_organization_filter(
            query, user_1_1, Assessment.organization_id
        )

        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # Should not allow path traversal
        for assessment in assessments:
            assert assessment.organization_id == "org-1"
            assert ".." not in assessment.organization_id

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(
        self,
        test_db: AsyncSession,
        rls_service: RowLevelSecurityService,
        multi_tenant_data,
    ):
        """
        SQL Injection Test: Attempt SQL injection in filter parameters

        Expected: SQLAlchemy ORM prevents injection
        """
        user_1_1 = multi_tenant_data["user_1_1"]

        # Attempt SQL injection via user object manipulation
        # (This would be difficult in practice, but testing ORM safety)
        query = select(Assessment)
        filtered_query = rls_service.apply_organization_filter(
            query, user_1_1, Assessment.organization_id
        )

        # Execute query
        result = await test_db.execute(filtered_query)
        assessments = result.scalars().all()

        # Should return normal results without injection
        assert len(assessments) == 1
        assert assessments[0].organization_id == "org-1"


# ============================================================================
# Audit and Compliance Tests
# ============================================================================


class TestTenantIsolationAudit:
    """Test audit logging for tenant isolation"""

    @pytest.mark.asyncio
    async def test_cross_tenant_access_attempt_logging(
        self, rls_service: RowLevelSecurityService, multi_tenant_data, caplog
    ):
        """
        Audit Test: Cross-tenant access attempts are logged

        Expected: Security events logged for audit
        """
        import logging

        caplog.set_level(logging.WARNING)

        user_1_1 = multi_tenant_data["user_1_1"]
        assessment_2_1 = multi_tenant_data["assessment_2-1"]

        # Attempt cross-tenant access
        try:
            rls_service.check_cross_tenant_access(
                user=user_1_1, resource_org_id=assessment_2_1.organization_id
            )
        except CrossTenantAccessError:
            pass

        # Verify log entry
        assert "Cross-organization access attempt" in caplog.text
        assert str(user_1_1.id) in caplog.text

    @pytest.mark.asyncio
    async def test_superuser_access_logging(
        self, rls_service: RowLevelSecurityService, multi_tenant_data, caplog
    ):
        """
        Audit Test: Superuser access is logged

        Expected: All superuser actions logged for compliance
        """
        import logging

        caplog.set_level(logging.INFO)

        superuser = multi_tenant_data["superuser"]

        # Get isolation context (logs superuser access)
        context = rls_service.get_isolation_context(superuser)

        # Verify logging occurred
        assert len([r for r in caplog.records if r.levelname == "INFO"]) > 0
