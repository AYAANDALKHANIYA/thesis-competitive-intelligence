"""
Model evaluator — compares models and selects the best performer.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelEvaluator:
    """Compares prediction models and selects the best."""

    def compare_models(
        self, model_results: Dict[str, Dict[str, float]], metric: str = "mae"
    ) -> Dict:
        """Compare models by a selected evaluation metric.

        Args:
            model_results: Dict mapping model_name → {mae, rmse, mape}
            metric: Which metric to rank by (lower is better).

        Returns:
            Dict with ranking, best model, and comparison table.
        """
        if not model_results:
            return {"best_model": None, "ranking": [], "metric": metric}

        ranking = sorted(
            model_results.items(),
            key=lambda x: x[1].get(metric, float("inf")),
        )

        return {
            "best_model": ranking[0][0],
            "best_score": ranking[0][1].get(metric),
            "ranking": [
                {
                    "model_name": name,
                    "rank": i + 1,
                    **scores,
                }
                for i, (name, scores) in enumerate(ranking)
            ],
            "metric": metric,
        }

    def is_model_better(
        self,
        new_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        metric: str = "mae",
    ) -> bool:
        """Check if new model outperforms the baseline."""
        new_val = new_metrics.get(metric, float("inf"))
        base_val = baseline_metrics.get(metric, float("inf"))
        return new_val < base_val
