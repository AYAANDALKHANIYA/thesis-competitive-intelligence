import asyncio
import sys
from sqlalchemy import select

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.db.session import async_session_factory
from backend.app.models.company import Company
from backend.app.services.ingestion.orchestrator import IngestionOrchestrator

async def run_collection():
    print("Starting collection test...")
    async with async_session_factory() as session:
        # Get Curato ID 9
        stmt = select(Company).where(Company.id == 9)
        result = await session.execute(stmt)
        curato = result.scalar_one_or_none()
        
        if not curato:
            print("Curato not found!")
            return
            
        print(f"Running collection for {curato.name} (ID: {curato.id})")
        
        orchestrator = IngestionOrchestrator(session)
        result = await orchestrator.run_collection_for_company(curato.id)
        
        print("\nCollection Results:")
        for res in result:
            print(f"- Company ID {res['company_id']}:")
            print(f"  Duration: {res.get('duration_seconds', 0):.2f}s")
            print(f"  Sources Attempted: {res.get('sources_attempted')}")
            print(f"  Sources Success: {res.get('sources_successful')}")
            print(f"  Docs Collected: {res.get('documents_collected')}")
            print(f"  Docs Skipped: {res.get('documents_skipped')}")
            print(f"  Processing Results: {res.get('processing_results')}")
            print(f"  Errors: {res.get('errors')}")

if __name__ == "__main__":
    asyncio.run(run_collection())
