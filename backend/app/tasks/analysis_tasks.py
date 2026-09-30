"""
NLP processing task — processes unprocessed documents through the NLP pipeline.
"""

from __future__ import annotations

from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.analysis import AnalysisRepository
from app.repositories.documents import DocumentRepository
from app.services.nlp import sentiment as sentiment_svc
from app.services.nlp import entities as entity_svc
from app.services.nlp import embeddings as embedding_svc

logger = get_logger(__name__)


async def process_unprocessed_documents(
    db: AsyncSession, company_id: int | None = None, batch_size: int = 32
) -> Dict[str, int]:
    """Process all unprocessed documents through NLP pipeline."""
    settings = get_settings()
    doc_repo = DocumentRepository(db)
    analysis_repo = AnalysisRepository(db)

    docs = await doc_repo.get_unprocessed(
        limit=batch_size, company_id=company_id
    )

    stats = {"processed": 0, "sentiment": 0, "entities": 0, "embeddings": 0, "errors": 0}

    if not docs:
        return stats

    texts = [d.content or "" for d in docs]

    # Batch sentiment
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        sentiment_results = await loop.run_in_executor(
            None, 
            sentiment_svc.analyse_batch, 
            texts, 
            settings.NLP_BATCH_SIZE
        )
        for doc, result in zip(docs, sentiment_results):
            if result:
                label_val = str(result["label"]) if result["label"] is not None else "unknown"
                score_val = float(result["score"])
                conf_val = float(result["confidence"])
                logger.info(f"Inserting sentiment doc={doc.id} label={label_val} score={score_val}")
                await analysis_repo.create_sentiment(
                    document_id=doc.id,
                    label=label_val,
                    score=score_val,
                    confidence=conf_val,
                    model_name=str(result["model_name"]),
                    model_version=str(result["model_version"]),
                )
                stats["sentiment"] += 1
    except Exception as exc:
        await db.rollback()
        logger.error("batch_sentiment_error", error=str(exc))
        stats["errors"] += 1
        raise

    # Batch entity extraction
    try:
        def extract_all(docs):
            return [entity_svc.extract_entities(doc.content or "") for doc in docs]
        
        all_entities = await loop.run_in_executor(None, extract_all, docs)
        
        for doc, entities in zip(docs, all_entities):
            for ent in entities:
                await analysis_repo.create_entity(
                    document_id=doc.id,
                    entity_text=str(ent["entity_text"]),
                    entity_type=str(ent["entity_type"]),
                    start_position=int(ent["start_position"]) if ent.get("start_position") is not None else None,
                    end_position=int(ent["end_position"]) if ent.get("end_position") is not None else None,
                    confidence=float(ent["confidence"]) if ent.get("confidence") is not None else None,
                )
                stats["entities"] += 1
    except Exception as exc:
        await db.rollback()
        logger.error("batch_entity_error", error=str(exc))
        stats["errors"] += 1
        raise

    # Batch embeddings
    try:
        emb_results = await loop.run_in_executor(
            None,
            embedding_svc.generate_batch,
            texts,
            settings.NLP_BATCH_SIZE
        )
        for doc, emb in zip(docs, emb_results):
            if emb:
                if len(emb) != 384:
                    raise ValueError(f"Invalid embedding dimension: expected 384, got {len(emb)}")
                existing = await analysis_repo.has_embedding(doc.id)
                if not existing:
                    await analysis_repo.create_embedding(
                        document_id=doc.id,
                        embedding=emb,
                        model_name=settings.EMBEDDING_MODEL,
                    )
                    stats["embeddings"] += 1
    except Exception as exc:
        await db.rollback()
        logger.error("batch_embedding_error", error=str(exc))
        stats["errors"] += 1
        raise

    # Mark documents as processed
    for doc in docs:
        await doc_repo.mark_processed(doc.id)
        stats["processed"] += 1

    logger.info("nlp_processing_complete", **stats)
    return stats
