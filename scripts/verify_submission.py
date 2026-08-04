import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.db.models.assessment import AssessmentResponse
from app.db.models.user import User
from app.services.mental_health_screening import MentalHealthScreeningService


async def verify():
    async with AsyncSessionLocal() as db:
        # Get a user (use the one created earlier)
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("No user found")
            return

        service = MentalHealthScreeningService(db)
        responses = {"phq9_1": 1, "phq9_2": 1}

        try:
            result = await service.process_assessment_responses(
                user=user, assessment_type="phq9", responses=responses
            )
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify())
