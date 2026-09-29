"""Unit tests for model evaluator and baselines."""

from app.services.prediction.baseline import NaiveBaseline, MovingAverageBaseline, _calculate_metrics
from app.services.prediction.evaluator import ModelEvaluator
import pandas as pd


class TestCalculateMetrics:
    def test_perfect_predictions(self):
        metrics = _calculate_metrics([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["mape"] == 0.0

    def test_imperfect_predictions(self):
        metrics = _calculate_metrics([10.0, 20.0, 30.0], [11.0, 19.0, 31.0])
        assert metrics["mae"] > 0
        assert metrics["rmse"] > 0
        assert metrics["mape"] > 0

    def test_handles_empty(self):
        metrics = _calculate_metrics([], [])
        assert metrics["mae"] == 0.0

    def test_handles_zeros_in_mape(self):
        metrics = _calculate_metrics([0.0, 1.0, 2.0], [0.1, 1.1, 2.1])
        # MAPE should skip zeros
        assert metrics["mape"] >= 0


class TestModelEvaluator:
    def test_compare_models(self):
        evaluator = ModelEvaluator()
        results = {
            "baseline": {"mae": 5.0, "rmse": 6.0, "mape": 10.0},
            "xgboost": {"mae": 3.0, "rmse": 4.0, "mape": 7.0},
        }
        comparison = evaluator.compare_models(results, metric="mae")
        assert comparison["best_model"] == "xgboost"
        assert comparison["ranking"][0]["model_name"] == "xgboost"

    def test_is_model_better(self):
        evaluator = ModelEvaluator()
        assert evaluator.is_model_better(
            {"mae": 3.0}, {"mae": 5.0}, metric="mae"
        )
        assert not evaluator.is_model_better(
            {"mae": 7.0}, {"mae": 5.0}, metric="mae"
        )
