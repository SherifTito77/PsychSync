from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.organization import create_org, get_orgs
from app.schemas.organization import OrganizationCreate, OrganizationRead
from typing import List

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationRead)
async def create_organization(org: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    return await create_org(db, org)

@router.get("/", response_model=List[OrganizationRead])
async def list_organizations(db: AsyncSession = Depends(get_db)):
    return await get_orgs(db)
