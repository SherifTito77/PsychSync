from typing import Any
from uuid import UUID

from app.core.cache_strategy import CacheStrategy
from app.db.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate, PredictionUpdate
from app.services.base_service import BaseService


class PredictionResultService(
    BaseService[Prediction, PredictionCreate, PredictionUpdate]
):
    """
    Service for CRUD operations on prediction results.
    """

    @property
    def model(self) -> type[Prediction]:
        return Prediction

    @property
    def cache_strategy(self) -> CacheStrategy:
        return CacheStrategy.PREDICTION_DATA

    def get_cache_key(self, operation: str, **kwargs) -> str:
        if operation == "get_by_id":
            return f"prediction:{kwargs.get('id')}"
        return f"prediction:{operation}"

    def validate_create_data(self, data: PredictionCreate) -> None:
        if not data.prediction_type:
            raise ValueError("Prediction type is required")

    def validate_update_data(
        self, data: PredictionUpdate, existing: Prediction
    ) -> None:
        pass
