from pydantic import BaseModel, constr
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: constr(min_length=1)
    slug: constr(min_length=1)

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationRead(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
