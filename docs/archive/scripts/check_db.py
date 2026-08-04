import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.team import Team
from app.db.models.user import User


async def check_db():
    async with AsyncSessionLocal() as session:
        try:
            # Check Users
            user_count = (
                await session.execute(select(func.count()).select_from(User))
            ).scalar()
            # Check Teams
            team_count = (
                await session.execute(select(func.count()).select_from(Team))
            ).scalar()
            # Check Assessments
            assessment_count = (
                await session.execute(select(func.count()).select_from(Assessment))
            ).scalar()
            # Check Responses
            response_count = (
                await session.execute(select(func.count()).select_from(Response))
            ).scalar()

            print(f"Users: {user_count}")
            print(f"Teams: {team_count}")
            print(f"Assessments: {assessment_count}")
            print(f"Responses: {response_count}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_db())
