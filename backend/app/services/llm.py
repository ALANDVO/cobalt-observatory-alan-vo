"""
LLM adapter service for opt-in explanations.
Supports OpenAI-compatible, Anthropic, and Gemini providers.
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx

from app.core.config import settings


@dataclass
class LLMMessage:
    """LLM message structure."""
    role: str
    content: str


@dataclass
class LLMResponse:
    """LLM response structure."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters."""

    @abstractmethod
    async def complete(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Complete a chat conversation."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider identifier."""
        pass


class OpenAICompatibleAdapter(LLMAdapter):
    """OpenAI-compatible adapter (OpenAI, LiteLLM, OpenRouter, Ollama)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def complete(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error="LLM_API_KEY not configured",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 500),
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            return LLMResponse(
                content=content,
                provider=self.get_provider_name(),
                model=self.model,
                usage=usage,
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error=str(e),
            )

    def get_provider_name(self) -> str:
        return "openai-compatible"


class AnthropicAdapter(LLMAdapter):
    """Anthropic Messages API adapter."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def complete(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error="LLM_API_KEY not configured",
            )

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        # Convert to Anthropic format
        system_messages = [m.content for m in messages if m.role == "system"]
        user_messages = [m for m in messages if m.role != "system"]

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in user_messages],
            "max_tokens": kwargs.get("max_tokens", 500),
            "temperature": kwargs.get("temperature", 0.3),
        }
        if system_messages:
            payload["system"] = "\n".join(system_messages)

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            content = data["content"][0]["text"]
            usage = data.get("usage")

            return LLMResponse(
                content=content,
                provider=self.get_provider_name(),
                model=self.model,
                usage=usage,
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error=str(e),
            )

    def get_provider_name(self) -> str:
        return "anthropic"


class GeminiAdapter(LLMAdapter):
    """Google Gemini generateContent adapter."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def complete(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error="LLM_API_KEY not configured",
            )

        # Convert messages to Gemini format
        contents = []
        for m in messages:
            role = "user" if m.role in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.3),
                "maxOutputTokens": kwargs.get("max_tokens", 500),
            },
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            content = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata")

            return LLMResponse(
                content=content,
                provider=self.get_provider_name(),
                model=self.model,
                usage=usage,
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=self.get_provider_name(),
                model=self.model,
                error=str(e),
            )

    def get_provider_name(self) -> str:
        return "gemini"


def get_llm_adapter() -> Optional[LLMAdapter]:
    """Factory function to get configured LLM adapter."""
    if not settings.llm_api_key:
        return None

    provider = settings.llm_provider.lower()
    base_url = settings.llm_base_url
    model = settings.llm_model

    if provider in ("openai", "openai-compatible", "litellm", "openrouter", "ollama"):
        if not base_url:
            base_url = "https://api.openai.com/v1"
        return OpenAICompatibleAdapter(settings.llm_api_key, base_url, model)
    elif provider in ("anthropic", "claude"):
        if not base_url:
            base_url = "https://api.anthropic.com"
        return AnthropicAdapter(settings.llm_api_key, base_url, model)
    elif provider in ("gemini", "google"):
        if not base_url:
            base_url = "https://generativelanguage.googleapis.com"
        return GeminiAdapter(settings.llm_api_key, base_url, model)
    else:
        return None


async def generate_evaluation_explanation(
    agent_name: str,
    dataset: str,
    score: float,
    metrics: Dict[str, Any],
    details: Optional[str] = None
) -> Optional[str]:
    """Generate an LLM explanation for evaluation results (opt-in)."""
    adapter = get_llm_adapter()
    if not adapter:
        return None

    prompt = f"""You are an AI evaluation analyst. Provide a concise, factual explanation of this agent evaluation result.

Agent: {agent_name}
Dataset: {dataset}
Score: {score:.3f}
Metrics: {json.dumps(metrics, indent=2)}
Details: {details or 'N/A'}

Explain what the score means, notable metric patterns, and any caveats. Keep it under 200 words. Label as advisory only."""

    messages = [
        LLMMessage(role="system", content="You are an evaluation analyst. Provide factual, concise explanations."),
        LLMMessage(role="user", content=prompt),
    ]

    response = await adapter.complete(messages, temperature=0.2, max_tokens=300)

    if response.error:
        return f"[LLM Error: {response.error}]"

    return f"[ADVISORY - {adapter.get_provider_name()}/{adapter.model}] {response.content}"