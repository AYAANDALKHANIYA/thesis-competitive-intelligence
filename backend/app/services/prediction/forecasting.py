"""
Prophet forecasting model — used when sufficient historical data exists.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from app.core.logging import get_logger
from app.services.prediction.baseline import _calculate_metrics

logger = get_logger(__name__)


class ProphetForecaster:
    """Prophet-based time-series forecasting."""

    name = "prophet"

    def __init__(self) -> None:
        self.model = None

    def train_and_forecast(
        self,
        dates: list,
        values: list,
        horizon_days: int = 30,
        min_samples: int = 30,
    ) -> Optional[Dict]:
        """Train Prophet and generate forecast.

        Returns None if insufficient data.
        """
        if len(dates) < min_samples:
            logger.info(
                "prophet_skipped",
                reason="insufficient_data",
                samples=len(dates),
                min_required=min_samples,
            )
            return None

        try:
            from prophet import Prophet

            df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": values})

            self.model = Prophet(
                changepoint_prior_scale=0.05,
                seasonality_mode="multiplicative",
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False if len(dates) < 365 else True,
            )
            self.model.fit(df)

            future = self.model.make_future_dataframe(periods=horizon_days)
            forecast = self.model.predict(future)

            # Extract forecast for future dates only
            future_forecast = forecast.iloc[-horizon_days:]

            predictions = []
            for _, row in future_forecast.iterrows():
                predictions.append({
                    "date": row["ds"].date().isoformat(),
                    "predicted": round(float(row["yhat"]), 4),
                    "lower": round(float(row["yhat_lower"]), 4),
                    "upper": round(float(row["yhat_upper"]), 4),
                })

            # In-sample evaluation
            in_sample = forecast.iloc[:-horizon_days]
            if len(in_sample) > 0:
                in_sample_preds = in_sample["yhat"].tolist()
                metrics = _calculate_metrics(values[:len(in_sample_preds)], in_sample_preds)
            else:
                metrics = {"mae": 0, "rmse": 0, "mape": 0}

            logger.info("prophet_trained", horizon=horizon_days, **metrics)

            return {
                "predictions": predictions,
                "metrics": metrics,
                "training_samples": len(dates),
            }

        except Exception as exc:
            logger.error("prophet_error", error=str(exc))
            return None
