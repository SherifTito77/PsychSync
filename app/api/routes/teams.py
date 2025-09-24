# app/api/routes/teams.py
from fastapi import APIRouter
from app.schemas.team import TeamCreate, TeamOut

router = APIRouter()

@router.post("/", response_model=TeamOut)
async def create_team(team: TeamCreate):
    # TODO: Replace with actual DB logic
    return {"id": 1, "name": team.name, "members": team.members}

@router.get("/{team_id}", response_model=TeamOut)
async def get_team(team_id: int):
    # TODO: Replace with actual DB lookup
    return {"id": team_id, "name": "Demo Team", "members": []}
