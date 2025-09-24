
# app/schemas/behavioral_insight.py
from pydantic import BaseModel
from typing import Optional


class BehavioralInsight(BaseModel):
    user_id: int
    insight: str
    recommendation: Optional[str] = None


# from pydantic import BaseModel

# class BehavioralInsight(BaseModel):
#     user_id: int
#     insight: str
#     recommendation: str | None = None

