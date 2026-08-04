import asyncio
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_user
from app.main import app

client = TestClient(app)


async def test_override():
    user = MagicMock()
    user.id = "123"

    async def override():
        return user

    app.dependency_overrides[get_current_user] = override

    # Try a request without auth header to see if it bypasses 401
    response = client.get("/api/v1/billing/admin/analytics")
    print(f"Status: {response.status_code}")
    app.dependency_overrides.clear()


asyncio.run(test_override())
