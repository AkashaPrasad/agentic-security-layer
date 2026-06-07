"""
Target AI executor — sends prompts to the target AI and extracts responses.

Handles HTTP invocation, auth injection, payload template rendering,
timeout, retry with exponential backoff, and response JSON-path extraction.

Also supports *direct provider* mode: when ``endpoint_url`` starts with
``direct://<provider_id>``, the executor calls the platform's LLMGateway
in-process, bypassing HTTP entirely.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.engine.context import TargetConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON-path mini-extractor (supports simple dot-notation / bracket paths)
# ---------------------------------------------------------------------------


def _extract_json_path(data: dict | list, path: str) -> str | None:
    """
    Simple JSON-path extractor supporting ``$.field.sub`` and ``$.field[0]``.
    """
    if not path or path == "$":
        return json.dumps(data) if isinstance(data, (dict, list)) else str(data)

    parts = path.lstrip("$").lstrip(".")
    current = data
    for part in re.split(r"\.|(?=\[)", parts):
        if not part:
            continue
        # Array index: [0]
        m = re.match(r"\[(\d+)]", part)
        if m:
            idx = int(m.group(1))
            if isinstance(current, list) and idx < len(current):
                current = current[idx]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return None
        else:
            return None

    if isinstance(current, str):
        return current
    return json.dumps(current) if current is not None else None


# ---------------------------------------------------------------------------
# Send prompt to target AI
# ---------------------------------------------------------------------------


async def send_prompt(
    target: "TargetConfig",
    prompt: str,
    *,
    thread_id: str | None = None,
    gateway: object | None = None,
    retries: int = 3,
    backoff_base: float = 2.0,
) -> tuple[str | None, int]:
    """
    Send a prompt to the target AI and return (response_text, latency_ms).

    Returns (None, latency_ms) if all retries are exhausted.
    """
    import asyncio
    import time

    # ── Direct Provider shortcut ──
    if target.endpoint_url.startswith("direct://"):
        return await _send_direct(target, prompt, gateway=gateway)

    # Build payload from template
    payload_str = target.payload_template.replace("{{prompt}}", prompt)
    if thread_id and "{{thread_id}}" in payload_str:
        payload_str = payload_str.replace("{{thread_id}}", thread_id)
    if target.system_prompt and "{{system_prompt}}" in payload_str:
        payload_str = payload_str.replace("{{system_prompt}}", target.system_prompt)

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = {"prompt": prompt}

    # Auto-inject system prompt into "messages" array if present and not
    # already handled via the {{system_prompt}} placeholder
    if target.system_prompt and "{{system_prompt}}" not in target.payload_template:
        if isinstance(payload, dict) and "messages" in payload and isinstance(payload["messages"], list):
            payload["messages"].insert(0, {"role": "system", "content": target.system_prompt})

    # Build headers
    headers = dict(target.headers) if target.headers else {}
    headers.setdefault("Content-Type", "application/json")

    # Inject auth
    if target.auth_type == "bearer" and target.auth_value:
        headers["Authorization"] = f"Bearer {target.auth_value}"
    elif target.auth_type == "api_key" and target.auth_value:
        headers["X-API-Key"] = target.auth_value
    elif target.auth_type == "basic" and target.auth_value:
        import base64
        encoded = base64.b64encode(target.auth_value.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"

    timeout = httpx.Timeout(float(target.timeout_seconds), connect=10.0)

    for attempt in range(retries):
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if target.method.upper() == "GET":
                    resp = await client.get(target.endpoint_url, headers=headers, params=payload)
                else:
                    resp = await client.post(target.endpoint_url, headers=headers, json=payload)

            latency_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code >= 400:
                if attempt < retries - 1:
                    await asyncio.sleep(backoff_base ** attempt)
                    continue
                return None, latency_ms

            # Extract response
            try:
                resp_data = resp.json()
                extracted = _extract_json_path(resp_data, target.response_json_path)
                return extracted or resp.text, latency_ms
            except Exception:
                return resp.text, latency_ms

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError):
            latency_ms = int((time.monotonic() - start) * 1000)
            if attempt < retries - 1:
                await asyncio.sleep(backoff_base ** attempt)
                continue
            return None, latency_ms

    return None, 0


# ---------------------------------------------------------------------------
# Multi-turn: init thread
# ---------------------------------------------------------------------------


async def init_thread(target: "TargetConfig") -> str | None:
    """
    Call the thread_endpoint_url to create a new conversation thread.
    Returns the thread_id extracted via thread_id_path.
    """
    if not target.thread_endpoint_url:
        return None

    headers = dict(target.headers) if target.headers else {}
    headers.setdefault("Content-Type", "application/json")

    if target.auth_type == "bearer" and target.auth_value:
        headers["Authorization"] = f"Bearer {target.auth_value}"

    timeout = httpx.Timeout(float(target.timeout_seconds), connect=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                target.thread_endpoint_url,
                headers=headers,
                json={},
            )
        if resp.status_code < 400:
            data = resp.json()
            if target.thread_id_path:
                return _extract_json_path(data, target.thread_id_path)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Direct Provider — call LLMGateway in-process (no HTTP round-trip)
# ---------------------------------------------------------------------------

# Module-level cache: one standalone (engine, session_factory) per process.
# The global async_engine in database.py is bound to the web-server's event
# loop and cannot be used from Celery workers (each worker calls asyncio.run()
# creating its own loop). Rather than creating a fresh engine — and therefore
# a fresh connection pool — on every single _send_direct fallback call, we
# create one per worker process and reuse it.
_STANDALONE_SESSION_FACTORY: tuple | None = None


def _get_or_create_standalone_session_factory() -> tuple:
    global _STANDALONE_SESSION_FACTORY
    if _STANDALONE_SESSION_FACTORY is None:
        from app.storage.database import create_standalone_session_factory
        _STANDALONE_SESSION_FACTORY = create_standalone_session_factory()
    return _STANDALONE_SESSION_FACTORY


async def _send_direct(
    target: "TargetConfig",
    prompt: str,
    *,
    gateway: object | None = None,
    retries: int = 5,
    backoff_base: float = 2.0,
) -> tuple[str | None, int]:
    """
    Send a prompt through the platform's LLMGateway.  When a pre-built
    ``gateway`` is provided (normal code-path from the experiment runner)
    it is used directly — no DB lookup needed.  Otherwise falls back to
    loading the provider from the database.

    The ``direct://<provider_id>`` URL pattern signals this code path.

    Includes retry-with-exponential-backoff for rate-limit (429) errors.

    Returns (response_text, latency_ms).
    """
    import asyncio
    import time
    from uuid import UUID

    from app.services.llm_gateway import LLMGateway

    start = time.monotonic()

    try:
        # If no gateway was passed, load provider from DB (fallback path).
        # Uses the process-level cached engine — not a fresh one per call.
        if gateway is None:
            from sqlalchemy import select
            from app.storage.models.provider import ModelProvider

            provider_id_str = target.endpoint_url.removeprefix("direct://")
            try:
                provider_uuid = UUID(provider_id_str)
            except ValueError:
                logger.error("Invalid provider UUID in direct:// URL: %s", provider_id_str)
                return None, 0

            _engine, _SessionFactory = _get_or_create_standalone_session_factory()
            async with _SessionFactory() as session:
                row = await session.execute(
                    select(ModelProvider).where(ModelProvider.id == provider_uuid)
                )
                provider = row.scalar_one_or_none()

            if provider is None:
                logger.error("Provider %s not found for direct mode", provider_id_str)
                return None, 0

            gateway = LLMGateway(
                provider_type=provider.provider_type,
                encrypted_api_key=provider.encrypted_api_key,
                endpoint_url=provider.endpoint_url,
                model=provider.model,
            )

        messages = []
        if target.system_prompt:
            messages.append({"role": "system", "content": target.system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Retry loop with exponential backoff for rate-limit errors
        last_exc = None
        for attempt in range(retries):
            try:
                response_text = await gateway.chat(messages)
                latency_ms = int((time.monotonic() - start) * 1000)
                return response_text, latency_ms
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc).lower()
                # Retry on rate-limit (429) or server errors (5xx)
                if "429" in exc_str or "rate" in exc_str or "too many" in exc_str or "503" in exc_str:
                    wait = backoff_base ** attempt
                    logger.warning(
                        "Direct call rate-limited (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1, retries, wait, exc,
                    )
                    await asyncio.sleep(wait)
                    continue
                # Non-retryable error
                raise

        # All retries exhausted
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.error("Direct provider call exhausted %d retries: %s", retries, last_exc)
        return None, latency_ms

    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.exception("Direct provider call failed: %s", exc)
        return None, latency_ms
