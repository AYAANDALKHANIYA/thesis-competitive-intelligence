"""Analysis pipeline orchestrator for the simplified flow."""

import asyncio
import time
from datetime import datetime, timezone, timedelta
import json
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import PendingRollbackError

from app.core.logging import get_logger
from app.models.analysis import AnalysisRun, AnalysisCompetitor
from app.models.company import Company
from app.models.document import Document
from app.models.metric import MarketMetric
from app.models.insight import Insight
from app.models.review import Review
from app.models.sentiment import SentimentResult
from app.models.topic import Topic, DocumentTopic

from app.services.extraction.website import WebsiteExtractor
from app.services.extraction.gdelt import GDELTExtractor
from app.services.extraction.pagespeed import PageSpeedExtractor
from app.services.extraction.base import ExtractionResult
from app.tasks.analysis_tasks import process_unprocessed_documents
from app.services.llm.insight_generator import InsightGenerator

from app.services.nlp.topics import extract_deterministic_topics
from app.db.session import async_session_factory

logger = get_logger(__name__)

async def _save_documents(session: AsyncSession, company_id: int, results: List[ExtractionResult]) -> List[Document]:
    pass # Replaced by inline _save

async def _ensure_source(session: AsyncSession, name: str, type: str) -> int:
    from app.models.source import Source
    res = await session.execute(select(Source).where(Source.name == name))
    source = res.scalars().first()
    if not source:
        source = Source(name=name, source_type=type)
        session.add(source)
        await session.flush()
    return source.id

