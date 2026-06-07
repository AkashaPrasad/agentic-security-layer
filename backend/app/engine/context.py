"""
ExperimentContext — loaded from DB at experiment start.

Carries all state the engine needs: experiment config, project scope,
provider credentials, and template selections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class TargetConfig:
    """Parsed and decrypted target configuration."""

    endpoint_url: str
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    payload_template: str = '{"prompt": "{{prompt}}"}'
    response_json_path: str = "$.response"
    auth_type: str | None = None  # "bearer" | "api_key" | "basic" | None
    auth_value: str | None = None
    timeout_seconds: int = 30
    # Multi-turn
    thread_endpoint_url: str | None = None
    thread_id_path: str | None = None
    # System prompt for the target AI
    system_prompt: str | None = None
    # Per-experiment override for prompt batch concurrency
    experiment_batch_concurrency: int | None = None
    # Deterministic run seed for reproducibility
    random_seed: int | None = None
    # Retry metadata (internal)
    retry_source_experiment_id: str | None = None
    retry_mode: str | None = None
    # Strategy orchestration mode
    strategy_mode: str | None = None
    attack_pipeline: list[str] | None = None


@dataclass
class ProjectScope:
    """Project scope information used for context-aware generation."""

    project_id: UUID
    project_name: str
    business_scope: str
    allowed_intents: list[str] = field(default_factory=list)
    restricted_intents: list[str] = field(default_factory=list)
    analyzed_scope: dict | None = None


@dataclass
class ProviderInfo:
    """Decrypted provider credentials."""

    provider_id: UUID
    provider_type: str  # "openai" | "azure_openai"
    api_key: str  # Decrypted
    endpoint_url: str | None = None
    model: str = "gpt-4o"


@dataclass
class ExperimentContext:
    """
    Immutable context for a single experiment run.
    Built once at the start of ``runner.run_experiment`` and passed
    through the entire pipeline.
    """

    experiment_id: UUID
    experiment_type: str  # "adversarial" | "behavioural"
    sub_type: str
    turn_mode: str  # "single_turn" | "multi_turn"
    testing_level: str  # "50" | "100" | "200" | "300" | "400" | "basic" | "moderate" | "aggressive"
    language: str  # ISO 639-1

    total_tests: int  # Budget from TESTING_LEVEL_COUNTS

    target: TargetConfig
    scope: ProjectScope
    provider: ProviderInfo

    # Optional plugin filter — list of promptfoo-compatible plugin IDs.
    # None / empty list → use all strategy keys with default weights.
    plugins: list[str] | None = None

    # Populated by planner
    created_by_id: UUID | None = None
