"""
Pydantic schemas for the Firewall API (Phase 6.6).
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.api.schemas.shared import UserBrief


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class FirewallEvalRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)
    agent_prompt: str | None = Field(None, max_length=10_000)

    @model_validator(mode="after")
    def strip_prompt(self):
        self.prompt = self.prompt.strip()
        if not self.prompt:
            raise ValueError("PROMPT_REQUIRED")
        if self.agent_prompt:
            self.agent_prompt = self.agent_prompt.strip() or None
        return self


RULE_TYPES = {"block_pattern", "allow_pattern", "custom_policy"}
PATTERN_RULE_TYPES = {"block_pattern", "allow_pattern"}


class FirewallRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    rule_type: str
    pattern: str | None = Field(None, max_length=2000)
    policy: str | None = Field(None, max_length=5000)
    priority: int = Field(0, ge=0, le=1000)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_rule_fields(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Name must not be empty after stripping")
        if self.rule_type not in RULE_TYPES:
            raise ValueError(
                f"rule_type must be one of {sorted(RULE_TYPES)}"
            )
        if self.rule_type in PATTERN_RULE_TYPES:
            if not self.pattern:
                raise ValueError("PATTERN_REQUIRED")
            if self.policy is not None:
                raise ValueError("FIELD_NOT_APPLICABLE")
            # Validate regex
            try:
                re.compile(self.pattern)
            except re.error:
                raise ValueError("INVALID_REGEX")
        elif self.rule_type == "custom_policy":
            if not self.policy:
                raise ValueError("POLICY_REQUIRED")
            if self.pattern is not None:
                raise ValueError("FIELD_NOT_APPLICABLE")
        return self


class FirewallRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    pattern: str | None = Field(None, max_length=2000)
    policy: str | None = Field(None, max_length=5000)
    priority: int | None = Field(None, ge=0, le=1000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not any(
            v is not None
            for v in [self.name, self.pattern, self.policy, self.priority, self.is_active]
        ):
            raise ValueError("NO_FIELDS_TO_UPDATE")
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("Name must not be empty after stripping")
        if self.pattern is not None:
            try:
                re.compile(self.pattern)
            except re.error:
                raise ValueError("INVALID_REGEX")
        return self


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FirewallVerdictResponse(BaseModel):
    status: bool  # true = safe, false = blocked
    fail_category: str | None = None
    explanation: str
    confidence: float
    matched_rule: str | None = None


class FirewallRuleResponse(BaseModel):
    id: UUID
    name: str
    rule_type: str
    pattern: str | None = None
    policy: str | None = None
    priority: int
    is_active: bool
    created_by: UserBrief | None = None
    created_at: datetime
    updated_at: datetime


class FirewallRuleList(BaseModel):
    items: list[FirewallRuleResponse]
    total: int


class FirewallLogEntry(BaseModel):
    id: UUID
    prompt_preview: str | None = None
    verdict_status: bool
    fail_category: str | None = None
    confidence: float | None = None
    matched_rule_name: str | None = None
    latency_ms: int
    ip_address: str | None = None
    created_at: datetime


class FirewallLogList(BaseModel):
    items: list[FirewallLogEntry]
    total: int
    cursor: str | None = None
    page_size: int


class DailyStats(BaseModel):
    date: str
    total: int
    passed: int
    blocked: int


class FirewallStatsResponse(BaseModel):
    project_id: UUID
    period: str
    total_requests: int = 0
    passed: int = 0
    blocked: int = 0
    pass_rate: float = 0.0
    category_breakdown: dict[str, int] = {}
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    daily_breakdown: list[DailyStats] = []


class FirewallIntegrationResponse(BaseModel):
    endpoint_url: str
    api_key_prefix: str
    rate_limit: int
    python_snippet: str
    javascript_snippet: str
    curl_snippet: str
