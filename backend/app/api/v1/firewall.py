"""
Firewall API routes (Phase 6.6 + Phase 8).

Mixed auth:
  - POST /firewall/{project_id}  → API key auth (public evaluation)
                                    Full pipeline via firewall service (Phase 8)
  - All others                   → JWT auth (management)

Provides real-time prompt evaluation, rule CRUD, log browsing,
usage statistics, and integration documentation.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import cast, case, func, select, and_, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.engine.deps import require_member
from app.api.schemas.firewall import (
    DailyStats,
    FirewallEvalRequest,
    FirewallIntegrationResponse,
    FirewallLogEntry,
    FirewallLogList,
    FirewallRuleCreate,
    FirewallRuleList,
    FirewallRuleResponse,
    FirewallRuleUpdate,
    FirewallStatsResponse,
    FirewallVerdictResponse,
    PATTERN_RULE_TYPES,
)
from app.api.schemas.shared import UserBrief
from app.config import settings
from app.services.audit import write_audit_log
from app.services import firewall as firewall_service
from app.storage.database import get_async_session
from app.storage.models.firewall_log import FirewallLog
from app.storage.models.firewall_rule import FirewallRule
from app.storage.models.project import Project
from app.storage.models.user import User

router = APIRouter(tags=["firewall"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_project_or_404(
    project_id: UUID,
    user: User,
    session: AsyncSession,
) -> Project:
    stmt = select(Project).where(
        Project.id == project_id,
        Project.owner_id == user.id,
    )
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
    return project


def _rule_to_response(rule: FirewallRule) -> FirewallRuleResponse:
    created_by = None
    if rule.created_by:
        created_by = UserBrief(
            id=rule.created_by.id,
            email=rule.created_by.email,
            full_name=rule.created_by.full_name,
        )
    return FirewallRuleResponse(
        id=rule.id,
        name=rule.name,
        rule_type=rule.rule_type,
        pattern=rule.pattern,
        policy=rule.policy,
        priority=rule.priority,
        is_active=rule.is_active,
        created_by=created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _ensure_firewall_enabled() -> None:
    if not settings.firewall_enabled:
        raise HTTPException(
            status_code=501,
            detail="FIREWALL_COMING_SOON: AI Firewall is not enabled in this environment yet.",
        )


def _encode_cursor(sort_value: str, record_id: UUID) -> str:
    payload = json.dumps({"s": str(sort_value), "id": str(record_id)})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, UUID]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return payload["s"], UUID(payload["id"])
    except Exception:
        raise HTTPException(status_code=400, detail="INVALID_CURSOR")


# ---------------------------------------------------------------------------
# 1. Public Evaluation — POST /firewall/{project_id}
#    Full pipeline delegated to firewall service (Phase 8)
# ---------------------------------------------------------------------------


@router.post(
    "/firewall/{project_id}",
    response_model=FirewallVerdictResponse,
)
async def evaluate_prompt(
    project_id: UUID,
    body: FirewallEvalRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Evaluate a user prompt against the project's firewall rules and scope.

    Authentication is handled internally by the firewall service using
    Redis-cached API key verification with negative caching (Phase 8 §3.2).
    """
    _ensure_firewall_enabled()

    # Extract API key from Authorization header
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    raw_key = authorization.removeprefix("Bearer ").strip()

    verdict = await firewall_service.evaluate_prompt(
        project_id_param=str(project_id),
        prompt=body.prompt,
        agent_prompt=body.agent_prompt,
        raw_api_key=raw_key,
        ip_address=request.client.host if request.client else None,
        session=session,
    )

    return FirewallVerdictResponse(**verdict)


