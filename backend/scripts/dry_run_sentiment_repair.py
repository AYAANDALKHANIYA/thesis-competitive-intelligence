import asyncio
from sqlalchemy import select, func
from app.db.session import async_session_factory

# Import all models to configure registry
import app.models.company
import app.models.competitor
import app.models.document
import app.models.embedding
import app.models.entity
import app.models.ingestion_run
import app.models.insight
import app.models.metric
import app.models.model_version
import app.models.prediction
import app.models.sentiment
import app.models.source
import app.models.source_state
import app.models.topic

from app.models.sentiment import SentimentResult
from app.models.document import Document
from app.core.logging import get_logger

logger = get_logger(__name__)

async def run_dry_run():
    async with async_session_factory() as session:
        # Find all sentiment results
        query = select(SentimentResult, Document).join(Document, SentimentResult.document_id == Document.id)
        result = await session.execute(query)
        rows = result.all()

        total_rows = len(rows)
        affected_rows = 0
        positive_rows = 0
        neutral_rows = 0
        negative_rows = 0
        
        affected_companies = set()
        affected_dates = set()

        for sent, doc in rows:
            is_affected = False
            if sent.label == "negative" and sent.score > 0:
                is_affected = True
                negative_rows += 1
            elif sent.label == "neutral" and sent.score != 0:
                is_affected = True
                neutral_rows += 1
            elif sent.label == "positive":
                positive_rows += 1
                
            if is_affected:
                affected_rows += 1
                affected_companies.add(doc.company_id)
                if doc.collected_at:
                    affected_dates.add((doc.company_id, doc.collected_at.date()))

        print("=== DRY RUN: SENTIMENT REPAIR ===")
        print(f"Total sentiment rows: {total_rows}")
        print(f"Total affected rows: {affected_rows}")
        print(f"  - Positive rows (unaffected): {positive_rows}")
        print(f"  - Neutral rows affected: {neutral_rows}")
        print(f"  - Negative rows affected: {negative_rows}")
        print(f"Total affected companies: {len(affected_companies)}")
        print(f"Total affected MAI observations (company + date pairs): {len(affected_dates)}")
        
        if affected_dates:
            print("\nAffected MAI Observation Pairs:")
            for comp, dt in sorted(list(affected_dates)):
                print(f"  Company {comp}, Date {dt}")

if __name__ == "__main__":
    asyncio.run(run_dry_run())
