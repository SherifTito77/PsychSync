import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_endpoints():
    # Use ASGITransport to test the FastAPI application
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        print("Testing burnout endpoints...")

        # Test summary endpoint (using organization name 'default-org')
        response = await client.get(
            "/api/v1/executive/burnout/summary?org_id=default-org"
        )
        print(f"Summary status: {response.status_code}")
        print(f"Summary response: {response.json()}")

        # Test cost-benefit endpoint
        response = await client.get(
            "/api/v1/executive/burnout/cost-benefit?org_id=default-org"
        )
        print(f"Cost-benefit status: {response.status_code}")
        print(f"Cost-benefit response: {response.json()}")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
