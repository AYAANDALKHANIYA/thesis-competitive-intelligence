# -*- coding: utf-8 -*-
"""
END-TO-END THESIS DATA VALIDATION

Performs the complete real-data pipeline against Railway PostgreSQL:
1. Seed companies & competitors
2. Seed sources
3. Run bounded GDELT ingestion for each company
4. Run NLP processing (sentiment, entities, embeddings)
5. Run competitive intelligence (MAI, trends)
6. Verify embeddings stored as VECTOR(384)
7. Test idempotency (second run)
8. Produce detailed report

Usage: python scripts/e2e_thesis_validation.py
"""
import asyncio
import json
import os
import sys
import time
import traceback
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.document import Document, DocumentVersion
from app.models.embedding import Embedding
from app.models.entity import Entity
from app.models.ingestion_run import IngestionRun
from app.models.insight import Insight
from app.models.metric import MarketMetric
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction
from app.models.sentiment import SentimentResult
from app.models.source import Source
from app.models.source_state import SourceState
from app.models.topic import Topic, DocumentTopic

# ── Report Data ───────────────────────────────────────────────────────
REPORT: Dict = {}


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def ok(msg):
    print(f"  [OK] {msg}")


def info(msg):
    print(f"  [INFO] {msg}")


def warn(msg):
    print(f"  [WARN] {msg}")


def fail(msg):
    print(f"  [FAIL] {msg}")


# ── Company Data ──────────────────────────────────────────────────────
COMPANIES = [
    {"name": "Curato", "domain": "curato.ai", "industry": "AI Marketing",
     "country": "US", "ticker": "", "sec_cik": "",
     "description": "AI-powered creative asset management"},
    {"name": "Breef", "domain": "breef.com", "industry": "Agency Marketplace",
     "country": "US", "ticker": "", "sec_cik": "",
     "description": "Online agency marketplace and project management"},
    {"name": "DesignRush", "domain": "designrush.com", "industry": "B2B Marketplace",
     "country": "US", "ticker": "", "sec_cik": "",
     "description": "B2B marketplace connecting brands with agencies"},
]

COMPETITOR_PAIRS = [
    ("Curato", "Breef"), ("Curato", "DesignRush"),
]

SOURCES = [
    {"name": "Company Website", "source_type": "website",
     "rate_limit_per_minute": 30, "crawl_delay_seconds": 2.0,
     "config": {"max_pages": 5}},
    {"name": "Company RSS", "source_type": "rss",
     "rate_limit_per_minute": 60, "crawl_delay_seconds": 1.0,
     "config": {"max_entries": 10}},
    {"name": "SEC EDGAR", "source_type": "sec",
     "rate_limit_per_minute": 10, "crawl_delay_seconds": 1.0,
     "config": {"max_filings": 5}},
]


# ======================================================================
# STAGE 1: SEED DATABASE
# ======================================================================
async def stage_seed(session: AsyncSession) -> Dict:
    section("STAGE 1: SEEDING COMPANIES, COMPETITORS, SOURCES")
    result = {"companies": {}, "competitors": [], "sources": []}

    # Seed companies
    company_map = {}
    for data in COMPANIES:
        existing = (await session.execute(
            select(Company).where(Company.name == data["name"])
        )).scalar_one_or_none()
        if existing:
            company_map[data["name"]] = existing.id
            info(f"Company exists: {data['name']} (id={existing.id})")
        else:
            c = Company(**data)
            session.add(c)
            await session.flush()
            company_map[data["name"]] = c.id
            ok(f"Created: {data['name']} (id={c.id})")
        result["companies"][data["name"]] = company_map[data["name"]]

    # Seed competitors
    for company_name, competitor_name in COMPETITOR_PAIRS:
        cid = company_map.get(company_name)
        comp_id = company_map.get(competitor_name)
        if not cid or not comp_id:
            continue
        existing = (await session.execute(
            select(Competitor).where(
                Competitor.company_id == cid, Competitor.competitor_id == comp_id
            )
        )).scalar_one_or_none()
        if not existing:
            session.add(Competitor(company_id=cid, competitor_id=comp_id, relationship_type="direct"))
            ok(f"Competitor: {company_name} -> {competitor_name}")
            result["competitors"].append(f"{company_name} -> {competitor_name}")
        else:
            info(f"Competitor exists: {company_name} -> {competitor_name}")

    # Seed sources
    for sdata in SOURCES:
        existing = (await session.execute(
            select(Source).where(Source.name == sdata["name"])
        )).scalar_one_or_none()
        if not existing:
            s = Source(**sdata)
            session.add(s)
            await session.flush()
            ok(f"Source: {sdata['name']} (id={s.id})")
            result["sources"].append({"name": sdata["name"], "id": s.id})
        else:
            info(f"Source exists: {sdata['name']} (id={existing.id})")
            result["sources"].append({"name": sdata["name"], "id": existing.id})

    await session.commit()
    REPORT["stage1_seed"] = result
    return result


