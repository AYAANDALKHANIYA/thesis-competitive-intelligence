import asyncio
import json
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.services.pipeline.orchestrator import run_analysis_pipeline
from app.models.analysis import AnalysisRun, AnalysisCompetitor
from app.models.company import Company
from app.models.metric import MarketMetric
from app.models.insight import Insight
from app.models.document import Document
from app.models.sentiment import SentimentResult
from app.models.topic import Topic, DocumentTopic

async def main():
    async with async_session_factory() as session:
        # Create companies
        c1 = Company(name="Semrush", domain="semrush.com", is_primary=False)
        c2 = Company(name="Ahrefs", domain="ahrefs.com", is_primary=False)
        c3 = Company(name="Moz", domain="moz.com", is_primary=False)
        session.add_all([c1, c2, c3])
        await session.flush()

        analysis = AnalysisRun(company_id=c1.id, status="QUEUED")
        session.add(analysis)
        await session.flush()

        ac1 = AnalysisCompetitor(analysis_run_id=analysis.id, competitor_id=c2.id)
        ac2 = AnalysisCompetitor(analysis_run_id=analysis.id, competitor_id=c3.id)
        session.add_all([ac1, ac2])
        await session.commit()
        
        analysis_id = analysis.id
        print(f"Created AnalysisRun {analysis_id}")
        
    async with async_session_factory() as session:
        print("Running pipeline...")
        await run_analysis_pipeline(session, analysis_id)
        print("Pipeline finished.")
        
    # Diagnostics
    async with async_session_factory() as session:
        companies = [c1, c2, c3]
        for c in companies:
            print(f"\n=========================================")
            print(f"DIAGNOSTIC REPORT: {c.name}")
            print(f"=========================================")
            
            # Docs & Pages
            res = await session.execute(select(Document).where(Document.company_id == c.id))
            docs = res.scalars().all()
            
            pages_crawled = len([d for d in docs if d.document_type == "webpage"])
            news_articles = len([d for d in docs if d.document_type == "news_article"])
            total_docs = len(docs)
            total_text = sum(len(d.content) for d in docs if d.content)
            
            print(f"pages crawled: {pages_crawled}")
            print(f"documents processed: {total_docs}")
            print(f"total text processed: {total_text}")
            print(f"news articles found: {news_articles}")
            
            # Sentiments
            doc_ids = [d.id for d in docs]
            if doc_ids:
                res = await session.execute(select(SentimentResult).where(SentimentResult.document_id.in_(doc_ids)))
                sentiments = res.scalars().all()
                pos = sum(1 for s in sentiments if s.label.lower() == 'positive')
                neu = sum(1 for s in sentiments if s.label.lower() == 'neutral')
                neg = sum(1 for s in sentiments if s.label.lower() == 'negative')
                
                score_map = {"positive": 100.0, "neutral": 50.0, "negative": 0.0}
                avg_sent = sum(score_map.get(s.label.lower(), 50) for s in sentiments) / len(sentiments) if sentiments else None
            else:
                pos = neu = neg = 0
                avg_sent = None
                
            print(f"positive sentiment count: {pos}")
            print(f"neutral sentiment count: {neu}")
            print(f"negative sentiment count: {neg}")
            print(f"average sentiment: {avg_sent}")
            
            # Topics
            if doc_ids:
                res = await session.execute(
                    select(Topic.name)
                    .join(DocumentTopic)
                    .where(DocumentTopic.document_id.in_(doc_ids))
                    .distinct()
                )
                topics = res.scalars().all()
            else:
                topics = []
                
            print(f"topics extracted: {len(topics)} -> {topics[:5]}...")
            
            # Metrics
            res = await session.execute(select(MarketMetric).where(MarketMetric.company_id == c.id))
            metrics = {m.metric_name: m for m in res.scalars().all()}
            
            ma_score = metrics.get("Market Activity Score")
            print(f"\nMarket Activity Score: {ma_score.metric_value if ma_score else 'Missing'}")
            print(f"Market Activity Score components: {ma_score.components if ma_score else 'Missing'}")
            
            print(f"content activity: {ma_score.components.get('Content Activity') if ma_score else 'Missing'}")
            print(f"review activity: {ma_score.components.get('Review/Mention Activity') if ma_score else 'Missing'}")
            print(f"topic momentum: {ma_score.components.get('Topic Momentum') if ma_score else 'Missing'}")
            
            seo_score = metrics.get("Technical SEO Score")
            print(f"technical SEO score: {seo_score.metric_value if seo_score else 'Missing'}")
            print(f"SEO component breakdown: {seo_score.components if seo_score else 'Missing'}")
            
            # Growth signals
            res = await session.execute(select(Insight).where(Insight.company_id == c.id, Insight.insight_type == "growth_signal"))
            signals = res.scalars().all()
            print(f"growth signals: {len(signals)}")
            if signals:
                for s in signals:
                    print(f"  - {s.summary[:60]}...")

if __name__ == "__main__":
    asyncio.run(main())
