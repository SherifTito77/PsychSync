from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.organization import Organization
from app.schemas.organization import OrganizationCreate

async def create_org(db: AsyncSession, org_in: OrganizationCreate) -> Organization:
    org = Organization(**org_in.dict())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

async def get_orgs(db: AsyncSession):
    res = await db.execute(select(Organization))
    return res.scalars().all()