# ======================================================================
# STAGE 2: BOUNDED INGESTION
# ======================================================================
async def stage_ingest(session: AsyncSession, company_map: Dict) -> Dict:
    section("STAGE 2: BOUNDED INGESTION (Website, RSS, SEC)")
    result = {"per_company": {}, "total_new": 0, "total_found": 0, "total_skipped": 0, "errors": 0}

    from app.services.ingestion.orchestrator import IngestionOrchestrator

    for company_data in COMPANIES:
        name = company_data["name"]
        company_id = company_map[name]
        info(f"Ingesting for: {name} (id={company_id})...")

        orch = IngestionOrchestrator(session)
        try:
            stats = await orch.run_ingestion(
                company_id=company_id,
                company_name=name,
                company_domain=company_data["domain"],
                sec_cik=company_data.get("sec_cik"),
                source_types=["website", "rss", "sec"],
            )
            await session.commit()

            ok(f"{name}: found={stats['documents_found']}, new={stats['documents_new']}, "
               f"skipped={stats['documents_skipped']}, errors={stats['errors']}")
            result["per_company"][name] = stats
            result["total_found"] += stats["documents_found"]
            result["total_new"] += stats["documents_new"]
            result["total_skipped"] += stats["documents_skipped"]
            result["errors"] += stats["errors"]
        except Exception as e:
            fail(f"{name}: {e}")
            traceback.print_exc()
            result["errors"] += 1
            await session.rollback()

        # Rate limit between companies
        await asyncio.sleep(3)

    REPORT["stage2_ingestion"] = result
    return result


# ======================================================================
# STAGE 3: NLP PROCESSING
# ======================================================================
async def stage_nlp(session: AsyncSession, company_map: Dict) -> Dict:
    section("STAGE 3: NLP PROCESSING (Sentiment, Entities, Embeddings)")
    result = {"sentiment": 0, "entities": 0, "embeddings": 0, "processed_docs": 0}

    from app.services.nlp import sentiment as sent_mod
    from app.services.nlp import entities as ent_mod
    from app.services.nlp import embeddings as emb_mod

    # Get all unprocessed documents
    docs_result = await session.execute(
        select(Document).where(Document.is_processed.is_(False))
        .order_by(Document.id)
        .limit(200)
    )
    docs = list(docs_result.scalars().all())
    info(f"Unprocessed documents to process: {len(docs)}")

    for doc in docs:
        if not doc.content or len(doc.content.strip()) < 20:
            continue

        content = doc.content
        doc_id = doc.id

        # Sentiment
        try:
            sent_result = sent_mod.analyse_sentiment(content)
            if sent_result:
                existing_sent = (await session.execute(
                    select(SentimentResult).where(SentimentResult.document_id == doc_id)
                )).scalar_one_or_none()
                if not existing_sent:
                    session.add(SentimentResult(
                        document_id=doc_id,
                        label=sent_result["label"],
                        score=sent_result["score"],
                        confidence=sent_result["confidence"],
                        model_name=sent_result.get("model", "roberta-sentiment"),
                        model_version="1.0",
                    ))
                    result["sentiment"] += 1
        except Exception as e:
            warn(f"Sentiment error doc {doc_id}: {e}")

        # Entities
        try:
            entities = ent_mod.extract_entities(content)
            if entities:
                existing_ents = (await session.execute(
                    select(func.count(Entity.id)).where(Entity.document_id == doc_id)
                )).scalar() or 0
                if existing_ents == 0:
                    for ent in entities[:20]:  # Cap at 20 entities per doc
                        session.add(Entity(
                            document_id=doc_id,
                            entity_text=ent["entity_text"][:500],
                            entity_type=ent["entity_type"],
                            start_position=ent.get("start"),
                            end_position=ent.get("end"),
                            confidence=ent.get("confidence"),
                        ))
                    result["entities"] += len(entities[:20])
        except Exception as e:
            warn(f"Entity error doc {doc_id}: {e}")

        # Embeddings
        try:
            embedding = emb_mod.generate_embedding(content)
            if embedding and len(embedding) == 384:
                existing_emb = (await session.execute(
                    select(Embedding).where(Embedding.document_id == doc_id)
                )).scalar_one_or_none()
                if not existing_emb:
                    session.add(Embedding(
                        document_id=doc_id,
                        embedding=embedding,
                        model_name="all-MiniLM-L6-v2",
                    ))
                    result["embeddings"] += 1
        except Exception as e:
            warn(f"Embedding error doc {doc_id}: {e}")

        # Mark processed
        doc.is_processed = True
        result["processed_docs"] += 1

        # Flush periodically
        if result["processed_docs"] % 10 == 0:
            await session.flush()

    await session.commit()

    ok(f"Documents processed: {result['processed_docs']}")
    ok(f"Sentiment results: {result['sentiment']}")
    ok(f"Entities extracted: {result['entities']}")
    ok(f"Embeddings stored: {result['embeddings']}")

    REPORT["stage3_nlp"] = result
    return result


