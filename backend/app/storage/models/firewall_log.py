"""
FirewallLog model — evaluation log for an AI Firewall request.

Each record represents one prompt evaluation by the firewall.  Stores
a SHA-256 hash of the full prompt (for deduplication / analytics), a
truncated preview, the pass/fail verdict, optional matched rule
reference, and performance metrics.
"""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FirewallLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "firewall_logs"

    # --- Foreign Keys ---
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matched_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("firewall_rules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Request data ---
    prompt_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # SHA-256 hex digest
    prompt_preview: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # first 200 chars for display
    agent_prompt_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # hash of the agent/system prompt, if provided

    # --- Verdict ---
    verdict_status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, index=True
    )  # True = passed, False = blocked
    fail_category: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # category of failure, null when passed
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- Performance / context ---
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # --- Relationships ---
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="firewall_logs",
    )
    matched_rule: Mapped["FirewallRule | None"] = relationship(  # noqa: F821
        "FirewallRule",
        back_populates="firewall_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<FirewallLog id={self.id} project_id={self.project_id} "
            f"passed={self.verdict_status}>"
        )
