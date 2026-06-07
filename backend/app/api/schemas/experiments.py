"""
Pydantic schemas for the Experiments API (Phase 6.3).
"""

import math
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.api.schemas.shared import ProviderBrief, UserBrief

# ---------------------------------------------------------------------------
# Valid sub_types
# ---------------------------------------------------------------------------
ADVERSARIAL_SUB_TYPES = {"owasp_llm_top10", "owasp_agentic", "adaptive"}
BEHAVIOURAL_SUB_TYPES = {"user_interaction", "functional", "scope_validation"}
DATASET_SUB_TYPES = {"beavertails"}
VALID_SUB_TYPES = ADVERSARIAL_SUB_TYPES | BEHAVIOURAL_SUB_TYPES | DATASET_SUB_TYPES

TESTING_LEVEL_COUNTS = {
    "50": 50,
    "100": 100,
    "200": 200,
    "300": 300,
    "400": 400,
    "basic": 500,
    "moderate": 1200,
    "aggressive": 2000,
}


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class TargetConfig(BaseModel):
    endpoint_url: str = Field(..., max_length=500)
    method: str = Field("POST", pattern=r"^(POST|PUT)$")
    headers: dict[str, str] = Field(default_factory=dict)
    payload_template: str = Field(..., min_length=1, max_length=2000)
    auth_type: str | None = Field(None, pattern=r"^(bearer|api_key|basic|none)$")
    auth_value: str | None = Field(None, max_length=500)
    timeout_seconds: int = Field(30, ge=5, le=120)
    thread_endpoint_url: str | None = Field(None, max_length=500)
    thread_id_path: str | None = Field(None, max_length=200)
    system_prompt: str | None = Field(None, max_length=10000)
    experiment_batch_concurrency: int | None = Field(None, ge=1, le=32)
    strategy_mode: str | None = Field(None, pattern=r"^(independent|chained_adaptive)$")
    attack_pipeline: list[str] | None = Field(default=None, max_length=10)

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "TargetConfig":
        if "{{prompt}}" not in self.payload_template:
            raise ValueError("payload_template must contain the {{prompt}} placeholder")
        # Normalise "none" string to None
        if self.auth_type == "none":
            self.auth_type = None
        if self.auth_type and not self.auth_value:
            raise ValueError("auth_value is required when auth_type is set")
        return self

    @property
    def is_direct_provider(self) -> bool:
        """True when the experiment targets a platform provider directly."""
        return self.endpoint_url.startswith("direct://")

    @property
    def direct_provider_id(self) -> str | None:
        """Extract provider UUID from a direct:// URL."""
        if self.is_direct_provider:
            return self.endpoint_url.removeprefix("direct://")
        return None


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    provider_id: UUID
    experiment_type: str = Field(..., pattern=r"^(adversarial|behavioural|dataset_test)$")
    sub_type: str
    turn_mode: str = Field("single_turn", pattern=r"^(single_turn|multi_turn)$")
    testing_level: str = Field("50", pattern=r"^(50|100|200|300|400|basic|moderate|aggressive)$")
    random_seed: int | None = Field(None, ge=0, le=2_147_483_647)
    language: str = Field("en", min_length=2, max_length=10)
    plugins: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of plugin IDs to run. When None or empty, all strategies "
            "are used with default weights. When provided, only strategy keys that "
            "map to the selected plugin IDs are included in the test plan."
        ),
    )
    target_config: TargetConfig

    @model_validator(mode="after")
    def validate_experiment(self) -> "ExperimentCreate":
        # Validate sub_type for experiment_type
        if self.experiment_type == "adversarial":
            if self.sub_type not in ADVERSARIAL_SUB_TYPES:
                raise ValueError(
                    f"Invalid sub_type '{self.sub_type}' for adversarial. "
                    f"Valid: {ADVERSARIAL_SUB_TYPES}"
                )
        elif self.experiment_type == "behavioural":
            if self.sub_type not in BEHAVIOURAL_SUB_TYPES:
                raise ValueError(
                    f"Invalid sub_type '{self.sub_type}' for behavioural. "
                    f"Valid: {BEHAVIOURAL_SUB_TYPES}"
                )
        else:  # dataset_test
            if self.sub_type not in DATASET_SUB_TYPES:
                raise ValueError(
                    f"Invalid sub_type '{self.sub_type}' for dataset_test. "
                    f"Valid: {DATASET_SUB_TYPES}"
                )
            # dataset_test does not require multi_turn validation
            return self

        # adaptive requires multi_turn
        if self.sub_type == "adaptive" and self.turn_mode != "multi_turn":
            raise ValueError("sub_type 'adaptive' requires turn_mode 'multi_turn'")

        # multi_turn requires thread config
        if self.turn_mode == "multi_turn":
            if not self.target_config.thread_endpoint_url:
                raise ValueError("thread_endpoint_url required for multi_turn mode")
            if not self.target_config.thread_id_path:
                raise ValueError("thread_id_path required for multi_turn mode")

        return self


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TargetConfigResponse(BaseModel):
    endpoint_url: str
    method: str
    headers: dict[str, str]
    payload_template: str
    auth_type: str | None = None
    auth_value_preview: str | None = None
    timeout_seconds: int
    thread_endpoint_url: str | None = None
    thread_id_path: str | None = None
    system_prompt: str | None = None
    experiment_batch_concurrency: int | None = None
    strategy_mode: str | None = None
    attack_pipeline: list[str] | None = None


class ExperimentProgress(BaseModel):
    total: int | None = None
    completed: int = 0
    percentage: float | None = None


class ExperimentAnalytics(BaseModel):
    total_tests: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    severity_breakdown: dict[str, int] = {}
    category_breakdown: list[dict] = []
    cost_summary: dict | None = None


class ExperimentResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None = None
    experiment_type: str
    sub_type: str
    turn_mode: str
    testing_level: str
    language: str
    target_config: TargetConfigResponse
    status: str
    progress: ExperimentProgress
    analytics: ExperimentAnalytics | None = None
    provider: ProviderBrief | None = None
    created_by: UserBrief | None = None
    error_message: str | None = None
    status_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExperimentSummary(BaseModel):
    id: UUID
    name: str
    experiment_type: str
    sub_type: str
    turn_mode: str
    testing_level: str
    status: str
    progress: ExperimentProgress
    pass_rate: float | None = None
    error_message: str | None = None
    status_message: str | None = None
    created_by: UserBrief | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentList(BaseModel):
    items: list[ExperimentSummary]
    total: int
    page: int
    page_size: int
    pages: int = 0

    @classmethod
    def build(cls, items: list[ExperimentSummary], total: int, page: int, page_size: int) -> "ExperimentList":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if page_size > 0 else 0,
        )


class ExperimentStatusResponse(BaseModel):
    id: UUID
    status: str
    progress: ExperimentProgress
    error_message: str | None = None
    status_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ExperimentRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
