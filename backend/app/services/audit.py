"""
Audit logging service.

Provides a helper to insert tamper-evident AuditLog records for any mutation.
Called from route handlers after successful database writes.

Each record carries:
  - ``prev_hash`` — the ``row_hash`` of the most recently inserted audit log,
    creating a hash chain analogous to a blockchain's prev-block-hash.
  - ``row_hash``  — SHA-256 of the canonical fields of *this* record including
    prev_hash, so any gap or alteration breaks the chain.

Verification: iterate audit_logs ORDER BY created_at ASC and re-compute each
row_hash; any mismatch indicates tampering.
"""

from __future__ import annotations

import hashlib
import json
import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import AuditLog, User


def _compute_row_hash(
    *,
    row_id: UUID,
    created_at_iso: str,
    user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    details: dict | None,
    ip_address: str | None,
    prev_hash: str | None,
) -> str:
    """Return the SHA-256 hex digest of the canonical row fields."""
    canonical = json.dumps(
        {
            "id": str(row_id),
            "created_at": created_at_iso,
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "ip_address": ip_address,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


async def _get_latest_row_hash(session: AsyncSession) -> str | None:
    """Return the row_hash of the most recently created audit log, or None."""
    result = await session.execute(
        select(AuditLog.row_hash)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row


async def write_audit_log(
    session: AsyncSession,
    *,
    user: User | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Write a tamper-evident, append-only audit record."""
    row_id = _uuid.uuid4()
    now = datetime.now(timezone.utc)
    created_at_iso = now.isoformat()

    prev_hash = await _get_latest_row_hash(session)

    row_hash = _compute_row_hash(
        row_id=row_id,
        created_at_iso=created_at_iso,
        user_id=str(user.id) if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details,
        ip_address=ip_address,
        prev_hash=prev_hash,
    )

    log = AuditLog(
        id=row_id,
        created_at=now,
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
    session.add(log)
    # flushed on next session.commit()
