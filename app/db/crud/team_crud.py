# app/db/crud/team_crud.py
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.team import Team


class TeamCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_team(self, team_id: UUID) -> Team | None:
        result = await self.db.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()
