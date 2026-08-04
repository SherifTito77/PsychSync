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
    user = User(role="admin")  # Try setting role directly
    mock_db = AsyncMock()

    # Check
    has_perm = await permission_service.has_permission(
        db=mock_db, user=user, permission=Permission.MANAGE_SYSTEM
    )
    print(f"Has permission: {has_perm}")


asyncio.run(main())
