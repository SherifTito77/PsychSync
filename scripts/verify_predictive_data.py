import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.services.prediction_data_service import PredictionDataCollectionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_data():
    async with AsyncSessionLocal() as db:
        service = PredictionDataCollectionService()
        result = await service.collect_training_data(
            db=db,
            include_assessment_responses=True,
            include_team_performance=True,
            include_demographics=True,
        )

        if result["success"]:
            df = result["data"]
            print(f"Data collected: {len(df)} rows, {len(df.columns)} columns")
            print(f"Columns: {list(df.columns)}")

            if "team_performance_score" in df.columns:
                print("✅ 'team_performance_score' found in data!")
                print(df["team_performance_score"].head())
            else:
                print("❌ 'team_performance_score' NOT found in data!")
        else:
            print(f"Failed to collect data: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(verify_data())
