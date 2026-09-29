"""
XGBoost prediction model.

Uses chronological splitting. Does NOT randomly shuffle time-series data.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.core.logging import get_logger
from app.services.prediction.baseline import _calculate_metrics
from app.services.prediction.features import get_feature_columns

logger = get_logger(__name__)


class XGBoostPredictor:
    """XGBoost-based time-series regression."""

    name = "xgboost"

    def __init__(self) -> None:
        self.model = None
        self.feature_columns: List[str] = []

    def train(self, train_df: pd.DataFrame, val_df: Optional[pd.DataFrame] = None) -> Dict:
        """Train XGBoost on feature DataFrame."""
        try:
            import xgboost as xgb
        except ImportError:
            logger.error("xgboost_not_installed")
            return {"error": "xgboost not installed"}

        self.feature_columns = get_feature_columns(train_df)
        X_train = train_df[self.feature_columns].values
        y_train = train_df["value"].values

        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective="reg:squarederror",
        )

        eval_set = []
        if val_df is not None and len(val_df) > 0:
            X_val = val_df[self.feature_columns].values
            y_val = val_df["value"].values
            eval_set = [(X_val, y_val)]

        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set if eval_set else None,
            verbose=False,
        )

        train_preds = self.model.predict(X_train)
        train_metrics = _calculate_metrics(y_train.tolist(), train_preds.tolist())

        result = {"train_metrics": train_metrics, "features": self.feature_columns}

        if val_df is not None and len(val_df) > 0:
            val_preds = self.model.predict(X_val)
            val_metrics = _calculate_metrics(y_val.tolist(), val_preds.tolist())
            result["val_metrics"] = val_metrics

        logger.info("xgboost_trained", **result.get("val_metrics", result["train_metrics"]))
        return result

    def predict(self, df: pd.DataFrame) -> List[float]:
        """Predict using trained model."""
        if self.model is None:
            raise ValueError("Model not trained")
        X = df[self.feature_columns].values
        return self.model.predict(X).tolist()

    def evaluate(self, test_df: pd.DataFrame) -> Dict[str, float]:
        """Evaluate on test set."""
        if self.model is None:
            return {"mae": 0, "rmse": 0, "mape": 0}
        predictions = self.predict(test_df)
        actuals = test_df["value"].tolist()
        return _calculate_metrics(actuals, predictions)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if self.model is None:
            return {}
        importance = self.model.feature_importances_
        return {
            col: round(float(imp), 4)
            for col, imp in zip(self.feature_columns, importance)
        }
