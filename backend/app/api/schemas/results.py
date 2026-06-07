"""
Pydantic schemas for the Results API (Phase 6.4).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class SeverityBreakdown(BaseModel):
    high: int = 0
    medium: int = 0
    low: int = 0


class CategoryBreakdownItem(BaseModel):
    risk_category: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    owasp_mapping: str | None = None


class FailImpact(BaseModel):
    level: str  # "low" | "medium" | "high" | "critical"
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary: str


class ExperimentInsights(BaseModel):
    summary: str
    key_findings: list[str] = []
    risk_assessment: str  # "low" | "medium" | "high" | "critical"
    recommendations: list[str] = []
    generated_at: datetime | None = None


class DashboardResponse(BaseModel):
    experiment_id: UUID
    experiment_name: str
    experiment_type: str
    sub_type: str
    status: str

    # Aggregate scores
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float = 0.0
    error_rate: float = 0.0
    fail_impact: FailImpact | None = None

    # Breakdowns
    severity_breakdown: SeverityBreakdown = SeverityBreakdown()
    category_breakdown: list[CategoryBreakdownItem] = []

    # AI Insights
    insights: ExperimentInsights | None = None

    # Optional cost telemetry
    cost_summary: dict | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


class FeedbackSnapshot(BaseModel):
    id: UUID
    vote: str
    correction: str | None = None
    comment: str | None = None
    created_at: datetime


class LogEntry(BaseModel):
    test_case_id: UUID
    sequence_order: int
    prompt_preview: str
    result: str  # "pass" | "fail" | "error"
    severity: str | None = None
    risk_category: str | None = None
    owasp_mapping: str | None = None
    confidence: float | None = None
    is_representative: bool = False
    data_strategy: str | None = None
    latency_ms: int | None = None
    has_feedback: bool = False
    created_at: datetime


class LogList(BaseModel):
    items: list[LogEntry]
    total: int
    next_cursor: str | None = None
    has_more: bool = False


class ConversationTurn(BaseModel):
    role: str
    content: str


class LogDetailResponse(BaseModel):
    test_case_id: UUID
    experiment_id: UUID
    sequence_order: int

    # Prompt / Response
    prompt: str
    response: str | None = None
    conversation_turns: list[ConversationTurn] | None = None

    # Generation metadata
    risk_category: str | None = None
    data_strategy: str | None = None
    attack_converter: str | None = None
    is_representative: bool = False
    latency_ms: int | None = None

    # Verdict (from Result)
    result: str
    severity: str | None = None
    confidence: float | None = None
    explanation: str | None = None
    owasp_mapping: str | None = None

    # User's feedback
    my_feedback: FeedbackSnapshot | None = None

    created_at: datetime
