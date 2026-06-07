"""
Providers API routes — CRUD + validation for model provider configurations.

Providers are scoped per user — each user manages their own providers.
"""

from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.deps import get_current_user
from app.api.schemas.providers import (
    ProviderCreate,
    ProviderList,
    ProviderResponse,
    ProviderUpdate,
    ProviderValidationResult,
)
from app.api.schemas.shared import UserBrief
from app.services.audit import write_audit_log
from app.services.encryption import decrypt_value, encrypt_value, mask_secret
from app.services.llm_gateway import LLMGateway
from app.storage.database import get_async_session
from app.storage.models import Experiment, ModelProvider, User

router = APIRouter(prefix="/providers", tags=["providers"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _to_response(
    provider: ModelProvider,
    session: AsyncSession,
) -> ProviderResponse:
    """Convert ORM model to response schema."""
    try:
        plain_key = decrypt_value(provider.encrypted_api_key)
        preview = mask_secret(plain_key)
    except Exception:
        preview = "***"

    # Decrypt judge key for response
    judge_api_key_plain: str | None = None
    if provider.judge_api_key_enc:
        try:
            judge_api_key_plain = mask_secret(decrypt_value(provider.judge_api_key_enc))
        except Exception:
            judge_api_key_plain = "***"

    # Decrypt backup key for response
    backup_api_key_plain: str | None = None
    if provider.backup_api_key_enc:
        try:
            backup_api_key_plain = mask_secret(decrypt_value(provider.backup_api_key_enc))
        except Exception:
            backup_api_key_plain = "***"

    # Check if any experiments reference this provider
    exp_count = await session.execute(
        select(func.count()).where(Experiment.provider_id == provider.id)
    )
    has_experiments = exp_count.scalar_one() > 0

    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        endpoint_url=provider.endpoint_url,
        model=provider.model,
        api_key_preview=preview,
        is_valid=provider.is_valid,
        has_experiments=has_experiments,
        created_by=None,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
        requests_per_minute=provider.requests_per_minute,
        tokens_per_minute=provider.tokens_per_minute,
        max_calls_per_experiment=provider.max_calls_per_experiment,
        judge_api_key=judge_api_key_plain,
        judge_endpoint=provider.judge_endpoint,
        judge_model=provider.judge_model,
        use_separate_judge=provider.use_separate_judge,
        default_target_endpoint=provider.default_target_endpoint,
        default_system_prompt=provider.default_system_prompt,
        backup_api_key=backup_api_key_plain,
        backup_endpoint=provider.backup_endpoint,
        backup_model=provider.backup_model,
        use_backup_key=provider.use_backup_key,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=ProviderList)
async def list_providers(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProviderList:
    """List all providers owned by the current user."""
    result = await session.execute(
        select(ModelProvider)
        .where(ModelProvider.owner_id == current_user.id)
        .order_by(ModelProvider.created_at.desc())
    )
    providers = result.scalars().all()
    return ProviderList(
        items=[await _to_response(p, session) for p in providers],
        total=len(providers),
    )


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProviderResponse:
    """Get a single provider by ID."""
    provider = await _get_provider_or_404(provider_id, current_user, session)
    return await _to_response(provider, session)


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    body: ProviderCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProviderResponse:
    """Create a new model provider."""
    if body.provider_type == "azure_openai" and not body.endpoint_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endpoint_url is required for Azure OpenAI providers",
        )
    if body.provider_type in {"openai_compatible", "custom"} and not body.endpoint_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endpoint_url is required for openai_compatible/custom providers",
        )

    # Validate credentials
    gateway = LLMGateway(
        provider_type=body.provider_type,
        encrypted_api_key=encrypt_value(body.api_key),
        endpoint_url=body.endpoint_url,
        model=body.model,
    )
    is_valid, _err = await gateway.validate_credentials()

    provider = ModelProvider(
        owner_id=current_user.id,
        name=body.name,
        provider_type=body.provider_type,
        encrypted_api_key=encrypt_value(body.api_key),
        endpoint_url=body.endpoint_url,
        model=body.model,
        is_valid=is_valid,
        requests_per_minute=body.requests_per_minute,
        tokens_per_minute=body.tokens_per_minute,
        max_calls_per_experiment=body.max_calls_per_experiment,
        judge_api_key_enc=encrypt_value(body.judge_api_key) if body.judge_api_key and body.use_separate_judge else None,
        judge_endpoint=body.judge_endpoint,
        judge_model=body.judge_model,
        use_separate_judge=body.use_separate_judge,
        default_target_endpoint=body.default_target_endpoint,
        default_system_prompt=body.default_system_prompt,
        backup_api_key_enc=encrypt_value(body.backup_api_key) if body.backup_api_key and body.use_backup_key else None,
        backup_endpoint=body.backup_endpoint,
        backup_model=body.backup_model,
        use_backup_key=body.use_backup_key,
    )
    session.add(provider)
    await session.flush()

    await write_audit_log(
        session,
        user=current_user,
        action="provider.created",
        entity_type="model_provider",
        entity_id=provider.id,
        ip_address=request.client.host if request.client else None,
    )

    await session.refresh(provider)
    return await _to_response(provider, session)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UUID,
    body: ProviderUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProviderResponse:
    """Update a provider.

    When experiments reference this provider, only ``name`` may be changed —
    core settings (api_key, endpoint_url, model) are locked to protect
    historical experiment integrity.
    """
    provider = await _get_provider_or_404(provider_id, current_user, session)

    # Check if provider is referenced by experiments
    exp_count = await session.execute(
        select(func.count()).where(Experiment.provider_id == provider.id)
    )
    has_experiments = exp_count.scalar_one() > 0

    # When experiments exist, only name is editable
    if has_experiments:
        core_changes = []
        if body.api_key is not None:
            core_changes.append("api_key")
        if body.endpoint_url is not None:
            core_changes.append("endpoint_url")
        if body.model is not None:
            core_changes.append("model")
        if core_changes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot change {', '.join(core_changes)} — this provider "
                    f"is used by experiments. Only the name can be updated."
                ),
            )

    if body.name is not None:
        provider.name = body.name
    if body.endpoint_url is not None:
        provider.endpoint_url = body.endpoint_url
    if body.model is not None:
        provider.model = body.model

    if body.api_key is not None:
        provider.encrypted_api_key = encrypt_value(body.api_key)
        # Re-validate on key change
        gateway = LLMGateway(
            provider_type=provider.provider_type,
            encrypted_api_key=provider.encrypted_api_key,
            endpoint_url=provider.endpoint_url,
            model=provider.model,
        )
        provider.is_valid, _ = await gateway.validate_credentials()

    # Advanced fields — always update if provided
    if body.requests_per_minute is not None:
        provider.requests_per_minute = body.requests_per_minute
    if body.tokens_per_minute is not None:
        provider.tokens_per_minute = body.tokens_per_minute
    if body.max_calls_per_experiment is not None:
        provider.max_calls_per_experiment = body.max_calls_per_experiment
    if body.use_separate_judge is not None:
        provider.use_separate_judge = body.use_separate_judge
    if body.judge_api_key is not None:
        provider.judge_api_key_enc = encrypt_value(body.judge_api_key) if body.judge_api_key else None
    if body.judge_endpoint is not None:
        provider.judge_endpoint = body.judge_endpoint
    if body.judge_model is not None:
        provider.judge_model = body.judge_model
    if body.default_target_endpoint is not None:
        provider.default_target_endpoint = body.default_target_endpoint
    if body.default_system_prompt is not None:
        provider.default_system_prompt = body.default_system_prompt
    if body.use_backup_key is not None:
        provider.use_backup_key = body.use_backup_key
    if body.backup_api_key is not None:
        provider.backup_api_key_enc = encrypt_value(body.backup_api_key) if body.backup_api_key else None
    if body.backup_endpoint is not None:
        provider.backup_endpoint = body.backup_endpoint
    if body.backup_model is not None:
        provider.backup_model = body.backup_model

    await session.flush()

    await write_audit_log(
        session,
        user=current_user,
        action="provider.updated",
        entity_type="model_provider",
        entity_id=provider.id,
        ip_address=request.client.host if request.client else None,
    )

    await session.refresh(provider)
    return await _to_response(provider, session)


