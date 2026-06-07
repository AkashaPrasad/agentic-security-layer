"""
Engine runner — Celery task entry point and orchestration loop.

Coordinates the full experiment pipeline:
  1. Load context
  2. Plan tests
  3. Generate prompts
  4. Execute against target in batches
  5. Judge each response
  6. Select representatives
  7. Compute analytics
  8. Finalise experiment
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.engine.context import (
    ExperimentContext,
    ProjectScope,
    ProviderInfo,
    TargetConfig,
)
from app.engine.executor import init_thread, send_prompt
from app.engine.generator import GeneratedPrompt, generate_prompts
from app.engine.judge import JudgeVerdict, evaluate as judge_evaluate
from app.engine.planner import create_test_plan
from app.engine.plugins import emit_plugin_hook, ensure_plugins_loaded
from app.engine.provider_pool import ProviderPool
from app.engine.sampler import select_representatives
from app.engine.scorer import compute_analytics, generate_insights
from app.services.encryption import decrypt_value
from app.services.llm_gateway import LLMGateway
from app.storage.database import create_standalone_session_factory
from app.storage.models.experiment import Experiment
from app.storage.models.project import Project
from app.storage.models.provider import ModelProvider
from app.storage.models.result import Result
from app.storage.models.test_case import TestCase

logger = logging.getLogger(__name__)

# Testing level → total test count
TESTING_LEVEL_COUNTS: dict[str, int] = {
    "50": 50,
    "100": 100,
    "200": 200,
    "300": 300,
    "400": 400,
    "basic": 500,
    "moderate": 1200,
    "aggressive": 2000,
}

# Engine settings
BATCH_SIZE = getattr(settings, "experiment_batch_size", 5)
ERROR_THRESHOLD_WINDOW = 50
ERROR_THRESHOLD_RATE = 0.60

# Per-provider inter-request delay (seconds).
# Groq's free tier enforces strict token-per-minute limits; the delay prevents
# 429 storms.  Paid OpenAI / Anthropic / Gemini tiers have generous rate limits
# and don't need throttling here — throughput is controlled by batch_concurrency.
# Set to 0.0 to disable; override per-provider via environment variable
# EXPERIMENT_INTER_REQUEST_DELAY_{PROVIDER_TYPE_UPPER}.
_PROVIDER_DELAYS: dict[str, float] = {
    "groq": 1.0,
    "openai": 0.0,
    "azure_openai": 0.0,
    "anthropic": 0.0,
    "gemini": 0.0,
    "ollama": 0.0,
    "openai_compatible": 0.0,
    "custom": 0.0,
}


def _inter_request_delay(provider_type: str) -> float:
    """Return the appropriate inter-request delay for the given provider."""
    # Allow per-provider overrides via env variables, e.g.
    # EXPERIMENT_INTER_REQUEST_DELAY_GROQ=0.5
    env_key = f"experiment_inter_request_delay_{provider_type.lower()}"
    env_val = getattr(settings, env_key, None)
    if env_val is not None:
        try:
            return float(env_val)
        except (TypeError, ValueError):
            pass
    return _PROVIDER_DELAYS.get(provider_type.lower(), 0.0)

# Strategy memory
STRATEGY_MEMORY_TTL_SECONDS = int(
    getattr(settings, "experiment_strategy_memory_ttl_seconds", 1_209_600)
)
STRATEGY_MEMORY_MAX_ITEMS = int(
    getattr(settings, "experiment_strategy_memory_max_items", 40)
)

# Estimated token pricing (USD per 1M tokens), used for internal cost controls.
_PRICE_PER_1M_TOKENS: dict[str, dict[str, tuple[float, float]]] = {
    "openai": {
        "gpt-4o": (5.0, 15.0),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4.1": (2.0, 8.0),
        "gpt-4.1-mini": (0.40, 1.60),
    },
    "azure_openai": {
        "gpt-4o": (5.0, 15.0),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4.1": (2.0, 8.0),
        "gpt-4.1-mini": (0.40, 1.60),
    },
    "groq": {
        "llama-3.3-70b-versatile": (0.59, 0.79),
    },
    "_default": {
        "_default": (1.00, 3.00),
    },
}


@dataclass
class _ProviderSpend:
    provider_type: str
    model: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class _CostLedger:
    budget_usd: float
    revenue_per_test_usd: float
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    provider_breakdown: dict[str, _ProviderSpend] = dataclasses.field(default_factory=dict)

    def register_usage_events(self, events: list[dict]) -> None:
        for event in events:
            if str(event.get("status", "")) != "success":
                continue

            provider_type = str(event.get("provider_type", "unknown"))
            model = str(event.get("model", "unknown"))
            input_tokens = int(event.get("input_tokens", 0) or 0)
            output_tokens = int(event.get("output_tokens", 0) or 0)
            cost = _estimate_llm_cost_usd(provider_type, model, input_tokens, output_tokens)

            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.estimated_cost_usd += cost

            key = f"{provider_type}:{model}"
            if key not in self.provider_breakdown:
                self.provider_breakdown[key] = _ProviderSpend(
                    provider_type=provider_type,
                    model=model,
                )
            item = self.provider_breakdown[key]
            item.calls += 1
            item.input_tokens += input_tokens
            item.output_tokens += output_tokens
            item.estimated_cost_usd += cost

    def over_budget(self) -> bool:
        if self.budget_usd <= 0:
            return False
        return self.estimated_cost_usd >= self.budget_usd

    def to_summary(self, completed_tests: int) -> dict:
        total_tokens = self.input_tokens + self.output_tokens
        budget_utilization = (
            self.estimated_cost_usd / self.budget_usd
            if self.budget_usd > 0
            else 0.0
        )
        estimated_revenue = max(0.0, completed_tests * self.revenue_per_test_usd)
        if estimated_revenue > 0:
            estimated_margin_pct = ((estimated_revenue - self.estimated_cost_usd) / estimated_revenue) * 100.0
        else:
            estimated_margin_pct = 0.0

        breakdown = [
            {
                "provider_type": item.provider_type,
                "model": item.model,
                "calls": item.calls,
                "input_tokens": item.input_tokens,
                "output_tokens": item.output_tokens,
                "total_tokens": item.input_tokens + item.output_tokens,
                "estimated_cost_usd": round(item.estimated_cost_usd, 6),
            }
            for item in sorted(
                self.provider_breakdown.values(),
                key=lambda value: value.estimated_cost_usd,
                reverse=True,
            )
        ]

        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "budget_usd": round(self.budget_usd, 2),
            "budget_utilization": round(budget_utilization, 4),
            "estimated_revenue_usd": round(estimated_revenue, 6),
            "estimated_margin_pct": round(estimated_margin_pct, 2),
            "provider_breakdown": breakdown,
        }


def _resolve_price(provider_type: str, model: str) -> tuple[float, float]:
    provider_prices = _PRICE_PER_1M_TOKENS.get(provider_type, _PRICE_PER_1M_TOKENS["_default"])
    if model in provider_prices:
        return provider_prices[model]
    for model_prefix, prices in provider_prices.items():
        if model_prefix != "_default" and model.startswith(model_prefix):
            return prices
    return provider_prices.get("_default", _PRICE_PER_1M_TOKENS["_default"]["_default"])


def _estimate_llm_cost_usd(
    provider_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    input_rate, output_rate = _resolve_price(provider_type, model)
    input_cost = (max(0, input_tokens) / 1_000_000.0) * input_rate
    output_cost = (max(0, output_tokens) / 1_000_000.0) * output_rate
    return input_cost + output_cost


def _drain_gateway_usage(gateway: object) -> list[dict]:
    if hasattr(gateway, "consume_usage_events"):
        try:
            return gateway.consume_usage_events()  # type: ignore[attr-defined]
        except Exception:
            return []
    return []


def _to_storage_safe_text(text: str | None) -> str | None:
    """Return text that can be stored in WIN1252-backed PostgreSQL.

    On Windows clusters initialized with a WIN1252 locale, some Unicode
    codepoints (e.g., U+2060 word-joiner) are not representable and can
    crash inserts. We preserve content by backslash-escaping only the
    unsupported codepoints.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)
    try:
        text.encode("cp1252")
        return text
    except UnicodeEncodeError:
        return text.encode("cp1252", errors="backslashreplace").decode("cp1252")


