"""merge monthly leaderboard

Revision ID: d47a6961a161
Revises: add_monthly_leaderboard, e94c1c6e483f
Create Date: 2026-03-02 00:54:47.078416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd47a6961a161'
down_revision: Union[str, None] = ('add_monthly_leaderboard', 'e94c1c6e483f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