@router.delete("/{provider_id}", responses={204: {"description": "Provider deleted"}})
async def delete_provider(
    provider_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    """Delete a provider.

    Linked experiments keep their data but their ``provider_id`` is set
    to NULL (the FK uses ``ondelete=SET NULL``).
    """
    provider = await _get_provider_or_404(provider_id, current_user, session)

    await session.delete(provider)
    await session.flush()

    await write_audit_log(
        session,
        user=current_user,
        action="provider.deleted",
        entity_type="model_provider",
        entity_id=provider_id,
        ip_address=request.client.host if request.client else None,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{provider_id}/validate", response_model=ProviderValidationResult)
async def validate_provider(
    provider_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProviderValidationResult:
    """Validate a provider's credentials with a test call."""
    provider = await _get_provider_or_404(provider_id, current_user, session)

    gateway = LLMGateway(
        provider_type=provider.provider_type,
        encrypted_api_key=provider.encrypted_api_key,
        endpoint_url=provider.endpoint_url,
        model=provider.model,
    )
    start = time.monotonic()
    is_valid, error_msg = await gateway.validate_credentials()
    latency_ms = int((time.monotonic() - start) * 1000)
    provider.is_valid = is_valid
    await session.flush()

    return ProviderValidationResult(
        provider_id=provider.id,
        is_valid=is_valid,
        message="Provider credentials are valid" if is_valid else f"Validation failed: {error_msg}",
        latency_ms=latency_ms if is_valid else None,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_provider_or_404(
    provider_id: UUID,
    user: User,
    session: AsyncSession,
) -> ModelProvider:
    result = await session.execute(
        select(ModelProvider).where(
            ModelProvider.id == provider_id,
            ModelProvider.owner_id == user.id,
        )
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return provider
