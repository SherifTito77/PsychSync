import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

# Add the project root to sys.path to import from app
sys.path.append(os.getcwd())

from app.schemas.clinical import ScreeningResponse

# Simulated data from the endpoint
data = {
    "id": uuid4(),
    "screening_type": "LSAS",
    "total_score": 79.0,
    "severity_level": "moderate",
    "risk_level": "moderate",
    "interpretation": "LSAS Total Score: 79. Severe social anxiety.",
    "recommendations": ["Therapy"],
    "crisis_alert": False,
    "risk_flags": [],
    "subscale_scores": {
        "total_fear": 47,
        "total_avoidance": 32,
        "performance_anxiety": 35,
        "social_interaction_anxiety": 44,
    },
    "completed_at": datetime.utcnow(),
}

response = ScreeningResponse(**data)
print(f"Serialized response keys: {response.model_dump().keys()}")
if "subscale_scores" not in response.model_dump():
    print("BUG STILL PRESENT: subscale_scores is missing from the serialized response!")
else:
    print("SUCCESS: subscale_scores are now present in the response.")
    print(f"Subscale scores content: {response.model_dump()['subscale_scores']}")
