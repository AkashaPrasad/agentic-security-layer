"""audit_log_tamper_evidence

Adds SHA-256 hash-chain columns (prev_hash, row_hash) to audit_logs and
installs a PostgreSQL rule that prevents UPDATE and DELETE on the table,
making audit records append-only at the database layer.

Revision ID: a3f91b2c4d78
Revises: 31137afcedbd
Create Date: 2026-03-22 09:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3f91b2c4d78'
down_revision: Union[str, None] = '31137afcedbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# PostgreSQL rule names
_RULE_NO_UPDATE = 'audit_logs_no_update'
_RULE_NO_DELETE = 'audit_logs_no_delete'


def upgrade() -> None:
    """Add tamper-evidence columns and install append-only rules."""

    # 1. Add prev_hash — SHA-256 of the previous record's row_hash (NULL for first)
    op.add_column(
        'audit_logs',
        sa.Column('prev_hash', sa.String(length=64), nullable=True),
    )

    # 2. Add row_hash — SHA-256 of this record's canonical fields + prev_hash
    op.add_column(
        'audit_logs',
        sa.Column('row_hash', sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f('ix_audit_logs_row_hash'),
        'audit_logs',
        ['row_hash'],
        unique=False,
    )

    # 3. Install PostgreSQL rules that silently block UPDATE and DELETE.
    #    Using NOTHING means any UPDATE/DELETE simply does nothing rather than
    #    raising an error — prevents application crashes while still blocking
    #    tampering. SOC2 auditors verify the rule exists; any attempt to delete
    #    or modify a row silently no-ops.
    op.execute(
        f"CREATE OR REPLACE RULE {_RULE_NO_UPDATE} AS "
        f"ON UPDATE TO audit_logs DO INSTEAD NOTHING;"
    )
    op.execute(
        f"CREATE OR REPLACE RULE {_RULE_NO_DELETE} AS "
        f"ON DELETE TO audit_logs DO INSTEAD NOTHING;"
    )


def downgrade() -> None:
    """Remove tamper-evidence columns and rules."""
    op.execute(f"DROP RULE IF EXISTS {_RULE_NO_DELETE} ON audit_logs;")
    op.execute(f"DROP RULE IF EXISTS {_RULE_NO_UPDATE} ON audit_logs;")
    op.drop_index(op.f('ix_audit_logs_row_hash'), table_name='audit_logs')
    op.drop_column('audit_logs', 'row_hash')
    op.drop_column('audit_logs', 'prev_hash')
