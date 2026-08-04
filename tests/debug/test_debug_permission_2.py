import asyncio
from unittest.mock import AsyncMock

from app.db.models.user import User
from app.services.permission_service import (
    ROLE_PERMISSIONS,
    Permission,
    Role,
    permission_service,
)


async def main():
    # Set up user exactly as test_rbac_integration.py does
    user = User()
    user.role = "super_admin"
    user.is_superuser = True

    mock_db = AsyncMock()

    # Check
    has_perm = await permission_service.has_permission(
        db=mock_db, user=user, permission=Permission.MANAGE_SYSTEM
    )
    print(f"User is superuser: {user.is_superuser}")
    print(f"Has permission: {has_perm}")


asyncio.run(main())
