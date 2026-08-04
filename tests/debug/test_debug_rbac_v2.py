import asyncio
from unittest.mock import AsyncMock

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.permissions import require_permission
from app.api.v1.deps import get_current_user
from app.core.database import get_async_db
from app.db.models.user import User
from app.services.permission_service import Permission

app = FastAPI()

mock_db = AsyncMock()


@app.get("/test")
async def test_endpoint(
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM)),
):
    return {"message": "success"}


def test_rbac():
    client = TestClient(app)
    user = User(role="super_admin", is_superuser=True)

    async def override():
        return user

    app.dependency_overrides[get_current_user] = override
    app.dependency_overrides[get_async_db] = lambda: mock_db

    response = client.get("/test", headers={"Authorization": "Bearer token"})
    print(f"Response: {response.status_code}, Body: {response.json()}")


test_rbac()
