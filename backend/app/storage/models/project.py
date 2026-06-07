"""
Project model — container for an AI application under test.

A Project belongs to a single user (owner). Each project holds the business
scope, allowed/restricted intents, and owns all experiments, firewall rules,
and firewall logs for one AI system. Each project gets a unique API key for
firewall integration.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    # --- Foreign Keys ---
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- Columns ---
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_scope: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_intents: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    restricted_intents: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    analyzed_scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    api_key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    owner: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="projects",
    )
    experiments: Mapped[list["Experiment"]] = relationship(  # noqa: F821
        "Experiment",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    firewall_rules: Mapped[list["FirewallRule"]] = relationship(  # noqa: F821
        "FirewallRule",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    firewall_logs: Mapped[list["FirewallLog"]] = relationship(  # noqa: F821
        "FirewallLog",
        back_populates="project",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"
