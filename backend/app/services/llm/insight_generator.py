"""
LLM insight generator — uses OpenAI to produce evidence-grounded insights.

The LLM receives structured evidence and must NOT invent statistics or sources.
Insights are cached by evidence hash to prevent redundant API calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.insights import InsightRepository
from app.services.llm.evidence_builder import EvidenceBuilder

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert competitive intelligence analyst. Your role is to produce clear, evidence-based insights from structured analytical data.

CRITICAL RULES:
1. Use ONLY the evidence provided below. Do NOT invent statistics, sources, companies, or predictions.
2. Every claim must reference specific evidence items provided.
3. Clearly distinguish observed facts from projections or inferences.
4. If data is insufficient for a conclusion, state that explicitly.
5. Do NOT fabricate numerical values, dates, or source names.
6. The output must strictly follow the FACT, OBSERVATION, INFERENCE framework.
7. You must NOT calculate or modify Market Activity Score, Sentiment, Topic counts, SEO scores, Growth metrics, or Prediction metrics. Those values are provided to you. You only interpret them.

Respond with a JSON object containing EXACTLY this concise structure:
{
    "title": "Brief insight title",
    "severity": "low|medium|high|critical",
    "confidence": 0.0-1.0,
    "brief": {
        "executive_summary": "A concise 2-sentence summary of the market position.",
        "data_limitations": "1 sentence noting what data is missing."
    },
    "key_findings": [
        {
            "fact": "A verifiable fact from the evidence.",
            "observation": "What this fact means in context.",
            "inference": "The strategic implication.",
            "evidence_reference": "Source URL or metric."
        }
    ]
}
NOTE: Limit key_findings to a maximum of 3 items to remain concise.
"""


class InsightGenerator:
    """Generates evidence-grounded insights using an LLM."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.evidence_builder = EvidenceBuilder(db)
        self.insight_repo = InsightRepository(db)

    async def generate_insight(
        self,
        company_id: int,
        company_name: str,
        insight_type: str = "market_overview",
        force: bool = False,
    ) -> Dict[str, Any]:
        """Generate an insight for a company.

        Uses caching: if evidence hasn't changed and cache isn't expired, returns cached insight.
        """
        # Build evidence
        evidence = await self.evidence_builder.build_evidence(company_id, insight_type)
        evidence_hash = self.evidence_builder.compute_evidence_hash(evidence)

        # Check cache
        if not force:
            cached = await self.insight_repo.get_by_input_hash(company_id, evidence_hash)
            if cached:
                logger.info("insight_cache_hit_identical_evidence", company_id=company_id, type=insight_type)
                return {
                    "id": cached.id,
                    "cached": True,
                    "title": cached.title,
                    "summary": cached.summary,
                    "severity": cached.severity,
                    "evidence": cached.evidence,
                }

        # Call LLM
        prompt = self._build_prompt(company_name, insight_type, evidence)
        llm_response = await self._call_llm(prompt)

        if not llm_response:
            return {"error": "LLM call failed", "evidence": evidence}

        # Parse structured response
        parsed = self._parse_response(llm_response)

        # Store insight
        insight = await self.insight_repo.create(
            company_id=company_id,
            insight_type=insight_type,
            title=parsed.get("title", f"{insight_type.title()} Insight"),
            summary=json.dumps(parsed.get("brief", {"summary": parsed.get("summary", llm_response)})),
            severity=parsed.get("severity", "medium"),
            confidence=parsed.get("confidence"),
            model_name=self.settings.OPENAI_MODEL,
            model_version="1.0",
            evidence={
                "input_evidence": evidence,
                "key_findings": parsed.get("key_findings", []),
            },
            input_hash=evidence_hash,
        )

        logger.info(
            "insight_generated",
            company_id=company_id,
            type=insight_type,
            insight_id=insight.id,
        )

        await self.db.commit()

        return {
            "id": insight.id,
            "cached": False,
            "title": parsed.get("title", ""),
            "summary": insight.summary,
            "severity": parsed.get("severity", "medium"),
            "confidence": parsed.get("confidence"),
            "evidence": insight.evidence,
        }

    def _build_prompt(
        self, company_name: str, insight_type: str, evidence: Dict
    ) -> str:
        """Build the user prompt with structured evidence."""
        
        doc_count = evidence.get("sentiment", {}).get("total_analysed", 0)
        
        # Evidence-aware intelligence calibration
        if doc_count < 10:
            calibration = (
                "LOW DATA WARNING: The current dataset is very small (under 10 documents). "
                "You MUST NOT generate strong strategic recommendations or infer causality from content volume. "
                "Restrict your insight to direct observations only. Explicitly state that current intelligence is limited "
                "and more historical data is required before establishing reliable trends or trajectories."
            )
        elif doc_count < 30:
            calibration = (
                "MEDIUM DATA: The dataset is growing but still limited (under 30 documents). "
                "You may provide competitive comparisons and note early signals, but avoid definitive, strong strategic recommendations. "
                "Acknowledge that trends are preliminary."
            )
        else:
            calibration = (
                "SUFFICIENT DATA: The dataset has sufficient evidence for robust analysis. "
                "Provide strong, evidence-backed strategic insights, trends, and recommendations."
            )

        return f"""Generate a {insight_type} insight for company: {company_name}

CALIBRATION DIRECTIVE:
{calibration}

EVIDENCE DATA:
{json.dumps(evidence, indent=2, default=str)}

Analyse this evidence following the calibration directive and provide actionable competitive intelligence."""

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the Groq API via OpenAI client."""
        if not self.settings.GROQ_API_KEY:
            logger.warning("groq_api_key_not_set")
            return None

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.settings.GROQ_API_KEY,
                base_url=self.settings.GROQ_BASE_URL
            )
            response = await client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=900,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        except Exception as exc:
            logger.error("llm_call_error", error=str(exc))
            return None

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "title": "Market Intelligence Insight",
                "summary": response_text,
                "severity": "medium",
            }
