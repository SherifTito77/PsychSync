
# app/schemas/team_optimization.py
from pydantic import BaseModel
from typing import List


class TeamOptimizationRequest(BaseModel):
    team_id: int
    member_ids: List[int]


# from pydantic import BaseModel
# from typing import List

# class TeamOptimizationRequest(BaseModel):
#     team_id: int
#     goals: List[str]  # e.g., ["increase collaboration", "balance skills"]
