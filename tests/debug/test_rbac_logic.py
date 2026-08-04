import asyncio
from unittest.mock import AsyncMock

from app.db.models.user import User
from app.services.permission_service import ROLE_PERMISSIONS, Permission, Role


async def main():
    user = User(is_superuser=True)
    mock_db = AsyncMock()

    # Check if a user with role='admin' has 'manage_system' permission
    # In the code:
    # Role.ADMIN: { Permission.READ, ..., Permission.MANAGE_SYSTEM, ... }
    # So ADMIN role SHOULD have 'manage_system' permission.

    print(f"Role.ADMIN: {Role.ADMIN}")
    print(f"Permission.MANAGE_SYSTEM: {Permission.MANAGE_SYSTEM}")

    perms = ROLE_PERMISSIONS.get(Role.ADMIN, set())
    print(f"Perms in ADMIN: {perms}")
    print(f"Is MANAGE_SYSTEM in perms? {Permission.MANAGE_SYSTEM in perms}")


asyncio.run(main())
