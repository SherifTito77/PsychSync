from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_team_optimize():
    r = client.post('/api/v1/team-optimizer/optimize', json={"members":[{"id":1,"name":"A","role":"dev","traits":{}}]})
    assert r.status_code == 200
    assert 'recommended_groups' in r.json()