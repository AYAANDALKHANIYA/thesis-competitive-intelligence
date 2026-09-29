"""Prediction Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    id: int
    company_id: int
    metric_name: str
    prediction_date: date
    horizon_days: int
    predicted_value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    model_version_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelVersionResponse(BaseModel):
    id: int
    model_name: str
    version: str
    trained_at: datetime
    training_samples: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    status: str
    metadata_: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelComparisonResponse(BaseModel):
    models: List[ModelVersionResponse]
    best_model_id: Optional[int] = None
    comparison_metric: str = "mae"


class PredictionRequest(BaseModel):
    metric_name: str = "market_activity_index"
    horizon_days: int = 30
    force_retrain: bool = False
