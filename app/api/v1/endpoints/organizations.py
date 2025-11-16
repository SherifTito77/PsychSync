#app/api/routes/organizations.py

from fastapi import APIRouter
from app.schemas.organization import OrganizationCreate, OrganizationOut, OrganizationUpdate
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter()

@router.post("/", response_model=OrganizationOut)
async def create_organization(org: OrganizationCreate):
    return {"id": 1, "name": org.name}


__all__ = [
    "UserCreate", "UserUpdate", "UserOut",
    "OrganizationCreate", "OrganizationUpdate", "OrganizationOut",
]

