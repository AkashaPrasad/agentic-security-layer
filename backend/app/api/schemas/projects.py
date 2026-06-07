"""
Pydantic schemas for the Projects API (Phase 6.2).
"""

import math
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.shared import UserBrief


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=255)
    business_scope: str = Field(..., min_length=1, max_length=10000)
    allowed_intents: list[str] = Field(default_factory=list, max_length=100)
    restricted_intents: list[str] = Field(default_factory=list, max_length=100)
    system_prompt: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=255)
    business_scope: str | None = Field(None, min_length=1, max_length=10000)
    allowed_intents: list[str] | None = Field(None, max_length=100)
    restricted_intents: list[str] | None = Field(None, max_length=100)
    system_prompt: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    business_scope: str
    allowed_intents: list[str]
    restricted_intents: list[str]
    analyzed_scope: dict | None = None
    system_prompt: str | None = None
    api_key_prefix: str
    is_active: bool
    created_by: UserBrief | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    experiment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    items: list[ProjectSummary]
    total: int
    page: int
    page_size: int
    pages: int = 0

    @classmethod
    def build(cls, items: list[ProjectSummary], total: int, page: int, page_size: int) -> "ProjectList":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if page_size > 0 else 0,
        )


class ApiKeyResponse(BaseModel):
    api_key: str
    api_key_prefix: str
    message: str


class ScopeAnalysisResponse(BaseModel):
    analyzed_scope: dict
    message: str
