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
        generator = InsightGenerator()
        generator.settings = settings
        
        # Execute only _call_llm to verify configuration
        await generator._call_llm("test prompt")

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
