"""
Experiment model — a single red-teaming or behavioural test run.

An Experiment belongs to a Project, uses a ModelProvider, and generates
TestCases.  It is executed asynchronously by a Celery worker and tracks
progress, status, timing, and aggregate analytics.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Experiment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "experiments"

    # --- Foreign Keys ---
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_providers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Configuration ---
    experiment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g. "adversarial", "behavioural"
    sub_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g. "safety", "hallucination", "stereotypes"
    turn_mode: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "single_turn" | "multi_turn"
    testing_level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "50" | "100" | "200" | "300" | "400" | "basic" | "moderate" | "aggressive"
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="en"
    )
    target_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # model, temperature, system_prompt, etc.

    # --- Execution state ---
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending", index=True
    )  # pending | running | completed | failed | cancelled
    progress_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    progress_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # --- Results / analytics ---
    analytics: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # pass_rate, severity_breakdown, category_breakdown, etc.

    # --- Timing ---
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )

    # --- Relationships ---
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="experiments",
    )
    created_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        foreign_keys=[created_by_id],
    )
    provider: Mapped["ModelProvider"] = relationship(  # noqa: F821
        "ModelProvider",
        back_populates="experiments",
    )
    test_cases: Mapped[list["TestCase"]] = relationship(  # noqa: F821
        "TestCase",
        back_populates="experiment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Experiment id={self.id} name={self.name!r} "
            f"type={self.experiment_type} status={self.status}>"
        )
