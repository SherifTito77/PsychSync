#tests/api/test_assessments.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.schemas.assessment import AssessmentCreate

@pytest.mark.asyncio
async def test_create_assessment():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = AssessmentCreate(title="Psych Test", score=95)
        response = await ac.post("/assessments/", json=payload.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Psych Test"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_assessment():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/assessments/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
