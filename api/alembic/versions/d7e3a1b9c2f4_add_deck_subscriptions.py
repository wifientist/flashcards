"""add deck_subscriptions table

Revision ID: d7e3a1b9c2f4
Revises: b1f2c3d4e5a6
Create Date: 2026-06-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd7e3a1b9c2f4'
down_revision: Union[str, None] = 'b1f2c3d4e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'deck_subscriptions',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('deck_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'deck_id'),
    )


def downgrade() -> None:
    op.drop_table('deck_subscriptions')
