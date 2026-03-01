"""
Миграция для системы месячных рейтингов

Добавляет:
- monthly_seasons (сезоны)
- monthly_stats (статистика за месяц)
- monthly_awards (награды)
- win_streaks (серии побед)
- обновления users
"""

revision = 'add_monthly_2026'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Создание таблиц для месячной системы рейтинга"""

    # 1. Таблица сезонов
    op.create_table(
        'monthly_seasons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('winners_finalized', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('year', 'month', name='uq_season_year_month')
    )

    # 2. Таблица месячной статистики
    op.create_table(
        'monthly_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('monthly_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_quizzes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_words', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_reverse', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_avg_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('final_rank', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'season_id', name='uq_monthly_user_season')
    )

    # Индексы для monthly_stats
    op.create_index('idx_monthly_stats_season', 'monthly_stats', ['season_id', 'monthly_score'], postgresql_ops={'monthly_score': 'DESC'})
    op.create_index('idx_monthly_stats_user', 'monthly_stats', ['user_id'])

    # 3. Таблица наград
    op.create_table(
        'monthly_awards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('award_type', sa.String(20), nullable=False),
        sa.Column('lifetime_bonus', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['season_id'], ['monthly_seasons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'season_id', name='uq_award_user_season')
    )

    op.create_index('idx_awards_user', 'monthly_awards', ['user_id'])

    # 4. Таблица серий побед
    op.create_table(
        'win_streaks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('best_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_wins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_win_season', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_win_season'], ['monthly_seasons.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_winstreak_user')
    )

    # 5. Обновление таблицы users
    op.add_column('users', sa.Column('lifetime_score', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('best_streak_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('total_monthly_wins', sa.Integer(), nullable=False, server_default='0'))

    # Убираем server_default
    op.alter_column('users', 'lifetime_score', server_default=None)
    op.alter_column('users', 'best_streak_days', server_default=None)
    op.alter_column('users', 'total_monthly_wins', server_default=None)

    print("✅ Созданы таблицы для месячной системы рейтинга")


def downgrade() -> None:
    """Откат миграции"""
    op.drop_column('users', 'total_monthly_wins')
    op.drop_column('users', 'best_streak_days')
    op.drop_column('users', 'lifetime_score')

    op.drop_table('win_streaks')
    op.drop_table('monthly_awards')
    op.drop_index('idx_monthly_stats_user', table_name='monthly_stats')
    op.drop_index('idx_monthly_stats_season', table_name='monthly_stats')
    op.drop_table('monthly_stats')
    op.drop_table('monthly_seasons')

    print("✅ Удалены таблицы месячной системы рейтинга")