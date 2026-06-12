"""add users.study_labels and users.study_statuses

Revision ID: b1f2c3d4e5a6
Revises: 4a760e5feccb
Create Date: 2026-06-12 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1f2c3d4e5a6'
down_revision: Union[str, None] = '4a760e5feccb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('study_labels', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False))
    op.add_column('users', sa.Column('study_statuses', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'study_statuses')
    op.drop_column('users', 'study_labels')
