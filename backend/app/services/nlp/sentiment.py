"""
Sentiment analysis service — local transformer model.

Uses cardiffnlp/twitter-roberta-base-sentiment-latest (3-class: positive/neutral/negative).
Model is lazy-loaded and reused across calls.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Lazy-loaded model singleton
_pipeline = None
_model_name: str = ""
_model_version: str = "1.0"


def _get_pipeline():
    """Lazy-load the sentiment pipeline."""
    global _pipeline, _model_name
    if _pipeline is None:
        settings = get_settings()
        _model_name = settings.SENTIMENT_MODEL
        logger.info("loading_sentiment_model", model=_model_name)
        try:
            from transformers import pipeline
            _pipeline = pipeline(
                "sentiment-analysis",
                model=_model_name,
                tokenizer=_model_name,
                truncation=True,
                max_length=512,
                top_k=None,  # Return all class scores
            )
            logger.info("sentiment_model_loaded", model=_model_name)
        except Exception as exc:
            logger.error("sentiment_model_load_error", error=str(exc))
            _pipeline = None
    return _pipeline


# Label mapping for the RoBERTa model
LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}


def analyse_sentiment(text: str) -> Optional[Dict]:
    """Analyse sentiment of a single text.

    Returns:
        dict with keys: label, score, confidence, model_name, model_version
    """
    pipe = _get_pipeline()
    if pipe is None:
        return None

    try:
        # Truncate very long texts
        truncated = text[:2048]
        results = pipe(truncated)

        if not results:
            return None

        # Results is a list of dicts when top_k=None
        if isinstance(results[0], list):
            scores = results[0]
        else:
            scores = results

        # Find the best label
        best = max(scores, key=lambda x: x["score"])
        label = LABEL_MAP.get(best["label"], best["label"])

        # Map score to polarity
        score_val = best["score"]
        if label == "negative":
            score_val = -score_val
        elif label == "neutral":
            score_val = 0.0

        return {
            "label": label,
            "score": score_val,
            "confidence": best["score"],
            "model_name": _model_name,
            "model_version": _model_version,
        }

    except Exception as exc:
        logger.error("sentiment_analysis_error", error=str(exc))
        return None


def analyse_batch(texts: List[str], batch_size: int = 32) -> List[Optional[Dict]]:
    """Analyse sentiment for a batch of texts."""
    pipe = _get_pipeline()
    if pipe is None:
        return [None] * len(texts)

    results: List[Optional[Dict]] = []
    for i in range(0, len(texts), batch_size):
        batch = [t[:2048] for t in texts[i: i + batch_size]]
        try:
            batch_results = pipe(batch)
            for raw in batch_results:
                if isinstance(raw, list):
                    scores = raw
                else:
                    scores = [raw]
                best = max(scores, key=lambda x: x["score"])
                label = LABEL_MAP.get(best["label"], best["label"])
                
                score_val = best["score"]
                if label == "negative":
                    score_val = -score_val
                elif label == "neutral":
                    score_val = 0.0
                    
                results.append({
                    "label": label,
                    "score": score_val,
                    "confidence": best["score"],
                    "model_name": _model_name,
                    "model_version": _model_version,
                })
        except Exception as exc:
            logger.error("sentiment_batch_error", error=str(exc), batch_idx=i)
            results.extend([None] * len(batch))

    return results
