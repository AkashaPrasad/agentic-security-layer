"""
Firewall Service — Phase 8

Core evaluation pipeline for the AI Firewall. Implements the three-layer
waterfall (pattern rules → custom policies → LLM-as-Judge) with Redis-first
caching on the hot path to stay within the 500 ms latency budget.

Public API
----------
- ``evaluate_prompt``           — full evaluation pipeline
- ``authenticate_api_key``      — Redis-cached auth with negative caching
- ``load_scope``                — Redis-cached scope loading
- ``load_rules``                — Redis-cached rules loading
- ``check_rate_limit``          — sliding-window rate limiter (fail-open)
- ``evaluate_pattern_rules``    — deterministic regex matching
- ``evaluate_with_llm``         — LLM-as-Judge deep evaluation
- ``write_firewall_log``        — fire-and-forget async log writer

Cache invalidation helpers:
- ``invalidate_auth_cache``
- ``invalidate_scope_cache``
- ``invalidate_rules_cache``
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
import uuid as _uuid
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.llm_gateway import LLMGateway
from app.storage.models.firewall_log import FirewallLog
from app.storage.models.firewall_rule import FirewallRule
from app.storage.models.provider import ModelProvider
from app.storage.models.project import Project

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUTH_CACHE_TTL = 300  # 5 minutes
SCOPE_CACHE_TTL = 300
RULES_CACHE_TTL = 300


# ---------------------------------------------------------------------------
# Redis helper
# ---------------------------------------------------------------------------


async def _get_redis() -> aioredis.Redis:
    """Return a Redis client for application cache."""
    return aioredis.Redis.from_url(
        str(settings.redis_connection_url),
        decode_responses=True,
    )


# ---------------------------------------------------------------------------
# 1. Authentication — Redis-cached with negative caching (§3.2)
# ---------------------------------------------------------------------------


async def authenticate_api_key(
    raw_key: str,
    session: AsyncSession,
) -> dict:
    """Authenticate a project API key.

    Returns ``{"project_id": str, "owner_id": str}`` on success.

    Uses a Redis cache (``firewall:auth:{hash}``) with 5-minute TTL.
    Invalid keys are cached as ``"null"`` to block brute-force attempts.
    """
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # --- Redis cache check ---
    try:
        rd = await _get_redis()
        cached = await rd.get(f"firewall:auth:{key_hash}")
        await rd.aclose()

        if cached == "null":
            raise HTTPException(status_code=401, detail="Invalid API key")
        if cached:
            return json.loads(cached)
    except HTTPException:
        raise
    except Exception:
        pass  # Redis unavailable — fall through to DB

    # --- Cache miss — query DB ---
    result = await session.execute(
        select(Project.id, Project.owner_id).where(
            Project.api_key_hash == key_hash,
            Project.is_active.is_(True),
        )
    )
    row = result.one_or_none()

    if row is None:
        # Negative cache
        try:
            rd = await _get_redis()
            await rd.set(f"firewall:auth:{key_hash}", "null", ex=AUTH_CACHE_TTL)
            await rd.aclose()
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Invalid API key")

    data = {
        "project_id": str(row.id),
        "owner_id": str(row.owner_id),
    }

    try:
        rd = await _get_redis()
        await rd.set(
            f"firewall:auth:{key_hash}", json.dumps(data), ex=AUTH_CACHE_TTL,
        )
        await rd.aclose()
    except Exception:
        pass

    return data


# ---------------------------------------------------------------------------
# 2. Rate Limiting — sliding-window sorted set (§8)
# ---------------------------------------------------------------------------


async def check_rate_limit(project_id: str) -> None:
    """Sliding-window rate limit using Redis sorted set.

    Raises ``HTTPException(429)`` when the limit is exceeded.
    **Fails open**: if Redis is down, rate limiting is skipped.
    """
    try:
        rd = await _get_redis()
        rate_key = f"firewall:rate:{project_id}"
        now_ms = int(time.time() * 1000)
        window_ms = 60_000

        pipe = rd.pipeline()
        pipe.zremrangebyscore(rate_key, 0, now_ms - window_ms)
        pipe.zcard(rate_key)
        pipe.zadd(rate_key, {str(_uuid.uuid4()): now_ms})
        pipe.expire(rate_key, 61)
        results = await pipe.execute()
        current_count = results[1]

        if current_count >= settings.firewall_rate_limit_per_minute:
            oldest = await rd.zrange(rate_key, 0, 0, withscores=True)
            retry_after = 60
            if oldest:
                oldest_ms = int(oldest[0][1])
                retry_after = max(1, int((oldest_ms + window_ms - now_ms) / 1000))
            await rd.aclose()
            raise HTTPException(
                status_code=429,
                detail="RATE_LIMIT_EXCEEDED",
                headers={"Retry-After": str(retry_after)},
            )
        await rd.aclose()
    except HTTPException:
        raise
    except Exception:
        pass  # Fail open — Redis down, skip rate limiting


# ---------------------------------------------------------------------------
# 3. Scope Loading — Redis-cached (§7.1)
# ---------------------------------------------------------------------------


async def load_scope(
    project_id: str,
    session: AsyncSession,
) -> dict:
    """Load a project's scope definition from Redis or DB.

    Returns ``{"business_scope": str, "allowed_intents": list,
    "restricted_intents": list}``.
    """
    scope_key = f"firewall:scope:{project_id}"

    try:
        rd = await _get_redis()
        cached = await rd.get(scope_key)
        await rd.aclose()
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    # Cache miss — query DB
    result = await session.execute(
        select(
            Project.business_scope,
            Project.allowed_intents,
            Project.restricted_intents,
        ).where(Project.id == UUID(project_id))
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")

    scope = {
        "business_scope": row.business_scope or "",
        "allowed_intents": row.allowed_intents or [],
        "restricted_intents": row.restricted_intents or [],
    }

    try:
        rd = await _get_redis()
        await rd.set(scope_key, json.dumps(scope), ex=SCOPE_CACHE_TTL)
        await rd.aclose()
    except Exception:
        pass

    return scope


# ---------------------------------------------------------------------------
# 4. Rules Loading — Redis-cached (§7.1)
# ---------------------------------------------------------------------------


async def load_rules(
    project_id: str,
    session: AsyncSession,
) -> list[dict]:
    """Load active firewall rules sorted by priority.

    Returns a list of dicts with keys: id, name, rule_type, pattern, policy.
    """
    rules_key = f"firewall:rules:{project_id}"

    try:
        rd = await _get_redis()
        cached = await rd.get(rules_key)
        await rd.aclose()
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    # Cache miss — query DB
    stmt = (
        select(FirewallRule)
        .where(
            FirewallRule.project_id == UUID(project_id),
            FirewallRule.is_active.is_(True),
        )
        .order_by(FirewallRule.priority.asc())
    )
    result = await session.execute(stmt)
    db_rules = result.scalars().all()

    rules = [
        {
            "id": str(r.id),
            "name": r.name,
            "rule_type": r.rule_type,
            "pattern": r.pattern,
            "policy": r.policy,
        }
        for r in db_rules
    ]

    try:
        rd = await _get_redis()
        await rd.set(rules_key, json.dumps(rules), ex=RULES_CACHE_TTL)
        await rd.aclose()
    except Exception:
        pass

    return rules


# ---------------------------------------------------------------------------
# 5. Pattern Rule Evaluation (§4.2 — Layer 1)
# ---------------------------------------------------------------------------


def evaluate_pattern_rules(
    prompt: str,
    rules: list[dict],
) -> dict | None:
    """Evaluate block/allow pattern rules in priority order.

    Returns a verdict dict on first match, or ``None`` if no patterns match.
    Individual regex errors are silently skipped (fail-open per rule).
    """
    for rule in rules:
        if rule["rule_type"] == "block_pattern" and rule.get("pattern"):
            try:
                if re.search(rule["pattern"], prompt, re.IGNORECASE):
                    return {
                        "status": False,
                        "fail_category": "restriction",
                        "explanation": f"Blocked by pattern rule: {rule['name']}",
                        "confidence": 1.0,
                        "matched_rule": rule["name"],
                        "matched_rule_id": rule["id"],
                    }
            except re.error:
                continue

        elif rule["rule_type"] == "allow_pattern" and rule.get("pattern"):
            try:
                if re.search(rule["pattern"], prompt, re.IGNORECASE):
                    return {
                        "status": True,
                        "fail_category": None,
                        "explanation": f"Allowed by pattern rule: {rule['name']}",
                        "confidence": 1.0,
                        "matched_rule": rule["name"],
                        "matched_rule_id": rule["id"],
                    }
            except re.error:
                continue

    return None


# ---------------------------------------------------------------------------
# 6. LLM-as-Judge Evaluation (§4.4 — Layer 3)
# ---------------------------------------------------------------------------


def build_judge_prompt(
    scope: dict,
    custom_policies: list[str],
    agent_prompt: str | None,
) -> str:
    """Construct the system prompt for the LLM judge."""
    parts = [
        "You are an AI Firewall judge. Evaluate whether the user prompt "
        "is safe and within scope.",
        'Respond ONLY with a JSON object: {"status": bool, '
        '"fail_category": str|null, "explanation": str, "confidence": float}',
        "",
        f"Business scope: {scope.get('business_scope', 'Not defined')}",
        f"Allowed intents: {json.dumps(scope.get('allowed_intents', []))}",
        f"Restricted intents: {json.dumps(scope.get('restricted_intents', []))}",
    ]
    if custom_policies:
        parts.append("")
        parts.append("Custom policies to enforce:")
        for i, p in enumerate(custom_policies, 1):
            parts.append(f"  {i}. {p}")
    if agent_prompt:
        parts.append("")
        parts.append(f"Agent/system prompt context: {agent_prompt}")
    parts.extend([
        "",
        "fail_category values when status=false:",
        '  - "off_topic": prompt is outside the defined business scope',
        '  - "violation": prompt violates allowed intents',
        '  - "restriction": prompt attempts a restricted action',
        "",
        "If the prompt is safe and within scope, set status=true "
        "and fail_category=null.",
    ])
    return "\n".join(parts)


async def evaluate_with_llm(
    prompt: str,
    scope: dict,
    rules: list[dict],
    owner_id: str,
    agent_prompt: str | None,
    session: AsyncSession,
) -> dict:
    """Run the LLM-as-Judge evaluation.

    Returns a verdict dict. Raises ``HTTPException(400)`` if no provider
    is configured, or ``HTTPException(502)`` if the LLM call fails.
    """
    # Find a valid provider for this user
    stmt = select(ModelProvider).where(
        ModelProvider.owner_id == UUID(owner_id),
        ModelProvider.is_valid.is_(True),
    )
    result = await session.execute(stmt)
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=400, detail="NO_PROVIDER_CONFIGURED")

    # Collect custom policy text
    custom_policies = [
        r["policy"] for r in rules
        if r["rule_type"] == "custom_policy" and r.get("policy")
    ]

    system_prompt = build_judge_prompt(scope, custom_policies, agent_prompt)

    try:
        gateway = LLMGateway(
            provider_type=provider.provider_type,
            encrypted_api_key=provider.encrypted_api_key,
            endpoint_url=provider.endpoint_url,
            model=settings.llm_judge_model,
        )
        response_text = await gateway.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        verdict = json.loads(response_text)
    except Exception:
        raise HTTPException(status_code=502, detail="EVALUATION_FAILED")

    verdict_status = verdict.get("status", True)
    return {
        "status": verdict_status,
        "fail_category": (
            verdict.get("fail_category") if not verdict_status else None
        ),
        "explanation": verdict.get("explanation", "Evaluation complete."),
        "confidence": float(verdict.get("confidence", 0.5)),
        "matched_rule": None,
        "matched_rule_id": None,
    }


# ---------------------------------------------------------------------------
# 7. Async Log Writer (§10.1 — fire-and-forget)
# ---------------------------------------------------------------------------


async def write_firewall_log(
    project_id: str,
    prompt: str,
    agent_prompt: str | None,
    verdict_status: bool,
    fail_category: str | None,
    explanation: str | None,
    confidence: float | None,
    matched_rule_id: str | None,
    latency_ms: int,
    ip_address: str | None,
) -> None:
    """Persist a firewall evaluation log. Uses an independent DB session."""
    from app.storage.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as log_session:
            log = FirewallLog(
                project_id=UUID(project_id),
                matched_rule_id=(
                    UUID(matched_rule_id) if matched_rule_id else None
                ),
                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                prompt_preview=prompt[:200] if prompt else None,
                agent_prompt_hash=(
                    hashlib.sha256(agent_prompt.encode()).hexdigest()
                    if agent_prompt
                    else None
                ),
                verdict_status=verdict_status,
                fail_category=fail_category,
                explanation=explanation,
                confidence=confidence,
                latency_ms=latency_ms,
                ip_address=ip_address,
            )
            log_session.add(log)
            await log_session.commit()
    except Exception:
        pass  # Fire-and-forget — never crash the response


# ---------------------------------------------------------------------------
# 8. Full Evaluation Pipeline (§4.1)
# ---------------------------------------------------------------------------


async def evaluate_prompt(
    project_id_param: str,
    prompt: str,
    agent_prompt: str | None,
    raw_api_key: str,
    ip_address: str | None,
    session: AsyncSession,
) -> dict:
    """Execute the complete firewall evaluation pipeline.

    Sequence (per Phase 8 §4.1):
      1. Auth — Redis-cached with negative caching
      2. Rate limit — sliding-window sorted set (fail-open)
      3. Load scope — Redis-cached
      4. Load rules — Redis-cached
      5. Pattern rules — deterministic regex (fast path)
      6. LLM-as-Judge — context-aware deep evaluation
      7. Async log write — fire-and-forget

    Returns a dict suitable for ``FirewallVerdictResponse``.
    """
    start_time = time.monotonic()

    # 1. Authenticate
    auth = await authenticate_api_key(raw_api_key, session)
    project_id = auth["project_id"]
    owner_id = auth["owner_id"]

    # Verify that the path parameter matches the authenticated project
    if project_id != project_id_param:
        raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")

    # 2. Rate limit
    await check_rate_limit(project_id)

    # 3. Load scope
    scope = await load_scope(project_id, session)

    # 4. Load rules
    rules = await load_rules(project_id, session)

    # 5. Pattern rules (fast path — ~1 ms)
    pattern_verdict = evaluate_pattern_rules(prompt, rules)
    if pattern_verdict:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        asyncio.create_task(
            write_firewall_log(
                project_id=project_id,
                prompt=prompt,
                agent_prompt=agent_prompt,
                verdict_status=pattern_verdict["status"],
                fail_category=pattern_verdict["fail_category"],
                explanation=pattern_verdict["explanation"],
                confidence=pattern_verdict["confidence"],
                matched_rule_id=pattern_verdict.get("matched_rule_id"),
                latency_ms=latency_ms,
                ip_address=ip_address,
            )
        )
        return {
            "status": pattern_verdict["status"],
            "fail_category": pattern_verdict["fail_category"],
            "explanation": pattern_verdict["explanation"],
            "confidence": pattern_verdict["confidence"],
            "matched_rule": pattern_verdict["matched_rule"],
        }

    # 6. LLM-as-Judge (deep evaluation — ~300-400 ms)
    llm_verdict = await evaluate_with_llm(
        prompt=prompt,
        scope=scope,
        rules=rules,
        owner_id=owner_id,
        agent_prompt=agent_prompt,
        session=session,
    )

    latency_ms = int((time.monotonic() - start_time) * 1000)

    # 7. Async log write (fire-and-forget)
    asyncio.create_task(
        write_firewall_log(
            project_id=project_id,
            prompt=prompt,
            agent_prompt=agent_prompt,
            verdict_status=llm_verdict["status"],
            fail_category=llm_verdict["fail_category"],
            explanation=llm_verdict["explanation"],
            confidence=llm_verdict["confidence"],
            matched_rule_id=None,
            latency_ms=latency_ms,
            ip_address=ip_address,
        )
    )

    return {
        "status": llm_verdict["status"],
        "fail_category": llm_verdict["fail_category"],
        "explanation": llm_verdict["explanation"],
        "confidence": llm_verdict["confidence"],
        "matched_rule": None,
    }


# ---------------------------------------------------------------------------
# 9. Cache Invalidation Helpers (§7.2)
# ---------------------------------------------------------------------------


async def invalidate_auth_cache(api_key_hash: str) -> None:
    """Delete the auth cache entry for a specific API key hash."""
    try:
        rd = await _get_redis()
        await rd.delete(f"firewall:auth:{api_key_hash}")
        await rd.aclose()
    except Exception:
        pass


async def invalidate_scope_cache(project_id: str | UUID) -> None:
    """Delete the scope cache for a project."""
    try:
        rd = await _get_redis()
        await rd.delete(f"firewall:scope:{project_id}")
        await rd.aclose()
    except Exception:
        pass


async def invalidate_rules_cache(project_id: str | UUID) -> None:
    """Delete the rules cache for a project."""
    try:
        rd = await _get_redis()
        await rd.delete(f"firewall:rules:{project_id}")
        await rd.aclose()
    except Exception:
        pass
