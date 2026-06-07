"""
LLM Gateway — unified interface for calling any configured model provider.

All LLM calls (judge, augmentation, scope analysis, firewall) route through
this gateway to centralise credential management, error handling, and logging.

Supported providers
-------------------
  openai            — OpenAI API (GPT-4o, GPT-4.1, etc.)
  azure_openai      — Azure OpenAI Service
  groq              — Groq (LLaMA-3, Mixtral, etc.)
  openai_compatible — Any server with an OpenAI-compatible /chat/completions
                      endpoint (LM Studio, vLLM, LocalAI, text-generation-webui)
  anthropic         — Anthropic API (Claude 3.x / 4.x family)
  gemini            — Google Gemini via the OpenAI-compatible REST endpoint
                      (https://generativelanguage.googleapis.com/v1beta/openai/)
  ollama            — Ollama local server via its OpenAI-compatible endpoint
                      (http://localhost:11434/v1 — no API key required)
  mistral           — Mistral AI (mistral-large-latest, etc.)
  together          — Together AI (Meta-Llama, Mixtral, etc.)
  deepseek          — DeepSeek (deepseek-chat, deepseek-reasoner, etc.)
  perplexity        — Perplexity AI (sonar-pro, sonar, etc.)
  fireworks         — Fireworks AI (LLaMA, Mixtral, etc.)
  xai               — xAI Grok (grok-3, etc.)
  cohere            — Cohere (command-r-plus, etc.) via OpenAI-compat endpoint
  huggingface       — HuggingFace Inference API (OpenAI-compat per-model endpoint)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.services.encryption import decrypt_value

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default model names per provider
# ---------------------------------------------------------------------------
_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "azure_openai": "gpt-4o",
    "groq": "llama-3.3-70b-versatile",
    "anthropic": "claude-sonnet-4-6",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.2",
    "openai_compatible": "gpt-4o",
    "custom": "gpt-4o",
    "mistral": "mistral-large-latest",
    "together": "meta-llama/Llama-3-70b-chat-hf",
    "deepseek": "deepseek-chat",
    "perplexity": "sonar-pro",
    "fireworks": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    "xai": "grok-3",
    "cohere": "command-r-plus-08-2024",
    "huggingface": "meta-llama/Meta-Llama-3-70B-Instruct",
}

# Base URLs for each provider
_PROVIDER_BASE_URLS: dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "ollama": "http://localhost:11434/v1",
    "mistral": "https://api.mistral.ai/v1",
    "together": "https://api.together.xyz/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "perplexity": "https://api.perplexity.ai",
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "xai": "https://api.x.ai/v1",
    "cohere": "https://api.cohere.ai/compatibility/v1",
    # huggingface base_url is constructed dynamically from the model name
}


class LLMGateway:
    """Thin wrapper that routes LLM calls to the appropriate provider."""

    def __init__(
        self,
        provider_type: str,
        encrypted_api_key: str | None = None,
        endpoint_url: str | None = None,
        model: str | None = None,
        *,
        api_key: str | None = None,
    ) -> None:
        self.provider_type = provider_type
        # Accept either an already-decrypted key or an encrypted one.
        # Ollama requires no key — use a placeholder to satisfy client libs.
        if api_key:
            self.api_key = api_key
        elif encrypted_api_key:
            self.api_key = decrypt_value(encrypted_api_key)
        elif provider_type == "ollama":
            self.api_key = "ollama"  # Ollama ignores the key; placeholder only
        else:
            raise ValueError(f"Either api_key or encrypted_api_key is required for provider {provider_type!r}")

        self.endpoint_url = endpoint_url
        self._model = model

    @property
    def model(self) -> str:
        """Return the configured model, falling back to a provider-appropriate default."""
        if self._model:
            return self._model
        return _PROVIDER_DEFAULT_MODELS.get(self.provider_type, settings.llm_judge_model)

    # ----- public API ---------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Send a chat-completion request and return the assistant content."""
        temp = temperature if temperature is not None else settings.llm_judge_temperature
        tokens = max_tokens or settings.llm_judge_max_tokens

        if self.provider_type == "anthropic":
            return await self._call_anthropic(messages, temp, tokens)
        elif self.provider_type in {
            "openai", "openai_compatible", "custom",
            "groq", "gemini", "ollama",
            "mistral", "together", "deepseek", "perplexity",
            "fireworks", "xai", "cohere", "huggingface",
        }:
            return await self._call_openai_compat(messages, temp, tokens, response_format)
        elif self.provider_type == "azure_openai":
            return await self._call_azure(messages, temp, tokens, response_format)
        else:
            raise ValueError(f"Unsupported provider type: {self.provider_type!r}")

    async def validate_credentials(self) -> tuple[bool, str | None]:
        """Lightweight probe to verify credentials are working.

        Returns (is_valid, error_message).
        """
        try:
            await self.chat(
                [{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            return True, None
        except Exception as exc:
            return False, str(exc)

    # ----- OpenAI-compatible (covers OpenAI, Groq, Gemini, Ollama, vLLM…) ---

    async def _call_openai_compat(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: dict | None,
    ) -> str:
        """Single implementation for all OpenAI-compatible endpoints."""
        base_url: str | None = None

        if self.provider_type in {"openai_compatible", "custom"}:
            if not self.endpoint_url:
                raise ValueError(
                    f"{self.provider_type!r} provider requires endpoint_url"
                )
            base_url = self.endpoint_url
        elif self.provider_type == "huggingface":
            # HuggingFace uses a per-model OpenAI-compat endpoint
            base_url = (
                self.endpoint_url
                or f"https://api-inference.huggingface.co/models/{self.model}/v1"
            )
        elif self.provider_type in _PROVIDER_BASE_URLS:
            # Use provider-supplied URL or the well-known default
            base_url = self.endpoint_url or _PROVIDER_BASE_URLS[self.provider_type]

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=httpx.Timeout(settings.llm_request_timeout, connect=10),
        )
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    # ----- Anthropic (native SDK — not OpenAI-compatible) --------------------

    async def _call_anthropic(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the Anthropic Messages API via the official `anthropic` SDK."""
        try:
            import anthropic  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for Anthropic provider support. "
                "Install it with: pip install anthropic"
            ) from exc

        # Anthropic separates the system prompt from the messages list.
        system_content: str = ""
        user_messages: list[dict[str, str]] = []
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            else:
                user_messages.append({"role": msg["role"], "content": msg.get("content", "")})

        client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            timeout=httpx.Timeout(settings.llm_request_timeout, connect=10),
        )

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": user_messages,
        }
        if system_content:
            kwargs["system"] = system_content

        response = await client.messages.create(**kwargs)
        # Extract plain text from content blocks
        text_blocks = [
            block.text
            for block in response.content
            if hasattr(block, "text")
        ]
        return "".join(text_blocks)

    # ----- Azure OpenAI -------------------------------------------------------

    async def _call_azure(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: dict | None,
    ) -> str:
        if not self.endpoint_url:
            raise ValueError("Azure OpenAI requires an endpoint_url")

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.endpoint_url,
            timeout=httpx.Timeout(settings.llm_request_timeout, connect=10),
        )
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