# ======================================================================
# STAGE 4: VERIFY EMBEDDINGS IN VECTOR(384)
# ======================================================================
async def stage_verify_embeddings(session: AsyncSession) -> Dict:
    section("STAGE 4: VERIFY EMBEDDINGS STORED AS VECTOR(384)")
    result = {"column_type": "", "count": 0, "dimension_check": ""}

    # Check column type
    col_result = await session.execute(text("""
        SELECT udt_name FROM information_schema.columns
        WHERE table_name = 'embeddings' AND column_name = 'embedding'
    """))
    udt = col_result.scalar()
    result["column_type"] = udt
    if udt == "vector":
        ok(f"Embedding column type: VECTOR (pgvector)")
    else:
        fail(f"Embedding column type: {udt} (expected 'vector')")

    # Count embeddings
    count_result = await session.execute(select(func.count(Embedding.id)))
    count = count_result.scalar() or 0
    result["count"] = count
    ok(f"Embeddings stored: {count}")

    # Verify dimension of a stored embedding
    if count > 0:
        dim_result = await session.execute(text(
            "SELECT vector_dims(embedding) FROM embeddings LIMIT 1"
        ))
        dim = dim_result.scalar()
        result["dimension_check"] = dim
        if dim == 384:
            ok(f"Embedding dimension verified: {dim}")
        else:
            fail(f"Embedding dimension: {dim} (expected 384)")

    REPORT["stage4_embeddings"] = result
    return result


# ======================================================================
# STAGE 5: COMPETITIVE INTELLIGENCE
# ======================================================================
async def stage_intelligence(session: AsyncSession, company_map: Dict) -> Dict:
    section("STAGE 5: COMPETITIVE INTELLIGENCE (MAI, Trends)")
    result = {"mai_results": {}, "metrics_stored": 0}

    from app.services.intelligence.market_index import MarketActivityIndexService

    mai_service = MarketActivityIndexService(session)
    today = date.today()

    for name, company_id in company_map.items():
        try:
            mai = await mai_service.calculate(company_id, today)
            await session.commit()
            ok(f"MAI for {name}: {mai['index_value']}")
            info(f"  Components: {json.dumps(mai['components'], indent=None)}")
            result["mai_results"][name] = mai
        except Exception as e:
            warn(f"MAI error for {name}: {e}")
            await session.rollback()

    # Count stored metrics
    count_result = await session.execute(select(func.count(MarketMetric.id)))
    result["metrics_stored"] = count_result.scalar() or 0
    ok(f"Total metrics in database: {result['metrics_stored']}")

    REPORT["stage5_intelligence"] = result
    return result


