
# app/schemas/organization.py
from pydantic import BaseModel
from typing import Optional


class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class OrganizationOut(OrganizationBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizationResponse(OrganizationBase):
    id: int
    owner_id: Optional[int] = None  # useful if tied to a user
    size: Optional[int] = None      # number of members
    industry: Optional[str] = None

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
