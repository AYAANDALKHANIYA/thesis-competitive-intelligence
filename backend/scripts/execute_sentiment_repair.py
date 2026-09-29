import asyncio
from datetime import datetime, date
from sqlalchemy import select, func, update
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
from app.models.metric import MarketMetric
from app.services.intelligence.market_index import MarketActivityIndexService
from app.core.logging import get_logger

logger = get_logger(__name__)

async def run_repair():
    async with async_session_factory() as session:
        # Find all sentiment results
        query = select(SentimentResult, Document).join(Document, SentimentResult.document_id == Document.id)
        result = await session.execute(query)
        rows = result.all()

        affected_rows = 0
        affected_dates = set()

        for sent, doc in rows:
            is_affected = False
            new_score = sent.score
            
            if sent.label == "negative" and sent.score > 0:
                is_affected = True
                new_score = -sent.score
            elif sent.label == "neutral" and sent.score != 0:
                is_affected = True
                new_score = 0.0
                
            if is_affected:
                # Idempotent update
                sent.score = new_score
                session.add(sent)
                affected_rows += 1
                if doc.collected_at:
                    affected_dates.add((doc.company_id, doc.collected_at.date()))

        if affected_rows > 0:
            await session.commit()
            print(f"Repaired {affected_rows} sentiment records.")
        else:
            print("No sentiment records needed repair.")

        # Recalculate MAI for affected company-date pairs
        mai_service = MarketActivityIndexService(session)
        print(f"Recalculating MAI for {len(affected_dates)} company-date pairs...")
        for comp_id, dt in sorted(list(affected_dates)):
            print(f"Recalculating MAI for company {comp_id} on {dt}...")
            await mai_service.calculate(comp_id, target_date=dt)
            # Also calculate for today just in case, because metrics are normally up to date
            await mai_service.calculate(comp_id, target_date=date.today())

if __name__ == "__main__":
    asyncio.run(run_repair())