async def run_analysis_pipeline(analysis_id: int):
    """Run the complete competitive intelligence pipeline for an analysis run."""
    
    # 1. Fetch AnalysisRun (Short session)
    logger.info("db_session_opened")
    async with async_session_factory() as session:
        res = await session.execute(
            select(AnalysisRun)
            .options(selectinload(AnalysisRun.company), selectinload(AnalysisRun.competitors).selectinload(AnalysisCompetitor.competitor_company))
            .where(AnalysisRun.id == analysis_id)
        )
        analysis = res.scalars().first()
        if not analysis:
            logger.error(f"AnalysisRun {analysis_id} not found.")
            return
            
        if analysis.status != "COMPLETED":
            analysis.status = "RUNNING"
            analysis.started_at = datetime.now(timezone.utc)
            
        primary_company = analysis.company
        primary_company_id = primary_company.id
        primary_company_name = primary_company.name
        
        # We extract primitives since we will close the session
        companies_to_process = []
        companies_to_process.append({"id": primary_company.id, "name": primary_company.name, "domain": primary_company.domain})
        for c in analysis.competitors:
            companies_to_process.append({
                "id": c.competitor_company.id, 
                "name": c.competitor_company.name, 
                "domain": c.competitor_company.domain
            })
            
        web_source_id = await _ensure_source(session, "Pipeline Website Crawl", "website")
        news_source_id = await _ensure_source(session, "Pipeline GDELT", "gdelt")
        await session.commit()
    logger.info("db_session_closed")
    
    try:
        website_extractor = WebsiteExtractor()
        gdelt_extractor = GDELTExtractor()
        pagespeed_extractor = PageSpeedExtractor()
        
        metrics_to_add_dicts = []
        insights_to_add_dicts = []
        status_update = "COMPLETED"
        
        for comp in companies_to_process:
            logger.info(f"Processing company: {comp['name']}")
            web_results = []
            news_results = []
            seo_score = None
            web_extraction_success = False
            news_extraction_success = False
            
            # 2. Website Collection & 3. SEO Analysis
            try:
                web_results = await website_extractor.extract(comp['name'], comp['domain'], {"max_pages": 15})
                web_extraction_success = True
                if web_results:
                    valid_pages = [r for r in web_results if r.metadata.get("status_code") == 200]
                    has_title = sum(1 for r in valid_pages if r.title)
                    has_meta = sum(1 for r in valid_pages if r.metadata.get("meta_description"))
                    has_h1 = sum(1 for r in valid_pages if r.metadata.get("h1_tags"))
                    has_h2 = sum(1 for r in valid_pages if r.metadata.get("h2_tags"))
                    has_canonical = sum(1 for r in valid_pages if r.metadata.get("has_canonical"))
                    has_schema = sum(1 for r in valid_pages if r.metadata.get("has_schema"))
                    
                    total_images = sum(r.metadata.get("images_count", 0) for r in valid_pages)
                    alt_images = sum(r.metadata.get("images_with_alt", 0) for r in valid_pages)
                    
                    score_components = {
                        "pages_crawled": len(valid_pages),
                        "title_coverage": (has_title / len(valid_pages) * 100) if valid_pages else 0,
                        "meta_coverage": (has_meta / len(valid_pages) * 100) if valid_pages else 0,
                        "h1_coverage": (has_h1 / len(valid_pages) * 100) if valid_pages else 0,
                        "h2_coverage": (has_h2 / len(valid_pages) * 100) if valid_pages else 0,
                        "canonical_coverage": (has_canonical / len(valid_pages) * 100) if valid_pages else 0,
                        "schema_coverage": (has_schema / len(valid_pages) * 100) if valid_pages else 0,
                        "image_alt_coverage": (alt_images / total_images * 100) if total_images > 0 else 100,
                    }
                    
                    if valid_pages:
                        seo_score = (
                            score_components["title_coverage"] * 0.2 + 
                            score_components["meta_coverage"] * 0.2 + 
                            score_components["h1_coverage"] * 0.1 +
                            score_components["h2_coverage"] * 0.1 +
                            score_components["canonical_coverage"] * 0.1 +
                            score_components["schema_coverage"] * 0.1 +
                            score_components["image_alt_coverage"] * 0.2
                        )
                    
                    metrics_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "metric_name": "Technical SEO Score",
                        "metric_value": seo_score,
                        "metric_date": datetime.now(timezone.utc).date(),
                        "components": score_components
                    })
                else:
                    metrics_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "metric_name": "Technical SEO Score",
                        "metric_value": 0.0,
                        "metric_date": datetime.now(timezone.utc).date(),
                        "components": {"status": "unavailable", "message": "Website extraction failed or returned no pages."}
                    })
            except Exception as e:
                logger.error(f"Website extraction failed for {comp['name']}: {e}")
                status_update = "PARTIAL"
                metrics_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "metric_name": "Technical SEO Score",
                    "metric_value": 0.0,
                    "metric_date": datetime.now(timezone.utc).date(),
                    "components": {"status": "unavailable", "message": f"Website extraction failed: {str(e)}"}
                })
            
            # 4. PageSpeed Analysis (Real)
            try:
                ps_data = await pagespeed_extractor.extract(comp['domain'])
                if ps_data:
                    metrics_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "metric_name": "PageSpeed",
                        "metric_value": ps_data.get("performance", 0.0),
                        "metric_date": datetime.now(timezone.utc).date(),
                        "components": ps_data
                    })
                else:
                    metrics_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "metric_name": "PageSpeed",
                        "metric_value": None,
                        "metric_date": datetime.now(timezone.utc).date(),
                        "components": {"status": "unavailable", "message": "Performance data unavailable"}
                    })
            except Exception as e:
                logger.error(f"PageSpeed extraction failed for {comp['name']}: {e}")
                status_update = "PARTIAL"
                metrics_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "metric_name": "PageSpeed",
                    "metric_value": None, # PageSpeed unavailable
                    "metric_date": datetime.now(timezone.utc).date(),
                    "components": {"status": "unavailable", "message": "Performance data unavailable"}
                })

            # 6. GDELT News Collection
            try:
                news_results = await gdelt_extractor.extract(comp['name'], comp['domain'], {"max_records": 10})
                news_extraction_success = True
            except Exception as e:
                logger.error(f"GDELT extraction failed for {comp['name']}: {e}")
                status_update = "PARTIAL"
            
            # 7. Save Documents to DB
            for r in web_results: r.source_type = "website"
            for r in news_results: r.source_type = "gdelt"
            
            for r in web_results: r.source_id = web_source_id
            for r in news_results: r.source_id = news_source_id
            
            async def _save(session, results, s_id, force_published_at_none=False):
                import hashlib
                docs = []
                for r in results:
                    url = r.url[:2000]
                    content = r.content or ""
                    c_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                    pub_at = None if force_published_at_none else r.published_at
                    
                    existing_result = await session.execute(
                        select(Document).where(Document.company_id == comp['id'], Document.url == url)
                    )
                    existing_doc = existing_result.scalars().first()
                    
                    if existing_doc:
                        if existing_doc.content_hash == c_hash:
                            docs.append(existing_doc)
                            continue
                        else:
                            existing_doc.content = content
                            existing_doc.content_hash = c_hash
                            existing_doc.title = r.title[:500] if r.title else None
                            existing_doc.is_processed = False
                            if pub_at:
                                existing_doc.published_at = pub_at
                            docs.append(existing_doc)
                            continue
                    
                    new_doc = Document(
                        company_id=comp['id'],
                        source_id=s_id,
                        url=url,
                        title=r.title[:500] if r.title else None,
                        content=content,
                        content_hash=c_hash,
                        document_type=r.document_type,
                        metadata_=r.metadata,
                        published_at=pub_at
                    )
                    session.add(new_doc)
                    docs.append(new_doc)
                    
                await session.flush()
                return docs

            logger.info("db_session_opened")
            async with async_session_factory() as session:
                web_docs = await _save(session, web_results, web_source_id, force_published_at_none=True)
                news_docs = await _save(session, news_results, news_source_id)
                await session.commit()
            logger.info("db_session_closed")
            
            # 8. NLP processing
            if web_docs or news_docs:
                try:
                    logger.info("nlp_processing_started")
                    await process_unprocessed_documents(comp['id'])
                    logger.info("nlp_processing_completed")
                except Exception as e:
                    logger.error(f"NLP processing failed for {comp['name']}: {e}")
                    raise

            # 8b. Fetch fresh data for analysis calculations
            logger.info("db_session_opened")
            async with async_session_factory() as session:
                # 5. G2/Capterra Review Data
                reviews_result = await session.execute(select(Review).where(Review.company_id == comp['id']))
                reviews = reviews_result.scalars().all()
                review_count = len(reviews)
                
                if reviews:
                    avg_rating = sum(r.rating for r in reviews) / review_count
                    metrics_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "metric_name": "Review Sentiment",
                        "metric_value": avg_rating,
                        "metric_date": datetime.now(timezone.utc).date(),
                        "components": {"status": "available", "count": review_count, "avg_rating": avg_rating}
                    })
                else:
                    metrics_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "metric_name": "Review Sentiment",
                        "metric_value": 0.0,
                        "metric_date": datetime.now(timezone.utc).date(),
                        "components": {"status": "unavailable", "message": "Review data unavailable for this source"}
                    })
                
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                res_hist_docs = await session.execute(
                    select(Document).where(Document.company_id == comp['id'], Document.published_at < seven_days_ago)
                )
                hist_docs = res_hist_docs.scalars().all()
                hist_docs_data = []
                for d in hist_docs:
                    hist_docs_data.append({
                        "content": d.content,
                        "title": d.title,
                        "document_type": d.document_type,
                        "source_type": getattr(d, 'source_type', 'website')
                    })
                    
                # We need all current documents associated with this run to calculate stats
                # Re-fetch web and news docs to get valid IDs and content
                all_current_docs = []
                if web_results or news_results:
                    urls = [r.url[:2000] for r in web_results + news_results]
                    if urls:
                        res_curr = await session.execute(
                            select(Document).where(Document.company_id == comp['id'], Document.url.in_(urls))
                        )
                        all_current_docs = res_curr.scalars().all()
                
                all_docs_data = []
                for d in all_current_docs:
                    all_docs_data.append({
                        "id": d.id,
                        "content": d.content,
                        "title": d.title,
                        "document_type": d.document_type,
                        "source_type": getattr(d, 'source_type', 'website')
                    })
                    
                web_docs_count = len([d for d in all_docs_data if d["source_type"] == "website"])
                news_docs_count = len([d for d in all_docs_data if d["source_type"] == "gdelt"])

                # Sentiment
                doc_ids = [d["id"] for d in all_docs_data]
                sentiments_data = []
                if doc_ids:
                    res_sent = await session.execute(select(SentimentResult).where(SentimentResult.document_id.in_(doc_ids)))
                    sentiments = res_sent.scalars().all()
                    for s in sentiments:
                        s.analysis_id = analysis_id
                        sentiments_data.append(s.label.lower())
                
                await session.commit()
            logger.info("db_session_closed")
            
            # Calculate Activity Scores Safely based on requested methodology
            total_weight = 0.0
            market_activity_score = 0.0
            components_status = {}
            
            # Content Activity (30%)
            if web_extraction_success and web_docs_count > 0:
                ca_score = min(web_docs_count * 5, 100)
                market_activity_score += ca_score * 0.3
                total_weight += 0.3
                components_status["Content Activity"] = ca_score
                metrics_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "metric_name": "Content Activity",
                    "metric_value": ca_score,
                    "metric_date": datetime.now(timezone.utc).date()
                })
            else:
                components_status["Content Activity"] = "UNAVAILABLE"
                
            # Review/Mention Activity (30%)
            if review_count > 0 or news_extraction_success:
                rm_score = min(review_count * 20 + news_docs_count * 10, 100)
                market_activity_score += rm_score * 0.3
                total_weight += 0.3
                components_status["Review/Mention Activity"] = rm_score
                metrics_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "metric_name": "Review/Mention Activity",
                    "metric_value": rm_score,
                    "metric_date": datetime.now(timezone.utc).date()
                })
            else:
                components_status["Review/Mention Activity"] = "UNAVAILABLE"
            
            # Topic Extraction & Momentum (20%)
            doc_texts = []
            for d in all_docs_data:
                if d["content"]:
                    doc_texts.append(d["content"])
                elif d["title"]:
                    doc_texts.append(d["title"])
                    
            current_topic_res = extract_deterministic_topics(doc_texts)
            
            if current_topic_res.get("status") == "AVAILABLE":
                logger.info("db_session_opened")
                async with async_session_factory() as session:
                    for i, topic_data in enumerate(current_topic_res.get("topics", [])):
                        topic_keyphrase = topic_data["topic_keyphrase"]
                        res_topic = await session.execute(select(Topic).where(Topic.name == topic_keyphrase))
                        topic = res_topic.scalars().first()
                        if not topic:
                            topic = Topic(
                                topic_key=i,
                                name=topic_keyphrase,
                                model_version="deterministic_1.0",
                                document_count=topic_data["document_count"],
                            )
                            session.add(topic)
                            await session.flush()
                        assigned = 0
                        for d in all_docs_data:
                            if d["content"] and topic_keyphrase in d["content"].lower():
                                dt = DocumentTopic(
                                    document_id=d["id"],
                                    topic_id=topic.id,
                                    probability=1.0
                                )
                                session.add(dt)
                                assigned += 1
                            if assigned >= topic_data["document_count"]:
                                break
                    await session.commit()
                logger.info("db_session_closed")
                
                if len(hist_docs_data) >= 5:
                    hist_topic_res = extract_deterministic_topics([d["content"] for d in hist_docs_data if d.get("content")])
                    if hist_topic_res.get("status") == "AVAILABLE":
                        hist_topics = {t["topic_keyphrase"] for t in hist_topic_res["topics"]}
                        curr_topics = {t["topic_keyphrase"] for t in current_topic_res["topics"]}
                        kept_or_new = len(curr_topics)
                        topic_momentum = min(max(kept_or_new * 10, 0), 100)
                        
                        components_status["Topic Momentum"] = topic_momentum
                        market_activity_score += topic_momentum * 0.2
                        total_weight += 0.2
                        metrics_to_add_dicts.append({
                            "company_id": comp['id'],
                            "analysis_id": analysis_id,
                            "metric_name": "Topic Momentum",
                            "metric_value": topic_momentum,
                            "metric_date": datetime.now(timezone.utc).date()
                        })
                    else:
                        components_status["Topic Momentum"] = "UNAVAILABLE"
                else:
                    components_status["Topic Momentum"] = "INSUFFICIENT_DATA"
            else:
                components_status["Topic Momentum"] = "UNAVAILABLE"
            
            # Sentiment (20%)
            if sentiments_data:
                score_map = {"positive": 100, "neutral": 50, "negative": 0}
                sent_score = sum(score_map.get(lbl, 50) for lbl in sentiments_data) / len(sentiments_data)
                market_activity_score += sent_score * 0.2
                total_weight += 0.2
                components_status["Sentiment"] = sent_score
            else:
                components_status["Sentiment"] = "UNAVAILABLE"
                
            # Final MAI
            if total_weight >= 0.5:
                final_score = market_activity_score / total_weight
                components_status["note"] = "Calculated using available components with proportional weight adjustment."
                components_status["status"] = "available"
                metrics_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "metric_name": "market_activity_index",
                    "metric_value": final_score,
                    "metric_date": datetime.now(timezone.utc).date(),
                    "components": components_status
                })
            else:
                components_status["note"] = "Not enough usable data was collected to calculate a reliable Market Activity Score."
                components_status["status"] = "insufficient_data"
                metrics_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "metric_name": "market_activity_index",
                    "metric_value": None,
                    "metric_date": datetime.now(timezone.utc).date(),
                    "components": components_status
                })
            
            # 9. Growth Signals
            if len(hist_docs_data) < 5:
                insights_to_add_dicts.append({
                    "company_id": comp['id'],
                    "analysis_id": analysis_id,
                    "insight_type": "Growth Signal",
                    "title": "Growth Signals",
                    "summary": "INSUFFICIENT HISTORICAL DATA",
                    "evidence": {"evidence": "Fewer than 5 historical documents found."},
                    "confidence": None,
                    "severity": "info"
                })
            else:
                hist_web_docs = [d for d in hist_docs_data if d["source_type"] == 'website']
                if web_docs_count > len(hist_web_docs) and len(hist_web_docs) > 0:
                    insights_to_add_dicts.append({
                        "company_id": comp['id'],
                        "analysis_id": analysis_id,
                        "insight_type": "Growth Signal",
                        "title": "Content expansion",
                        "summary": "Content activity expanded in the recent observation period.",
                        "evidence": {"metric": f"+{round(((web_docs_count-len(hist_web_docs))/len(hist_web_docs))*100)}%", "comparison_period": "Recent period vs previous period", "evidence": f"Found {web_docs_count} recent pages compared to {len(hist_web_docs)} previously."},
                        "confidence": 0.5,
                        "severity": "info"
                    })
                    
                if 'hist_topic_res' not in locals():
                    hist_topic_res = extract_deterministic_topics([d["content"] for d in hist_docs_data if d.get("content")])
                if hist_topic_res.get("status") == "AVAILABLE" and current_topic_res.get("status") == "AVAILABLE":
                    hist_topics = {t["topic_keyphrase"] for t in hist_topic_res["topics"]}
                    curr_topics = {t["topic_keyphrase"] for t in current_topic_res["topics"]}
                    new_topics = curr_topics - hist_topics
                    if new_topics:
                        insights_to_add_dicts.append({
                            "company_id": comp['id'],
                            "analysis_id": analysis_id,
                            "insight_type": "Growth Signal",
                            "title": "Service/topic expansion",
                            "summary": "Topic activity increased with newly observed keyphrases.",
                            "evidence": {"metric": f"{len(new_topics)} new topics", "comparison_period": "Recent period vs previous period", "evidence": f"New topics emerged: {', '.join(list(new_topics)[:3])}."},
                            "confidence": 0.5,
                            "severity": "info"
                        })
                        
                hist_news_docs = [d for d in hist_docs_data if d["source_type"] == 'gdelt']
                if news_docs_count > len(hist_news_docs) and len(hist_news_docs) > 0:
                    pct_change = round(((news_docs_count - len(hist_news_docs)) / len(hist_news_docs)) * 100)
                    if pct_change > 10:
                        insights_to_add_dicts.append({
                            "company_id": comp['id'],
                            "analysis_id": analysis_id,
                            "insight_type": "Growth Signal",
                            "title": "News activity increase",
                            "summary": "More frequent news mentions were observed.",
                            "evidence": {"metric": f"+{pct_change}%", "comparison_period": "Recent period vs previous period", "evidence": f"{news_docs_count} recent mentions vs {len(hist_news_docs)} earlier."},
                            "confidence": 0.8,
                            "severity": "info"
                        })

        # 10. AI Intelligence (LONG RUNNING)
        logger.info("insight_generation_started")
        insight_gen = InsightGenerator()
        try:
            insight_res = await insight_gen.generate_insight(primary_company_id, primary_company_name, "market_overview")
            insights_to_add_dicts.append({
                "company_id": primary_company_id,
                "analysis_id": analysis_id,
                "insight_type": "AI Summary",
                "title": "AI Competitive Intelligence",
                "summary": insight_res.get("summary", "AI Intelligence: UNAVAILABLE"),
                "severity": insight_res.get("severity", "info"),
                "confidence": insight_res.get("confidence"),
                "evidence": insight_res.get("evidence")
            })
            logger.info("insight_generation_completed")
        except Exception as e:
            logger.error(f"LLM failure: {e}")
            insights_to_add_dicts.append({
                "company_id": primary_company_id,
                "analysis_id": analysis_id,
                "insight_type": "AI Summary",
                "title": "AI Competitive Intelligence",
                "summary": "AI Intelligence: UNAVAILABLE",
                "severity": "error",
                "confidence": None,
                "evidence": None
            })
            
        await website_extractor.close()
        await gdelt_extractor.close()

        # FINAL WRITE RESULTS (Fresh session)
        logger.info("results_persistence_started")
        start_time = time.time()
        logger.info("db_session_opened")
        async with async_session_factory() as session:
            # fetch analysis again
            res = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
            analysis = res.scalars().first()
            if analysis:
                for m_dict in metrics_to_add_dicts:
                    session.add(MarketMetric(**m_dict))
                for i_dict in insights_to_add_dicts:
                    session.add(Insight(**i_dict))
                
                # Check status and update
                if status_update != "PARTIAL" and analysis.status != "PARTIAL":
                    analysis.status = "COMPLETED"
                elif status_update == "PARTIAL":
                    analysis.status = "PARTIAL"
                    
                analysis.completed_at = datetime.now(timezone.utc)
                
                logger.info("analysis_flush_started")
                try:
                    await session.flush()
                except Exception as flush_exc:
                    logger.exception("analysis_flush_failed")
                    logger.error(
                        "flush_failed_details",
                        exc_class=type(flush_exc).__name__,
                        exc_repr=repr(flush_exc),
                        exc_str=str(flush_exc),
                        cause_class=type(flush_exc.__cause__).__name__ if flush_exc.__cause__ else None,
                        cause_repr=repr(flush_exc.__cause__),
                        context_class=type(flush_exc.__context__).__name__ if flush_exc.__context__ else None,
                        context_repr=repr(flush_exc.__context__)
                    )
                    
                    if hasattr(flush_exc, "orig") or "DBAPIError" in type(flush_exc).__name__:
                        orig = getattr(flush_exc, "orig", None)
                        logger.error(
                            "flush_failed_dbapi_details",
                            orig_type=type(orig).__name__ if orig else None,
                            orig_repr=repr(orig),
                            orig_str=str(orig),
                            sqlstate=getattr(orig, "sqlstate", None),
                            pgcode=getattr(orig, "pgcode", None),
                            detail=getattr(orig, "detail", None),
                            constraint_name=getattr(orig, "constraint_name", None),
                            table_name=getattr(orig, "table_name", None),
                            column_name=getattr(orig, "column_name", None),
                            statement=getattr(flush_exc, "statement", None)
                        )
                        
                    try:
                        await session.rollback()
                    except Exception:
                        logger.exception("rollback_after_flush_failure_failed")
                        
                    raise flush_exc

                logger.info("analysis_commit_started")
                try:
                    await session.commit()
                except Exception as commit_exc:
                    logger.exception("analysis_commit_failed")
                    try:
                        await session.rollback()
                    except Exception:
                        logger.exception("rollback_after_commit_failure_failed")
                    raise commit_exc
                    
                logger.info("analysis_commit_completed", elapsed_seconds=round(time.time() - start_time, 2))
                
            logger.info(f"AnalysisRun {analysis_id} completed successfully with status {analysis.status if analysis else 'UNKNOWN'}.")
        logger.info("db_session_closed")
        logger.info("results_persistence_completed")
        
    except Exception as e:
        logger.exception(f"AnalysisRun {analysis_id} failed fatally.")
        
        safe_error = str(e)[:2000].replace("\x00", "")
        
        # Robust error handler (Fresh session)
        logger.info("db_session_opened (error handler)")
        try:
            async with async_session_factory() as session:
                res = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
                logger.info("AnalysisRun SELECT succeeded")
                analysis = res.scalars().first()
                if analysis:
                    analysis.status = "FAILED"
                    logger.info("status assignment succeeded")
                    analysis.error_summary = safe_error
                    logger.info("error_summary assignment succeeded")
                    analysis.completed_at = datetime.now(timezone.utc)
                    try:
                        await session.commit()
                        logger.info("failure-state commit succeeded")
                    except Exception as failure_commit_exc:
                        logger.exception("analysis_failure_state_commit_failed")
                        try:
                            await session.rollback()
                        except Exception:
                            pass
        except Exception as secondary_e:
            logger.error(f"Secondary failure saving error state for AnalysisRun {analysis_id}: {secondary_e}")
        finally:
            logger.info("db_session_closed (error handler)")
