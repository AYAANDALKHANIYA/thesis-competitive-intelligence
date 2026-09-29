"""
Baseline prediction models — naive last-value and moving-average baselines.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from app.core.logging import get_logger

logger = get_logger(__name__)


class NaiveBaseline:
    """Last-value baseline: predicts the last observed value."""

    name = "naive_last_value"

    def predict(self, train: pd.DataFrame, horizon: int) -> List[float]:
        last_value = train["value"].iloc[-1]
        return [float(last_value)] * horizon

    def evaluate(self, actuals: List[float], predictions: List[float]) -> Dict[str, float]:
        return _calculate_metrics(actuals, predictions)


class MovingAverageBaseline:
    """Moving average baseline: predicts the rolling mean."""

    name = "moving_average"

    def __init__(self, window: int = 7) -> None:
        self.window = window

    def predict(self, train: pd.DataFrame, horizon: int) -> List[float]:
        avg = train["value"].iloc[-self.window:].mean()
        return [float(avg)] * horizon

    def evaluate(self, actuals: List[float], predictions: List[float]) -> Dict[str, float]:
        return _calculate_metrics(actuals, predictions)


def _calculate_metrics(actuals: List[float], predictions: List[float]) -> Dict[str, float]:
    """Calculate MAE, RMSE, MAPE with safe zero handling."""
    y = np.array(actuals)
    yhat = np.array(predictions[:len(y)])

    if len(y) == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

    errors = y - yhat
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # MAPE: exclude zeros to avoid division errors
    mask = y != 0
    if mask.sum() > 0:
        mape = float(np.mean(np.abs((y[mask] - yhat[mask]) / y[mask]))) * 100
    else:
        mape = 0.0

    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 2)}
