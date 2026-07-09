"""Clean multi-LLM router with provider abstraction.

March 2026 style: simple, typed, extensible.
"""

import httpx
import time
from typing import Literal

from ..core.models import LLMResponse
from ..core.config import settings


Provider = Literal["openai", "anthropic", "grok", "ollama"]


class LLMError(Exception):
    """Raised when an LLM call fails."""
    pass


class LLMRouter:
    """Routes requests to different LLM providers with a unified interface."""

    def __init__(self, default_provider: Provider | None = None):
        self.default_provider = default_provider or settings.default_llm_provider
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        prompt: str,
        provider: Provider | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text using the selected provider."""
        provider = provider or self.default_provider

        start = time.perf_counter()

        if provider == "grok":
            response = await self._call_grok(prompt, model, max_tokens, temperature)
        elif provider == "openai":
            response = await self._call_openai(prompt, model, max_tokens, temperature)
        elif provider == "anthropic":
            response = await self._call_anthropic(prompt, model, max_tokens, temperature)
        elif provider == "ollama":
            response = await self._call_ollama(prompt, model, max_tokens, temperature)
        else:
            raise LLMError(f"Unknown provider: {provider}")

        latency = (time.perf_counter() - start) * 1000
        response.latency_ms = latency
        return response

    async def _call_grok(self, prompt: str, model: str | None, max_tokens: int, temperature: float) -> LLMResponse:
        model = model or "grok-3"
        if not settings.grok_api_key:
            raise LLMError("GROK_API_KEY not configured")

        resp = await self.client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.grok_api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            provider="grok",
            model=model,
            content=data["choices"][0]["message"]["content"],
            tokens_used=data.get("usage", {}).get("total_tokens"),
        )

    async def _call_openai(self, prompt: str, model: str | None, max_tokens: int, temperature: float) -> LLMResponse:
        model = model or "gpt-4o-mini"
        if not settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY not configured")

        resp = await self.client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            provider="openai",
            model=model,
            content=data["choices"][0]["message"]["content"],
            tokens_used=data.get("usage", {}).get("total_tokens"),
        )

    async def _call_anthropic(self, prompt: str, model: str | None, max_tokens: int, temperature: float) -> LLMResponse:
        model = model or "claude-3-5-sonnet-20240620"
        if not settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY not configured")

        resp = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            provider="anthropic",
            model=model,
            content=data["content"][0]["text"],
            tokens_used=data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
        )

    async def _call_ollama(self, prompt: str, model: str | None, max_tokens: int, temperature: float) -> LLMResponse:
        model = model or "llama3.1"
        resp = await self.client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(
            provider="ollama",
            model=model,
            content=data.get("response", ""),
        )

    async def close(self):
        await self.client.aclose()