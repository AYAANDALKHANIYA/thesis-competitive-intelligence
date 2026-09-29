"""
Entity extraction service using spaCy.

Lazy-loads the spaCy model and extracts ORG, PERSON, GPE, LOC, PRODUCT entities.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_nlp = None


def _get_nlp():
    """Lazy-load spaCy model."""
    global _nlp
    if _nlp is None:
        settings = get_settings()
        model_name = settings.SPACY_MODEL
        logger.info("loading_spacy_model", model=model_name)
        try:
            import spacy
            _nlp = spacy.load(model_name)
            logger.info("spacy_model_loaded", model=model_name)
        except OSError:
            logger.warning("spacy_model_not_found", model=model_name)
            try:
                import spacy.cli
                spacy.cli.download(model_name)
                import spacy
                _nlp = spacy.load(model_name)
            except Exception as exc:
                logger.error("spacy_download_error", error=str(exc))
                _nlp = None
    return _nlp


ENTITY_TYPES = {"ORG", "PERSON", "GPE", "LOC", "PRODUCT", "NORP", "EVENT"}


def extract_entities(text: str, max_length: int = 100000) -> List[Dict]:
    """Extract named entities from text.

    Returns list of dicts with keys: entity_text, entity_type, start, end, confidence.
    """
    nlp = _get_nlp()
    if nlp is None:
        return []

    try:
        # Truncate very long texts for performance
        truncated = text[:max_length]
        doc = nlp(truncated)

        entities = []
        seen = set()
        for ent in doc.ents:
            if ent.label_ not in ENTITY_TYPES:
                continue
            # Deduplicate by text + type within document
            key = (ent.text.strip().lower(), ent.label_)
            if key in seen:
                continue
            seen.add(key)

            entities.append({
                "entity_text": ent.text.strip(),
                "entity_type": ent.label_,
                "start_position": ent.start_char,
                "end_position": ent.end_char,
                "confidence": None,  # spaCy sm model doesn't provide confidence
            })

        return entities

    except Exception as exc:
        logger.error("entity_extraction_error", error=str(exc))
        return []


def extract_batch(texts: List[str], batch_size: int = 50) -> List[List[Dict]]:
    """Extract entities from a batch of texts."""
    nlp = _get_nlp()
    if nlp is None:
        return [[] for _ in texts]

    results = []
    for text in texts:
        results.append(extract_entities(text))
    return results
