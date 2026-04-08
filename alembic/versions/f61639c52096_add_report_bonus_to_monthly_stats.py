"""add_report_bonus_to_monthly_stats

Revision ID: f61639c52096
Revises: 7f7a5d79c7e7
Create Date: 2026-04-08 16:59:22.849134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f61639c52096'
down_revision: Union[str, None] = '7f7a5d79c7e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('monthly_stats', sa.Column(
        'report_bonus', sa.Integer(), nullable=False, server_default='0'
    ))


def downgrade() -> None:
    op.drop_column('monthly_stats', 'report_bonus')