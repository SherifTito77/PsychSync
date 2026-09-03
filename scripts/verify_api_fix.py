import asyncio

import httpx

ENDPOINTS = [
    "/metrics/summary",
    "/jira_integration/bugs/summary?project_key=PROJ&days=14",
    "/pull-requests?limit=10",
    "/jira_integration/reports/performance?project_key=PROJ&days=7",
    "/jira_integration/sprints?project_key=PROJ",
    "/sql_audit/queries/summary",
    "/sql_audit/queries?limit=5",
    "/query_performance/queries/summary",
    "/query_performance/queries?limit=5",
    "/build_analysis/failures/summary",
    "/build_analysis/failures/unresolved?limit=5",
    "/caching_config/entries/summary",
    "/caching_config/entries/low_hit_rate?limit=5",
    "/breaking_changes/changes/summary",
    "/breaking_changes/changes/unapproved?limit=5",
]

BASE_URL = "http://localhost:8000/api/v1"


async def verify_endpoints():
    async with httpx.AsyncClient() as client:
        for endpoint in ENDPOINTS:
            url = f"{BASE_URL}{endpoint}"
            try:
                response = await client.get(url)
                if response.status_code in [404, 500]:
                    print(f"❌ {url} returned {response.status_code}")
                else:
                    print(f"✅ {url} returned {response.status_code}")
            except Exception as e:
                print(f"❌ {url} failed: {e}")


if __name__ == "__main__":
    asyncio.run(verify_endpoints())
