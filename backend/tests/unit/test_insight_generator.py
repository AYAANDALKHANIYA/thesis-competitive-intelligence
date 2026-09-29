import pytest
from unittest.mock import patch, MagicMock

from app.services.llm.insight_generator import InsightGenerator
from app.core.config import get_settings

@pytest.mark.asyncio
async def test_groq_client_configuration():
    """Verify that the InsightGenerator configures the LLM client for Groq."""
    settings = get_settings()
    
    # We want to mock AsyncOpenAI and see what it's initialized with
    with patch("openai.AsyncOpenAI") as mock_openai:
        # Also mock the completions create call to return a valid JSON structure
        mock_client_instance = mock_openai.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"title": "Test", "summary": "Test", "severity": "info"}'
        mock_client_instance.chat.completions.create.return_value = mock_response

        # Mock dependencies for InsightGenerator
        generator = InsightGenerator(db=MagicMock())
        generator.settings = settings
        generator.insight_repo = MagicMock()
        generator.evidence_builder = MagicMock()
        
        from unittest.mock import AsyncMock
        # Override the evidence builder to avoid DB queries
        generator.evidence_builder.build_evidence = AsyncMock(return_value={})
        generator.evidence_builder.compute_evidence_hash.return_value = "hash"
        generator.insight_repo.get_by_input_hash = AsyncMock(return_value=None)
        generator.insight_repo.create = AsyncMock()

        # Execute
        await generator.generate_insight(1, "TestCompany", "market_overview")

        # Verify client initialization
        mock_openai.assert_called_once_with(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL
        )

        # Verify completion call uses correct model and JSON formatting
        mock_client_instance.chat.completions.create.assert_called_once()
        call_kwargs = mock_client_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == settings.GROQ_MODEL
        assert call_kwargs["response_format"] == {"type": "json_object"}
