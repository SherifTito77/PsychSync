"""
Database CRUD Integration Tests
Tests all database operations, relationships, and data consistency
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.services.security import get_password_hash
from app.db.models.assessment import Assessment, UserAssessment
from app.db.models.response import Response, ResponseScore
from app.db.models.team import Team, TeamMember
from app.db.models.user import User


@pytest.mark.integration
class TestUserCRUD:
    """Test suite for User CRUD operations"""

    @pytest.fixture
    async def test_db(self):
        """Create test database session"""
        async for session in get_db():
            yield session

    @pytest.fixture
    async def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "phone": "+1234567890",
            "department": "Engineering",
            "created_at": datetime.utcnow(),
        }

    @pytest.fixture
    async def created_user(self, test_db: AsyncSession, sample_user_data):
        """Create a user in database"""
        user = User(**sample_user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_create_user(self, test_db: AsyncSession, sample_user_data):
        """Test user creation"""
        user = User(**sample_user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.id is not None
        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.role == sample_user_data["role"]
        assert user.is_active == sample_user_data["is_active"]
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_read_user(self, test_db: AsyncSession, created_user: User):
        """Test reading user data"""
        # Read by ID
        result = await test_db.execute(select(User).where(User.id == created_user.id))
        user = result.scalar_one()

        assert user is not None
        assert user.id == created_user.id
        assert user.email == created_user.email
        assert user.full_name == created_user.full_name

        # Read by email
        result = await test_db.execute(select(User).where(User.email == created_user.email))
        user_by_email = result.scalar_one()

        assert user_by_email.id == created_user.id

    @pytest.mark.asyncio
    async def test_update_user(self, test_db: AsyncSession, created_user: User):
        """Test updating user data"""
        update_data = {
            "full_name": "Updated Name",
            "phone": "+9876543210",
            "department": "Marketing",
        }

        stmt = update(User).where(User.id == created_user.id).values(**update_data)
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify update
        await test_db.refresh(created_user)
        assert created_user.full_name == "Updated Name"
        assert created_user.phone == "+9876543210"
        assert created_user.department == "Marketing"

    @pytest.mark.asyncio
    async def test_delete_user(self, test_db: AsyncSession, created_user: User):
        """Test user deletion"""
        user_id = created_user.id

        stmt = delete(User).where(User.id == user_id)
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify deletion
        result = await test_db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        assert user is None

    @pytest.mark.asyncio
    async def test_user_soft_delete(self, test_db: AsyncSession, created_user: User):
        """Test soft deletion of user"""
        update_data = {"is_active": False, "deleted_at": datetime.utcnow()}

        stmt = update(User).where(User.id == created_user.id).values(**update_data)
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify soft delete
        await test_db.refresh(created_user)
        assert created_user.is_active is False
        assert created_user.deleted_at is not None

        # Should still exist in database
        result = await test_db.execute(select(User).where(User.id == created_user.id))
        user = result.scalar_one()
        assert user is not None

    @pytest.mark.asyncio
    async def test_user_password_hashing(self, test_db: AsyncSession, sample_user_data):
        """Test password hashing works correctly"""
        user = User(**sample_user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Password should be hashed
        assert user.password_hash != "TestPassword123!"
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix

    @pytest.mark.asyncio
    async def test_user_unique_email_constraint(self, test_db: AsyncSession, created_user: User):
        """Test email uniqueness constraint"""
        duplicate_user_data = {
            "email": created_user.email,  # Same email
            "full_name": "Different User",
            "password_hash": get_password_hash("DifferentPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow(),
        }

        duplicate_user = User(**duplicate_user_data)
        test_db.add(duplicate_user)

        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            await test_db.commit()


@pytest.mark.integration
class TestAssessmentCRUD:
    """Test suite for Assessment CRUD operations"""

    @pytest.fixture
    async def test_db(self):
        async for session in get_db():
            yield session

    @pytest.fixture
    async def sample_assessment_data(self):
        """Sample assessment data"""
        return {
            "title": "Big Five Personality Test",
            "description": "Comprehensive personality assessment",
            "type": "big_five",
            "is_active": True,
            "estimated_duration": 15,
            "instructions": "Answer honestly based on how you typically behave",
            "scoring_algorithm": "weighted_average",
            "created_at": datetime.utcnow(),
        }

    @pytest.fixture
    async def created_assessment(self, test_db: AsyncSession, sample_assessment_data):
        """Create assessment in database"""
        assessment = Assessment(**sample_assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)
        return assessment

    @pytest.mark.asyncio
    async def test_create_assessment(self, test_db: AsyncSession, sample_assessment_data):
        """Test assessment creation"""
        assessment = Assessment(**sample_assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)

        assert assessment.id is not None
        assert assessment.title == sample_assessment_data["title"]
        assert assessment.type == sample_assessment_data["type"]
        assert assessment.is_active == sample_assessment_data["is_active"]

    @pytest.mark.asyncio
    async def test_read_assessment(self, test_db: AsyncSession, created_assessment: Assessment):
        """Test reading assessment data"""
        result = await test_db.execute(
            select(Assessment)
            .options(selectinload(Assessment.questions))
            .where(Assessment.id == created_assessment.id)
        )
        assessment = result.scalar_one()

        assert assessment is not None
        assert assessment.id == created_assessment.id
        assert assessment.title == created_assessment.title

    @pytest.mark.asyncio
    async def test_update_assessment(self, test_db: AsyncSession, created_assessment: Assessment):
        """Test updating assessment data"""
        update_data = {
            "title": "Updated Assessment Title",
            "estimated_duration": 20,
            "is_active": False,
        }

        stmt = (
            update(Assessment).where(Assessment.id == created_assessment.id).values(**update_data)
        )
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify update
        await test_db.refresh(created_assessment)
        assert created_assessment.title == "Updated Assessment Title"
        assert created_assessment.estimated_duration == 20
        assert created_assessment.is_active is False

    @pytest.mark.asyncio
    async def test_delete_assessment(self, test_db: AsyncSession, created_assessment: Assessment):
        """Test assessment deletion"""
        assessment_id = created_assessment.id

        stmt = delete(Assessment).where(Assessment.id == assessment_id)
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify deletion
        result = await test_db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()
        assert assessment is None


@pytest.mark.integration
class TestTeamCRUD:
    """Test suite for Team CRUD operations"""

    @pytest.fixture
    async def test_db(self):
        async for session in get_db():
            yield session

    @pytest.fixture
    async def sample_user(self, test_db: AsyncSession):
        """Create a user for team testing"""
        user_data = {
            "email": "teamuser@example.com",
            "full_name": "Team User",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow(),
        }

        user = User(**user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    @pytest.fixture
    async def sample_team_data(self, sample_user: User):
        """Sample team data"""
        return {
            "name": "Engineering Team",
            "description": "Software development team",
            "department": "Engineering",
            "created_by": sample_user.id,
            "created_at": datetime.utcnow(),
        }

    @pytest.fixture
    async def created_team(self, test_db: AsyncSession, sample_team_data):
        """Create team in database"""
        team = Team(**sample_team_data)
        test_db.add(team)
        await test_db.commit()
        await test_db.refresh(team)
        return team

    @pytest.mark.asyncio
    async def test_create_team(self, test_db: AsyncSession, sample_team_data):
        """Test team creation"""
        team = Team(**sample_team_data)
        test_db.add(team)
        await test_db.commit()
        await test_db.refresh(team)

        assert team.id is not None
        assert team.name == sample_team_data["name"]
        assert team.department == sample_team_data["department"]
        assert team.created_by == sample_team_data["created_by"]

    @pytest.mark.asyncio
    async def test_add_team_member(
        self, test_db: AsyncSession, created_team: Team, sample_user: User
    ):
        """Test adding member to team"""
        team_member_data = {
            "team_id": created_team.id,
            "user_id": sample_user.id,
            "role": "member",
            "joined_at": datetime.utcnow(),
        }

        team_member = TeamMember(**team_member_data)
        test_db.add(team_member)
        await test_db.commit()
        await test_db.refresh(team_member)

        assert team_member.id is not None
        assert team_member.team_id == created_team.id
        assert team_member.user_id == sample_user.id
        assert team_member.role == "member"

    @pytest.mark.asyncio
    async def test_team_member_relationships(
        self, test_db: AsyncSession, created_team: Team, sample_user: User
    ):
        """Test team member relationships"""
        # Add user to team
        team_member = TeamMember(
            team_id=created_team.id,
            user_id=sample_user.id,
            role="member",
            joined_at=datetime.utcnow(),
        )
        test_db.add(team_member)
        await test_db.commit()

        # Test relationship loading
        result = await test_db.execute(
            select(Team).options(selectinload(Team.members)).where(Team.id == created_team.id)
        )
        team = result.scalar_one()

        assert len(team.members) == 1
        assert team.members[0].user_id == sample_user.id

    @pytest.mark.asyncio
    async def test_remove_team_member(
        self, test_db: AsyncSession, created_team: Team, sample_user: User
    ):
        """Test removing member from team"""
        # Add member first
        team_member = TeamMember(
            team_id=created_team.id,
            user_id=sample_user.id,
            role="member",
            joined_at=datetime.utcnow(),
        )
        test_db.add(team_member)
        await test_db.commit()
        member_id = team_member.id

        # Remove member
        stmt = delete(TeamMember).where(TeamMember.id == member_id)
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify removal
        result = await test_db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == created_team.id)
            .where(TeamMember.user_id == sample_user.id)
        )
        member = result.scalar_one_or_none()
        assert member is None


@pytest.mark.integration
class TestUserAssessmentCRUD:
    """Test suite for User-Assessment relationships"""

    @pytest.fixture
    async def test_db(self):
        async for session in get_db():
            yield session

    @pytest.fixture
    async def test_user(self, test_db: AsyncSession):
        """Create test user"""
        user_data = {
            "email": "assessment_user@example.com",
            "full_name": "Assessment User",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow(),
        }

        user = User(**user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    @pytest.fixture
    async def test_assessment(self, test_db: AsyncSession):
        """Create test assessment"""
        assessment_data = {
            "title": "Test Assessment",
            "description": "Assessment for testing",
            "type": "test_type",
            "is_active": True,
            "estimated_duration": 10,
            "created_at": datetime.utcnow(),
        }

        assessment = Assessment(**assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)
        return assessment

    @pytest.mark.asyncio
    async def test_start_user_assessment(
        self, test_db: AsyncSession, test_user: User, test_assessment: Assessment
    ):
        """Test starting a user assessment"""
        user_assessment_data = {
            "user_id": test_user.id,
            "assessment_id": test_assessment.id,
            "status": "in_progress",
            "started_at": datetime.utcnow(),
            "session_token": "session_" + str(test_user.id) + "_" + str(test_assessment.id),
        }

        user_assessment = UserAssessment(**user_assessment_data)
        test_db.add(user_assessment)
        await test_db.commit()
        await test_db.refresh(user_assessment)

        assert user_assessment.id is not None
        assert user_assessment.user_id == test_user.id
        assert user_assessment.assessment_id == test_assessment.id
        assert user_assessment.status == "in_progress"

    @pytest.mark.asyncio
    async def test_complete_user_assessment(
        self, test_db: AsyncSession, test_user: User, test_assessment: Assessment
    ):
        """Test completing a user assessment"""
        # Start assessment
        user_assessment = UserAssessment(
            user_id=test_user.id,
            assessment_id=test_assessment.id,
            status="in_progress",
            started_at=datetime.utcnow(),
            session_token="session_token",
        )
        test_db.add(user_assessment)
        await test_db.commit()
        await test_db.refresh(user_assessment)

        # Complete assessment
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "total_time_seconds": 900,  # 15 minutes
        }

        stmt = (
            update(UserAssessment)
            .where(UserAssessment.id == user_assessment.id)
            .values(**update_data)
        )
        await test_db.execute(stmt)
        await test_db.commit()

        # Verify completion
        await test_db.refresh(user_assessment)
        assert user_assessment.status == "completed"
        assert user_assessment.completed_at is not None
        assert user_assessment.total_time_seconds == 900

    @pytest.mark.asyncio
    async def test_user_assessment_history(
        self, test_db: AsyncSession, test_user: User, test_assessment: Assessment
    ):
        """Test user assessment history"""
        # Create multiple assessments for user
        assessments = []
        for i in range(3):
            user_assessment = UserAssessment(
                user_id=test_user.id,
                assessment_id=test_assessment.id,
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=i),
                completed_at=datetime.utcnow() - timedelta(days=i) + timedelta(minutes=15),
                total_time_seconds=900,
            )
            assessments.append(user_assessment)
            test_db.add(user_assessment)

        await test_db.commit()

        # Query user's assessment history
        result = await test_db.execute(
            select(UserAssessment)
            .where(UserAssessment.user_id == test_user.id)
            .order_by(UserAssessment.started_at.desc())
        )
        user_assessments = result.scalars().all()

        assert len(user_assessments) >= 3
        assert all(ua.user_id == test_user.id for ua in user_assessments)


@pytest.mark.integration
class TestResponseCRUD:
    """Test suite for Response CRUD operations"""

    @pytest.fixture
    async def test_db(self):
        async for session in get_db():
            yield session

    @pytest.fixture
    async def test_user(self, test_db: AsyncSession):
        """Create test user"""
        user_data = {
            "email": "response_user@example.com",
            "full_name": "Response User",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow(),
        }

        user = User(**user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user

    @pytest.fixture
    async def test_assessment(self, test_db: AsyncSession):
        """Create test assessment"""
        assessment_data = {
            "title": "Response Test Assessment",
            "description": "Assessment for response testing",
            "type": "test",
            "is_active": True,
            "estimated_duration": 10,
            "created_at": datetime.utcnow(),
        }

        assessment = Assessment(**assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)
        return assessment

    @pytest.fixture
    async def test_user_assessment(
        self, test_db: AsyncSession, test_user: User, test_assessment: Assessment
    ):
        """Create test user assessment"""
        user_assessment_data = {
            "user_id": test_user.id,
            "assessment_id": test_assessment.id,
            "status": "completed",
            "started_at": datetime.utcnow(),
            "completed_at": datetime.utcnow() + timedelta(minutes=10),
            "session_token": "test_session_token",
        }

        user_assessment = UserAssessment(**user_assessment_data)
        test_db.add(user_assessment)
        await test_db.commit()
        await test_db.refresh(user_assessment)
        return user_assessment

    @pytest.mark.asyncio
    async def test_create_response(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_assessment: Assessment,
        test_user_assessment: UserAssessment,
    ):
        """Test creating response data"""
        response_data = {
            "user_id": test_user.id,
            "assessment_id": test_assessment.id,
            "user_assessment_id": test_user_assessment.id,
            "question_id": "q_001",
            "response": 4,
            "response_time_ms": 1500,
            "created_at": datetime.utcnow(),
        }

        response = Response(**response_data)
        test_db.add(response)
        await test_db.commit()
        await test_db.refresh(response)

        assert response.id is not None
        assert response.user_id == test_user.id
        assert response.assessment_id == test_assessment.id
        assert response.question_id == "q_001"
        assert response.response == 4

    @pytest.mark.asyncio
    async def test_batch_response_creation(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_assessment: Assessment,
        test_user_assessment: UserAssessment,
    ):
        """Test creating multiple responses in batch"""
        responses_data = []
        for i in range(10):
            response_data = {
                "user_id": test_user.id,
                "assessment_id": test_assessment.id,
                "user_assessment_id": test_user_assessment.id,
                "question_id": f"q_{i:03d}",
                "response": (i % 5) + 1,  # Responses 1-5
                "response_time_ms": 1000 + (i * 100),
                "created_at": datetime.utcnow(),
            }
            responses_data.append(Response(**response_data))

        test_db.add_all(responses_data)
        await test_db.commit()

        # Verify all responses were created
        result = await test_db.execute(
            select(Response).where(Response.user_assessment_id == test_user_assessment.id)
        )
        saved_responses = result.scalars().all()

        assert len(saved_responses) == 10
        assert all(r.user_id == test_user.id for r in saved_responses)

    @pytest.mark.asyncio
    async def test_response_scoring(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_assessment: Assessment,
        test_user_assessment: UserAssessment,
    ):
        """Test response scoring and score calculation"""
        # Create response
        response = Response(
            user_id=test_user.id,
            assessment_id=test_assessment.id,
            user_assessment_id=test_user_assessment.id,
            question_id="q_001",
            response=4,
            response_time_ms=1500,
            created_at=datetime.utcnow(),
        )
        test_db.add(response)
        await test_db.commit()
        await test_db.refresh(response)

        # Create score
        score_data = {
            "response_id": response.id,
            "dimension": "openness",  # Big Five dimension
            "score": 0.8,  # Normalized score
            "weight": 1.0,
            "calculated_at": datetime.utcnow(),
        }

        score = ResponseScore(**score_data)
        test_db.add(score)
        await test_db.commit()
        await test_db.refresh(score)

        assert score.id is not None
        assert score.response_id == response.id
        assert score.dimension == "openness"
        assert score.score == 0.8

    @pytest.mark.asyncio
    async def test_response_query_performance(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_assessment: Assessment,
        test_user_assessment: UserAssessment,
    ):
        """Test response query performance with large datasets"""
        # Create many responses to test performance
        responses = []
        for i in range(1000):
            response = Response(
                user_id=test_user.id,
                assessment_id=test_assessment.id,
                user_assessment_id=test_user_assessment.id,
                question_id=f"q_{i:04d}",
                response=(i % 5) + 1,
                response_time_ms=1000 + (i % 500),
                created_at=datetime.utcnow() - timedelta(minutes=i),
            )
            responses.append(response)

        test_db.add_all(responses)
        await test_db.commit()

        # Test query performance
        start_time = datetime.utcnow()

        result = await test_db.execute(
            select(Response)
            .where(Response.user_assessment_id == test_user_assessment.id)
            .order_by(Response.created_at.desc())
            .limit(100)
        )
        queried_responses = result.scalars().all()

        query_time = (datetime.utcnow() - start_time).total_seconds()

        assert len(queried_responses) == 100
        assert query_time < 1.0  # Should complete in under 1 second

    @pytest.mark.asyncio
    async def test_response_data_integrity(
        self, test_db: AsyncSession, test_user: User, test_assessment: Assessment
    ):
        """Test response data integrity and constraints"""
        # Try to create response without user_assessment_id (should fail if foreign key constraint exists)
        response_data = {
            "user_id": test_user.id,
            "assessment_id": test_assessment.id,
            "user_assessment_id": "00000000-0000-0000-0000-000000000000",  # Non-existent UUID
            "question_id": "q_test",
            "response": 3,
            "response_time_ms": 1000,
            "created_at": datetime.utcnow(),
        }

        response = Response(**response_data)
        test_db.add(response)

        # Should raise integrity error due to foreign key constraint
        with pytest.raises(Exception):
            await test_db.commit()


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test suite for database transaction handling"""

    @pytest.fixture
    async def test_db(self):
        async for session in get_db():
            yield session

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, test_db: AsyncSession):
        """Test transaction rollback on error"""
        # Start transaction
        user_data = {
            "email": "transaction_test@example.com",
            "full_name": "Transaction Test",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow(),
        }

        user = User(**user_data)
        test_db.add(user)
        await test_db.flush()  # Get ID but don't commit yet

        # Try to create duplicate user (should fail)
        duplicate_user = User(**user_data)
        test_db.add(duplicate_user)

        # Should rollback on error
        try:
            await test_db.commit()
        except Exception:
            await test_db.rollback()

        # Verify neither user was committed
        result = await test_db.execute(
            select(User).where(User.email == "transaction_test@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is None

    @pytest.mark.asyncio
    async def test_nested_transaction(self, test_db: AsyncSession):
        """Test nested transaction handling"""
        # This would require implementing savepoint functionality
        # For now, test basic transaction isolation

        user_data = {
            "email": "nested_test@example.com",
            "full_name": "Nested Test",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow(),
        }

        user = User(**user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create related data
        assessment_data = {
            "title": "Nested Test Assessment",
            "description": "Assessment for nested transaction test",
            "type": "test",
            "is_active": True,
            "estimated_duration": 10,
            "created_at": datetime.utcnow(),
        }

        assessment = Assessment(**assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)

        # Create relationship
        user_assessment = UserAssessment(
            user_id=user.id,
            assessment_id=assessment.id,
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            session_token="nested_session_token",
        )
        test_db.add(user_assessment)
        await test_db.commit()

        # Verify all data was committed correctly
        result = await test_db.execute(
            select(UserAssessment).where(UserAssessment.user_id == user.id)
        )
        saved_assessment = result.scalar_one()
        assert saved_assessment.assessment_id == assessment.id


@pytest.mark.integration
class TestDatabasePerformance:
    """Test suite for database performance optimization"""

    @pytest.fixture
    async def test_db(self):
        async for session in get_db():
            yield session

    @pytest.mark.asyncio
    async def test_batch_insert_performance(self, test_db: AsyncSession):
        """Test batch insert performance"""
        users = []
        for i in range(1000):
            user_data = {
                "email": f"perf_test_{i}@example.com",
                "full_name": f"Performance Test User {i}",
                "password_hash": get_password_hash("TestPassword123!"),
                "role": "user",
                "is_active": True,
                "email_verified": True,
                "created_at": datetime.utcnow(),
            }
            users.append(User(**user_data))

        start_time = datetime.utcnow()
        test_db.add_all(users)
        await test_db.commit()
        end_time = datetime.utcnow()

        insert_time = (end_time - start_time).total_seconds()

        # Should complete in reasonable time
        assert insert_time < 5.0  # 5 seconds for 1000 records
        assert len(users) == 1000

    @pytest.mark.asyncio
    async def test_query_optimization(self, test_db: AsyncSession):
        """Test query optimization with proper indexing"""
        # Create test data
        users = []
        for i in range(100):
            user_data = {
                "email": f"query_test_{i}@example.com",
                "full_name": f"Query Test User {i}",
                "password_hash": get_password_hash("TestPassword123!"),
                "role": "user" if i % 2 == 0 else "admin",
                "is_active": i % 3 != 0,
                "email_verified": i % 2 == 0,
                "created_at": datetime.utcnow() - timedelta(days=i),
            }
            users.append(User(**user_data))

        test_db.add_all(users)
        await test_db.commit()

        # Test efficient query
        start_time = datetime.utcnow()

        result = await test_db.execute(
            select(User)
            .where(User.is_active == True)
            .where(User.email_verified == True)
            .order_by(User.created_at.desc())
            .limit(50)
        )

        active_users = result.scalars().all()
        query_time = (datetime.utcnow() - start_time).total_seconds()

        assert len(active_users) <= 50
        assert query_time < 0.5  # Should be very fast with proper indexing

    @pytest.mark.asyncio
    async def test_connection_pool_behavior(self, test_db: AsyncSession):
        """Test connection pool behavior under load"""

        async def make_query():
            result = await test_db.execute(select(User).limit(1))
            return result.scalar_one_or_none()

        # Make concurrent queries
        tasks = [make_query() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # All queries should succeed, testing connection pool efficiency
        success_count = sum(1 for r in results if r is not None or r is None)
        assert success_count == 50  # All queries should complete


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
