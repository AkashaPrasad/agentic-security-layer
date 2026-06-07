"""
Result model — the evaluation verdict for a single TestCase.

Stores the pass/fail/error outcome produced by the LLM judge, along
with severity, confidence score, a human-readable explanation, and an
optional OWASP LLM Top-10 mapping.  Has a strict 1:1 relationship
with TestCase (enforced via UNIQUE constraint on test_case_id).
"""

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Result(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "results"

    # --- Foreign Keys (1:1 with TestCase) ---
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # --- Verdict ---
    result: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "pass" | "fail" | "error"
    severity: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "low" | "medium" | "high"  (null when result=pass)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Classification ---
    owasp_mapping: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # e.g. "LLM01", "LLM02"

    # --- Relationships ---
    test_case: Mapped["TestCase"] = relationship(  # noqa: F821
        "TestCase",
        back_populates="result",
    )

    def __repr__(self) -> str:
        return (
            f"<Result id={self.id} test_case_id={self.test_case_id} "
            f"result={self.result} severity={self.severity}>"
        )
