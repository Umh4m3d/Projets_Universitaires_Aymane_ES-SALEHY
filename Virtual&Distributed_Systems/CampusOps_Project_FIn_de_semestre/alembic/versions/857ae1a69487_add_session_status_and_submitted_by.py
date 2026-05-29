"""add session status and submitted_by

Revision ID: 857ae1a69487
Revises: edda5f331e50
Create Date: 2026-05-01 12:33:17.231412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '857ae1a69487'
down_revision: Union[str, Sequence[str], None] = 'edda5f331e50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions',
        sa.Column('status', sa.String(length=20),
                  nullable=False,
                  server_default='approved')
    )
    op.add_column('sessions',
        sa.Column('submitted_by_id', sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        None, 'sessions', 'users',
        ['submitted_by_id'], ['id']
    )
    # Remove the server default after backfilling
    op.alter_column('sessions', 'status', server_default=None)


def downgrade() -> None:
    op.drop_constraint(None, 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'submitted_by_id')
    op.drop_column('sessions', 'status')
