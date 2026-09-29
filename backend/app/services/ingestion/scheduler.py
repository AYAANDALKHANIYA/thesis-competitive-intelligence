"""
APScheduler-based job scheduler for background ingestion and analytics.

WARNING: APScheduler is in-process. If Railway runs multiple replicas,
each replica will independently run these jobs. This architecture assumes
a SINGLE worker/replica for scheduled jobs.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def _run_all_ingestion():
    """Scheduled job: run ingestion for all companies."""
    from app.db.session import async_session_factory
    from app.repositories.companies import CompanyRepository
    from app.repositories.competitors import CompetitorRepository
    from app.tasks.ingestion_tasks import run_company_ingestion
    from app.tasks.analysis_tasks import process_unprocessed_documents

    async with async_session_factory() as session:
        try:
            repo = CompanyRepository(session)
            comp_repo = CompetitorRepository(session)
            
            from sqlalchemy import select
            from app.models.company import Company
            stmt = select(Company).where(Company.is_primary == True).limit(1)
            primary = (await session.execute(stmt)).scalar_one_or_none()
            
            if not primary:
                return
                
            # Primary company
            companies_to_run = [primary]
            
            # Competitors
            competitors = await comp_repo.get_by_company(primary.id)
            for comp in competitors:
                comp_company = await repo.get_by_id(comp.competitor_id)
                if comp_company:
                    companies_to_run.append(comp_company)
                    
            for company in companies_to_run:
                try:
                    await run_company_ingestion(session, company.id)
                    await session.commit()
                    await process_unprocessed_documents(session, company.id)
                    await session.commit()
                    
                    # Automated Intelligence Generation (caches permanently if no new evidence)
                    from app.services.llm.insight_generator import InsightGenerator
                    generator = InsightGenerator(session)
                    await generator.generate_insight(
                        company_id=company.id,
                        company_name=company.name,
                        insight_type="market_overview",
                        force=False
                    )
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.error("scheduled_company_ingestion_error", company_id=company.id, error=str(e))
                    
        except Exception as exc:
            await session.rollback()
            logger.error("scheduled_ingestion_error", error=str(exc))


def setup_scheduler() -> None:
    """Configure background jobs. Call during application startup."""
    settings = get_settings()

    # Ingestion job — runs at the shortest source interval (RSS)
    scheduler.add_job(
        _run_all_ingestion,
        trigger=IntervalTrigger(seconds=settings.RSS_INTERVAL),
        id="scheduled_ingestion",
        name="Scheduled Ingestion",
        replace_existing=True,
        max_instances=1,  # Overlap protection
        misfire_grace_time=300,
    )

    logger.info(
        "scheduler_configured",
        rss_interval=settings.RSS_INTERVAL,
        gdelt_interval=settings.GDELT_INTERVAL,
        website_interval=settings.WEBSITE_INTERVAL,
    )


def start_scheduler() -> None:
    """Start the scheduler if not already running."""
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler_started")


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_shutdown")
