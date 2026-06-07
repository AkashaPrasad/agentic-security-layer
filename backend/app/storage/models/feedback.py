"""
Feedback model — human review of a TestCase verdict.

Captures an authenticated user's vote (agree / disagree), an optional
severity correction, and a free-text comment.  At most one feedback
record per (test_case, user) pair is allowed (UNIQUE constraint).
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Feedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint("test_case_id", "user_id", name="uq_feedback_testcase_user"),
    )

    # --- Foreign Keys ---
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Feedback data ---
    vote: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "up" | "down"
    correction: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "pass" | "low" | "medium" | "high"
    comment: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # --- Relationships ---
    test_case: Mapped["TestCase"] = relationship(  # noqa: F821
        "TestCase",
        back_populates="feedback",
    )
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="feedback",
    )

    def __repr__(self) -> str:
        return (
            f"<Feedback id={self.id} test_case_id={self.test_case_id} "
            f"user_id={self.user_id} vote={self.vote}>"
        )
