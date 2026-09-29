"""Prediction endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.predictions import PredictionRepository
from app.schemas.prediction import ModelVersionResponse, PredictionResponse

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])


@router.get("", response_model=list[PredictionResponse])
async def list_predictions(
    company_id: int | None = None,
    metric_name: str | None = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    repo = PredictionRepository(db)
    preds = await repo.get_predictions(company_id=company_id, metric_name=metric_name, limit=limit)
    return [PredictionResponse.model_validate(p) for p in preds]


# NOTE: /models routes MUST be registered BEFORE /{company_id} to prevent
# FastAPI from matching the literal "models" as a company_id path parameter.
@router.get("/models", response_model=list[ModelVersionResponse])
async def list_models(
    model_name: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = PredictionRepository(db)
    versions = await repo.get_model_versions(model_name=model_name, status=status)
    return [ModelVersionResponse.model_validate(v) for v in versions]


@router.get("/models/{model_version_id}", response_model=ModelVersionResponse)
async def get_model_version(model_version_id: int, db: AsyncSession = Depends(get_db)):
    repo = PredictionRepository(db)
    version = await repo.get_model_version_by_id(model_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")
    return ModelVersionResponse.model_validate(version)


@router.get("/{company_id}")
async def get_company_predictions(
    company_id: int,
    metric_name: str = "market_activity_index",
    db: AsyncSession = Depends(get_db),
):
    repo = PredictionRepository(db)
    
    # Get observation count for empty state
    from app.models.metric import MarketMetric
    from sqlalchemy import select, func
    obs_count = (await db.execute(select(func.count(MarketMetric.id)).where(MarketMetric.company_id == company_id, MarketMetric.metric_name == metric_name))).scalar() or 0
    
    preds = await repo.get_predictions(company_id=company_id, metric_name=metric_name)
    return {
        "company_id": company_id,
        "metric_name": metric_name,
        "observation_count": obs_count,
        "required_observations": 30,
        "predictions": [PredictionResponse.model_validate(p) for p in preds],
    }
