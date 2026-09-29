"""
Ingestion task — wraps the orchestrator for background execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.companies import CompanyRepository
from app.services.ingestion.orchestrator import IngestionOrchestrator

logger = get_logger(__name__)


async def run_company_ingestion(
    db: AsyncSession,
    company_id: int,
    source_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run ingestion for a specific company."""
    company_repo = CompanyRepository(db)
    company = await company_repo.get_by_id(company_id)
    if not company:
        return {"error": f"Company {company_id} not found"}

    orchestrator = IngestionOrchestrator(db)
    stats = await orchestrator.run_ingestion(
        company_id=company.id,
        company_name=company.name,
        company_domain=company.domain,
        sec_cik=company.sec_cik,
        source_types=source_types,
    )

    return stats
