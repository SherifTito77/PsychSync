
# app/schemas/team.py
from pydantic import BaseModel
from typing import Optional


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamResponse(TeamBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


# from pydantic import BaseModel

# class TeamCreate(BaseModel):
#     name: str
#     description: str | None = None

# class TeamResponse(BaseModel):
#     id: int
#     name: str
#     description: str | None = None

#     class Config:
#         orm_mode = True

