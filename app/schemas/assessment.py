
# app/schemas/assessment.py
from pydantic import BaseModel
from typing import Optional


class AssessmentCreate(BaseModel):
    user_id: int
    team_id: int
    answers: dict  # flexible field for responses


class AssessmentResponse(BaseModel):
    id: int
    user_id: int
    team_id: int
    score: Optional[float] = None

    model_config = {"from_attributes": True}


# from pydantic import BaseModel
# from datetime import datetime

# class AssessmentCreate(BaseModel):
#     user_id: int
#     title: str
#     description: str | None = None

# class AssessmentResponse(BaseModel):
#     id: int
#     user_id: int
#     title: str
#     description: str | None = None
#     created_at: datetime

#     class Config:
#         orm_mode = True
