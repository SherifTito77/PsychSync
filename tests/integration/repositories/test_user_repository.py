"""
Integration Tests for UserRepository

Tests the UserRepository implementation with real database interactions.
These are integration tests that require a test database.
"""

from uuid import uuid4

import pytest

from app.db.models.user import UserRole
from app.domain.value_objects.password import Password
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserRepository:
    """Test UserRepository with database"""

    # ========================================================================
    # BASIC CRUD TESTS
    # ========================================================================

    async def test_create_user(self, test_db):
        """Should create user in database"""
        repo = UserRepository(db=test_db)

        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )

        user = await repo.create(user_data, password_hash=password_hash)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False

    async def test_get_user_by_id(self, test_db):
        """Should retrieve user by ID"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        created_user = await repo.create(user_data, password_hash=password_hash)

        # Get user
        retrieved_user = await repo.get(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "test@example.com"

    async def test_get_user_by_id_not_found(self, test_db):
        """Should return None for non-existent user"""
        repo = UserRepository(db=test_db)

        user = await repo.get(uuid4())

        assert user is None

    async def test_update_user(self, test_db):
        """Should update user"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Update user
        update_data = UserUpdate(full_name="Updated Name")
        updated_user = await repo.update(user.id, update_data)

        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "test@example.com"  # Unchanged

    async def test_delete_user(self, test_db):
        """Should delete user"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Delete user
        result = await repo.delete(user.id)

        assert result is True

        # Verify deleted
        deleted_user = await repo.get(user.id)
        assert deleted_user is None

    async def test_delete_user_not_found(self, test_db):
        """Should return False when deleting non-existent user"""
        repo = UserRepository(db=test_db)

        result = await repo.delete(uuid4())

        assert result is False

    # ========================================================================
    # EMAIL LOOKUP TESTS
    # ========================================================================

    async def test_get_by_email(self, test_db):
        """Should find user by email"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        await repo.create(user_data, password_hash=password_hash)

        # Find by email
        user = await repo.get_by_email("test@example.com")

        assert user is not None
        assert user.email == "test@example.com"

    async def test_get_by_email_case_insensitive(self, test_db):
        """Should find email regardless of case"""
        repo = UserRepository(db=test_db)

        # Create user with lowercase email
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        await repo.create(user_data, password_hash=password_hash)

        # Find with uppercase
        user = await repo.get_by_email("TEST@EXAMPLE.COM")

        assert user is not None
        assert user.email == "test@example.com"

    async def test_get_by_email_not_found(self, test_db):
        """Should return None for non-existent email"""
        repo = UserRepository(db=test_db)

        user = await repo.get_by_email("nonexistent@example.com")

        assert user is None

    # ========================================================================
    # EMAIL EXISTS TESTS
    # ========================================================================

    async def test_email_exists_true(self, test_db):
        """Should return True when email exists"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        await repo.create(user_data, password_hash=password_hash)

        # Check exists
        exists = await repo.email_exists("test@example.com")

        assert exists is True

    async def test_email_exists_false(self, test_db):
        """Should return False when email doesn't exist"""
        repo = UserRepository(db=test_db)

        exists = await repo.email_exists("nonexistent@example.com")

        assert exists is False

    async def test_email_exists_exclude_id(self, test_db):
        """Should exclude user ID when checking existence"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Check exists excluding the same user (should be False)
        exists = await repo.email_exists("test@example.com", exclude_id=user.id)

        assert exists is False

        # Check exists excluding different user (should be True)
        different_id = uuid4()
        exists = await repo.email_exists("test@example.com", exclude_id=different_id)

        assert exists is True

    # ========================================================================
    # LIST AND FILTER TESTS
    # ========================================================================

    async def test_list_users(self, test_db):
        """Should list all users with pagination"""
        repo = UserRepository(db=test_db)

        # Create multiple users
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        for i in range(5):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            await repo.create(user_data, password_hash=password_hash)

        # List users
        users, total = await repo.list(skip=0, limit=10)

        assert len(users) == 5
        assert total == 5

    async def test_list_users_with_pagination(self, test_db):
        """Should paginate user list"""
        repo = UserRepository(db=test_db)

        # Create multiple users
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        for i in range(15):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            await repo.create(user_data, password_hash=password_hash)

        # First page
        users1, total1 = await repo.list(skip=0, limit=10)
        assert len(users1) == 10
        assert total1 == 15

        # Second page
        users2, total2 = await repo.list(skip=10, limit=10)
        assert len(users2) == 5
        assert total2 == 15

    async def test_list_users_with_filters(self, test_db):
        """Should filter users by field"""
        repo = UserRepository(db=test_db)

        # Create users with different statuses
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        for i in range(5):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            user = await repo.create(user_data, password_hash=password_hash)
            # Deactivate even-numbered users
            if i % 2 == 0:
                user.is_active = False
                test_db.add(user)
                await test_db.commit()

        # Filter active users
        users, total = await repo.list(skip=0, limit=10, filters={"is_active": True})

        assert len(users) == 2  # Users 1 and 3
        assert all(u.is_active for u in users)

    async def test_list_by_organization(self, test_db):
        """Should list users by organization"""
        repo = UserRepository(db=test_db)

        org_id = uuid4()

        # Create users in organization
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            user = await repo.create(user_data, password_hash=password_hash)
            user.organization_id = org_id
            test_db.add(user)
            await test_db.commit()

        # List by organization
        users, total = await repo.list_by_organization(org_id)

        assert len(users) == 3
        assert total == 3
        assert all(u.organization_id == org_id for u in users)

    async def test_search_users(self, test_db):
        """Should search users by email or name"""
        repo = UserRepository(db=test_db)

        # Create users
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data1 = UserCreate(
            email="john.doe@example.com", full_name="John Doe", password="SecureP@ss99!"
        )
        user_data2 = UserCreate(
            email="jane.smith@example.com",
            full_name="Jane Smith",
            password="SecureP@ss99!",
        )
        await repo.create(user_data1, password_hash=password_hash)
        await repo.create(user_data2, password_hash=password_hash)

        # Search by name
        users, total = await repo.search("John")

        assert len(users) == 1
        assert users[0].full_name == "John Doe"
        assert total == 1

        # Search by email
        users, total = await repo.search("jane")

        assert len(users) == 1
        assert users[0].email == "jane.smith@example.com"

    # ========================================================================
    # STATUS OPERATIONS TESTS
    # ========================================================================

    async def test_activate_user(self, test_db):
        """Should activate user"""
        repo = UserRepository(db=test_db)

        # Create inactive user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)
        user.is_active = False
        test_db.add(user)
        await test_db.commit()

        # Activate
        await repo.activate(user.id)

        # Refresh and check
        await test_db.refresh(user)
        assert user.is_active is True

    async def test_deactivate_user(self, test_db):
        """Should deactivate user"""
        repo = UserRepository(db=test_db)

        # Create active user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Deactivate
        await repo.deactivate(user.id)

        # Refresh and check
        await test_db.refresh(user)
        assert user.is_active is False

    async def test_verify_email(self, test_db):
        """Should mark email as verified"""
        repo = UserRepository(db=test_db)

        # Create unverified user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Verify email
        await repo.verify_email(user.id)

        # Refresh and check
        await test_db.refresh(user)
        assert user.is_verified is True

    # ========================================================================
    # PASSWORD OPERATIONS TESTS
    # ========================================================================

    async def test_update_password(self, test_db):
        """Should update user password"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)
        old_hash = user.password_hash

        # Update password
        new_hash = Password.create(plaintext="NewP@ss99!").hash_value
        await repo.update_password(user.id, new_hash)

        # Refresh and check
        await test_db.refresh(user)
        assert user.password_hash != old_hash
        assert user.password_hash == new_hash

    # ========================================================================
    # ROLE OPERATIONS TESTS
    # ========================================================================

    async def test_set_role(self, test_db):
        """Should set user role"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Set role
        await repo.set_role(user.id, UserRole.ADMIN)

        # Refresh and check
        await test_db.refresh(user)
        assert user.role == UserRole.ADMIN

    async def test_make_superuser(self, test_db):
        """Should make user superuser"""
        repo = UserRepository(db=test_db)

        # Create user
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="SecureP@ss99!"
        )
        user = await repo.create(user_data, password_hash=password_hash)

        # Make superuser
        await repo.make_superuser(user.id)

        # Refresh and check
        await test_db.refresh(user)
        assert user.is_superuser is True

    # ========================================================================
    # BATCH OPERATIONS TESTS
    # ========================================================================

    async def test_bulk_create(self, test_db):
        """Should create multiple users at once"""
        repo = UserRepository(db=test_db)

        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        users_data = [
            UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            for i in range(5)
        ]

        users = await repo.bulk_create(users_data, password_hash=password_hash)

        assert len(users) == 5

        # Verify in database
        for user in users:
            assert user.id is not None

    async def test_bulk_activate(self, test_db):
        """Should activate multiple users"""
        repo = UserRepository(db=test_db)

        # Create inactive users
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_ids = []
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            user = await repo.create(user_data, password_hash=password_hash)
            user.is_active = False
            test_db.add(user)
            await test_db.commit()
            user_ids.append(user.id)

        # Bulk activate
        await repo.bulk_activate(user_ids)

        # Verify all activated
        for user_id in user_ids:
            user = await repo.get(user_id)
            assert user.is_active is True

    async def test_bulk_deactivate(self, test_db):
        """Should deactivate multiple users"""
        repo = UserRepository(db=test_db)

        # Create active users
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        user_ids = []
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            user = await repo.create(user_data, password_hash=password_hash)
            user_ids.append(user.id)

        # Bulk deactivate
        await repo.bulk_deactivate(user_ids)

        # Verify all deactivated
        for user_id in user_ids:
            user = await repo.get(user_id)
            assert user.is_active is False

    # ========================================================================
    # COUNT TESTS
    # ========================================================================

    async def test_count_total(self, test_db):
        """Should count total users"""
        repo = UserRepository(db=test_db)

        # Create users
        password_hash = Password.create(plaintext="SecureP@ss99!").hash_value
        for i in range(7):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            await repo.create(user_data, password_hash=password_hash)

        # Count
        count = await repo.count({})

        assert count == 7

    async def test_count_by_status(self, test_db):
        """Should count users by status"""
        repo = UserRepository(db=test_db)

        # Create users with different statuses
        password_hash = Password.create(plaintext("SecureP@ss99!").hash_value)
        for i in range(5):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            user = await repo.create(user_data, password_hash=password_hash)
            if i % 2 == 0:
                user.is_active = False
                test_db.add(user)
                await test_db.commit()

        # Count active
        active_count = await repo.count_by_status(is_active=True)
        assert active_count == 2  # Users 1 and 3

        # Count inactive
        inactive_count = await repo.count_by_status(is_active=False)
        assert inactive_count == 3  # Users 0, 2, and 4

    async def test_count_by_role(self, test_db):
        """Should count users by role"""
        repo = UserRepository(db=test_db)

        # Create users with different roles
        password_hash = Password.create(plaintext("SecureP@ss99!").hash_value)
        for i in range(5):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                password="SecureP@ss99!",
            )
            user = await repo.create(user_data, password_hash=password_hash)
            if i == 0:
                user.role = UserRole.ADMIN
                test_db.add(user)
                await test_db.commit()

        # Count by role
        admin_count = await repo.count_by_role(UserRole.ADMIN)
        assert admin_count == 1

        user_count = await repo.count_by_role(UserRole.USER)
        assert user_count == 4
