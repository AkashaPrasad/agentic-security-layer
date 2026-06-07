"""
Base strategy abstract class.

All attack/test strategies inherit from BaseStrategy and implement
the generate() method to produce category-specific prompts.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.engine.context import ExperimentContext


@dataclass
class PromptSpec:
    """A single prompt specification from a strategy."""
    id: str
    text: str
    severity: str = "medium"  # low | medium | high
    tags: list[str] = field(default_factory=list)
    expected_behaviour: str | None = None  # behavioural tests only


class BaseStrategy(ABC):
    """
    Abstract base class for all attack / test strategies.

    Each strategy owns one risk_category and produces prompt
    specifications that feed into the generation pipeline.
    """

    risk_category: str = ""
    owasp_id: str | None = None
    compatible_converters: list[str] = [
        "base64", "rot13", "unicode_substitution",
        "payload_split", "leetspeak", "translation",
        "jailbreak_wrapper",
    ]

    @abstractmethod
    def generate(self, ctx: ExperimentContext, count: int) -> list[PromptSpec]:
        """
        Generate *count* prompt specifications for this category.

        Parameters
        ----------
        ctx : ExperimentContext
            Full experiment context with project scope, intents, etc.
        count : int
            Number of prompts to produce.

        Returns
        -------
        list[PromptSpec]
        """
        ...

    # ------------------------------------------------------------------
    # Helpers available to all strategies
    # ------------------------------------------------------------------

    @staticmethod
    def _pick(items: list[str], n: int = 1) -> list[str]:
        """Pick *n* random items from a list (with replacement if needed)."""
        if not items:
            return ["general topic"]
        return random.choices(items, k=n)

    @staticmethod
    def _pick_one(items: list[str]) -> str:
        if not items:
            return "general topic"
        return random.choice(items)

    def _restricted(self, ctx: ExperimentContext) -> str:
        return self._pick_one(ctx.scope.restricted_intents)

    def _allowed(self, ctx: ExperimentContext) -> str:
        return self._pick_one(ctx.scope.allowed_intents)

    def _scope(self, ctx: ExperimentContext) -> str:
        return ctx.scope.business_scope or ctx.scope.project_name

    def _persona(self) -> str:
        return random.choice([
            "developer", "administrator", "support agent",
            "CEO", "security researcher", "compliance officer",
            "system administrator", "data scientist",
        ])

    def _expand(
        self,
        templates: list[tuple[str, str, str, list[str]]],
        ctx: ExperimentContext,
        count: int,
        prefix: str = "",
    ) -> list[PromptSpec]:
        """
        Expand a list of (id, text, severity, tags) tuples into
        PromptSpecs, cycling/sampling to fill *count*.
        """
        specs: list[PromptSpec] = []
        idx = 0
        while len(specs) < count:
            tpl_id, tpl_text, sev, tags = templates[idx % len(templates)]
            text = tpl_text.format(
                restricted_intent=self._restricted(ctx),
                allowed_intent=self._allowed(ctx),
                scope_topic=self._scope(ctx),
                business_scope=self._scope(ctx),
                project_name=ctx.scope.project_name,
                persona=self._persona(),
            )
            specs.append(PromptSpec(
                id=f"{prefix}{tpl_id}_{len(specs):04d}",
                text=text,
                severity=sev,
                tags=tags,
            ))
            idx += 1
        return specs[:count]
