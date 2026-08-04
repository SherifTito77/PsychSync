import asyncio

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

REQUIRED_TABLES = [
    "users",
    "teams",
    "team_members",
    "assessments",
    "assessment_responses",
    "organizations",
    "refresh_tokens",
]


async def verify_tables():
    async with AsyncSessionLocal() as db:
        for table in REQUIRED_TABLES:
            try:
                await db.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                print(f"✅ {table} — exists")
            except Exception as e:
                print(f"❌ {table} — MISSING: {str(e).split(']')[0].split(':')[0]}")


if __name__ == "__main__":
    asyncio.run(verify_tables())
