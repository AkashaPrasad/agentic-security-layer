"""
Pydantic schemas for the Feedback API (Phase 6.5).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class FeedbackSubmit(BaseModel):
    vote: str = Field(..., pattern=r"^(up|down)$")
    correction: str | None = Field(None, pattern=r"^(pass|low|medium|high)$")
    comment: str | None = Field(None, max_length=150)

    @model_validator(mode="after")
    def correction_only_on_downvote(self):
        if self.vote == "up" and self.correction is not None:
            raise ValueError("CORRECTION_NOT_ALLOWED")
        if self.comment:
            self.comment = self.comment.strip() or None
        return self


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class FeedbackResponse(BaseModel):
    id: UUID
    test_case_id: UUID
    user_id: UUID
    vote: str
    correction: str | None = None
    comment: str | None = None
    created_at: datetime
    updated_at: datetime


class CorrectionBreakdown(BaseModel):
    to_pass: int = 0
    to_low: int = 0
    to_medium: int = 0
    to_high: int = 0


class VoteBreakdown(BaseModel):
    thumbs_up: int = 0
    thumbs_down: int = 0
    corrections: CorrectionBreakdown = CorrectionBreakdown()


class FeedbackSummaryResponse(BaseModel):
    experiment_id: UUID
    total_test_cases: int = 0
    total_with_feedback: int = 0
    coverage_percentage: float = 0.0
    representative_total: int = 0
    representative_with_feedback: int = 0
    representative_coverage: float = 0.0
    vote_breakdown: VoteBreakdown = VoteBreakdown()
    my_feedback_count: int = 0
