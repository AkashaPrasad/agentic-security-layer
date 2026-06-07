"""
Template Registry — loads, validates, and indexes YAML attack templates.

Singleton pattern. Loaded once at worker startup, templates are cached
in memory for O(1) lookup by (experiment_type, sub_type, turn_mode).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default template directory
DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class PromptDefinition:
    id: str
    text: str
    severity: str = "medium"
    tags: list[str] = field(default_factory=list)
    expected_behaviour: str | None = None


@dataclass
class ConversationTurn:
    turn: int
    role: str
    text: str
    adaptive: bool = False
    notes: str | None = None


@dataclass
class ConversationTemplate:
    max_turns: int
    escalation_strategy: str
    turns: list[ConversationTurn] = field(default_factory=list)
    adaptive_rewrite_instruction: str | None = None


@dataclass
class ContextVariable:
    name: str
    source: str
    values: list[str] | None = None
    instruction: str | None = None
    description: str | None = None


@dataclass
class LLMAugmentation:
    enabled: bool = True
    max_variants_per_prompt: int = 3
    instruction: str = ""


@dataclass
class AttackTemplate:
    template_id: str
    version: str
    risk_category: str
    owasp_id: str | None
    severity_default: str
    experiment_types: list[str]
    sub_types: list[str]
    turn_modes: list[str]
    prompts: list[PromptDefinition] = field(default_factory=list)
    context_variables: list[ContextVariable] = field(default_factory=list)
    compatible_converters: list[str] = field(default_factory=list)
    llm_augmentation: LLMAugmentation | None = None
    conversation_template: ConversationTemplate | None = None


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TemplateRegistry:
    """
    Singleton. Loads all YAML templates from disk, validates their schema,
    indexes by (experiment_type, sub_type, turn_mode) for O(1) lookup.
    """

    _instance: TemplateRegistry | None = None
    _loaded: bool = False

    _templates: dict[str, AttackTemplate]
    _index: dict[tuple[str, str, str], list[str]]

    def __new__(cls) -> TemplateRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._templates = {}
            cls._instance._index = {}
        return cls._instance

    def load_all(self, template_dir: Path | None = None) -> None:
        """Walk template_dir, parse YAML, validate, build indices."""
        if self._loaded:
            return

        directory = template_dir or DEFAULT_TEMPLATE_DIR
        if not directory.exists():
            logger.warning("Template directory not found: %s", directory)
            self._loaded = True
            return

        yaml_files = list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))
        logger.info("Loading %d template files from %s", len(yaml_files), directory)

        for yaml_file in yaml_files:
            try:
                self._load_file(yaml_file)
            except Exception as e:
                logger.error("Failed to load template %s: %s", yaml_file, e)

        # Build index
        self._build_index()
        self._loaded = True
        logger.info(
            "Template registry loaded: %d templates, %d index keys",
            len(self._templates),
            len(self._index),
        )

    def _load_file(self, path: Path) -> None:
        """Parse a single YAML file into an AttackTemplate."""
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)

        if not data or "template_id" not in data:
            return

        # Parse prompts
        prompts = []
        for p in data.get("prompts", []):
            prompts.append(PromptDefinition(
                id=p.get("id", ""),
                text=p.get("text", ""),
                severity=p.get("severity", "medium"),
                tags=p.get("tags", []),
                expected_behaviour=p.get("expected_behaviour"),
            ))

        # Parse context variables
        ctx_vars = []
        for cv in data.get("context_variables", []):
            ctx_vars.append(ContextVariable(
                name=cv.get("name", ""),
                source=cv.get("source", ""),
                values=cv.get("values"),
                instruction=cv.get("instruction"),
                description=cv.get("description"),
            ))

        # Parse LLM augmentation
        aug_data = data.get("llm_augmentation")
        llm_aug = None
        if aug_data:
            llm_aug = LLMAugmentation(
                enabled=aug_data.get("enabled", True),
                max_variants_per_prompt=aug_data.get("max_variants_per_prompt", 3),
                instruction=aug_data.get("instruction", ""),
            )

        # Parse conversation template
        conv_data = data.get("conversation_template")
        conv_template = None
        if conv_data:
            turns = []
            for t in conv_data.get("turns", []):
                turns.append(ConversationTurn(
                    turn=t.get("turn", 0),
                    role=t.get("role", ""),
                    text=t.get("text", ""),
                    adaptive=t.get("adaptive", False),
                    notes=t.get("notes"),
                ))
            conv_template = ConversationTemplate(
                max_turns=conv_data.get("max_turns", 5),
                escalation_strategy=conv_data.get("escalation_strategy", "crescendo"),
                turns=turns,
                adaptive_rewrite_instruction=conv_data.get("adaptive_rewrite_instruction"),
            )

        template = AttackTemplate(
            template_id=data["template_id"],
            version=data.get("version", "1.0.0"),
            risk_category=data.get("risk_category", ""),
            owasp_id=data.get("owasp_id"),
            severity_default=data.get("severity_default", "medium"),
            experiment_types=data.get("experiment_types", []),
            sub_types=data.get("sub_types", []),
            turn_modes=data.get("turn_modes", ["single_turn"]),
            prompts=prompts,
            context_variables=ctx_vars,
            compatible_converters=data.get("compatible_converters", []),
            llm_augmentation=llm_aug,
            conversation_template=conv_template,
        )

        self._templates[template.template_id] = template

    def _build_index(self) -> None:
        """Build (experiment_type, sub_type, turn_mode) → [template_ids] index."""
        self._index.clear()
        for template in self._templates.values():
            for exp_type in template.experiment_types:
                for sub_type in template.sub_types:
                    for turn_mode in template.turn_modes:
                        key = (exp_type, sub_type, turn_mode)
                        if key not in self._index:
                            self._index[key] = []
                        self._index[key].append(template.template_id)

    def get_templates(
        self,
        experiment_type: str,
        sub_type: str,
        turn_mode: str,
    ) -> list[AttackTemplate]:
        """Return all templates matching the given experiment configuration."""
        if not self._loaded:
            self.load_all()

        key = (experiment_type, sub_type, turn_mode)
        template_ids = self._index.get(key, [])
        return [self._templates[tid] for tid in template_ids if tid in self._templates]

    def get_template(self, template_id: str) -> AttackTemplate | None:
        """Return a specific template by ID."""
        if not self._loaded:
            self.load_all()
        return self._templates.get(template_id)

    @property
    def template_count(self) -> int:
        if not self._loaded:
            self.load_all()
        return len(self._templates)

    def reset(self) -> None:
        """Reset the registry (mainly for testing)."""
        self._templates.clear()
        self._index.clear()
        self._loaded = False
