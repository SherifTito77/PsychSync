# app/schemas/organization.py

from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    description: str | None = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class OrganizationOut(OrganizationBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizationResponse(OrganizationBase):
    id: int
    owner_id: int | None = None  # useful if tied to a user
    size: int | None = None  # number of members
    industry: str | None = None

    model_config = {"from_attributes": True}


# from pydantic import BaseModel
# from typing import Optional

# class OrganizationBase(BaseModel):
#     name: str
#     description: Optional[str] = None

# class OrganizationCreate(OrganizationBase):
#     owner_id: int

# class OrganizationUpdate(OrganizationBase):
#     pass

# class OrganizationOut(OrganizationBase):
#     id: int
#     owner_id: int
#     model_config = {"from_attributes": True}
