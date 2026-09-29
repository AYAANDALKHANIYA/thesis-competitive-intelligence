"""
Ingestion orchestrator — central coordination for the entire ingestion pipeline.

Flow: Source discovery → Freshness check → Fetch → Clean → Normalise →
      Hash → Deduplicate → Persist → Queue for NLP
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.documents import DocumentRepository
from app.repositories.ingestion_runs import IngestionRunRepository
from app.repositories.source_state import SourceStateRepository
from app.repositories.sources import SourceRepository
from app.services.extraction.base import BaseExtractor, ExtractionResult, content_hash, normalise_url
from app.services.extraction.gdelt import GDELTExtractor
from app.services.extraction.rss import RSSExtractor
from app.services.extraction.sec import SECExtractor
from app.services.extraction.website import WebsiteExtractor
from app.services.ingestion.policies import FreshnessPolicy
from app.services.processing.cleaner import ContentCleaner
from app.services.processing.normalizer import ContentNormalizer

logger = get_logger(__name__)

EXTRACTOR_MAP: Dict[str, Type[BaseExtractor]] = {
    "website": WebsiteExtractor,
    "rss": RSSExtractor,
    "gdelt": GDELTExtractor,
    "sec": SECExtractor,
}


class IngestionOrchestrator:
    """Orchestrates the full ingestion pipeline for a company."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.source_repo = SourceRepository(db)
        self.state_repo = SourceStateRepository(db)
        self.run_repo = IngestionRunRepository(db)
        self.cleaner = ContentCleaner()
        self.normalizer = ContentNormalizer()
        self.policy = FreshnessPolicy()

    async def run_ingestion(
        self,
        company_id: int,
        company_name: str,
        company_domain: Optional[str] = None,
        sec_cik: Optional[str] = None,
        source_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run full ingestion pipeline for a company.

        Returns a dict of statistics about the run.
        """
        stats = {
            "documents_found": 0,
            "documents_new": 0,
            "documents_changed": 0,
            "documents_skipped": 0,
            "requests_made": 0,
            "errors": 0,
            "source_results": {},
        }

        # Get enabled sources
        sources = await self.source_repo.get_enabled()
        if source_types:
            sources = [s for s in sources if s.source_type in source_types]

        for source in sources:
            # Create ingestion run record
            run = await self.run_repo.create(
                company_id=company_id, source_id=source.id, status="RUNNING"
            )

            try:
                # Handle NOT_APPLICABLE for SEC
                if source.source_type == "sec" and not sec_cik:
                    await self.run_repo.complete(run, status="NOT_APPLICABLE")
                    stats["source_results"][source.source_type] = {
                        "found": 0, "new": 0, "changed": 0, "skipped": 0, "requests": 0, "errors": 0
                    }
                    continue

                source_stats = await self._process_source(
                    company_id=company_id,
                    company_name=company_name,
                    company_domain=company_domain,
                    sec_cik=sec_cik,
                    source=source,
                )

                if source_stats["errors"] > 0 and source_stats["found"] == 0:
                    final_status = "FAILED"
                elif source_stats["found"] == 0 and source_stats["requests"] == 0:
                    final_status = "SKIPPED"
                else:
                    final_status = "SUCCESS"

                await self.run_repo.complete(
                    run,
                    status=final_status,
                    documents_found=source_stats["found"],
                    documents_new=source_stats["new"],
                    documents_changed=source_stats["changed"],
                    documents_skipped=source_stats["skipped"],
                    requests_made=source_stats["requests"],
                    errors=source_stats["errors"],
                )

                stats["documents_found"] += source_stats["found"]
                stats["documents_new"] += source_stats["new"]
                stats["documents_changed"] += source_stats["changed"]
                stats["documents_skipped"] += source_stats["skipped"]
                stats["source_results"][source.source_type] = source_stats

            except Exception as exc:
                logger.error(
                    "ingestion_source_error",
                    source=source.name,
                    source_type=source.source_type,
                    error=str(exc),
                )
                await self.run_repo.complete(run, status="FAILED", errors=1)
                stats["errors"] += 1

        logger.info(
            "ingestion_complete",
            company=company_name,
            new=stats["documents_new"],
            changed=stats["documents_changed"],
            skipped=stats["documents_skipped"],
        )

        return stats

    async def _process_source(
        self,
        company_id: int,
        company_name: str,
        company_domain: Optional[str],
        sec_cik: Optional[str],
        source,
    ) -> Dict[str, int]:
        """Process a single source adapter."""
        source_stats = {
            "found": 0, "new": 0, "changed": 0, "skipped": 0, "requests": 0, "errors": 0,
        }

        extractor_cls = EXTRACTOR_MAP.get(source.source_type)
        if not extractor_cls:
            logger.warning("unknown_source_type", source_type=source.source_type)
            return source_stats

        extractor = extractor_cls()
        try:
            # Build config from source settings
            config = source.config or {}
            if source.source_type == "sec" and sec_cik:
                config["cik"] = sec_cik
            config.setdefault("rate_limit", source.rate_limit_per_minute)
            config.setdefault("crawl_delay", source.crawl_delay_seconds)

            results = await extractor.extract(
                company_name=company_name,
                company_domain=company_domain,
                config=config,
            )
            source_stats["found"] = len(results)
            source_stats["requests"] = len(results)  # Approximate

            for result in results:
                try:
                    outcome = await self._process_document(
                        company_id=company_id,
                        source_id=source.id,
                        source_type=source.source_type,
                        result=result,
                    )
                    source_stats[outcome] += 1
                except Exception as exc:
                    logger.error(
                        "document_processing_error",
                        url=result.url,
                        error=str(exc),
                    )
                    source_stats["errors"] += 1

        finally:
            await extractor.close()

        return source_stats

    async def _process_document(
        self,
        company_id: int,
        source_id: int,
        source_type: str,
        result: ExtractionResult,
    ) -> str:
        """Process a single extraction result. Returns 'new', 'changed', or 'skipped'."""
        url = normalise_url(result.url)

        # Clean and normalise content
        cleaned = self.cleaner.clean(result.content or "", is_html="<" in (result.content or ""))
        if not cleaned:
            return "skipped"

        if not self.normalizer.is_valid_content(cleaned):
            return "skipped"

        # Hash the cleaned content
        doc_hash = content_hash(cleaned)

        # Check source state for this URL
        state = await self.state_repo.get(source_id, company_id, url)
        now = datetime.now(timezone.utc)

        if state and state.content_hash == doc_hash:
            # Content unchanged — update check time, skip
            await self.state_repo.upsert(
                source_id=source_id,
                company_id=company_id,
                url=url,
                last_checked_at=now,
                fetch_status="not_modified",
                next_check_at=self.policy.next_check_time(source_type),
            )
            return "skipped"

        # Detect language and word count
        language = self.normalizer.detect_language(cleaned)
        word_count = self.normalizer.count_words(cleaned)

        # Check for existing document by URL
        existing_doc = await self.doc_repo.get_by_url_and_company(url, company_id)

        if existing_doc:
            # Document exists but content changed
            await self.doc_repo.update_content(
                existing_doc, cleaned, doc_hash, title=result.title
            )
            outcome = "changed"
        else:
            # New document
            await self.doc_repo.create(
                company_id=company_id,
                source_id=source_id,
                url=url,
                title=result.title,
                content=cleaned,
                content_hash=doc_hash,
                author=result.author,
                published_at=result.published_at,
                language=language,
                document_type=result.document_type,
                word_count=word_count,
                metadata_=result.metadata,
            )
            outcome = "new"

        # Update source state
        etag = result.metadata.get("etag") if result.metadata else None
        last_mod = result.metadata.get("last_modified") if result.metadata else None

        await self.state_repo.upsert(
            source_id=source_id,
            company_id=company_id,
            url=url,
            etag=etag,
            last_modified=last_mod,
            content_hash=doc_hash,
            last_checked_at=now,
            last_changed_at=now,
            fetch_status="success",
            http_status=200,
            error_count=0,
            next_check_at=self.policy.next_check_time(source_type),
        )

        return outcome