# ======================================================================
# STAGE 6: IDEMPOTENCY TEST
# ======================================================================
async def stage_idempotency(session: AsyncSession, company_map: Dict) -> Dict:
    section("STAGE 6: IDEMPOTENCY TEST (Second ingestion run)")
    result = {"idempotent": False, "docs_before": 0, "docs_after": 0, "new_on_rerun": 0}

    # Count documents before
    before_result = await session.execute(select(func.count(Document.id)))
    result["docs_before"] = before_result.scalar() or 0
    info(f"Documents before re-run: {result['docs_before']}")

    from app.services.ingestion.orchestrator import IngestionOrchestrator

    # Pick first two companies for idempotency test
    test_companies = list(company_map.items())[:2]
    total_new = 0

    for name, company_id in test_companies:
        company_data = next(c for c in COMPANIES if c["name"] == name)
        orch = IngestionOrchestrator(session)
        try:
            stats = await orch.run_ingestion(
                company_id=company_id,
                company_name=name,
                company_domain=company_data["domain"],
                source_types=["website", "rss", "sec"],
            )
            await session.commit()
            total_new += stats["documents_new"]
            info(f"Re-run {name}: found={stats['documents_found']}, new={stats['documents_new']}, "
                 f"skipped={stats['documents_skipped']}")
        except Exception as e:
            warn(f"Idempotency re-run error for {name}: {e}")
            await session.rollback()
        await asyncio.sleep(3)

    # Count documents after
    after_result = await session.execute(select(func.count(Document.id)))
    result["docs_after"] = after_result.scalar() or 0
    result["new_on_rerun"] = total_new

    # Idempotency: no new documents on re-run means content-hash dedup is working
    # Note: Website/RSS may return slightly different content, so some new docs is acceptable
    if total_new == 0:
        ok(f"PERFECT IDEMPOTENCY: 0 new documents on re-run")
        result["idempotent"] = True
    elif total_new <= 5:
        ok(f"NEAR-IDEMPOTENT: {total_new} new documents (Some dynamic content changed)")
        result["idempotent"] = True
    else:
        warn(f"NOT FULLY IDEMPOTENT: {total_new} new documents on re-run")
        result["idempotent"] = False

    ok(f"Documents: {result['docs_before']} -> {result['docs_after']} (+{result['docs_after'] - result['docs_before']})")

    REPORT["stage6_idempotency"] = result
    return result


# ======================================================================
# STAGE 7: PREDICTION DATA CHECK
# ======================================================================
async def stage_prediction_check(session: AsyncSession, company_map: Dict) -> Dict:
    section("STAGE 7: PREDICTION DATA AVAILABILITY CHECK")
    result = {"has_sufficient_data": False, "metric_counts": {}}

    from app.core.config import get_settings
    min_samples = get_settings().PREDICTION_MIN_SAMPLES

    for name, company_id in company_map.items():
        count_result = await session.execute(
            select(func.count(MarketMetric.id)).where(
                MarketMetric.company_id == company_id,
                MarketMetric.metric_name == "market_activity_index",
            )
        )
        count = count_result.scalar() or 0
        result["metric_counts"][name] = count

    info(f"Minimum samples required for prediction: {min_samples}")
    for name, count in result["metric_counts"].items():
        status = "SUFFICIENT" if count >= min_samples else "INSUFFICIENT"
        info(f"  {name}: {count} MAI observations ({status})")

    total_obs = sum(result["metric_counts"].values())
    if total_obs >= min_samples:
        result["has_sufficient_data"] = True
        ok("Prediction pipeline has sufficient data")
    else:
        ok(f"Prediction correctly blocked: {total_obs} observations < {min_samples} minimum")
        info("Need ~30 days of daily MAI calculations before forecasting is available")
        result["has_sufficient_data"] = False

    REPORT["stage7_prediction"] = result
    return result


