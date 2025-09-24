# tests/api/test_teams.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.team import TeamCreate

@pytest.mark.asyncio
async def test_create_team():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = TeamCreate(name="Dev Team", members=[1, 2])
        response = await ac.post("/teams/", json=payload.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Dev Team"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_team():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/teams/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
