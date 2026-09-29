"""
Embedding generation service using Sentence Transformers.

Uses all-MiniLM-L6-v2 (384-dim) — lightweight and effective.
Lazy-loaded, batch generation, stores in pgvector.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_model = None


def _get_model():
    """Lazy-load sentence transformer model."""
    global _model
    if _model is None:
        settings = get_settings()
        model_name = settings.EMBEDDING_MODEL
        logger.info("loading_embedding_model", model=model_name)
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(model_name)
            logger.info("embedding_model_loaded", model=model_name)
        except Exception as exc:
            logger.error("embedding_model_load_error", error=str(exc))
            _model = None
    return _model


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for a single text."""
    model = _get_model()
    if model is None:
        return None
    try:
        embedding = model.encode(text[:8192], show_progress_bar=False)
        return embedding.tolist()
    except Exception as exc:
        logger.error("embedding_error", error=str(exc))
        return None


def generate_batch(
    texts: List[str], batch_size: int = 32
) -> List[Optional[List[float]]]:
    """Generate embeddings for a batch of texts."""
    model = _get_model()
    if model is None:
        return [None] * len(texts)

    try:
        truncated = [t[:8192] for t in texts]
        embeddings = model.encode(
            truncated,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        return [emb.tolist() for emb in embeddings]
    except Exception as exc:
        logger.error("embedding_batch_error", error=str(exc))
        return [None] * len(texts)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
