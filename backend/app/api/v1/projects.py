"""
Projects API routes — CRUD, scope analysis, and API key management.

Projects are scoped per user — each user can only see their own projects.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.deps import get_current_user
from app.api.schemas.projects import (
    ApiKeyResponse,
    ProjectCreate,
    ProjectList,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdate,
    ScopeAnalysisResponse,
)
from app.api.schemas.shared import UserBrief
from app.services.audit import write_audit_log
from app.services.encryption import encrypt_value
from app.services import firewall as firewall_service
from app.services.llm_gateway import LLMGateway
from app.storage.database import get_async_session
from app.storage.models import Experiment, ModelProvider, Project, User

router = APIRouter(prefix="/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KEY_PREFIX = "art_"

def _generate_api_key() -> tuple[str, str, str]:
    """Generate a project API key → (raw_key, display_prefix, sha256_hash).

    Format: art_<43-char urlsafe token>
    The display prefix is the first 8 chars (e.g. art_su_r) so the UI can
    identify which key is which without exposing the full secret.
    """
    raw_key = f"{_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    prefix = raw_key[: len(_KEY_PREFIX) + 4]   # e.g. "art_su_r"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, prefix, key_hash


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        business_scope=project.business_scope,
        allowed_intents=project.allowed_intents or [],
        restricted_intents=project.restricted_intents or [],
        analyzed_scope=project.analyzed_scope,
        system_prompt=project.system_prompt,
        api_key_prefix=project.api_key_prefix,
        is_active=project.is_active,
        created_by=None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=ProjectList)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=200),
    is_active: bool | None = Query(None),
    sort_by: str = Query("created_at", pattern=r"^(name|created_at|updated_at)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProjectList:
    """List projects owned by the current user."""
    query = select(Project).where(
        Project.owner_id == current_user.id
    )
    count_query = select(func.count()).select_from(Project).where(
        Project.owner_id == current_user.id
    )

    if is_active is not None:
        query = query.where(Project.is_active == is_active)
        count_query = count_query.where(Project.is_active == is_active)
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))
        count_query = count_query.where(Project.name.ilike(f"%{search}%"))

    sort_column_map = {"name": Project.name, "created_at": Project.created_at, "updated_at": Project.updated_at}
    sort_col = sort_column_map.get(sort_by, Project.created_at)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    result = await session.execute(query)
    projects = result.scalars().all()

    items = []
    for p in projects:
        # Get experiment count
        exp_count_res = await session.execute(
            select(func.count()).where(Experiment.project_id == p.id)
        )
        items.append(ProjectSummary(
            id=p.id,
            name=p.name,
            description=p.description,
            is_active=p.is_active,
            experiment_count=exp_count_res.scalar_one(),
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))

    return ProjectList.build(items=items, total=total, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProjectResponse:
    project = await _get_project_or_404(project_id, current_user, session)
    return _to_response(project)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProjectResponse:
    """Create a new project. Returns the project (API key shown via separate endpoint)."""
    raw_key, prefix, key_hash = _generate_api_key()

    project = Project(
        owner_id=current_user.id,
        name=body.name,
        description=body.description,
        business_scope=body.business_scope,
        allowed_intents=body.allowed_intents,
        restricted_intents=body.restricted_intents,
        system_prompt=body.system_prompt,
        api_key_hash=key_hash,
        api_key_prefix=prefix,
    )
    session.add(project)
    await session.flush()

    await write_audit_log(
        session,
        user=current_user,
        action="project.created",
        entity_type="project",
        entity_id=project.id,
        ip_address=request.client.host if request.client else None,
    )

    resp = _to_response(project)
    return resp


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProjectResponse:
    project = await _get_project_or_404(project_id, current_user, session)

    # Track whether scope-related fields changed (for cache invalidation)
    scope_changed = False

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.business_scope is not None:
        project.business_scope = body.business_scope
        scope_changed = True
    if body.allowed_intents is not None:
        project.allowed_intents = body.allowed_intents
        scope_changed = True
    if body.restricted_intents is not None:
        project.restricted_intents = body.restricted_intents
        scope_changed = True
    if body.system_prompt is not None:
        project.system_prompt = body.system_prompt

    await session.flush()

    # Phase 8 §7.2 — invalidate firewall scope cache when scope/intents change
    if scope_changed:
        await firewall_service.invalidate_scope_cache(project.id)

    await write_audit_log(
        session,
        user=current_user,
        action="project.updated",
        entity_type="project",
        entity_id=project.id,
        ip_address=request.client.host if request.client else None,
    )

    return _to_response(project)


@router.delete("/{project_id}", responses={204: {"description": "Project deleted"}})
async def delete_project(
    project_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    project = await _get_project_or_404(project_id, current_user, session)

    # Phase 8 §7.2 — invalidate firewall caches before deletion
    if project.api_key_hash:
        await firewall_service.invalidate_auth_cache(project.api_key_hash)
    await firewall_service.invalidate_scope_cache(project.id)
    await firewall_service.invalidate_rules_cache(project.id)

    await session.delete(project)
    await session.flush()

    await write_audit_log(
        session,
        user=current_user,
        action="project.deleted",
        entity_type="project",
        entity_id=project_id,
        ip_address=request.client.host if request.client else None,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/analyze-scope", response_model=ScopeAnalysisResponse)
async def analyze_scope(
    project_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ScopeAnalysisResponse:
    """Use an LLM to analyze and structure the project's scope and intents."""
    project = await _get_project_or_404(project_id, current_user, session)

    # Find a valid provider owned by user
    provider_result = await session.execute(
        select(ModelProvider).where(
            ModelProvider.owner_id == current_user.id,
            ModelProvider.is_valid == True,  # noqa: E712
        ).limit(1)
    )
    provider = provider_result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid model provider configured",
        )

    gateway = LLMGateway(
        provider_type=provider.provider_type,
        encrypted_api_key=provider.encrypted_api_key,
        endpoint_url=provider.endpoint_url,
    )

    prompt = (
        "Analyze and structure the following AI project scope definition. "
        "Deduplicate, categorize, and return a clean JSON object with keys: "
        "'business_scope_summary', 'allowed_intents' (array), 'restricted_intents' (array), "
        "'risk_areas' (array), 'recommendations' (array).\n\n"
        f"Business Scope:\n{project.business_scope}\n\n"
        f"Allowed Intents:\n{json.dumps(project.allowed_intents)}\n\n"
        f"Restricted Intents:\n{json.dumps(project.restricted_intents)}"
    )

    raw_response = await gateway.chat(
        [{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    try:
        analyzed = json.loads(raw_response)
    except json.JSONDecodeError:
        analyzed = {"raw": raw_response}

    project.analyzed_scope = analyzed
    await session.flush()

    return ScopeAnalysisResponse(
        analyzed_scope=analyzed,
        message="Scope analysis complete",
    )


@router.post("/{project_id}/regenerate-api-key", response_model=ApiKeyResponse)
async def regenerate_api_key(
    project_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ApiKeyResponse:
    """Regenerate the project's API key. Old key is invalidated immediately."""
    project = await _get_project_or_404(project_id, current_user, session)

    # Phase 8 §7.2 — invalidate the OLD key's auth cache before replacing
    old_key_hash = project.api_key_hash
    if old_key_hash:
        await firewall_service.invalidate_auth_cache(old_key_hash)

    raw_key, prefix, key_hash = _generate_api_key()

    project.api_key_hash = key_hash
    project.api_key_prefix = prefix
    await session.flush()

    await write_audit_log(
        session,
        user=current_user,
        action="project.api_key_regenerated",
        entity_type="project",
        entity_id=project.id,
        ip_address=request.client.host if request.client else None,
    )

    return ApiKeyResponse(
        api_key=raw_key,
        api_key_prefix=prefix,
        message="API key regenerated. Store it securely — it won't be shown again.",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_project_or_404(
    project_id: UUID,
    user: User,
    session: AsyncSession,
) -> Project:
    result = await session.execute(
        select(Project)
        .where(
            Project.id == project_id,
            Project.owner_id == user.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
