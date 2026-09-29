"""
SEC EDGAR extractor — retrieves public filings for companies with CIK.

Uses the official SEC EDGAR API with proper User-Agent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.extraction.base import BaseExtractor, ExtractionResult, normalise_url

logger = get_logger(__name__)

SEC_COMPANY_API = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_FILING_BASE = "https://www.sec.gov/Archives/edgar/data"


class SECExtractor(BaseExtractor):
    """Extracts filing data from SEC EDGAR for public companies."""

    source_type = "sec"

    async def _get_client(self):
        """Override to use SEC-specific User-Agent."""
        import httpx

        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.REQUEST_TIMEOUT),
                headers={
                    "User-Agent": self.settings.SEC_USER_AGENT,
                    "Accept": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    async def extract(
        self,
        company_name: str,
        company_domain: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExtractionResult]:
        config = config or {}
        cik = config.get("cik", "")
        if not cik:
            logger.debug("sec_no_cik", company=company_name)
            return []

        # Pad CIK to 10 digits as SEC requires
        cik_padded = cik.zfill(10)
        source_key = "sec"
        rate_limit = config.get("rate_limit", 10)  # SEC is strict: 10 req/sec
        max_filings = config.get("max_filings", 20)

        url = SEC_COMPANY_API.format(cik=cik_padded)
        response = await self.fetch_url(url, source_key, rate_limit)
        if not response or response.status_code != 200:
            logger.warning("sec_fetch_failed", company=company_name, cik=cik)
            return []

        try:
            data = response.json()
        except Exception:
            logger.warning("sec_json_parse_error", company=company_name)
            return []

        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return []

        results: List[ExtractionResult] = []
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocDescription", [])
        docs = recent.get("primaryDocument", [])

        for i in range(min(len(forms), max_filings)):
            form_type = forms[i] if i < len(forms) else ""
            filing_date = dates[i] if i < len(dates) else ""
            accession = accessions[i] if i < len(accessions) else ""
            description = descriptions[i] if i < len(descriptions) else ""
            primary_doc = docs[i] if i < len(docs) else ""

            # Only process key filing types
            if form_type not in ("10-K", "10-Q", "8-K", "DEF 14A", "S-1", "20-F", "6-K"):
                continue

            accession_clean = accession.replace("-", "")
            filing_url = f"{SEC_FILING_BASE}/{cik}/{accession_clean}/{primary_doc}"

            published_at = None
            if filing_date:
                try:
                    published_at = datetime.strptime(filing_date, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    pass

            content = f"SEC Filing: {form_type}\n"
            content += f"Company: {data.get('name', company_name)}\n"
            content += f"CIK: {cik}\n"
            content += f"Filing Date: {filing_date}\n"
            content += f"Description: {description}\n"
            content += f"Accession: {accession}\n"

            results.append(
                ExtractionResult(
                    url=normalise_url(filing_url),
                    title=f"{form_type} - {data.get('name', company_name)} ({filing_date})",
                    content=content,
                    published_at=published_at,
                    document_type="sec_filing",
                    source_type="sec",
                    metadata={
                        "form_type": form_type,
                        "accession_number": accession,
                        "cik": cik,
                        "company_name_sec": data.get("name", ""),
                        "sic": data.get("sic", ""),
                        "sic_description": data.get("sicDescription", ""),
                    },
                )
            )

        logger.info(
            "sec_extraction_complete",
            company=company_name,
            filings=len(results),
        )
        return results
