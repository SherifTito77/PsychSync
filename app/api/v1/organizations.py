# app/api/v1/organizations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_async_db
from app.db.models.organization import Organization
from app.schemas import OrganizationCreate

router = APIRouter()


@router.post("/", response_model=OrganizationCreate)
async def create_organization(
    org: OrganizationCreate, db: Session = Depends(get_async_db)
):
    db_org = Organization(name=org.name, description=org.description)
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)
    return db_org
