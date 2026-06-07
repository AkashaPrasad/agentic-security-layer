"""add owasp_breakdown and kill_switch_active to monad_attestations

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('monad_attestations', sa.Column('owasp_breakdown', JSONB, nullable=False, server_default='{}'))
    op.add_column('monad_attestations', sa.Column('kill_switch_active', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('monad_attestations', 'kill_switch_active')
    op.drop_column('monad_attestations', 'owasp_breakdown')
