"""Predictions and model version repository."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_version import ModelVersion
from app.models.prediction import Prediction


class PredictionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_prediction(self, **kwargs) -> Prediction:
        pred = Prediction(**kwargs)
        self.db.add(pred)
        await self.db.flush()
        return pred

    async def get_predictions(
        self,
        company_id: Optional[int] = None,
        metric_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Prediction]:
        query = select(Prediction)
        if company_id:
            query = query.where(Prediction.company_id == company_id)
        if metric_name:
            query = query.where(Prediction.metric_name == metric_name)
        result = await self.db.execute(
            query.order_by(Prediction.prediction_date.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Prediction.id)))
        return result.scalar() or 0

    # ── Model Versions ───────────────────────────────────────────────────

    async def create_model_version(self, **kwargs) -> ModelVersion:
        mv = ModelVersion(**kwargs)
        self.db.add(mv)
        await self.db.flush()
        await self.db.refresh(mv)
        return mv

    async def get_model_versions(
        self, model_name: Optional[str] = None, status: Optional[str] = None
    ) -> List[ModelVersion]:
        query = select(ModelVersion)
        if model_name:
            query = query.where(ModelVersion.model_name == model_name)
        if status:
            query = query.where(ModelVersion.status == status)
        result = await self.db.execute(
            query.order_by(ModelVersion.trained_at.desc())
        )
        return list(result.scalars().all())

    async def get_model_version_by_id(self, version_id: int) -> Optional[ModelVersion]:
        result = await self.db.execute(
            select(ModelVersion).where(ModelVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_best_model(self, model_name: Optional[str] = None) -> Optional[ModelVersion]:
        """Get best model by lowest MAE among active models."""
        query = select(ModelVersion).where(
            ModelVersion.status == "active",
            ModelVersion.mae.isnot(None),
        )
        if model_name:
            query = query.where(ModelVersion.model_name == model_name)
        result = await self.db.execute(query.order_by(ModelVersion.mae.asc()).limit(1))
        return result.scalar_one_or_none()

    async def set_model_status(self, version_id: int, status: str) -> None:
        mv = await self.get_model_version_by_id(version_id)
        if mv:
            mv.status = status
            await self.db.flush()
