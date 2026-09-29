"""
Model registry service — manages model versions, stores evaluation metrics.

Never overwrites historical evaluation results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.predictions import PredictionRepository

logger = get_logger(__name__)


class ModelRegistry:
    """Manages ML model versions and their evaluation metrics."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pred_repo = PredictionRepository(db)

    async def register_model(
        self,
        model_name: str,
        version: str,
        training_samples: int,
        features: List[str],
        metrics: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "trained",
    ) -> int:
        """Register a new model version with evaluation metrics."""
        mv = await self.pred_repo.create_model_version(
            model_name=model_name,
            version=version,
            trained_at=datetime.now(timezone.utc),
            training_samples=training_samples,
            features={"feature_names": features},
            mae=metrics.get("mae"),
            rmse=metrics.get("rmse"),
            mape=metrics.get("mape"),
            status=status,
            metadata_=metadata,
        )
        logger.info(
            "model_registered",
            model_name=model_name,
            version=version,
            mae=metrics.get("mae"),
            status=status,
        )
        return mv.id

    async def activate_model(self, version_id: int) -> None:
        """Set a model version as active."""
        await self.pred_repo.set_model_status(version_id, "active")

    async def retire_model(self, version_id: int) -> None:
        """Retire a model version."""
        await self.pred_repo.set_model_status(version_id, "retired")

    async def get_best_model(self, model_name: Optional[str] = None):
        """Get the best-performing active model."""
        return await self.pred_repo.get_best_model(model_name)

    async def store_predictions(
        self,
        company_id: int,
        metric_name: str,
        predictions: List[Dict],
        model_version_id: int,
    ) -> int:
        """Store prediction results linked to a model version."""
        count = 0
        for pred in predictions:
            await self.pred_repo.create_prediction(
                company_id=company_id,
                metric_name=metric_name,
                prediction_date=pred["date"],
                horizon_days=pred.get("horizon_days", 1),
                predicted_value=pred["predicted"],
                lower_bound=pred.get("lower"),
                upper_bound=pred.get("upper"),
                model_version_id=model_version_id,
            )
            count += 1
        return count
