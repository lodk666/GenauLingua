"""add monthly leaderboard tables

Revision ID: add_monthly_leaderboard
Revises: 3a55ad48f919
Create Date: 2026-03-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_monthly_leaderboard'
down_revision: Union[str, None] = '3a55ad48f919'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём таблицу monthly_seasons
    op.create_table(
        'monthly_seasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаём таблицу monthly_stats
    op.create_table(
        'monthly_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=True, default=0),
        sa.Column('quizzes_completed', sa.Integer(), nullable=True, default=0),
        sa.Column('words_learned', sa.Integer(), nullable=True, default=0),
        sa.Column('correct_answers', sa.Integer(), nullable=True, default=0),
        sa.Column('total_questions', sa.Integer(), nullable=True, default=0),
        sa.Column('current_win_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('best_win_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаём индексы для быстрого поиска
    op.create_index('ix_monthly_stats_user_season', 'monthly_stats', ['user_id', 'season_id'], unique=True)
    op.create_index('ix_monthly_stats_season_points', 'monthly_stats', ['season_id', 'total_points'])

    # Создаём таблицу win_streaks
    op.create_table(
        'win_streaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('streak_length', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаём таблицу monthly_awards
    op.create_table(
        'monthly_awards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('award_type', sa.String(length=50), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('awarded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('monthly_awards')
    op.drop_table('win_streaks')
    op.drop_index('ix_monthly_stats_season_points', table_name='monthly_stats')
    op.drop_index('ix_monthly_stats_user_season', table_name='monthly_stats')
    op.drop_table('monthly_stats')
    op.drop_table('monthly_seasons')