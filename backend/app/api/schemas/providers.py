"""
Pydantic schemas for the Providers API (Phase 6.1).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.shared import UserBrief


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(
        ...,
        pattern=(
            r"^(openai|azure_openai|groq|openai_compatible|custom|"
            r"anthropic|gemini|ollama|mistral|together|deepseek|"
            r"perplexity|fireworks|xai|cohere|huggingface)$"
        ),
    )
    api_key: str = Field(..., min_length=1, max_length=500)
    endpoint_url: str | None = Field(None, max_length=500)
    model: str | None = Field(None, max_length=100)
    # Rate limiting
    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    max_calls_per_experiment: int | None = None
    # Judge config
    judge_api_key: str | None = None
    judge_endpoint: str | None = None
    judge_model: str | None = None
    use_separate_judge: bool = False
    # Default config
    default_target_endpoint: str | None = None
    default_system_prompt: str | None = None
    # Backup key failover
    backup_api_key: str | None = None
    backup_endpoint: str | None = None
    backup_model: str | None = None
    use_backup_key: bool = False


class ProviderUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    api_key: str | None = Field(None, min_length=1, max_length=500)
    endpoint_url: str | None = Field(None, max_length=500)
    model: str | None = Field(None, max_length=100)
    # Rate limiting
    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    max_calls_per_experiment: int | None = None
    # Judge config
    judge_api_key: str | None = None
    judge_endpoint: str | None = None
    judge_model: str | None = None
    use_separate_judge: bool | None = None
    # Default config
    default_target_endpoint: str | None = None
    default_system_prompt: str | None = None
    # Backup key failover
    backup_api_key: str | None = None
    backup_endpoint: str | None = None
    backup_model: str | None = None
    use_backup_key: bool | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ProviderResponse(BaseModel):
    id: UUID
    name: str
    provider_type: str
    endpoint_url: str | None = None
    model: str | None = None
    api_key_preview: str | None = None
    is_valid: bool
    has_experiments: bool = False
    created_by: UserBrief | None = None
    created_at: datetime
    updated_at: datetime
    # Rate limiting
    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None
    max_calls_per_experiment: int | None = None
    # Judge config
    judge_api_key: str | None = None
    judge_endpoint: str | None = None
    judge_model: str | None = None
    use_separate_judge: bool = False
    # Default config
    default_target_endpoint: str | None = None
    default_system_prompt: str | None = None
    # Backup key failover
    backup_api_key: str | None = None
    backup_endpoint: str | None = None
    backup_model: str | None = None
    use_backup_key: bool = False

    model_config = {"from_attributes": True}


class ProviderList(BaseModel):
    items: list[ProviderResponse]
    total: int


class ProviderValidationResult(BaseModel):
    provider_id: UUID
    is_valid: bool
    message: str
    latency_ms: int | None = None
