"""
AuditLog model — tamper-evident, append-only record of security-relevant actions.

Captures who did what, when, and from where.

Tamper-evidence is implemented via a SHA-256 hash chain:
  - ``row_hash``  — SHA-256 of (id | created_at | user_id | action | entity_type |
                    entity_id | details | ip_address | prev_hash) for this row.
  - ``prev_hash`` — ``row_hash`` of the immediately preceding audit log record
                    (NULL for the first record).

A PostgreSQL rule blocks UPDATE and DELETE on the table at the DB layer.
Even if the application or an attacker with DB credentials attempts to modify
or delete a row, the rule will prevent it, making tampering detectable.
"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    # --- Foreign Keys ---
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- Event data ---
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    details: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )

    # --- Request context ---
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # --- Tamper-evidence hash chain ---
    # prev_hash: row_hash of the previous record (NULL for the first record).
    prev_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    # row_hash: SHA-256 hex digest over the canonical fields of this record.
    row_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    # --- Relationships ---
    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        back_populates="audit_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"entity={self.entity_type}:{self.entity_id}>"
        )
