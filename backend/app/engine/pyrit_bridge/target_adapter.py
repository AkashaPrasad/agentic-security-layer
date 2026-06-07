"""
PyRIT Target Adapter — adapts our TargetConfig to a PyRIT PromptTarget.

Handles: HTTPS calls, auth injection, payload template rendering,
timeout, retry, and response extraction.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.engine.context import TargetConfig
from app.engine.executor import send_prompt, init_thread

if TYPE_CHECKING:
    from app.services.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)


class AppHTTPTarget:
    """
    Adapts the experiment's TargetConfig into a PyRIT-compatible target.

    If PyRIT is installed, this can serve as a PromptTarget subclass.
    Otherwise, it wraps our own executor for direct use.
    """

    def __init__(self, target_config: TargetConfig, llm_gateway: "LLMGateway"):
        self.config = target_config
        self.gateway = llm_gateway
        self._thread_id: str | None = None

    async def send_prompt_async(self, prompt: str) -> str:
        """
        Send a single prompt to the target AI.

        1. Render payload_template with {{prompt}}
        2. Build HTTP request (method, url, headers, auth)
        3. Send via httpx async client
        4. Extract response text
        5. Return response text
        """
        response_text, _ = await send_prompt(self.config, prompt)
        return response_text or ""

    async def send_thread_prompt_async(
        self,
        prompt: str,
        thread_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Multi-turn variant.

        1. If thread_id is None → call thread_endpoint_url to init
        2. Extract thread_id from response via thread_id_path
        3. Send prompt to endpoint_url with thread_id in payload
        4. Return (response_text, thread_id)
        """
        if thread_id is None and self._thread_id is None:
            self._thread_id = await init_thread(self.config)
        elif thread_id is not None:
            self._thread_id = thread_id

        response_text, _ = await send_prompt(
            self.config,
            prompt,
            thread_id=self._thread_id,
        )
        return response_text or "", self._thread_id or ""

    async def reset_thread(self) -> None:
        """Reset the conversation thread for a new multi-turn exchange."""
        self._thread_id = None
