import asyncio
import json
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.db.session import async_session_factory
from app.services.pipeline.orchestrator import run_analysis_pipeline
from app.models.analysis import AnalysisRun, AnalysisCompetitor
from app.models.company import Company
from app.models.metric import MarketMetric
from app.models.insight import Insight
from app.models.document import Document

async def main():
    async with async_session_factory() as session:
        # Create companies
        c1 = Company(name="Curato", domain="curato.ai", is_primary=False)
        c2 = Company(name="Breef", domain="breef.com", is_primary=False)
        c3 = Company(name="DesignRush", domain="designrush.com", is_primary=False)
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
        # Run pipeline
        print("Running pipeline...")
        await run_analysis_pipeline(session, analysis_id)
        print("Pipeline finished.")
        
    # Verification
    async with async_session_factory() as session:
        # Status
        res = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
        ar = res.scalars().first()
        print("--- ANALYSIS RUN STATUS ---")
        print(f"Status: {ar.status}")
        if ar.error_summary:
            print(f"Error Summary: {ar.error_summary}")
        
        # Metrics
        res = await session.execute(select(MarketMetric).where(MarketMetric.company_id.in_([c1.id, c2.id, c3.id])))
        metrics = res.scalars().all()
        print("\n--- METRICS ---")
        for m in metrics:
            print(f"Company {m.company_id} | {m.metric_name}: {m.metric_value} | {m.components}")
            
        # Insights
        res = await session.execute(select(Insight).where(Insight.company_id.in_([c1.id, c2.id, c3.id])))
        insights = res.scalars().all()
        print("\n--- INSIGHTS ---")
        for i in insights:
            print(f"Company {i.company_id} | {i.insight_type}: {i.summary[:150]}...")
            
        # Evidence
        res = await session.execute(select(Document).where(Document.company_id.in_([c1.id, c2.id, c3.id])))
        docs = res.scalars().all()
        print("\n--- EVIDENCE ---")
        print(f"Total documents collected: {len(docs)}")
        for d in docs[:5]:
            print(f"Company {d.company_id} | {d.source_type} | {d.url}")

if __name__ == "__main__":
    asyncio.run(main())
