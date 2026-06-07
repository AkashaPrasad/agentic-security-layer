"""
Chat Playground API — send messages to any configured provider.

Provides a simple chat-completion endpoint so users can interactively
test their LLM provider keys (Groq, OpenAI, Azure) from the UI.
"""

from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.deps import get_current_user
from app.services.llm_gateway import LLMGateway
from app.storage.database import get_async_session
from app.storage.models import ModelProvider, User

router = APIRouter(prefix="/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(system|user|assistant)$")
    content: str = Field(..., min_length=1, max_length=32_000)


class ChatRequest(BaseModel):
    provider_id: UUID
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=32_000)


class ChatResponse(BaseModel):
    content: str
    model: str
    provider_type: str
    latency_ms: int


class ProviderOption(BaseModel):
    id: UUID
    name: str
    provider_type: str
    model: str | None = None
    is_valid: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/providers", response_model=list[ProviderOption])
async def list_chat_providers(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[ProviderOption]:
    """List available (valid) providers for chat use."""
    result = await session.execute(
        select(ModelProvider).where(
            ModelProvider.owner_id == current_user.id,
        ).order_by(ModelProvider.name)
    )
    providers = result.scalars().all()
    return [
        ProviderOption(
            id=p.id,
            name=p.name,
            provider_type=p.provider_type,
            model=p.model,
            is_valid=p.is_valid,
        )
        for p in providers
    ]


@router.post("", response_model=ChatResponse)
async def send_chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ChatResponse:
    """Send a chat-completion request via a configured provider."""
    # Fetch provider
    result = await session.execute(
        select(ModelProvider).where(
            ModelProvider.id == body.provider_id,
            ModelProvider.owner_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    if not provider.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider credentials are not validated. Validate the provider first.",
        )

    gateway = LLMGateway(
        provider_type=provider.provider_type,
        encrypted_api_key=provider.encrypted_api_key,
        endpoint_url=provider.endpoint_url,
        model=provider.model,
    )

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    start = time.monotonic()
    try:
        content = await gateway.chat(
            messages,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM call failed: {exc}",
        )
    latency_ms = int((time.monotonic() - start) * 1000)

    return ChatResponse(
        content=content,
        model=gateway.model,
        provider_type=provider.provider_type,
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# Provider Proxy — experiment-compatible endpoint
# ---------------------------------------------------------------------------
# This endpoint accepts the same payload format that experiments use
# ({"messages": [{"role": "user", "content": "..."}]}) so experiments
# can target the platform's own providers directly.

class ProxyMessage(BaseModel):
    role: str
    content: str


class ProxyRequest(BaseModel):
    messages: list[ProxyMessage] = Field(..., min_length=1)
    temperature: float | None = None
    max_tokens: int | None = None


class ProxyResponse(BaseModel):
    choices: list[dict]
    model: str


@router.post("/proxy/{provider_id}", response_model=ProxyResponse)
async def proxy_provider(
    provider_id: UUID,
    body: ProxyRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProxyResponse:
    """OpenAI-compatible proxy endpoint for experiments using direct provider mode.

    Accepts the standard ``{"messages": [...]}`` format and returns an
    OpenAI-compatible ``{"choices": [{"message": {"role": "assistant", "content": "..."}}]}``
    structure so the experiment runner can parse responses uniformly.
    """
    result = await session.execute(
        select(ModelProvider).where(
            ModelProvider.id == provider_id,
            ModelProvider.owner_id == current_user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    if not provider.is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider not validated")

    gateway = LLMGateway(
        provider_type=provider.provider_type,
        encrypted_api_key=provider.encrypted_api_key,
        endpoint_url=provider.endpoint_url,
        model=provider.model,
    )

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    kwargs = {}
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    try:
        content = await gateway.chat(messages, **kwargs)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return ProxyResponse(
        choices=[{"message": {"role": "assistant", "content": content}}],
        model=gateway.model,
    )
