"""
TestCase model — a single test prompt/response pair within an Experiment.

Stores the adversarial or behavioural prompt sent to the target AI, the
raw response received, optional multi-turn conversation history, and
metadata about the generation strategy.  Has a 1:1 relationship with
Result (the evaluation verdict) and 1:N with Feedback (human review).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TestCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "test_cases"

    # --- Foreign Keys ---
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Prompt / Response ---
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # full multi-turn conversation [{role, content}, ...]

    # --- Generation metadata ---
    risk_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_strategy: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g. "pyrit_crescendo", "template_injection"
    attack_converter: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # PyRIT converter used, if any
    sequence_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # --- Flags ---
    is_representative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # flagged as canonical example

    # --- Performance ---
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Relationships ---
    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        "Experiment",
        back_populates="test_cases",
    )
    result: Mapped["Result | None"] = relationship(  # noqa: F821
        "Result",
        back_populates="test_case",
        uselist=False,
        cascade="all, delete-orphan",
    )
    feedback: Mapped[list["Feedback"]] = relationship(  # noqa: F821
        "Feedback",
        back_populates="test_case",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TestCase id={self.id} experiment_id={self.experiment_id} "
            f"category={self.risk_category}>"
        )
