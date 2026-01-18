# app/api/routes/organizations.py

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy
from app.schemas.organization import OrganizationCreate, OrganizationOut, OrganizationUpdate
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter()


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
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