def _to_storage_safe_json(value: object) -> object:
    """Recursively sanitize JSON-like payloads for DB storage."""
    if isinstance(value, str):
        return _to_storage_safe_text(value)
    if isinstance(value, list):
        return [_to_storage_safe_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_storage_safe_json(item) for key, item in value.items()}
    return value


def _prompt_signature(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    if not normalized:
        return ""
    return " ".join(normalized.split(" ")[:14])


def _trim_unique(items: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    trimmed: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        trimmed.append(normalized)
        if len(trimmed) >= limit:
            break
    return trimmed


def _default_strategy_memory() -> dict:
    return {
        "effective_prompts": [],
        "blocked_prompts": [],
        "effective_signatures": [],
        "blocked_signatures": [],
    }


def _merge_strategy_memory(raw: dict | None) -> dict:
    merged = _default_strategy_memory()
    if not isinstance(raw, dict):
        return merged
    for key in merged.keys():
        values = raw.get(key, [])
        if isinstance(values, list):
            merged[key] = _trim_unique([str(v) for v in values], STRATEGY_MEMORY_MAX_ITEMS)
    return merged


def _update_strategy_memory(memory: dict, prompt: str, verdict_status: str) -> None:
    signature = _prompt_signature(prompt)
    if not signature:
        return

    if verdict_status == "fail":
        memory["effective_prompts"] = _trim_unique(
            [prompt] + list(memory.get("effective_prompts", [])),
            STRATEGY_MEMORY_MAX_ITEMS,
        )
        memory["effective_signatures"] = _trim_unique(
            [signature] + list(memory.get("effective_signatures", [])),
            STRATEGY_MEMORY_MAX_ITEMS,
        )
    elif verdict_status == "pass":
        memory["blocked_prompts"] = _trim_unique(
            [prompt] + list(memory.get("blocked_prompts", [])),
            STRATEGY_MEMORY_MAX_ITEMS,
        )
        memory["blocked_signatures"] = _trim_unique(
            [signature] + list(memory.get("blocked_signatures", [])),
            STRATEGY_MEMORY_MAX_ITEMS,
        )


def _strategy_memory_key(project_id: UUID, category: str) -> str:
    return f"strategy:memory:{project_id}:{category}"


async def _load_strategy_memory(project_id: UUID, category: str) -> dict:
    rd = await _get_redis()
    if not rd:
        return _default_strategy_memory()
    try:
        raw = await rd.get(_strategy_memory_key(project_id, category))
        if not raw:
            return _default_strategy_memory()
        return _merge_strategy_memory(json.loads(raw))
    except Exception:
        return _default_strategy_memory()
    finally:
        try:
            await rd.aclose()
        except Exception:
            pass


async def _persist_strategy_memory(project_id: UUID, category: str, memory: dict) -> None:
    rd = await _get_redis()
    if not rd:
        return
    try:
        payload = json.dumps(_merge_strategy_memory(memory))
        await rd.set(
            _strategy_memory_key(project_id, category),
            payload,
            ex=STRATEGY_MEMORY_TTL_SECONDS,
        )
    except Exception:
        pass
    finally:
        try:
            await rd.aclose()
        except Exception:
            pass


async def _persist_all_strategy_memory(project_id: UUID, by_category: dict[str, dict]) -> None:
    for category, memory in by_category.items():
        await _persist_strategy_memory(project_id, category, memory)


async def _load_retry_error_prompts(
    session: AsyncSession,
    source_experiment_id: UUID,
) -> list[GeneratedPrompt]:
    """Load failed/error prompts from a previous experiment for targeted retries."""
    rows = (
        await session.execute(
            select(TestCase, Result)
            .join(Result, Result.test_case_id == TestCase.id)
            .where(
                TestCase.experiment_id == source_experiment_id,
                Result.result.in_(["fail", "error"]),
            )
            .order_by(TestCase.sequence_order.asc(), TestCase.created_at.asc())
        )
    ).all()

    prompts: list[GeneratedPrompt] = []
    for idx, (tc, res) in enumerate(rows):
        prompts.append(
            GeneratedPrompt(
                prompt_text=tc.prompt,
                template_id=f"retry_error_{idx:04d}",
                prompt_id=f"retry_error_{idx:04d}",
                risk_category=tc.risk_category or "unknown",
                owasp_id=res.owasp_mapping,
                data_strategy="retry_errors",
                converter_applied=tc.attack_converter,
                sequence_order=idx,
                tags=["retry_errors"],
            )
        )

    return prompts


# ---------------------------------------------------------------------------
# Context loader
# ---------------------------------------------------------------------------


async def _load_context(
    experiment_id: UUID,
    session: AsyncSession,
) -> ExperimentContext:
    """Load experiment, project, and provider from DB; build context."""
    stmt = select(Experiment).where(Experiment.id == experiment_id)
    result = await session.execute(stmt)
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise ValueError(f"Experiment {experiment_id} not found")

    proj_stmt = select(Project).where(Project.id == experiment.project_id)
    project = (await session.execute(proj_stmt)).scalar_one_or_none()
    if not project:
        raise ValueError(f"Project {experiment.project_id} not found")

    prov_stmt = select(ModelProvider).where(ModelProvider.id == experiment.provider_id)
    provider = (await session.execute(prov_stmt)).scalar_one_or_none()
    if not provider:
        raise ValueError(f"Provider {experiment.provider_id} not found")

    # Parse target config
    tc_raw: dict = experiment.target_config or {}
    target = TargetConfig(
        endpoint_url=tc_raw.get("endpoint_url", ""),
        method=tc_raw.get("method", "POST"),
        headers=tc_raw.get("headers", {}),
        payload_template=tc_raw.get("payload_template", '{"prompt": "{{prompt}}"}'),
        response_json_path=tc_raw.get("response_json_path", "$.response"),
        auth_type=tc_raw.get("auth_type"),
        auth_value=tc_raw.get("auth_value"),
        timeout_seconds=tc_raw.get("timeout_seconds", 30),
        thread_endpoint_url=tc_raw.get("thread_endpoint_url"),
        thread_id_path=tc_raw.get("thread_id_path"),
        system_prompt=tc_raw.get("system_prompt"),
        experiment_batch_concurrency=tc_raw.get("experiment_batch_concurrency"),
        random_seed=tc_raw.get("random_seed"),
        retry_source_experiment_id=tc_raw.get("retry_source_experiment_id"),
        retry_mode=tc_raw.get("retry_mode"),
        strategy_mode=tc_raw.get("strategy_mode"),
        attack_pipeline=tc_raw.get("attack_pipeline"),
    )

    # Decrypt auth value if present
    if target.auth_value:
        try:
            target.auth_value = decrypt_value(target.auth_value)
        except Exception:
            pass  # May already be plaintext

    scope = ProjectScope(
        project_id=project.id,
        project_name=project.name,
        business_scope=project.business_scope or "",
        allowed_intents=project.allowed_intents or [],
        restricted_intents=project.restricted_intents or [],
        analyzed_scope=project.analyzed_scope,
    )

    prov_info = ProviderInfo(
        provider_id=provider.id,
        provider_type=provider.provider_type,
        api_key=decrypt_value(provider.encrypted_api_key),
        endpoint_url=provider.endpoint_url,
    )

    total_tests = TESTING_LEVEL_COUNTS.get(experiment.testing_level, 500)

    return ExperimentContext(
        experiment_id=experiment.id,
        experiment_type=experiment.experiment_type,
        sub_type=experiment.sub_type,
        turn_mode=experiment.turn_mode or "single_turn",
        testing_level=experiment.testing_level,
        language=experiment.language or "en",
        total_tests=total_tests,
        target=target,
        scope=scope,
        provider=prov_info,
        created_by_id=experiment.created_by_id,
        plugins=experiment.target_config.get("plugins") or None,
    )


# ---------------------------------------------------------------------------
# Redis progress helpers
# ---------------------------------------------------------------------------


async def _get_redis() -> aioredis.Redis | None:
    try:
        return aioredis.Redis.from_url(
            str(settings.redis_connection_url),
            decode_responses=True,
        )
    except Exception:
        return None


async def _update_progress(
    experiment_id: UUID,
    completed: int,
    total: int,
):
    rd = await _get_redis()
    if rd:
        try:
            key = f"experiment:{experiment_id}:progress"
            await rd.set(key, f"{completed}/{total}", ex=86400)
            await rd.aclose()
        except Exception:
            pass


async def _check_cancelled(experiment_id: UUID) -> bool:
    rd = await _get_redis()
    if rd:
        try:
            flag = await rd.get(f"experiment:{experiment_id}:cancel")
            await rd.aclose()
            return flag is not None
        except Exception:
            pass
    return False


# ---------------------------------------------------------------------------
# Main execution pipeline
# ---------------------------------------------------------------------------


async def run_experiment_async(experiment_id: UUID) -> None:
    """Full async experiment execution pipeline."""
    start_time = time.monotonic()
    ensure_plugins_loaded()

    # Create a standalone engine + session factory for this event loop.
    # The global AsyncSessionLocal is bound to the *main* web-server loop;
    # using it from a background thread causes "Future attached to a
    # different loop".
    _engine, _SessionFactory = create_standalone_session_factory()

    try:
        async with _SessionFactory() as session:
            # --- 1. LOAD CONTEXT ---
            try:
                ctx = await _load_context(experiment_id, session)
                seed = ctx.target.random_seed
                if seed is None:
                    seed = int(getattr(settings, "experiment_default_seed", 1337))
                random.seed(seed)
            except Exception as e:
                logger.error("Failed to load experiment context: %s", e)
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status="failed",
                        error_message=str(e),
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
                return

            # Set status -> running
            await session.execute(
                update(Experiment)
                .where(Experiment.id == experiment_id)
                .values(
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    progress_total=ctx.total_tests,
                    progress_completed=0,
                    status_message="validating_provider",
                )
            )
            await session.commit()
            await _update_progress(experiment_id, 0, ctx.total_tests)
            emit_plugin_hook(
                "before_experiment",
                {
                    "experiment_id": str(experiment_id),
                    "experiment_type": ctx.experiment_type,
                    "sub_type": ctx.sub_type,
                    "testing_level": ctx.testing_level,
                },
            )

            # Build LLM gateway(s) — primary + backup key (if configured) +
            # all other valid providers owned by the same user, enabling
            # automatic rate-limit failover.
            primary_gw = LLMGateway(
                provider_type=ctx.provider.provider_type,
                api_key=ctx.provider.api_key,
                endpoint_url=ctx.provider.endpoint_url,
            )

            all_gateways = [primary_gw]

            # Add backup key as secondary gateway if configured
            try:
                primary_prov = (
                    await session.execute(
                        select(ModelProvider).where(ModelProvider.id == ctx.provider.provider_id)
                    )
                ).scalar_one_or_none()
                if primary_prov and primary_prov.use_backup_key and primary_prov.backup_api_key_enc:
                    try:
                        backup_key = decrypt_value(primary_prov.backup_api_key_enc)
                        backup_gw = LLMGateway(
                            provider_type=primary_prov.provider_type,
                            api_key=backup_key,
                            endpoint_url=primary_prov.backup_endpoint or primary_prov.endpoint_url,
                            model=primary_prov.backup_model or primary_prov.model,
                        )
                        all_gateways.append(backup_gw)
                        logger.info(
                            "Backup key gateway added for experiment %s (provider %s)",
                            experiment_id,
                            ctx.provider.provider_id,
                        )
                    except Exception:
                        logger.debug("Could not load backup key for provider %s", ctx.provider.provider_id)
            except Exception:
                logger.debug("Could not check backup key for provider (non-fatal)")

            # Get per-provider rate limits from the primary provider config
            provider_rpm: int | None = None
            provider_tpm: int | None = None
            try:
                if primary_prov and primary_prov.requests_per_minute:
                    provider_rpm = primary_prov.requests_per_minute
                if primary_prov and primary_prov.tokens_per_minute:
                    provider_tpm = primary_prov.tokens_per_minute
            except Exception:
                pass

            try:
                other_provs = (
                    await session.execute(
                        select(ModelProvider).where(
                            ModelProvider.owner_id == ctx.created_by_id,
                            ModelProvider.is_valid.is_(True),
                            ModelProvider.id != ctx.provider.provider_id,
                        )
                    )
                ).scalars().all()
                for prov in other_provs:
                    try:
                        gw = LLMGateway(
                            provider_type=prov.provider_type,
                            encrypted_api_key=prov.encrypted_api_key,
                            endpoint_url=prov.endpoint_url,
                        )
                        all_gateways.append(gw)
                    except Exception:
                        pass
            except Exception:
                logger.debug("Could not load fallback providers (non-fatal)")

            gateway = ProviderPool(
                all_gateways,
                requests_per_minute=provider_rpm,
                tokens_per_minute=provider_tpm,
            )
            if gateway.provider_count > 1:
                logger.info(
                    "ProviderPool initialised with %d providers for experiment %s",
                    gateway.provider_count,
                    experiment_id,
                )

            cost_ledger = _CostLedger(
                budget_usd=max(0.0, float(getattr(settings, "experiment_cost_budget_usd", 0.0))),
                revenue_per_test_usd=max(0.0, float(getattr(settings, "experiment_revenue_per_test_usd", 0.0))),
            )
            strategy_memory_by_category: dict[str, dict] = {}

            # Validate provider credentials
            try:
                is_valid, val_error = await gateway.validate_credentials()
                if not is_valid:
                    raise ValueError(val_error or "Provider credentials invalid")
                cost_ledger.register_usage_events(_drain_gateway_usage(gateway))
            except Exception as e:
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status="failed",
                        error_message=_to_storage_safe_text(f"Provider validation failed: {e}"),
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
                return

            # --- 2. PLAN ---
            await session.execute(
                update(Experiment)
                .where(Experiment.id == experiment_id)
                .values(status_message="generating_prompts")
            )
            await session.commit()
            try:
                plan = create_test_plan(ctx)
                emit_plugin_hook(
                    "before_generation",
                    {
                        "experiment_id": str(experiment_id),
                        "task_count": len(plan.tasks),
                        "total_budget": plan.total_budget,
                    },
                )
            except Exception as e:
                logger.exception("Test plan creation failed for %s", experiment_id)
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status="failed",
                        error_message=_to_storage_safe_text(f"Test plan creation failed: {e}"),
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
                return

            # --- 3. GENERATE ---
            all_prompts: list[GeneratedPrompt] = []
            seq = 0
            strategy_failure_count = 0
            judge_error_count = 0
            try:
                retry_source_id = ctx.target.retry_source_experiment_id
                retry_mode = (ctx.target.retry_mode or "").lower()
                if retry_source_id and retry_mode == "errors_only":
                    retry_source_uuid = UUID(str(retry_source_id))
                    all_prompts = await _load_retry_error_prompts(session, retry_source_uuid)
                    seq = len(all_prompts)
                    logger.info(
                        "Experiment %s running in retry_errors mode with %d prompts from %s",
                        experiment_id,
                        len(all_prompts),
                        retry_source_uuid,
                    )
                    if not all_prompts:
                        raise RuntimeError("Retry-errors mode found no failed/error prompts to run")
                else:
                    for task in plan.tasks:
                        task_memory = await _load_strategy_memory(ctx.scope.project_id, task.category)
                        strategy_memory_by_category[task.category] = task_memory

                        converters = None
                        if plan.converters_enabled:
                            from app.engine.converters import get_all_converters
                            converters = get_all_converters()

                        prompts = await generate_prompts(
                            task=task,
                            ctx=ctx,
                            gateway=gateway,
                            converters=converters,
                            converter_probability=plan.converter_probability,
                            max_converter_chain=plan.max_converter_chain,
                            augmentation_variants=plan.llm_augmentation_variants,
                            start_sequence=seq,
                            strategy_memory=task_memory,
                        )
                        cost_ledger.register_usage_events(_drain_gateway_usage(gateway))
                        if cost_ledger.over_budget():
                            raise RuntimeError(
                                "Cost budget exceeded during prompt generation: "
                                f"${cost_ledger.estimated_cost_usd:.2f} >= ${cost_ledger.budget_usd:.2f}"
                            )
                        all_prompts.extend(prompts)
                        seq += len(prompts)

                plugin_generation_ctx = emit_plugin_hook(
                    "after_generation",
                    {
                        "experiment_id": str(experiment_id),
                        "prompt_count": len(all_prompts),
                    },
                )
                plugin_prompt_count = plugin_generation_ctx.get("prompt_count")
                if isinstance(plugin_prompt_count, int) and plugin_prompt_count >= 0:
                    all_prompts = all_prompts[:plugin_prompt_count]
            except Exception as e:
                logger.exception("Prompt generation failed for %s", experiment_id)
                if "strategy" in str(e).lower():
                    strategy_failure_count += 1
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status="failed",
                        error_message=_to_storage_safe_text(f"Prompt generation failed: {e}"),
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
                return

            # Update total if generation produced different count
            actual_total = len(all_prompts)
            await session.execute(
                update(Experiment)
                .where(Experiment.id == experiment_id)
                .values(progress_total=actual_total, status_message="executing_prompts")
            )
            await session.commit()

            # --- 4. EXECUTE LOOP ---
            completed = 0
            result_records: list[dict] = []
            recent_window: list[bool] = []
            failure_reason: str | None = None
            rate_limit_hit_count: int = 0

            try:
                for batch_start in range(0, actual_total, BATCH_SIZE):
                    if cost_ledger.over_budget():
                        failure_reason = (
                            "Cost budget exceeded: "
                            f"${cost_ledger.estimated_cost_usd:.2f} >= ${cost_ledger.budget_usd:.2f}"
                        )
                        break

                    if await _check_cancelled(experiment_id):
                        await session.execute(
                            update(Experiment)
                            .where(Experiment.id == experiment_id)
                            .values(
                                status="cancelled",
                                completed_at=datetime.now(timezone.utc),
                                progress_completed=completed,
                            )
                        )
                        await session.commit()
                        logger.info("Experiment %s cancelled", experiment_id)
                        failure_reason = "Experiment cancelled by user"
                        break

                    batch = all_prompts[batch_start : batch_start + BATCH_SIZE]
                    configured_batch_concurrency = (
                        ctx.target.experiment_batch_concurrency
                        if ctx.target.experiment_batch_concurrency is not None
                        else getattr(settings, "experiment_batch_concurrency", 3)
                    )
                    batch_concurrency = max(1, int(configured_batch_concurrency))
                    semaphore = asyncio.Semaphore(batch_concurrency)

                    async def _run_prompt(gp: GeneratedPrompt) -> dict:
                        async with semaphore:
                            try:
                                await asyncio.sleep(_inter_request_delay(ctx.provider.provider_type))

                                plugin_before = emit_plugin_hook(
                                    "before_each_prompt",
                                    {
                                        "experiment_id": str(experiment_id),
                                        "prompt": gp.prompt_text,
                                        "risk_category": gp.risk_category,
                                    },
                                )
                                executed_prompt = gp.prompt_text
                                plugin_prompt = plugin_before.get("prompt")
                                if isinstance(plugin_prompt, str) and plugin_prompt.strip():
                                    executed_prompt = plugin_prompt

                                if gp.conversation_plan and ctx.turn_mode == "multi_turn":
                                    response_text, latency_ms, conversation = await _execute_multi_turn(
                                        ctx,
                                        gp,
                                        gateway,
                                    )
                                else:
                                    response_text, latency_ms = await send_prompt(
                                        ctx.target,
                                        executed_prompt,
                                        gateway=gateway,
                                    )
                                    conversation = None

                                await asyncio.sleep(_inter_request_delay(ctx.provider.provider_type))
                                verdict = await judge_evaluate(
                                    ctx=ctx,
                                    gateway=gateway,
                                    test_prompt=executed_prompt,
                                    ai_response=response_text or "",
                                    risk_category=gp.risk_category,
                                    expected_behaviour=gp.expected_behaviour,
                                    conversation=conversation,
                                )

                                return {
                                    "gp": gp,
                                    "executed_prompt": executed_prompt,
                                    "response_text": response_text,
                                    "latency_ms": latency_ms,
                                    "conversation": conversation,
                                    "is_rate_limit": False,
                                    "verdict": verdict,
                                }
                            except Exception as exc:
                                exc_msg = str(exc).lower()
                                is_rate_limit = any(
                                    kw in exc_msg for kw in (
                                        "429", "rate", "too many", "quota", "limit exceeded",
                                        "retry-after", "rate_limit", "ratelimit",
                                    )
                                )
                                return {
                                    "gp": gp,
                                    "executed_prompt": gp.prompt_text,
                                    "response_text": None,
                                    "latency_ms": 0,
                                    "conversation": None,
                                    "is_rate_limit": is_rate_limit,
                                    "verdict": JudgeVerdict(
                                        status="error",
                                        risk_category=gp.risk_category,
                                        explanation=f"Batch worker error: {exc}",
                                        confidence=0.0,
                                    ),
                                }

                    batch_outputs = await asyncio.gather(*[_run_prompt(gp) for gp in batch])

                    for output in batch_outputs:
                        gp = output["gp"]
                        executed_prompt = output["executed_prompt"]
                        response_text = output["response_text"]
                        latency_ms = output["latency_ms"]
                        conversation = output["conversation"]
                        verdict: JudgeVerdict = output["verdict"]

                        if output.get("is_rate_limit"):
                            rate_limit_hit_count += 1
                        if verdict.status == "error":
                            judge_error_count += 1

                        safe_prompt = _to_storage_safe_text(executed_prompt) or ""
                        safe_response = _to_storage_safe_text(response_text)
                        safe_conversation = _to_storage_safe_json(conversation)
                        safe_explanation = _to_storage_safe_text(verdict.explanation) or ""

                        tc = TestCase(
                            experiment_id=experiment_id,
                            prompt=safe_prompt,
                            response=safe_response,
                            conversation=safe_conversation,
                            risk_category=gp.risk_category,
                            data_strategy=gp.data_strategy,
                            attack_converter=gp.converter_applied,
                            sequence_order=gp.sequence_order,
                            is_representative=False,
                            latency_ms=latency_ms,
                        )
                        session.add(tc)
                        await session.flush()

                        res = Result(
                            test_case_id=tc.id,
                            result=verdict.status,
                            severity=verdict.severity,
                            confidence=verdict.confidence,
                            explanation=safe_explanation,
                            owasp_mapping=gp.owasp_id,
                        )
                        session.add(res)

                        category_memory = strategy_memory_by_category.setdefault(
                            gp.risk_category,
                            _default_strategy_memory(),
                        )
                        _update_strategy_memory(category_memory, executed_prompt, verdict.status)

                        cost_ledger.register_usage_events(_drain_gateway_usage(gateway))
                        if cost_ledger.over_budget():
                            failure_reason = (
                                "Cost budget exceeded: "
                                f"${cost_ledger.estimated_cost_usd:.2f} >= ${cost_ledger.budget_usd:.2f}"
                            )
                            break

                        result_records.append(
                            {
                                "id": tc.id,
                                "status": verdict.status,
                                "severity": verdict.severity,
                                "risk_category": gp.risk_category,
                                "owasp_mapping": gp.owasp_id,
                                "confidence": verdict.confidence,
                                "latency_ms": latency_ms,
                            }
                        )

                        emit_plugin_hook(
                            "after_each_prompt",
                            {
                                "experiment_id": str(experiment_id),
                                "prompt": executed_prompt,
                                "risk_category": gp.risk_category,
                                "response": response_text or "",
                                "verdict": verdict.status,
                            },
                        )

                        completed += 1

                        is_error = response_text is None or verdict.status == "error"
                        recent_window.append(is_error)
                        if len(recent_window) > ERROR_THRESHOLD_WINDOW:
                            recent_window.pop(0)
                        if len(recent_window) >= ERROR_THRESHOLD_WINDOW:
                            err_rate = sum(recent_window) / len(recent_window)
                            if err_rate > ERROR_THRESHOLD_RATE:
                                if rate_limit_hit_count > 0:
                                    failure_reason = (
                                        f"Rate limit reached after {completed} tests. "
                                        f"Showing partial results ({completed} of {actual_total} completed)."
                                    )
                                else:
                                    failure_reason = (
                                        f"Error threshold exceeded: {err_rate:.0%} errors "
                                        f"in last {ERROR_THRESHOLD_WINDOW} tests"
                                    )
                                break

                    if failure_reason:
                        break

                    await session.commit()
                    await _update_progress(experiment_id, completed, actual_total)
                    _live_msg = f"Executing tests: {completed}/{actual_total} completed"
                    await session.execute(
                        update(Experiment)
                        .where(Experiment.id == experiment_id)
                        .values(
                            progress_completed=completed,
                            status_message=_live_msg,
                        )
                    )
                    await session.commit()
                    await _persist_all_strategy_memory(ctx.scope.project_id, strategy_memory_by_category)

            except Exception as e:
                logger.exception(
                    "Experiment %s execution failed at test %d: %s",
                    experiment_id,
                    completed,
                    e,
                )
                failure_reason = _to_storage_safe_text(
                    f"Execution failed after {completed} tests: {e}"
                ) or "Execution failed"
                try:
                    await session.rollback()
                except Exception:
                    pass

            cost_ledger.register_usage_events(_drain_gateway_usage(gateway))
            await _persist_all_strategy_memory(ctx.scope.project_id, strategy_memory_by_category)

            if not failure_reason:
                try:
                    await session.commit()
                except Exception:
                    pass

            # --- 5. SAMPLE representatives ---
            rep_ids = select_representatives(result_records, ctx.testing_level)
            if rep_ids:
                await session.execute(
                    update(TestCase)
                    .where(TestCase.id.in_(rep_ids))
                    .values(is_representative=True)
                )
                await session.commit()

            # --- 6. SCORE ---
            duration = int(time.monotonic() - start_time)
            cost_summary = cost_ledger.to_summary(completed_tests=completed)
            analytics = (
                compute_analytics(
                    result_records,
                    duration,
                    cost_summary=cost_summary,
                )
                if result_records
                else None
            )

            if analytics:
                if not failure_reason or completed >= 10:
                    try:
                        insight_items = await generate_insights(analytics, ctx, gateway)
                        cost_ledger.register_usage_events(_drain_gateway_usage(gateway))
                        analytics.cost_summary = cost_ledger.to_summary(completed_tests=completed)
                        analytics.insights = {
                            "summary": insight_items[0].description if insight_items else "",
                            "key_findings": [i.title for i in insight_items],
                            "risk_assessment": analytics.fail_impact,
                            "recommendations": [i.recommendation for i in insight_items],
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    except Exception:
                        pass

                analytics_dict = dataclasses.asdict(analytics)
                analytics_dict["reliability_diagnostics"] = {
                    "judge_errors": judge_error_count,
                    "strategy_failures": strategy_failure_count,
                    "judge_fallback_enabled": bool(getattr(settings, "judge_fallback_enabled", True)),
                    "strategy_mode": ctx.target.strategy_mode or "independent",
                    "attack_pipeline": list(ctx.target.attack_pipeline or []),
                    "random_seed": ctx.target.random_seed,
                }
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(analytics=_to_storage_safe_json(analytics_dict))
                )
                await session.commit()

            # --- 7. FINALISE ---
            if failure_reason:
                final_status = "cancelled" if "cancelled" in failure_reason.lower() else "failed"
                # For rate-limit failures with partial results, use an informative status_message
                is_rate_limit_failure = rate_limit_hit_count > 0 and "rate limit" in failure_reason.lower()
                if is_rate_limit_failure and completed > 0:
                    final_status_message = (
                        f"Rate limit reached. Showing partial results "
                        f"({completed} of {actual_total} test cases completed)."
                    )
                else:
                    final_status_message = f"failed: {failure_reason[:200]}"
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status=final_status,
                        error_message=failure_reason,
                        status_message=final_status_message,
                        completed_at=datetime.now(timezone.utc),
                        progress_completed=completed,
                    )
                )
                await session.commit()
                logger.warning(
                    "Experiment %s %s after %d tests: %s",
                    experiment_id,
                    final_status,
                    completed,
                    failure_reason,
                )
                emit_plugin_hook(
                    "after_experiment",
                    {
                        "experiment_id": str(experiment_id),
                        "status": final_status,
                        "completed": completed,
                        "failure_reason": failure_reason,
                    },
                )
            else:
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status="completed",
                        status_message="finalizing",
                        completed_at=datetime.now(timezone.utc),
                        progress_completed=completed,
                    )
                )
                await session.commit()
                logger.info(
                    "Experiment %s completed: %d tests, TPI=%.1f",
                    experiment_id,
                    completed,
                    analytics.tpi_score if analytics else 0,
                )
                emit_plugin_hook(
                    "after_experiment",
                    {
                        "experiment_id": str(experiment_id),
                        "status": "completed",
                        "completed": completed,
                        "failure_reason": None,
                    },
                )

            rd = await _get_redis()
            if rd:
                try:
                    await rd.delete(f"experiment:{experiment_id}:progress")
                    await rd.delete(f"experiment:{experiment_id}:cancel")
                    await rd.aclose()
                except Exception:
                    pass
    finally:
        # Dispose the standalone engine to release all connections
        await _engine.dispose()


