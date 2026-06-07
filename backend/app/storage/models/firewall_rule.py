"""
FirewallRule model — configurable policy for the AI Firewall.

Rules define patterns or custom policies that the firewall evaluates
against incoming prompts before they reach the target AI model.
Rules are scoped to a Project and can be activated/deactivated.
Priority determines evaluation order (lower = evaluated first).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FirewallRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "firewall_rules"

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

    # --- Rule definition ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "block_pattern" | "allow_pattern" | "custom_policy"
    pattern: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # regex or keyword pattern for pattern-based rules
    policy: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # natural-language policy description for LLM judge

    # --- Evaluation order ---
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    # --- State ---
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="firewall_rules",
    )
    created_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        foreign_keys=[created_by_id],
    )
    firewall_logs: Mapped[list["FirewallLog"]] = relationship(  # noqa: F821
        "FirewallLog",
        back_populates="matched_rule",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<FirewallRule id={self.id} name={self.name!r} "
            f"type={self.rule_type} active={self.is_active}>"
        )
