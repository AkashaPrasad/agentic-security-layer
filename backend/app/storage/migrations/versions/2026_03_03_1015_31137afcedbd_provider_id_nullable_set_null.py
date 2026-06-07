"""provider_id_nullable_set_null

Revision ID: 31137afcedbd
Revises: fef67a062fc9
Create Date: 2026-03-03 10:15:04.237082+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '31137afcedbd'
down_revision: Union[str, None] = 'fef67a062fc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('experiments', 'provider_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.drop_constraint('experiments_provider_id_fkey', 'experiments', type_='foreignkey')
    op.create_foreign_key(None, 'experiments', 'model_providers', ['provider_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'experiments', type_='foreignkey')
    op.create_foreign_key('experiments_provider_id_fkey', 'experiments', 'model_providers', ['provider_id'], ['id'], ondelete='RESTRICT')
    op.alter_column('experiments', 'provider_id',
               existing_type=sa.UUID(),
               nullable=False)