# ---------------------------------------------------------------------------
# Multi-turn execution (with closed-loop adaptive rewriting)
# ---------------------------------------------------------------------------


async def _execute_multi_turn(
    ctx: ExperimentContext,
    gp: GeneratedPrompt,
    gateway: LLMGateway,
) -> tuple[str | None, int, list[dict]]:
    """
    Execute a multi-turn conversation with closed-loop adaptive rewriting.

    For turns marked as ``adaptive``, the attacker LLM rewrites the planned
    message based on the target's actual response (closed-loop feedback).
    This makes attacks significantly more effective than pre-planned scripts.

    Returns (last_response, total_latency, conversation).
    """
    from app.engine.strategies.adaptive import AdaptiveStrategy

    conversation: list[dict] = []
    total_latency = 0
    last_response = None

    # Init thread if needed
    thread_id = None
    if ctx.target.thread_endpoint_url:
        thread_id = await init_thread(ctx.target)

    # Build turn plan
    if gp.conversation_plan:
        turns = gp.conversation_plan
    else:
        # Fall back to single-turn
        turns = [{"text": gp.prompt_text, "content": gp.prompt_text, "adaptive": False}]

    # Extract strategy and restricted intent for adaptive rewriting
    strategy = turns[0].get("strategy", "crescendo") if turns else "crescendo"
    restricted_intent = gp.prompt_text  # The final goal

    for i, turn in enumerate(turns):
        turn_text = turn.get("text", turn.get("content", ""))
        is_adaptive = turn.get("adaptive", False)

        # Closed-loop: rewrite adaptive turns based on target's actual response
        if is_adaptive and last_response and len(conversation) >= 2:
            await asyncio.sleep(_inter_request_delay(ctx.provider.provider_type))
            turn_text = await AdaptiveStrategy.rewrite_turn_from_response(
                gateway=gateway,
                ctx=ctx,
                original_turn_text=turn_text,
                target_response=last_response,
                conversation_so_far=conversation,
                strategy=strategy,
                turn_number=i + 1,
                restricted_intent=restricted_intent,
            )

        conversation.append({"role": "user", "content": turn_text})

        # Send to target
        response_text, latency = await send_prompt(
            ctx.target,
            turn_text,
            thread_id=thread_id,
            gateway=gateway,
        )
        total_latency += latency
        ai_text = response_text or ""
        conversation.append({"role": "assistant", "content": ai_text})
        last_response = ai_text

        # Rate-limit delay between turns
        if i < len(turns) - 1:
            await asyncio.sleep(_inter_request_delay(ctx.provider.provider_type))

    return last_response, total_latency, conversation


# ---------------------------------------------------------------------------
# Sync entry point for Celery
# ---------------------------------------------------------------------------


def run_experiment(experiment_id: UUID) -> None:
    """Synchronous wrapper for Celery tasks."""
    asyncio.run(run_experiment_async(experiment_id))
