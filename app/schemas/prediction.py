
# app/schemas/prediction.py
from pydantic import BaseModel
from typing import Any


class PredictionResponse(BaseModel):
    team_id: int
    prediction: Any  # could be dict or str depending on ML output


# from pydantic import BaseModel

# class PredictionResponse(BaseModel):
#     id: int
#     assessment_id: int
#     prediction: str
#     confidence: float

#     class Config:
#        model_config = ConfigDict(from_attributes=True)