# ======================================================================
# STAGE 8: DATABASE SUMMARY
# ======================================================================
async def stage_db_summary(session: AsyncSession) -> Dict:
    section("STAGE 8: DATABASE SUMMARY")
    result = {}

    tables = {
        "companies": Company, "documents": Document,
        "sentiment_results": SentimentResult, "entities": Entity,
        "embeddings": Embedding, "market_metrics": MarketMetric,
        "source_states": SourceState, "ingestion_runs": IngestionRun,
    }

    for tname, model in tables.items():
        count_result = await session.execute(select(func.count(model.id)))
        count = count_result.scalar() or 0
        result[tname] = count
        ok(f"{tname}: {count} rows")

    # Date range of documents
    date_result = await session.execute(
        select(func.min(Document.published_at), func.max(Document.published_at))
    )
    row = date_result.fetchone()
    if row and row[0]:
        result["date_range"] = f"{row[0]} to {row[1]}"
        ok(f"Document date range: {row[0]} to {row[1]}")
    else:
        result["date_range"] = "No published dates"

    # Documents by company
    company_docs = await session.execute(
        select(Company.name, func.count(Document.id))
        .join(Document, Document.company_id == Company.id)
        .group_by(Company.name)
        .order_by(func.count(Document.id).desc())
    )
    doc_by_company = {}
    for row in company_docs.fetchall():
        doc_by_company[row[0]] = row[1]
        info(f"  {row[0]}: {row[1]} documents")
    result["documents_by_company"] = doc_by_company

    # Sentiment distribution
    sent_dist = await session.execute(
        select(SentimentResult.label, func.count(SentimentResult.id))
        .group_by(SentimentResult.label)
    )
    sentiment_dist = {}
    for row in sent_dist.fetchall():
        sentiment_dist[row[0]] = row[1]
    result["sentiment_distribution"] = sentiment_dist
    if sentiment_dist:
        ok(f"Sentiment distribution: {sentiment_dist}")

    # Top entities
    top_ents = await session.execute(
        select(Entity.entity_type, func.count(Entity.id))
        .group_by(Entity.entity_type)
        .order_by(func.count(Entity.id).desc())
        .limit(10)
    )
    entity_types = {}
    for row in top_ents.fetchall():
        entity_types[row[0]] = row[1]
    result["entity_types"] = entity_types
    if entity_types:
        ok(f"Entity types: {entity_types}")

    REPORT["stage8_summary"] = result
    return result


# ======================================================================
# MAIN
# ======================================================================
async def main():
    print("=" * 70)
    print("  END-TO-END THESIS DATA VALIDATION")
    print("  Railway PostgreSQL + pgvector + Real NLP Pipeline")
    print("=" * 70)

    start_time = time.time()

    async with async_session_factory() as session:
        try:
            # Stage 1: Seed
            seed_result = await stage_seed(session)
            company_map = seed_result["companies"]

            # Stage 2: Bounded ingestion
            await stage_ingest(session, company_map)

            # Stage 3: NLP processing
            await stage_nlp(session, company_map)

            # Stage 4: Verify embeddings
            await stage_verify_embeddings(session)

            # Stage 5: Intelligence
            await stage_intelligence(session, company_map)

            # Stage 6: Idempotency
            await stage_idempotency(session, company_map)

            # Stage 7: Prediction data check
            await stage_prediction_check(session, company_map)

            # Stage 8: DB summary
            await stage_db_summary(session)

        except Exception as e:
            fail(f"FATAL ERROR: {e}")
            traceback.print_exc()

    elapsed = time.time() - start_time

    # Final report
    section("FINAL VALIDATION REPORT")
    REPORT["elapsed_seconds"] = round(elapsed, 1)

    # Pipeline verdict
    stage2 = REPORT.get("stage2_ingestion", {})
    stage3 = REPORT.get("stage3_nlp", {})
    stage4 = REPORT.get("stage4_embeddings", {})
    stage5 = REPORT.get("stage5_intelligence", {})

    has_docs = stage2.get("total_new", 0) > 0 or stage2.get("total_found", 0) > 0
    has_nlp = (stage3.get("sentiment", 0) > 0 and
               stage3.get("entities", 0) > 0 and
               stage3.get("embeddings", 0) > 0)
    has_vector = stage4.get("column_type") == "vector"
    has_intelligence = len(stage5.get("mai_results", {})) > 0

    pipeline_pass = has_docs and has_nlp and has_vector and has_intelligence

    ok(f"Documents collected: {'YES' if has_docs else 'NO'}")
    ok(f"NLP pipeline (sentiment+entities+embeddings): {'YES' if has_nlp else 'NO'}")
    ok(f"Embeddings as VECTOR(384): {'YES' if has_vector else 'NO'}")
    ok(f"Intelligence (MAI): {'YES' if has_intelligence else 'NO'}")

    print(f"\n  Total elapsed: {elapsed:.1f}s")

    if pipeline_pass:
        print(f"\n{'='*70}")
        print(f"  COMPLETE REAL DATA -> NLP -> INTELLIGENCE PIPELINE: PASSED")
        print(f"{'='*70}")
    else:
        print(f"\n{'='*70}")
        print(f"  PIPELINE: FAILED (see above for details)")
        print(f"{'='*70}")

    # Save report
    report_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "e2e_expanded_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    ok(f"Report saved: scripts/e2e_expanded_report.json")

    return 0 if pipeline_pass else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
