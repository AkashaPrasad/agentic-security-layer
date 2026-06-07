"""monad_attestations

Revision ID: a1b2c3d4e5f6
Revises: 08c94229b6b3
Create Date: 2026-06-07 12:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '08c94229b6b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create monad_attestations table."""
    op.create_table(
        'monad_attestations',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('agent_endpoint', sa.Text(), nullable=False),
        sa.Column('wallet_address', sa.String(42), nullable=True),
        sa.Column('tpi_score', sa.Integer(), nullable=False),
        sa.Column('result_hash', sa.String(66), nullable=False),
        sa.Column('tx_hash', sa.String(66), nullable=True),
        sa.Column('erc8004_feedback_id', sa.Integer(), nullable=True),
        sa.Column('passed_tests', sa.Integer(), nullable=False),
        sa.Column('total_tests', sa.Integer(), nullable=False, server_default=sa.text('5')),
        sa.Column('test_results', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
    )
    op.create_index('ix_monad_attestations_agent_id', 'monad_attestations', ['agent_id'])


def downgrade() -> None:
    """Drop monad_attestations table."""
    op.drop_index('ix_monad_attestations_agent_id', table_name='monad_attestations')
    op.drop_table('monad_attestations')
