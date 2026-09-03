import asyncio

from app.core.database import AsyncSessionLocal
from app.services.mental_health_screening import MentalHealthScreeningService


async def debug():
    async with AsyncSessionLocal() as db:
        service = MentalHealthScreeningService(db)
        # Mock responses
        responses = {"phq9_1": "Several days", "phq9_2": 1}
        print(f"Responses: {responses}")
        # Try to calculate sum directly to reproduce the error
        try:
            total = sum(responses.values())
            print(f"Total: {total}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug())
