import asyncio

from app.core.database import AsyncSessionLocal
from app.db.models.assessment import Assessment
from app.services.mental_health_screening import MentalHealthScreeningService


async def test_method():
    async with AsyncSessionLocal() as db:
        service = MentalHealthScreeningService(db)
        # Check if the method exists
        print(
            f"Has attribute: {hasattr(service, '_get_or_create_clinical_assessment')}"
        )
        # Try finding a similar method
        print(f"Dir: {[m for m in dir(service) if 'get' in m]}")


if __name__ == "__main__":
    asyncio.run(test_method())
