"""
Topic modelling service using BERTopic.

- Lazy-loads model
- Trains when sufficient documents exist
- Assigns topics to new documents without retraining
- Stores model version metadata
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_topic_model = None
_model_version: str = ""
_model_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models_cache")


def _get_model():
    global _topic_model
    return _topic_model


def train_topic_model(
    documents: List[str],
    min_documents: int = 20,
) -> Optional[Dict[str, Any]]:
    """Train a BERTopic model on a corpus, with a fallback to TF-IDF for small datasets.

    Returns topic metadata dict or None if insufficient data.
    """
    global _topic_model, _model_version

    settings = get_settings()
    min_docs = max(min_documents, settings.TOPIC_MIN_DOCUMENTS)
    doc_count = len(documents)

    if doc_count < 5:
        logger.info(
            "topic_training_skipped",
            reason="insufficient_documents_for_any_analysis",
            count=doc_count,
        )
        # Return a specific structure that the frontend/pipeline can recognize as insufficient
        return {
            "version": "insufficient_data",
            "topics": [],
            "document_count": doc_count,
            "status": "Insufficient data for reliable topic analysis."
        }

    if doc_count < min_docs:
        logger.info("topic_model_fallback", reason="using_tfidf", count=doc_count)
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np

            # Use TF-IDF as a lightweight fallback for early signals
            vectorizer = TfidfVectorizer(stop_words="english", max_features=20)
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()
            scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
            
            # Combine into a single "Early Signals" topic
            top_indices = scores.argsort()[::-1][:10]
            keywords = [{"word": feature_names[i], "weight": round(float(scores[i]), 4)} for i in top_indices]

            _model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_fallback")
            topic_data = [{
                "topic_key": 0,
                "name": "Early Keyword Signals (Low Data)",
                "keywords": keywords,
                "document_count": doc_count,
            }]

            return {
                "version": _model_version,
                "topics": topic_data,
                "document_count": doc_count,
                "all_topics": [0] * doc_count,
                "all_probs": [1.0] * doc_count,
                "status": "Early keyword signal extraction applied."
            }
        except Exception as exc:
            logger.error("topic_fallback_error", error=str(exc))
            return None

    logger.info("topic_model_training", document_count=doc_count)

    try:
        from bertopic import BERTopic
        from sklearn.feature_extraction.text import CountVectorizer

        vectorizer = CountVectorizer(stop_words="english", min_df=2, max_df=0.95)

        _topic_model = BERTopic(
            vectorizer_model=vectorizer,
            nr_topics="auto",
            top_n_words=10,
            verbose=False,
            calculate_probabilities=True,
            min_topic_size=max(3, doc_count // 20),
        )

        topics, probs = _topic_model.fit_transform(documents)

        _model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Extract topic info
        topic_info = _topic_model.get_topic_info()
        topic_data = []
        for _, row in topic_info.iterrows():
            topic_key = row["Topic"]
            if topic_key == -1:
                continue
            topic_words = _topic_model.get_topic(topic_key)
            keywords = [{"word": w, "weight": round(s, 4)} for w, s in topic_words[:10]]
            topic_data.append({
                "topic_key": topic_key,
                "name": f"Topic_{topic_key}",
                "keywords": keywords,
                "document_count": row["Count"],
            })

        logger.info(
            "topic_model_trained",
            topics_found=len(topic_data),
            version=_model_version,
        )

        return {
            "version": _model_version,
            "topics": topic_data,
            "document_count": doc_count,
            "all_topics": topics,
            "all_probs": probs,
        }

    except Exception as exc:
        logger.error("topic_training_error", error=str(exc))
        return None


def assign_topics(
    documents: List[str],
) -> List[Tuple[int, float]]:
    """Assign topics to new documents using the trained model.

    Returns list of (topic_key, probability) tuples.
    """
    model = _get_model()
    if model is None:
        return [(-1, 0.0)] * len(documents)

    try:
        topics, probs = model.transform(documents)
        results = []
        for i, topic in enumerate(topics):
            prob = float(probs[i].max()) if hasattr(probs[i], 'max') else float(probs[i]) if probs is not None else 0.0
            results.append((int(topic), prob))
        return results
    except Exception as exc:
        logger.error("topic_assignment_error", error=str(exc))
        return [(-1, 0.0)] * len(documents)


def get_model_version() -> str:
    return _model_version


def extract_deterministic_topics(documents: List[str]) -> Dict[str, Any]:
    """
    Extract deterministic topics/keyphrases using TF-IDF and spaCy noun chunks.
    Does not depend on BERTopic or OpenAI.
    """
    doc_count = len(documents)
    if doc_count < 1:
        logger.info("deterministic_topics_skipped", reason="insufficient_documents", count=doc_count)
        return {
            "status": "INSUFFICIENT DATA",
            "topics": [],
            "topic_count": 0
        }

    try:
        import spacy
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        # Load spaCy model for noun chunk extraction
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            import spacy.cli
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        # 1. Extract valid phrases from each document using spaCy
        processed_docs = []
        for doc_text in documents:
            if not doc_text or len(doc_text.strip()) == 0:
                processed_docs.append("")
                continue
            
            # Truncate text for performance if needed
            doc = nlp(doc_text[:10000])
            valid_phrases = []
            
            valid_domain_terms = {"ai", "seo", "ppc", "crm", "api", "ux", "ui", "b2b", "ml", "bi", "saas", "roi"}
            generic_phrases = {"click here", "learn more", "contact us", "read more", "get started", "sign up", "marketing pros", "the conference"}
            generic_words = {"company", "website", "business", "service", "system", "platform", "stat", "mo", "explore", "unlimited"}
            stopwords = {"the", "and", "of", "to", "for", "a", "an", "in", "on", "at", "by", "with", "from", "as", "is", "are", "was", "were", "be", "this", "that", "it"}
            
            import re
            for chunk in doc.noun_chunks:
                if len(chunk) > 0 and chunk.root.pos_ in ["NOUN", "PROPN"]:
                    phrase = re.sub(r'[^\w\s]', '', chunk.text).lower().strip()
                    
                    # 1. Filter out standalone numbers
                    if phrase.isdigit():
                        continue
                        
                    # 2. Filter out tokens dominated by digits (e.g. "500", "000")
                    if sum(c.isdigit() for c in phrase) > len(phrase) / 2:
                        continue
                        
                    # 3. Filter generic words, stopwords, and phrases
                    if phrase in generic_words or phrase in generic_phrases or phrase in stopwords:
                        continue
                        
                    # 4. Filter very short fragments unless it's a domain term
                    if len(phrase) < 3 and phrase not in valid_domain_terms:
                        continue
                        
                    valid_phrases.append(phrase)
                        
            processed_docs.append(" ".join([p.replace(" ", "_") for p in valid_phrases]))

        # 2. Apply TF-IDF on the extracted phrases
        min_df_val = 2 if len(processed_docs) >= 5 else 1
        
        # Prevent crash if no valid phrases were extracted across all documents
        if not any(d.strip() for d in processed_docs):
            return {
                "status": "AVAILABLE",
                "topics": [],
                "topic_count": 0
            }
            
        vectorizer = TfidfVectorizer(max_features=20, min_df=min_df_val, token_pattern=r"(?u)\S+")
        try:
            tfidf_matrix = vectorizer.fit_transform(processed_docs)
        except ValueError as e:
            if "empty vocabulary" in str(e).lower() or "no terms remain" in str(e).lower():
                return {
                    "status": "AVAILABLE",
                    "topics": [],
                    "topic_count": 0
                }
            raise
        
        feature_names = vectorizer.get_feature_names_out()
        scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
        
        # 3. Sort and format results
        top_indices = scores.argsort()[::-1]
        
        topics = []
        for i in top_indices:
            score = float(scores[i])
            if score > 0:
                original_phrase = feature_names[i].replace("_", " ")
                
                # Secondary safety filter to guarantee no stopwords/fragments slip through
                if original_phrase in stopwords or original_phrase in generic_words or original_phrase in generic_phrases:
                    continue
                    
                # Filter out numbers that might have slipped through
                if original_phrase.isdigit():
                    continue
                
                # Count document frequency for this phrase
                doc_freq = sum(1 for d in processed_docs if feature_names[i] in d)
                
                topics.append({
                    "topic_keyphrase": original_phrase,
                    "relevance_score": round(score, 4),
                    "document_count": doc_freq,
                    "frequency": doc_freq # Simplified frequency as document frequency
                })

        return {
            "status": "AVAILABLE",
            "topics": topics[:10],
            "topic_count": len(topics[:10])
        }

    except Exception as exc:
        logger.error("deterministic_topics_error", error=str(exc))
        return {
            "status": "ERROR",
            "topics": [],
            "topic_count": 0,
            "message": str(exc)
        }
