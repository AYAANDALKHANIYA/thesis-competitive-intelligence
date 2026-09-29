"""Manual ingestion runner script."""

import asyncio
import sys
sys.path.insert(0, ".")

from app.core.logging import setup_logging
from app.db.session import async_session_factory
from app.tasks.ingestion_tasks import run_company_ingestion
from app.tasks.analysis_tasks import process_unprocessed_documents


async def main(company_id: int):
    setup_logging()
    print(f"Running ingestion for company {company_id}...")

    async with async_session_factory() as session:
        stats = await run_company_ingestion(session, company_id)
        await session.commit()
        print(f"Ingestion stats: {stats}")

        print("Processing NLP pipeline...")
        nlp_stats = await process_unprocessed_documents(session, company_id)
        await session.commit()
        print(f"NLP stats: {nlp_stats}")


if __name__ == "__main__":
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(main(cid))
