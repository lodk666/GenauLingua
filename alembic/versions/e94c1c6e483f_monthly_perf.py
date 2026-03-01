"""monthly perf

Revision ID: e94c1c6e483f
Revises: add_monthly_2026
Create Date: 2026-03-01 23:18:01.176165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e94c1c6e483f'
down_revision: Union[str, None] = 'add_monthly_2026'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'monthly_quiz_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.UniqueConstraint('quiz_session_id')
    )

    op.add_column('monthly_stats', sa.Column('total_correct', sa.Integer(), server_default='0'))
    op.add_column('monthly_stats', sa.Column('total_questions', sa.Integer(), server_default='0'))
    op.add_column('monthly_stats', sa.Column('last_quiz_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('monthly_stats', 'last_quiz_date')
    op.drop_column('monthly_stats', 'total_questions')
    op.drop_column('monthly_stats', 'total_correct')
    op.drop_table('monthly_quiz_events')
