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
    company_id: int | None = None, batch_size: int = 32
) -> Dict[str, int]:
    """Process all unprocessed documents through NLP pipeline."""
    settings = get_settings()
    from app.db.session import async_session_factory
    
    stats = {"processed": 0, "sentiment": 0, "entities": 0, "embeddings": 0, "errors": 0}

    # READ REQUIRED DATA
    async with async_session_factory() as session:
        doc_repo = DocumentRepository(session)
        docs = await doc_repo.get_unprocessed(limit=batch_size, company_id=company_id)
        if not docs:
            return stats
        
        # Extract primitive data needed before closing the session
        docs_data = [{"id": d.id, "content": d.content or ""} for d in docs]
    # Session is closed here.
    
    texts = [d["content"] for d in docs_data]

    # LONG-RUNNING AI/NLP PROCESSING (No active DB session)
    import asyncio
    loop = asyncio.get_running_loop()
    
    try:
        sentiment_results = await loop.run_in_executor(
            None, 
            sentiment_svc.analyse_batch, 
            texts, 
            settings.NLP_BATCH_SIZE
        )
    except Exception as exc:
        logger.error("batch_sentiment_error", error=str(exc))
        stats["errors"] += 1
        raise

    try:
        def extract_all(texts):
            return [entity_svc.extract_entities(text) for text in texts]
        
        all_entities = await loop.run_in_executor(None, extract_all, texts)
    except Exception as exc:
        logger.error("batch_entity_error", error=str(exc))
        stats["errors"] += 1
        raise

    try:
        emb_results = await loop.run_in_executor(
            None,
            embedding_svc.generate_batch,
            texts,
            settings.NLP_BATCH_SIZE
        )
    except Exception as exc:
        logger.error("batch_embedding_error", error=str(exc))
        stats["errors"] += 1
        raise

    # CREATE FRESH SESSION TO WRITE RESULTS
    async with async_session_factory() as session:
        analysis_repo = AnalysisRepository(session)
        doc_repo = DocumentRepository(session)
        
        try:
            for doc_data, result, entities, emb in zip(docs_data, sentiment_results, all_entities, emb_results):
                doc_id = doc_data["id"]
                
                # Write sentiment
                if result:
                    label_val = str(result["label"]) if result["label"] is not None else "unknown"
                    score_val = float(result["score"])
                    conf_val = float(result["confidence"])
                    await analysis_repo.create_sentiment(
                        document_id=doc_id,
                        label=label_val,
                        score=score_val,
                        confidence=conf_val,
                        model_name=str(result["model_name"]),
                        model_version=str(result["model_version"]),
                    )
                    stats["sentiment"] += 1
                    
                # Write entities
                for ent in entities:
                    await analysis_repo.create_entity(
                        document_id=doc_id,
                        entity_text=str(ent["entity_text"]),
                        entity_type=str(ent["entity_type"]),
                        start_position=int(ent["start_position"]) if ent.get("start_position") is not None else None,
                        end_position=int(ent["end_position"]) if ent.get("end_position") is not None else None,
                        confidence=float(ent["confidence"]) if ent.get("confidence") is not None else None,
                    )
                    stats["entities"] += 1
                    
                # Write embeddings
                if emb:
                    if len(emb) != 384:
                        raise ValueError(f"Invalid embedding dimension: expected 384, got {len(emb)}")
                    existing = await analysis_repo.has_embedding(doc_id)
                    if not existing:
                        await analysis_repo.create_embedding(
                            document_id=doc_id,
                            embedding=emb,
                            model_name=settings.EMBEDDING_MODEL,
                        )
                        stats["embeddings"] += 1
                
                # Mark document as processed
                await doc_repo.mark_processed(doc_id)
                stats["processed"] += 1
                
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("batch_write_error", error=str(exc))
            stats["errors"] += 1
            raise

    logger.info("nlp_processing_complete", **stats)
    return stats
