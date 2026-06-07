"""
ProviderPool — multi-provider gateway with automatic rate-limit failover.

Wraps multiple ``LLMGateway`` instances and presents the same public API
(``chat``, ``validate_credentials``, plus the properties callers rely on).
When the active provider returns a rate-limit error (HTTP 429 / "rate" /
"too many requests"), the pool marks it on cooldown and transparently
switches to the next available provider.

Usage in the experiment runner:
    pool = ProviderPool(gateways=[gw_primary, gw_secondary, ...])
    result = await pool.chat(messages)          # failover is automatic
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis

from app.config import settings
from app.services.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)

# How long (seconds) a provider stays on cooldown after a rate-limit hit.
DEFAULT_COOLDOWN_SECONDS = 60


@dataclass
class _TokenBucket:
    """Simple token bucket used for request and token quotas."""

    capacity: float
    refill_per_second: float
    tokens: float
    last_refill: float

    @classmethod
    def create(cls, capacity: float, refill_per_second: float) -> "_TokenBucket":
        now = time.monotonic()
        return cls(
            capacity=capacity,
            refill_per_second=refill_per_second,
            tokens=capacity,
            last_refill=now,
        )

    def refill(self) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - self.last_refill)
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_per_second))
        self.last_refill = now

    def seconds_until(self, amount: float) -> float:
        self.refill()
        deficit = max(0.0, amount - self.tokens)
        if deficit <= 0:
            return 0.0
        if self.refill_per_second <= 0:
            return 0.5
        return deficit / self.refill_per_second


@dataclass
class _ProviderQuotaState:
    request_bucket: _TokenBucket
    token_bucket: _TokenBucket


class ProviderPool:
    """Drop-in replacement for ``LLMGateway`` that tries multiple providers."""

    def __init__(
        self,
        gateways: list[LLMGateway],
        *,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        requests_per_minute: int | None = None,
        tokens_per_minute: int | None = None,
        max_rate_limit_retries: int | None = None,
        base_retry_delay_seconds: float | None = None,
        max_retry_delay_seconds: float | None = None,
    ) -> None:
        if not gateways:
            raise ValueError("ProviderPool requires at least one gateway")
        self._gateways = gateways
        self._current: int = 0
        # index → monotonic timestamp when cooldown expires
        self._cooldown_until: dict[int, float] = {}
        self._cooldown_seconds = cooldown_seconds

        rpm = max(1, int(requests_per_minute or getattr(settings, "provider_pool_requests_per_minute", 60)))
        tpm = max(100, int(tokens_per_minute or getattr(settings, "provider_pool_tokens_per_minute", 120000)))
        self._max_rate_limit_retries = max(
            0,
            int(max_rate_limit_retries if max_rate_limit_retries is not None else getattr(settings, "provider_pool_max_rate_limit_retries", 2)),
        )
        self._base_retry_delay_seconds = max(
            0.05,
            float(base_retry_delay_seconds if base_retry_delay_seconds is not None else getattr(settings, "provider_pool_base_retry_delay_seconds", 0.5)),
        )
        self._max_retry_delay_seconds = max(
            self._base_retry_delay_seconds,
            float(max_retry_delay_seconds if max_retry_delay_seconds is not None else getattr(settings, "provider_pool_max_retry_delay_seconds", 20.0)),
        )

        req_refill = float(rpm) / 60.0
        tok_refill = float(tpm) / 60.0
        self._quota_state: list[_ProviderQuotaState] = [
            _ProviderQuotaState(
                request_bucket=_TokenBucket.create(float(rpm), req_refill),
                token_bucket=_TokenBucket.create(float(tpm), tok_refill),
            )
            for _ in gateways
        ]

        # Buffered usage events for downstream cost accounting.
        self._usage_events: list[dict[str, Any]] = []

        # Deterministic response cache (inspired by promptfoo-style eval caching).
        self._cache_enabled = bool(getattr(settings, "provider_pool_cache_enabled", True))
        self._cache_ttl_seconds = max(30, int(getattr(settings, "provider_pool_cache_ttl_seconds", 1800)))
        self._cache_max_entries = max(100, int(getattr(settings, "provider_pool_cache_max_entries", 5000)))
        self._local_cache: dict[str, tuple[float, str]] = {}
        self._redis_cache_client: aioredis.Redis | None = None
        self._redis_cache_disabled = False

    # ------------------------------------------------------------------
    # Properties forwarded from the currently-active gateway
    # ------------------------------------------------------------------

    @property
    def _active(self) -> LLMGateway:
        return self._gateways[self._current]

    @property
    def provider_type(self) -> str:
        return self._active.provider_type

    @property
    def api_key(self) -> str:
        return self._active.api_key

    @property
    def endpoint_url(self) -> str | None:
        return self._active.endpoint_url

    @property
    def model(self) -> str:
        return self._active.model

    @property
    def provider_count(self) -> int:
        return len(self._gateways)

    # ------------------------------------------------------------------
    # Rate-limit detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Heuristic: does this exception look like a rate-limit response?"""
        msg = str(exc).lower()
        return any(kw in msg for kw in ("429", "rate", "too many", "quota", "limit exceeded", "retry-after", "rate_limit"))

    @staticmethod
    def _is_transient_provider_error(exc: Exception) -> bool:
        """Heuristic for provider outages/timeouts where failover should be attempted."""
        msg = str(exc).lower()
        transient_markers = (
            "500",
            "502",
            "503",
            "504",
            "gateway timeout",
            "service unavailable",
            "timeout",
            "temporarily unavailable",
            "connection reset",
            "connection refused",
            "upstream",
        )
        return any(marker in msg for marker in transient_markers)

    @staticmethod
    def _extract_retry_after_seconds(exc: Exception) -> float | None:
        """Best-effort extraction of server-provided retry-after delay."""
        for attr_name in ("retry_after", "retry_after_seconds"):
            value = getattr(exc, attr_name, None)
            if isinstance(value, (int, float)) and value >= 0:
                return float(value)

        response = getattr(exc, "response", None)
        if response is not None:
            try:
                header_value = response.headers.get("retry-after")
                if header_value:
                    return float(header_value)
            except Exception:
                pass

        match = re.search(r"retry[- ]after[: ]+([0-9]+(?:\.[0-9]+)?)", str(exc), flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except Exception:
                return None
        return None

    @classmethod
    def _estimate_tokens(
        cls,
        messages: list[dict[str, str]],
        max_tokens: int | None,
    ) -> tuple[int, int, int]:
        """Estimate (input, planned_output, reserved_total) tokens for quota usage."""
        input_chars = 0
        for message in messages:
            input_chars += len(message.get("role", ""))
            input_chars += len(message.get("content", ""))

        estimated_input = max(1, input_chars // 4)
        output_budget = max_tokens if max_tokens is not None else 256
        estimated_output = max(32, min(output_budget, 1024))
        reserved_total = estimated_input + estimated_output
        return estimated_input, estimated_output, reserved_total

    @staticmethod
    def _estimate_text_tokens(text: str | None) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _compute_retry_delay(self, attempt: int, exc: Exception) -> float:
        retry_after = self._extract_retry_after_seconds(exc)
        if retry_after is not None and retry_after > 0:
            jitter = random.uniform(0.0, min(1.0, retry_after * 0.1))
            return retry_after + jitter

        exponential = min(
            self._max_retry_delay_seconds,
            self._base_retry_delay_seconds * (2 ** attempt),
        )
        jitter = random.uniform(0.0, max(0.05, exponential * 0.25))
        return min(self._max_retry_delay_seconds, exponential + jitter)

    @staticmethod
    def _is_cacheable_request(
        temperature: float | None,
        response_format: dict | None,
    ) -> bool:
        """Cache only deterministic calls to avoid changing stochastic behavior."""
        if temperature is None or float(temperature) == 0.0:
            return True
        if response_format and response_format.get("type") == "json_object":
            return True
        return False

    @staticmethod
    def _cache_key(
        provider_type: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        response_format: dict | None,
    ) -> str:
        payload = {
            "provider_type": provider_type,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": response_format,
        }
        digest = hashlib.sha256(
            json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return f"llm:chat:cache:{provider_type}:{model}:{digest}"

    async def _get_redis_cache(self) -> aioredis.Redis | None:
        if self._redis_cache_disabled:
            return None
        if self._redis_cache_client is None:
            try:
                self._redis_cache_client = aioredis.from_url(
                    settings.redis_connection_url,
                    decode_responses=True,
                )
            except Exception:
                self._redis_cache_disabled = True
                return None
        return self._redis_cache_client

    async def _cache_get(self, key: str) -> str | None:
        now = time.monotonic()
        local = self._local_cache.get(key)
        if local and local[0] > now:
            return local[1]
        if local and local[0] <= now:
            self._local_cache.pop(key, None)

        rd = await self._get_redis_cache()
        if rd is None:
            return None
        try:
            value = await rd.get(key)
            if value is not None:
                self._local_cache[key] = (now + 30.0, value)
            return value
        except Exception:
            return None

    async def _cache_set(self, key: str, value: str) -> None:
        now = time.monotonic()
        self._local_cache[key] = (now + min(120.0, float(self._cache_ttl_seconds)), value)
        if len(self._local_cache) > self._cache_max_entries:
            oldest_key = min(self._local_cache.keys(), key=lambda item: self._local_cache[item][0])
            self._local_cache.pop(oldest_key, None)

        rd = await self._get_redis_cache()
        if rd is None:
            return
        try:
            await rd.set(key, value, ex=self._cache_ttl_seconds)
        except Exception:
            return

    def _record_usage_event(
        self,
        idx: int,
        *,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        status: str,
        retries: int,
    ) -> None:
        gw = self._gateways[idx]
        self._usage_events.append(
            {
                "provider_type": gw.provider_type,
                "model": gw.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "latency_ms": latency_ms,
                "status": status,
                "retries": retries,
            }
        )

    def consume_usage_events(self) -> list[dict[str, Any]]:
        """Return and clear buffered usage events for cost accounting."""
        events = self._usage_events
        self._usage_events = []
        return events

    async def _acquire_quota(self, idx: int, reserved_tokens: int) -> None:
        """Wait until both RPM and TPM buckets have enough capacity."""
        import asyncio

        state = self._quota_state[idx]
        needed_tokens = float(max(1, reserved_tokens))
        if needed_tokens > state.token_bucket.capacity:
            needed_tokens = state.token_bucket.capacity

        while True:
            state.request_bucket.refill()
            state.token_bucket.refill()

            has_request = state.request_bucket.tokens >= 1.0
            has_tokens = state.token_bucket.tokens >= needed_tokens
            if has_request and has_tokens:
                state.request_bucket.tokens -= 1.0
                state.token_bucket.tokens -= needed_tokens
                return

            req_wait = state.request_bucket.seconds_until(1.0) if not has_request else 0.0
            tok_wait = state.token_bucket.seconds_until(needed_tokens) if not has_tokens else 0.0
            await asyncio.sleep(max(req_wait, tok_wait, 0.05))

    def _reconcile_token_reservation(self, idx: int, reserved_tokens: int, actual_tokens: int) -> None:
        """Refund over-reserved tokens to keep the bucket accurate enough."""
        state = self._quota_state[idx]
        state.token_bucket.refill()
        refund = max(0.0, float(reserved_tokens - actual_tokens))
        if refund > 0:
            state.token_bucket.tokens = min(
                state.token_bucket.capacity,
                state.token_bucket.tokens + refund,
            )

    # ------------------------------------------------------------------
    # Cooldown helpers
    # ------------------------------------------------------------------

    def _is_on_cooldown(self, idx: int) -> bool:
        expires = self._cooldown_until.get(idx)
        if expires is None:
            return False
        if time.monotonic() >= expires:
            del self._cooldown_until[idx]
            return False
        return True

    def _mark_cooldown(self, idx: int, reason: str = "rate-limited") -> None:
        self._cooldown_until[idx] = time.monotonic() + self._cooldown_seconds
        logger.warning(
            "Provider #%d (%s / %s) %s — cooldown %.0fs",
            idx,
            self._gateways[idx].provider_type,
            self._gateways[idx].model,
            reason,
            self._cooldown_seconds,
        )

    def _next_available(self, exclude: set[int]) -> int | None:
        """Find the next gateway that is not on cooldown and not excluded."""
        n = len(self._gateways)
        for offset in range(1, n + 1):
            candidate = (self._current + offset) % n
            if candidate in exclude:
                continue
            if not self._is_on_cooldown(candidate):
                return candidate
        return None

    def _shortest_remaining_cooldown(self) -> float:
        """Seconds until the earliest cooldown expires (min 0.5)."""
        now = time.monotonic()
        remaining = [v - now for v in self._cooldown_until.values() if v > now]
        return max(min(remaining) if remaining else 0.5, 0.5)

    # ------------------------------------------------------------------
    # Public API — matches LLMGateway interface
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        """
        Send a chat request, automatically failing over on rate limits.

        Tries each provider at most once per call.  If every provider is
        rate-limited, waits for the shortest cooldown and retries once.
        """
        import asyncio

        tried: set[int] = set()
        last_exc: Exception | None = None
        n = len(self._gateways)

        waited_for_global_cooldown = False

        cache_key: str | None = None
        if self._cache_enabled and self._is_cacheable_request(temperature, response_format):
            current = self._active
            cache_key = self._cache_key(
                provider_type=current.provider_type,
                model=current.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
            cached_result = await self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result

        while True:
            while len(tried) < n:
                # Skip current if on cooldown
                if self._is_on_cooldown(self._current):
                    nxt = self._next_available(tried)
                    if nxt is not None:
                        self._current = nxt
                    else:
                        break  # all on cooldown
                    continue

                idx = self._current
                gw = self._gateways[idx]
                tried.add(idx)

                estimated_input, _estimated_output, reserved_total = self._estimate_tokens(messages, max_tokens)
                await self._acquire_quota(idx, reserved_total)

                for retry in range(self._max_rate_limit_retries + 1):
                    started = time.monotonic()
                    try:
                        result = await gw.chat(
                            messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            response_format=response_format,
                        )
                        latency_ms = int((time.monotonic() - started) * 1000)
                        output_tokens = self._estimate_text_tokens(result)
                        self._record_usage_event(
                            idx,
                            input_tokens=estimated_input,
                            output_tokens=output_tokens,
                            latency_ms=latency_ms,
                            status="success",
                            retries=retry,
                        )
                        self._reconcile_token_reservation(
                            idx,
                            reserved_tokens=reserved_total,
                            actual_tokens=estimated_input + output_tokens,
                        )
                        if cache_key is not None:
                            await self._cache_set(cache_key, result)
                        return result
                    except Exception as exc:
                        last_exc = exc
                        latency_ms = int((time.monotonic() - started) * 1000)

                        if self._is_rate_limit_error(exc):
                            self._record_usage_event(
                                idx,
                                input_tokens=estimated_input,
                                output_tokens=0,
                                latency_ms=latency_ms,
                                status="rate_limited",
                                retries=retry,
                            )
                            self._mark_cooldown(idx, reason="rate-limited")

                            # Single-provider pools retry with exponential backoff + jitter.
                            if n == 1 and retry < self._max_rate_limit_retries:
                                delay = self._compute_retry_delay(retry, exc)
                                logger.warning(
                                    "Provider #%d (%s / %s) rate-limited, retrying in %.2fs",
                                    idx,
                                    gw.provider_type,
                                    gw.model,
                                    delay,
                                )
                                await asyncio.sleep(delay)
                                continue

                            # Multi-provider pools fail over immediately after a rate limit.
                            break

                        if bool(getattr(settings, "provider_pool_failover_on_transient_errors", True)) and self._is_transient_provider_error(exc):
                            self._record_usage_event(
                                idx,
                                input_tokens=estimated_input,
                                output_tokens=0,
                                latency_ms=latency_ms,
                                status="transient_error",
                                retries=retry,
                            )
                            self._mark_cooldown(idx, reason="transient provider failure")
                            break

                        self._record_usage_event(
                            idx,
                            input_tokens=estimated_input,
                            output_tokens=0,
                            latency_ms=latency_ms,
                            status="error",
                            retries=retry,
                        )
                        raise

                # Try next available provider after exhausting retries for this one.
                nxt = self._next_available(tried)
                if nxt is not None:
                    self._current = nxt
                    continue

                # All providers exhausted in this pass.
                break

            # All providers exhausted or on cooldown — wait once and retry full sweep.
            if (
                last_exc is not None
                and self._is_rate_limit_error(last_exc)
                and not waited_for_global_cooldown
            ):
                wait = self._shortest_remaining_cooldown()
                wait += random.uniform(0.0, max(0.05, wait * 0.25))
                logger.warning(
                    "All %d provider(s) rate-limited. Waiting %.2fs for cooldown before retrying…",
                    n,
                    wait,
                )
                await asyncio.sleep(wait)
                waited_for_global_cooldown = True
                tried.clear()
                # Start from first available provider after cooldown.
                for idx in range(n):
                    if not self._is_on_cooldown(idx):
                        self._current = idx
                        break
                continue

            break

        # Propagate the last exception
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("ProviderPool: no providers available")

    async def validate_credentials(self) -> tuple[bool, str | None]:
        """Validate at least one provider's credentials."""
        errors: list[str] = []
        for idx, gw in enumerate(self._gateways):
            ok, err = await gw.validate_credentials()
            if ok:
                self._current = idx  # prefer the validated one as primary
                return True, None
            errors.append(f"Provider #{idx} ({gw.provider_type}): {err}")
        return False, "; ".join(errors)
