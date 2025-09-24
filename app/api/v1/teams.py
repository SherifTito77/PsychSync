
#/psychsync/app/api/v1/teams.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.team import Team
from app.schemas import TeamCreate, TeamResponse

router = APIRouter()

@router.post("/", response_model=TeamResponse)
async def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    db_team = Team(
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        team_type=team.team_type
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return TeamResponse.from_orm(db_team)

@router.get("/", response_model=list[TeamResponse])
async def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return [TeamResponse.from_orm(team) for team in teams]

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.from_orm(team)