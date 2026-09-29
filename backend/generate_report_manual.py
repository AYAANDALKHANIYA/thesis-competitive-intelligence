import asyncio
from sqlalchemy import select, func, text
from app.db.session import async_session_factory
from app.models.company import Company
from app.models.document import Document
from app.models.sentiment import SentimentResult
from app.models.entity import Entity
from app.models.metric import MarketMetric
from app.models.ingestion_run import IngestionRun

async def main():
    async with async_session_factory() as session:
        # DATA COLLECTION
        print("=== DATA COLLECTION ===")
        runs = await session.execute(select(IngestionRun.company_id, IngestionRun.documents_found, IngestionRun.documents_new, IngestionRun.documents_skipped, IngestionRun.errors, IngestionRun.status))
        for r in runs.fetchall():
            print(f"Run: company_id={r[0]} status={r[5]} found={r[1]} new={r[2]} skipped={r[3]} errors={r[4]}")
            
        print("\n=== DOCUMENTS ===")
        docs = await session.execute(select(Document.company_id, Document.title, Document.url, Document.published_at))
        doc_list = docs.fetchall()
        for d in doc_list:
            print(f"Company: {d[0]} | Title: {d[1]} | URL: {d[2]} | Date: {d[3]}")
            
        print("\n=== NLP ===")
        sents = await session.execute(select(SentimentResult.label, func.count(SentimentResult.id), func.avg(SentimentResult.score)).group_by(SentimentResult.label))
        for s in sents.fetchall():
            print(f"Sentiment: {s[0]} | Count: {s[1]} | Avg Score: {s[2]:.4f}")
            
        ents = await session.execute(select(Entity.entity_type, Entity.entity_text, func.count(Entity.id)).group_by(Entity.entity_type, Entity.entity_text).order_by(func.count(Entity.id).desc()).limit(10))
        for e in ents.fetchall():
            print(f"Entity: {e[0]} - {e[1]} ({e[2]})")
            
        print("\n=== COMPETITIVE INTELLIGENCE ===")
        metrics = await session.execute(select(MarketMetric.company_id, MarketMetric.metric_name, MarketMetric.metric_value, MarketMetric.components).order_by(MarketMetric.metric_date.desc()).limit(10))
        for m in metrics.fetchall():
            print(f"Company: {m[0]} | Metric: {m[1]} | Value: {m[2]} | Components: {m[3]}")
            
if __name__ == "__main__":
    asyncio.run(main())
