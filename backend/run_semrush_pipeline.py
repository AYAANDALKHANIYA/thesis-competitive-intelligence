import asyncio
import os
from sqlalchemy.orm import selectinload
from sqlalchemy import select, text
from app.db.session import async_session_factory
from app.services.pipeline.orchestrator import run_analysis_pipeline
from app.models.analysis import AnalysisRun, AnalysisCompetitor
from app.models.company import Company
from app.models.metric import MarketMetric

async def main():
    async with async_session_factory() as session:
        # Get companies
        for name in ["Semrush", "Ahrefs", "Moz"]:
            res = await session.execute(select(Company).where(Company.name == name))
            c = res.scalars().first()
            if not c:
                c = Company(name=name, domain=f"{name.lower()}.com", is_primary=(name=="Semrush"))
                session.add(c)
        await session.commit()
        
        # Get companies again
        res = await session.execute(select(Company).where(Company.name.in_(["Semrush", "Ahrefs", "Moz"])))
        comps = res.scalars().all()
        cmap = {c.name: c for c in comps}
        
        if "Semrush" not in cmap:
            return
            
        analysis = AnalysisRun(company_id=cmap["Semrush"].id, status="QUEUED")
        session.add(analysis)
        await session.flush()
        
        if "Ahrefs" in cmap:
            ac1 = AnalysisCompetitor(analysis_run_id=analysis.id, competitor_id=cmap["Ahrefs"].id)
            session.add(ac1)
        if "Moz" in cmap:
            ac2 = AnalysisCompetitor(analysis_run_id=analysis.id, competitor_id=cmap["Moz"].id)
            session.add(ac2)
            
        await session.commit()
        
        analysis_id = analysis.id
        print(f"Created AnalysisRun {analysis_id}")
        
    async with async_session_factory() as session:
        # Delete old metrics for these companies to avoid query_results.py getting confused with duplicates
        for c in comps:
            await session.execute(text("DELETE FROM market_metrics WHERE company_id = :cid"), {"cid": c.id})
            # Also topics and document_topics because we fixed topic extraction
            await session.execute(text("DELETE FROM document_topics WHERE document_id IN (SELECT id FROM documents WHERE company_id = :cid)"), {"cid": c.id})
        await session.commit()
        
        print("Running pipeline...")
        await run_analysis_pipeline(session, analysis_id)
        print("Pipeline finished.")

if __name__ == "__main__":
    asyncio.run(main())