# ---------------------------------------------------------------------------
# 2. List firewall rules — GET /projects/{project_id}/firewall/rules
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/firewall/rules",
    response_model=FirewallRuleList,
)
async def list_rules(
    project_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    stmt = (
        select(FirewallRule)
        .options(joinedload(FirewallRule.created_by))
        .where(FirewallRule.project_id == project.id)
        .order_by(FirewallRule.priority.asc())
    )
    result = await session.execute(stmt)
    rules = result.unique().scalars().all()

    return FirewallRuleList(
        items=[_rule_to_response(r) for r in rules],
        total=len(rules),
    )


# ---------------------------------------------------------------------------
# 3. Create firewall rule — POST /projects/{project_id}/firewall/rules
# ---------------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/firewall/rules",
    response_model=FirewallRuleResponse,
    status_code=201,
)
async def create_rule(
    project_id: UUID,
    body: FirewallRuleCreate,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    rule = FirewallRule(
        project_id=project.id,
        created_by_id=user.id,
        name=body.name,
        rule_type=body.rule_type,
        pattern=body.pattern,
        policy=body.policy,
        priority=body.priority,
        is_active=body.is_active,
    )
    session.add(rule)
    await session.flush()
    await session.refresh(rule)

    # Invalidate rule cache
    await firewall_service.invalidate_rules_cache(project.id)

    await write_audit_log(
        session=session,
        user=user,
        action="firewall_rule.created",
        entity_type="firewall_rule",
        entity_id=str(rule.id),
        details={"name": rule.name, "rule_type": rule.rule_type},
    )

    # Reload with creator
    stmt = (
        select(FirewallRule)
        .options(joinedload(FirewallRule.created_by))
        .where(FirewallRule.id == rule.id)
    )
    result = await session.execute(stmt)
    rule = result.unique().scalar_one()

    return _rule_to_response(rule)


# ---------------------------------------------------------------------------
# 4. Update firewall rule — PUT /projects/{project_id}/firewall/rules/{rule_id}
# ---------------------------------------------------------------------------


@router.put(
    "/projects/{project_id}/firewall/rules/{rule_id}",
    response_model=FirewallRuleResponse,
)
async def update_rule(
    project_id: UUID,
    rule_id: UUID,
    body: FirewallRuleUpdate,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    stmt = (
        select(FirewallRule)
        .options(joinedload(FirewallRule.created_by))
        .where(
            FirewallRule.id == rule_id,
            FirewallRule.project_id == project.id,
        )
    )
    result = await session.execute(stmt)
    rule = result.unique().scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="RULE_NOT_FOUND")

    # Cross-field validation against existing rule_type
    if body.pattern is not None and rule.rule_type not in PATTERN_RULE_TYPES:
        raise HTTPException(status_code=400, detail="FIELD_NOT_APPLICABLE")
    if body.policy is not None and rule.rule_type != "custom_policy":
        raise HTTPException(status_code=400, detail="FIELD_NOT_APPLICABLE")

    if body.name is not None:
        rule.name = body.name
    if body.pattern is not None:
        rule.pattern = body.pattern
    if body.policy is not None:
        rule.policy = body.policy
    if body.priority is not None:
        rule.priority = body.priority
    if body.is_active is not None:
        rule.is_active = body.is_active

    await session.flush()
    await session.refresh(rule)

    # Invalidate rule cache
    await firewall_service.invalidate_rules_cache(project.id)

    await write_audit_log(
        session=session,
        user=user,
        action="firewall_rule.updated",
        entity_type="firewall_rule",
        entity_id=str(rule.id),
        details={"name": rule.name},
    )

    return _rule_to_response(rule)


# ---------------------------------------------------------------------------
# 5. Delete firewall rule — DELETE /projects/{project_id}/firewall/rules/{rule_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/projects/{project_id}/firewall/rules/{rule_id}",
    status_code=204,
)
async def delete_rule(
    project_id: UUID,
    rule_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    stmt = select(FirewallRule).where(
        FirewallRule.id == rule_id,
        FirewallRule.project_id == project.id,
    )
    result = await session.execute(stmt)
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="RULE_NOT_FOUND")

    rule_name = rule.name
    await session.delete(rule)

    # Invalidate rule cache
    await firewall_service.invalidate_rules_cache(project.id)

    await write_audit_log(
        session=session,
        user=user,
        action="firewall_rule.deleted",
        entity_type="firewall_rule",
        entity_id=str(rule_id),
        details={"name": rule_name},
    )

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# 6. Firewall logs — GET /projects/{project_id}/firewall/logs
# ---------------------------------------------------------------------------

