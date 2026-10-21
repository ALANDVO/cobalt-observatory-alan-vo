"""
LLM Service tests.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm import (
    OpenAICompatibleAdapter,
    AnthropicAdapter,
    GeminiAdapter,
    LLMMessage,
    LLMResponse,
    get_llm_adapter,
    generate_evaluation_explanation,
)


class TestLLMAdapters:
    """Tests for LLM adapters."""

    @pytest.mark.asyncio
    async def test_openai_adapter_no_key(self):
        """OpenAI adapter returns error when no API key."""
        adapter = OpenAICompatibleAdapter("", "https://api.openai.com/v1", "gpt-4o")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await adapter.complete(messages)
        assert response.error is not None
        assert "not configured" in response.error

    @pytest.mark.asyncio
    async def test_anthropic_adapter_no_key(self):
        """Anthropic adapter returns error when no API key."""
        adapter = AnthropicAdapter("", "https://api.anthropic.com", "claude-3")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await adapter.complete(messages)
        assert response.error is not None
        assert "not configured" in response.error

    @pytest.mark.asyncio
    async def test_gemini_adapter_no_key(self):
        """Gemini adapter returns error when no API key."""
        adapter = GeminiAdapter("", "https://generativelanguage.googleapis.com", "gemini-pro")
        messages = [LLMMessage(role="user", content="Hello")]
        response = await adapter.complete(messages)
        assert response.error is not None
        assert "not configured" in response.error

    @pytest.mark.asyncio
    async def test_openai_adapter_success(self):
        """OpenAI adapter successful response."""
        adapter = OpenAICompatibleAdapter("test-key", "https://api.openai.com/v1", "gpt-4o")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.raise_for_status = lambda: None
            mock_post.return_value.json = lambda: {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}
            }

            messages = [LLMMessage(role="user", content="Hello")]
            response = await adapter.complete(messages)

            assert response.error is None
            assert response.content == "Test response"
            assert response.provider == "openai-compatible"
            assert response.model == "gpt-4o"
            assert response.usage is not None

    def test_get_llm_adapter_none_when_no_key(self):
        """get_llm_adapter returns None when no API key configured."""
        with patch("app.services.llm.settings") as mock_settings:
            mock_settings.llm_api_key = ""
            adapter = get_llm_adapter()
            assert adapter is None

    def test_get_llm_adapter_openai(self):
        """get_llm_adapter returns OpenAI adapter."""
        with patch("app.services.llm.settings") as mock_settings:
            mock_settings.llm_api_key = "test-key"
            mock_settings.llm_provider = "openai"
            mock_settings.llm_model = "gpt-4o"
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            adapter = get_llm_adapter()
            assert isinstance(adapter, OpenAICompatibleAdapter)

    def test_get_llm_adapter_anthropic(self):
        """get_llm_adapter returns Anthropic adapter."""
        with patch("app.services.llm.settings") as mock_settings:
            mock_settings.llm_api_key = "test-key"
            mock_settings.llm_provider = "anthropic"
            mock_settings.llm_model = "claude-3"
            mock_settings.llm_base_url = "https://api.anthropic.com"
            adapter = get_llm_adapter()
            assert isinstance(adapter, AnthropicAdapter)

    def test_get_llm_adapter_gemini(self):
        """get_llm_adapter returns Gemini adapter."""
        with patch("app.services.llm.settings") as mock_settings:
            mock_settings.llm_api_key = "test-key"
            mock_settings.llm_provider = "gemini"
            mock_settings.llm_model = "gemini-pro"
            mock_settings.llm_base_url = "https://generativelanguage.googleapis.com"
            adapter = get_llm_adapter()
            assert isinstance(adapter, GeminiAdapter)

    @pytest.mark.asyncio
    async def test_generate_explanation_no_adapter(self):
        """generate_evaluation_explanation returns None when no adapter."""
        with patch("app.services.llm.get_llm_adapter", return_value=None):
            result = await generate_evaluation_explanation(
                "test-agent", "test-dataset", 0.8, {}
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_explanation_with_adapter(self):
        """generate_evaluation_explanation returns formatted explanation."""
        mock_adapter = AsyncMock()
        mock_response = LLMResponse(
            content="Test explanation",
            provider="openai-compatible",
            model="gpt-4o",
            error=None,
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        mock_adapter.get_provider_name = MagicMock(return_value="openai-compatible")
        mock_adapter.model = "gpt-4o"

        with patch("app.services.llm.get_llm_adapter", return_value=mock_adapter):
            result = await generate_evaluation_explanation(
                "test-agent", "test-dataset", 0.8, {"accuracy": 0.9}
            )
            assert result is not None
            assert "[ADVISORY" in result
            assert "openai-compatible" in result
            assert "Test explanation" in result
