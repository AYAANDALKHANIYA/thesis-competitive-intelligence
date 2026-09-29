import asyncio
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.db.session import async_session_factory
from backend.app.repositories.analysis import AnalysisRepository
from backend.app.repositories.companies import CompanyRepository
from backend.app.repositories.insights import InsightRepository
from backend.app.services.intelligence.emerging_signals import EmergingSignalService
from backend.app.services.intelligence.market_index import MarketActivityIndexService

async def debug_dashboard(company_id=9):
    print(f"Starting debug for company {company_id}...")
    async with async_session_factory() as db:
        print("1. CompanyRepository.get_by_id...")
        t0 = time.time()
        company_repo = CompanyRepository(db)
        company = await company_repo.get_by_id(company_id)
        print(f"   Done in {time.time()-t0:.2f}s")
        
        print("2. MarketActivityIndexService.calculate...")
        t0 = time.time()
        index_svc = MarketActivityIndexService(db)
        mai_data = await index_svc.calculate(company_id)
        print(f"   Done in {time.time()-t0:.2f}s")
        
        print("3. AnalysisRepository.get_sentiments_by_company...")
        t0 = time.time()
        analysis_repo = AnalysisRepository(db)
        results = await analysis_repo.get_sentiments_by_company(company_id, limit=200)
        print(f"   Done in {time.time()-t0:.2f}s, found {len(results)}")
        
        print("4. EmergingSignalService.detect_signals...")
        t0 = time.time()
        signal_svc = EmergingSignalService(db)
        signals = await signal_svc.detect_signals(company_id)
        print(f"   Done in {time.time()-t0:.2f}s, found {len(signals)}")
        
        print("5. AnalysisRepository.get_topics_by_company...")
        t0 = time.time()
        topics = await analysis_repo.get_topics_by_company(company_id, limit=5)
        print(f"   Done in {time.time()-t0:.2f}s, found {len(topics)}")
        
        print("6. InsightRepository.get_all...")
        t0 = time.time()
        insight_repo = InsightRepository(db)
        docs, _ = await insight_repo.get_all(limit=5, company_id=company_id)
        print(f"   Done in {time.time()-t0:.2f}s, found {len(docs)}")
        
        print("Finished!")

if __name__ == "__main__":
    asyncio.run(debug_dashboard())
