#tests/api/test_organizations.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_org():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/organizations/", json={"name": "OpenAI"})
    assert response.status_code == 200
    assert response.json()["name"] == "OpenAI"