LOG_SORT_COLUMNS = {
    "created_at": FirewallLog.created_at,
    "latency_ms": FirewallLog.latency_ms,
}


@router.get(
    "/projects/{project_id}/firewall/logs",
    response_model=FirewallLogList,
)
async def list_firewall_logs(
    project_id: UUID,
    cursor: str | None = Query(None),
    page_size: int = Query(50, ge=1, le=100),
    verdict_status: bool | None = Query(None),
    fail_category: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    stmt = (
        select(FirewallLog, FirewallRule.name.label("rule_name"))
        .outerjoin(FirewallRule, FirewallLog.matched_rule_id == FirewallRule.id)
        .where(FirewallLog.project_id == project.id)
    )

    # Filters
    if verdict_status is not None:
        stmt = stmt.where(FirewallLog.verdict_status == verdict_status)
    if fail_category:
        stmt = stmt.where(FirewallLog.fail_category == fail_category)
    if date_from:
        stmt = stmt.where(FirewallLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(FirewallLog.created_at <= date_to)

    # Total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = LOG_SORT_COLUMNS.get(sort_by, FirewallLog.created_at)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_col.desc(), FirewallLog.id.desc())
    else:
        stmt = stmt.order_by(sort_col.asc(), FirewallLog.id.asc())

    # Cursor
    if cursor:
        cursor_sort_val, cursor_id = _decode_cursor(cursor)
        if sort_order == "desc":
            stmt = stmt.where(
                (sort_col < cursor_sort_val)
                | (and_(sort_col == cursor_sort_val, FirewallLog.id < cursor_id))
            )
        else:
            stmt = stmt.where(
                (sort_col > cursor_sort_val)
                | (and_(sort_col == cursor_sort_val, FirewallLog.id > cursor_id))
            )

    stmt = stmt.limit(page_size + 1)
    rows = (await session.execute(stmt)).all()

    has_next = len(rows) > page_size
    page_rows = rows[:page_size]

    items: list[FirewallLogEntry] = []
    last_sort_value = ""
    last_id: UUID | None = None
    for log, rule_name in page_rows:
        items.append(
            FirewallLogEntry(
                id=log.id,
                prompt_preview=log.prompt_preview,
                verdict_status=log.verdict_status,
                fail_category=log.fail_category,
                confidence=log.confidence,
                matched_rule_name=rule_name,
                latency_ms=log.latency_ms,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
        )
        if sort_by == "latency_ms":
            last_sort_value = str(log.latency_ms)
        else:
            last_sort_value = log.created_at.isoformat() if log.created_at else ""
        last_id = log.id

    next_cursor = None
    if has_next and last_id is not None:
        next_cursor = _encode_cursor(str(last_sort_value), last_id)

    return FirewallLogList(
        items=items,
        total=total,
        cursor=next_cursor,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# 7. Firewall stats — GET /projects/{project_id}/firewall/stats
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/firewall/stats",
    response_model=FirewallStatsResponse,
)
async def get_firewall_stats(
    project_id: UUID,
    period: str = Query("7d", pattern=r"^(24h|7d|30d)$"),
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    # Determine cutoff
    now = datetime.now(timezone.utc)
    if period == "24h":
        cutoff = now - timedelta(hours=24)
    elif period == "7d":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(days=30)

    base_filter = and_(
        FirewallLog.project_id == project.id,
        FirewallLog.created_at >= cutoff,
    )

    # Aggregate counts
    agg_stmt = select(
        func.count(FirewallLog.id).label("total"),
        func.count(case((FirewallLog.verdict_status.is_(True), 1))).label("passed"),
        func.count(case((FirewallLog.verdict_status.is_(False), 1))).label("blocked"),
        func.coalesce(func.avg(FirewallLog.latency_ms), 0).label("avg_latency"),
    ).where(base_filter)

    agg_row = (await session.execute(agg_stmt)).one()
    total_requests = agg_row.total
    passed = agg_row.passed
    blocked = agg_row.blocked
    avg_latency_ms = float(agg_row.avg_latency)

    pass_rate = (passed / total_requests) if total_requests > 0 else 0.0

    # Percentiles (PostgreSQL PERCENTILE_CONT)
    p95 = 0.0
    p99 = 0.0
    if total_requests > 0:
        try:
            pct_stmt = select(
                func.percentile_cont(0.95).within_group(
                    FirewallLog.latency_ms.asc()
                ).label("p95"),
                func.percentile_cont(0.99).within_group(
                    FirewallLog.latency_ms.asc()
                ).label("p99"),
            ).where(base_filter)
            pct_row = (await session.execute(pct_stmt)).one()
            p95 = float(pct_row.p95 or 0)
            p99 = float(pct_row.p99 or 0)
        except Exception:
            pass

    # Category breakdown
    cat_stmt = (
        select(
            FirewallLog.fail_category,
            func.count(FirewallLog.id).label("cnt"),
        )
        .where(base_filter, FirewallLog.fail_category.isnot(None))
        .group_by(FirewallLog.fail_category)
    )
    cat_rows = (await session.execute(cat_stmt)).all()
    category_breakdown = {row.fail_category: row.cnt for row in cat_rows}

    # Daily breakdown
    daily_stmt = (
        select(
            cast(FirewallLog.created_at, Date).label("day"),
            func.count(FirewallLog.id).label("total"),
            func.count(case((FirewallLog.verdict_status.is_(True), 1))).label("passed"),
            func.count(case((FirewallLog.verdict_status.is_(False), 1))).label("blocked"),
        )
        .where(base_filter)
        .group_by(cast(FirewallLog.created_at, Date))
        .order_by(cast(FirewallLog.created_at, Date).asc())
    )
    daily_rows = (await session.execute(daily_stmt)).all()
    daily_breakdown = [
        DailyStats(
            date=str(row.day),
            total=row.total,
            passed=row.passed,
            blocked=row.blocked,
        )
        for row in daily_rows
    ]

    return FirewallStatsResponse(
        project_id=project.id,
        period=period,
        total_requests=total_requests,
        passed=passed,
        blocked=blocked,
        pass_rate=round(pass_rate, 4),
        category_breakdown=category_breakdown,
        avg_latency_ms=round(avg_latency_ms, 2),
        p95_latency_ms=round(p95, 2),
        p99_latency_ms=round(p99, 2),
        daily_breakdown=daily_breakdown,
    )


# ---------------------------------------------------------------------------
# 8. Integration details — GET /projects/{project_id}/firewall/integration
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/firewall/integration",
    response_model=FirewallIntegrationResponse,
)
async def get_integration(
    project_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    _ensure_firewall_enabled()
    project = await _get_project_or_404(project_id, user, session)

    endpoint_url = f"{settings.api_v1_prefix}/firewall/{project.id}"

    python_snippet = f'''import requests

response = requests.post(
    "{endpoint_url}",
    headers={{"Authorization": "Bearer YOUR_API_KEY"}},
    json={{"prompt": "User message here"}}
)
verdict = response.json()
if verdict["status"]:
    # Safe — proceed to your AI
    pass
else:
    # Blocked — handle accordingly
    print(f"Blocked: {{verdict['fail_category']}} - {{verdict['explanation']}}")'''

    javascript_snippet = f'''const response = await fetch("{endpoint_url}", {{
  method: "POST",
  headers: {{
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
  }},
  body: JSON.stringify({{ prompt: "User message here" }})
}});
const verdict = await response.json();
if (verdict.status) {{
  // Safe — proceed to your AI
}} else {{
  // Blocked — handle accordingly
  console.log(`Blocked: ${{verdict.fail_category}} - ${{verdict.explanation}}`);
}}'''

    curl_snippet = f'''curl -X POST {endpoint_url} \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"prompt": "User message here"}}\''''

    return FirewallIntegrationResponse(
        endpoint_url=endpoint_url,
        api_key_prefix=project.api_key_prefix or "",
        rate_limit=settings.firewall_rate_limit_per_minute,
        python_snippet=python_snippet,
        javascript_snippet=javascript_snippet,
        curl_snippet=curl_snippet,
    )
