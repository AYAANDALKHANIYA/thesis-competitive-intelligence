"""
Prediction task — orchestrates feature engineering, model training, and evaluation.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.metrics import MetricsRepository
from app.services.prediction.baseline import MovingAverageBaseline, NaiveBaseline
from app.services.prediction.evaluator import ModelEvaluator
from app.services.prediction.features import build_features, chronological_split, get_feature_columns
from app.services.prediction.registry import ModelRegistry
from app.services.prediction.xgboost_model import XGBoostPredictor

logger = get_logger(__name__)


async def run_prediction_pipeline(
    db: AsyncSession,
    company_id: int,
    metric_name: str = "market_activity_index",
    horizon_days: int = 30,
) -> Dict[str, Any]:
    """Run the full prediction pipeline for a company metric.

    Steps:
    1. Load historical metrics
    2. Build features
    3. Chronological split
    4. Train baselines + XGBoost
    5. Evaluate all models
    6. Register best model
    7. Generate and store predictions
    """
    settings = get_settings()
    metrics_repo = MetricsRepository(db)
    registry = ModelRegistry(db)
    evaluator = ModelEvaluator()

    # 1. Load historical data
    metrics = await metrics_repo.get_by_company(
        company_id, metric_name=metric_name, limit=1000
    )

    if len(metrics) < settings.PREDICTION_MIN_SAMPLES:
        return {
            "error": "insufficient_data",
            "samples": len(metrics),
            "min_required": settings.PREDICTION_MIN_SAMPLES,
        }

    dates = [m.metric_date for m in metrics]
    values = [m.metric_value for m in metrics]

    # 2. Build features
    df = build_features(dates, values)
    if len(df) < 20:
        return {"error": "insufficient_features_after_engineering", "rows": len(df)}

    # 3. Chronological split
    train, val, test = chronological_split(df)

    if len(test) < 3:
        return {"error": "insufficient_test_data"}

    model_results = {}
    version_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 4a. Naive baseline
    try:
        naive = NaiveBaseline()
        naive_preds = naive.predict(train, len(test))
        naive_metrics = naive.evaluate(test["value"].tolist(), naive_preds)
        model_results["naive_last_value"] = naive_metrics

        await registry.register_model(
            model_name="naive_last_value",
            version=version_ts,
            training_samples=len(train),
            features=[],
            metrics=naive_metrics,
            status="trained",
        )
    except Exception as exc:
        logger.error("naive_baseline_error", error=str(exc))

    # 4b. Moving average baseline
    try:
        ma = MovingAverageBaseline(window=7)
        ma_preds = ma.predict(train, len(test))
        ma_metrics = ma.evaluate(test["value"].tolist(), ma_preds)
        model_results["moving_average"] = ma_metrics

        await registry.register_model(
            model_name="moving_average",
            version=version_ts,
            training_samples=len(train),
            features=[],
            metrics=ma_metrics,
            status="trained",
        )
    except Exception as exc:
        logger.error("moving_average_error", error=str(exc))

    # 4c. XGBoost
    xgb_version_id = None
    try:
        xgb = XGBoostPredictor()
        xgb_result = xgb.train(train, val)
        xgb_test_metrics = xgb.evaluate(test)
        model_results["xgboost"] = xgb_test_metrics

        feature_cols = get_feature_columns(train)
        xgb_version_id = await registry.register_model(
            model_name="xgboost",
            version=version_ts,
            training_samples=len(train),
            features=feature_cols,
            metrics=xgb_test_metrics,
            metadata={"feature_importance": xgb.get_feature_importance()},
            status="trained",
        )
    except Exception as exc:
        logger.error("xgboost_error", error=str(exc))

    # 5. Compare models
    comparison = evaluator.compare_models(model_results, metric="mae")

    # 6. Activate best model
    best_model_name = comparison.get("best_model")
    if best_model_name and xgb_version_id and best_model_name == "xgboost":
        await registry.activate_model(xgb_version_id)

    # 7. Generate future predictions using best model
    predictions_stored = 0
    if best_model_name == "xgboost" and xgb_version_id:
        try:
            # Use the last rows of data to predict forward
            last_features = df.tail(1)
            future_preds = []
            today = date.today()
            for d in range(1, horizon_days + 1):
                pred_date = today + timedelta(days=d)
                pred_val = float(xgb.predict(last_features)[0])
                future_preds.append({
                    "date": pred_date,
                    "predicted": round(pred_val, 4),
                    "lower": round(pred_val * 0.9, 4),
                    "upper": round(pred_val * 1.1, 4),
                    "horizon_days": d,
                })

            predictions_stored = await registry.store_predictions(
                company_id=company_id,
                metric_name=metric_name,
                predictions=future_preds,
                model_version_id=xgb_version_id,
            )
        except Exception as exc:
            logger.error("prediction_storage_error", error=str(exc))

    result = {
        "company_id": company_id,
        "metric_name": metric_name,
        "data_points": len(metrics),
        "features_built": len(df),
        "model_comparison": comparison,
        "predictions_stored": predictions_stored,
        "best_model": best_model_name,
    }

    logger.info("prediction_pipeline_complete", **result)
    return result
