import asyncio
from unittest.mock import AsyncMock

from app.db.models.user import User
from app.services.permission_service import Permission, permission_service


async def test_super_admin_permission():
    user = User(is_superuser=True)
    mock_db = AsyncMock()

    has_perm = await permission_service.has_permission(
        db=mock_db, user=user, permission=Permission.MANAGE_SYSTEM
    )
    print(f"Super admin has permission: {has_perm}")


asyncio.run(test_super_admin_permission())
