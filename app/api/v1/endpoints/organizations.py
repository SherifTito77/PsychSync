# app/api/routes/organizations.py

from fastapi import APIRouter

from app.api.v1.deps import get_current_user
from app.middleware.rate_limiter import check_rate_limit
from app.schemas.organization import OrganizationCreate, OrganizationOut, OrganizationUpdate
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter()


@check_rate_limit(identifier="public", limit_name="public")
@router.post("/", response_model=OrganizationOut, dependencies=[Depends(get_current_user)])
async def create_organization(org: OrganizationCreate):
    return {"id": 1, "name": org.name}


__all__ = [
    "OrganizationCreate",
    "OrganizationOut",
    "OrganizationUpdate",
    "UserCreate",
    "UserOut",
    "UserUpdate",
]
