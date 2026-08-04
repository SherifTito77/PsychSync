"""
IRT Session Manager — handles stateful adaptive testing via API
Stores session state in Redis/cache between requests
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IRTSession:
    """Represents an in-progress adaptive test session"""

    session_id: str
    assessment_id: int
    user_id: int
    current_theta: float = 0.0
    current_se: float = float("inf")
    items_administered: List[str] = field(default_factory=list)
    responses: List[int] = field(default_factory=list)
    theta_trajectory: List[float] = field(default_factory=list)
    is_complete: bool = False
    stopping_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "assessment_id": self.assessment_id,
            "user_id": self.user_id,
            "current_theta": self.current_theta,
            "current_se": self.current_se,
            "items_administered": self.items_administered,
            "responses": self.responses,
            "theta_trajectory": self.theta_trajectory,
            "is_complete": self.is_complete,
            "stopping_reason": self.stopping_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IRTSession":
        return cls(**data)
