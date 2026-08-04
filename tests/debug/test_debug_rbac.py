import asyncio
from unittest.mock import AsyncMock

from app.api.v1.deps import get_current_user
from app.db.models.user import User
from app.services.permission_service import Permission, permission_service


async def main():
    user = User(role="super_admin", is_superuser=True)
    mock_db = AsyncMock()

    # Check
    has_perm = await permission_service.has_permission(
        db=mock_db, user=user, permission=Permission.MANAGE_SYSTEM
    )
    print(f"Has permission: {has_perm}")


asyncio.run(main())
